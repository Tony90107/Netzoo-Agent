/**
 * Compare lines each field tag up as a row of its own, and shows names and notes.
 */
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";

import { compareSessions, type ComparedSession } from "../../transport/files";
import { CompareView } from "./CompareView";

vi.mock("../../transport/files", () => ({ compareSessions: vi.fn() }));
vi.mock("../timeline/timeZone", () => ({ useTimeZone: () => ({ zone: "UTC" }) }));
afterEach(() => { cleanup(); vi.resetAllMocks(); });
const config = { token: "t", port: 8765, baseUrl: "http://127.0.0.1:8765", socketUrl: "ws://127.0.0.1:8765" };
const row = (id: string, extra: Partial<ComparedSession>): ComparedSession => ({
  session_id: id, title: "We collected another batch", status: "completed", workflow: "PANDA", updated_at: 1,
  total_tokens: 10, tags: [], models: {}, inputs: {}, outputs: [], output_dir: "", ...extra });

it("puts each field on its own row and marks the ones that differ", async () => {
  vi.mocked(compareSessions).mockResolvedValue({ sessions: [
    row("a", { name: "Batch 2: DNA damage", notes: "Mutations first.", tags: ["pilot", "dataset:batch-2", "hypothesis:dna"] }),
    row("b", { tags: ["dataset:batch-2", "hypothesis:rewiring"] }),
  ] });
  render(<CompareView config={config} sessionIds={["a", "b"]} onOpenSession={vi.fn()} onOpenOutput={vi.fn()} onClose={vi.fn()} />);
  await screen.findByText("Batch 2: DNA damage");
  const rowOf = (label: string) => screen.getByRole("rowheader", { name: label }).closest("tr")!;
  expect(rowOf("dataset").className).toBe("");
  expect(rowOf("hypothesis").className).toBe("is-diff");
  expect(rowOf("hypothesis").textContent).toBe("hypothesisdnarewiring");
  expect(rowOf("Notes").textContent).toBe("NotesMutations first.—");
  // Labels stay in Tags; fields are not repeated there.
  expect(rowOf("Tags").textContent).toBe("Tagspilot—");
  // The request stays visible under the name.
  expect(screen.getAllByText("We collected another batch").length).toBe(2);
});
