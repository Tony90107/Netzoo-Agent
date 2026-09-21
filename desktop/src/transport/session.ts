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
  TraceEvent,
  UsagePayload,
  ViewPayload,
  WS_TOKEN_SUBPROTOCOL,
} from "./protocol";

export type Entry =
  | { kind: "user"; id: number; text: string }
  | { kind: "agent"; id: number; text: string }
  | { kind: "notice"; id: number; text: string }
  | { kind: "error"; id: number; errorType: string; text: string };

export type SessionState = {
  sessionId: string;
  entries: Entry[];
  view: ViewPayload | null;
  /** Set while a graph turn is running; the input area is disabled then. */
  busy: boolean;
  progress: string | null;
  trace: TraceEvent[];
  usage: UsagePayload | null;
  stopped: boolean;
  connection: "connecting" | "open" | "closed";
};

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
});

let nextEntryId = 1;
const entryId = () => nextEntryId++;

export async function createSession(config: DaemonConfig): Promise<string> {
  const response = await fetch(`${config.baseUrl}/v1/sessions`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${config.token}`,
      "Content-Type": "application/json",
    },
    body: "{}",
  });
  if (!response.ok) {
    throw new Error(`could not start a session (${response.status})`);
  }
  return (await response.json()).session_id as string;
}

export class SessionSocket {
  private socket: WebSocket | null = null;
  private lastSeq = 0;

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

    socket.onopen = () => this.onChange((s) => ({ ...s, connection: "open" }));
    socket.onclose = () => this.onChange((s) => ({ ...s, connection: "closed" }));
    socket.onmessage = (event) => this.receive(event.data as string);
  }

  close(): void {
    this.socket?.close();
    this.socket = null;
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

  /** Answer the current prompt. Clears the view so the input area locks. */
  answer(text: string, echo = true): void {
    this.onChange((s) => ({
      ...s,
      entries: echo ? [...s.entries, { kind: "user", id: entryId(), text }] : s.entries,
      view: null,
    }));
    this.send({ type: "answer", text });
  }

  approveExecution(planHash: string): void {
    this.onChange((s) => ({ ...s, view: null }));
    this.send({ type: "approve_execution", plan_hash: planHash });
  }

  declineExecution(): void {
    this.onChange((s) => ({ ...s, view: null }));
    this.send({ type: "decline_execution" });
  }

  cancel(): void {
    this.send({ type: "cancel" });
  }

  private receive(raw: string): void {
    let envelope: Envelope;
    try {
      envelope = JSON.parse(raw);
    } catch {
      return;
    }
    if (envelope.seq > this.lastSeq) this.lastSeq = envelope.seq;
    const payload = envelope.payload as never;
    this.onChange((state) => reduce(state, envelope.type, payload));
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
        entries: [...state.entries, { kind: "agent", id: entryId(), text: String(body.text) }],
      };
    case "notice":
      return {
        ...state,
        entries: [...state.entries, { kind: "notice", id: entryId(), text: String(body.text) }],
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
      return { ...state, usage: body as unknown as UsagePayload };
    case "error":
      return {
        ...state,
        entries: [
          ...state.entries,
          {
            kind: "error",
            id: entryId(),
            errorType: String(body.error_type),
            text: String(body.message),
          },
        ],
      };
    case "stopped":
      return { ...state, stopped: true, busy: false, view: null };
    default:
      return state;
  }
}
