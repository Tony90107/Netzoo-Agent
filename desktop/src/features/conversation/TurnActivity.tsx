/**
 * The steps of one turn, inline in the conversation, the way Claude Code shows its work: open while
 * the agent works, folded into one line ("Worked 18 s · 4 steps · 7 model calls") once it is done.
 *
 * Every line is read from the run's trace, never written by a model. NetZoo's decisions are made by
 * code from the workflow contracts; a model's free-text "reason" is not what decided, so it is not
 * shown here as one. What a model did is shown by its recorded role (which part of the request it
 * read), its model name and its tokens.
 */
import { useState } from "react";

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
        // The action is the recorded choice; its `reason` is model prose, so it is left out.
        if (payload.action === "no_tool") details.push("Reply in the conversation; no workflow is run");
        else if (text(payload.action) && !stage.rows.some((other) => other.eventType === "core.decision")) {
          details.push(`Selected ${actionLabel(text(payload.action))}`);
        }
        break;
      case "core.decision": {
        const line = decisionLine(payload);
        if (line) details.push(line);
        details.push(...decisionDetails(payload));
        break;
      }
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
      // Sub-steps, as the code records each one finishing (live while the step runs).
      case "routing.semantic_interpretation_retried":
        details.push("The first reading was incomplete; reading again");
        break;
      case "routing.semantic_interpretation_accepted": {
        const lines = readingLines(payload.reading);
        details.push(...(lines.length ? lines : ["Read what you asked for"]));
        break;
      }
      case "routing.study_purpose_detected":
        details.push(purposeLine(payload));
        break;
      case "routing.capability_checked":
        details.push("Checked what the methods can do", ...capabilityLines(payload.check));
        break;
      case "core.fact_check":
        details.push("Checked the stated facts", ...factCheckLines(payload));
        break;
      case "core.jev_guard": {
        const line = guardLine(payload);
        if (line) details.push(line);
        break;
      }
      case "routing.request_concerns_matched":
        details.push("Noted your stated concerns");
        break;
      case "routing.intent_classified":
        // An early reading the decision can overrule; shown, it contradicted the decision line.
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
      case "tool.completed": {
        details.push(`Tool ${text(payload.status).replace(/_/g, " ") || "finished"}${short(payload.summary) ? `: ${short(payload.summary)}` : ""}`);
        const errors = Array.isArray(payload.errors) ? payload.errors.map(short).filter(Boolean) : [];
        for (const error of errors.slice(0, 3)) details.push(`  Problem: ${error}`);
        if (errors.length > 3) details.push(`  …and ${errors.length - 3} more problems (see the log)`);
        const artifacts = Array.isArray(payload.artifacts) ? payload.artifacts.map(text).filter(Boolean) : [];
        for (const file of artifacts.slice(0, 5)) details.push(`  Output: ${file}`);
        if (text(payload.log_file)) details.push(`  Log: ${text(payload.log_file)}`);
        break;
      }
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
  const calls = modelCallLine(stage);
  if (calls) details.push(calls);
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

const ROLE_LABELS: Record<string, string> = {
  semantic_interpreter: "read the request",
  semantic_reviewer: "review that reading",
  semantic_discriminator: "tell readings apart",
  semantic_sibling_repair: "repair the reading",
  intent_router: "classify the request",
  router: "route the request",
  router_repair: "repair the route",
  goal_read: "read the goal",
  study_purpose: "read the study purpose",
  capability_check: "check what the methods can do",
  capability_second_opinion: "second opinion on that check",
  capability_reread: "re-read that check",
  fact_check: "check the stated facts",
  data_facts: "read facts about the data",
  hypothesis_bases: "read what each reading rests on",
  request_concerns: "read stated concerns",
  selection_conditions: "read stated preferences",
  follow_up: "read the follow-up",
  normalization_need: "check whether normalization is needed",
  input_content_mapper: "match file contents to inputs",
  response: "write the reply",
};

const roleLabel = (role: string): string => ROLE_LABELS[role] ?? role.replace(/_/g, " ");
const shortModel = (model: string): string => model.split("/").pop() ?? model;

