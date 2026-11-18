/**
 * The LLM provider and API key new sessions (and model switches) use.
 *
 * The one editable part of Settings. The key goes to the local daemon only,
 * which stores it owner-only under .netzoo/ and never sends it back: this form
 * shows whether one is saved and its last four characters. The .env allowlists
 * and token limits stay read-only; another provider's models are the ones
 * listed here, and its calls are billed to that account.
 */
import { FormEvent, useEffect, useState } from "react";

import { DaemonConfig } from "../../transport/daemon";
import { ProviderName, ProviderView, readProvider, saveProvider } from "../../transport/files";
import { modelLabel } from "./NewSessionDialog";

const LABELS: Record<ProviderName, string> = {
  openrouter: "OpenRouter",
  openai: "OpenAI",
  custom: "Other OpenAI-compatible endpoint",
};

export function ProviderSettings({ config, onSaved }: { config: DaemonConfig; onSaved?: () => void }) {
  const [view, setView] = useState<ProviderView | null>(null);
  const [provider, setProvider] = useState<ProviderName>("openrouter");
  const [baseUrl, setBaseUrl] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [models, setModels] = useState("");
  const [status, setStatus] = useState<{ kind: "ok" | "error"; text: string } | null>(null);
  const [saving, setSaving] = useState(false);

  const show = (next: ProviderView) => {
    setView(next);
    setProvider(next.provider);
    setBaseUrl(next.base_url);
    setModels(next.models.join(", "));
    setApiKey("");
  };

  useEffect(() => {
    readProvider(config).then(show).catch((problem) => setStatus({ kind: "error", text: String(problem) }));
  }, [config]);

  const submit = async (event: FormEvent, clearKey = false) => {
    event.preventDefault();
    setSaving(true);
    setStatus(null);
    try {
      const next = await saveProvider(config, {
        provider,
        base_url: baseUrl.trim(),
        api_key: apiKey.trim(),
        clear_key: clearKey,
        models: models.split(",").map((item) => item.trim()).filter(Boolean),
      });
      show(next);
      setStatus({ kind: "ok", text: "Saved. New sessions use it; a running session picks it up at its next model switch." });
      onSaved?.();
    } catch (problem) {
      setStatus({ kind: "error", text: problem instanceof Error ? problem.message : String(problem) });
    } finally {
      setSaving(false);
    }
  };

  if (!view) {
    return status ? <div className="fv__error">{status.text}</div> : <div className="pane__empty">Reading provider…</div>;
  }
  const keyState = view.key_saved
    ? `Saved key ${view.key_hint}`
    : view.key_source === "env" ? "Using OPENROUTER_API_KEY from .env" : "No key";
  return (
    <form className="set__group prov" onSubmit={(event) => void submit(event)}>
      <div className="set__title">Provider</div>
      <p className="set__note">
        Your own key stays on this machine: the daemon stores it owner-only and never shows it again.
      </p>
      <label className="prov__field">Provider
        <select value={provider} onChange={(event) => {
          const next = event.target.value as ProviderName;
          setProvider(next);
          setBaseUrl(view.presets[next] ?? "");
        }}>
          {(Object.keys(LABELS) as ProviderName[]).map((name) => <option key={name} value={name}>{LABELS[name]}</option>)}
        </select>
      </label>
      <label className="prov__field">Base URL
        <input value={baseUrl} onChange={(event) => setBaseUrl(event.target.value)}
          placeholder="https://api.groq.com/openai/v1" disabled={provider !== "custom"} />
        {provider === "custom" ? <span className="nsd__hint">Any OpenAI-compatible /v1 endpoint. A local Ollama is http://host.docker.internal:11434/v1 (no key).</span> : null}
      </label>
      <label className="prov__field">API key
        <input type="password" autoComplete="off" value={apiKey} onChange={(event) => setApiKey(event.target.value)}
          placeholder={view.key_saved && view.provider === provider ? `${view.key_hint} (leave empty to keep)` : "Paste your key"} />
        <span className="nsd__hint">{keyState}</span>
      </label>
      <label className="prov__field">Models
        <input value={models} onChange={(event) => setModels(event.target.value)}
          placeholder={provider === "openrouter" ? "optional, e.g. anthropic/claude-haiku-5.5" : "e.g. gpt-4o-mini, gpt-4.1-mini"} />
        <span className="nsd__hint">
          {provider === "openrouter"
            ? "Models you added (the model menus' \"All models…\" adds them here; remove one by deleting it). The recommended models are always offered: the .env allowlist plus these free models:"
            : "Comma-separated model ids this provider serves; the first is the default. Every role of a session runs on the chosen one, through function calling."}
        </span>
      </label>
      {provider === "openrouter" ? (
        <ul className="prov__free">
          {view.free_models.map((name) => <li key={name}><code>{modelLabel(name)}</code></li>)}
        </ul>
      ) : null}
      <div className="prov__actions">
        <button className="btn btn--primary" type="submit" disabled={saving}>Save provider</button>
        {view.key_saved ? (
          <button className="btn" type="button" disabled={saving} onClick={(event) => void submit(event, true)}>
            Remove saved key
          </button>
        ) : null}
      </div>
      {status ? <div className={status.kind === "error" ? "fv__error" : "set__note"}>{status.text}</div> : null}
    </form>
  );
}
