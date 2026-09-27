/**
 * Bringing the daemon up, and saying something useful when it does not come up.
 *
 * The shell owns the container and the token; this module owns the waiting.
 * Everything here is about the gap between "we asked Docker to start something"
 * and "the agent can take a question", because that gap is the whole of the
 * cold start the user experiences.
 */
import { invoke } from "@tauri-apps/api/core";

export type DaemonConfig = {
  token: string;
  port: number;
  baseUrl: string;
  socketUrl: string;
};

export type DaemonFault = {
  kind: string;
  message: string;
  remedy: string;
  detail: string;
};

export type Phase =
  | { name: "idle" }
  | { name: "starting"; step: string; sinceMs: number }
  | { name: "ready"; config: DaemonConfig; tookMs: number }
  | { name: "failed"; fault: DaemonFault; tookMs: number };

/** Health polling budget. Past this the container exists but is not answering. */
const HEALTH_TIMEOUT_MS = 60_000;
const HEALTH_INTERVAL_MS = 250;

function isFault(value: unknown): value is DaemonFault {
  return typeof value === "object" && value !== null && "kind" in value;
}

function asFault(error: unknown, kind: string, remedy: string): DaemonFault {
  if (isFault(error)) return error;
  return {
    kind,
    message: error instanceof Error ? error.message : String(error),
    remedy,
    detail: "",
  };
}

async function health(config: DaemonConfig): Promise<boolean> {
  try {
    const response = await fetch(`${config.baseUrl}/health`);
    if (!response.ok) return false;
    const body = await response.json();
    return body?.status === "ok";
  } catch {
    // Connection refused is the normal state while the container boots.
    return false;
  }
}

/**
 * Does the daemon on that port accept *our* token?
 *
 * `/health` needs no token, so a daemon left over from an earlier launch — one
 * that was force-killed before it could stop its container — answers it
 * happily while holding a different secret. Reusing it on the strength of
 * /health alone produced a window that started cleanly and then failed every
 * request with 401.
 */
async function authorized(config: DaemonConfig): Promise<boolean> {
  try {
    const response = await fetch(`${config.baseUrl}/v1/sessions`, {
      headers: { Authorization: `Bearer ${config.token}` },
    });
    return response.ok;
  } catch {
    return false;
  }
}

/** Key a developer sets by hand to run this UI in a plain browser. */
const DEV_CONFIG_KEY = "netzoo.daemon";

function inTauri(): boolean {
  return typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;
}

function developerConfig(): DaemonConfig | null {
  // Outside Tauri there is no shell to mint a token or start a container, so
  // the daemon has to be running already and its token supplied by hand. This
  // exists so the window's own code can be exercised in a browser; it grants
  // nothing, because whoever sets it already holds the token.
  try {
    const raw = window.localStorage.getItem(DEV_CONFIG_KEY);
    return raw ? (JSON.parse(raw) as DaemonConfig) : null;
  } catch {
    return null;
  }
}

async function bootDaemon(
  report: (step: string) => void,
): Promise<{ config: DaemonConfig }> {
  report("Reading shell configuration");
  if (!inTauri()) {
    const config = developerConfig();
    if (!config) {
      throw {
        kind: "no_shell",
        message: "This page is not running inside the NetZoo Agent window.",
        remedy:
          `Start the daemon yourself and put its config in localStorage under "${DEV_CONFIG_KEY}".`,
        detail: "",
      } satisfies DaemonFault;
    }
    report("Waiting for the agent to answer");
    if (await health(config)) return { config };
    throw {
      kind: "health_timeout",
      message: "No daemon answered on the configured port.",
      remedy: "Start it with `docker compose up -d netzoo-daemon`.",
      detail: config.baseUrl,
    } satisfies DaemonFault;
  }
  const config = await invoke<DaemonConfig>("daemon_config");

  // An already-running daemon is reused only when it answers to this launch's
  // token; otherwise it is a leftover and compose recreates it below, because
  // the changed token changes the service definition.
  report("Looking for a running daemon");
  if ((await health(config)) && (await authorized(config))) return { config };

  report("Starting the daemon container");
  try {
    await invoke("start_daemon");
  } catch (error) {
    throw asFault(
      error,
      "start_failed",
      "Run `docker compose up netzoo-daemon` in a terminal to see the full output.",
    );
  }

  report("Waiting for the agent to answer");
  const deadline = Date.now() + HEALTH_TIMEOUT_MS;
  while (Date.now() < deadline) {
    if ((await health(config)) && (await authorized(config))) return { config };
    await new Promise((resolve) => setTimeout(resolve, HEALTH_INTERVAL_MS));
  }
  throw {
    kind: "health_timeout",
    message: "The daemon container started but never became healthy.",
    remedy: "Check its output with `docker compose logs netzoo-daemon`.",
    detail: `No healthy response within ${HEALTH_TIMEOUT_MS / 1000}s.`,
  } satisfies DaemonFault;
}

let pendingStart: Promise<{ config: DaemonConfig }> | null = null;
const startupListeners = new Set<(step: string) => void>();
let startupStep = "Starting the agent";

/** StrictMode and retries share an in-progress boot instead of racing Compose. */
export function startDaemon(report: (step: string) => void): Promise<{ config: DaemonConfig }> {
  startupListeners.add(report);
  if (!pendingStart) {
    pendingStart = bootDaemon((step) => {
      startupStep = step;
      for (const listener of startupListeners) listener(step);
    }).finally(() => { pendingStart = null; startupListeners.clear(); });
  } else {
    report(startupStep);
  }
  return pendingStart;
}

export async function stopDaemon(): Promise<void> {
  try {
    await invoke("stop_daemon");
  } catch {
    // The window is closing; a failure to stop the container is not worth
    // blocking quit over, and the container is idle either way.
  }
}
