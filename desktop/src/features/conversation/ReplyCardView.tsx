/**
 * A reply's brief form: the bottom line and a few key points first, the
 * agent's full explanation one click away.
 *
 * The card is derived from the same decision as the text and never replaces
 * it — the full reply is always in the disclosure, unedited — so nothing the
 * agent wrote is lost by showing less of it at first. Replies without a brief
 * form (no headline) render exactly as before.
 */
import { ReplyCard } from "../../transport/protocol";
import { Markdown } from "./Markdown";

const KIND_LABELS: Partial<Record<ReplyCard["kind"], string>> = {
  method_choice: "Choose a method",
  clarification: "One detail needed",
  reading_choice: "Several readings",
  hypothesis_choice: "Several hypotheses",
  capability_gap: "Not supported",
  workflow_guidance: "Recommended workflow",
  composition: "Workflow",
  plan_ready: "Plan ready",
  run_completed: "Run finished",
  run_failed: "Run stopped",
  unresolved: "Not understood",
};

export function ReplyCardView({ card, text }: { card: ReplyCard; text: string }) {
  if (!card.headline) return <Markdown>{text}</Markdown>;
  const tone = card.kind === "run_failed" || card.kind === "capability_gap" || card.kind === "unresolved"
    ? " rc--warn" : card.kind === "run_completed" ? " rc--done" : "";
  return (
    <div className={`rc${tone}`}>
      <div className="rc__kicker">
        <span>{KIND_LABELS[card.kind] ?? "Answer"}</span>
        {card.ran_nothing ? <span className="rc__safe" title="No files were inspected and no analysis ran in this turn.">Nothing ran</span> : null}
      </div>
      <p className="rc__headline">{card.headline}</p>
      {card.points.length > 0 ? (
        <ul className="rc__points">
          {card.points.map((point) => <li key={point}>{point}</li>)}
        </ul>
      ) : null}
      {card.unavailable.length > 0 ? (
        <div className="rc__unavailable" role="note">
          <div className="rc__section">Related, but not available in this agent</div>
          <ul>
            {card.unavailable.map((item) => (
              <li key={item.key}>
                <span className="rc__unavailable-label">{item.label}</span>
                {item.reason ? <span className="rc__unavailable-reason"> — {item.reason}</span> : null}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      <details className="rc__details">
        <summary>Full explanation</summary>
        <Markdown className="rc__full">{text}</Markdown>
      </details>
    </div>
  );
}
