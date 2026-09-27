import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { TimeZoneSettings } from "./TimeZoneSettings";
import { setTimeZone, useTimeZone } from "../timeline/timeZone";
import { RunLog } from "../timeline/RunLog";
import { exportLog } from "../../transport/export";

vi.mock("../../transport/export", () => ({ exportLog: vi.fn().mockResolvedValue("Saved.") }));
afterEach(() => { cleanup(); setTimeZone("system"); vi.clearAllMocks(); });
function Reader() { const { zone } = useTimeZone(); return <p data-testid="zone">{zone}</p>; }

it("changes every mounted view, persists the preference and resets to the system", () => {
  render(<><TimeZoneSettings /><Reader /><RunLog sessionId="s" incomplete={false} rows={[{ id: "1", at: "2026-09-26T16:10:00Z", source: "tool", level: "info", label: "Run", summary: "Done" }]} /></>);
  fireEvent.change(screen.getByLabelText("Time zone · country / city"), { target: { value: "Asia/Taipei" } });
  expect(screen.getByTestId("zone").textContent).toBe("Asia/Taipei");
  expect(screen.getByText("00:10:00.000")).toBeTruthy();
  expect(localStorage.getItem("netzoo.display.time-zone")).toBe("Asia/Taipei");
  cleanup(); render(<TimeZoneSettings />);
  expect((screen.getByLabelText("Time zone · country / city") as HTMLSelectElement).value).toBe("Asia/Taipei");
  fireEvent.change(screen.getByLabelText("Time zone · country / city"), { target: { value: "system" } });
  expect((screen.getByLabelText("Time zone · country / city") as HTMLSelectElement).value).toBe("system");
  expect(setTimeZone("made-up-zone")).toBe(false);
});

it("exports the selected zone while keeping original UTC evidence", async () => {
  setTimeZone("America/New_York");
  render(<RunLog sessionId="s" incomplete={false} rows={[{ id: "1", at: "2026-09-26T16:10:00Z", source: "tool", level: "info", label: "Run", summary: "Done" }]} />);
  expect(screen.getByText("12:10:00.000")).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Export JSON" }));
  await screen.findByText("Saved.");
  const json = JSON.parse(vi.mocked(exportLog).mock.calls[0][0]);
  expect(json.time_zone).toBe("America/New_York");
  expect(json.records[0].at).toBe("2026-09-26T16:10:00Z");
});
