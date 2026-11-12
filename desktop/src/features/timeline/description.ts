/**
 * One readable description per run.
 *
 * The agent records an `operation.summary` event when it replies: the request, how it was read, the method and
 * steps, what ran, outputs and the next step, in plain English. A run without one (it started before summaries
 * were recorded, it ended before the agent replied, or it is still working) is described from its recorded
 * tool results instead, and says so.
 */
import type { Entry } from "../../transport/session";
import { entryTimestamp } from "../../transport/session";
import type { TraceEvent } from "../../transport/protocol";
import { buildResults } from "./results";

export type SummaryInput = { field: string; value: string; status: string; source: string };
export type SummaryTool = { label: string; status: string; summary: string; superseded: boolean };
export type SummaryStep = { action: string; label: string; purpose: string };

export type SummaryFile = {
  path: string; title: string; read: string; written: boolean; workflow: string | null; tags: string[];
  bytes?: number; columns?: { name: string; meaning: string }[]; first_row?: string[]; more_columns?: number;
};
export type SummaryMeaning = {
  workflow: string; role: string; about: string; read: string; limits: string;
  sources: { title: string; url: string }[]; next: { workflow: string; relation: string; description: string }[];
};

export type OperationSummary = {
  outcome: string;
  headline: string;
  request: string;
  follow_up: string | null;
  narrative: string[];
  decision: { kind: string | null; action: string | null; reason: string | null; workflows: string[]; candidates: string[]; partial: boolean; declined: { quote: string; reasons: string[] }[] };
  method: { workflow: string | null; objective: string | null; plan_status: string | null; steps: SummaryStep[] };
  inputs: SummaryInput[];
  missing_inputs: string[];
  tools: SummaryTool[];
  outputs: string[];
  planned_outputs: string[];
  warnings: string[];
  errors: string[];
  evaluation: string | null;
  questions: string[];
  next_step: string | null;
  reply_excerpt: string | null;
  usage: { llm_calls?: number; total_tokens?: number; cost_usd?: number; cost_complete?: boolean; models?: string[] };
  meaning: SummaryMeaning[];
  files: SummaryFile[];
  caveats: string[];
};

export type RunDescription = {
  id: string;
  index: number;
  startedAt: string;
  endedAt: string | null;
  elapsedMs: number | null;
  status: string;
  /** Recorded by the agent; null when this description was assembled from the tool results. */
  summary: OperationSummary | null;
  /** Used when no summary was recorded. */
  fallback: { headline: string; request: string; narrative: string[]; outputs: string[]; errors: string[] } | null;
};

export const SUMMARY_EVENT = "operation.summary";

const strings = (value: unknown): string[] => Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
const text = (value: unknown): string => typeof value === "string" ? value : "";
const record = (value: unknown): Record<string, unknown> => value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : {};

