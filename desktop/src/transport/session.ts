/**
 * One session's socket, and the state it accumulates.
 *
 * The daemon's rule is that `view` is the only thing that says what the user
 * may enter next. This client keeps that rule: it never infers a prompt from
 * a message or a plan, it only ever renders the last `view` it was sent. That
 * is what stops the window and the terminal drifting into two different state
 * machines.
 */
import { DaemonConfig } from "./daemon";
import {
  ClientMessage,
  Envelope,
  PROTOCOL_VERSION,
  ReplyCard,
  TraceEvent,
  LLMUsage,
  ViewPayload,
  WS_TOKEN_SUBPROTOCOL,
} from "./protocol";

export type Entry = (
  | { kind: "user"; id: number; text: string }
  | { kind: "agent"; id: number; text: string; card?: ReplyCard | null }
  | { kind: "notice"; id: number; text: string }
  | { kind: "error"; id: number; errorType: string; text: string }
) & { at?: string; timeSource?: "server" | "local" | "received"; action?: "message" | "command" | "confirmation" };

export type SessionState = {
  sessionId: string;
  entries: Entry[];
  view: ViewPayload | null;
  /** Set while a graph turn is running; the input area is disabled then. */
  busy: boolean;
  progress: string | null;
  trace: TraceEvent[];
  usage: LLMUsage | null;
  stopped: boolean;
  connection: Connection;
  /** Why the socket closed for good, when it did. */
  closedReason: string | null;
  /**
   * True once the daemon could not replay everything that was missed.
   *
   * It keeps the last 500 events per session. Past that, a reconnect resumes
   * from a later event than the one the client last saw, and the timeline is
   * no longer the whole run — which is precisely the claim the timeline makes,
   * so it has to be said rather than quietly papered over.
   */
  missedEvents: boolean;
};

export type Connection = "connecting" | "open" | "reconnecting" | "closed";

/**
 * Close codes that mean "do not come back".
 *
 * Short, because a rejected handshake cannot carry one: when the daemon
 * closes before accepting — an unknown session, a bad token — the browser
 * reports 1006, the same code a killed daemon produces. Telling those apart
 * needs a question the socket cannot answer, so `sessionVerdict` asks over
 * HTTP instead.
 */
const TERMINAL_CLOSE: Record<number, string> = {
  1000: "The session ended.",
};

export const SESSION_GONE = "That session is no longer running.";
export const NOT_AUTHORISED = "This window is no longer authorised.";

/**
 * Should a dropped socket be retried?
 *
 * Returns a reason to stop, or null to keep trying. A daemon that does not
 * answer at all is restarting, which is exactly the case reconnecting exists
 * for; a daemon that answers and does not know this session has lost it.
 */
export async function sessionVerdict(
  config: DaemonConfig,
  sessionId: string,
): Promise<string | null> {
  let response: Response;
  try {
    response = await fetch(`${config.baseUrl}/v1/sessions`, {
      headers: { Authorization: `Bearer ${config.token}` },
    });
  } catch {
    return null;
  }
  if (response.status === 401) return NOT_AUTHORISED;
  if (!response.ok) return null;
  try {
    const body = await response.json();
    const alive = (body.sessions ?? []).some(
      (entry: { session_id: string }) => entry.session_id === sessionId,
    );
    return alive ? null : SESSION_GONE;
  } catch {
    return null;
  }
}

/** Retry delay in ms; flat after a few tries so a long outage stays cheap. */
export function backoffDelay(attempt: number): number {
  return Math.min(250 * 2 ** attempt, 5_000);
}

export function closeReason(code: number, closedByUs: boolean): string | null {
  if (closedByUs) return "Disconnected.";
  return TERMINAL_CLOSE[code] ?? null;
}

export const emptySession = (sessionId: string): SessionState => ({
  sessionId,
  entries: [],
  view: null,
  busy: false,
  progress: null,
  trace: [],
  usage: null,
  stopped: false,
  connection: "connecting",
  closedReason: null,
  missedEvents: false,
});

