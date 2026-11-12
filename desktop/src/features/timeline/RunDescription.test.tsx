import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { TraceEvent } from "../../transport/protocol";
import type { Entry } from "../../transport/session";
import { buildDescriptions, descriptionText } from "./description";
import { RunDescriptionView } from "./RunDescription";
import { Timeline } from "./Timeline";

afterEach(cleanup);
let count = 0;
function event(event_type: string, payload: Record<string, unknown> = {}, run_id = "r1", occurred_at = "2026-11-11T10:00:00Z"): TraceEvent {
  return { schema_version: 1, event_id: `e${++count}`, run_id, sequence: count, event_type, payload,
    node: "respond", occurred_at, recorded_at: occurred_at,
    parent_event_id: null, visibility: "local_only", previous_hash: "0".repeat(64), event_hash: "1".repeat(64) };
}

const summary = {
  version: 1, outcome: "executed", headline: "PANDA ran and finished; 1 output file recorded.",
  request: "Run PANDA on data/toy", narrative: ["You asked: “Run PANDA on data/toy”", "What ran: Run PANDA completed."],
  decision: { kind: "DO", action: "run_panda", reason: "The request names PANDA.", workflows: ["PANDA"], candidates: ["run_panda", "run_otter"], partial: false, declined: [] },
  method: { workflow: "PANDA", objective: "Build one network", plan_status: "ready", steps: [{ action: "run_panda", label: "Run PANDA", purpose: "Execute the requested NetZoo workflow." }] },
  inputs: [{ field: "expression_file", value: "data/toy/expr.tsv", status: "provided", source: "given in the request" }],
  missing_inputs: [], tools: [{ label: "Run PANDA", status: "success", summary: "Passed checks", superseded: false }],
  outputs: ["/work/outputs/panda.tsv"], planned_outputs: [], warnings: ["Small sample"], errors: [],
  evaluation: "All planned steps completed successfully.", next_step: "Open the recorded outputs.", reply_excerpt: "PANDA finished.",
  usage: { llm_calls: 3, total_tokens: 1234, cost_usd: 0.0012, cost_complete: true, models: ["openai/gpt-4o-mini"] },
};

it("shows the recorded description: conclusion, method, steps, inputs, outputs and next step", () => {
  const open = vi.fn();
  const trace = [event("run.started"), event("tool.completed", { action: "run_panda", status: "success", artifacts: ["/work/outputs/panda.tsv"] }),
    event("operation.summary", summary), event("run.finished", { status: "completed" })];
  render(<RunDescriptionView trace={trace} onOpenOutput={open} />);
  expect(screen.getByText(summary.headline)).toBeTruthy();
  expect(screen.getByText("Can be done with an available workflow")).toBeTruthy();
  expect(screen.getByText(/Candidates considered: run_panda, run_otter/)).toBeTruthy();
  expect(screen.getByText("data/toy/expr.tsv")).toBeTruthy();
  expect(screen.getByText("Open the recorded outputs.")).toBeTruthy();
  expect(screen.getByText(/1,234 tokens · US\$0.0012/)).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Preview output" }));
  expect(open).toHaveBeenCalledWith("outputs/panda.tsv");
});

it("describes a run without a recorded summary from its tool results and the request before it", () => {
  const entries: Entry[] = [{ kind: "user", id: 1, text: "Preview LIONESS", at: "2026-11-11T09:59:59Z" }];
  const trace = [event("run.started", {}, "r2"), event("tool.completed", { action: "run_lioness", status: "dry_run" }, "r2"), event("run.finished", { status: "completed" }, "r2")];
  const [run] = buildDescriptions(trace, entries);
  expect(run.summary).toBeNull();
  expect(run.fallback?.request).toBe("Preview LIONESS");
  expect(run.fallback?.headline).toBe("Command preview · analysis was not executed");
  expect(run.fallback?.narrative.join(" ")).toMatch(/Run LIONESS previewed \(dry run, not executed\)/);
  expect(descriptionText(run)).toMatch(/Request: Preview LIONESS/);
});

it("keeps the latest summary of a paused-then-finished run and lists runs newest first", () => {
  const waiting = { ...summary, outcome: "preview", headline: "PANDA was checked and previewed as a dry run; the analysis has not run yet." };
  const trace = [event("run.started"), event("operation.summary", waiting), event("run.finished", { status: "completed" }),
    event("run.started", {}, "r3", "2026-11-11T10:05:00Z"), event("operation.summary", summary, "r3", "2026-11-11T10:05:30Z"), event("run.finished", { status: "completed" }, "r3", "2026-11-11T10:06:00Z")];
  render(<RunDescriptionView trace={trace} />);
  const cards = screen.getAllByRole("article");
  expect(cards[0].textContent).toMatch(/Run 2 · latest/);
  expect(cards[1].textContent).toMatch(/previewed as a dry run/);
});

