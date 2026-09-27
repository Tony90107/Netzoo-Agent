import { useMemo } from "react";
import type { TraceEvent } from "../../transport/protocol";
import { buildResults, outputPath, repairSteps } from "./results";
import { fullTime, durationLabel } from "./time";
import { useTimeZone } from "./timeZone";

export function RunResults({ trace, onOpenOutput }: { trace: TraceEvent[]; onOpenOutput?: (path: string) => void }) {
  const runs = useMemo(() => buildResults(trace), [trace]);
  const { zone } = useTimeZone();
  return <div className="pane__scroll run-results">
    {!runs.length ? <p className="pane__empty">Results appear when a run is recorded.</p> : null}
    {[...runs].reverse().map((run, index) => <article key={run.id} className={`run-result${run.status === "Failed" ? " is-failed" : ""}`}>
      <header><h2>Run {runs.length - index} · {run.id.slice(0, 8)}</h2><strong className="run-result__outcome">{run.outcome}</strong></header>
      <p className="log__clock">{fullTime(run.startedAt, zone)}{run.endedAt ? ` · elapsed ${durationLabel(run.elapsedMs)}` : " · no end time recorded"}{run.tokens !== null ? ` · ${run.tokens.toLocaleString()} tokens` : ""}</p>
      <p className="run-result__metrics">{run.tools.length} {run.tools.length === 1 ? "tool result" : "tool results"} · {run.outputs} recorded output paths{run.plannedOutputs ? ` · ${run.plannedOutputs} planned output paths` : ""} · {run.warnings} {run.warnings === 1 ? "warning" : "warnings"}</p>
      {run.tools.map((tool) => <section key={tool.id} className={`run-result__tool${tool.errors.length ? " has-error" : ""}`}>
        <h3>{tool.action} <span className="tl__status">{tool.superseded ? "Superseded attempt" : tool.status === "dry_run" ? "Preview only" : tool.status === "success" ? "Passed" : tool.status || "Status unavailable"}</span></h3>
        {tool.summary ? <p>{tool.summary}</p> : null}
        {tool.metrics.length ? <p className="run-result__metrics">{tool.metrics.map(([key, value]) => `${key.replace(/_/g, " ")}: ${Number(value).toLocaleString()}`).join(" · ")}</p> : null}
        {tool.artifacts.length ? <><h4>{tool.status === "dry_run" ? "Planned output paths" : "Recorded outputs"}</h4><ul className="run-result__outputs">{[...new Set(tool.artifacts)].map((path) => <li key={path}>
          <code>{path.replace(/^\/work\//, "")}</code>
          {tool.status === "success" && !tool.superseded && outputPath(path) && onOpenOutput ? <button className="btn btn--quiet btn--small" type="button" onClick={() => onOpenOutput(outputPath(path)!)}>Preview output</button> : null}
        </li>)}</ul></> : <p className="set__note">No output files recorded for this step.</p>}
        {tool.repairs.length ? <div className="run-result__repair"><h4>Suggested repair{tool.superseded ? " for this earlier attempt" : ""}</h4><ol>{tool.repairs.map((step) => <li key={step}>{step}</li>)}</ol><details><summary>Full error · {tool.errors.length} {tool.errors.length === 1 ? "item" : "items"}</summary><ul>{tool.errors.map((error, i) => <li key={i}>{error}</li>)}</ul></details></div> : null}
        {tool.warnings.length ? <details className="run-result__warnings"><summary>{tool.warnings.length} {tool.warnings.length === 1 ? "warning" : "warnings"}</summary><ul>{[...new Set(tool.warnings)].map((warning) => <li key={warning}>{warning}</li>)}</ul></details> : null}
      </section>)}
      {run.errors.map((error) => <div className="run-result__repair" key={error.id}><h3>Execution error</h3><p>{error.message}</p><ol>{repairSteps([error.message]).map((step) => <li key={step}>{step}</li>)}</ol></div>)}
      {!run.tools.length ? <p className="set__note">No tool results recorded. Check Timeline for planning, waiting or conversation activity.</p> : null}
      {run.status === "Failed" && !run.errors.length && !run.tools.some((tool) => tool.errors.length) ? <div className="run-result__repair"><h4>Suggested checks</h4><p>The run ended as failed without a detailed cause in the available events. Check Log for the failing stage and reload the saved Activity if events are missing.</p></div> : null}
    </article>)}
    {runs.some((run) => run.tools.some((tool) => tool.artifacts.length)) ? <p className="set__note">These are the paths recorded at execution time. Preview opens the current file; it may have changed or been removed since this run.</p> : null}
  </div>;
}
