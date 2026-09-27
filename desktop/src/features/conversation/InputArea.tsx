/**
 * The input area takes its shape from `view.prompt_kind`, never from a guess.
 *
 * Every branch here sends a string the terminal state machine already accepts,
 * because it is the same state machine. The candidate buttons send a 1-based
 * number and the bundle buttons send a 1-based index, which is exactly what
 * `parse_clarification_assignments` and `bundle_clarification_continuation`
 * read; `field=value` is rejected by the wizard, so it is never sent.
 *
 * Execution is the one flow with its own controls. Asking for a preview and
 * approving it stay two separate acts, and the approval names the plan it
 * approves so the daemon can refuse a stale one.
 */
import { useEffect, useRef, useState } from "react";

import { ViewPayload } from "../../transport/protocol";
import { Markdown } from "./Markdown";

type Props = {
  view: ViewPayload;
  busy: boolean;
  onAnswer: (text: string) => void;
  onApprove: (planHash: string) => void;
  onDecline: () => void;
};

function FreeText({
  placeholder,
  submitLabel,
  onSubmit,
  autoFocus = true,
}: {
  placeholder: string;
  submitLabel: string;
  onSubmit: (text: string) => void;
  autoFocus?: boolean;
}) {
  const [text, setText] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (autoFocus) ref.current?.focus();
  }, [autoFocus]);

  const submit = () => {
    const trimmed = text.trim();
    if (!trimmed) return;
    setText("");
    onSubmit(trimmed);
  };

  return (
    <div className="composer">
      <textarea
        ref={ref}
        className="composer__text"
        rows={3}
        value={text}
        placeholder={placeholder}
        aria-label={placeholder}
        onChange={(event) => setText(event.target.value)}
        onKeyDown={(event) => {
          // Enter sends; Shift-Enter is a newline, matching the terminal's
          // single-submission behaviour for a pasted multi-line task.
          if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
            event.preventDefault();
            submit();
          }
        }}
      />
      <button className="btn btn--primary" type="button" onClick={submit}>
        {submitLabel}
      </button>
    </div>
  );
}

function Choices({
  title,
  options,
  onPick,
  extra,
  question,
}: {
  title: string;
  options: { key: string; label: string; detail?: string; answer: string }[];
  onPick: (answer: string) => void;
  extra?: React.ReactNode;
  question?: React.ReactNode;
}) {
  return (
    <div className="choices">
      {question}
      <div className="choices__title">{title}</div>
      <div className="choices__list">
        {options.map((option) => (
          <button
            key={option.key}
            className="choice"
            type="button"
            onClick={() => onPick(option.answer)}
          >
            <span className="choice__label">{option.label}</span>
            {option.detail ? <span className="choice__detail">{option.detail}</span> : null}
          </button>
        ))}
      </div>
      {extra}
    </div>
  );
}

/**
 * The agent's own wording for the current question.
 *
 * `view.text` is the exact string the terminal prints, mode prefix and all.
 * Showing it is what keeps the window honest: the reason an input was refused
 * lives there, and a UI that invented its own label would drop it.
 */
function AgentQuestion({ view }: { view: ViewPayload }) {
  const text = view.text
    .replace(/^\s*\[(Planning|Execute|Test)\]\s*/, "")
    .trim();
  if (!text) return null;
  return <Markdown className="agent-question">{text}</Markdown>;
}

export function InputArea({ view, busy, onAnswer, onApprove, onDecline }: Props) {
  if (busy) {
    return <div className="composer composer--busy">Working…</div>;
  }

  switch (view.prompt_kind) {
    case "execution_confirmation":
      return (
        <div className="approval">
          <div className="approval__title">
            Run the validated {view.plan?.workflow ?? "NetZoo"} workflow now?
          </div>
          <p className="approval__note">
            This executes the plan above once. The next prompt returns to Planning mode.
          </p>
          <div className="approval__actions">
            <button
              className="btn btn--danger"
              type="button"
              disabled={!view.plan_hash}
              onClick={() => view.plan_hash && onApprove(view.plan_hash)}
            >
              Execute this plan
            </button>
            <button className="btn" type="button" onClick={onDecline}>
              Cancel
            </button>
          </div>
        </div>
      );

    case "preference_confirmation":
      return (
        <Choices
          title="Save these preferences to your profile?"
          question={<AgentQuestion view={view} />}
          options={[
            { key: "yes", label: "Save", answer: "y" },
            { key: "no", label: "Do not save", answer: "n" },
          ]}
          onPick={onAnswer}
        />
      );

    case "input_confirmation":
      return (
        <Choices
          title="Use the inputs shown above?"
          question={<AgentQuestion view={view} />}
          options={[
            { key: "yes", label: "Yes, use these", answer: "y" },
            { key: "no", label: "No, let me correct them", answer: "n" },
          ]}
          onPick={onAnswer}
          extra={
            <FreeText
              autoFocus={false}
              placeholder="Or type corrected paths as field=path"
              submitLabel="Send"
              onSubmit={onAnswer}
            />
          }
        />
      );

    case "clarification": {
      const plan = view.plan;
      if (view.preflight_correction) {
        // A different mode: the plan has its inputs but they failed
        // validation, so the answer corrects them by name.
        return (
          <div className="wizard">
            <AgentQuestion view={view} />
            <FreeText
              placeholder="Corrected inputs, as field=path"
              submitLabel="Use these inputs"
              onSubmit={onAnswer}
            />
          </div>
        );
      }
      if (view.choosing_bundle && plan && plan.input_bundle_options.length > 0) {
        return (
          <Choices
            title="Choose one complete set of inputs"
            options={plan.input_bundle_options.map((bundle, index) => ({
              key: bundle.bundle_id,
              label: bundle.directory,
              detail: Object.entries(bundle.inputs)
                .map(([field, path]) => `${field}: ${path.split("/").pop()}`)
                .join(" · "),
              answer: String(index + 1),
            }))}
            onPick={onAnswer}
            extra={
              <button className="btn btn--quiet" type="button" onClick={() => onAnswer("custom")}>
                Compose inputs myself
              </button>
            }
          />
        );
      }
      const field = view.target_field;
      const evidence = plan?.evidence.find((item) => item.field === field);
      const candidates = evidence?.candidates ?? [];
      return (
        <div className="wizard">
          <AgentQuestion view={view} />
          <div className="wizard__field">
            Needs <code>{field ?? "an input"}</code>
            {evidence?.reason ? <span className="wizard__reason">{evidence.reason}</span> : null}
          </div>
          {candidates.length > 0 ? (
            <Choices
              title="Found in your workspace"
              options={candidates.map((candidate, index) => ({
                key: candidate,
                label: candidate,
                answer: String(index + 1),
              }))}
              onPick={onAnswer}
            />
          ) : null}
          <FreeText
            placeholder="Or type the full path"
            submitLabel="Use this path"
            onSubmit={onAnswer}
          />
        </div>
      );
    }

    case "main":
    default: {
      const readyToExecute = view.next_prompt?.kind === "dry_run";
      return (
        <div className="main-input">
          {view.next_prompt?.question ? (
            <p className="main-input__question">{view.next_prompt.question}</p>
          ) : null}
          {readyToExecute ? (
            <button className="btn btn--primary" type="button" onClick={() => onAnswer("/execute")}>
              Review and execute this plan
            </button>
          ) : null}
          <FreeText
            placeholder="What would you like to accomplish with NetZoo?"
            submitLabel="Send"
            onSubmit={onAnswer}
          />
        </div>
      );
    }
  }
}
