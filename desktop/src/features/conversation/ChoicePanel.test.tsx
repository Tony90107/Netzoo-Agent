/**
 * The choice panel sends the text the agent's prompt already accepts.
 *
 * Every option carries its own `answer`; the panel's job is to send exactly
 * that, whichever way it is chosen — click, Enter, or its number. What the
 * agent cannot run is listed once, in the card above, not again here. The last
 * row sends the user's own words instead, exactly as typed.
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
  render(<ChoicePanel card={card} onAnswer={onAnswer} onOpenOutputs={onOpenOutputs} />);
  return { onAnswer, onOpenOutputs };
}

const group = () => screen.getByRole("group", { name: "Which method fits your study?" });

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
    fireEvent.keyDown(group(), { key: "2" });
    expect(onAnswer).toHaveBeenLastCalledWith("Use LIONESS-COEXPRESSION");
    fireEvent.keyDown(group(), { key: "ArrowDown" });
    expect(document.activeElement?.textContent).toContain("LIONESS-COEXPRESSION");
  });

  it("ends with a row for an answer in your own words", () => {
    harness();
    const own = screen.getByText("Type your own answer").closest(".cp__option")!;
    expect(own.querySelector(".cp__num")?.textContent).toBe("3");
  });

  it("starts that answer with any other key and sends it as typed", () => {
    const { onAnswer } = harness();
    fireEvent.keyDown(group(), { key: "b" });
    const box = screen.getByLabelText("Type your own answer") as HTMLTextAreaElement;
    expect(document.activeElement).toBe(box);
    expect(box.value).toBe("b");
    fireEvent.change(box, { target: { value: "both, starting with BONOBO" } });
    fireEvent.keyDown(box, { key: "Enter" });
    expect(onAnswer).toHaveBeenCalledTimes(1);
    expect(onAnswer).toHaveBeenCalledWith("both, starting with BONOBO");
  });

  it("opens the answer row by its number, never sending it empty", () => {
    const { onAnswer } = harness();
    fireEvent.keyDown(group(), { key: "3" });
    const box = screen.getByLabelText("Type your own answer") as HTMLTextAreaElement;
    expect(box.value).toBe("");
    fireEvent.keyDown(box, { key: "Enter" });
    fireEvent.click(screen.getByText("Send"));
    expect(onAnswer).not.toHaveBeenCalled();
  });

  it("keeps a draft when Escape returns to the options", () => {
    harness();
    fireEvent.click(screen.getByText("Type your own answer"));
    const box = screen.getByLabelText("Type your own answer");
    fireEvent.change(box, { target: { value: "only 12 samples" } });
    fireEvent.keyDown(box, { key: "Escape" });
    expect(document.activeElement?.textContent).toContain("LIONESS-COEXPRESSION");
    expect(screen.getByText("Draft: only 12 samples")).toBeTruthy();
  });

  it("offers no answer row when the card allows none", () => {
    const { onAnswer } = harness(makeCard({ ...CARD, choices: { ...CARD.choices!, allow_other: false } }));
    expect(screen.queryByText("Type your own answer")).toBeNull();
    fireEvent.keyDown(group(), { key: "h" });
    expect(onAnswer).not.toHaveBeenCalled();
  });

  it("leaves what cannot run here to the card above instead of listing it twice", () => {
    harness();
    expect(screen.queryByText("TIGER")).toBeNull();
    expect(screen.queryByText("Not runnable here (netZooR, R)")).toBeNull();
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
