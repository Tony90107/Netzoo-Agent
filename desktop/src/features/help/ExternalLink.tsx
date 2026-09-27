import { useState, type ReactNode } from "react";
import { invoke } from "@tauri-apps/api/core";

export function ExternalLink({ href, children }: { href: string; children: ReactNode }) {
  const [error, setError] = useState("");
  if (!/^https?:\/\//i.test(href)) return <span>{children}</span>;
  return <>
    <a href={href} target="_blank" rel="noopener noreferrer" title={`Open in your browser: ${href}`} onClick={(event) => {
      if (!("__TAURI_INTERNALS__" in window)) return;
      event.preventDefault(); setError("");
      void invoke("open_external_url", { url: href }).catch(() => setError(`Unable to open link. Copy this address: ${href}`));
    }}>{children}</a>
    {error ? <span className="link-error" role="alert">{error}</span> : null}
  </>;
}
