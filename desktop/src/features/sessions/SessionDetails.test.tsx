/**
 * Names, notes and field tags are the person's, saved as the daemon keeps them.
 */
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";

import { saveDetails } from "../../transport/files";
import { NotesEditor, SessionName } from "./SessionDetails";
import { TagChips } from "./TagEditor";

vi.mock("../../transport/files", () => ({ saveDetails: vi.fn() }));
afterEach(() => { cleanup(); vi.resetAllMocks(); });
const config = { token: "t", port: 8765, baseUrl: "http://127.0.0.1:8765", socketUrl: "ws://127.0.0.1:8765" };

it("renames in place and shows the name the daemon kept", async () => {
  vi.mocked(saveDetails).mockResolvedValue({ name: "Batch 2: DNA damage", notes: "" });
  const onSaved = vi.fn();
  render(<SessionName config={config} sessionId="s1" name="" onSaved={onSaved} />);
  fireEvent.click(screen.getByText("Name this session"));
  const input = screen.getByLabelText("Session name");
  fireEvent.change(input, { target: { value: "  Batch 2:  DNA damage " } });
  fireEvent.keyDown(input, { key: "Enter" });
  fireEvent.blur(input);
  await screen.findByText("Batch 2: DNA damage");
  expect(saveDetails).toHaveBeenCalledTimes(1);
  expect(saveDetails).toHaveBeenCalledWith(config, "s1", { name: "  Batch 2:  DNA damage " });
  expect(onSaved).toHaveBeenCalledWith("Batch 2: DNA damage");
});

it("cancels a rename with Escape and never saves an unchanged name", async () => {
  render(<SessionName config={config} sessionId="s1" name="Pilot" />);
  fireEvent.click(screen.getByText("Pilot"));
  fireEvent.change(screen.getByLabelText("Session name"), { target: { value: "Something else" } });
  fireEvent.keyDown(screen.getByLabelText("Session name"), { key: "Escape" });
  expect(screen.getByText("Pilot")).toBeTruthy();
  fireEvent.click(screen.getByText("Pilot"));
  fireEvent.keyDown(screen.getByLabelText("Session name"), { key: "Enter" });
  expect(saveDetails).not.toHaveBeenCalled();
});

it("saves notes on request, keeps line breaks, and can revert", async () => {
  vi.mocked(saveDetails).mockResolvedValue({ name: "", notes: "Mutations first.\nThen rewiring." });
  render(<NotesEditor config={config} sessionId="s1" notes="" />);
  const box = screen.getByLabelText("Session notes");
  const save = screen.getByText("Save notes") as HTMLButtonElement;
  expect(save.disabled).toBe(true);
  fireEvent.change(box, { target: { value: "draft" } });
  fireEvent.click(screen.getByText("Revert"));
  expect((box as HTMLTextAreaElement).value).toBe("");
  fireEvent.change(box, { target: { value: "Mutations first.\nThen rewiring.  " } });
  fireEvent.keyDown(box, { key: "Enter", metaKey: true });
  await screen.findByText("Saved");
  expect(saveDetails).toHaveBeenCalledWith(config, "s1", { notes: "Mutations first.\nThen rewiring.  " });
  expect((box as HTMLTextAreaElement).value).toBe("Mutations first.\nThen rewiring.");
});

it("says so when notes could not be saved", async () => {
  vi.mocked(saveDetails).mockRejectedValue(new Error("no such session"));
  render(<NotesEditor config={config} sessionId="gone" notes="" />);
  fireEvent.change(screen.getByLabelText("Session notes"), { target: { value: "x" } });
  fireEvent.click(screen.getByText("Save notes"));
  await waitFor(() => expect(screen.getByRole("alert").textContent).toBe("no such session"));
});

it("sets a field tag's key apart from its value", () => {
  render(<TagChips tags={["pilot", "dataset:batch-2"]} />);
  expect(screen.getByText("dataset:").className).toBe("tag__key");
  expect(screen.getByText("dataset:").parentElement?.textContent).toBe("dataset:batch-2");
  expect(screen.getByText("pilot")).toBeTruthy();
});
