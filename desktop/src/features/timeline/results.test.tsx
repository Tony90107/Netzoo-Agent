import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { TraceEvent } from "../../transport/protocol";
import { buildResults, outputPath, repairSteps } from "./results";
import { RunResults } from "./RunResults";

afterEach(cleanup);
let count = 0;
function event(event_type: string, payload: Record<string, unknown> = {}, run_id = "r1"): TraceEvent {
  return { schema_version: 1, event_id: `e${++count}`, run_id, sequence: count, event_type, payload,
    node: "execute_tool", occurred_at: "2026-09-26T16:10:00Z", recorded_at: "2026-09-26T16:10:00Z",
    parent_event_id: null, visibility: "shareable", previous_hash: "0".repeat(64), event_hash: "1".repeat(64) };
}

it("distinguishes dry runs from real outputs and conversation-only turns", () => {
  const open = vi.fn();
  const trace = [event("run.started"), event("tool.completed", { action: "run_panda", status: "dry_run", artifacts: ["outputs/planned.tsv"] }), event("run.finished", { status: "completed" }),
    event("run.started", {}, "r2"), event("tool.completed", { action: "run_panda", status: "success", artifacts: ["/work/outputs/real.tsv"], metrics: { validated_artifacts: 1, raw_output_chars: 900 } }, "r2"), event("run.finished", { status: "completed" }, "r2"),
    event("run.started", {}, "r3"), event("run.finished", { status: "completed" }, "r3")];
  render(<RunResults trace={trace} onOpenOutput={open} />);
  expect(screen.getByText("Command preview · analysis was not executed")).toBeTruthy();
  expect(screen.getByText("Conversation completed · no workflow executed")).toBeTruthy();
  expect(screen.getAllByRole("button", { name: "Preview output" })).toHaveLength(1);
  fireEvent.click(screen.getByRole("button", { name: "Preview output" }));
  expect(open).toHaveBeenCalledWith("outputs/real.tsv");
  expect(screen.queryByText(/raw output chars/)).toBeNull();
});

it("uses actual validation errors for organism and synthetic-data repair hints", () => {
  const errors = ["expression genes not recognized by the configured gene authority: GeneA", "motif regulator genes cannot be verified without a species; set taxon"];
  const trace = [event("run.started"), event("tool.completed", { action: "inspect_inputs", status: "failed", summary: "Validation failed", errors }), event("run.finished", { status: "failed" })];
  render(<RunResults trace={trace} />);
  expect(screen.getByText(/Specify the organism/)).toBeTruthy();
  expect(screen.getByText(/keep that mode off for real analysis/)).toBeTruthy();
  expect(screen.getByText(errors[0])).toBeTruthy();
  expect(screen.getByText("Execution failed")).toBeTruthy();
});

it("keeps earlier failed attempts and warnings without calling a completed run failed", () => {
  const trace = [event("run.started"), event("tool.completed", { action: "run_panda", status: "failed", errors: ["no such file"], superseded: true }), event("tool.completed", { action: "run_panda", status: "success", warnings: ["Check the matrix"] }), event("run.finished", { status: "completed", token_usage: { total_tokens: 123 } })];
  const result = buildResults(trace)[0];
  expect(result.outcome).toBe("Workflow completed");
  expect(result.tokens).toBe(123);
  expect(result.tools[0].superseded).toBe(true);
  expect(result.tools[0].repairs[0]).toContain("input path");
  expect(result.tools[1].warnings).toEqual(["Check the matrix"]);
});

it("leaves unknown errors explicit and refuses output path escapes", () => {
  expect(repairSteps(["unclassified failure"])[0]).toContain("Expand the full error");
  expect(repairSteps(["Docker image not found"])[0]).toContain("/doctor");
  expect(outputPath("outputs/../data/input.tsv")).toBeNull();
  expect(outputPath("https://example.com/results")).toBeNull();
  expect(outputPath("/work/outputs/result.tsv")).toBe("outputs/result.tsv");
});