/** "gpt-4o-mini · 6 calls (read the request ×2, …) · 32,104 tokens", from `llm.completed` only. */
export function modelCallLine(stage: Stage): string {
  const calls = stage.rows.filter((row) => row.eventType === "llm.completed");
  if (calls.length === 0) return "";
  const models = [...new Set(calls.map((row) => text(row.payload.model)).filter(Boolean).map(shortModel))];
  const roles = new Map<string, number>();
  for (const row of calls) {
    const role = text(row.payload.role);
    if (role) roles.set(role, (roles.get(role) ?? 0) + 1);
  }
  const roleText = [...roles].map(([role, count]) => `${roleLabel(role)}${count > 1 ? ` ×${count}` : ""}`).join(", ");
  const failed = calls.filter((row) => row.payload.status === "failed").length;
  return [
    models.join(", ") || "Model",
    `${calls.length} ${calls.length === 1 ? "call" : "calls"}${roleText ? ` (${roleText})` : ""}`,
    stage.tokens ? `${stage.tokens.toLocaleString()} tokens` : "",
    failed ? `${failed} retried` : "",
  ].filter(Boolean).join(" · ");
}

/** "lioness_panda.per_sample_networks" -> "LIONESS-PANDA (per sample networks)". */
function deliveredBy(value: unknown): string {
  const [workflow, result] = String(value).split(".");
  const name = (workflow ?? "").replace(/_/g, "-").toUpperCase();
  return result ? `${name} (${result.replace(/_/g, " ")})` : name;
}

/**
 * What the capability check found for each result the request asked for. Only findings with an
 * explicit basis are shown: the workflows that deliver it, or a recorded limit. A bare "not
 * available" is left out: later checks can still settle it, and the decision line says how it ended.
 */
function capabilityLines(check: unknown): string[] {
  if (!check || typeof check !== "object") return [];
  const requirements = (check as Record<string, unknown>).requirements;
  if (!Array.isArray(requirements)) return [];
  const lines: string[] = [];
  for (const entry of requirements) {
    const item = (entry ?? {}) as Record<string, unknown>;
    if (item.kind !== "result" || !text(item.quote)) continue;
    const quote = `  “${short(item.quote)}”`;
    const by = Array.isArray(item.delivered_by) ? item.delivered_by.slice(0, 4).map(deliveredBy) : [];
    const more = Array.isArray(item.delivered_by) && item.delivered_by.length > 4 ? ` and ${item.delivered_by.length - 4} more` : "";
    if (item.status === "available" && by.length) lines.push(`${quote} → ${by.join(", ")}${more}`);
    else if (item.status === "with_step" && by.length) lines.push(`${quote} → with an extra step: ${by.join(", ")}${more}`);
    else if (item.status === "needs_fact" && by.length) lines.push(`${quote} → ${by.join(", ")}${more}, once a fact is confirmed`);
    else if (item.status === "not_available") {
      const limits = Array.isArray(item.limits) ? item.limits.map(short).filter(Boolean) : [];
      const notBy = Array.isArray(item.not_by) ? item.not_by.map((value) => String(value).replace(/_/g, " ")) : [];
      if (limits.length) lines.push(`${quote} → not available: ${limits[0]}`);
      else if (notBy.length) lines.push(`${quote} → not available: no workflow does ${notBy.join(", ")}`);
    }
  }
  return lines;
}

/** The fact check: which methods it weighed, and the questions the code held back, by rule. */
function factCheckLines(payload: Record<string, unknown>): string[] {
  const lines: string[] = [];
  const candidates = Array.isArray(payload.candidates) ? payload.candidates.map(text).filter(Boolean) : [];
  if (candidates.length) lines.push(`  Methods weighed: ${candidates.join(", ")}`);
  const rejected = Array.isArray(payload.rejected) ? payload.rejected : [];
  const rules = [...new Set(rejected.map((item) => text((item as Record<string, unknown>)?.rule).replace(/^R\d+[a-z]?\s+/i, "")).filter(Boolean))];
  if (rejected.length) {
    lines.push(`  ${rejected.length} possible ${rejected.length === 1 ? "question" : "questions"} not asked${rules.length ? `: ${rules.join("; ")}` : ""}`);
  }
  const accepted = Array.isArray(payload.accepted) ? payload.accepted.length : 0;
  if (accepted) lines.push(`  ${accepted} ${accepted === 1 ? "fact" : "facts"} to confirm with you`);
  return lines;
}

