/**
 * What has been asked before, and a way back into it.
 *
 * The list is read from the same checkpoints the terminal writes, so a
 * session started in one can be resumed in the other. Only a session the
 * agent paused mid-question can be resumed; the rest are history, and the
 * pane says which is which rather than offering a button that would fail.
 */
import { useCallback, useEffect, useState } from "react";

import { DaemonConfig } from "../../transport/daemon";
import { SessionSummary, listSessions } from "../../transport/files";

function when(seconds: number): string {
  const elapsed = Date.now() / 1000 - seconds;
  if (elapsed < 60) return "just now";
  if (elapsed < 3600) return `${Math.floor(elapsed / 60)}m ago`;
  if (elapsed < 86400) return `${Math.floor(elapsed / 3600)}h ago`;
  return `${Math.floor(elapsed / 86400)}d ago`;
}

export function SessionsPane({
  config,
  currentId,
  onResume,
}: {
  config: DaemonConfig;
  currentId: string | null;
  onResume: (sessionId: string) => void;
}) {
  const [sessions, setSessions] = useState<SessionSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    try {
      setSessions((await listSessions(config)).sessions);
      setError(null);
    } catch (problem) {
      setError(problem instanceof Error ? problem.message : String(problem));
    }
  }, [config]);

  useEffect(() => {
    void reload();
  }, [reload, currentId]);

  return (
    <section className="pane">
      <header className="pane__header">
        Sessions
        <button className="pane__action" type="button" onClick={() => void reload()}>
          refresh
        </button>
      </header>
      <div className="pane__scroll">
        {error ? <div className="fv__error">{error}</div> : null}
        {sessions === null ? (
          <div className="pane__empty">Reading history…</div>
        ) : sessions.length === 0 ? (
          <div className="pane__empty">No earlier sessions.</div>
        ) : (
          <ul className="sl">
            {sessions.map((session) => (
              <li
                key={session.session_id}
                className={`sl__item${
                  session.session_id === currentId ? " is-current" : ""
                }`}
              >
                <div className="sl__title">{session.title || "(no request recorded)"}</div>
                <div className="sl__meta">
                  <span>{session.workflow || "—"}</span>
                  <span>{when(session.updated_at)}</span>
                  {session.total_tokens > 0 ? (
                    <span>{session.total_tokens.toLocaleString()}t</span>
                  ) : null}
                </div>
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
                    {session.session_id === currentId ? "current" : session.status}
                  </span>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
