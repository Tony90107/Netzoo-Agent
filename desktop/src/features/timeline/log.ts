import { entryTimestamp, type Entry } from "../../transport/session";
import type { TraceEvent } from "../../transport/protocol";
import { eventLevel, summarise, nodeLabel, actionLabel, type EventLevel } from "./model";
import { timestamp, fullTime } from "./time";

export type LogSource = "user" | "agent" | "tool" | "system";
export type LogRow = {
  id: string;
  at: string;
  source: LogSource;
  level: EventLevel;
  label: string;
  summary: string;
  payload?: Record<string, unknown>;
  eventType?: string;
  node?: string;
  runId?: string;
  sequence?: number;
  timeSource?: Entry["timeSource"];
};

const EVENT_TITLES: Record<string, string> = {
  "run.started": "Run started", "run.finished": "Run finished", "run.paused": "Waiting for input", "run.resumed": "Run resumed", "run.interrupted": "Run interrupted",
  "plan.created": "Work Plan created", "plan.approved": "Plan approved", "plan.deferred": "Plan needs attention", "plan.rejected": "Plan rejected",
  "tool.started": "Workflow started", "tool.completed": "Workflow finished", "error.recorded": "Execution error", "evaluation.recorded": "Result reviewed",
};

export function isImportant(row: LogRow): boolean {
  if (!row.eventType) return row.summary.trim().length > 0;
  if (row.level === "error") return true;
  if (row.eventType.startsWith("routing.")) return false;
  return row.level === "warning" || row.eventType in EVENT_TITLES;
}

function readableSummary(event: TraceEvent): string {
  const payload = event.payload ?? {};
  if (event.event_type === "tool.started" || event.event_type === "plan.approved" || event.event_type === "run.finished") return "";
  if (event.event_type === "tool.completed") return typeof payload.summary === "string" ? payload.summary : summarise(event);
  return summarise(event);
}

function readableTitle(event: TraceEvent): string {
  const action = event.payload?.action;
  if (event.event_type.startsWith("tool.") && typeof action === "string") {
    const verdict = event.event_type === "tool.started" ? "Started" : event.payload.status === "failed" ? "Failed" : event.payload.status === "dry_run" ? "Preview ready" : "Finished";
    return `${actionLabel(action)} · ${verdict}`;
  }
  return EVENT_TITLES[event.event_type] ?? nodeLabel(event.node);
}

export function buildLog(trace: TraceEvent[], entries: Entry[]): LogRow[] {
  const messages: LogRow[] = entries.map((entry) => ({
    id: `message-${entry.id}`, at: entryTimestamp(entry) ?? "",
    source: entry.kind === "user" ? "user" : entry.kind === "notice" || entry.kind === "error" ? "system" : "agent",
    level: entry.kind === "error" ? "error" : "info",
    label: entry.kind === "user" ? `You${entry.action === "confirmation" ? " · confirmation" : entry.action === "command" ? " · command" : ""}` : entry.kind === "error" ? entry.errorType : entry.kind === "notice" ? "System" : "Agent",
    summary: entry.text,
    timeSource: entry.timeSource,
  }));
  const events: LogRow[] = trace.map((event) => ({
    id: event.event_id, at: event.occurred_at,
    source: event.event_type.startsWith("tool.") ? "tool" : event.event_type.startsWith("llm.") ? "agent" : "system",
    level: eventLevel(event),
    label: readableTitle(event),
    summary: readableSummary(event), payload: event.payload ?? {},
    eventType: event.event_type, node: event.node, runId: event.run_id, sequence: event.sequence,
  }));
  return [...messages, ...events].sort((a, b) => {
    const difference = (timestamp(a.at) ?? 0) - (timestamp(b.at) ?? 0);
    return difference || (a.runId && a.runId === b.runId ? (a.sequence ?? 0) - (b.sequence ?? 0) : 0);
  });
}

export function filterLog(rows: LogRow[], query: string, source: LogSource | "all", level: EventLevel | "all"): LogRow[] {
  const needle = query.trim().toLowerCase();
  return rows.filter((row) => (source === "all" || row.source === source) &&
    (level === "all" || row.level === level) &&
    (!needle || `${row.at} ${row.label} ${row.eventType ?? ""} ${row.node ?? ""} ${row.runId ?? ""} ${row.summary} ${JSON.stringify(row.payload ?? {})}`.toLowerCase().includes(needle)));
}

export function logText(rows: LogRow[], zone?: string): string {
  return rows.map((row) => `[${zone ? fullTime(row.at, zone) : row.at || "time unavailable"}]${zone && row.at ? ` [original ${row.at}]` : ""} [${row.level}] [${row.source}] ${row.label}${row.eventType ? ` [${row.eventType}] [run ${row.runId}] [sequence ${row.sequence}]` : ""}${row.timeSource === "received" ? " [received time; original time unavailable]" : ""}\n${row.summary}${row.payload ? `\n${JSON.stringify(row.payload)}` : ""}`).join("\n\n");
}
