/**
 * The last reply's question, as options — and what to do next.
 *
 * Modelled on the question prompts of terminal coding agents: a short header,
 * the question, numbered options with one line on what each gives you, the
 * best-supported first. Keys work the way they do there: arrows move, Enter
 * or a digit picks, and any other key starts typing your own answer.
 *
 * Every option sends plain text the agent's prompt already accepts (the same
 * text the terminal accepts), so this panel adds no path around the agent's
 * own rules: "Execute this plan" still stops at the explicit approval.
 */
import { KeyboardEvent, useEffect, useRef, useState } from "react";

import { ReplyCard, ReplyOption } from "../../transport/protocol";

type Props = {
  card: ReplyCard;
  onAnswer: (text: string) => void;
  onOpenOutputs?: (paths: string[]) => void;
  /** Focus the free-text box; called when a key starts a typed answer. */
  onType?: () => void;
};

function Badge({ option }: { option: ReplyOption }) {
  if (!option.badge) return null;
  const title = option.badge === "Recommended"
    ? "Recommended from what you stated about your study."
    : "The only option whose output matches everything you asked for.";
  return <span className={`cp__badge cp__badge--${option.badge === "Recommended" ? "rec" : "best"}`} title={title}>{option.badge}</span>;
}

function Options({ card, onAnswer, onType }: Props) {
  const options = (card.choices?.options ?? []).filter((option) => option.available);
  const blocked = card.unavailable;
  const [active, setActive] = useState(0);
  const refs = useRef<(HTMLButtonElement | null)[]>([]);
  const signature = options.map((option) => option.key).join("|");

  useEffect(() => {
    setActive(0);
    refs.current[0]?.focus({ preventScroll: true });
  }, [signature]);

  const move = (index: number) => {
    const next = (index + options.length) % options.length;
    setActive(next);
    refs.current[next]?.focus();
  };

  const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.metaKey || event.ctrlKey || event.altKey) return;
    if (event.key === "ArrowDown") { event.preventDefault(); move(active + 1); return; }
    if (event.key === "ArrowUp") { event.preventDefault(); move(active - 1); return; }
    if (event.key === "Home") { event.preventDefault(); move(0); return; }
    if (event.key === "End") { event.preventDefault(); move(options.length - 1); return; }
    if (/^[1-9]$/.test(event.key)) {
      const picked = options[Number(event.key) - 1];
      if (picked) { event.preventDefault(); onAnswer(picked.answer); }
      return;
    }
    if (event.key === "Escape" || (event.key.length === 1 && event.key !== " ")) onType?.();
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
        {blocked.map((option) => (
          <div key={option.key} className="cp__option cp__option--blocked" aria-disabled="true">
            <span className="cp__num" aria-hidden="true">✕</span>
            <span className="cp__body">
              <span className="cp__label">{option.label}<span className="cp__badge cp__badge--off">Not available here</span></span>
              <span className="cp__desc">{option.reason || option.description}</span>
            </span>
          </div>
        ))}
      </div>
      <div className="cp__hint">
        <kbd>↑</kbd><kbd>↓</kbd> move · <kbd>Enter</kbd> or <kbd>1</kbd>–<kbd>{Math.min(options.length, 9)}</kbd> choose · start typing to answer in your own words
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
