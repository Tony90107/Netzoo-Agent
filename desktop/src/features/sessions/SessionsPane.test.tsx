import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { SessionsPane } from "./SessionsPane";
import { listSessions, type SessionSummary } from "../../transport/files";

vi.mock("../../transport/files", () => ({ listSessions: vi.fn(), listTags: vi.fn() }));
afterEach(() => { cleanup(); vi.resetAllMocks(); });
const config = { token: "t", port: 8765, baseUrl: "http://127.0.0.1:8765", socketUrl: "ws://127.0.0.1:8765" };
const props = { config, currentId: "live", selectedId: null, onOpen: vi.fn(), onResume: vi.fn(), refreshToken: false };
const row = (id: string): SessionSummary => ({ session_id: id, profile_id: "default", updated_at: 1, auto_generated: false, workflow: "PANDA", status: "completed", resumable: false, title: id, total_tokens: 10 });
const page = (ids: string[], next: number | null = null) => ({ sessions: ids.map(row), offset: 0, has_more: next !== null, next_offset: next });

it("appends older sessions and searches the server from the first page", async () => {
  vi.mocked(listSessions).mockResolvedValueOnce(page(["latest"], 60)).mockResolvedValueOnce(page(["older"])).mockResolvedValueOnce(page(["matched"]));
  render(<SessionsPane {...props} />);
  await screen.findByText("latest");
  fireEvent.click(screen.getByRole("button", { name: "Load older sessions" }));
  await screen.findByText("older");
  expect(screen.getByText("latest")).toBeTruthy();
  expect(vi.mocked(listSessions).mock.calls[1][1]?.offset).toBe(60);
  fireEvent.change(screen.getByLabelText("Search sessions"), { target: { value: "LIONESS" } });
  await screen.findByText("matched");
  expect(screen.queryByText("older")).toBeNull();
  expect(vi.mocked(listSessions).mock.calls[2][1]).toEqual({ query: "LIONESS", status: "all", offset: 0 });
});

it("ignores stale results after a filter change", async () => {
  let resolveOld!: (value: ReturnType<typeof page>) => void;
  vi.mocked(listSessions).mockImplementationOnce(() => new Promise(resolve => { resolveOld = resolve; })).mockResolvedValueOnce(page(["failed run"]));
  render(<SessionsPane {...props} />);
  await waitFor(() => expect(listSessions).toHaveBeenCalledTimes(1));
  fireEvent.change(screen.getByLabelText("Latest saved state"), { target: { value: "failed" } });
  await screen.findByText("failed run");
  resolveOld(page(["stale"]));
  await waitFor(() => expect(screen.queryByText("stale")).toBeNull());
  expect(vi.mocked(listSessions).mock.calls[0][2]?.aborted).toBe(true);
});

it("refreshes the latest page after execution and recovers from a failed history request", async () => {
  vi.mocked(listSessions).mockResolvedValueOnce(page(["latest"], 60)).mockResolvedValueOnce(page(["older"])).mockRejectedValueOnce(new Error("History unavailable")).mockResolvedValue(page(["updated"]));
  const view = render(<SessionsPane {...props} />);
  await screen.findByText("latest");
  fireEvent.click(screen.getByRole("button", { name: "Load older sessions" }));
  await screen.findByText("older");
  view.rerender(<SessionsPane {...props} refreshToken />);
  await screen.findByRole("alert");
  expect(vi.mocked(listSessions).mock.calls[2][1]?.offset).toBe(0);
  fireEvent.click(screen.getByRole("button", { name: "refresh" }));
  await screen.findByText("updated");
  expect(screen.queryByText("older")).toBeNull();
});

it("filters by tag and picks sessions to compare", async () => {
  const { listTags } = await import("../../transport/files");
  vi.mocked(listTags).mockResolvedValue({ tags: [{ tag: "pilot", count: 2 }] });
  vi.mocked(listSessions).mockResolvedValue({ ...page(["a", "b"]), sessions: [
    { ...row("a"), tags: ["pilot"], output_count: 2, models: { response: "openai/gpt-4o-mini" } }, row("b")] });
  const onCompare = vi.fn();
  render(<SessionsPane {...props} onCompare={onCompare} />);
  await screen.findByText("a");
  expect(screen.getByText("pilot")).toBeTruthy();
  expect(screen.getByText("2 out")).toBeTruthy();
  expect(screen.getByText("gpt-4o-mini")).toBeTruthy();
  fireEvent.change(await screen.findByLabelText("Tag"), { target: { value: "pilot" } });
  await waitFor(() => expect(vi.mocked(listSessions).mock.calls.at(-1)?.[1]).toEqual({ query: "", status: "all", offset: 0, tag: "pilot" }));
  fireEvent.click(screen.getByRole("button", { name: "compare" }));
  fireEvent.click(screen.getByLabelText("Compare a"));
  fireEvent.click(screen.getByLabelText("Compare b"));
  fireEvent.click(screen.getByRole("button", { name: "Compare" }));
  expect(onCompare).toHaveBeenCalledWith(["a", "b"]);
});

it("shows a session's name over its request and groups field tags by key", async () => {
  const { listTags } = await import("../../transport/files");
  vi.mocked(listTags).mockResolvedValue({ tags: [
    { tag: "pilot", count: 1 }, { tag: "dataset:batch-2", count: 2 }, { tag: "dataset:batch-1", count: 1 }] });
  vi.mocked(listSessions).mockResolvedValue({ ...page(["n1"]), sessions: [
    { ...row("n1"), title: "We collected another batch of patient data", name: "Batch 2: DNA damage",
      notes_preview: "Mutations first.", tags: ["dataset:batch-2"] }] });
  render(<SessionsPane {...props} />);
  await screen.findByText("Batch 2: DNA damage");
  expect(screen.getByText("We collected another batch of patient data").className).toBe("sl__request");
  expect(screen.getByText("notes").getAttribute("title")).toBe("Mutations first.");
  const filter = await screen.findByLabelText("Tag");
  const groups = Array.from(filter.querySelectorAll("optgroup")).map((group) => group.label);
  expect(groups).toEqual(["Labels", "dataset"]);
  expect(filter.querySelector('option[value="dataset:batch-1"]')?.textContent).toBe("dataset: batch-1 (1)");
});