/** The independent second reading (jev guard), in what it did to the decision. */
function guardLine(payload: Record<string, unknown>): string {
  const jev = (payload.jev ?? {}) as Record<string, unknown>;
  const read = text(jev.kind);
  const confidence = typeof jev.confidence === "number" ? ` (${Math.round(jev.confidence * 100)}%)` : "";
  const reading = read ? `it read the request as ${read}${confidence}` : "";
  switch (payload.action) {
    case "clarify": return `Independent check changed the decision to asking what you want${reading ? `: ${reading}` : ""}`;
    case "ask": return `Independent check changed the decision to asking you first${reading ? `: ${reading}` : ""}`;
    case "agrees_or_unsure": return `Independent check: decision kept${reading ? `; ${reading}` : ""}`;
    default: return "";
  }
}

/** The study purpose as read, or that none was stated. */
function purposeLine(payload: Record<string, unknown>): string {
  const design = text(payload.design);
  const claims = Array.isArray(payload.claims) ? payload.claims.map((claim) => Array.isArray(claim) ? String(claim[0]) : text(claim)).filter(Boolean) : [];
  const parts = [design ? `design: ${design.replace(/_/g, " ")}` : "", claims.length ? `aims: ${claims.join(", ").replace(/_/g, " ")}` : ""].filter(Boolean);
  if (!parts.length) return "Read the study purpose: none stated";
  return `Read the study purpose: ${parts.join("; ")}${text(payload.design_quote) ? ` (“${short(payload.design_quote)}”)` : ""}`;
}

/** What the decision leads to: the code's own questions, the rule each rests on, and what is not possible. */
function decisionDetails(payload: Record<string, unknown>): string[] {
  const lines: string[] = [];
  const clarify = payload.clarify as Record<string, unknown> | null | undefined;
  if (clarify && text(clarify.question)) {
    lines.push(`  Will ask: “${short(clarify.question)}”`);
    const candidates = Array.isArray(clarify.candidates) ? clarify.candidates.map(text).filter(Boolean) : [];
    if (candidates.length) lines.push(`  Possible methods: ${candidates.slice(0, 8).join(", ")}${candidates.length > 8 ? ` and ${candidates.length - 8} more` : ""}`);
  }
  for (const entry of Array.isArray(payload.facts) ? payload.facts.slice(0, 4) : []) {
    const fact = (entry ?? {}) as Record<string, unknown>;
    if (!text(fact.question)) continue;
    lines.push(`  Will ask: “${short(fact.question)}”`);
    if (text(fact.contract_quote)) lines.push(`    Rule: “${short(fact.contract_quote)}”`);
  }
  for (const entry of Array.isArray(payload.declined) ? payload.declined.slice(0, 4) : []) {
    const declined = (entry ?? {}) as Record<string, unknown>;
    if (text(declined.line)) lines.push(`  Not possible: ${short(declined.line)}`);
  }
  return lines;
}

/** What the code decided (`core.decision`), in words; "" for a kind it does not name. */
function decisionLine(payload: Record<string, unknown>): string {
  const workflows = Array.isArray(payload.workflows)
    ? payload.workflows.filter((name): name is string => typeof name === "string" && name !== "NO-TOOL")
    : [];
  switch (payload.kind) {
    case "DO": {
      // DO means "can deliver"; the basis says how (core_decision.py), so only a run is called one.
      const names = workflows.join(", ");
      const part = payload.partial ? " (part of what you asked)" : "";
      if (payload.basis === "run") return `Decision: prepare a run of ${names || "the workflow"}${part}`;
      if (payload.basis === "run_held") return `Decision: hold the run of ${names || "the workflow"} for now${part}`;
      return names ? `Decision: ${names} can give what you asked for${part}` : "";
    }
    case "ASK": return "Decision: ask you for what is still missing";
    case "CLARIFY": return "Decision: ask what you want to get";
    case "DECLINE": return "Decision: not possible with the available methods";
    default: return "";
  }
}

