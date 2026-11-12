/** Description: what each run did, in words — the request, the method, what ran, the outputs and the conclusion. */
import { useMemo, useState } from "react";

import type { Entry } from "../../transport/session";
import type { TraceEvent } from "../../transport/protocol";
import { AutoTagChips } from "../files/OutputTags";
import { ExternalLink } from "../help/ExternalLink";
import { buildDescriptions, descriptionText, kindLabel, outcomeLabel, type RunDescription, type SummaryFile, type SummaryMeaning } from "./description";
import { outputPath, repairSteps } from "./results";
import { durationLabel, fullTime } from "./time";
import { useTimeZone } from "./timeZone";

function Outputs({ paths, onOpenOutput }: { paths: string[]; onOpenOutput?: (path: string) => void }) {
  return <ul className="run-result__outputs">{paths.map((path) => <li key={path}>
    <code>{path.replace(/^\/work\//, "")}</code>
    {outputPath(path) && onOpenOutput ? <button className="btn btn--quiet btn--small" type="button" onClick={() => onOpenOutput(outputPath(path)!)}>Preview output</button> : null}
  </li>)}</ul>;
}

function sizeLabel(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
  return `${(bytes / 1024 ** 3).toFixed(2)} GB`;
}

/** Each output file: its name opens the file, then what it is and how to read it. */
function Files({ files, onOpenOutput }: { files: SummaryFile[]; onOpenOutput?: (path: string) => void }) {
  return <ul className="run-desc__files">{files.map((file) => {
    const name = file.path.split("/").filter(Boolean).pop() ?? file.path;
    const openable = file.written && outputPath(file.path) && onOpenOutput;
    return <li key={file.path}>
      {openable ? <button type="button" className="run-desc__file-link" title={`Open ${file.path}`} onClick={() => onOpenOutput!(outputPath(file.path)!)}>{name}</button>
        : <code title={file.path}>{name}</code>}
      {!file.written ? <span className="run-desc__note-inline"> · not written yet</span> : file.bytes !== undefined ? <span className="run-desc__note-inline"> · {sizeLabel(file.bytes)}</span> : null}
      <span className="run-desc__file-title">{file.title}</span>
      {file.tags.length ? <span className="run-desc__tags"><AutoTagChips tags={file.tags} /></span> : null}
      {file.read ? <span className="run-desc__note">{file.read}</span> : null}
      {file.columns?.length ? <span className="run-desc__note">Columns: {file.columns.map((column, i) => <span key={i}>{i ? ", " : ""}<code>{column.name}</code>{column.meaning ? ` (${column.meaning})` : ""}</span>)}{file.more_columns ? ` … and ${file.more_columns} more` : ""}</span> : null}
      {file.first_row?.length ? <span className="run-desc__note">No header row. First row: <code>{file.first_row.join("  ")}</code>{file.more_columns ? ` … and ${file.more_columns} more` : ""}</span> : null}
      <span className="run-desc__path">{file.path}</span>
    </li>;
  })}</ul>;
}

/** What the method's result means, how to read it, what it does not show, and where it can go next. */
function Meaning({ item }: { item: SummaryMeaning }) {
  return <section className="run-desc__meaning" aria-label={`About ${item.workflow}`}>
    <h3>{item.role === "considered" ? `About ${item.workflow} (considered)` : `About ${item.workflow}`}</h3>
    <p>{item.about}</p>
    <dl className="run-desc__facts">
      <dt>How to read it</dt><dd>{item.read}</dd>
      <dt>What it does not show</dt><dd>{item.limits}</dd>
      {item.next.length ? <><dt>Next analyses</dt><dd><ul>{item.next.map((next) => <li key={next.workflow}><strong>{next.workflow}</strong> · {next.relation}<span className="run-desc__note">{next.description}</span></li>)}</ul></dd></> : null}
      {item.sources.length ? <><dt>Sources</dt><dd><ul>{item.sources.map((source) => <li key={source.url}><ExternalLink href={source.url}>{source.title}</ExternalLink></li>)}</ul></dd></> : null}
    </dl>
  </section>;
}

function CopyButton({ run }: { run: RunDescription }) {
  const [copied, setCopied] = useState(false);
  return <button className="btn btn--quiet btn--small" type="button" onClick={() => {
    void navigator.clipboard?.writeText(descriptionText(run)).then(() => { setCopied(true); setTimeout(() => setCopied(false), 1500); }).catch(() => undefined);
  }}>{copied ? "Copied" : "Copy as text"}</button>;
}

function Card({ run, total, onOpenOutput }: { run: RunDescription; total: number; onOpenOutput?: (path: string) => void }) {
  const { zone } = useTimeZone();
  const summary = run.summary;
  const failed = summary ? summary.outcome === "failed" : run.status === "Failed";
  const usage = summary?.usage;
  return <article className={`run-result run-desc${failed ? " is-failed" : ""}`} aria-label={`Description of run ${run.index + 1}`}>
    <header className="run-desc__head">
      <h2>Run {run.index + 1}{run.index === total - 1 ? " · latest" : ""} · {run.id.slice(0, 8)}</h2>
      <span className="tl__status">{summary ? outcomeLabel(summary.outcome) : run.status}</span>
      <CopyButton run={run} />
    </header>
    <p className="log__clock">{fullTime(run.startedAt, zone)}{run.endedAt ? ` · elapsed ${durationLabel(run.elapsedMs)}` : ""}</p>
    <p className="run-desc__headline"><strong>Conclusion:</strong> {summary?.headline ?? run.fallback!.headline}</p>
    {summary ? <>
      {summary.caveats.map((caveat) => <p key={caveat} className="run-desc__caveat" role="note">{caveat}</p>)}
      <div className="run-desc__story">{summary.narrative.map((line, i) => <p key={i}>{line}</p>)}</div>
      <dl className="run-desc__facts">
        <dt>How the request was read</dt>
        <dd>{kindLabel(summary.decision.kind)}{summary.decision.partial ? " · part of the request was not done" : ""}
          {summary.decision.reason ? <span className="run-desc__note">Recorded reason: {summary.decision.reason}</span> : null}</dd>
        {summary.method.workflow || summary.decision.workflows.length ? <><dt>{summary.method.workflow ? "Method chosen" : summary.decision.workflows.length > 1 ? "Methods that fit" : "Method"}</dt><dd>{summary.method.workflow ?? summary.decision.workflows.join(", ")}
          {summary.decision.candidates.length > 1 ? <span className="run-desc__note">Candidates considered: {summary.decision.candidates.join(", ")}</span> : null}</dd></> : null}
        {summary.method.steps.length ? <><dt>Planned steps</dt><dd><ol>{summary.method.steps.map((step, i) => <li key={i}>{step.label}{step.purpose ? <span className="run-desc__note">{step.purpose}</span> : null}</li>)}</ol></dd></> : null}
        {summary.inputs.length ? <><dt>Inputs</dt><dd><ul>{summary.inputs.map((item) => <li key={item.field}><code>{item.field}</code>: {item.value ? <code>{item.value}</code> : "none"} <span className="run-desc__note-inline">({item.source})</span></li>)}</ul></dd></> : null}
        {summary.missing_inputs.length ? <><dt>Missing inputs</dt><dd>{summary.missing_inputs.join(", ")}</dd></> : null}
        {summary.tools.length ? <><dt>What ran</dt><dd><ul>{summary.tools.map((tool, i) => <li key={i}>{tool.label} · {tool.status === "dry_run" ? "dry run (not executed)" : tool.status === "success" ? "completed" : tool.status}{tool.superseded ? " · replaced by a later attempt" : ""}{tool.summary ? <span className="run-desc__note">{tool.summary}</span> : null}</li>)}</ul></dd></> : <><dt>What ran</dt><dd>No workflow step ran in this turn.</dd></>}
        {summary.files.length ? <><dt>{summary.files.some((file) => file.written) ? "Output files" : "Planned output files"}</dt><dd><Files files={summary.files} onOpenOutput={onOpenOutput} /></dd></> : summary.outputs.length ? <><dt>Outputs</dt><dd><Outputs paths={summary.outputs} onOpenOutput={onOpenOutput} /></dd></> : summary.planned_outputs.length ? <><dt>Planned outputs (not written yet)</dt><dd><ul>{summary.planned_outputs.map((path) => <li key={path}><code>{path}</code></li>)}</ul></dd></> : null}
        {summary.warnings.length ? <><dt>Warnings</dt><dd><ul>{summary.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul></dd></> : null}
        {summary.errors.length ? <><dt>Errors</dt><dd><ul className="run-desc__errors">{summary.errors.map((error) => <li key={error}>{error}</li>)}</ul></dd></> : null}
        {summary.errors.length ? <><dt>Suggested repair</dt><dd><ol>{repairSteps(summary.errors).map((step) => <li key={step}>{step}</li>)}</ol></dd></> : null}
        {summary.evaluation ? <><dt>Result check</dt><dd>{summary.evaluation}</dd></> : null}
        {summary.questions.length ? <><dt>{summary.questions.length === 1 ? "Question asked" : "Questions asked"}</dt><dd><ul>{summary.questions.map((question) => <li key={question} className="run-desc__question">{question}</li>)}</ul></dd></> : null}
        {summary.next_step ? <><dt>Next step</dt><dd>{summary.next_step}</dd></> : null}
        {usage && usage.llm_calls !== undefined ? <><dt>Cost</dt><dd>{usage.llm_calls} model {usage.llm_calls === 1 ? "call" : "calls"} · {(usage.total_tokens ?? 0).toLocaleString()} tokens{typeof usage.cost_usd === "number" ? ` · US$${usage.cost_usd.toFixed(4)}${usage.cost_complete === false ? " (some calls unpriced)" : ""}` : ""}{usage.models?.length ? <span className="run-desc__note">{usage.models.join(", ")}</span> : null}</dd></> : null}
      </dl>
      {summary.meaning.length ? <div className="run-desc__meanings">
        <h3 className="run-desc__section-title">{summary.meaning.every((item) => item.role === "considered") ? "About the methods considered" : summary.meaning.every((item) => item.role === "selected") ? "About the selected method" : "What this result means"}</h3>
        {summary.meaning.map((item) => <Meaning key={item.workflow} item={item} />)}
      </div> : null}
      {summary.reply_excerpt ? <details className="run-desc__reply"><summary>The agent's reply</summary><p>{summary.reply_excerpt}</p></details> : null}
    </> : <>
      {run.fallback!.request ? <p>You asked: “{run.fallback!.request}”</p> : null}
      <div className="run-desc__story">{run.fallback!.narrative.map((line, i) => <p key={i}>{line}</p>)}</div>
      {run.fallback!.outputs.length ? <Outputs paths={run.fallback!.outputs} onOpenOutput={onOpenOutput} /> : null}
      {run.fallback!.errors.length ? <ul className="run-desc__errors">{run.fallback!.errors.map((error) => <li key={error}>{error}</li>)}</ul> : null}
    </>}
  </article>;
}

export function RunDescriptionView({ trace, entries = [], onOpenOutput }: { trace: TraceEvent[]; entries?: Entry[]; onOpenOutput?: (path: string) => void }) {
  const runs = useMemo(() => buildDescriptions(trace, entries), [trace, entries]);
  return <div className="pane__scroll run-results run-descs">
    {!runs.length ? <p className="pane__empty">A written description of each run appears here once the agent starts working.</p> : null}
    {[...runs].reverse().map((run) => <Card key={run.id} run={run} total={runs.length} onOpenOutput={onOpenOutput} />)}
  </div>;
}
