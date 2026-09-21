/**
 * The outputs browser.
 *
 * A result is only useful if it can be looked at, and these files are too
 * large to open casually: the PANDA toy network is 3.1MB and a real one is
 * far bigger. Previews are capped by the daemon and say so, and the pane says
 * it too rather than quietly showing the top of a file as if it were all of
 * it.
 */
import { useCallback, useEffect, useState } from "react";

import { DaemonConfig } from "../../transport/daemon";
import {
  Listing,
  Preview,
  formatBytes,
  listDirectory,
  previewFile,
} from "../../transport/files";

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

export function FilesPane({ config }: { config: DaemonConfig }) {
  const [listing, setListing] = useState<Listing | null>(null);
  const [preview, setPreview] = useState<Preview | null>(null);
  const [error, setError] = useState<string | null>(null);

  const browse = useCallback(
    async (path: string) => {
      setError(null);
      setPreview(null);
      try {
        setListing(await listDirectory(config, path));
      } catch (problem) {
        setError(problem instanceof Error ? problem.message : String(problem));
      }
    },
    [config],
  );

  useEffect(() => {
    void browse("");
  }, [browse]);

  const open = async (path: string) => {
    setError(null);
    try {
      setPreview(await previewFile(config, path));
    } catch (problem) {
      setError(problem instanceof Error ? problem.message : String(problem));
    }
  };

  const parent = listing && listing.path.includes("/")
    ? listing.path.slice(0, listing.path.lastIndexOf("/"))
    : null;

  return (
    <section className="pane">
      <header className="pane__header">
        Outputs
        <button
          className="pane__action"
          type="button"
          onClick={() => void browse(listing?.path ?? "")}
          title="Re-read this directory"
        >
          refresh
        </button>
      </header>

      {/* Where you are. "Files" alone did not say these are the agent's own
          results, nor which directory you had navigated into. */}
      <div className="fl__where" title={listing?.host_path ?? ""}>
        {listing ? listing.path : "outputs"}
      </div>

      <div className="pane__scroll">
        {error ? <div className="fv__error">{error}</div> : null}

        {preview ? (
          <div className="fv">
            <div className="fv__head">
              <button className="btn btn--quiet btn--small" type="button" onClick={() => setPreview(null)}>
                ← back
              </button>
              <span className="fv__name">{preview.path.split("/").pop()}</span>
            </div>
            <div className="fv__meta">
              {formatBytes(preview.size_bytes)}
              {preview.truncated ? ` · showing ${preview.note}` : ""}
            </div>
            <div className="fv__path" title={preview.host_path}>{preview.host_path}</div>
            <PreviewBody preview={preview} />
          </div>
        ) : listing ? (
          <ul className="fl">
            {parent !== null ? (
              <li>
                <button className="fl__row" type="button" onClick={() => void browse(parent)}>
                  <span className="fl__icon">↰</span>
                  <span className="fl__name">..</span>
                </button>
              </li>
            ) : null}
            {listing.entries.length === 0 ? (
              <li className="fl__empty">
                Nothing here yet. Results the agent writes appear in this tree.
              </li>
            ) : null}
            {listing.entries.map((entry) => (
              <li key={entry.path}>
                <button
                  className="fl__row"
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
        ) : (
          <div className="pane__empty">Reading outputs…</div>
        )}
      </div>
    </section>
  );
}
