/**
 * The conversation thread plus whatever the agent is currently asking for.
 */
import { useEffect, useRef } from "react";

import { Entry, SessionState } from "../../transport/session";
import { Markdown } from "./Markdown";
import { InputArea } from "./InputArea";
import { ModeSwitch } from "./ModeSwitch";
import { ReplyCardView } from "./ReplyCardView";

function Bubble({ entry }: { entry: Entry }) {
  if (entry.kind === "error") {
    return (
      <div className="bubble bubble--error">
        <div className="bubble__label">{entry.errorType}</div>
        <div className="bubble__body"><Markdown>{entry.text}</Markdown></div>
      </div>
    );
  }
  return (
    <div className={`bubble bubble--${entry.kind}${entry.kind === "agent" && entry.card?.headline ? " bubble--card" : ""}`}>
      <div className={`bubble__body${entry.kind === "user" ? " bubble__body--plain" : ""}`}>
        {entry.kind === "user"
          ? entry.text
          : entry.kind === "agent" && entry.card
            ? <ReplyCardView card={entry.card} text={entry.text} />
            : <Markdown>{entry.text}</Markdown>}
      </div>
    </div>
  );
}

type Props = {
  session: SessionState;
  onAnswer: (text: string) => void;
  onSlash: (command: string) => void;
  onApprove: (planHash: string) => void;
  onDecline: () => void;
  onCancel: () => void;
  onOpenOutputs?: (paths: string[]) => void;
};

export function Conversation({
  session,
  onAnswer,
  onSlash,
  onApprove,
  onDecline,
  onCancel,
  onOpenOutputs,
}: Props) {
  const tail = useRef<HTMLDivElement>(null);

  useEffect(() => {
    tail.current?.scrollIntoView({ behavior: window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "end" });
  }, [session.entries.length, session.busy, session.view]);

  return (
    <section className="pane pane--wide">
      <header className="pane__header">
        Conversation
        <button className="btn btn--quiet btn--small" type="button" disabled={session.busy || session.stopped || !session.view}
          title="Check the running agent environment without executing a workflow" onClick={() => onSlash("/doctor")}>/doctor</button>
        <ModeSwitch
          mode={session.view?.mode}
          disabled={session.busy || session.stopped || !session.view}
          onSelect={onSlash}
        />
      </header>

      <div className="thread">
        {session.entries.length === 0 && !session.busy ? (
          <div className="thread__empty">
            Describe a NetZoo goal, or ask how a workflow works.
            <br />
            Nothing runs until you approve a plan.
          </div>
        ) : null}
        {session.entries.map((entry) => (
          <Bubble key={entry.id} entry={entry} />
        ))}
        {session.busy ? (
          <div className="thread__progress">
            <span className="thread__spinner" aria-hidden="true" />
            {session.progress ?? "Working…"}
            <button
              className="btn btn--quiet btn--small"
              type="button"
              // Interrupting ends the session, the same way Ctrl-C does in the
              // terminal. Say so here rather than surprising someone with it.
              title="Stop this turn. Nothing unfinished is reported as completed, and the session ends."
              onClick={onCancel}
            >
              Interrupt
            </button>
          </div>
        ) : null}
        <div ref={tail} />
      </div>

      <div className="composer-slot">
        {session.stopped ? (
          <div className="composer composer--busy">This session has ended.</div>
        ) : session.view || session.busy ? (
          <InputArea
            // A null view while busy is the locked state; InputArea reads busy first.
            view={session.view ?? ({ prompt_kind: "main" } as never)}
            busy={session.busy}
            onAnswer={onAnswer}
            onApprove={onApprove}
            onDecline={onDecline}
            onOpenOutputs={onOpenOutputs}
          />
        ) : (
          <div className="composer composer--busy">Connecting…</div>
        )}
      </div>
    </section>
  );
}
