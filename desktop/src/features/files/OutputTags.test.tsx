import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { OutputsBySession } from "./OutputsBySession";
import { OutputTagEditor } from "./OutputTags";
import { listSessionOutputs, readOutputTags, saveOutputTags, type SessionOutputs } from "../../transport/files";

vi.mock("../../transport/files", async (original) => ({
  ...(await original<typeof import("../../transport/files")>()),
  listSessionOutputs: vi.fn(), readOutputTags: vi.fn(), saveOutputTags: vi.fn(),
}));
const config = { token: "t", port: 8765, baseUrl: "http://127.0.0.1:8765", socketUrl: "ws://127.0.0.1:8765" };
afterEach(() => { cleanup(); vi.clearAllMocks(); });

const file = (name: string, auto: string[], user: string[] = []) => ({
  name, path: `outputs/sessions/s1/${name}`, size_bytes: 10, modified_at: 1, result: true, role: "result" as const, tags: { auto, user },
});
const session = (id: string, files: ReturnType<typeof file>[]): SessionOutputs => ({
  session_id: id, name: `Session ${id}`, title: "", workflow: "LIONESS-PANDA", status: "completed", saved: true,
  added_at: 1, folder: `outputs/sessions/${id}`, files,
});

it("filters outputs by an auto tag or a user tag and opens the match", async () => {
  vi.mocked(listSessionOutputs).mockResolvedValue({ other_files: 0, sessions: [
    session("s1", [file("agg.tsv", ["method:LIONESS-PANDA", "scale:cohort"]), file("per.tsv", ["method:LIONESS-PANDA", "scale:per-sample"], ["baseline"])]),
    session("s2", [file("panda.tsv", ["method:PANDA", "scale:cohort"])]),
  ] });
  const open = vi.fn();
  render(<OutputsBySession config={config} onOpenFile={open} onBrowseFolders={vi.fn()} />);
  const filter = await screen.findByRole("combobox", { name: "Filter outputs by tag" });
  expect(screen.getByRole("option", { name: "scale:cohort (2)" })).toBeTruthy();
  expect(screen.getByRole("group", { name: "Your tags" })).toBeTruthy();

  fireEvent.change(filter, { target: { value: "scale:cohort" } });
  const tagged = screen.getByRole("list", { name: "Outputs tagged scale:cohort" });
  expect([...tagged.querySelectorAll(".ob__label")].map((node) => node.textContent)).toEqual(["agg.tsv", "panda.tsv"]);

  fireEvent.change(filter, { target: { value: "baseline" } });
  fireEvent.click(screen.getByRole("button", { name: /per\.tsv/ }));
  expect(open).toHaveBeenCalledWith("outputs/sessions/s1/per.tsv");

  fireEvent.click(screen.getByRole("button", { name: "Clear" }));
  expect(screen.queryByRole("list", { name: /Outputs tagged/ })).toBeNull();
});

it("shows auto tags read-only and saves the user's own, showing a refusal's reason", async () => {
  vi.mocked(readOutputTags).mockResolvedValue({ path: "outputs/a.tsv", auto: ["method:PANDA"], user: [] });
  vi.mocked(saveOutputTags).mockResolvedValueOnce({ path: "outputs/a.tsv", auto: ["method:PANDA"], user: ["baseline"] })
    .mockRejectedValueOnce(new Error("method: is set by NetZoo from the run record and cannot be typed."));
  render(<OutputTagEditor config={config} path="outputs/a.tsv" />);
  const input = await screen.findByRole("textbox", { name: "Add a tag to this output file" });
  expect(screen.getByText("PANDA").closest(".tag--auto")).toBeTruthy();
  expect(screen.queryByRole("button", { name: "Remove tag method:PANDA" })).toBeNull();

  fireEvent.change(input, { target: { value: "baseline" } });
  fireEvent.keyDown(input, { key: "Enter" });
  await waitFor(() => expect(saveOutputTags).toHaveBeenCalledWith(config, "outputs/a.tsv", ["baseline"]));
  expect(await screen.findByRole("button", { name: "Remove tag baseline" })).toBeTruthy();

  fireEvent.change(input, { target: { value: "method:OTTER" } });
  fireEvent.keyDown(input, { key: "Enter" });
  expect(await screen.findByRole("alert")).toHaveProperty("textContent", "method: is set by NetZoo from the run record and cannot be typed.");
});