it("is reachable from the Activity pane as its own tab", () => {
  const trace = [event("run.started"), event("operation.summary", summary), event("run.finished", { status: "completed" })];
  render(<Timeline trace={trace} entries={[]} sessionId="s1" busy={false} incomplete={false} />);
  fireEvent.click(screen.getByRole("button", { name: "Description" }));
  expect(screen.getByText(summary.headline)).toBeTruthy();
});

it("adds the display-only repair advice when a step failed", () => {
  const failed = { ...summary, outcome: "failed", headline: "PANDA did not finish: a step failed.", outputs: [],
    errors: ["expression genes are gene symbols and cannot be verified without a species; set taxon"] };
  render(<RunDescriptionView trace={[event("run.started", {}, "r9"), event("operation.summary", failed, "r9"), event("run.finished", { status: "failed" }, "r9")]} />);
  expect(screen.getByText(/Specify the organism/)).toBeTruthy();
  expect(screen.getByRole("article").className).toMatch(/is-failed/);
});

const meaning = {
  workflow: "PANDA", role: "ran", about: "PANDA starts from a TF-to-gene motif prior.", read: "Higher means more support.",
  limits: "Not probabilities.", sources: [{ title: "PANDA (netZoo)", url: "https://netzoo.github.io/zooanimals/panda/panda/" }, { title: "bad", url: "javascript:alert(1)" }],
  next: [{ workflow: "CONDOR", relation: "can take this result as input", description: "Detect communities." }],
};

it("names each output file as a link that opens it, with what it is and its columns", () => {
  const open = vi.fn();
  const withFiles = { ...summary, caveats: ["Synthetic Test mode was on."], meaning: [meaning], files: [{
    path: "outputs/s/toy-panda.tsv", title: "Cohort TF-to-gene network", read: "One row per TF-gene edge.", written: true,
    workflow: "PANDA", bytes: 3_145_728, columns: [{ name: "tf", meaning: "transcription factor" }, { name: "force", meaning: "PANDA edge score" }], more_columns: 0 }] };
  render(<RunDescriptionView trace={[event("run.started", {}, "f1"), event("operation.summary", withFiles, "f1"), event("run.finished", { status: "completed" }, "f1")]} onOpenOutput={open} />);
  fireEvent.click(screen.getByRole("button", { name: "toy-panda.tsv" }));
  expect(open).toHaveBeenCalledWith("outputs/s/toy-panda.tsv");
  expect(screen.getByText("Cohort TF-to-gene network")).toBeTruthy();
  expect(screen.getByText(/3\.0 MB/)).toBeTruthy();
  expect(screen.getByText(/\(PANDA edge score\)/)).toBeTruthy();
  expect(screen.getByText("Synthetic Test mode was on.")).toBeTruthy();
  expect(screen.getByText("What this result means")).toBeTruthy();
  expect(screen.getByRole("link", { name: "PANDA (netZoo)" }).getAttribute("href")).toBe("https://netzoo.github.io/zooanimals/panda/panda/");
  expect(screen.queryByRole("link", { name: "bad" })).toBeNull();
  expect(screen.getByText("CONDOR")).toBeTruthy();
});

it("lists planned files as text, never as links, and labels methods that were only considered", () => {
  const planned = { ...summary, outcome: "preview", outputs: [], meaning: [{ ...meaning, role: "considered" }], files: [{
    path: "outputs/s/planned.tsv", title: "Cohort TF-to-gene network", read: "", written: false, workflow: "PANDA" }] };
  render(<RunDescriptionView trace={[event("run.started", {}, "f2"), event("operation.summary", planned, "f2"), event("run.finished", { status: "completed" }, "f2")]} onOpenOutput={vi.fn()} />);
  expect(screen.queryByRole("button", { name: "planned.tsv" })).toBeNull();
  expect(screen.getByText(/not written yet/)).toBeTruthy();
  expect(screen.getByText("Planned output files")).toBeTruthy();
  expect(screen.getByText("About the methods considered")).toBeTruthy();
  const [run] = buildDescriptions([event("run.started", {}, "f3"), event("operation.summary", planned, "f3")]);
  expect(descriptionText(run)).toMatch(/Planned output: outputs\/s\/planned\.tsv — Cohort TF-to-gene network/);
  expect(descriptionText(run)).toMatch(/Source: PANDA \(netZoo\) https:\/\/netzoo/);
});
