/**
 * The Work Plan, as a thing to read rather than a wall of text.
 *
 * The evidence ledger is the part that matters: it is the agent's account of
 * where every input came from, and `missing` is what the next question will
 * be about. Nothing here is editable — the plan is the agent's, and changing
 * an input means answering its question, not editing its record.
 */
import { WorkflowPlan } from "../../transport/protocol";

const STATUS_LABEL: Record<WorkflowPlan["status"], string> = {
  ready: "Ready",
  needs_input: "Needs input",
  needs_confirmation: "Needs confirmation",
  respond_only: "Answer only",
};

const EVIDENCE_LABEL: Record<string, string> = {
  provided: "you gave it",
  selected: "you chose it",
  discovered: "found in workspace",
  derived: "derived",
  demo_bundle: "demo bundle",
  defaulted: "default",
  missing: "missing",
};

export function PlanCard({ plan, hash }: { plan: WorkflowPlan; hash: string | null }) {
  return (
    <div className="plan">
      <div className="plan__head">
        <span className="plan__workflow">{plan.workflow}</span>
        <span className={`plan__status plan__status--${plan.status}`}>
          {STATUS_LABEL[plan.status]}
        </span>
      </div>
      {plan.objective ? <p className="plan__objective">{plan.objective}</p> : null}

      {plan.evidence.length > 0 ? (
        <table className="plan__evidence">
          <tbody>
            {plan.evidence.map((item) => (
              <tr key={item.field} className={item.status === "missing" ? "is-missing" : ""}>
                <td className="plan__field">{item.field}</td>
                <td className="plan__value">{item.value ?? "—"}</td>
                <td className="plan__origin">{EVIDENCE_LABEL[item.status] ?? item.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}

      {plan.steps.length > 0 ? (
        <details className="plan__steps" open>
          <summary>{plan.steps.length} step{plan.steps.length === 1 ? "" : "s"}</summary>
          <ol>
            {plan.steps.map((step, index) => (
              <li key={`${step.action}-${index}`}>
                <code>{step.action}</code>
                <span>{step.purpose}</span>
              </li>
            ))}
          </ol>
        </details>
      ) : null}

      {plan.recovery_action ? (
        <p className="plan__recovery">
          Recovery attempt {plan.recovery_attempt}: <code>{plan.recovery_action}</code>
        </p>
      ) : null}

      {plan.policy_notes.length + plan.memory_notes.length > 0 ? (
        <details className="plan__notes">
          <summary>Policy and memory notes</summary>
          <ul>
            {plan.policy_notes.map((note) => (
              <li key={`policy-${note}`}>{note}</li>
            ))}
            {plan.memory_notes.map((note) => (
              <li key={`memory-${note}`}>{note}</li>
            ))}
          </ul>
        </details>
      ) : null}

      {hash ? <div className="plan__hash">plan {hash.slice(0, 12)}</div> : null}
    </div>
  );
}
