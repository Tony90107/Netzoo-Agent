import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { FilesPane } from "./FilesPane";
import { listDirectory, listSessionOutputs, previewFile, type Preview } from "../../transport/files";

vi.mock("../../transport/files", async (original) => ({
  ...(await original<typeof import("../../transport/files")>()),
  listDirectory: vi.fn(), previewFile: vi.fn(), listSessionOutputs: vi.fn(),
}));
const config = { token: "t", port: 8765, baseUrl: "http://127.0.0.1:8765", socketUrl: "ws://127.0.0.1:8765" };
const preview = (name: string, overrides: Partial<Preview> = {}): Preview => ({
  path: `outputs/${name}`, host_path: `/project/outputs/${name}`, kind: "table", size_bytes: 100,
  truncated: false, columns: ["gene"], rows: [[name]], text: "", arrays: [], note: "",
  offset: 0, next_offset: null, version: "v1", total_columns: 1, ...overrides,
});
beforeEach(() => {
  vi.mocked(listSessionOutputs).mockResolvedValue({ sessions: [], other_files: 2 });
  vi.mocked(listDirectory).mockResolvedValue({ path: "outputs", host_path: "/project/outputs", total: 2, offset: 0, limit: 100, has_more: false,
    entries: ["a.tsv", "b.tsv"].map((name) => ({ name, path: `outputs/${name}`, kind: "file", size_bytes: 100, modified_at: 0 })),
  });
});
afterEach(() => { cleanup(); vi.clearAllMocks(); });

describe("buffered output viewer", () => {
  it("ignores an older preview response when the user selects a different file", async () => {
    let first!: (value: Preview) => void;
    let second!: (value: Preview) => void;
    vi.mocked(previewFile).mockImplementation((_config, path) => new Promise((resolve) => {
      if (path.endsWith("a.tsv")) first = resolve; else second = resolve;
    }));
    render(<FilesPane config={config} />);
    fireEvent.click(screen.getByRole("button", { name: "Folders" }));
    fireEvent.click(await screen.findByText("a.tsv"));
    fireEvent.click(screen.getByText("b.tsv"));
    await act(async () => second(preview("b.tsv")));
    await act(async () => first(preview("a.tsv")));
    expect(screen.getByText("/project/outputs/b.tsv")).toBeTruthy();
    expect(screen.queryByText("/project/outputs/a.tsv")).toBeNull();
  });

  it("requests the next cursor with its file version and can return to the first page", async () => {
    vi.mocked(previewFile).mockImplementation(async (_config, _path, offset = 0) => preview("a.tsv", offset === 0 ? {
      rows: [["first"]], next_offset: 50, truncated: true,
    } : { rows: [["second"]], offset: 50 }));
    render(<FilesPane config={config} />);
    fireEvent.click(screen.getByRole("button", { name: "Folders" }));
    fireEvent.click(await screen.findByText("a.tsv"));
    await screen.findByText("first");
    fireEvent.click(screen.getByRole("button", { name: "Next page" }));
    await screen.findByText("second");
    expect(previewFile).toHaveBeenLastCalledWith(config, "outputs/a.tsv", 50, "v1");
    expect((screen.getByRole("button", { name: "Next page" }) as HTMLButtonElement).disabled).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: "Previous page" }));
    await waitFor(() => expect(screen.getByText("first")).toBeTruthy());
    expect(previewFile).toHaveBeenLastCalledWith(config, "outputs/a.tsv", 0, "v1");
  });
});

