/**
 * Turning a trace into something a person can read.
 *
 * The chain is faithful but flat: one PANDA turn produced 123 events, most of
 * them `routing.*` detail from inside a single node. Grouping them under the
 * node that emitted them is what makes the shape of a run visible — and the
 * detail stays, collapsed, because that detail is exactly what a routing
 * failure has to be diagnosed from.
 *
 * Nothing here interprets an event. A row shows what the chain recorded; if
 * this module cannot classify an event it shows it rather than dropping it.
 */
import type { TraceEvent } from "../../transport/protocol";
import { timestamp } from "./time";

/** The graph's nodes, in the order `graph/topology.py` wires them. */
const NODE_LABELS: Record<string, string> = {
  apply_project_policy: "Apply project policy",
  classify: "Interpret the request",
  retrieve_memory: "Retrieve memory",
  plan: "Build the Work Plan",
  evaluate_plan: "Evaluate the plan",
  execute_tool: "Run the workflow",
  evaluate: "Evaluate the result",
  recover: "Recover",
  consolidate_memory: "Consolidate memory",
  respond: "Respond",
  cli: "Session",
};

export type RowKind = "detail" | "tool" | "llm" | "error" | "warning" | "lifecycle";
export type EventLevel = "info" | "warning" | "error";

/** Read explicit execution verdicts, including failures that do not throw. */
export function eventLevel(event: TraceEvent): EventLevel {
  const payload = event.payload ?? {};
  if (event.event_type === "error.recorded" ||
      (["tool.completed", "evaluation.recorded", "run.finished"].includes(event.event_type) && payload.status === "failed")) return "error";
  if ((Array.isArray(payload.warnings) && payload.warnings.length > 0) ||
      event.event_type === "run.interrupted" ||
      ["rejected", "deferred", "replan", "needs_input"].includes(String(payload.status)) ||
      event.event_type.endsWith(".rejected") || event.event_type.endsWith(".deferred")) return "warning";
  return "info";
}

export type DetailRow = {
  id: string;
  kind: RowKind;
  eventType: string;
  occurredAt: string;
  summary: string;
  payload: Record<string, unknown>;
};

export type Stage = {
  id: string;
  node: string;
  runId: string;
  label: string;
  startedAt: string;
  /** Absent while the node is still running. */
  durationMs: number | null;
  running: boolean;
  failed: boolean;
  warning: boolean;
  waiting: boolean;
  interrupted: boolean;
  rows: DetailRow[];
  /** Tokens reported by `llm.completed` events inside this node. */
  tokens: number;
};

export function nodeLabel(node: string): string {
  return NODE_LABELS[node] ?? node.replace(/_/g, " ");
}

export function actionLabel(action: string): string {
  if (action === "inspect_inputs") return "Inspect input data";
  if (action.startsWith("run_")) return `Run ${action.slice(4).replace(/_/g, "-").toUpperCase()}`;
  return action.replace(/_/g, " ");
}

function rowKind(event: TraceEvent): RowKind {
  const level = eventLevel(event);
  if (level === "error" || level === "warning") return level;
  const eventType = event.event_type;
  if (eventType.startsWith("tool.")) return "tool";
  if (eventType.startsWith("llm.")) return "llm";
  if (eventType.startsWith("run.")) return "lifecycle";
  return "detail";
}

/**
 * A one-line reading of an event, drawn from its payload.
 *
 * Deliberately shallow: the whole payload stays available underneath, and a
 * summary that tried to explain an event it did not recognise would be the
 * window putting words in the agent's mouth.
 */
export function summarise(event: TraceEvent): string {
  const payload = event.payload ?? {};
  const named = (key: string) =>
    typeof payload[key] === "string" ? (payload[key] as string) : null;

  switch (event.event_type) {
    case "llm.completed": {
      const total = payload.total_tokens ?? payload.tokens;
      return typeof total === "number" ? `${total.toLocaleString()} tokens` : "";
    }
    case "plan.created":
      return named("workflow") ?? named("action") ?? "";
    case "decision.recorded":
      return named("action") ?? named("reason_code") ?? "";
    case "policy.loaded":
      return named("policy_hash")?.slice(0, 12) ?? "";
    case "error.recorded":
      return [named("error_type"), named("message")].filter(Boolean).join(": ");
    case "tool.started":
      return named("action") ?? named("command") ?? "";
    case "tool.completed":
      return [named("action"), named("status"), named("summary")].filter(Boolean).join(" · ");
    default: {
      const issues = payload.issues;
      if (Array.isArray(issues) && issues.length > 0) return issues.join(", ");
      return named("reason") ?? named("status") ?? "";
    }
  }
}

