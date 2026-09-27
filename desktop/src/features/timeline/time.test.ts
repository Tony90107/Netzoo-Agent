import { expect, it } from "vitest";
import { clockLabel, dateLabel, durationLabel, timestamp } from "./time";

it("converts UTC across midnight into a local date and a 24-hour millisecond clock", () => {
  const at = "2026-09-26T16:11:08.599212Z";
  expect(clockLabel(at, "Asia/Taipei")).toBe("00:11:08.599");
  expect(dateLabel(at, "Asia/Taipei")).toBe("27 Sept 2026");
  expect(clockLabel(at, "UTC")).toBe("16:11:08.599");
});

it("does not pretend an invalid or timezone-less value is an original event time", () => {
  expect(timestamp("2026-09-26T16:11:08")).toBeNull();
  expect(clockLabel("broken")).toBe("Time unavailable");
  expect(durationLabel(2)).toBe("2 ms");
  expect(durationLabel(null)).toBe("Timing unavailable");
});

it("uses the selected zone's daylight saving rules rather than a fixed offset", () => {
  expect(clockLabel("2026-01-26T16:00:00Z", "America/New_York")).toBe("11:00:00.000");
  expect(clockLabel("2026-07-26T16:00:00Z", "America/New_York")).toBe("12:00:00.000");
});
