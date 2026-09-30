/**
 * The outputs browser.
 *
 * A result is only useful if it can be looked at, and these files are too
 * large to open casually: the PANDA toy network is 3.1MB and a real one is
 * far bigger. Previews are capped by the daemon and say so, and the pane says
 * it too rather than quietly showing the top of a file as if it were all of
 * it.
 */
import { useCallback, useEffect, useRef, useState } from "react";

import { DaemonConfig } from "../../transport/daemon";
import {
  Listing,
  OutputOwner,
  Preview,
  formatBytes,
  listDirectory,
  outputProvenance,
  previewFile,
} from "../../transport/files";
import { TagChips } from "../sessions/TagEditor";

import { useTimeZone } from "../timeline/timeZone";
import { fullTime } from "../timeline/time";

function TablePreview({ preview }: { preview: Preview }) {
  return (
    <table className="fv__table">
      <thead>
        <tr>
          {preview.columns.map((column, index) => (
            <th key={`${column}-${index}`}>{column}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {preview.rows.map((row, rowIndex) => (
          <tr key={rowIndex}>
            {row.map((cell, cellIndex) => (
              <td key={cellIndex}>{cell}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function PreviewBody({ preview }: { preview: Preview }) {
  switch (preview.kind) {
    case "table":
      return <TablePreview preview={preview} />;
    case "text":
      return <pre className="fv__text">{preview.text}</pre>;
    case "arrays":
      return (
        <table className="fv__table">
          <thead>
            <tr>
              <th>array</th>
              <th>shape</th>
              <th>dtype</th>
            </tr>
          </thead>
          <tbody>
            {preview.arrays.map((array) => (
              <tr key={array.name}>
                <td>{array.name}</td>
                <td>{array.shape.join(" × ")}</td>
                <td>{array.dtype}</td>
              </tr>
            ))}
          </tbody>
        </table>
      );
    default:
      return <div className="fv__none">{preview.note}</div>;
  }
}

/** Which saved session wrote this file, so a result leads back to its experiment. */
function Provenance({ config, path, onOpenSession }: { config: DaemonConfig; path: string; onOpenSession?: (id: string) => void }) {
  const [owners, setOwners] = useState<OutputOwner[] | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    setOwners(null);
    outputProvenance(config, path, controller.signal).then((body) => setOwners(body.sessions)).catch(() => setOwners([]));
    return () => controller.abort();
  }, [config, path]);
  if (!owners || owners.length === 0) return null;
  const [latest, ...earlier] = owners;
  return (
    <div className="fv__origin">
      <span>From session</span>
      <button type="button" className="fv__origin-link" disabled={!onOpenSession}
        title={`Open session ${latest.session_id}`} onClick={() => onOpenSession?.(latest.session_id)}>
        {latest.title || latest.session_id}
      </button>
      <code>{latest.session_id}</code>
      {latest.workflow ? <span className="fv__origin-meta">{latest.workflow}</span> : null}
      <TagChips tags={latest.tags} />
      {earlier.length ? (
        <span className="fv__origin-warn" title={earlier.map((item) => `${item.session_id} ${item.title}`).join("\n")}>
          {earlier.length} earlier session{earlier.length === 1 ? "" : "s"} wrote the same path; this file is the latest version.
        </span>
      ) : null}
    </div>
  );
}

export function FilesPane({ config, initialPath, onOpenSession }: { config: DaemonConfig; initialPath?: string; onOpenSession?: (sessionId: string) => void }) {
  const { zone } = useTimeZone();
  const [listing, setListing] = useState<Listing | null>(null);
  const [preview, setPreview] = useState<Preview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [previewPage, setPreviewPage] = useState(0);
  const [previewOffsets, setPreviewOffsets] = useState([0]);
  const requestId = useRef(0);
  const scroll = useRef<HTMLDivElement>(null);

  const browse = useCallback(
    async (path: string, offset = 0) => {
      const request = ++requestId.current;
      setError(null); setPreview(null); setBusy(true);
      try {
        const result = await listDirectory(config, path, offset, 100);
        if (request === requestId.current) { setListing(result); scroll.current?.scrollTo?.({ top: 0, left: 0 }); }
      } catch (problem) {
        if (request === requestId.current) setError(problem instanceof Error ? problem.message : String(problem));
      } finally {
        if (request === requestId.current) setBusy(false);
      }
    }, [config],
  );

  useEffect(() => {
    setListing(null);
    let active = true;
    const directory = initialPath ? initialPath.split("/").slice(0, -1).join("/") : "";
    void browse(directory).then(() => { if (active && initialPath) void open(initialPath); });
    return () => { active = false; requestId.current += 1; };
  }, [browse, initialPath]);

  const open = async (path: string, offset = 0, version = "", page = 0) => {
    const request = ++requestId.current;
    setError(null); setBusy(true);
    try {
      const result = await previewFile(config, path, offset, version);
      if (request !== requestId.current) return;
      setPreview(result); setPreviewPage(page);
      scroll.current?.scrollTo?.({ top: 0, left: 0 });
      setPreviewOffsets((current) => page === 0 ? [0] : [...current.slice(0, page), offset]);
    } catch (problem) {
      if (request === requestId.current) setError(problem instanceof Error ? problem.message : String(problem));
    } finally {
      if (request === requestId.current) setBusy(false);
    }
  };

  // `listing.path` is project-relative and always starts at `outputs`; the
  // crumbs are what lies beyond it.
  const segments = listing ? listing.path.split("/").slice(1) : [];
  const crumbs = segments.map((name, index) => ({
    name,
    path: ["outputs", ...segments.slice(0, index + 1)].join("/"),
  }));

  return (
    <section className="pane">
      <header className="pane__header fv__header">
        <span>Outputs</span>
        <div className="fv__header-actions">
          {listing ? (
            <span className="pane__count">
              {listing.total === 0 ? "0 files" : `${listing.offset + 1}–${listing.offset + listing.entries.length} of ${listing.total.toLocaleString()}`}
            </span>
          ) : null}
          <button
            className="pane__action"
            type="button"
            disabled={busy}
            onClick={() => preview ? void open(preview.path) : void browse(listing?.path ?? "")}
            title={preview ? "Restart this file preview" : "Refresh this directory"}
          >
            Refresh
          </button>
        </div>
      </header>

      {/* Only shown once you are somewhere: at the root it would just repeat
          the pane's own title. Segments are relative to outputs/ and each one
          is a way back. */}
      {crumbs.length > 0 ? (
        <nav className="fl__where" title={listing?.host_path ?? ""}>
          <button type="button" onClick={() => void browse("")}>
            outputs
          </button>
          {crumbs.map((crumb) => (
            <span key={crumb.path}>
              <span className="fl__sep">/</span>
              <button type="button" onClick={() => void browse(crumb.path)}>
                {crumb.name}
              </button>
            </span>
          ))}
        </nav>
      ) : null}

      {preview && (preview.kind === "table" || preview.kind === "text") ? (
        <div className="fv__paging">
          <button className="btn btn--quiet btn--small" type="button" disabled={busy || previewPage === 0}
            onClick={() => void open(preview.path, previewOffsets[previewPage - 1], preview.version, previewPage - 1)}>Previous page</button>
          <span>Page {previewPage + 1}{preview.kind === "table" ? ` · ${preview.rows.length} rows` : ""}</span>
          <button className="btn btn--quiet btn--small" type="button" disabled={busy || preview.next_offset == null}
            onClick={() => preview.next_offset != null && void open(preview.path, preview.next_offset, preview.version, previewPage + 1)}>Next page</button>
        </div>
      ) : null}

      <div className="pane__scroll" ref={scroll} aria-busy={busy}>
        {busy ? <div className="fv__loading" role="status">Reading outputs…</div> : null}
        {error ? <div className="fv__error" role="alert">{error}</div> : null}

        {preview ? (
          <div className="fv">
            <div className="fv__head">
              <button className="btn btn--quiet btn--small" type="button" onClick={() => { requestId.current += 1; setBusy(false); setError(null); setPreview(null); }}>
                ← back
              </button>
              <span className="fv__name">{preview.path.split("/").pop()}</span>
            </div>
            <div className="fv__meta">
              {formatBytes(preview.size_bytes)}
              {preview.truncated ? ` · showing ${preview.note}` : ""}
            </div>
            <div className="fv__path" title={preview.host_path}>{preview.host_path}</div>
            <Provenance config={config} path={preview.path} onOpenSession={onOpenSession} />
            <PreviewBody preview={preview} />
          </div>
        ) : listing ? (
          <>
            <ul className="fl">
              {listing.entries.length === 0 ? (
                <li className="fl__empty">
                  Nothing here yet. Results the agent writes appear in this tree.
                </li>
              ) : null}
              {listing.entries.map((entry) => (
                <li key={entry.path}>
                  <button
                    className="fl__row"
                    title={`${entry.path}${entry.kind === "file" ? ` · Modified ${fullTime(new Date(entry.modified_at * 1000).toISOString(), zone)}` : ""}`}
                    type="button"
                    onClick={() =>
                      entry.kind === "directory" ? void browse(entry.path) : void open(entry.path)
                    }
                  >
                    <span className="fl__icon">{entry.kind === "directory" ? "▸" : "·"}</span>
                    <span className="fl__name">{entry.name}</span>
                    {entry.kind === "file" ? (
                      <span className="fl__size">{formatBytes(entry.size_bytes)}</span>
                    ) : null}
                  </button>
                </li>
              ))}
            </ul>
            {listing.total > listing.limit ? (
              <div className="fv__paging">
                <button className="btn btn--quiet btn--small" type="button" disabled={busy || listing.offset === 0}
                  onClick={() => void browse(listing.path, Math.max(0, listing.offset - listing.limit))}>Previous files</button>
                <span>Page {Math.floor(listing.offset / listing.limit) + 1}</span>
                <button className="btn btn--quiet btn--small" type="button" disabled={busy || !listing.has_more}
                  onClick={() => void browse(listing.path, listing.offset + listing.limit)}>Next files</button>
              </div>
            ) : null}
          </>
        ) : (
          <div className="pane__empty">Reading outputs…</div>
        )}
      </div>
    </section>
  );
}
