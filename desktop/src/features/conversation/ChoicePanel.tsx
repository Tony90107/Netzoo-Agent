/**
 * The last reply's question, as options — and what to do next.
 *
 * Modelled on the question prompts of terminal coding agents: a short header,
 * the question, numbered options with one line on what each gives you, the
 * best-supported first, and a last row for an answer in your own words. Keys
 * work the way they do there: arrows move, Enter or a digit picks, and any
 * other key starts that typed answer.
 *
 * Every option sends plain text the agent's prompt already accepts (the same
 * text the terminal accepts), so this panel adds no path around the agent's
 * own rules: "Execute this plan" still stops at the explicit approval, and a
 * typed answer is read like any other reply to the question.
 */
import { KeyboardEvent, useEffect, useRef, useState } from "react";

import { ReplyCard, ReplyOption } from "../../transport/protocol";

type Props = {
  card: ReplyCard;
  onAnswer: (text: string) => void;
  onOpenOutputs?: (paths: string[]) => void;
};

const OWN_ANSWER = "Type your own answer";

function Badge({ option }: { option: ReplyOption }) {
  if (!option.badge) return null;
  const title = option.badge === "Recommended"
    ? "Recommended from what you stated about your study."
    : "The only option whose output matches everything you asked for.";
  return <span className={`cp__badge cp__badge--${option.badge === "Recommended" ? "rec" : "best"}`} title={title}>{option.badge}</span>;
}

