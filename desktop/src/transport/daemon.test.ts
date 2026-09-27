import { afterEach, expect, it, vi } from "vitest";
import { startDaemon } from "./daemon";

afterEach(() => { vi.unstubAllGlobals(); window.localStorage.clear(); });
it("shares one pending daemon startup between concurrent callers", async () => {
  window.localStorage.setItem("netzoo.daemon", JSON.stringify({ token: "t", baseUrl: "http://127.0.0.1:8765", port: 8765, socketUrl: "ws://127.0.0.1:8765" }));
  let respond!: (value: unknown) => void;
  const fetch = vi.fn(() => new Promise((resolve) => { respond = resolve; }));
  vi.stubGlobal("fetch", fetch);
  const first = startDaemon(vi.fn());
  const second = startDaemon(vi.fn());
  expect(first).toBe(second);
  expect(fetch).toHaveBeenCalledTimes(1);
  respond({ ok: true, json: async () => ({ status: "ok" }) });
  await Promise.all([first, second]);
});
