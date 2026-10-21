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
  expect(screen.getByText("Used project policy: /work/AGENTS.md")).toBeTruthy();
  expect(screen.getByText("Interpret the request")).toBeTruthy();
  expect(screen.getByText("Checking inputs")).toBeTruthy();

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

  expect(screen.getByText(/Selected run panda: Network inference matches/)).toBeTruthy();
  expect(screen.getByText("Input · expression_file: data/expression.tsv (provided)")).toBeTruthy();
  expect(screen.getByText("web search started: Retrieve method references")).toBeTruthy();
  expect(screen.getByText("Run PANDA started: Infer a gene network")).toBeTruthy();
  expect(screen.getByText("Tool success: Sources retrieved")).toBeTruthy();
  expect(screen.getByText("Search: PANDA network method")).toBeTruthy();
  expect(screen.getByText("Tool success: Network file created")).toBeTruthy();
  expect(screen.getByRole("link", { name: "Method paper" }).getAttribute("href")).toBe("https://example.org/paper");
  expect(screen.getByText("Result completed: Output validated")).toBeTruthy();
  const threadText = view.container.querySelector(".thread")?.textContent ?? "";
  expect(threadText.indexOf("Agent activity")).toBeLessThan(threadText.indexOf("Analysis is ready."));
  const card = view.container.querySelector("details.turn-activity") as HTMLDetailsElement;
  expect(card.open).toBe(true);
  fireEvent.click(card.querySelector("summary")!);
  expect(card.open).toBe(false);
  view.rerender(<Conversation session={{ ...completed, entries: [...completed.entries, { kind: "notice", id: 3, text: "Saved", at: new Date(baseTime + 14_000).toISOString() }] }} {...callbacks} />);
  expect(card.open).toBe(false);
});

it("does not turn arbitrary trace payloads into visible model reasoning", () => {
  render(<Conversation session={session({ busy: true, trace: [
    event(1, "cli", "run.started"),
    event(2, "classify", "node.started"),
    event(3, "classify", "routing.internal_detail", { private_reasoning: "hidden analysis text" }),
  ] })} {...callbacks} />);

  expect(screen.getByText("Interpret the request")).toBeTruthy();
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
  expect(screen.getByText("Model responses recorded: 1")).toBeTruthy();
  expect(screen.getByText("Decided to answer without running a workflow: The user is seeking guidance on methods rather than execution.")).toBeTruthy();
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
