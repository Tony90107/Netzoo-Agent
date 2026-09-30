/**
 * The choice panel sends the text the agent's prompt already accepts.
 *
 * Every option carries its own `answer`; the panel's job is to send exactly
 * that, whichever way it is chosen — click, Enter, or its number — and to keep
 * things the agent cannot run visible but unselectable.
 */
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { makeCard, makeOption } from "../../test-support/fixtures";
import { ChoicePanel } from "./ChoicePanel";

afterEach(cleanup);

const CARD = makeCard({
  choices: {
    header: "Method",
    question: "Which method fits your study?",
    ordering: "Recommended first, from what you said.",
    allow_other: true,
    options: [
      makeOption({ key: "run_bonobo", label: "BONOBO", answer: "Use BONOBO", badge: "Recommended", recommended: true,
        description: "Fits what you said: you have only a handful of samples" }),
      makeOption({ key: "run_lioness_coexpression", label: "LIONESS-COEXPRESSION", answer: "Use LIONESS-COEXPRESSION" }),
    ],
  },
  unavailable: [makeOption({ key: "external-1", label: "TIGER", available: false, resolution: "none",
    reason: "Not runnable here (netZooR, R)", answer: "" })],
  next_steps: [makeOption({ key: "new-task", label: "Start a new task", answer: "new", resolution: "command", action: null })],
});

function harness(card = CARD) {
  const onAnswer = vi.fn();
  const onOpenOutputs = vi.fn();
  const onType = vi.fn();
  render(<ChoicePanel card={card} onAnswer={onAnswer} onOpenOutputs={onOpenOutputs} onType={onType} />);
  return { onAnswer, onOpenOutputs, onType };
}

describe("the choice panel", () => {
  it("shows the question, the ordering and the recommendation badge", () => {
    harness();
    expect(screen.getByText("Which method fits your study?")).toBeTruthy();
    expect(screen.getByText("Recommended first, from what you said.")).toBeTruthy();
    expect(screen.getByText("Recommended")).toBeTruthy();
  });

  it("sends an option's own answer text when clicked", () => {
    const { onAnswer } = harness();
    fireEvent.click(screen.getByText("LIONESS-COEXPRESSION"));
    expect(onAnswer).toHaveBeenCalledWith("Use LIONESS-COEXPRESSION");
  });

  it("picks by number and moves with the arrow keys", () => {
    const { onAnswer } = harness();
    const group = screen.getByRole("group", { name: "Which method fits your study?" });
    fireEvent.keyDown(group, { key: "2" });
    expect(onAnswer).toHaveBeenLastCalledWith("Use LIONESS-COEXPRESSION");
    fireEvent.keyDown(group, { key: "ArrowDown" });
    expect(document.activeElement?.textContent).toContain("LIONESS-COEXPRESSION");
  });

  it("hands any other key to the free-text box", () => {
    const { onType, onAnswer } = harness();
    fireEvent.keyDown(screen.getByRole("group", { name: "Which method fits your study?" }), { key: "h" });
    expect(onType).toHaveBeenCalled();
    expect(onAnswer).not.toHaveBeenCalled();
  });

  it("lists what cannot run here without making it selectable", () => {
    const { onAnswer } = harness();
    const blocked = screen.getByText("TIGER").closest(".cp__option")!;
    expect(blocked.getAttribute("aria-disabled")).toBe("true");
    expect(screen.getByText("Not runnable here (netZooR, R)")).toBeTruthy();
    fireEvent.click(blocked);
    expect(onAnswer).not.toHaveBeenCalled();
  });

  it("opens outputs in the window instead of sending text", () => {
    const { onAnswer, onOpenOutputs } = harness(makeCard({
      next_steps: [makeOption({ key: "outputs", label: "Open the outputs", resolution: "open_outputs", answer: "",
        action: null, paths: ["outputs/sessions/a1b2c3d4/panda.tsv"] })],
    }));
    fireEvent.click(screen.getByText("Open the outputs"));
    expect(onOpenOutputs).toHaveBeenCalledWith(["outputs/sessions/a1b2c3d4/panda.tsv"]);
    expect(onAnswer).not.toHaveBeenCalled();
  });

  it("makes execution the primary next step, still sent as /execute", () => {
    const { onAnswer } = harness(makeCard({
      next_steps: [
        makeOption({ key: "execute", label: "Execute this plan", answer: "/execute", resolution: "command", action: null }),
        makeOption({ key: "new-task", label: "Start a new task", answer: "new", resolution: "command", action: null }),
      ],
    }));
    const execute = screen.getByText("Execute this plan");
    expect(execute.className).toContain("btn--primary");
    fireEvent.click(execute);
    expect(onAnswer).toHaveBeenCalledWith("/execute");
  });
});
