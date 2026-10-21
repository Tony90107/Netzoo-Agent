/**
 * The conversation thread plus whatever the agent is currently asking for.
 */
import { useEffect, useRef } from "react";

import { Entry, entryTimestamp, SessionState } from "../../transport/session";
import { Splitter, usePaneSize } from "../../app/Splitter";
import { buildRuns, type ActivityRun } from "../timeline/model";
import { Markdown } from "./Markdown";
import { InputArea } from "./InputArea";
import { ModeSwitch } from "./ModeSwitch";
import { ReplyCardView } from "./ReplyCardView";
import { TurnActivity } from "./TurnActivity";

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
  const composerSlot = useRef<HTMLDivElement>(null);
  const followTail = useRef(true);
  const [choicesHeight, setChoicesHeight] = usePaneSize("choices-height", 320, 190, 1000);
  const hasChoices = !session.busy && session.view?.prompt_kind === "main" &&
    Boolean(session.view.card?.choices?.options.some((option) => option.available));
  const runs = buildRuns(session.trace);
  const items: ({ kind: "entry"; entry: Entry; at: number; order: number } | { kind: "run"; run: ActivityRun; at: number; order: number })[] = [
    ...session.entries.map((entry, order) => ({ kind: "entry" as const, entry, at: Date.parse(entryTimestamp(entry) ?? "") || 0, order })),
    ...runs.map((run, order) => ({ kind: "run" as const, run, at: Date.parse(run.startedAt) || 0, order })),
  ];
  items.sort((left, right) => left.at - right.at || (left.kind === "entry" ? 0 : 1) - (right.kind === "entry" ? 0 : 1) || left.order - right.order);

  useEffect(() => {
    if (followTail.current) tail.current?.scrollIntoView({ behavior: window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "end" });
  }, [session.entries.length, session.trace.length, session.busy, session.view]);

  return (
    <section className="pane pane--wide">
      <header className="pane__header">
        Conversation
        <ModeSwitch
          mode={session.view?.mode}
          disabled={session.busy || session.stopped || !session.view}
          onSelect={onSlash}
        />
      </header>

      <div className="thread" onScroll={(event) => {
        const node = event.currentTarget;
        followTail.current = node.scrollHeight - node.scrollTop - node.clientHeight < 100;
      }}>
        {session.entries.length === 0 && !session.busy ? (
          <div className="thread__empty">
            Describe a NetZoo goal, or ask how a workflow works.
            <br />
            Nothing runs until you approve a plan.
          </div>
        ) : null}
        {items.map((item) => item.kind === "entry"
          ? <Bubble key={`entry-${item.entry.id}`} entry={item.entry} />
          : <TurnActivity key={`run-${item.run.id}`} run={item.run} busy={session.busy && item.run.id === runs.at(-1)?.id} incomplete={session.missedEvents} />)}
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

      {hasChoices ? <Splitter
        orientation="horizontal"
        className="splitter--composer"
        label="Resize choices and conversation: drag or use arrow keys"
        onDelta={(delta) => setChoicesHeight((composerSlot.current?.getBoundingClientRect().height || choicesHeight) - delta)}
      /> : null}
      <div
        ref={composerSlot}
        className={`composer-slot${hasChoices ? " composer-slot--resizable" : ""}`}
        style={hasChoices ? { height: choicesHeight } : undefined}
      >
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
