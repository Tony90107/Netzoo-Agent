/**
 * Start a session as an experiment: name it, pick its model once, and tag it.
 *
 * The model list is the daemon's own allowlist, so nothing here widens it; a
 * session keeps its model for its whole life, including when it is resumed.
 */
import { FormEvent, useEffect, useRef, useState } from "react";

import { DaemonConfig } from "../../transport/daemon";
import { readSettings } from "../../transport/files";
import { NewSessionOptions } from "../../transport/session";

function allowlisted(value: string | undefined): string[] {
  return (value ?? "").split(",").map((item) => item.trim()).filter((item) => item && item !== "(unset)");
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
  const [models, setModels] = useState<string[]>([]);
  const [model, setModel] = useState("");
  const [tags, setTags] = useState("");
  const [name, setName] = useState("");
  const dialog = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    let current = true;
    readSettings(config).then((settings) => {
      if (!current) return;
      const allowed = allowlisted(settings.allowlists?.response);
      const fallback = settings.models?.response && settings.models.response !== "(unset)" ? [settings.models.response] : [];
      const options = allowed.length ? allowed : fallback;
      setModels(options);
      setModel(options.includes(settings.models?.response) ? settings.models.response : options[0] ?? "");
    }).catch(() => undefined);
    return () => { current = false; };
  }, [config]);

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
        <p className="nsd__note">One session is one experiment: its model is fixed for its whole life, and its outputs go to their own folder.</p>
        <label className="nsd__field">Name (optional)
          <input value={name} onChange={(event) => setName(event.target.value)} placeholder="e.g. Batch 2: DNA damage vs rewiring" maxLength={80} />
          <span className="nsd__hint">Shown instead of your first request in the session list and in Compare.</span>
        </label>
        <label className="nsd__field">Model
          <select value={model} onChange={(event) => setModel(event.target.value)} disabled={models.length <= 1}>
            {models.length === 0 ? <option value="">Daemon default</option> : null}
            {models.map((name) => <option key={name} value={name}>{name}</option>)}
          </select>
          {models.length === 1 ? <span className="nsd__hint">The only model the allowlist permits.</span> : null}
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
    </dialog>
  );
}
