import { invoke } from "@tauri-apps/api/core";

/** Explicit export action: native Downloads file in Tauri, download in a browser. */
export async function exportLog(contents: string, format: "txt" | "json"): Promise<string> {
  if ("__TAURI_INTERNALS__" in window) return invoke<string>("export_run_log", { contents, format });
  const blob = new Blob([contents], { type: format === "json" ? "application/json" : "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `netzoo-run-${new Date().toISOString().replace(/[:.]/g, "-")}.${format}`;
  document.body.append(anchor); anchor.click(); anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 10_000);
  return "Downloaded the run log.";
}
