/** The compact run timeline and its detailed chronological log. */
import { useMemo, useState } from "react";

import { RunLog } from "./RunLog";
import { buildLog } from "./log";
import { entryTimestamp, type Entry } from "../../transport/session";
import type { TraceEvent } from "../../transport/protocol";
import { Stage, buildRuns, type ActivityRun } from "./model";
import { clockLabel, fullTime, durationLabel } from "./time";

import { useTimeZone } from "./timeZone";
import { RunResults } from "./RunResults";

const SYSTEM_NODES = new Set(["apply_project_policy", "retrieve_memory", "consolidate_memory"]);

function StageRow({ stage, busy, onOpenOutput }: { stage: Stage; busy: boolean; onOpenOutput?: (path: string) => void }) {
  const { zone } = useTimeZone();
  const [open, setOpen] = useState(stage.failed);
  const status = stage.failed ? "Failed" : stage.interrupted ? "Interrupted" : stage.waiting ? "Waiting" : stage.running ? (busy ? "Running" : "Awaiting events") : stage.warning ? "Warning" : "Completed";
  const marker = stage.failed ? "✕" : stage.interrupted || stage.warning ? "!" : stage.waiting || stage.running ? "●" : "✓";

  return (
    <li className={`tl__stage${stage.failed ? " is-failed" : ""}${stage.running ? " is-running" : ""}${stage.warning ? " is-warning" : ""}`}>
      <button
        type="button"
        className="tl__head"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
      >
        <span className="tl__marker" aria-hidden="true">{marker}</span>
        <span className="tl__label">{stage.label}</span>
        <span className="tl__status">{status}</span>
        {stage.durationMs !== null ? (
          <span className="tl__duration">{durationLabel(stage.durationMs)}</span>
        ) : null}
        {stage.rows.length > 0 ? (
          <span className="tl__count">{open ? "−" : `+${stage.rows.length}`}</span>
        ) : null}
      </button>
      <div className="tl__stage-clock"><time dateTime={stage.startedAt} title={fullTime(stage.startedAt, zone)}>{clockLabel(stage.startedAt, zone)}</time></div>
      {open ? (
        <div>
        {stage.tokens > 0 ? <p className="tl__metrics">{stage.tokens.toLocaleString()} tokens</p> : null}
        {stage.rows.length === 0 ? <p className="tl__metrics">No additional events.</p> : null}
        <ul className="tl__rows">
          {stage.rows.map((row) => (
            <li key={row.id} className={`tl__row tl__row--${row.kind}`}>
              <details>
                <summary><time dateTime={row.occurredAt} title={fullTime(row.occurredAt, zone)}>{clockLabel(row.occurredAt, zone)}</time> <code className="tl__event">{row.eventType}</code></summary>
                {row.summary ? <p className="tl__summary">{row.summary}</p> : null}
                <pre className="tl__payload">{JSON.stringify(row.payload, null, 2)}</pre>
                {Array.isArray(row.payload.artifacts) ? row.payload.artifacts.filter((path): path is string => typeof path === "string").map((path) => (
                  <div className="tl__artifact" key={path}>{onOpenOutput && (path.startsWith("outputs/") || path.startsWith("/work/outputs/")) ?
                    <button className="btn btn--quiet btn--small" type="button" onClick={() => onOpenOutput(path.replace(/^\/work\//, ""))}>Open {path.split("/").pop()}</button> : <code>{path}</code>}</div>
                )) : null}
              </details>
            </li>
          ))}
        </ul>
        </div>
      ) : null}
    </li>
  );
}

type TimelineItem =
  | { kind: "run"; at: number; run: ActivityRun; index: number }
  | { kind: "user"; at: number; entry: Extract<Entry, { kind: "user" }> };

export function Timeline({ trace, entries, sessionId, busy, incomplete, onOpenOutput, onExpand, initialTab = "timeline" }: { trace: TraceEvent[]; entries: Entry[]; sessionId: string; busy: boolean; incomplete: boolean; onOpenOutput?: (path: string) => void; onExpand?: () => void; initialTab?: "timeline" | "log" | "results" }) {
  const { zone } = useTimeZone();
  const [tab, setTab] = useState<"timeline" | "log" | "results">(initialTab);
  const log = useMemo(() => buildLog(trace, entries), [trace, entries]);
  const runs = useMemo(() => buildRuns(trace), [trace]);
  const userEntries = entries.filter(
    (entry): entry is Extract<Entry, { kind: "user" }> => entry.kind === "user",
  );
  const items: TimelineItem[] = [
    ...runs.map((run, index) => ({
      kind: "run" as const,
      at: Date.parse(run.startedAt) || 0,
      run, index,
    })),
    ...userEntries.map((entry) => ({
      kind: "user" as const,
      at: Date.parse(entryTimestamp(entry) ?? "") || 0,
      entry,
    })),
  ].sort((left, right) => left.at - right.at);

  return (
    <section className="pane">
      <header className="pane__header tl__header">
        <span>Run activity</span>
        {onExpand ? <button className="pane__action" type="button" onClick={onExpand}>Expand</button> : null}
        <div className="tl__tabs" role="group" aria-label="Run activity view">
          <button
            type="button"
            aria-pressed={tab === "timeline"}
            onClick={() => setTab("timeline")}
          >
            Timeline
          </button>
          <button type="button" aria-pressed={tab === "results"} onClick={() => setTab("results")}>Results</button>
          <button
            type="button"
            aria-pressed={tab === "log"}
            onClick={() => setTab("log")}
          >
            Log
          </button>
        </div>
      </header>
      {incomplete ? <p className="tl__incomplete" role="status">Activity is incomplete: some events are missing, still loading, or the run has no sealed end record. Exports contain only the available snapshot.</p> : null}
      {tab === "results" ? <RunResults trace={trace} onOpenOutput={onOpenOutput} /> : tab === "log" ? (
        <RunLog rows={log} sessionId={sessionId} incomplete={incomplete} />
      ) : items.length === 0 ? (
        <div className="pane__empty">The agent's steps appear here while it works.</div>
      ) : (
        <div className="pane__scroll">
          <p className="log__clock tl__clock">Display time · {zone} · oldest first</p>
          <ol className="tl">
            {items.map((item) => item.kind === "run" ? (
              <li className={`tl__run${item.run.status === "Failed" ? " is-failed" : ""}`} key={item.run.id}>
                <details open={item.index === runs.length - 1}>
                  <summary className="tl__run-head">
                    <strong>Run {item.index + 1}</strong><span className="tl__status">{item.run.status === "Running" && !busy ? "Awaiting events" : item.run.status}</span>
                    <span className="tl__run-id" title={item.run.id}>{item.run.id.slice(0, 8)}</span>
                    <span className="tl__run-time">{fullTime(item.run.startedAt, zone)}</span>
                    <span className="tl__run-time">{item.run.endedAt ? `Finished ${clockLabel(item.run.endedAt, zone)} · elapsed ${durationLabel(item.run.elapsedMs)}` : item.run.status === "Waiting" ? "Waiting for your input" : "End time not recorded"}</span>
                  </summary>
                  <ol className="tl__run-stages">{item.run.stages.filter((stage) => !SYSTEM_NODES.has(stage.node) || stage.failed).map((stage) => <StageRow key={stage.id} stage={stage} busy={busy} onOpenOutput={onOpenOutput} />)}</ol>
                  {item.run.stages.some((stage) => SYSTEM_NODES.has(stage.node) && !stage.failed) ? <details className="tl__system-stages"><summary>System stages</summary><ol className="tl__run-stages">{item.run.stages.filter((stage) => SYSTEM_NODES.has(stage.node) && !stage.failed).map((stage) => <StageRow key={stage.id} stage={stage} busy={busy} onOpenOutput={onOpenOutput} />)}</ol></details> : null}
                  {item.run.stages.length === 0 ? <p className="tl__metrics">No workflow stages recorded.</p> : null}
                </details>
              </li>
            ) : (
              <li className="tl__user" key={`user-${item.entry.id}`}>
                <span className="tl__user-marker" aria-hidden="true">●</span>
                <span className="tl__user-label">You{item.entry.action === "confirmation" ? " · confirmation" : item.entry.action === "command" ? " · command" : ""}</span>
                <time dateTime={entryTimestamp(item.entry)} title={fullTime(entryTimestamp(item.entry), zone)}>{clockLabel(entryTimestamp(item.entry), zone)}</time>
                <div className="tl__user-text">{item.entry.text}</div>
              </li>
            ))}
          </ol>
        </div>
      )}
    </section>
  );
}
