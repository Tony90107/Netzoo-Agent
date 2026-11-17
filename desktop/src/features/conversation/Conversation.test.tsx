import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeAll, expect, it, vi } from "vitest";

import { makeCard, makeOption, makeView } from "../../test-support/fixtures";
import { emptySession, type SessionState } from "../../transport/session";
import type { TraceEvent } from "../../transport/protocol";
import { Conversation } from "./Conversation";

const baseTime = Date.parse("2026-10-14T10:00:00.000Z");

function event(sequence: number, node: string, eventType: string, payload: Record<string, unknown> = {}): TraceEvent {
  const at = new Date(baseTime + sequence * 1000).toISOString();
  return {
    schema_version: 1,
    event_id: `event-${sequence}`,
    run_id: "run-1",
    sequence,
    event_type: eventType,
    occurred_at: at,
    recorded_at: at,
    node,
    parent_event_id: null,
    visibility: "shareable",
    payload,
    previous_hash: "",
    event_hash: "",
  };
}

function session(overrides: Partial<SessionState> = {}): SessionState {
  return {
    ...emptySession("session-1"),
    entries: [{ kind: "user", id: 1, text: "Analyze my expression data", at: new Date(baseTime).toISOString() }],
    ...overrides,
  };
}

const callbacks = {
  onAnswer: vi.fn(),
  onSlash: vi.fn(),
  onApprove: vi.fn(),
  onDecline: vi.fn(),
  onCancel: vi.fn(),
};

beforeAll(() => {
  Element.prototype.scrollIntoView = vi.fn();
});
afterEach(() => { cleanup(); window.localStorage.clear(); });

it("shows live source, decision, and tool steps before the answer, then keeps them for review", () => {
  const initial = session({
    busy: true,
    progress: "Checking inputs",
    trace: [
      event(1, "cli", "run.started"),
      event(2, "apply_project_policy", "node.started"),
      event(3, "apply_project_policy", "policy.loaded", { agents_path: "/work/AGENTS.md" }),
      event(4, "classify", "node.started"),
    ],
  });
  const view = render(<Conversation session={initial} {...callbacks} />);
  // Open while working, headed by the step in progress; bookkeeping steps stay out of the way.
  expect(screen.getByText("Reading your request…")).toBeTruthy();
  expect(screen.getByText("Reading your request")).toBeTruthy();
  expect(screen.queryByText("Used project policy: /work/AGENTS.md")).toBeNull();
  expect((view.container.querySelector("details.turn-activity") as HTMLDetailsElement).open).toBe(true);
  // The step box says what is happening; the row under it keeps only Interrupt.
  expect(screen.queryByText("Checking inputs")).toBeNull();
  expect(screen.getByText("Interrupt")).toBeTruthy();

  const completed = session({
    busy: false,
    view: makeView(),
    entries: [
      initial.entries[0],
      { kind: "agent", id: 2, text: "Analysis is ready.", at: new Date(baseTime + 13_000).toISOString() },
    ],
    trace: [
      ...initial.trace,
      event(5, "classify", "decision.recorded", { action: "run_panda", reason: "Network inference matches the requested output." }),
      event(6, "plan", "plan.created", { workflow: "PANDA", status: "ready", evidence: [{ field: "expression_file", status: "provided", value: "data/expression.tsv" }] }),
      event(7, "execute_tool", "tool.started", { action: "web_search", purpose: "Retrieve method references", lookup: { query: "PANDA network method" } }),
      event(8, "execute_tool", "tool.completed", { action: "web_search", status: "success", summary: "Sources retrieved", source_refs: [{ title: "Method paper", url: "https://example.org/paper" }] }),
      event(9, "execute_tool", "tool.started", { action: "run_panda", purpose: "Infer a gene network" }),
      event(10, "execute_tool", "tool.completed", { action: "run_panda", status: "success", summary: "Network file created" }),
      event(11, "evaluate", "evaluation.recorded", { status: "completed", reason: "Output validated" }),
      event(12, "cli", "run.finished", { status: "completed" }),
    ],
  });
  view.rerender(<Conversation session={completed} {...callbacks} />);

  // The recorded choice is shown; the model's prose reason is not.
  expect(screen.getByText("Selected Run PANDA")).toBeTruthy();
  expect(screen.queryByText(/Network inference matches/)).toBeNull();
  expect(screen.getByText("Ran web search and PANDA")).toBeTruthy();
  expect(screen.getByText("Input · expression_file: data/expression.tsv (provided)")).toBeTruthy();
  expect(screen.getByText("web search started: Retrieve method references")).toBeTruthy();
  expect(screen.getByText("Run PANDA started: Infer a gene network")).toBeTruthy();
  expect(screen.getByText("Tool success: Sources retrieved")).toBeTruthy();
  expect(screen.getByText("Search: PANDA network method")).toBeTruthy();
  expect(screen.getByText("Tool success: Network file created")).toBeTruthy();
  expect(screen.getByRole("link", { name: "Method paper" }).getAttribute("href")).toBe("https://example.org/paper");
  expect(screen.getByText("Result completed: Output validated")).toBeTruthy();
  const threadText = view.container.querySelector(".thread")?.textContent ?? "";
  expect(threadText.indexOf("Worked")).toBeLessThan(threadText.indexOf("Analysis is ready."));
  // Folded into one line once the turn is done; opening it is the person's choice and sticks.
  const card = view.container.querySelector("details.turn-activity") as HTMLDetailsElement;
  expect(card.open).toBe(false);
  expect(card.querySelector("summary")?.textContent).toMatch(/^Worked .*steps/);
  card.open = true;
  fireEvent(card, new Event("toggle"));
  view.rerender(<Conversation session={{ ...completed, entries: [...completed.entries, { kind: "notice", id: 3, text: "Saved", at: new Date(baseTime + 14_000).toISOString() }] }} {...callbacks} />);
  expect(card.open).toBe(true);
});