let nextEntryId = 1;
const entryId = () => nextEntryId++;
function timestamped<T extends Entry>(entry: T, body?: Record<string, unknown>): T {
  const original = body?.occurred_at;
  const valid = typeof original === "string" && /(?:Z|[+-]\d{2}:\d{2})$/i.test(original) && Number.isFinite(Date.parse(original));
  return { ...entry, at: valid ? original : new Date().toISOString(), timeSource: valid ? "server" : body ? "received" : "local" };
}

export function entryTimestamp(entry: Entry): string | undefined {
  return entry.at;
}

export type NewSessionOptions = { model?: string; tags?: string[]; name?: string };

export async function createSession(
  config: DaemonConfig,
  resume?: string,
  options: NewSessionOptions = {},
): Promise<string> {
  const body: Record<string, unknown> = resume ? { resume } : {};
  // A model is chosen once, when a session starts (one session, one model);
  // the daemon still refuses any model its allowlist does not name.
  if (!resume && options.model) body.model = options.model;
  if (!resume && options.tags?.length) body.tags = options.tags;
  if (!resume && options.name?.trim()) body.name = options.name.trim();
  const response = await fetch(`${config.baseUrl}/v1/sessions`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${config.token}`,
      "Content-Type": "application/json",
    },
    // Resuming hands the checkpoint id to the worker, which is the same path
    // `--resume` takes in the terminal.
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`could not start a session (${response.status})`);
  }
  return (await response.json()).session_id as string;
}

export class SessionSocket {
  private socket: WebSocket | null = null;
  private lastSeq = 0;
  private promptSeq = 0;
  private attempt = 0;
  private closedByUs = false;
  private retry: ReturnType<typeof setTimeout> | null = null;

  constructor(
    private readonly config: DaemonConfig,
    private readonly sessionId: string,
    private readonly onChange: (apply: (state: SessionState) => SessionState) => void,
  ) {}

  open(): void {
    // The token rides in the subprotocol: a browser cannot set an
    // Authorization header here, and a query parameter would be copied into
    // the daemon's access log.
    const url = `${this.config.socketUrl}/ws/session/${this.sessionId}?since=${this.lastSeq}`;
    const socket = new WebSocket(url, [WS_TOKEN_SUBPROTOCOL, this.config.token]);
    this.socket = socket;

    socket.onopen = () => {
      this.attempt = 0;
      this.onChange((s) => ({ ...s, connection: "open", closedReason: null }));
    };
    socket.onclose = (event) => this.handleClose(event.code);
    socket.onmessage = (event) => this.receive(event.data as string);
  }

  close(): void {
    this.closedByUs = true;
    if (this.retry !== null) clearTimeout(this.retry);
    this.retry = null;
    this.socket?.close();
    this.socket = null;
  }

  /**
   * A dropped socket is not a dead session.
   *
   * The worker keeps running across a daemon restart, a sleep, or a blip, and
   * the daemon can replay what was missed from `since`. Without this the
   * window simply went quiet and the only way back was to relaunch it.
   */
  private handleClose(code: number): void {
    const reason = closeReason(code, this.closedByUs);
    if (reason !== null) {
      this.onChange((s) => ({ ...s, connection: "closed", closedReason: reason }));
      return;
    }
    const delay = backoffDelay(this.attempt);
    this.attempt += 1;
    this.onChange((s) => ({ ...s, connection: "reconnecting" }));
    this.retry = setTimeout(() => {
      this.retry = null;
      if (this.closedByUs) return;
      void sessionVerdict(this.config, this.sessionId).then((verdict) => {
        if (this.closedByUs) return;
        if (verdict !== null) {
          this.onChange((s) => ({
            ...s,
            connection: "closed",
            closedReason: verdict,
          }));
          return;
        }
        this.open();
      });
    }, delay);
  }

  private send(message: ClientMessage): void {
    const { type, ...payload } = message;
    const envelope: Envelope = {
      v: PROTOCOL_VERSION,
      type,
      session_id: this.sessionId,
      seq: 0,
      payload: payload as Record<string, unknown>,
    };
    this.socket?.send(JSON.stringify(envelope));
  }

  /** Answer the current prompt. Clears the view so the input area locks. Records user controls for the activity log. */
  answer(text: string, echo = true): void {
    this.onChange((s) => ({
      ...s,
      entries: [...s.entries, timestamped({ kind: "user", id: entryId(), text, action: echo ? "message" : "command" })],
      view: null,
    }));
    this.send({ type: "answer", text, prompt_seq: this.promptSeq });
  }

  approveExecution(planHash: string): void {
    this.onChange((s) => ({ ...s, view: null, entries: [...s.entries, timestamped({
      kind: "user", id: entryId(), text: `Requested execution of plan ${planHash.slice(0, 12)}.`, action: "confirmation",
    })] }));
    this.send({
      type: "approve_execution",
      plan_hash: planHash,
      prompt_seq: this.promptSeq,
    });
  }

  declineExecution(): void {
    this.onChange((s) => ({ ...s, view: null, entries: [...s.entries, timestamped({
      kind: "user", id: entryId(), text: "Declined execution of the current plan.", action: "confirmation",
    })] }));
    this.send({ type: "decline_execution", prompt_seq: this.promptSeq });
  }

  /**
   * Interrupt the turn that is running.
   *
   * Not a socket message: while a turn runs the worker is inside
   * `app.invoke()` and is not reading the channel, so a `cancel` envelope
   * would sit in the queue and only be read at the *next* prompt — where it
   * ends the session, long after the analysis it was meant to stop has
   * finished. The daemon's cancel endpoint signals the process instead,
   * which is the path the agent already handles.
   */
  async cancel(): Promise<void> {
    this.onChange((s) => ({ ...s, entries: [...s.entries, timestamped({
      kind: "user", id: entryId(), text: "Requested interruption of the current turn.", action: "command",
    })] }));
    try {
      await fetch(`${this.config.baseUrl}/v1/sessions/${this.sessionId}/cancel`, {
        method: "POST",
        headers: { Authorization: `Bearer ${this.config.token}` },
      });
    } catch {
      // The turn either stops or it does not; a failed request is reported by
      // the session going quiet, not by a second error box.
    }
  }

  private receive(raw: string): void {
    let envelope: Envelope;
    try {
      envelope = JSON.parse(raw);
    } catch {
      return;
    }
    // Envelopes are numbered per session, so a jump means the daemon's replay
    // buffer had already rolled past what this client last saw.
    const gap = envelope.seq > this.lastSeq + 1 && this.lastSeq > 0;
    if (envelope.seq > this.lastSeq) this.lastSeq = envelope.seq;
    if (envelope.type === "view") this.promptSeq = envelope.seq;
    const payload = envelope.payload as never;
    this.onChange((state) => {
      const next = reduce(state, envelope.type, payload);
      return gap ? { ...next, missedEvents: true } : next;
    });
  }
}

export function reduce(
  state: SessionState,
  type: string,
  payload: never,
): SessionState {
  const body = payload as unknown as Record<string, unknown>;
  switch (type) {
    case "view":
      return { ...state, view: body as unknown as ViewPayload, busy: false, progress: null };
    case "message":
      return {
        ...state,
        entries: [...state.entries, timestamped({
          kind: "agent", id: entryId(), text: String(body.text),
          card: (body.card as ReplyCard | undefined) ?? null,
        }, body)],
      };
    case "notice":
      return {
        ...state,
        entries: [...state.entries, timestamped({
          kind: "notice", id: entryId(), text: String(body.text),
        }, body)],
      };
    case "progress":
      return { ...state, progress: String(body.text) };
    case "trace":
      return { ...state, trace: [...state.trace, body as unknown as TraceEvent] };
    case "turn_started":
      return { ...state, busy: true, view: null };
    case "turn_finished":
      return { ...state, busy: false, progress: null };
    case "usage":
      return { ...state, usage: body as unknown as LLMUsage };
    case "error":
      return {
        ...state,
        entries: [
          ...state.entries,
          timestamped({
            kind: "error",
            id: entryId(),
            errorType: String(body.error_type),
            text: String(body.message),
          }, body),
        ],
      };
    case "stopped":
      return { ...state, stopped: true, busy: false, view: null };
    default:
      return state;
  }
}
