import type { DaemonConfig } from "./daemon";
import type { TraceEvent } from "./protocol";
import { get } from "./files";

export type SavedRun = {
  run_id: string; session_id: string; created_at: string; updated_at: string;
  finished_at: string | null; status: string; event_count: number; sealed: boolean;
};
export type SavedRuns = { runs: SavedRun[]; total: number; offset: number; has_more: boolean; unavailable_metadata: number };
export type SavedEvents = { events: TraceEvent[]; run: SavedRun; version: string; next_sequence: number | null; incomplete: boolean; note: string };

export function readRuns(config: DaemonConfig, sessionId: string, offset = 0, signal?: AbortSignal) {
  return get<SavedRuns>(config, `/v1/history/${encodeURIComponent(sessionId)}/activity?offset=${offset}`, signal);
}
export function readEvents(config: DaemonConfig, sessionId: string, runId: string, after = 0, version = "", signal?: AbortSignal) {
  const query = new URLSearchParams({ after_sequence: String(after), version });
  return get<SavedEvents>(config, `/v1/history/${encodeURIComponent(sessionId)}/activity/${encodeURIComponent(runId)}?${query}`, signal);
}
