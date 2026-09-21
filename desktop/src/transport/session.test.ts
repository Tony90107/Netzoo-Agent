/**
 * Reconnecting, and being honest when a reconnect could not recover
 * everything. The timeline claims to show the whole run, so a replay that
 * silently skipped events would turn that claim into a lie.
 */
import { describe, expect, it } from "vitest";

import {
  NOT_AUTHORISED,
  SESSION_GONE,
  backoffDelay,
  closeReason,
  emptySession,
  reduce,
  sessionVerdict,
} from "./session";

const config = {
  token: "t",
  port: 8765,
  baseUrl: "http://127.0.0.1:8765",
  socketUrl: "ws://127.0.0.1:8765",
};

function stubFetch(impl: () => Promise<unknown>) {
  (globalThis as { fetch: unknown }).fetch = impl as never;
}

describe("the reconnect policy", () => {
  it("stops when the daemon closed the session cleanly", () => {
    expect(closeReason(1000, false)).toBe("The session ended.");
  });

  it("cannot decide from an abnormal close alone", () => {
    // A rejected handshake and a killed daemon both surface as 1006, so the
    // code is not enough: the verdict has to be asked for over HTTP.
    expect(closeReason(1006, false)).toBeNull();
    expect(closeReason(1011, false)).toBeNull();
  });

  it("never reconnects after the window closed the socket itself", () => {
    expect(closeReason(1006, true)).not.toBeNull();
  });

  it("backs off, then stops growing so a long outage stays cheap", () => {
    const delays = [0, 1, 2, 3, 4, 5, 9].map(backoffDelay);
    expect(delays).toEqual([250, 500, 1000, 2000, 4000, 5000, 5000]);
    expect(Math.max(...delays)).toBe(5000);
  });
});

describe("session state", () => {
  it("starts with nothing missed", () => {
    expect(emptySession("s").missedEvents).toBe(false);
  });

  it("keeps an unknown message from disturbing the state", () => {
    const before = emptySession("s");
    expect(reduce(before, "not_a_type", {} as never)).toBe(before);
  });
});


describe("deciding whether a dropped session can come back", () => {
  it("keeps trying while the daemon is unreachable", async () => {
    stubFetch(() => Promise.reject(new Error("connection refused")));
    expect(await sessionVerdict(config, "s1")).toBeNull();
  });

  it("keeps trying while the daemon is up but unhealthy", async () => {
    stubFetch(() => Promise.resolve({ ok: false, status: 503 }));
    expect(await sessionVerdict(config, "s1")).toBeNull();
  });

  it("keeps trying when the session is still there", async () => {
    stubFetch(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ sessions: [{ session_id: "s1" }] }),
      }),
    );
    expect(await sessionVerdict(config, "s1")).toBeNull();
  });

  it("stops when the daemon is up and has never heard of the session", async () => {
    stubFetch(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ sessions: [{ session_id: "other" }] }),
      }),
    );
    expect(await sessionVerdict(config, "s1")).toBe(SESSION_GONE);
  });

  it("stops when the token is no longer accepted", async () => {
    stubFetch(() => Promise.resolve({ ok: false, status: 401 }));
    expect(await sessionVerdict(config, "s1")).toBe(NOT_AUTHORISED);
  });
});
