import { invoke } from "@tauri-apps/api/core";
import type { DaemonConfig } from "./daemon";

export type EnvironmentCheck = {
  key: string;
  label: string;
  status: "passed" | "warning" | "failed" | "unknown";
  detail: string;
  remedy: string;
};

export type EnvironmentReport = {
  checked_at: string;
  checks: EnvironmentCheck[];
  netzoopy_version: string;
  source_ref: string;
  available_methods: string[];
  note: string;
};

export async function checkHostEnvironment(): Promise<EnvironmentCheck[]> {
  if (!("__TAURI_INTERNALS__" in window)) return [{
    key: "host", label: "Host Docker and image", status: "unknown",
    detail: "Host checks are available in the desktop app. This browser cannot inspect Docker.",
    remedy: "Open NetZoo Agent on your desktop to inspect the host environment.",
  }];
  return invoke<EnvironmentCheck[]>("check_environment");
}

export async function checkRuntimeEnvironment(config: DaemonConfig): Promise<EnvironmentReport> {
  const response = await fetch(`${config.baseUrl}/v1/environment`, {
    headers: { Authorization: `Bearer ${config.token}` },
    signal: AbortSignal.timeout(15_000),
  });
  if (!response.ok) throw new Error(`Environment check failed (${response.status}). Restart the daemon if it is running an older version.`);
  return response.json() as Promise<EnvironmentReport>;
}
