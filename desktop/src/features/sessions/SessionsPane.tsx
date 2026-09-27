/**
 * What has been asked before, and a way back into it.
 *
 * The list is read from the same checkpoints the terminal writes, so a
 * session started in one can be resumed in the other. Only a session the
 * agent paused mid-question can be resumed; the rest are history, and the
 * pane says which is which rather than offering a button that would fail.
 */
import { useEffect, useState } from "react";

import { DaemonConfig } from "../../transport/daemon";
import { SessionSummary, listSessions, type SessionFilter } from "../../transport/files";

import { useTimeZone } from "../timeline/timeZone";
import { fullTime } from "../timeline/time";

function when(seconds: number): string {
  const elapsed = Date.now() / 1000 - seconds;
  if (elapsed < 60) return "just now";
  if (elapsed < 3600) return `${Math.floor(elapsed / 60)}m ago`;
  if (elapsed < 86400) return `${Math.floor(elapsed / 3600)}h ago`;
  return `${Math.floor(elapsed / 86400)}d ago`;
}

const STATUS_LABELS: Record<string, string> = {
  needs_input: "Needs input", needs_confirmation: "Needs approval", completed: "Completed",
  failed: "Failed", dry_run: "Preview only", ready: "Plan ready", respond_only: "Conversation", unknown: "Unknown",
};

export function SessionsPane({
  config,
  currentId,
  selectedId,
  onResume,
  onOpen,
  refreshToken,
}: {
  config: DaemonConfig;
  currentId: string | null;
  selectedId: string | null;
  onResume: (sessionId: string) => void;
  onOpen: (sessionId: string) => void;
  refreshToken?: boolean;
}) {
  const { zone } = useTimeZone();
  const [sessions, setSessions] = useState<SessionSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<SessionFilter>("all");
  const [offset, setOffset] = useState(0);
  const [nextOffset, setNextOffset] = useState<number | null>(null);
  const [revision, setRevision] = useState(0);
  const [loading, setLoading] = useState(true);

  // A fresh checkpoint can move to the top or change its saved state. Refresh
  // from the first page instead of appending an outdated later page.
  useEffect(() => { setOffset(0); }, [config, currentId, refreshToken]);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError(null);
    const timer = window.setTimeout(() => {
      void listSessions(config, { query, status, offset }, controller.signal).then((page) => {
        if (controller.signal.aborted) return;
        setSessions((old) => offset ? [...(old ?? []).filter((item) => !page.sessions.some((next) => next.session_id === item.session_id)), ...page.sessions] : page.sessions);
        setNextOffset(page.next_offset);
      }).catch((problem) => {
        if (!controller.signal.aborted) setError(problem instanceof Error ? problem.message : String(problem));
      }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    }, query.trim() ? 200 : 0);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [config, currentId, query, status, offset, revision, refreshToken]);

  return (
    <section className="pane">
      <header className="pane__header">
        Sessions
        <button className="pane__action" type="button" disabled={loading} onClick={() => { setOffset(0); setRevision((value) => value + 1); }}>
          refresh
        </button>
      </header>
      <div className="sl__controls">
        <label>Search sessions<input type="search" maxLength={200} placeholder="Request, workflow or ID" value={query} onChange={(event) => { setQuery(event.target.value); setOffset(0); }} /></label>
        <label>Latest saved state<select value={status} onChange={(event) => { setStatus(event.target.value as SessionFilter); setOffset(0); }}>
          <option value="all">All states</option><option value="needs_input">Needs input</option><option value="needs_confirmation">Needs approval</option>
          <option value="failed">Failed</option><option value="completed">Completed</option><option value="dry_run">Preview only</option>
        </select></label>
      </div>
      <div className="pane__scroll">
        {error ? <div className="fv__error" role="alert">{error}</div> : null}
        {(loading && offset === 0) || sessions === null ? (
          <div className="pane__empty" role="status">{error ? "History could not be loaded. Use refresh to try again." : "Reading history…"}</div>
        ) : sessions.length === 0 ? (
          <div className="pane__empty">{query || status !== "all" ? "No matching sessions. Try another search or clear the filters." : "No earlier sessions."}</div>
        ) : (
          <ul className="sl">
            {sessions.map((session) => (
              <li
                key={session.session_id}
                className={`sl__item${
                  session.session_id === currentId ? " is-current" : ""
                }${session.session_id === selectedId ? " is-selected" : ""}`}
              >
                <button
                  className="sl__open"
                  type="button"
                  title="Read this session"
                  aria-current={session.session_id === selectedId ? "page" : undefined}
                  onClick={() => onOpen(session.session_id)}
                >
                  <span className="sl__title">
                    {session.title || "(no request recorded)"}
                  </span>
                  <span className="sl__meta">
                    <span>{session.workflow || "—"}</span>
                    <span title={fullTime(new Date(session.updated_at * 1000).toISOString(), zone)}>{when(session.updated_at)}</span>
                    {session.total_tokens > 0 ? (
                      <span>{session.total_tokens.toLocaleString()}t</span>
                    ) : null}
                  </span>
                </button>
                {session.resumable && session.session_id !== currentId ? (
                  <button
                    className="btn btn--quiet btn--small"
                    type="button"
                    title="Reopen this session where the agent left off"
                    onClick={() => onResume(session.session_id)}
                  >
                    Resume
                  </button>
                ) : (
                  <span className="sl__status">
                    {session.session_id === currentId ? "Current" : STATUS_LABELS[session.status] ?? session.status.replace(/_/g, " ")}
                  </span>
                )}
              </li>
            ))}
          </ul>
        )}
        {nextOffset !== null && !error && (!loading || offset > 0) ? <div className="sl__more"><button className="btn btn--quiet btn--small" disabled={loading} type="button" onClick={() => setOffset(nextOffset)}>{loading ? "Loading…" : "Load older sessions"}</button></div> : null}
      </div>
    </section>
  );
}