it("does not turn arbitrary trace payloads into visible model reasoning", () => {
  render(<Conversation session={session({ busy: true, trace: [
    event(1, "cli", "run.started"),
    event(2, "classify", "node.started"),
    event(3, "classify", "routing.internal_detail", { private_reasoning: "hidden analysis text" }),
  ] })} {...callbacks} />);

  expect(screen.getByText("Reading your request")).toBeTruthy();
  expect(screen.queryByText("hidden analysis text")).toBeNull();
});

it("explains a method-only run from its recorded routing decisions", () => {
  render(<Conversation session={session({ busy: false, view: makeView(), trace: [
    event(1, "cli", "run.started"),
    event(2, "classify", "node.started"),
    event(3, "classify", "routing.registry_match_completed", {
      status: "ambiguous",
      hypothesis_actions: ["run_panda", "run_lioness_panda", "run_otter", "run_giraffe"],
      matched_actions: [],
    }),
    event(4, "classify", "routing.selection_conditions_unresolved", {
      candidate_actions: ["run_panda", "run_lioness_panda", "run_otter", "run_giraffe"],
    }),
    event(5, "classify", "routing.intent_classified", { mode: "answer" }),
    event(6, "classify", "llm.completed", { status: "success" }),
    event(7, "classify", "decision.recorded", {
      action: "no_tool",
      reason: "The user is seeking guidance on methods rather than execution.",
    }),
    event(8, "plan", "plan.created", { workflow: "NO-TOOL", status: "respond_only" }),
    event(9, "cli", "run.finished", { status: "completed" }),
  ] })} {...callbacks} />);

  expect(screen.getByText("Candidate workflows: PANDA, LIONESS-PANDA, OTTER, GIRAFFE")).toBeTruthy();
  expect(screen.getByText("Registry result: ambiguous; no workflow selected")).toBeTruthy();
  expect(screen.getByText("The stated preferences did not resolve the workflow choice")).toBeTruthy();
  expect(screen.getByText("Request type: answer")).toBeTruthy();
  expect(screen.getByText("Model · 1 call")).toBeTruthy();
  expect(screen.getByText("Answer in the conversation, without running a workflow")).toBeTruthy();
  expect(screen.queryByText(/seeking guidance on methods/)).toBeNull();
  expect(screen.getByText("Response path: no workflow execution planned")).toBeTruthy();
});

it("lets the user resize the choice list while preserving room for the conversation", () => {
  const choiceView = makeView({ card: makeCard({ choices: {
    header: "Method",
    question: "Which method fits your study?",
    ordering: "",
    allow_other: true,
    options: [makeOption({ key: "run_panda", label: "PANDA", answer: "Use PANDA" })],
  } }) });
  const current = session({ view: choiceView });
  const view = render(<Conversation session={current} {...callbacks} />);
  const divider = screen.getByRole("separator", { name: /resize choices and conversation/i });
  const slot = view.container.querySelector(".composer-slot") as HTMLDivElement;
  expect(slot.style.height).toBe("320px");
  expect(view.container.querySelector(".thread")).toBeTruthy();

  fireEvent.keyDown(divider, { key: "ArrowUp" });
  expect(slot.style.height).toBe("336px");
  fireEvent(divider, new MouseEvent("pointerdown", { bubbles: true, clientY: 400 }));
  fireEvent(window, new MouseEvent("pointermove", { bubbles: true, clientY: 380 }));
  fireEvent(window, new MouseEvent("pointerup", { bubbles: true }));
  expect(slot.style.height).toBe("356px");
  expect(window.localStorage.getItem("netzoo.layout.choices-height")).toBe("356");

  view.unmount();
  const reopened = render(<Conversation session={current} {...callbacks} />);
  expect((reopened.container.querySelector(".composer-slot") as HTMLDivElement).style.height).toBe("356px");
});

