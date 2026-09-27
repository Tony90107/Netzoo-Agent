import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { RunLog } from "./RunLog";
import { exportLog } from "../../transport/export";
import type { LogRow } from "./log";
import { dateLabel, TIME_ZONE } from "./time";

vi.mock("../../transport/export", () => ({ exportLog: vi.fn().mockResolvedValue("Saved log.") }));
afterEach(() => { cleanup(); vi.clearAllMocks(); });

it("starts with highlights, keeps raw events available, and uses one millisecond clock", () => {
  const rows: LogRow[] = [
    { id: "internal", at: "2026-09-26T16:11:08.599212Z", source: "system", level: "info", eventType: "routing.checked", label: "Interpret the request", summary: "Internal routing detail" },
    { id: "outcome", at: "2026-09-26T16:11:09.612Z", source: "tool", level: "error", eventType: "tool.completed", label: "Workflow failed", summary: "Output missing", runId: "r1", sequence: 4 },
  ];
  render(<RunLog rows={rows} sessionId="s" incomplete={false} />);
  expect(screen.queryByText("Internal routing detail")).toBeNull();
  expect(screen.getByText("Output missing")).toBeTruthy();
  expect(screen.getByText(/internal events hidden/).textContent).toContain("1 internal events hidden");
  expect(screen.getByText(/\.612$/)).toBeTruthy();
  expect((screen.getByLabelText("Follow latest") as HTMLInputElement).checked).toBe(true);
  fireEvent.click(screen.getByRole("button", { name: "All events" }));
  expect(screen.getByText("Internal routing detail")).toBeTruthy();
  expect((screen.getByLabelText("Follow latest") as HTMLInputElement).checked).toBe(false);
});

it("exports every matching event even though rendering is limited to a page", async () => {
  const rows: LogRow[] = Array.from({ length: 250 }, (_, index) => ({
    id: `e${index}`, at: "2026-09-26T10:00:00Z", source: "tool", level: index === 0 ? "error" : "info", label: `run_panda ${index}`, summary: "Result",
  }));
  render(<RunLog rows={rows} sessionId="s1" incomplete />);
  expect(screen.getAllByText("Result")).toHaveLength(200);
  fireEvent.click(screen.getByRole("button", { name: "Export JSON" }));
  await screen.findByText("Saved log.");
  let saved = JSON.parse(vi.mocked(exportLog).mock.calls[0][0]);
  expect(saved.records).toHaveLength(250);
  expect(saved.incomplete).toBe(true);
  fireEvent.change(screen.getByLabelText("Status"), { target: { value: "error" } });
  expect(screen.getAllByText("Result")).toHaveLength(1);
  fireEvent.click(screen.getByRole("button", { name: "Export JSON" }));
  await screen.findByText("Saved log.");
  saved = JSON.parse(vi.mocked(exportLog).mock.calls[1][0]);
  expect(saved.records).toHaveLength(1);
  expect(saved.filters.level).toBe("error");
});

it("keeps the execution sequence readable across dates and runs, with raw details collapsed", () => {
  const rows: LogRow[] = [
    { id: "user", at: "2026-09-25T01:00:00Z", source: "user", level: "info", label: "Your request", summary: "Run PANDA" },
    { id: "start", at: "2026-09-25T01:00:01Z", source: "system", level: "info", eventType: "run.started", runId: "r1", sequence: 1, label: "Started", summary: "Analysis" },
    { id: "error", at: "2026-09-26T01:00:00Z", source: "tool", level: "error", eventType: "tool.completed", runId: "r1", sequence: 2, label: "Failed", summary: "Expression file missing", payload: { path: "data/expression.tsv" } },
  ];
  render(<RunLog rows={rows} sessionId="s" incomplete={false} />);
  const timeline = screen.getByRole("list", { name: "Execution timeline" });
  const items = within(timeline).getAllByRole("listitem");
  expect(items.map(item => item.textContent)).toEqual([
    dateLabel(rows[0].at, TIME_ZONE), expect.stringContaining("Your request"), expect.stringContaining("Started"),
    dateLabel(rows[2].at, TIME_ZONE), expect.stringContaining("Expression file missing"),
  ]);
  expect(within(timeline).getByText("You")).toBeTruthy();
  expect(within(timeline).getByText("error")).toBeTruthy();
  expect(within(timeline).queryByText(/Run 0/)).toBeNull();
  expect(Array.from(timeline.querySelectorAll("details")).every(detail => !detail.open)).toBe(true);
  fireEvent.change(screen.getByLabelText("Run", { exact: true }), { target: { value: "r1" } });
  expect(within(timeline).queryByText("Your request")).toBeNull();
  expect(within(timeline).getByText("Expression file missing")).toBeTruthy();
});