describe("outputs by session", () => {
  const entry = (id: string, files: string[], results: number, extra = {}) => ({
    session_id: id, name: "", title: `request ${id}`, workflow: "PANDA", status: "completed", saved: true,
    added_at: 100, folder: `outputs/sessions/${id}`,
    files: files.map((name, index) => ({ name, path: `outputs/sessions/${id}/${name}`, size_bytes: 10, modified_at: 100, result: index < results })),
    ...extra,
  });

  it("is the default view: one result is one file, several results are one folder of that session's files", async () => {
    vi.mocked(listSessionOutputs).mockResolvedValue({ other_files: 1, sessions: [
      entry("new", ["lioness.tsv", "puma.tsv", "manifest.json"], 2, { name: "Batch 2: LIONESS-PUMA" }),
      entry("old", ["panda.tsv", "manifest.json", "panda-execution-x_TW.md"], 1),
    ] });
    vi.mocked(previewFile).mockResolvedValue(preview("sessions/old/panda.tsv"));
    render(<FilesPane config={config} />);
    const rows = await screen.findAllByRole("button", { name: /request old|Batch 2: LIONESS-PUMA/ });
    expect(rows).toHaveLength(2);
    expect(rows[0].textContent).toMatch(/^▾Batch 2: LIONESS-PUMA3 files/);
    // A single result is the entry itself; the run's record is one click away.
    expect(rows[1].textContent).toMatch(/^·request oldpanda\.tsv/);
    expect(screen.getByRole("button", { name: "+2 run files" })).toBeTruthy();
    // The newest folder starts open, its results first and marked.
    expect(screen.getAllByText("result").map((badge) => badge.closest("button")?.textContent?.slice(1, 12))).toEqual(["lioness.tsv", "puma.tsvres"]);
    expect(screen.getByText("1 other file was not written by a saved session.", { exact: false })).toBeTruthy();
    expect(listDirectory).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "+2 run files" }));
    expect(screen.getByText(/^Run report · /).closest("button")?.title).toBe("outputs/sessions/old/panda-execution-x_TW.md");
    fireEvent.click(screen.getByText("request old"));
    await screen.findByText("/project/outputs/sessions/old/panda.tsv");
    expect(previewFile).toHaveBeenCalledWith(config, "outputs/sessions/old/panda.tsv", 0, "");
    // Back returns to the session list, and a folder collapses on a click.
    fireEvent.click(screen.getByText("← back"));
    fireEvent.click(await screen.findByText("Batch 2: LIONESS-PUMA"));
    expect(screen.queryByText("lioness.tsv")).toBeNull();
  });

  it("says when nothing has been written and leads to the folders", async () => {
    render(<FilesPane config={config} />);
    await screen.findByText(/No session has written results yet/);
    fireEvent.click(screen.getByRole("button", { name: "Browse folders" }));
    await screen.findByText("a.tsv");
    expect(listDirectory).toHaveBeenCalledWith(config, "", 0, 100);
  });
});

describe("Markdown outputs", () => {
  const report = "# NetZoo execution summary\n\n## Summary\n\n- Workflow: `PANDA`\n- Status: `success`\n\n## Conclusion\n\nDone.\n";

  it("opens a run report readable in a window of its own, its source one click away", async () => {
    vi.mocked(listSessionOutputs).mockResolvedValue({ other_files: 0, sessions: [{
      session_id: "s1", name: "", title: "request s1", workflow: "PANDA", status: "completed", saved: true, added_at: 100,
      folder: "outputs/sessions/s1", files: [
        { name: "panda.tsv", path: "outputs/sessions/s1/panda.tsv", size_bytes: 10, modified_at: 100, result: true, role: "result" },
        { name: "panda-execution-x_TW.md", path: "outputs/sessions/s1/panda-execution-x_TW.md", size_bytes: 10, modified_at: 100, result: false, role: "report" },
      ] }] });
    vi.mocked(previewFile).mockResolvedValue(preview("sessions/s1/panda-execution-x_TW.md", { kind: "text", text: report }));
    render(<FilesPane config={config} />);
    fireEvent.click(await screen.findByRole("button", { name: "Report" }));
    await screen.findByText("PANDA run");
    expect(screen.getAllByText("Done.")[0].closest(".report__glance")).toBeTruthy();
    expect(previewFile).toHaveBeenCalledWith(config, "outputs/sessions/s1/panda-execution-x_TW.md");
    fireEvent.click(screen.getByRole("button", { name: "Markdown source", hidden: true }));
    expect(screen.getByText(/## Conclusion/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Close", hidden: true }));
    expect(screen.queryByText(/## Conclusion/)).toBeNull();
    // Its row among the run files reads as a report too.
    fireEvent.click(screen.getByRole("button", { name: "+1 run file" }));
    expect(screen.getByText(/^Run report · /)).toBeTruthy();
  });

  it("opens any .md under Folders the same way", async () => {
    vi.mocked(listDirectory).mockResolvedValue({ path: "outputs", host_path: "/project/outputs", total: 1, offset: 0, limit: 100, has_more: false,
      entries: [{ name: "notes.md", path: "outputs/notes.md", kind: "file", size_bytes: 20, modified_at: 0 }] });
    vi.mocked(previewFile).mockResolvedValue(preview("notes.md", { kind: "text", text: "# Notes\n\n- one" }));
    render(<FilesPane config={config} />);
    fireEvent.click(screen.getByRole("button", { name: "Folders" }));
    fireEvent.click(await screen.findByText("notes.md"));
    expect((await screen.findByText("Notes")).tagName).toBe("H1");
  });
});