const ARTIFACT_WORDS: Record<string, string> = {
  regulatory_network: "a regulatory network",
  coexpression_network: "a co-expression network",
  regulatory_network_and_tf_activity: "a regulatory network with TF activity",
  signed_regulatory_effect_network: "a signed regulatory network",
  multi_omic_network: "a network across omics layers",
  tf_activity_matrix: "TF activity per sample",
  expression_matrix: "an expression matrix",
  measurement_dataset: "a dataset",
  pvalue_matrix: "a p-value matrix",
  mutation_matrix: "a mutation matrix",
  pathway_mutation_matrix: "pathway mutation scores",
  gene_mutation_scores: "gene mutation scores",
  sample_distance_matrix: "distances between samples",
  sample_cluster_assignment: "sample clusters",
  community_assignment: "network communities",
  validation_report: "a validation report",
  pathway_heterogeneity_table: "pathways that vary between patients",
};
const GRANULARITY_WORDS: Record<string, string> = { aggregate: "one for all samples", sample_specific: "one per sample" };
const REGULATOR_WORDS: Record<string, string> = { tf: "TFs", mirna: "miRNAs" };

const OPERATION_WORDS: Record<string, string> = {
  infer: "build it", analyze: "analyze it", explain: "explain it", acquire: "get the data",
  prepare: "prepare the data", validate: "check it",
};

function valueWords(dimension: string, value: string): string {
  if (dimension === "operation") return `you want to ${OPERATION_WORDS[value] ?? value.replace(/_/g, " ")}`;
  if (dimension === "input_artifact") return `input: ${ARTIFACT_WORDS[value] ?? value.replace(/_/g, " ")}`;
  if (dimension === "artifact_type") return ARTIFACT_WORDS[value] ?? value.replace(/_/g, " ");
  if (dimension === "granularity") return GRANULARITY_WORDS[value] ?? value.replace(/_/g, " ");
  if (dimension === "regulator_type") return `regulators: ${REGULATOR_WORDS[value] ?? value}`;
  if (dimension === "target_type") return `targets: ${value === "gene" ? "genes" : value.replace(/_/g, " ")}`;
  if (dimension === "entity_type") return `about: ${value.replace(/_/g, " ")}`;
  if (dimension === "selection_tag") return `method feature: ${value.replace(/_/g, " ")}`;
  return value.replace(/_/g, " ");
}

/**
 * The accepted reading (interpretation/reading_view.py): what the model understood and the user's
 * words each stated value rests on. It is the model's output that routing went on to use; its
 * free-text rationale is never part of it.
 */
export function readingLines(reading: unknown): string[] {
  if (!Array.isArray(reading) || reading.length === 0) return [];
  const lines: string[] = [];
  const several = reading.length > 1;
  if (several) lines.push(`Understood ${reading.length} possible readings:`);
  reading.forEach((entry, index) => {
    if (!entry || typeof entry !== "object") return;
    const item = entry as Record<string, unknown>;
    const artifact = ARTIFACT_WORDS[text(item.artifact_type)] ?? "";
    const granularity = GRANULARITY_WORDS[text(item.granularity)] ?? "";
    const regulators = Array.isArray(item.regulator_types)
      ? item.regulator_types.map((value) => REGULATOR_WORDS[String(value)]).filter(Boolean) : [];
    const what = [artifact, granularity, regulators.length ? `regulators: ${regulators.join(" and ")}` : ""].filter(Boolean).join(", ");
    const asked = item.operation === "explain" ? " (to be explained, not run)" : "";
    lines.push(`${several ? `${index + 1}. ` : "Understood: "}${what || "no specific result"}${asked}`);
    for (const stated of Array.isArray(item.stated) ? item.stated : []) {
      const row = stated as Record<string, unknown>;
      if (text(row.quote)) lines.push(`  “${short(row.quote)}” → ${valueWords(text(row.dimension), text(row.value))}`);
    }
    const inferred = (Array.isArray(item.inferred) ? item.inferred : [])
      .map((row) => valueWords(text((row as Record<string, unknown>).dimension), text((row as Record<string, unknown>).value)))
      .filter(Boolean);
    if (inferred.length) lines.push(`  Not stated, inferred: ${[...new Set(inferred)].join(", ")}`);
    const unresolved = Array.isArray(item.unresolved) ? item.unresolved.map((value) => String(value).replace(/_/g, " ")) : [];
    if (unresolved.length) lines.push(`  Not clear from the request: ${unresolved.join(", ")}`);
  });
  return lines;
}