it("names the models a step used, by the part of the request each call read", () => {
  render(<Conversation session={session({ busy: false, view: makeView(), trace: [
    event(1, "cli", "run.started"),
    event(2, "classify", "node.started"),
    event(3, "classify", "llm.completed", { model: "openai/gpt-4o-mini", role: "semantic_interpreter", total_tokens: 1000, status: "failed" }),
    event(4, "classify", "llm.completed", { model: "openai/gpt-4o-mini", role: "semantic_interpreter", total_tokens: 1200 }),
    event(5, "classify", "llm.completed", { model: "openai/gpt-4o-mini", role: "fact_check", total_tokens: 300 }),
    event(6, "classify", "core.decision", { kind: "ASK", workflows: ["PANDA"] }),
    event(7, "classify", "node.finished", { duration_ms: 4200 }),
    event(8, "cli", "run.paused", { status: "pending" }),
  ] })} {...callbacks} />);

  expect(screen.getByText("gpt-4o-mini · 3 calls (read the request ×2, check the stated facts) · 2,500 tokens · 1 retried")).toBeTruthy();
  expect(screen.getByText("Decision: ask you for what is still missing")).toBeTruthy();
  expect(screen.getByText("Waiting for you · 4.2 s · 1 step · 3 model calls")).toBeTruthy();
});

it("shows no step box for a run that recorded no steps, such as a resume", () => {
  const view = render(<Conversation session={session({ busy: false, view: makeView(), trace: [
    event(1, "cli", "run.started"),
    event(2, "cli", "run.resumed", { session_id: "session-1" }),
  ] })} {...callbacks} />);

  expect(view.container.querySelector("details.turn-activity")).toBeNull();
});

it("names an input check in words, not by its action name", () => {
  render(<Conversation session={session({ busy: false, view: makeView(), trace: [
    event(1, "cli", "run.started"),
    event(2, "execute_tool", "node.started"),
    event(3, "execute_tool", "tool.started", { action: "inspect_inputs" }),
    event(4, "execute_tool", "tool.completed", { action: "inspect_inputs", status: "failed" }),
    event(5, "execute_tool", "node.finished", { duration_ms: 900 }),
    event(6, "cli", "run.finished", { status: "failed" }),
  ] })} {...callbacks} />);

  expect(screen.getByText("Checked the input files")).toBeTruthy();
  expect(screen.getByText(/^Failed at "Checked the input files"/)).toBeTruthy();
});

it("says which model call a running step is waiting on, and lists sub-steps as they finish", () => {
  const live = (extra: TraceEvent[]) => session({ busy: true, trace: [
    event(1, "cli", "run.started"),
    event(2, "classify", "node.started"),
    event(3, "llm", "llm.started", { role: "semantic_interpreter", model: "openai/gpt-4o-mini", label: "reading the request" }),
    ...extra,
  ] });
  const view = render(<Conversation session={live([])} {...callbacks} />);
  expect(screen.getByText("Reading your request — reading the request…")).toBeTruthy();
  expect(screen.getByText("Reading the request…")).toBeTruthy();

  view.rerender(<Conversation session={live([
    event(4, "classify", "routing.semantic_interpretation_accepted", {}),
    event(5, "llm", "llm.started", { role: "capability_check", model: "openai/gpt-4o-mini", label: "checking what the methods can do" }),
  ])} {...callbacks} />);
  expect(screen.getByText("Read what you asked for")).toBeTruthy();
  expect(screen.getByText("Reading your request — checking what the methods can do…")).toBeTruthy();
  expect(screen.getByText("Checking what the methods can do…")).toBeTruthy();
  // The call is attributed to the running step, never shown as a step of its own.
  expect(view.container.querySelectorAll(".turn-activity__stage")).toHaveLength(1);
});

it("words a decision by how the methods deliver, calling only a run a run", () => {
  const decided = (payload: Record<string, unknown>) => session({ busy: false, view: makeView(), trace: [
    event(1, "cli", "run.started"),
    event(2, "classify", "node.started"),
    event(3, "classify", "core.decision", payload),
    event(4, "classify", "node.finished", { duration_ms: 10 }),
    event(5, "cli", "run.finished", { status: "completed" }),
  ] });
  const view = render(<Conversation session={decided({ kind: "DO", basis: "results_given", workflows: ["LIONESS-PANDA", "LIONESS-PUMA"] })} {...callbacks} />);
  expect(screen.getByText("Decision: LIONESS-PANDA, LIONESS-PUMA can give what you asked for")).toBeTruthy();
  view.rerender(<Conversation session={decided({ kind: "DO", basis: "run", workflows: ["PANDA"] })} {...callbacks} />);
  expect(screen.getByText("Decision: prepare a run of PANDA")).toBeTruthy();
});