/** Read a recorded summary defensively: an older or partial payload must still render. */
export function readSummary(payload: Record<string, unknown>): OperationSummary | null {
  if (!text(payload.headline)) return null;
  const decision = record(payload.decision);
  const method = record(payload.method);
  const objects = (value: unknown) => Array.isArray(value) ? value.map(record) : [];
  return {
    outcome: text(payload.outcome),
    headline: text(payload.headline),
    request: text(payload.request),
    follow_up: text(payload.follow_up) || null,
    narrative: strings(payload.narrative),
    decision: {
      kind: text(decision.kind) || null, action: text(decision.action) || null, reason: text(decision.reason) || null,
      workflows: strings(decision.workflows), candidates: strings(decision.candidates), partial: decision.partial === true,
      declined: objects(decision.declined).map((part) => ({ quote: text(part.quote), reasons: strings(part.reasons) })),
    },
    method: {
      workflow: text(method.workflow) || null, objective: text(method.objective) || null, plan_status: text(method.plan_status) || null,
      steps: objects(method.steps).map((step) => ({ action: text(step.action), label: text(step.label), purpose: text(step.purpose) })),
    },
    inputs: objects(payload.inputs).map((item) => ({ field: text(item.field), value: text(item.value), status: text(item.status), source: text(item.source) })),
    missing_inputs: strings(payload.missing_inputs),
    tools: objects(payload.tools).map((tool) => ({ label: text(tool.label), status: text(tool.status), summary: text(tool.summary), superseded: tool.superseded === true })),
    outputs: strings(payload.outputs),
    planned_outputs: strings(payload.planned_outputs),
    warnings: strings(payload.warnings),
    errors: strings(payload.errors),
    evaluation: text(payload.evaluation) || null,
    questions: strings(payload.questions),
    next_step: text(payload.next_step) || null,
    reply_excerpt: text(payload.reply_excerpt) || null,
    usage: record(payload.usage) as OperationSummary["usage"],
    meaning: objects(payload.meaning).map((item) => ({
      workflow: text(item.workflow), role: text(item.role), about: text(item.about), read: text(item.read), limits: text(item.limits),
      sources: objects(item.sources).map((source) => ({ title: text(source.title), url: text(source.url) })).filter((source) => /^https:\/\//.test(source.url)),
      next: objects(item.next).map((next) => ({ workflow: text(next.workflow), relation: text(next.relation), description: text(next.description) })),
    })).filter((item) => item.workflow),
    files: objects(payload.files).map((file) => ({
      path: text(file.path), title: text(file.title), read: text(file.read), written: file.written === true, tags: strings(file.tags),
      workflow: text(file.workflow) || null, bytes: typeof file.bytes === "number" ? file.bytes : undefined,
      columns: Array.isArray(file.columns) ? objects(file.columns).map((column) => ({ name: text(column.name), meaning: text(column.meaning) })) : undefined,
      first_row: Array.isArray(file.first_row) ? strings(file.first_row) : undefined,
      more_columns: typeof file.more_columns === "number" ? file.more_columns : undefined,
    })).filter((file) => file.path),
    caveats: strings(payload.caveats),
  };
}

/** The user's last message sent before the run started: the request a run without a summary answered. */
function requestBefore(entries: Entry[], startedAt: string): string {
  const start = Date.parse(startedAt);
  let found = "";
  for (const entry of entries) {
    if (entry.kind !== "user") continue;
    const at = Date.parse(entryTimestamp(entry) ?? "");
    if (Number.isFinite(at) && Number.isFinite(start) && at <= start + 2_000) found = entry.text;
  }
  return found;
}

export function buildDescriptions(trace: TraceEvent[], entries: Entry[] = []): RunDescription[] {
  return buildResults(trace).map((run, index) => {
    const recorded = trace.filter((event) => event.run_id === run.id && event.event_type === SUMMARY_EVENT)
      .sort((left, right) => left.sequence - right.sequence).at(-1);
    const summary = recorded ? readSummary(recorded.payload) : null;
    const base = { id: run.id, index, startedAt: run.startedAt, endedAt: run.endedAt, elapsedMs: run.elapsedMs, status: run.status };
    if (summary) return { ...base, summary, fallback: null };
    const current = run.tools.filter((tool) => !tool.superseded);
    const narrative: string[] = [];
    if (run.status === "Running") narrative.push("The agent is still working on this run; the description is written when it replies.");
    else if (run.status === "Waiting") narrative.push("The run is paused, waiting for your answer in the conversation.");
    else narrative.push("No written description was recorded for this run (it was recorded before descriptions existed, or it ended before the agent replied). This one is assembled from the recorded tool results.");
    if (current.length) narrative.push("What ran: " + current.map((tool) => `${tool.action} ${tool.status === "dry_run" ? "previewed (dry run, not executed)" : tool.status === "success" ? "completed" : tool.status || "status not recorded"}`).join("; ") + ".");
    const outputs = [...new Set(current.filter((tool) => tool.status === "success").flatMap((tool) => tool.artifacts))];
    const errors = [...run.errors.map((error) => error.message), ...current.flatMap((tool) => tool.errors)];
    return { ...base, summary: null, fallback: { headline: run.outcome, request: requestBefore(entries, run.startedAt), narrative, outputs, errors } };
  });
}

const OUTCOME_LABELS: Record<string, string> = {
  executed: "Ran", preview: "Preview only", failed: "Failed", needs_input: "Needs input", needs_confirmation: "Needs confirmation",
  inspected: "Inputs inspected", asked: "Question asked", clarify: "Clarification asked", declined: "Declined", answered: "Answered",
  choice: "Choice asked", held: "Run held", rejected: "Plan rejected",
};
export const outcomeLabel = (outcome: string) => OUTCOME_LABELS[outcome] ?? outcome;

const KIND_LABELS: Record<string, string> = {
  DO: "Can be done with an available workflow", ASK: "Needs a fact before running", CLARIFY: "Needs the wanted result clarified",
  DECLINE: "No available workflow produces this", UNCHECKED: "Not checked",
};
export const kindLabel = (kind: string | null) => kind ? KIND_LABELS[kind] ?? kind : "Not recorded";

/** The same description as plain text, for copying into notes or a report. */
export function descriptionText(run: RunDescription): string {
  const lines = [`Run ${run.index + 1} (${run.id.slice(0, 8)}) · ${run.startedAt}`];
  const summary = run.summary;
  if (!summary) {
    const fallback = run.fallback!;
    lines.push(`Conclusion: ${fallback.headline}`);
    if (fallback.request) lines.push(`Request: ${fallback.request}`);
    lines.push(...fallback.narrative, ...fallback.outputs.map((path) => `Output: ${path}`), ...fallback.errors.map((error) => `Error: ${error}`));
    return lines.join("\n");
  }
  lines.push(`Conclusion: ${summary.headline}`, "", ...summary.narrative, "");
  lines.push(`How the request was read: ${kindLabel(summary.decision.kind)}`);
  if (summary.method.workflow || summary.decision.workflows.length) lines.push(`Method: ${summary.method.workflow ?? summary.decision.workflows.join(", ")}`);
  summary.method.steps.forEach((step, i) => lines.push(`  ${i + 1}. ${step.label}${step.purpose ? ` — ${step.purpose}` : ""}`));
  summary.inputs.forEach((item) => lines.push(`Input ${item.field}: ${item.value || "(none)"} (${item.source})`));
  summary.tools.forEach((tool) => lines.push(`Step ${tool.label}: ${tool.status}${tool.superseded ? " (replaced)" : ""}${tool.summary ? ` — ${tool.summary}` : ""}`));
  if (summary.files.length) summary.files.forEach((file) => lines.push(`${file.written ? "Output" : "Planned output"}: ${file.path} — ${file.title}${file.read ? `. ${file.read}` : ""}${file.tags.length ? ` [${file.tags.join(", ")}]` : ""}`));
  else summary.outputs.forEach((path) => lines.push(`Output: ${path}`));
  summary.warnings.forEach((warning) => lines.push(`Warning: ${warning}`));
  summary.errors.forEach((error) => lines.push(`Error: ${error}`));
  summary.questions.forEach((question) => lines.push(`Question asked: ${question}`));
  if (summary.next_step) lines.push(`Next step: ${summary.next_step}`);
  summary.caveats.forEach((caveat) => lines.push(`Note: ${caveat}`));
  summary.meaning.forEach((item) => {
    lines.push("", `About ${item.workflow}: ${item.about}`, `How to read it: ${item.read}`, `What it does not show: ${item.limits}`);
    item.next.forEach((next) => lines.push(`Next analysis: ${next.workflow} (${next.relation}) — ${next.description}`));
    item.sources.forEach((source) => lines.push(`Source: ${source.title} ${source.url}`));
  });
  return lines.join("\n");
}
