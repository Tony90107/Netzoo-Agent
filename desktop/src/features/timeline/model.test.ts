/**
 * The timeline must not lose or invent anything. The acceptance condition in
 * the architecture note is that a run's events all reach the view, so these
 * check the fold rather than the pixels.
 */
import { describe, expect, it } from "vitest";

import type { TraceEvent } from "../../transport/protocol";
import { buildStages, buildRuns } from "./model";

let sequence = 0;
function event(
  node: string,
  event_type: string,
  payload: Record<string, unknown> = {},
): TraceEvent {
  sequence += 1;
  return {
    schema_version: 1,
    event_id: `e${sequence}`,
    run_id: "r",
    sequence,
    event_type,
    occurred_at: "2026-09-21T00:00:00Z",
    recorded_at: "2026-09-21T00:00:00Z",
    node,
    parent_event_id: null,
    visibility: "shareable",
    payload,
    previous_hash: "0".repeat(64),
    event_hash: "1".repeat(64),
  };
}

describe("folding a trace into stages", () => {
  it("groups repeated turns into distinct runs with start, end, elapsed time and ordered stages", () => {
    const events = [
      { ...event("cli", "run.started"), occurred_at: "2026-09-26T23:59:59Z" },
      { ...event("plan", "node.started"), occurred_at: "2026-09-27T00:00:00Z" },
      event("plan", "node.finished", { duration_ms: 50 }),
      { ...event("cli", "run.finished", { status: "failed" }), occurred_at: "2026-09-27T00:00:01Z" },
      { ...event("cli", "run.started"), run_id: "r2", occurred_at: "2026-09-27T00:00:02Z" },
    ];
    const runs = buildRuns(events);
    expect(runs).toHaveLength(2);
    expect(runs[0].elapsedMs).toBe(2000);
    expect(runs[0].status).toBe("Failed");
    expect(runs[0].stages.map((stage) => stage.node)).toEqual(["plan"]);
    expect(runs[1].status).toBe("Running");
  });
  it("marks non-throwing tool failures as failed and keeps warnings distinct", () => {
    const stages = buildStages([
      event("execute_tool", "node.started"),
      event("execute_tool", "tool.completed", { action: "run_panda", status: "failed", summary: "Output validation failed." }),
      event("execute_tool", "node.finished", { duration_ms: 2 }),
      event("evaluate", "node.started"),
      event("evaluate", "evaluation.recorded", { status: "replan", reason: "Try recovery." }),
      event("evaluate", "node.finished", { duration_ms: 1 }),
    ]);
    expect(stages[0].failed).toBe(true);
    expect(stages[0].rows[0].kind).toBe("error");
    expect(stages[0].rows[0].summary).toContain("Output validation failed.");
    expect(stages[1].failed).toBe(false);
    expect(stages[1].warning).toBe(true);
  });

  it("closes unfinished stages on interruption and does not mix runs", () => {
    const secondRun = { ...event("classify", "node.started"), run_id: "another-run" };
    const stages = buildStages([
      event("classify", "node.started"), secondRun,
      event("cli", "run.interrupted"),
    ]);
    expect(stages[0].running).toBe(false);
    expect(stages[0].interrupted).toBe(true);
    expect(stages[1].running).toBe(true);
  });

  it("represents a pause as waiting instead of a permanently running Session", () => {
    const stages = buildStages([event("cli", "run.started"), event("cli", "run.paused", { status: "pending" })]);
    expect(stages[0].running).toBe(false);
    expect(stages[0].waiting).toBe(true);
  });
  it("clears waiting when a paused run resumes and finishes", () => {
    const stages = buildStages([event("cli", "run.started"), event("cli", "run.paused"), event("cli", "run.resumed"), event("cli", "run.finished", { status: "completed" })]);
    expect(stages[0].waiting).toBe(false);
    expect(stages[0].running).toBe(false);
  });
  it("groups a node's events under the node that emitted them", () => {
    const stages = buildStages([
      event("classify", "node.started"),
      event("classify", "routing.semantic_interpretation_rejected", { issues: ["a"] }),
      event("classify", "llm.completed", { total_tokens: 1200 }),
      event("classify", "node.finished", { duration_ms: 2710 }),
      event("plan", "node.started"),
      event("plan", "plan.created", { workflow: "PANDA" }),
      event("plan", "node.finished", { duration_ms: 90 }),
    ]);

    expect(stages.map((s) => s.label)).toEqual([
      "Interpret the request",
      "Build the Work Plan",
    ]);
    expect(stages[0].rows.map((r) => r.eventType)).toEqual([
      "routing.semantic_interpretation_rejected",
      "llm.completed",
    ]);
    expect(stages[0].durationMs).toBe(2710);
    expect(stages[0].tokens).toBe(1200);
    expect(stages[1].rows[0].summary).toBe("PANDA");
  });

  it("loses no event: every non-node event reaches a row", () => {
    const events = [
      event("cli", "run.started"),
      event("classify", "node.started"),
      event("classify", "routing.a"),
      event("classify", "routing.b"),
      event("classify", "node.finished", { duration_ms: 1 }),
      event("respond", "node.started"),
      event("respond", "node.finished", { duration_ms: 1 }),
    ];

    const rows = buildStages(events).flatMap((stage) => stage.rows);

    const expected = events.filter(
      (e) => !e.event_type.startsWith("node."),
    ).length;
    expect(rows).toHaveLength(expected);
  });

  it("gives a node that runs twice two stages, not one interleaved", () => {
    const stages = buildStages([
      event("evaluate_plan", "node.started"),
      event("evaluate_plan", "plan.deferred"),
      event("evaluate_plan", "node.finished", { duration_ms: 5 }),
      event("recover", "node.started"),
      event("recover", "node.finished", { duration_ms: 5 }),
      event("evaluate_plan", "node.started"),
      event("evaluate_plan", "plan.approved"),
      event("evaluate_plan", "node.finished", { duration_ms: 7 }),
    ]);

    const evaluations = stages.filter((s) => s.node === "evaluate_plan");
    expect(evaluations).toHaveLength(2);
    expect(evaluations[0].rows[0].eventType).toBe("plan.deferred");
    expect(evaluations[1].rows[0].eventType).toBe("plan.approved");
  });

  it("marks a stage that is still running, and one that failed", () => {
    const stages = buildStages([
      event("execute_tool", "node.started"),
      event("execute_tool", "tool.started", { action: "run_panda" }),
      event("evaluate", "node.started"),
      event("evaluate", "error.recorded", {
        error_type: "ValueError",
        message: "bad",
      }),
      event("evaluate", "node.finished", { duration_ms: 2 }),
    ]);

    expect(stages[0].running).toBe(true);
    expect(stages[0].durationMs).toBeNull();
    expect(stages[1].failed).toBe(true);
    expect(stages[1].rows[0].summary).toBe("ValueError: bad");
    expect(stages[1].rows[0].kind).toBe("error");
  });

  it("shows an event it cannot summarise rather than dropping it", () => {
    const stages = buildStages([
      event("classify", "node.started"),
      event("classify", "something.unrecognised", { nothing: "familiar" }),
      event("classify", "node.finished", { duration_ms: 1 }),
    ]);

    expect(stages[0].rows).toHaveLength(1);
    expect(stages[0].rows[0].eventType).toBe("something.unrecognised");
    expect(stages[0].rows[0].summary).toBe("");
    expect(stages[0].rows[0].payload).toEqual({ nothing: "familiar" });
  });
});
