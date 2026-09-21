import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { makePlan } from "../../test-support/fixtures";
import { WorkflowPlan } from "../../transport/protocol";
import { PlanPane } from "./PlanPane";

const plan = (workflow: string): WorkflowPlan => makePlan({ workflow, objective: "x" });

afterEach(() => {
  document.body.innerHTML = "";
});

describe("the plan pane", () => {
  it("starts a new plan at the top instead of the previous one's position", () => {
    const { rerender } = render(<PlanPane plan={plan("PANDA")} hash="aaa" />);
    const scroller = screen.getByTestId("plan-scroll");
    scroller.scrollTop = 400;

    rerender(<PlanPane plan={plan("LIONESS-PUMA")} hash="bbb" />);

    expect(scroller.scrollTop).toBe(0);
  });

  it("says so when there is no plan", () => {
    render(<PlanPane plan={null} hash={null} />);
    expect(screen.getByText(/No plan yet/)).toBeTruthy();
  });
});
