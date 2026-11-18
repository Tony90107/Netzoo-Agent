/**
 * Start a session as an experiment: name it, pick its starting model, and tag it.
 *
 * The model runs every role of the session (reply, routing, interpretation),
 * so the list holds only models the daemon permits under the saved provider:
 * both .env allowlists plus the curated OpenRouter free models, or the models
 * listed for another provider. The model can be switched between turns from
 * the session header; the session records each switch. OpenRouter's free
 * models (ids ending in ":free") are labelled. The menu groups the recommended
 * models apart from ones added through "All models…" (ModelCatalog).
 */
import { FormEvent, useEffect, useRef, useState } from "react";

import { DaemonConfig } from "../../transport/daemon";
import { readSettings } from "../../transport/files";
import { NewSessionOptions } from "../../transport/session";
import { BROWSE_ALL, ModelCatalogDialog, ModelGroups, ModelOptions, groupModels } from "./ModelCatalog";

function allowlisted(value: string | undefined): string[] {
  return (value ?? "").split(",").map((item) => item.trim()).filter((item) => item && item !== "(unset)");
}

/** Models a whole session can run on: allowed for replies and for routing alike. */
export function sessionModels(allowlists: Record<string, string> | undefined): string[] {
  const router = new Set(allowlisted(allowlists?.router));
  return allowlisted(allowlists?.response).filter((name) => router.has(name));
}

export function modelLabel(name: string): string {
  return name.endsWith(":free") ? `${name.slice(0, -":free".length)} (free)` : name;
}

export function NewSessionDialog({
  config,
  onStart,
  onCancel,
}: {
  config: DaemonConfig;
  onStart: (options: NewSessionOptions) => void;
  onCancel: () => void;
}) {
  const [groups, setGroups] = useState<ModelGroups>({ recommended: [], added: [] });
  const [model, setModel] = useState("");
  const [browsing, setBrowsing] = useState(false);
  const [tags, setTags] = useState("");
  const [name, setName] = useState("");
  const dialog = useRef<HTMLDialogElement>(null);

  const load = (keep?: string) => {
    let current = true;
    readSettings(config).then((settings) => {
      if (!current) return;
      const allowed = settings.model_choices?.length ? settings.model_choices : sessionModels(settings.allowlists);
      const fallback = settings.models?.response && settings.models.response !== "(unset)" ? [settings.models.response] : [];
      const options = allowed.length ? allowed : fallback;
      setGroups(groupModels(options, settings.provider?.recommended_models));
      setModel(keep && options.includes(keep) ? keep
        : options.includes(settings.models?.response) ? settings.models.response : options[0] ?? "");
    }).catch(() => undefined);
    return () => { current = false; };
  };
  useEffect(() => load(), [config]);

  useEffect(() => {
    const node = dialog.current;
    if (node && !node.open && typeof node.showModal === "function") node.showModal();
  }, []);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    onStart({
      model: model || undefined,
      tags: tags.split(",").map((item) => item.trim()).filter(Boolean),
      name: name.trim() || undefined,
    });
  };

  return (
    <dialog ref={dialog} className="nsd" aria-label="Start a new session" onCancel={(event) => { event.preventDefault(); onCancel(); }}>
      <form onSubmit={submit}>
        <h2 className="nsd__title">New session</h2>
        <p className="nsd__note">One session is one experiment: its outputs go to their own folder. You can switch model between turns from the session header; each switch is recorded.</p>
        <label className="nsd__field">Name (optional)
          <input value={name} onChange={(event) => setName(event.target.value)} placeholder="e.g. Batch 2: DNA damage vs rewiring" maxLength={80} />
          <span className="nsd__hint">Shown instead of your first request in the session list and in Compare.</span>
        </label>
        <label className="nsd__field">Model
          <select value={model} onChange={(event) => {
            if (event.target.value === BROWSE_ALL) setBrowsing(true);
            else setModel(event.target.value);
          }}>
            {!model ? <option value="">Daemon default</option> : null}
            <ModelOptions groups={groups} label={modelLabel} extra={model || undefined} />
          </select>
          {groups.added.includes(model) ? (
            <span className="nsd__hint">Added from All models: NetZoo was not checked on it, and a paid model is billed to your provider account.</span>
          ) : null}
          {model.endsWith(":free") ? (
            <span className="nsd__hint">Free on OpenRouter: at most 20 requests a minute and 1000 a day (fewer without account credit), often slower; its routing has not been measured like the default model's.</span>
          ) : null}
        </label>
        <label className="nsd__field">Tags
          <input value={tags} onChange={(event) => setTags(event.target.value)} placeholder="e.g. pilot, dataset:batch-2, hypothesis:dna-damage" maxLength={400} />
          <span className="nsd__hint">Comma-separated labels, or fields as key:value; Compare lines fields up side by side.</span>
        </label>
        <div className="nsd__actions">
          <button className="btn" type="button" onClick={onCancel}>Cancel</button>
          <button className="btn btn--primary" type="submit">Start session</button>
        </div>
      </form>
      {browsing ? (
        <ModelCatalogDialog config={config} current={model}
          onCancel={() => setBrowsing(false)}
          onPick={(next) => { setBrowsing(false); setModel(next); load(next); }} />
      ) : null}
    </dialog>
  );
}
