/**
 * Outputs, one entry per session, the most recently written first.
 *
 * One session is one experiment, so its results are one entry. A session with
 * one result is that file, opened directly; the manifest and execution record
 * every run writes beside it are one click away ("+2 run files"), not a
 * folder around it. A session with several results is one folder holding only
 * that session's files, results first. Files no saved session wrote stay
 * reachable from the folder view.
 */
import { useEffect, useState } from "react";

import { DaemonConfig } from "../../transport/daemon";
import { OutputsIndex, SessionOutputs, formatBytes, listSessionOutputs } from "../../transport/files";
import { fullTime, relativeTime } from "../timeline/time";
import { useTimeZone } from "../timeline/timeZone";

function label(entry: SessionOutputs): string {
  return entry.name || entry.title || `Session ${entry.session_id}`;
}

/** The one file an entry stands for, if it has one, and the files beside it. */
function shape(entry: SessionOutputs) {
  const results = entry.files.filter((file) => file.result);
  const single = results.length === 1 ? results[0] : results.length === 0 && entry.files.length === 1 ? entry.files[0] : null;
  return { single, beside: single ? entry.files.filter((file) => file !== single) : entry.files };
}

export function OutputsBySession({
  config,
  refreshToken,
  revision = 0,
  onOpenFile,
  onOpenSession,
  onBrowseFolders,
  onCount,
}: {
  config: DaemonConfig;
  /** Changes when a turn ends, so a session that just wrote files shows up. */
  refreshToken?: boolean;
  /** Bumped by the pane's Refresh button. */
  revision?: number;
  onOpenFile: (path: string) => void;
  onOpenSession?: (sessionId: string) => void;
  onBrowseFolders: () => void;
  onCount?: (count: number) => void;
}) {
  const { zone } = useTimeZone();
  const [index, setIndex] = useState<OutputsIndex | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<Set<string> | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setError(null);
    listSessionOutputs(config, controller.signal).then((body) => {
      if (controller.signal.aborted) return;
      setIndex(body);
      onCount?.(body.sessions.length);
      // The newest folder starts open: it is usually the one just written.
      setExpanded((current) => current ?? new Set(body.sessions.slice(0, 1).filter((entry) => !shape(entry).single).map((entry) => entry.session_id)));
    }).catch((problem) => {
      if (!controller.signal.aborted) setError(problem instanceof Error ? problem.message : String(problem));
    });
    return () => controller.abort();
  }, [config, refreshToken, revision]);

  const toggle = (sessionId: string) => setExpanded((current) => {
    const next = new Set(current ?? []);
    if (next.has(sessionId)) next.delete(sessionId); else next.add(sessionId);
    return next;
  });

  if (error) return <div className="fv__error" role="alert">{error}</div>;
  if (!index) return <div className="pane__empty" role="status">Reading outputs…</div>;
  return (
    <div className="ob">
      {index.sessions.length === 0 ? (
        <div className="fl__empty">
          No session has written results yet. Each session's results appear here as one entry, the newest first.
        </div>
      ) : null}
      <ul className="fl ob__list">
        {index.sessions.map((entry) => {
          const { single, beside } = shape(entry);
          const open = Boolean(expanded?.has(entry.session_id)) && beside.length > 0;
          const when = relativeTime(entry.added_at);
          const at = fullTime(new Date(entry.added_at * 1000).toISOString(), zone);
          const size = entry.files.reduce((total, file) => total + file.size_bytes, 0);
          return (
            <li key={entry.session_id} className="ob__item">
              <div className="ob__line">
              <button
                type="button"
                className="fl__row ob__row"
                aria-expanded={single ? undefined : open}
                title={`${single ? single.path : entry.folder || entry.session_id} · written ${at}`}
                onClick={() => (single ? onOpenFile(single.path) : toggle(entry.session_id))}
              >
                <span className="fl__icon">{single ? "·" : open ? "▾" : "▸"}</span>
                <span className="ob__main">
                  <span className="ob__label">{label(entry)}</span>
                  <span className="ob__sub">{single ? single.name : `${entry.files.length} files`}</span>
                </span>
                <span className="ob__meta">{[entry.workflow, when].filter(Boolean).join(" · ")}</span>
                <span className="fl__size">{formatBytes(single ? single.size_bytes : size)}</span>
              </button>
              {single && beside.length ? (
                <button type="button" className="ob__more" aria-expanded={open} onClick={() => toggle(entry.session_id)}
                  title="The run's manifest and execution record, written beside the result">
                  {open ? "hide" : `+${beside.length} run file${beside.length === 1 ? "" : "s"}`}
                </button>
              ) : null}
              </div>
              {open ? (
                <ul className="ob__files">
                  {beside.map((file) => (
                    <li key={file.path}>
                      <button type="button" className="fl__row ob__file" title={file.path} onClick={() => onOpenFile(file.path)}>
                        <span className="fl__icon">·</span>
                        <span className="fl__name">{file.name}</span>
                        {file.result ? <span className="ob__badge">result</span> : null}
                        <span className="fl__size">{formatBytes(file.size_bytes)}</span>
                      </button>
                    </li>
                  ))}
                  {onOpenSession && entry.saved ? (
                    <li className="ob__actions">
                      <button type="button" className="btn btn--quiet btn--small" onClick={() => onOpenSession(entry.session_id)}>
                        Open the session
                      </button>
                    </li>
                  ) : null}
                </ul>
              ) : null}
            </li>
          );
        })}
      </ul>
      {index.other_files > 0 ? (
        <div className="ob__other">
          {index.other_files.toLocaleString()} other file{index.other_files === 1 ? " was" : "s were"} not written by a saved session.
          <button type="button" className="btn btn--quiet btn--small" onClick={onBrowseFolders}>Browse folders</button>
        </div>
      ) : null}
    </div>
  );
}
