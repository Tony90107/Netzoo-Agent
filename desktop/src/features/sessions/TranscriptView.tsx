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
import { ReplyCardView } from "../conversation/ReplyCardView";
import { DaemonConfig } from "../../transport/daemon";
import { Transcript, readTranscript } from "../../transport/files";
import { HistoricalActivity } from "./HistoricalActivity";
import { NotesEditor, SessionName } from "./SessionDetails";
import { TagEditor } from "./TagEditor";
import { userTurn } from "./userTurn";

/** What this experiment was: its name, model, tags and notes, and what it wrote. */
export function SessionFacts({ config, transcript, onOpenOutput, onChanged }: {
  config: DaemonConfig; transcript: Transcript; onOpenOutput?: (path: string) => void;
  /** Called after the name, notes or tags were saved, so lists can refresh. */
  onChanged?: () => void;
}) {
  const models = Object.entries(transcript.models ?? {});
  const outputs = transcript.outputs ?? [];
  return (
    <div className="sd">
      <div className="sd__row">
        <span className="sd__label">Name</span>
        <SessionName config={config} sessionId={transcript.session_id} name={transcript.name ?? ""} onSaved={() => onChanged?.()} />
        {transcript.name && transcript.title ? <span className="sd__muted" title={transcript.title}>asked: {transcript.title}</span> : null}
      </div>
      <div className="sd__row">
        <span className="sd__label">Model</span>
        <span>{models.length ? models.map(([role, name]) => `${role}: ${name.split("/").pop()}`).join(" · ") : "not recorded (session predates model tracking)"}</span>
      </div>
      <div className="sd__row">
        <span className="sd__label">Tags</span>
        <TagEditor config={config} sessionId={transcript.session_id} tags={transcript.tags ?? []} onSaved={() => onChanged?.()} />
      </div>
      <div className="sd__row sd__row--top">
        <span className="sd__label">Notes</span>
        <NotesEditor config={config} sessionId={transcript.session_id} notes={transcript.notes ?? ""} onSaved={() => onChanged?.()} />
      </div>
      <div className="sd__row">
        <span className="sd__label">Outputs</span>
        {outputs.length === 0 ? <span className="sd__muted">No files written{transcript.output_dir ? ` · folder ${transcript.output_dir}/` : ""}</span> : (
          <span className="sd__files">
            {outputs.slice(0, 8).map((path) => onOpenOutput ? (
              <button key={path} type="button" className="btn btn--quiet btn--small" title={path}
                onClick={() => onOpenOutput(path)}>{path.split("/").pop()}</button>
            ) : <code key={path}>{path}</code>)}
            {outputs.length > 8 ? <span className="sd__muted">+{outputs.length - 8} more</span> : null}
          </span>
        )}
      </div>
    </div>
  );
}

export function TranscriptView({
  config,
  sessionId,
  onClose,
  onResume,
  onOpenOutput,
  onChanged,
}: {
  config: DaemonConfig;
  sessionId: string;
  onClose: () => void;
  onResume: (sessionId: string) => void;
  onOpenOutput?: (path: string) => void;
  onChanged?: () => void;
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

      {transcript ? <SessionFacts config={config} transcript={transcript} onOpenOutput={onOpenOutput} onChanged={onChanged} /> : null}
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
            {message.role === "user" ? (() => {
              const turn = userTurn(message.content);
              return (
                <div className="bubble__body bubble__body--plain" title={turn.kind === "said" ? undefined : message.content}>
                  {turn.kind === "chose" ? <span className="bubble__tag">Option</span> : turn.kind === "follow_up" ? <span className="bubble__tag">Follow-up</span> : null}
                  {turn.text}
                </div>
              );
            })() : <div className="bubble__body">{message.card
              ? <ReplyCardView card={message.card} text={message.content} />
              : <Markdown>{message.content}</Markdown>}</div>}
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
