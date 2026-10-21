import type { ActivityRun, Stage } from "../timeline/model";
import { actionLabel } from "../timeline/model";
import { ExternalLink } from "../help/ExternalLink";

const text = (value: unknown): string => typeof value === "string" ? value.trim() : "";
const short = (value: unknown): string => {
  const valueText = text(value);
  return valueText.length > 280 ? `${valueText.slice(0, 277)}…` : valueText;
};
const workflowNames = (value: unknown): string => Array.isArray(value)
  ? value.filter((action): action is string => typeof action === "string")
    .slice(0, 8).map((action) => actionLabel(action).replace(/^Run /, "")).join(", ")
  : "";

function stageDetails(stage: Stage): string[] {
  const details: string[] = [];
  for (const row of stage.rows) {
    const payload = row.payload;
    switch (row.eventType) {
      case "policy.loaded":
        details.push(`Used project policy${text(payload.agents_path) ? `: ${text(payload.agents_path)}` : ""}`);
        break;
      case "memory.retrieved": {
        const count = typeof payload.episode_count === "number" ? payload.episode_count : 0;
        details.push(`Checked saved profile and ${count} prior ${count === 1 ? "run" : "runs"}`);
        break;
      }
      case "decision.recorded":
        details.push(payload.action === "no_tool"
          ? `Decided to answer without running a workflow${short(payload.reason) ? `: ${short(payload.reason)}` : ""}`
          : `Selected ${text(payload.action).replace(/_/g, " ") || "a response path"}${short(payload.reason) ? `: ${short(payload.reason)}` : ""}`);
        break;
      case "plan.created": {
        details.push(payload.status === "respond_only"
          ? "Response path: no workflow execution planned"
          : `Plan: ${text(payload.workflow) || "workflow"} · ${text(payload.status).replace(/_/g, " ") || "prepared"}`);
        if (Array.isArray(payload.evidence)) {
          for (const item of payload.evidence) {
            if (!item || typeof item !== "object") continue;
            const evidence = item as Record<string, unknown>;
            const field = text(evidence.field);
            const status = text(evidence.status).replace(/_/g, " ");
            if (!field || !status || status === "missing") continue;
            const value = short(evidence.value);
            details.push(`Input · ${field}: ${value || status} (${status})`);
          }
        }
        break;
      }
      case "routing.registry_match_completed": {
        const candidates = workflowNames(payload.hypothesis_actions);
        if (candidates) details.push(`Candidate workflows: ${candidates}`);
        const matched = workflowNames(payload.matched_actions);
        if (matched) details.push(`Registry matched: ${matched}`);
        else if (payload.status === "ambiguous") details.push("Registry result: ambiguous; no workflow selected");
        break;
      }
      case "routing.selection_conditions_unresolved":
        details.push("The stated preferences did not resolve the workflow choice");
        break;
      case "routing.intent_classified":
        if (text(payload.mode)) details.push(`Request type: ${text(payload.mode).replace(/_/g, " ")}`);
        break;
      case "tool.started": {
        const action = text(payload.action);
        details.push(`${action ? actionLabel(action) : "Tool"} started${short(payload.purpose) ? `: ${short(payload.purpose)}` : ""}`);
        const lookup = payload.lookup;
        if (lookup && typeof lookup === "object") {
          const lookupData = lookup as Record<string, unknown>;
          if (text(lookupData.library)) details.push(`Documentation: ${short(lookupData.library)}`);
          if (text(lookupData.query)) details.push(`Search: ${short(lookupData.query)}`);
        }
        break;
      }
      case "tool.completed":
        details.push(`Tool ${text(payload.status).replace(/_/g, " ") || "finished"}${short(payload.summary) ? `: ${short(payload.summary)}` : ""}`);
        break;
      case "tool.refused":
        details.push(`Tool refused${short(payload.reason) ? `: ${short(payload.reason)}` : ""}`);
        break;
      case "evaluation.recorded":
        details.push(`Result ${text(payload.status).replace(/_/g, " ") || "reviewed"}${short(payload.reason) ? `: ${short(payload.reason)}` : ""}`);
        break;
      case "error.recorded":
        details.push(`Error${short(payload.message) ? `: ${short(payload.message)}` : ""}`);
        break;
      case "recovery.selected":
        details.push("Selected a recovery plan");
        break;
      default:
        break;
    }
  }
  const modelResponses = stage.rows.filter((row) => row.eventType === "llm.completed").length;
  if (modelResponses) details.push(`Model responses recorded: ${modelResponses}`);
  return details;
}

function stageSources(stage: Stage): { title: string; url: string }[] {
  return stage.rows.flatMap((row) => {
    if (row.eventType !== "tool.completed" || !Array.isArray(row.payload.source_refs)) return [];
    return row.payload.source_refs.flatMap((ref) => {
      if (!ref || typeof ref !== "object") return [];
      const source = ref as Record<string, unknown>;
      const url = text(source.url);
      if (!/^https?:\/\//i.test(url)) return [];
      return [{ title: short(source.title) || url, url }];
    });
  });
}

function stageStatus(stage: Stage, busy: boolean): string {
  if (stage.failed) return "Failed";
  if (stage.interrupted) return "Interrupted";
  if (stage.waiting) return "Waiting for input";
  if (stage.running) return busy ? "Working" : "Awaiting events";
  if (stage.warning) return "Needs attention";
  return "Done";
}

export function TurnActivity({ run, busy, incomplete }: {
  run: ActivityRun;
  busy: boolean;
  incomplete: boolean;
}) {
  return (
    <details className="turn-activity" open>
      <summary className="turn-activity__head">
        <span className="turn-activity__title">Agent activity</span>
        <span className="turn-activity__status">{run.status === "Running" && !busy ? "Awaiting events" : run.status}</span>
      </summary>
      <div className="turn-activity__body">
        {incomplete ? <p className="turn-activity__note">Some activity events are missing.</p> : null}
        <ol className="turn-activity__stages">
          {run.stages.map((stage) => {
            const details = stageDetails(stage);
            const sources = stageSources(stage);
            return (
              <li className="turn-activity__stage" key={stage.id}>
                <span className={`turn-activity__marker${stage.failed ? " is-failed" : stage.warning ? " is-warning" : stage.running ? " is-running" : ""}`} aria-hidden="true" />
                <div>
                  <div className="turn-activity__stage-head">
                    <strong>{stage.label}</strong>
                    <span>{stageStatus(stage, busy)}</span>
                  </div>
                  {details.length > 0 ? <ul className="turn-activity__details">{details.map((detail, index) => <li key={`${stage.id}-${index}`}>{detail}</li>)}</ul> : null}
                  {sources.length > 0 ? <ul className="turn-activity__sources">{sources.map((source, index) => <li key={`${stage.id}-source-${index}`}>Source: <ExternalLink href={source.url}>{source.title}</ExternalLink></li>)}</ul> : null}
                </div>
              </li>
            );
          })}
        </ol>
        {run.stages.length === 0 ? <p className="turn-activity__note">Starting the request…</p> : null}
      </div>
    </details>
  );
}
