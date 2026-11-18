/**
 * Recommended models first, then every model the provider serves.
 *
 * The model menus (new session, and the switch under the composer) group the
 * models NetZoo was checked on as "Recommended", the ones the person added as
 * "Your models", and end with "All models…", which opens this browser: the
 * provider's whole list, read by the daemon (the key stays there), searchable,
 * with price and whether the model takes function calls. Every NetZoo role
 * calls its model through a forced function call, so models that do not are
 * hidden by default. Choosing one adds it to the saved provider's list, which
 * is what lets the daemon run a session on it.
 */
import { useEffect, useMemo, useRef, useState } from "react";

import { DaemonConfig } from "../../transport/daemon";
import { CatalogModel, ModelCatalog, changeProviderModel, readCatalog } from "../../transport/files";

/** The menu value that opens the browser instead of choosing a model. */
export const BROWSE_ALL = "__browse_all_models__";

export type ModelGroups = { recommended: string[]; added: string[] };

/** Split the allowed models into recommended and added, keeping their order. */
export function groupModels(choices: string[], recommended: string[] | undefined): ModelGroups {
  // A daemon from before 2026-11-18 does not say which are recommended: all were.
  if (!recommended) return { recommended: choices, added: [] };
  const known = new Set(recommended);
  return {
    recommended: choices.filter((name) => known.has(name)),
    added: choices.filter((name) => !known.has(name)),
  };
}

export function ModelOptions({ groups, label, extra }: {
  groups: ModelGroups;
  label: (name: string) => string;
  /** A model to show although it is in neither group (the session's current one). */
  extra?: string;
}) {
  const listed = new Set([...groups.recommended, ...groups.added]);
  return (
    <>
      {extra && !listed.has(extra) ? <option value={extra}>{label(extra)}</option> : null}
      {groups.recommended.length ? (
        <optgroup label="Recommended">
          {groups.recommended.map((name) => <option key={name} value={name}>{label(name)}</option>)}
        </optgroup>
      ) : null}
      {groups.added.length ? (
        <optgroup label="Your models">
          {groups.added.map((name) => <option key={name} value={name}>{label(name)}</option>)}
        </optgroup>
      ) : null}
      <option value={BROWSE_ALL}>All models…</option>
    </>
  );
}

export function formatPrice(model: CatalogModel): string {
  if (model.free) return "free";
  if (model.prompt_per_million === null || model.completion_per_million === null) return "price not listed";
  const money = (value: number) => `$${value < 1 ? value.toFixed(2) : value.toFixed(value < 10 ? 2 : 0)}`;
  return `${money(model.prompt_per_million)} in · ${money(model.completion_per_million)} out per 1M tokens`;
}

function formatContext(length: number | null): string {
  if (!length) return "";
  return length >= 1_000_000 ? `${(length / 1_000_000).toFixed(length % 1_000_000 ? 1 : 0)}M context`
    : `${Math.round(length / 1000)}k context`;
}

const SHOWN = 150;

/** Search, filter and order the catalog: matching words in id or name. */
export function filterCatalog(models: CatalogModel[], query: string, options: { toolsOnly: boolean; freeOnly: boolean }): CatalogModel[] {
  const words = query.toLowerCase().split(/\s+/).filter(Boolean);
  return models.filter((model) => {
    if (options.toolsOnly && model.tools === false) return false;
    if (options.freeOnly && !model.free) return false;
    const text = `${model.id} ${model.name}`.toLowerCase();
    return words.every((word) => text.includes(word));
  });
}

