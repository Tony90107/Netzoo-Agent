import { describe, expect, it } from "vitest";

import { modelLabel, sessionModels } from "./NewSessionDialog";

describe("session models", () => {
  it("offers only models every role of the session may run on", () => {
    const allowlists = {
      response: "openai/gpt-4o-mini, nvidia/nemotron-3-super-120b-a12b:free, openai/gpt-4o",
      router: "openai/gpt-4o-mini,nvidia/nemotron-3-super-120b-a12b:free",
    };
    // gpt-4o may write replies but not route, so a whole session cannot run on it.
    expect(sessionModels(allowlists)).toEqual(["openai/gpt-4o-mini", "nvidia/nemotron-3-super-120b-a12b:free"]);
  });

  it("offers nothing from an unset allowlist", () => {
    expect(sessionModels({ response: "(unset)", router: "openai/gpt-4o-mini" })).toEqual([]);
    expect(sessionModels(undefined)).toEqual([]);
  });

  it("labels OpenRouter's free models", () => {
    expect(modelLabel("qwen/qwen3.8-27b:free")).toBe("qwen/qwen3.8-27b (free)");
    expect(modelLabel("openai/gpt-4o-mini")).toBe("openai/gpt-4o-mini");
  });
});