function Options({ card, onAnswer }: Props) {
  // What cannot run here is listed once, with its reason, in the card above.
  const options = (card.choices?.options ?? []).filter((option) => option.available);
  // The row after the options takes an answer in the user's own words, like
  // the "Other" row of those prompts. Its index is -1 when the card allows none.
  const own = card.choices?.allow_other === false ? -1 : options.length;
  const count = options.length + (own >= 0 ? 1 : 0);
  const [active, setActive] = useState(0);
  const [draft, setDraft] = useState("");
  const refs = useRef<(HTMLButtonElement | null)[]>([]);
  const ownRef = useRef<HTMLTextAreaElement>(null);
  const signature = options.map((option) => option.key).join("|");
  const typing = active === own;

  useEffect(() => {
    setActive(0);
    setDraft("");
    refs.current[0]?.focus({ preventScroll: true });
  }, [signature]);

  useEffect(() => {
    const field = ownRef.current;
    if (!typing || !field) return;
    field.focus();
    field.setSelectionRange(field.value.length, field.value.length);
  }, [typing]);

  const move = (index: number) => {
    const next = (index + count) % count;
    setActive(next);
    if (next !== own) refs.current[next]?.focus();
  };

  const send = () => {
    const text = draft.trim();
    if (!text) return;
    setDraft("");
    onAnswer(text);
  };

  const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.target === ownRef.current) return;
    if (event.metaKey || event.ctrlKey || event.altKey) return;
    if (event.key === "ArrowDown") { event.preventDefault(); move(active + 1); return; }
    if (event.key === "ArrowUp") { event.preventDefault(); move(active - 1); return; }
    if (event.key === "Home") { event.preventDefault(); move(0); return; }
    if (event.key === "End") { event.preventDefault(); move(count - 1); return; }
    if (/^[1-9]$/.test(event.key)) {
      const index = Number(event.key) - 1;
      if (index === own) { event.preventDefault(); move(own); return; }
      const picked = options[index];
      if (picked) { event.preventDefault(); onAnswer(picked.answer); }
      return;
    }
    if (own >= 0 && event.key.length === 1 && event.key !== " ") {
      // Any other key starts the typed answer, with that key as its first letter.
      event.preventDefault();
      setDraft((text) => text + event.key);
      move(own);
    }
  };

  const onOwnKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.nativeEvent.isComposing) return;
    // Enter sends and Shift-Enter is a newline, as in the message box below.
    if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); send(); return; }
    if (event.key === "Escape") { event.preventDefault(); move(own - 1); return; }
    if (!draft && (event.key === "ArrowUp" || event.key === "ArrowDown")) {
      event.preventDefault();
      move(active + (event.key === "ArrowDown" ? 1 : -1));
    }
  };

  if (!card.choices || options.length === 0) return null;
  return (
    <div className="cp__question">
      <div className="cp__head">
        <span className="cp__chip">{card.choices.header}</span>
        <span className="cp__title">{card.choices.question}</span>
      </div>
      {card.choices.ordering ? <div className="cp__ordering">{card.choices.ordering}</div> : null}
      <div className="cp__list" role="group" aria-label={card.choices.question} onKeyDown={onKeyDown}>
        {options.map((option, index) => (
          <button
            key={option.key}
            ref={(node) => { refs.current[index] = node; }}
            type="button"
            className={`cp__option${index === active ? " is-active" : ""}${option.badge ? " has-badge" : ""}`}
            tabIndex={index === active ? 0 : -1}
            onFocus={() => setActive(index)}
            onClick={() => onAnswer(option.answer)}
          >
            <span className="cp__num" aria-hidden="true">{index + 1}</span>
            <span className="cp__body">
              <span className="cp__label">{option.label}<Badge option={option} /></span>
              {option.description ? <span className="cp__desc">{option.description}</span> : null}
            </span>
          </button>
        ))}
        {own >= 0 && typing ? (
          <div className="cp__option cp__option--own is-active">
            <span className="cp__num" aria-hidden="true">{own + 1}</span>
            <span className="cp__body">
              <span className="cp__label">{OWN_ANSWER}</span>
              <textarea
                ref={ownRef}
                className="cp__own"
                rows={2}
                value={draft}
                placeholder="Say what you want, then press Enter"
                aria-label={OWN_ANSWER}
                onChange={(event) => setDraft(event.target.value)}
                onKeyDown={onOwnKeyDown}
              />
            </span>
            <button type="button" className="btn btn--primary btn--small cp__send" disabled={!draft.trim()} onClick={send}>
              Send
            </button>
          </div>
        ) : own >= 0 ? (
          <button type="button" className="cp__option cp__option--own" tabIndex={-1} onClick={() => move(own)}>
            <span className="cp__num" aria-hidden="true">{own + 1}</span>
            <span className="cp__body">
              <span className="cp__label">{OWN_ANSWER}</span>
              <span className="cp__desc">
                {draft ? `Draft: ${draft}` : "Not listed? Describe what you want; it is read together with your request above."}
              </span>
            </span>
          </button>
        ) : null}
      </div>
      <div className="cp__hint">
        <kbd>↑</kbd><kbd>↓</kbd> move · <kbd>Enter</kbd> or <kbd>1</kbd>–<kbd>{Math.min(count, 9)}</kbd> choose
        {own >= 0 ? " · or just start typing your own answer" : null}
      </div>
    </div>
  );
}

function NextSteps({ card, onAnswer, onOpenOutputs }: Props) {
  const steps = card.next_steps.filter((step) => step.available && step.resolution !== "none");
  if (steps.length === 0) return null;
  const primary = steps.find((step) => step.key === "execute") ?? steps.find((step) => step.resolution === "plan_workflow");
  return (
    <div className="cp__next" role="group" aria-label="Next steps">
      <span className="cp__next-label">Next</span>
      {steps.map((step) => (
        <button
          key={step.key}
          type="button"
          className={`btn btn--small${step === primary ? " btn--primary" : step.key === "new-task" ? " btn--quiet" : ""}`}
          aria-label={step.label}
          title={step.description}
          onClick={() => (step.resolution === "open_outputs" ? onOpenOutputs?.(step.paths) : onAnswer(step.answer))}
        >
          {step.label}
        </button>
      ))}
    </div>
  );
}

export function ChoicePanel(props: Props) {
  const hasChoices = Boolean(props.card.choices?.options.some((option) => option.available));
  const hasSteps = props.card.next_steps.some((step) => step.available && step.resolution !== "none");
  if (!hasChoices && !hasSteps) return null;
  return (
    <div className={`cp${hasChoices ? " cp--question" : ""}`}>
      <Options {...props} />
      <NextSteps {...props} />
    </div>
  );
}
