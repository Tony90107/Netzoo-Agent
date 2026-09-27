/**
 * An earlier session, as it was left.
 *
 * Read-only: this is a checkpoint, not a live session, so there is nothing to
 * type into. The one action it offers is the one that makes sense — reopening
 * a session the agent paused mid-question — and only when that is true.
 *
 * `save_session` compacts long runs, so what is here is what the agent kept.
 * The view says so rather than presenting a trimmed history as complete.
 */
import { useEffect, useState } from "react";

import { Markdown } from "../conversation/Markdown";
import { DaemonConfig } from "../../transport/daemon";
import { Transcript, readTranscript } from "../../transport/files";
import { HistoricalActivity } from "./HistoricalActivity";

export function TranscriptView({
  config,
  sessionId,
  onClose,
  onResume,
  onOpenOutput,
}: {
  config: DaemonConfig;
  sessionId: string;
  onClose: () => void;
  onResume: (sessionId: string) => void;
  onOpenOutput?: (path: string) => void;
}) {
  const [transcript, setTranscript] = useState<Transcript | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<"conversation" | "activity">("conversation");

  useEffect(() => {
    let current = true;
    setTranscript(null);
    setError(null);
    readTranscript(config, sessionId)
      .then((value) => { if (current) setTranscript(value); })
      .catch((problem) => { if (current) setError(String(problem)); });
    return () => { current = false; };
  }, [config, sessionId]);

  return (
    <section className="pane pane--wide">
      <header className="pane__header">
        Earlier session
        <span className="pane__badge">{sessionId}</span>
        <button className="pane__action" type="button" onClick={onClose}>
          close
        </button>
      </header>

      <nav className="workspace__tabs" role="group" aria-label="Saved session views">
        <button type="button" aria-pressed={tab === "conversation"} onClick={() => setTab("conversation")}>Conversation</button>
        <button type="button" aria-pressed={tab === "activity"} onClick={() => setTab("activity")}>Activity</button>
      </nav>
      {tab === "activity" ? <HistoricalActivity key={sessionId} config={config} sessionId={sessionId} onOpenOutput={onOpenOutput} /> : <div className="thread">
        {error ? <div className="fv__error">{error}</div> : null}
        {transcript === null && !error ? (
          <div className="thread__empty">Reading the checkpoint…</div>
        ) : null}
        {transcript?.truncated ? (
          <div className="bubble bubble--notice">
            Long runs are compacted when they are saved, so this is what the
            agent kept rather than every turn.
          </div>
        ) : null}
        {transcript?.messages.length === 0 ? (
          <div className="thread__empty">This session has no saved messages.</div>
        ) : null}
        {transcript?.messages.map((message, index) => (
          <div
            key={index}
            className={`bubble bubble--${message.role === "user" ? "user" : "agent"}`}
          >
            <div className="bubble__body">{message.role === "user" ? message.content : <Markdown>{message.content}</Markdown>}</div>
          </div>
        ))}
      </div>}

      <div className={`composer-slot${transcript?.resumable ? "" : " composer-slot--readonly"}`}>
        {transcript?.resumable ? (
          <div className="main-input">
            <p className="main-input__question">
              The agent stopped here waiting for an answer. Reopening continues
              from that question.
            </p>
            <button
              className="btn btn--primary"
              type="button"
              onClick={() => onResume(sessionId)}
            >
              Resume this session
            </button>
          </div>
        ) : (
          <div className="composer composer--busy">
            Saved session · read-only. Use Activity to review execution results.
          </div>
        )}
      </div>
    </section>
  );
}
