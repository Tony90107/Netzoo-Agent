import { afterEach, expect, it, vi } from "vitest";
import { startDaemon } from "./daemon";

const healthy = { ok: true, json: async () => ({ status: "ok" }) };

afterEach(() => { vi.unstubAllGlobals(); window.localStorage.clear(); window.history.replaceState(null, "", "/"); });
it("shares one pending daemon startup between concurrent callers", async () => {
  window.localStorage.setItem("netzoo.daemon", JSON.stringify({ token: "t", baseUrl: "http://127.0.0.1:8765", port: 8765, socketUrl: "ws://127.0.0.1:8765" }));
  let respond!: (value: unknown) => void;
  const fetch = vi.fn()
    .mockImplementationOnce(() => new Promise((resolve) => { respond = resolve; }))
    .mockResolvedValue(healthy);
  vi.stubGlobal("fetch", fetch);
  const first = startDaemon(vi.fn());
  const second = startDaemon(vi.fn());
  expect(first).toBe(second);
  expect(fetch).toHaveBeenCalledTimes(1);
  respond(healthy);
  await Promise.all([first, second]);
});

it("takes the token from the launcher's link and drops it from the address bar", async () => {
  window.history.replaceState(null, "", "/#token=abc123");
  const fetch = vi.fn().mockResolvedValue(healthy);
  vi.stubGlobal("fetch", fetch);
  const { config } = await startDaemon(vi.fn());
  expect(config.token).toBe("abc123");
  expect(config.baseUrl).toBe(window.location.origin);
  expect(config.socketUrl).toBe(window.location.origin.replace(/^http/, "ws"));
  expect(window.location.hash).toBe("");
  expect(JSON.parse(window.localStorage.getItem("netzoo.daemon") ?? "{}").token).toBe("abc123");
  expect(fetch).toHaveBeenCalledWith(`${window.location.origin}/v1/sessions`, { headers: { Authorization: "Bearer abc123" } });
});

it("forgets a token the running daemon no longer accepts", async () => {
  window.history.replaceState(null, "", "/#token=stale");
  vi.stubGlobal("fetch", vi.fn((url: string) => Promise.resolve(url.endsWith("/health") ? healthy : { ok: false })));
  await expect(startDaemon(vi.fn())).rejects.toMatchObject({ kind: "bad_token" });
  expect(window.localStorage.getItem("netzoo.daemon")).toBeNull();
});