/**
 * Fold the event stream into one stage per node execution.
 *
 * `node.started` opens a stage and `node.finished` closes it, so a node that
 * runs twice — `evaluate_plan` after a recovery, say — gets two stages rather
 * than one with its events interleaved.
 */
export function buildStages(events: TraceEvent[]): Stage[] {
  const stages: Stage[] = [];
  const open = new Map<string, Stage>();

  const currentFor = (node: string, startedAt: string, runId: string): Stage => {
    const key = `${runId}:${node}`;
    const existing = open.get(key);
    if (existing) return existing;
    const stage: Stage = {
      id: `${runId}-${node}-${stages.length}`,
      node,
      runId,
      label: nodeLabel(node),
      startedAt,
      durationMs: null,
      running: true,
      failed: false,
      warning: false,
      waiting: false,
      interrupted: false,
      rows: [],
      tokens: 0,
    };
    stages.push(stage);
    open.set(key, stage);
    return stage;
  };

  for (const event of events) {
    const stage = currentFor(event.node, event.occurred_at, event.run_id);

    if (event.event_type.startsWith("tool.") && typeof event.payload.action === "string") stage.label = actionLabel(event.payload.action);

    if (event.event_type === "node.started") continue;

    if (event.event_type === "node.finished") {
      const duration = event.payload?.duration_ms;
      stage.durationMs = typeof duration === "number" ? duration : null;
      stage.running = false;
      stage.waiting = false;
      open.delete(`${event.run_id}:${event.node}`);
      continue;
    }

    if (event.event_type === "llm.completed") {
      const total = event.payload?.total_tokens;
      if (typeof total === "number") stage.tokens += total;
    }
    const level = eventLevel(event);
    if (level === "error") stage.failed = true;
    if (level === "warning") stage.warning = true;
    if (event.event_type === "error.recorded") stage.running = false;

    if (["run.finished", "run.paused", "run.interrupted"].includes(event.event_type)) {
      for (const [key, active] of open) {
        if (active.runId !== event.run_id) continue;
        if (event.event_type === "run.paused") active.waiting = active.running;
        else active.waiting = false;
        if (event.event_type === "run.interrupted") active.interrupted = active.running;
        active.running = false;
        // A terminal event closes all remaining nodes; a pause may resume them.
        if (event.event_type !== "run.paused") open.delete(key);
      }
    }
    if (event.event_type === "run.started") { stage.running = true; stage.waiting = false; }
    if (event.event_type === "run.resumed") {
      for (const active of open.values()) {
        if (active.runId === event.run_id && active.waiting) { active.waiting = false; active.running = true; }
      }
    }

    stage.rows.push({
      id: event.event_id,
      kind: rowKind(event),
      eventType: event.event_type,
      occurredAt: event.occurred_at,
      summary: summarise(event),
      payload: event.payload ?? {},
    });
  }

  return stages;
}

export type ActivityRun = {
  id: string;
  startedAt: string;
  endedAt: string | null;
  elapsedMs: number | null;
  status: "Running" | "Waiting" | "Completed" | "Failed" | "Interrupted";
  stages: Stage[];
};

/** Runs enclose graph nodes. The CLI lifecycle is the run header, not a peer node. */
export function buildRuns(events: TraceEvent[]): ActivityRun[] {
  const groups = new Map<string, TraceEvent[]>();
  for (const event of events) {
    const group = groups.get(event.run_id) ?? [];
    group.push(event);
    groups.set(event.run_id, group);
  }
  const stages = buildStages(events);
  return Array.from(groups, ([id, group]) => {
    const ordered = [...group].sort((a, b) => a.sequence - b.sequence);
    const first = ordered.find((event) => event.event_type === "run.started") ?? ordered[0];
    const lifecycle = ordered.filter((event) => event.event_type.startsWith("run."));
    const last = lifecycle.at(-1);
    const terminal = last && ["run.finished", "run.interrupted"].includes(last.event_type) ? last : null;
    const begin = timestamp(first.occurred_at);
    const end = timestamp(terminal?.occurred_at);
    const status: ActivityRun["status"] = last?.event_type === "run.interrupted" ? "Interrupted" :
      last?.event_type === "run.paused" ? "Waiting" : terminal ?
        (terminal.payload.status === "failed" ? "Failed" : "Completed") : "Running";
    return { id, startedAt: first.occurred_at, endedAt: terminal?.occurred_at ?? null,
      elapsedMs: begin !== null && end !== null && end >= begin ? end - begin : null,
      status, stages: stages.filter((stage) => stage.runId === id && stage.node !== "cli") };
  });
}
