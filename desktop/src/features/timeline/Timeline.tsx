/**
 * The reasoning timeline.
 *
 * Stages are shown by default and their detail is collapsed, because the
 * `routing.*` events are the bulk of a run and are noise until something has
 * gone wrong — at which point they are the only thing that explains it. A
 * stage that recorded an error opens itself.
 */
import { useState } from "react";

import type { TraceEvent } from "../../transport/protocol";
import { Stage, buildStages } from "./model";

function StageRow({ stage }: { stage: Stage }) {
  const [open, setOpen] = useState(stage.failed);
  const marker = stage.failed ? "✕" : stage.running ? "●" : "✓";

  return (
    <li className={`tl__stage${stage.failed ? " is-failed" : ""}${stage.running ? " is-running" : ""}`}>
      <button
        type="button"
        className="tl__head"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        disabled={stage.rows.length === 0}
      >
        <span className="tl__marker" aria-hidden="true">{marker}</span>
        <span className="tl__label">{stage.label}</span>
        {stage.tokens > 0 ? (
          <span className="tl__tokens">{stage.tokens.toLocaleString()}t</span>
        ) : null}
        {stage.durationMs !== null ? (
          <span className="tl__duration">{(stage.durationMs / 1000).toFixed(2)}s</span>
        ) : null}
        {stage.rows.length > 0 ? (
          <span className="tl__count">{open ? "−" : `+${stage.rows.length}`}</span>
        ) : null}
      </button>
      {open ? (
        <ul className="tl__rows">
          {stage.rows.map((row) => (
            <li key={row.id} className={`tl__row tl__row--${row.kind}`}>
              <code className="tl__event">{row.eventType}</code>
              {row.summary ? <span className="tl__summary">{row.summary}</span> : null}
            </li>
          ))}
        </ul>
      ) : null}
    </li>
  );
}

export function Timeline({ trace }: { trace: TraceEvent[] }) {
  const stages = buildStages(trace);

  return (
    <section className="pane">
      <header className="pane__header">
        Timeline
        {trace.length > 0 ? <span className="pane__count">{trace.length}</span> : null}
      </header>
      {stages.length === 0 ? (
        <div className="pane__empty">
          The agent's steps appear here while it works.
        </div>
      ) : (
        <div className="pane__scroll">
          <ul className="tl">
            {stages.map((stage) => (
              <StageRow key={stage.id} stage={stage} />
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
