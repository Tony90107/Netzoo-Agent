import { StrictMode, useState } from "react";
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { App } from "./App";
import { startDaemon } from "../transport/daemon";
import { createSession } from "../transport/session";

vi.mock("../transport/daemon", () => ({ startDaemon: vi.fn(), stopDaemon: vi.fn() }));
vi.mock("../transport/session", async (original) => ({
  ...(await original<typeof import("../transport/session")>()),
  createSession: vi.fn().mockResolvedValue("current-session"),
  SessionSocket: class { open = vi.fn(); close = vi.fn(); },
}));
vi.mock("../features/conversation/Conversation", () => ({ Conversation: ({ session }: { session: { sessionId: string } }) => <div data-testid="live-conversation">{session.sessionId}</div> }));
vi.mock("../features/sessions/SessionsPane", () => ({ SessionsPane: ({ onOpen }: { onOpen: (id: string) => void }) => <button onClick={() => onOpen("saved-session")}>Read saved session</button> }));
vi.mock("../features/timeline/Timeline", () => ({ Timeline: ({ onOpenOutput }: { onOpenOutput: (path: string) => void }) => {
  const [query, setQuery] = useState("");
  return <div><label>Log query<input value={query} onChange={e => setQuery(e.target.value)} /></label><button onClick={() => onOpenOutput("outputs/live.tsv")}>Read live output</button></div>;
} }));
vi.mock("../features/sessions/TranscriptView", () => ({ TranscriptView: ({ onOpenOutput }: { onOpenOutput: (path: string) => void }) => {
  const [run, setRun] = useState("Run 1");
  return <div><label>Saved run<select value={run} onChange={e => setRun(e.target.value)}><option>Run 1</option><option>Run 2</option></select></label><button onClick={() => onOpenOutput("outputs/saved.tsv")}>Read saved output</button></div>;
} }));
vi.mock("../features/files/FilesPane", () => ({ FilesPane: ({ initialPath }: { initialPath: string }) => <div>Preview: {initialPath}</div> }));
vi.mock("../features/plan/PlanPane", () => ({ PlanPane: () => null }));

afterEach(() => { cleanup(); vi.clearAllMocks(); localStorage.clear(); });
it("ignores a superseded startup under StrictMode instead of connecting two sessions", async () => {
  const pending: ((value: Awaited<ReturnType<typeof startDaemon>>) => void)[] = [];
  vi.mocked(startDaemon).mockImplementation(() => new Promise((resolve) => pending.push(resolve)));
  render(<StrictMode><App /></StrictMode>);
  expect(pending).toHaveLength(2);
  const config = { token: "t", port: 8765, baseUrl: "http://127.0.0.1:8765", socketUrl: "ws://127.0.0.1:8765" };
  await act(async () => pending[1]({ config }));
  await screen.findByTestId("live-conversation");
  await act(async () => pending[0]({ config }));
  expect(createSession).toHaveBeenCalledTimes(1);
  expect(screen.getAllByTestId("live-conversation")).toHaveLength(1);
  expect(screen.getByTestId("live-conversation").textContent).toBe("current-session");
});

const config = { token: "t", port: 8765, baseUrl: "http://127.0.0.1:8765", socketUrl: "ws://127.0.0.1:8765" };
async function ready() {
  vi.mocked(startDaemon).mockResolvedValue({ config });
  render(<App />);
  await screen.findByTestId("live-conversation");
  return within(screen.getByRole("main"));
}

it("returns to the selected historical run without touching the live session", async () => {
  const main = await ready();
  fireEvent.click(screen.getByRole("button", { name: "Read saved session" }));
  fireEvent.change(main.getByLabelText("Saved run"), { target: { value: "Run 2" } });
  expect(main.getByText("Read only")).toBeTruthy();
  expect(screen.queryByRole("complementary", { name: "Current session inspector" })).toBeNull();
  fireEvent.click(main.getByRole("button", { name: "Read saved output" }));
  expect(main.getByText("Preview: outputs/saved.tsv")).toBeTruthy();
  fireEvent.click(main.getByRole("button", { name: /Back to saved Activity/ }));
  expect((main.getByLabelText("Saved run") as HTMLSelectElement).value).toBe("Run 2");
  expect(createSession).toHaveBeenCalledTimes(1);
});

it("preserves the live Log filter through output previews and clears the return action on another view", async () => {
  const main = await ready();
  fireEvent.click(main.getByRole("button", { name: "Activity" }));
  fireEvent.change(main.getByLabelText("Log query"), { target: { value: "failed" } });
  fireEvent.click(main.getByRole("button", { name: "Read live output" }));
  fireEvent.click(main.getByRole("button", { name: /Back to Activity/ }));
  expect((main.getByLabelText("Log query") as HTMLInputElement).value).toBe("failed");
  fireEvent.click(main.getByRole("button", { name: "Read live output" }));
  fireEvent.click(main.getByRole("button", { name: "Conversation" }));
  expect(main.queryByRole("button", { name: /Back to/ })).toBeNull();
});

it("remembers focus view and makes the live inspector an explicit choice", async () => {
  const main = await ready();
  expect(screen.getByRole("complementary", { name: "Current session inspector" })).toBeTruthy();
  fireEvent.change(main.getByLabelText("Workspace layout"), { target: { value: "focus" } });
  expect(screen.queryByRole("complementary", { name: "Current session inspector" })).toBeNull();
  expect(localStorage.getItem("netzoo.layout.view")).toBe("focus");
  cleanup();
  await ready();
  expect((screen.getByLabelText("Workspace layout") as HTMLSelectElement).value).toBe("focus");
  fireEvent.change(screen.getByLabelText("Workspace layout"), { target: { value: "inspector" } });
  expect(screen.getByRole("complementary", { name: "Current session inspector" })).toBeTruthy();
});

it("retires the session it leaves, which stays resumable from its checkpoint", async () => {
  const fetchMock = vi.fn().mockImplementation(() => Promise.resolve(new Response("{}", { status: 200 })));
  vi.stubGlobal("fetch", fetchMock);
  vi.mocked(createSession).mockResolvedValueOnce("current-session").mockResolvedValueOnce("next-session");
  try {
    await ready();
    fireEvent.click(screen.getByRole("button", { name: "New session" }));
    fireEvent.click(await screen.findByRole("button", { name: "Start session", hidden: true }));
    await waitFor(() => expect(screen.getByTestId("live-conversation").textContent).toBe("next-session"));
    const deletes = fetchMock.mock.calls.filter(([, init]) => init?.method === "DELETE").map(([url]) => String(url));
    expect(deletes).toEqual(["http://127.0.0.1:8765/v1/sessions/current-session"]);
  } finally {
    vi.unstubAllGlobals();
  }
});