export function ModelCatalogDialog({ config, current, onPick, onCancel }: {
  config: DaemonConfig;
  current?: string;
  onPick: (model: string) => void;
  onCancel: () => void;
}) {
  const [catalog, setCatalog] = useState<ModelCatalog | null>(null);
  const [problem, setProblem] = useState("");
  const [query, setQuery] = useState("");
  const [toolsOnly, setToolsOnly] = useState(true);
  const [freeOnly, setFreeOnly] = useState(false);
  const [busy, setBusy] = useState("");
  const dialog = useRef<HTMLDialogElement>(null);

  const load = (refresh = false) => {
    setProblem("");
    readCatalog(config, refresh).then(setCatalog).catch((error) => setProblem(error instanceof Error ? error.message : String(error)));
  };
  useEffect(() => load(), [config]);
  useEffect(() => {
    const node = dialog.current;
    if (node && !node.open && typeof node.showModal === "function") node.showModal();
  }, []);

  const matches = useMemo(
    () => (catalog ? filterCatalog(catalog.models, query, { toolsOnly, freeOnly }) : []),
    [catalog, query, toolsOnly, freeOnly],
  );
  const recommended = new Set(catalog?.recommended ?? []);
  const added = new Set(catalog?.added ?? []);

  const choose = async (model: string) => {
    setProblem("");
    if (recommended.has(model) || added.has(model)) { onPick(model); return; }
    setBusy(model);
    try {
      await changeProviderModel(config, model);
      onPick(model);
    } catch (error) {
      setProblem(error instanceof Error ? error.message : String(error));
    } finally {
      setBusy("");
    }
  };

  return (
    <dialog ref={dialog} className="nsd mcat" aria-label="All models"
      onCancel={(event) => { event.preventDefault(); onCancel(); }}>
      <h2 className="nsd__title">All models</h2>
      <p className="nsd__note">
        Every model your provider serves. NetZoo was checked on the recommended ones only; another model may
        follow its function calls less well, and a paid one is billed to the provider account.
        {catalog?.provider === "openrouter" ? " One OpenRouter key reaches OpenAI, Anthropic (Claude), Google and the rest." : null}
      </p>
      <div className="mcat__bar">
        <input autoFocus value={query} onChange={(event) => setQuery(event.target.value)}
          placeholder="Search, e.g. claude, gpt, gemini, qwen" aria-label="Search models" />
        <label className="mcat__toggle"><input type="checkbox" checked={toolsOnly} onChange={(event) => setToolsOnly(event.target.checked)} /> Function calling</label>
        <label className="mcat__toggle"><input type="checkbox" checked={freeOnly} onChange={(event) => setFreeOnly(event.target.checked)} /> Free only</label>
      </div>
      {problem ? <div className="fv__error">{problem}</div> : null}
      {!catalog && !problem ? <div className="pane__empty">Reading the provider's models…</div> : null}
      {catalog ? (
        <>
          <div className="nsd__hint">
            {matches.length > SHOWN ? `Showing ${SHOWN} of ${matches.length} matches; search to narrow.` : `${matches.length} of ${catalog.models.length} models.`}
            {" "}<button className="mcat__link" type="button" onClick={() => load(true)}>Refresh</button>
          </div>
          <ul className="mcat__list">
            {matches.slice(0, SHOWN).map((model) => {
              const tag = recommended.has(model.id) ? "Recommended" : added.has(model.id) ? "Added" : "";
              return (
                <li key={model.id} className={`mcat__row${model.id === current ? " mcat__row--current" : ""}`}>
                  <div className="mcat__info">
                    <div className="mcat__name">{model.name}{tag ? <span className="mcat__tag">{tag}</span> : null}</div>
                    <code className="mcat__id">{model.id}</code>
                    <div className="mcat__meta">
                      {formatPrice(model)}
                      {formatContext(model.context_length) ? ` · ${formatContext(model.context_length)}` : ""}
                      {model.tools === null ? " · function calling not listed" : model.tools === false ? " · no function calling" : ""}
                    </div>
                  </div>
                  <button className="btn" type="button" disabled={!!busy || model.id === current}
                    onClick={() => void choose(model.id)}>
                    {model.id === current ? "In use" : busy === model.id ? "Adding…" : "Use"}
                  </button>
                </li>
              );
            })}
          </ul>
        </>
      ) : null}
      <div className="nsd__actions">
        <button className="btn" type="button" onClick={onCancel}>Close</button>
      </div>
    </dialog>
  );
}
