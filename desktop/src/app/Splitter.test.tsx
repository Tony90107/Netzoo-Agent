/**
 * A remembered pane size, and the limits that keep a pane from vanishing.
 *
 * Dragging a divider off the edge of the window must leave something behind;
 * a pane dragged to zero cannot be dragged back, because its handle goes with
 * it.
 */
import { act, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { Splitter, usePaneSize } from "./Splitter";

function Harness({ initial = 240 }: { initial?: number }) {
  const [size, setSize] = usePaneSize("probe", initial, 170, 520);
  return (
    <div>
      <output data-testid="size">{size}</output>
      <Splitter
        orientation="vertical"
        label="probe"
        onDelta={(delta) => setSize(size + delta)}
      />
    </div>
  );
}

const size = () => Number(screen.getByTestId("size").textContent);

function press(key: string) {
  act(() => {
    screen.getByRole("separator").dispatchEvent(
      Object.assign(new KeyboardEvent("keydown", { bubbles: true, key }), {}),
    );
  });
}

afterEach(() => {
  window.localStorage.clear();
  document.body.innerHTML = "";
});

describe("a remembered pane size", () => {
  it("starts at its default", () => {
    render(<Harness />);
    expect(size()).toBe(240);
  });

  it("cannot be driven below its minimum", () => {
    render(<Harness initial={180} />);
    for (let i = 0; i < 20; i += 1) press("ArrowLeft");
    expect(size()).toBe(170);
  });

  it("cannot be driven above its maximum", () => {
    render(<Harness initial={500} />);
    for (let i = 0; i < 20; i += 1) press("ArrowRight");
    expect(size()).toBe(520);
  });

  it("is remembered, and clamped again on the way back in", () => {
    render(<Harness />);
    press("ArrowRight");
    expect(window.localStorage.getItem("netzoo.layout.probe")).toBe("256");

    document.body.innerHTML = "";
    window.localStorage.setItem("netzoo.layout.probe", "99999");
    render(<Harness />);
    expect(size()).toBe(520);
  });

  it("falls back to the default when what was stored is not a size", () => {
    window.localStorage.setItem("netzoo.layout.probe", "not-a-number");
    render(<Harness />);
    expect(size()).toBe(240);
  });
});

describe("the divider itself", () => {
  it("is a separator a keyboard can reach", () => {
    render(<Harness />);
    const handle = screen.getByRole("separator");
    expect(handle.getAttribute("aria-orientation")).toBe("vertical");
    expect(handle.getAttribute("tabindex")).toBe("0");
  });
});
