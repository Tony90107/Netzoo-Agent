/**
 * A Markdown output -- usually a run report -- in a window of its own:
 * readable by default, its Markdown source one click away.
 *
 * The file is read through the same capped preview as every other output, so
 * a large one is never loaded whole, and the dialog says when it shows only
 * the start of it.
 */
import { useEffect, useRef, useState } from "react";

import { DaemonConfig } from "../../transport/daemon";
import { Preview, formatBytes, previewFile } from "../../transport/files";
import { ReportView, parseReport } from "./ReportView";

export function ReportDialog({
  config,
  path,
  onClose,
  onOpenFile,
}: {
  config: DaemonConfig;
  path: string;
  onClose: () => void;
  /** Opens an output the report names; the dialog closes first. */
  onOpenFile?: (path: string) => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [preview, setPreview] = useState<Preview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [source, setSource] = useState(false);

  useEffect(() => {
    const node = dialog.current;
    if (node && !node.open && typeof node.showModal === "function") node.showModal();
  }, []);

  useEffect(() => {
    let current = true;
    setPreview(null); setError(null);
    previewFile(config, path)
      .then((value) => { if (current) setPreview(value); })
      .catch((problem) => { if (current) setError(problem instanceof Error ? problem.message : String(problem)); });
    return () => { current = false; };
  }, [config, path]);

  const name = path.split("/").pop() ?? path;
  const isReport = preview ? parseReport(preview.text) !== null : /-execution-/.test(name);
  return (
    <dialog ref={dialog} className="rpt" aria-label={isReport ? "Run report" : name}
      onCancel={(event) => { event.preventDefault(); onClose(); }}>
      <header className="rpt__head">
        <div className="rpt__title">
          <span className="rpt__name">{isReport ? "Run report" : name}</span>
          <span className="rpt__file" title={path}>{name}{preview ? ` · ${formatBytes(preview.size_bytes)}` : ""}</span>
        </div>
        <div className="rpt__actions">
          <div className="fv__modes" role="group" aria-label="Show the file as">
            <button type="button" aria-pressed={!source} onClick={() => setSource(false)}>Readable</button>
            <button type="button" aria-pressed={source} onClick={() => setSource(true)}>Markdown source</button>
          </div>
          <button className="btn btn--small" type="button" onClick={onClose}>Close</button>
        </div>
      </header>
      <div className="rpt__body">
        {error ? <div className="fv__error" role="alert">{error}</div> : null}
        {!preview && !error ? <div className="pane__empty" role="status">Reading the report…</div> : null}
        {preview ? (source ? <pre className="fv__text">{preview.text}</pre> : (
          <ReportView text={preview.text} onOpenFile={onOpenFile ? (target) => { onClose(); onOpenFile(target); } : undefined} />
        )) : null}
        {preview?.truncated ? <p className="rpt__note">This shows {preview.note} of the file.</p> : null}
      </div>
    </dialog>
  );
}
