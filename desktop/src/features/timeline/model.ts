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

export type RowKind = "detail" | "tool" | "llm" | "error" | "lifecycle";

export type DetailRow = {
  id: string;
  kind: RowKind;
  eventType: string;
  summary: string;
  payload: Record<string, unknown>;
};

export type Stage = {
  id: string;
  node: string;
  label: string;
  /** Absent while the node is still running. */
  durationMs: number | null;
  running: boolean;
  failed: boolean;
  rows: DetailRow[];
  /** Tokens reported by `llm.completed` events inside this node. */
  tokens: number;
};

function label(node: string): string {
  return NODE_LABELS[node] ?? node.replace(/_/g, " ");
}

function rowKind(eventType: string): RowKind {
  if (eventType === "error.recorded") return "error";
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
function summarise(event: TraceEvent): string {
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
    case "tool.completed":
      return named("action") ?? named("command") ?? "";
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

  const currentFor = (node: string): Stage => {
    const existing = open.get(node);
    if (existing) return existing;
    const stage: Stage = {
      id: `${node}-${stages.length}`,
      node,
      label: label(node),
      durationMs: null,
      running: true,
      failed: false,
      rows: [],
      tokens: 0,
    };
    stages.push(stage);
    open.set(node, stage);
    return stage;
  };

  for (const event of events) {
    const stage = currentFor(event.node);

    if (event.event_type === "node.started") continue;

    if (event.event_type === "node.finished") {
      const duration = event.payload?.duration_ms;
      stage.durationMs = typeof duration === "number" ? duration : null;
      stage.running = false;
      open.delete(event.node);
      continue;
    }

    if (event.event_type === "llm.completed") {
      const total = event.payload?.total_tokens;
      if (typeof total === "number") stage.tokens += total;
    }
    if (event.event_type === "error.recorded") stage.failed = true;

    stage.rows.push({
      id: event.event_id,
      kind: rowKind(event.event_type),
      eventType: event.event_type,
      summary: summarise(event),
      payload: event.payload ?? {},
    });
  }

  return stages;
}