/** The model call a running step is waiting on, by its recorded label ("checking the stated facts"). */
export function nowDoing(stage: Stage | undefined): string {
  if (!stage?.running) return "";
  const last = stage.rows.at(-1);
  return last?.eventType === "llm.started" && typeof last.payload.label === "string" ? last.payload.label : "";
}

/** Bookkeeping nodes: shown only when something went wrong in them. */
const QUIET_NODES = new Set(["apply_project_policy", "retrieve_memory", "consolidate_memory"]);

function stepLabel(stage: Stage): string {
  const doing = stage.running;
  switch (stage.node) {
    case "classify": return doing ? "Reading your request" : "Read your request";
    case "plan": return doing ? "Building a plan" : "Built a plan";
    case "evaluate_plan": return doing ? "Checking the plan" : "Checked the plan";
    case "execute_tool": {
      // One node run can start several tools (a lookup, then the workflow); name each once.
      const actions = [...new Set(stage.rows.filter((row) => row.eventType === "tool.started")
        .map((row) => text(row.payload.action)).filter(Boolean))];
      if (actions.length === 1 && actions[0] === "inspect_inputs") {
        return doing ? "Checking the input files" : "Checked the input files";
      }
      const names = actions
        .map((action) => {
          const label = actionLabel(action);
          return label.startsWith("Run ") ? label.slice(4) : label.charAt(0).toLowerCase() + label.slice(1);
        });
      const what = names.length === 0 ? "the workflow" : names.length === 1 ? names[0]
        : `${names.slice(0, -1).join(", ")} and ${names.at(-1)}`;
      return `${doing ? "Running" : "Ran"} ${what}`;
    }
    case "evaluate": return doing ? "Checking the result" : "Checked the result";
    case "recover": return doing ? "Choosing a recovery" : "Chose a recovery";
    case "respond": return doing ? "Writing the reply" : "Wrote the reply";
    case "input_content_mapper": return doing ? "Matching file contents to inputs" : "Matched file contents to inputs";
    case "follow_up": return doing ? "Reading your follow-up" : "Read your follow-up";
    default: return stage.label;
  }
}

function seconds(ms: number | null): string {
  if (ms === null) return "";
  return ms < 1000 ? "<1 s" : ms < 60_000 ? `${(ms / 1000).toFixed(ms < 10_000 ? 1 : 0)} s` : `${Math.floor(ms / 60_000)} min ${Math.round((ms % 60_000) / 1000)} s`;
}

function stageStatus(stage: Stage, busy: boolean): string {
  if (stage.failed) return "Failed";
  if (stage.interrupted) return "Interrupted";
  if (stage.waiting) return "Waiting for input";
  if (stage.running) return busy ? "Working" : "Awaiting events";
  if (stage.warning) return "Needs attention";
  return seconds(stage.durationMs);
}

