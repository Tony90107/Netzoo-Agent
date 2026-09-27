import { describe, expect, it } from "vitest";
import { buildLog, filterLog, logText, isImportant, type LogRow } from "./log";
import type { TraceEvent } from "../../transport/protocol";

const tool: TraceEvent = {
  schema_version: 1, run_id: "r1", sequence: 1, recorded_at: "2026-09-26T10:00:02Z", parent_event_id: null, visibility: "shareable", previous_hash: "0".repeat(64), event_hash: "1".repeat(64),
  event_id: "tool-event", event_type: "tool.completed", occurred_at: "2026-09-26T10:00:02Z",
  node: "execute_tool", payload: { action: "run_panda", status: "failed", summary: "Missing output.", artifacts: ["outputs/net.tsv"] },
};

describe("run log", () => {
  it("keeps workflow outcomes and user actions in highlights, with routing and lifecycle detail available separately", () => {
    const rows = buildLog([
      { ...tool, event_id: "routing", event_type: "routing.semantic_interpretation_rejected", payload: { status: "rejected" } },
      { ...tool, event_id: "node", event_type: "node.started", payload: {} },
      { ...tool, event_id: "llm", event_type: "llm.completed", payload: { total_tokens: 200 } },
      tool,
    ], [{ kind: "user", id: 1, text: "Run PANDA", at: "2026-09-26T10:00:01Z" }]);
    expect(rows.filter(isImportant).map((row) => row.id)).toEqual(["message-1", "tool-event"]);
    expect(rows.find((row) => row.id === "tool-event")?.label).toBe("Run PANDA · Failed");
    expect(rows).toHaveLength(5);
  });
  it("orders messages and trace events and distinguishes confirmations and tool failures", () => {
    const rows = buildLog([tool], [
      { kind: "agent", id: 2, text: "Done", at: "2026-09-26T10:00:03Z" },
      { kind: "user", id: 1, text: "Requested execution.", action: "confirmation", at: "2026-09-26T10:00:01Z" },
    ]);
    expect(rows.map((row) => row.source)).toEqual(["user", "tool", "agent"]);
    expect(rows[0].label).toContain("confirmation");
    expect(rows[1].level).toBe("error");
    expect(filterLog(rows, "OUTPUTS/NET", "tool", "error")).toHaveLength(1);
    expect(filterLog(rows, "", "user", "error")).toHaveLength(0);
  });

  it("exports complete matching details, including the original timestamp and payload", () => {
    const rows: LogRow[] = buildLog([tool], []);
    const text = logText(rows);
    expect(text).toContain("2026-09-26T10:00:02Z");
    expect(text).toContain("[error] [tool]");
    expect(text).toContain("outputs/net.tsv");
  });
});
