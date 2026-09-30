import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";

import { makeCard, makeOption } from "../../test-support/fixtures";
import { ReplyCardView } from "./ReplyCardView";

afterEach(cleanup);

it("shows the brief form first and keeps the full reply, unedited, one click away", () => {
  const card = makeCard({
    headline: "3 registered methods can build a cohort-level TF-gene regulatory network.",
    points: ["Understood goal: a cohort-level TF-gene regulatory network.", "Nothing has run yet."],
    unavailable: [makeOption({ key: "requested", label: "Download a regulatory network", available: false,
      resolution: "none", reason: "Only STRING protein networks can be downloaded.", answer: "" })],
  });
  const full = "**PANDA** — message passing.\n\n**OTTER** — graph matching.";
  render(<ReplyCardView card={card} text={full} />);
  expect(screen.getByText(card.headline)).toBeTruthy();
  expect(screen.getByText("Understood goal: a cohort-level TF-gene regulatory network.")).toBeTruthy();
  expect(screen.getByText("Related, but not available in this agent")).toBeTruthy();
  const details = screen.getByText("Full explanation").closest("details")!;
  expect(details.open).toBe(false);
  fireEvent.click(screen.getByText("Full explanation"));
  expect(details.querySelector("strong")?.textContent).toBe("PANDA");
});

it("renders a reply without a brief form exactly as Markdown", () => {
  render(<ReplyCardView card={makeCard({ headline: "" })} text={"## Result\n\nplain"} />);
  expect(screen.getByRole("heading", { name: "Result" })).toBeTruthy();
  expect(screen.queryByText("Full explanation")).toBeNull();
});
