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
};

async function get<T>(config: DaemonConfig, path: string): Promise<T> {
  const response = await fetch(`${config.baseUrl}${path}`, {
    headers: { Authorization: `Bearer ${config.token}` },
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail ?? `request failed (${response.status})`);
  }
  return (await response.json()) as T;
}

export function listDirectory(config: DaemonConfig, path = ""): Promise<Listing> {
  return get<Listing>(config, `/v1/files?path=${encodeURIComponent(path)}`);
}

export function previewFile(config: DaemonConfig, path: string): Promise<Preview> {
  return get<Preview>(config, `/v1/files/preview?path=${encodeURIComponent(path)}`);
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
