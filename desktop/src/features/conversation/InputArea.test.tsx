/**
 * The input area's job is to emit strings the agent's own state machine
 * accepts. These tests pin the mapping, because getting it wrong produces a
 * confusing rejection from the agent rather than a visible UI bug.
 *
 * The accepted forms come from `cli/clarification.py`:
 *  - the per-field wizard takes a 1-based candidate number or a full path,
 *    and explicitly rejects `field=value`
 *  - the bundle chooser takes a 1-based index, a directory, or "custom"
 */
import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { makeNextTurnPrompt, makePlan, makeView } from "../../test-support/fixtures";
import { ViewPayload } from "../../transport/protocol";
import { InputArea } from "./InputArea";

const PLAN = makePlan({
  evidence: [
    {
      field: "expression_file",
      status: "missing",
      value: null,
      reason: "required",
      candidates: ["data/study-a/expression.tsv", "data/study-b/expression.tsv"],
      candidate_bundle_ids: [],
      bundle_id: null,
      derived_from: null,
    },
  ],
  input_bundle_options: [
    {
      bundle_id: "directory:data/study-a",
      directory: "data/study-a",
      inputs: { expression_file: "data/study-a/expression.tsv" },
    },
    {
      bundle_id: "directory:data/study-b",
      directory: "data/study-b",
      inputs: { expression_file: "data/study-b/expression.tsv" },
    },
  ],
  missing_inputs: ["expression_file"],
});

const view = (overrides: Partial<ViewPayload>): ViewPayload => makeView(overrides);

function harness(payload: ViewPayload, busy = false) {
  const onAnswer = vi.fn();
  const onApprove = vi.fn();
  const onDecline = vi.fn();
  render(
    <InputArea
      view={payload}
      busy={busy}
      onAnswer={onAnswer}
      onApprove={onApprove}
      onDecline={onDecline}
    />,
  );
  return { onAnswer, onApprove, onDecline };
}

afterEach(() => {
  document.body.innerHTML = "";
});

describe("the clarification wizard", () => {
  it("sends a 1-based candidate number, not the path and not field=value", () => {
    const { onAnswer } = harness(
      view({
        prompt_kind: "clarification",
        plan: PLAN,
        target_field: "expression_file",
      }),
    );

    fireEvent.click(screen.getByText("data/study-b/expression.tsv"));

    expect(onAnswer).toHaveBeenCalledWith("2");
  });

  it("sends a typed path unchanged", () => {
    const { onAnswer } = harness(
      view({
        prompt_kind: "clarification",
        plan: PLAN,
        target_field: "expression_file",
      }),
    );

    fireEvent.change(screen.getByPlaceholderText("Or type the full path"), {
      target: { value: " /work/data/mine.tsv " },
    });
    fireEvent.click(screen.getByText("Use this path"));

    expect(onAnswer).toHaveBeenCalledWith("/work/data/mine.tsv");
  });

  it("names the field it is asking about", () => {
    harness(
      view({
        prompt_kind: "clarification",
        plan: PLAN,
        target_field: "expression_file",
      }),
    );

    expect(screen.getByText("expression_file")).toBeTruthy();
  });
});

describe("the bundle chooser", () => {
  it("sends a 1-based index", () => {
    const { onAnswer } = harness(
      view({ prompt_kind: "clarification", plan: PLAN, choosing_bundle: true }),
    );

    fireEvent.click(screen.getByText("data/study-b"));

    expect(onAnswer).toHaveBeenCalledWith("2");
  });

  it("offers the custom escape hatch the wizard understands", () => {
    const { onAnswer } = harness(
      view({ prompt_kind: "clarification", plan: PLAN, choosing_bundle: true }),
    );

    fireEvent.click(screen.getByText("Compose inputs myself"));

    expect(onAnswer).toHaveBeenCalledWith("custom");
  });
});

describe("execution", () => {
  it("asks for the preview with /execute rather than approving anything", () => {
    const { onAnswer, onApprove } = harness(
      view({
        prompt_kind: "main",
        next_prompt: makeNextTurnPrompt({ kind: "dry_run", question: "ready" }),
      }),
    );

    fireEvent.click(screen.getByText("Review and execute this plan"));

    expect(onAnswer).toHaveBeenCalledWith("/execute");
    expect(onApprove).not.toHaveBeenCalled();
  });

  it("approves by naming the plan hash", () => {
    const { onApprove } = harness(
      view({ prompt_kind: "execution_confirmation", plan: PLAN, plan_hash: "abc123" }),
    );

    fireEvent.click(screen.getByText("Execute this plan"));

    expect(onApprove).toHaveBeenCalledWith("abc123");
  });

  it("cannot approve when the daemon sent no hash", () => {
    const { onApprove } = harness(
      view({ prompt_kind: "execution_confirmation", plan: PLAN, plan_hash: null }),
    );

    fireEvent.click(screen.getByText("Execute this plan"));

    expect(onApprove).not.toHaveBeenCalled();
  });

  it("declines without sending a free-text answer", () => {
    const { onAnswer, onDecline } = harness(
      view({ prompt_kind: "execution_confirmation", plan: PLAN, plan_hash: "abc123" }),
    );

    fireEvent.click(screen.getByText("Cancel"));

    expect(onDecline).toHaveBeenCalled();
    expect(onAnswer).not.toHaveBeenCalled();
  });
});

