/**
 * Reading the outputs tree through the daemon.
 *
 * The window never touches the filesystem itself. Everything goes through the
 * daemon, which is the side that holds the containment rule, and paths on the
 * wire are project-relative — the one spelling both sides agree on. A host
 * path comes back alongside, for display only, so someone can find the file
 * in Finder.
 */
import { DaemonConfig } from "./daemon";

export type FileEntry = {
  name: string;
  path: string;
  kind: "directory" | "file";
  size_bytes: number;
  modified_at: number;
};

export type Listing = {
  path: string;
  host_path: string;
  entries: FileEntry[];
  total: number;
  offset: number;
  limit: number;
  has_more: boolean;
};

export type Preview = {
  path: string;
  host_path: string;
  kind: "table" | "text" | "arrays" | "binary";
  size_bytes: number;
  truncated: boolean;
  columns: string[];
  rows: string[][];
  text: string;
  arrays: { name: string; shape: number[]; dtype: string }[];
  note: string;
  offset: number;
  next_offset: number | null;
  version: string;
  total_columns: number;
};

export async function get<T>(config: DaemonConfig, path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${config.baseUrl}${path}`, {
    headers: { Authorization: `Bearer ${config.token}` },
    signal,
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail ?? `request failed (${response.status})`);
  }
  return (await response.json()) as T;
}

export function listDirectory(
  config: DaemonConfig,
  path = "",
  offset = 0,
  limit = 100,
): Promise<Listing> {
  const query = new URLSearchParams({ path, offset: String(offset), limit: String(limit) });
  return get<Listing>(config, `/v1/files?${query.toString()}`);
}

export function previewFile(config: DaemonConfig, path: string, offset = 0, version = ""): Promise<Preview> {
  const query = new URLSearchParams({ path, offset: String(offset), version });
  return get<Preview>(config, `/v1/files/preview?${query.toString()}`);
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  const units = ["KB", "MB", "GB"];
  let value = bytes / 1024;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return `${value.toFixed(value >= 10 ? 0 : 1)} ${units[unit]}`;
}

export type SessionSummary = {
  session_id: string;
  profile_id: string;
  updated_at: number;
  auto_generated: boolean;
  workflow: string;
  status: string;
  resumable: boolean;
  title: string;
  total_tokens: number;
};

export type EffectiveSettings = {
  models: Record<string, string>;
  allowlists: Record<string, string>;
  limits: Record<string, number>;
  paths: Record<string, string>;
  retention_days: Record<string, number>;
  storage: {
    sessions: { files: number; bytes: number };
    traces: { files: number; bytes: number; runs: number; unsealed_runs: number };
  };
  api_key_present: boolean;
};

export type SessionPage = { sessions: SessionSummary[]; offset: number; has_more: boolean; next_offset: number | null };
export type SessionFilter = "all" | "needs_input" | "needs_confirmation" | "completed" | "failed" | "dry_run";
export function listSessions(config: DaemonConfig, options: { query?: string; status?: SessionFilter; offset?: number } = {}, signal?: AbortSignal): Promise<SessionPage> {
  const params = new URLSearchParams({ query: options.query ?? "", status: options.status ?? "all", offset: String(options.offset ?? 0) });
  return get<SessionPage>(config, `/v1/history?${params}`, signal);
}

export function readSettings(config: DaemonConfig): Promise<EffectiveSettings> {
  return get<EffectiveSettings>(config, "/v1/settings");
}

export type Transcript = {
  session_id: string;
  status: string;
  workflow: string;
  resumable: boolean;
  messages: { role: string; content: string }[];
  truncated: boolean;
};

export function readTranscript(
  config: DaemonConfig,
  sessionId: string,
): Promise<Transcript> {
  return get<Transcript>(config, `/v1/history/${encodeURIComponent(sessionId)}`);
}
