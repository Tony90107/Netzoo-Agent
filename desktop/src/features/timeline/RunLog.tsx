import { Fragment, useEffect, useMemo, useRef, useState } from "react";
import { exportLog } from "../../transport/export";
import { filterLog, logText, isImportant, type LogRow, type LogSource } from "./log";
import type { EventLevel } from "./model";
import { actionLabel } from "./model";
import { clockLabel, dateLabel, fullTime } from "./time";
import { Markdown } from "../conversation/Markdown";

import { useTimeZone } from "./timeZone";

const PAGE_SIZE = 200;

type RunChoice = { id: string; workflow: string; outcome: string };

function runChoices(rows: LogRow[]): RunChoice[] {
  const ids = Array.from(new Set(rows.flatMap((row) => row.runId ? [row.runId] : [])));
  return ids.map((id) => {
    const events = rows.filter((row) => row.runId === id);
    let workflow = "";
    let outcome = "Running";
    for (const row of events) {
      const namedWorkflow = row.eventType === "plan.created" ? row.payload?.workflow : undefined;
      if (typeof namedWorkflow === "string" && namedWorkflow.trim()) {
        workflow = namedWorkflow === "NO-TOOL" ? "Advice only" : namedWorkflow;
      }
      if (!workflow && row.eventType?.startsWith("tool.")) {
        const action = row.payload?.action;
        if (typeof action === "string" && action.trim()) workflow = actionLabel(action).replace(/^Run\s+/, "");
      }
      if (row.eventType === "run.started" || row.eventType === "run.resumed") outcome = "Running";
      else if (row.eventType === "run.paused") outcome = "Waiting for input";
      else if (row.eventType === "run.interrupted") outcome = "Interrupted";
      else if (row.eventType === "run.finished") {
        outcome = row.payload?.status === "failed" ? "Failed" : "Completed";
      }
    }
    return { id, workflow: workflow || "General activity", outcome };
  });
}

function marker(row: LogRow): string {
  if (row.level === "error") return "!";
  if (row.source === "user") return "U";
  if (row.eventType === "run.finished") return "✓";
  if (row.eventType === "run.started") return "▶";
  if (row.level === "warning") return "!";
  if (row.source === "tool") return "◆";
  if (row.source === "agent") return "A";
  return "•";
}