describe("while a turn is running", () => {
  it("offers no way to answer", () => {
    harness(view({ prompt_kind: "main" }), true);

    expect(screen.queryByPlaceholderText(/accomplish with NetZoo/)).toBeNull();
    expect(screen.getByText("Working…")).toBeTruthy();
  });
});

describe("confirmation prompts", () => {
  it("sends the y/n the state machine reads", () => {
    const { onAnswer } = harness(
      view({ prompt_kind: "preference_confirmation", plan: PLAN }),
    );

    fireEvent.click(screen.getByText("Save"));
    expect(onAnswer).toHaveBeenCalledWith("y");
  });
});

describe("preflight correction", () => {
  it("is a different form from the per-field wizard, and accepts field=path", () => {
    const { onAnswer } = harness(
      view({
        prompt_kind: "clarification",
        plan: PLAN,
        preflight_correction: true,
        text: "[Planning] Input preflight failed, so the Work Plan is not ready:\n- expression genes are gene symbols",
      }),
    );

    // The per-field wizard's control must not be offered here.
    expect(screen.queryByText("Use this path")).toBeNull();
    // And the agent's own reason has to reach the user.
    expect(screen.getByText(/Input preflight failed/)).toBeTruthy();

    fireEvent.change(screen.getByPlaceholderText("Corrected inputs, as field=path"), {
      target: { value: "expression_file=/work/data/mine.tsv" },
    });
    fireEvent.click(screen.getByText("Use these inputs"));

    expect(onAnswer).toHaveBeenCalledWith("expression_file=/work/data/mine.tsv");
  });

  it("strips the mode prefix from the agent's question", () => {
    harness(
      view({
        prompt_kind: "clarification",
        plan: PLAN,
        target_field: "expression_file",
        text: "[Test] Which expression file should I use?",
      }),
    );

    expect(screen.getByText("Which expression file should I use?")).toBeTruthy();
  });
});

describe("the main prompt with a reply card", () => {
  it("puts the card's question first and still accepts a typed answer", async () => {
    const { makeCard, makeOption } = await import("../../test-support/fixtures");
    const card = makeCard({
      choices: { header: "Method", question: "Which method fits your study?", ordering: "", allow_other: true,
        options: [makeOption({ key: "run_panda", label: "PANDA", answer: "Use PANDA" }),
          makeOption({ key: "run_otter", label: "OTTER", answer: "Use OTTER", action: "run_otter" })] },
      next_steps: [makeOption({ key: "new-task", label: "Start a new task", answer: "new", resolution: "command", action: null })],
    });
    const { onAnswer } = harness(view({
      prompt_kind: "main", card,
      next_prompt: makeNextTurnPrompt({ kind: "clarify_outcome", question: "Which modeling assumption best matches?" }),
    }));
    expect(screen.getByText("Which method fits your study?")).toBeTruthy();
    // The card asks the question; the prompt's own copy of it is not repeated.
    expect(screen.queryByText("Which modeling assumption best matches?")).toBeNull();
    fireEvent.click(screen.getByText("OTTER"));
    expect(onAnswer).toHaveBeenLastCalledWith("Use OTTER");
    fireEvent.change(screen.getByLabelText("Or answer in your own words"), { target: { value: "neither, compare them" } });
    fireEvent.click(screen.getByText("Send"));
    expect(onAnswer).toHaveBeenLastCalledWith("neither, compare them");
  });

  it("offers execution once, from the card, at a ready plan", async () => {
    const { makeCard, makeOption } = await import("../../test-support/fixtures");
    const card = makeCard({ kind: "plan_ready", next_steps: [
      makeOption({ key: "execute", label: "Execute this plan", answer: "/execute", resolution: "command", action: null })] });
    const { onAnswer } = harness(view({ prompt_kind: "main", card, next_prompt: makeNextTurnPrompt({ kind: "dry_run", question: "Ready." }) }));
    expect(screen.queryByText("Review and execute this plan")).toBeNull();
    fireEvent.click(screen.getByText("Execute this plan"));
    expect(onAnswer).toHaveBeenCalledWith("/execute");
  });
});