/** The folded line: what the turn came to, how long the agent worked, and what it took. */
export function runSummary(run: ActivityRun, visible: Stage[], busy: boolean): string {
  const worked = run.stages.reduce((total, stage) => total + (stage.durationMs ?? 0), 0);
  const calls = run.stages.reduce((total, stage) => total + stage.rows.filter((row) => row.eventType === "llm.completed").length, 0);
  const failedAt = visible.find((stage) => stage.failed);
  const lead = run.status === "Failed" ? `Failed${failedAt ? ` at "${stepLabel(failedAt)}"` : ""}`
    : run.status === "Interrupted" ? "Interrupted"
      : run.status === "Waiting" ? "Waiting for you"
        : run.status === "Running" ? (busy ? "Working" : "Awaiting events")
          : "Worked";
  const counts = [
    worked ? seconds(worked) : "",
    `${visible.length} ${visible.length === 1 ? "step" : "steps"}`,
    calls ? `${calls} model ${calls === 1 ? "call" : "calls"}` : "",
  ].filter(Boolean).join(" · ");
  return run.status === "Completed" ? `Worked ${counts}` : `${lead} · ${counts}`;
}

export function TurnActivity({ run, busy, incomplete }: {
  run: ActivityRun;
  busy: boolean;
  incomplete: boolean;
}) {
  // Open while the agent works, folded once it is done; a click is the person's choice and sticks.
  const [chosen, setChosen] = useState<boolean | null>(null);
  const active = run.status === "Running" && busy;
  const open = chosen ?? (active || run.status === "Failed");
  const visible = run.stages.filter((stage) => !QUIET_NODES.has(stage.node) || stage.failed || stage.warning);
  const current = [...visible].reverse().find((stage) => stage.running);
  // A resume or a bare lifecycle record has no steps to show; an empty "0 steps" box is only noise.
  if (visible.length === 0 && !active && !incomplete) return null;
  return (
    <details className={`turn-activity${active ? " is-active" : ""}`} open={open}
      onToggle={(event) => {
        const next = (event.currentTarget as HTMLDetailsElement).open;
        if (next !== open) setChosen(next);
      }}>
      <summary className="turn-activity__head">
        <span className="turn-activity__title">
          {active ? <span className="thread__spinner" aria-hidden="true" /> : null}
          {active && current
            ? `${stepLabel(current)}${nowDoing(current) ? ` — ${nowDoing(current)}` : ""}…`
            : runSummary(run, visible, busy)}
        </span>
        <span className="turn-activity__status">{open ? "Hide steps" : "Show steps"}</span>
      </summary>
      <div className="turn-activity__body">
        {incomplete ? <p className="turn-activity__note">Some activity events are missing.</p> : null}
        <ol className="turn-activity__stages">
          {visible.map((stage) => {
            const details = stageDetails(stage);
            const sources = stageSources(stage);
            return (
              <li className="turn-activity__stage" key={stage.id}>
                <span className={`turn-activity__marker${stage.failed ? " is-failed" : stage.warning ? " is-warning" : stage.running ? " is-running" : ""}`} aria-hidden="true" />
                <div>
                  <div className="turn-activity__stage-head">
                    <strong>{stepLabel(stage)}</strong>
                    <span>{stageStatus(stage, busy)}</span>
                  </div>
                  {details.length > 0 || (busy && nowDoing(stage)) ? (
                    <ul className="turn-activity__details">
                      {details.map((detail, index) => <li key={`${stage.id}-${index}`}>{detail}</li>)}
                      {busy && nowDoing(stage) ? (
                        <li className="turn-activity__now"><span className="thread__spinner" aria-hidden="true" />
                          {nowDoing(stage).charAt(0).toUpperCase() + nowDoing(stage).slice(1)}…</li>
                      ) : null}
                    </ul>
                  ) : null}
                  {sources.length > 0 ? <ul className="turn-activity__sources">{sources.map((source, index) => <li key={`${stage.id}-source-${index}`}>Source: <ExternalLink href={source.url}>{source.title}</ExternalLink></li>)}</ul> : null}
                </div>
              </li>
            );
          })}
        </ol>
        {visible.length === 0 ? <p className="turn-activity__note">Starting the request…</p> : null}
      </div>
    </details>
  );
}