export function RunLog({ rows, sessionId, incomplete }: { rows: LogRow[]; sessionId: string; incomplete: boolean }) {
  const { zone } = useTimeZone();
  const [detail, setDetail] = useState<"highlights" | "all">("highlights");
  const [run, setRun] = useState("all");
  const [query, setQuery] = useState("");
  const [source, setSource] = useState<LogSource | "all">("all");
  const [level, setLevel] = useState<EventLevel | "all">("all");
  const [end, setEnd] = useState<number | null>(null);
  const [feedback, setFeedback] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [follow, setFollow] = useState(true);
  const list = useRef<HTMLDivElement>(null);
  const scope = JSON.stringify([detail, run, query, source, level]);
  const previousScope = useRef(scope);
  const runs = useMemo(() => runChoices(rows), [rows]);
  const selected = useMemo(() => rows.filter((row) => (detail === "all" || isImportant(row)) && (run === "all" || row.runId === run)), [rows, detail, run]);
  const filtered = useMemo(() => filterLog(selected, query, source, level), [selected, query, source, level]);
  const pageEnd = Math.min(end ?? filtered.length, filtered.length);
  const pageStart = Math.max(0, pageEnd - PAGE_SIZE);
  const visible = filtered.slice(pageStart, pageEnd);
  const dates = visible.length ? Array.from(new Set(visible.map((row) => dateLabel(row.at, zone)))) : [];

  useEffect(() => {
    if (scope !== previousScope.current) {
      previousScope.current = scope;
      setFollow(false);
      if (list.current) list.current.scrollTop = 0;
    } else if (follow && end === null && list.current) list.current.scrollTop = list.current.scrollHeight;
  }, [follow, end, filtered, scope]);

  async function copy() {
    setError(""); setFeedback("");
    try { await navigator.clipboard.writeText(logText(filtered, zone)); setFeedback(`Copied ${filtered.length} matching records.`); }
    catch { setError("Clipboard access failed. Export the log or select the text to copy it."); }
  }

  async function save(format: "txt" | "json") {
    setSaving(true); setError(""); setFeedback("");
    try {
      const contents = format === "txt" ? `NetZoo session ${sessionId}\nTime zone: ${zone}\n${incomplete ? "Incomplete: some events were not replayed.\n" : ""}Filters: ${detail}, run ${run}, ${source}, ${level}, ${query || "none"}\n\n${logText(filtered, zone)}` :
        JSON.stringify({ session_id: sessionId, exported_at: new Date().toISOString(), incomplete, time_zone: zone, filters: { query, source, level, detail, run }, records: filtered }, null, 2);
      setFeedback(await exportLog(contents, format));
    } catch (problem) { setError(`Export failed: ${String(problem)}`); }
    finally { setSaving(false); }
  }

  return <>
    <div className="log__controls">
      <div className="log__toolbar">
      <div className="log__view" role="group" aria-label="Log detail level">
        <button type="button" aria-pressed={detail === "highlights"} onClick={() => { setDetail("highlights"); setEnd(null); }}>Highlights</button>
        <button type="button" aria-pressed={detail === "all"} onClick={() => { setDetail("all"); setEnd(null); }}>All events</button>
      </div>
      <label className="log__follow"><input type="checkbox" checked={follow} onChange={(event) => { setFollow(event.target.checked); if (event.target.checked) setEnd(null); }} />Follow latest</label>
      </div>
      <p className="log__clock">Display time · {zone}{dates.length ? ` · ${dates.length === 1 ? dates[0] : `${dates[0]} – ${dates.at(-1)}`}` : ""} · oldest first</p>
      <div className="log__primary">
      <label>Search log<input type="search" placeholder="Tool, stage, message, or output" value={query} onChange={(event) => { setQuery(event.target.value); setEnd(null); }} /></label>
      {runs.length ? <label>Run<select value={run} onChange={(event) => { setRun(event.target.value); setEnd(null); }}>
        <option value="all">All runs and messages · {runs.length} {runs.length === 1 ? "run" : "runs"}</option>
        {runs.map((item, index) => <option key={item.id} value={item.id} title={item.id}>{item.workflow} · {item.outcome} · Run {index + 1} · {item.id.slice(0, 8)}</option>)}
      </select></label> : null}
      </div>
      {run !== "all" ? <p className="log__count">Execution events for this run. Conversation messages are in All runs and messages.</p> : null}
      <div className="log__secondary">
      <details className="log__options"><summary>Filters and export</summary>
      <div className="log__filters">
        <label>Source<select value={source} onChange={(event) => { setSource(event.target.value as LogSource | "all"); setEnd(null); }}>
          <option value="all">All sources</option><option value="user">You</option><option value="agent">Agent</option><option value="tool">Tools</option><option value="system">System</option>
        </select></label>
        <label>Status<select value={level} onChange={(event) => { setLevel(event.target.value as EventLevel | "all"); setEnd(null); }}>
          <option value="all">All statuses</option><option value="info">Information</option><option value="warning">Warnings</option><option value="error">Errors</option>
        </select></label>
      </div>
      <div className="log__actions">
        <button className="btn btn--quiet btn--small" type="button" disabled={!filtered.length} onClick={() => void copy()}>Copy matches</button>
        <button className="btn btn--quiet btn--small" type="button" disabled={!filtered.length || saving} onClick={() => void save("txt")}>Export text</button>
        <button className="btn btn--quiet btn--small" type="button" disabled={!filtered.length || saving} onClick={() => void save("json")}>Export JSON</button>
      </div>
      </details>
      <p className="log__count">{filtered.length.toLocaleString()} matches · {rows.length.toLocaleString()} records{detail === "highlights" ? ` · ${rows.filter((row) => !isImportant(row)).length} internal events hidden` : ""}</p>
      </div>
      {feedback ? <p className="log__feedback" role="status">{feedback}</p> : null}
      {error ? <p className="fv__error" role="alert">{error}</p> : null}
    </div>
    <div ref={list} className="pane__scroll tl__log" role="region" aria-label="Chronological execution log" onScroll={(event) => {
      const area = event.currentTarget;
      if (area.scrollHeight - area.scrollTop - area.clientHeight > 24) setFollow(false);
    }}>
      {visible.length === 0 ? <div className="pane__empty">{rows.length ? "No matching events. Clear the filters to see this run." : "Execution events and messages will appear here."}</div> :
        <ol className="tl__log-list" aria-label="Execution timeline">{visible.map((row, index) => (
          <Fragment key={row.id}>
            {index === 0 || dateLabel(visible[index - 1].at, zone) !== dateLabel(row.at, zone) ? <li className="log__date">{dateLabel(row.at, zone)}</li> : null}
          <li className={`tl__log-row tl__log-row--${row.source} tl__log-row--${row.level}${row.eventType?.startsWith("run.") ? " log__run-boundary" : ""}`}>
            <span className="log__rail-node" aria-hidden="true">{marker(row)}</span>
            <div className="log__row-content">
            <div className="log__row-head">
              <time dateTime={row.at || undefined} title={`${fullTime(row.at, zone)}${row.timeSource === "received" ? " · received time; original time unavailable" : ""}`}>{clockLabel(row.at, zone)}</time>
              <span className="log__source">{row.source === "user" ? "You" : row.source === "tool" ? "Tool" : row.source === "agent" ? "Agent" : "System"}</span>
              {row.level !== "info" ? <span className="log__severity">{row.level}</span> : null}
              {row.timeSource === "received" ? <span className="log__time-note">Received time</span> : null}
              {row.runId ? <span className="log__run-ref" title={row.runId}>Run {runs.findIndex((item) => item.id === row.runId) + 1}{detail === "all" && row.sequence !== undefined ? ` · #${row.sequence}` : ""}</span> : null}
            </div>
            <span className="tl__log-label">{row.label}</span>
            {detail === "all" && row.eventType ? <code className="log__event-type">{row.eventType}</code> : null}
            {row.summary ? <span className="tl__log-message">{row.summary.length > 240 ? `${row.summary.slice(0, 240)}…` : row.summary}</span> : null}
            {row.summary.length > 240 ? <details className="log__payload"><summary>Read full message</summary>{row.source === "agent" ? <Markdown>{row.summary}</Markdown> : <p className="log__full-message">{row.summary}</p>}</details> : null}
            {row.eventType || row.payload && Object.keys(row.payload).length > 0 ? <details className="log__payload"><summary>Technical details</summary>
              {row.eventType ? <p><code>{row.eventType}</code> · {row.node}<br />Run {row.runId} · event #{row.sequence}<br />Original timestamp: {row.at}</p> : null}
              {row.payload ? <pre>{JSON.stringify(row.payload, null, 2)}</pre> : null}
            </details> : null}
            </div>
          </li>
          </Fragment>
        ))}</ol>}
    </div>
    {filtered.length > PAGE_SIZE ? <div className="log__paging">
      <button className="btn btn--quiet btn--small" type="button" disabled={pageStart === 0} onClick={() => { setFollow(false); setEnd(pageStart); }}>Older</button>
      <span>{pageStart + 1}–{pageEnd}</span>
      <button className="btn btn--quiet btn--small" type="button" disabled={pageEnd >= filtered.length} onClick={() => setEnd(pageEnd + PAGE_SIZE >= filtered.length ? null : pageEnd + PAGE_SIZE)}>Newer</button>
      {end !== null ? <button className="btn btn--quiet btn--small" type="button" onClick={() => { setEnd(null); setFollow(true); }}>Latest</button> : null}
    </div> : null}
  </>;
}
