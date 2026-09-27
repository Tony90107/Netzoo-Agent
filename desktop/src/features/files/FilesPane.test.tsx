import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { FilesPane } from "./FilesPane";
import { listDirectory, previewFile, type Preview } from "../../transport/files";

vi.mock("../../transport/files", async (original) => ({
  ...(await original<typeof import("../../transport/files")>()),
  listDirectory: vi.fn(), previewFile: vi.fn(),
}));
const config = { token: "t", port: 8765, baseUrl: "http://127.0.0.1:8765", socketUrl: "ws://127.0.0.1:8765" };
const preview = (name: string, overrides: Partial<Preview> = {}): Preview => ({
  path: `outputs/${name}`, host_path: `/project/outputs/${name}`, kind: "table", size_bytes: 100,
  truncated: false, columns: ["gene"], rows: [[name]], text: "", arrays: [], note: "",
  offset: 0, next_offset: null, version: "v1", total_columns: 1, ...overrides,
});
beforeEach(() => {
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
