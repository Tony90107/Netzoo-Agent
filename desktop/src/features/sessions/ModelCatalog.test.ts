import { describe, expect, it } from "vitest";

import { CatalogModel } from "../../transport/files";
import { filterCatalog, formatPrice, groupModels } from "./ModelCatalog";

const model = (id: string, extra: Partial<CatalogModel> = {}): CatalogModel => ({
  id, name: id, context_length: null, prompt_per_million: null, completion_per_million: null,
  free: false, tools: true, created: null, ...extra,
});

describe("model menu groups", () => {
  it("puts the recommended models first and the added ones apart", () => {
    const choices = ["openai/gpt-4o-mini", "nvidia/x:free", "anthropic/claude-haiku-5.5"];
    expect(groupModels(choices, ["openai/gpt-4o-mini", "nvidia/x:free"])).toEqual({
      recommended: ["openai/gpt-4o-mini", "nvidia/x:free"], added: ["anthropic/claude-haiku-5.5"],
    });
  });

  it("treats every model as recommended when an older daemon does not say", () => {
    expect(groupModels(["a", "b"], undefined)).toEqual({ recommended: ["a", "b"], added: [] });
  });

  it("shows another provider's listed models as the person's own", () => {
    expect(groupModels(["gpt-4o-mini"], [])).toEqual({ recommended: [], added: ["gpt-4o-mini"] });
  });
});

describe("all-models browser", () => {
  const models = [
    model("anthropic/claude-haiku-5.5", { name: "Anthropic: Claude Haiku 5.5" }),
    model("vendor/no-tools", { tools: false }),
    model("vendor/unknown", { tools: null }),
    model("qwen/qwen3:free", { free: true }),
  ];

  it("hides models without function calling but keeps unknown ones", () => {
    expect(filterCatalog(models, "", { toolsOnly: true, freeOnly: false }).map((m) => m.id))
      .toEqual(["anthropic/claude-haiku-5.5", "vendor/unknown", "qwen/qwen3:free"]);
    expect(filterCatalog(models, "", { toolsOnly: false, freeOnly: false })).toHaveLength(4);
  });

  it("matches every search word in the id or the name", () => {
    expect(filterCatalog(models, "claude haiku", { toolsOnly: true, freeOnly: false }).map((m) => m.id))
      .toEqual(["anthropic/claude-haiku-5.5"]);
    expect(filterCatalog(models, "", { toolsOnly: true, freeOnly: true }).map((m) => m.id)).toEqual(["qwen/qwen3:free"]);
  });

  it("shows prices per million tokens", () => {
    expect(formatPrice(model("a", { prompt_per_million: 0.15, completion_per_million: 0.6 })))
      .toBe("$0.15 in · $0.60 out per 1M tokens");
    expect(formatPrice(model("b", { prompt_per_million: 15, completion_per_million: 75 })))
      .toBe("$15 in · $75 out per 1M tokens");
    expect(formatPrice(model("c", { free: true }))).toBe("free");
    expect(formatPrice(model("d"))).toBe("price not listed");
  });
});
