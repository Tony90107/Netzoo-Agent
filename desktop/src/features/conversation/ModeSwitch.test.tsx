/**
 * Mode is a control, not a typed command. These pin the two things that make
 * that safe: the engine still receives the slash command (the window never
 * sets EXECUTE_TOOLS or TEST_DATA_MODE itself), and the switch is inert while
 * a turn is running, when the agent cannot accept an answer.
 */
import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ModeSwitch } from "./ModeSwitch";

afterEach(() => {
  document.body.innerHTML = "";
});

describe("the mode switch", () => {
  it("sends the slash command the agent's state machine owns", () => {
    const onSelect = vi.fn();
    render(<ModeSwitch mode="Planning" disabled={false} onSelect={onSelect} />);

    fireEvent.click(screen.getByText("Synthetic test"));

    expect(onSelect).toHaveBeenCalledWith("/test");
  });

  it("switches back the same way", () => {
    const onSelect = vi.fn();
    render(<ModeSwitch mode="Test" disabled={false} onSelect={onSelect} />);

    fireEvent.click(screen.getByText("Planning"));

    expect(onSelect).toHaveBeenCalledWith("/planning");
  });

  it("marks the current mode and does not re-send it", () => {
    const onSelect = vi.fn();
    render(<ModeSwitch mode="Test" disabled={false} onSelect={onSelect} />);

    const current = screen.getByText("Synthetic test");
    expect(current.getAttribute("aria-pressed")).toBe("true");
    fireEvent.click(current);

    expect(onSelect).not.toHaveBeenCalled();
  });

  it("is inert while a turn is running", () => {
    const onSelect = vi.fn();
    render(<ModeSwitch mode="Planning" disabled onSelect={onSelect} />);

    fireEvent.click(screen.getByText("Synthetic test"));

    expect(onSelect).not.toHaveBeenCalled();
  });
});
