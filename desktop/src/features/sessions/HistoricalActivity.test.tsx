import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { HistoricalActivity } from "./HistoricalActivity";
import { readEvents, readRuns, type SavedEvents, type SavedRun } from "../../transport/activity";
import type { DaemonConfig } from "../../transport/daemon";
import type { TraceEvent } from "../../transport/protocol";

vi.mock("../../transport/activity", () => ({ readEvents: vi.fn(), readRuns: vi.fn() }));
afterEach(() => { cleanup(); vi.resetAllMocks(); });
const config = { baseUrl: "http://localhost", token: "test" } as DaemonConfig;
const run = (run_id: string): SavedRun => ({ run_id, session_id: "s", created_at: "2026-09-26T16:10:00Z", updated_at: "2026-09-26T16:10:00Z", finished_at: "2026-09-26T16:10:00Z", status: "completed", sealed: true, event_count: 2 });
const event = (run_id: string, sequence: number, payload: Record<string, unknown>): TraceEvent => ({ schema_version: 1, event_id: `${run_id}-${sequence}`, run_id, sequence, event_type: "tool.completed", node: "execute_tool", payload, occurred_at: "2026-09-26T16:10:00Z", recorded_at: "2026-09-26T16:10:00Z", visibility: "shareable", previous_hash: "0".repeat(64), event_hash: "1".repeat(64), parent_event_id: null });
const page = (id: string, events: TraceEvent[], next: number | null = null): SavedEvents => ({ events, run: run(id), version: "snapshot", next_sequence: next, incomplete: false, note: "" });

it("fetches only the selected run and joins paged events before showing outputs", async () => {
  vi.mocked(readRuns).mockResolvedValue({ runs: [run("r1"), run("r2")], total: 2, offset: 0, has_more: false, unavailable_metadata: 0 });
  vi.mocked(readEvents).mockResolvedValueOnce(page("r1", [event("r1", 1, { action: "inspect_inputs", status: "success" })], 1))
    .mockResolvedValueOnce(page("r1", [event("r1", 2, { action: "run_panda", status: "success", artifacts: ["outputs/result.tsv"] })]));
  const open = vi.fn();
  render(<HistoricalActivity config={config} sessionId="s" onOpenOutput={open} />);
  fireEvent.click(await screen.findByRole("button", { name: "Preview output" }));
  expect(open).toHaveBeenCalledWith("outputs/result.tsv");
  expect(vi.mocked(readEvents).mock.calls.map((call) => call.slice(1, 5))).toEqual([["s", "r1", 0, ""], ["s", "r1", 1, "snapshot"]]);
  expect(screen.queryByText(/Reading execution events/)).toBeNull();
});

it("does not replace the newly selected run with a late response", async () => {
  vi.mocked(readRuns).mockResolvedValue({ runs: [run("r1"), run("r2")], total: 2, offset: 0, has_more: false, unavailable_metadata: 0 });
  let late!: (value: SavedEvents) => void;
  vi.mocked(readEvents).mockImplementation((_config, _session, id) => id === "r1" ? new Promise((resolve) => { late = resolve; }) : Promise.resolve(page("r2", [event("r2", 1, { action: "run_puma", status: "success" })])));
  render(<HistoricalActivity config={config} sessionId="s" />);
  await waitFor(() => expect(readEvents).toHaveBeenCalled());
  fireEvent.change(screen.getByLabelText("Saved run"), { target: { value: "r2" } });
  await screen.findByText("Run PUMA");
  late(page("r1", [event("r1", 1, { action: "run_panda", status: "success" })]));
  await waitFor(() => expect(screen.queryByText("Run PANDA")).toBeNull());
});

it("explains legacy sessions without inventing traces", async () => {
  vi.mocked(readRuns).mockResolvedValue({ runs: [], total: 0, offset: 0, has_more: false, unavailable_metadata: 0 });
  render(<HistoricalActivity config={config} sessionId="legacy" />);
  expect(await screen.findByText(/No saved Activity/)).toBeTruthy();
  expect(readEvents).not.toHaveBeenCalled();
});
