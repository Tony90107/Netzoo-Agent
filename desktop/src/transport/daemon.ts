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

export async function startDaemon(
  report: (step: string) => void,
): Promise<{ config: DaemonConfig }> {
  report("Reading shell configuration");
  const config = await invoke<DaemonConfig>("daemon_config");

  // An already-running daemon (a previous launch, or one started by hand for
  // debugging) is reused rather than restarted.
  report("Looking for a running daemon");
  if (await health(config)) return { config };

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
    if (await health(config)) return { config };
    await new Promise((resolve) => setTimeout(resolve, HEALTH_INTERVAL_MS));
  }
  throw {
    kind: "health_timeout",
    message: "The daemon container started but never became healthy.",
    remedy: "Check its output with `docker compose logs netzoo-daemon`.",
    detail: `No healthy response within ${HEALTH_TIMEOUT_MS / 1000}s.`,
  } satisfies DaemonFault;
}

export async function stopDaemon(): Promise<void> {
  try {
    await invoke("stop_daemon");
  } catch {
    // The window is closing; a failure to stop the container is not worth
    // blocking quit over, and the container is idle either way.
  }
}
