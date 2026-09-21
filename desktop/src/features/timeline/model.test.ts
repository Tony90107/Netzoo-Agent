/**
 * The timeline must not lose or invent anything. The acceptance condition in
 * the architecture note is that a run's events all reach the view, so these
 * check the fold rather than the pixels.
 */
import { describe, expect, it } from "vitest";

import type { TraceEvent } from "../../transport/protocol";
import { buildStages } from "./model";

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
