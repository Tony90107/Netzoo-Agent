/**
 * The session's model, switchable between turns.
 *
 * Switching rebuilds only the worker's model layer: the conversation, the open
 * task, a pending question or plan and the trace run carry over. It is refused
 * while a turn is running (the worker would only read it afterwards anyway),
 * and the daemon still refuses any model its allowlists do not name.
 */
import { useEffect, useState } from "react";

import { DaemonConfig } from "../../transport/daemon";
import { readSettings } from "../../transport/files";
import { BROWSE_ALL, ModelCatalogDialog, ModelGroups, ModelOptions, groupModels } from "./ModelCatalog";
import { sessionModels } from "./NewSessionDialog";

/** "nvidia/nemotron-3-ultra-550b-a55b:free" → "Nemotron 3 Ultra · free". */
export function pickerLabel(name: string): string {
  const free = name.endsWith(":free");
  const base = (name.split("/").pop() ?? name).replace(/:free$/, "");
  const known: Record<string, string> = {
    "gpt-4o-mini": "GPT-4o mini",
    "nemotron-3-ultra-550b-a55b": "Nemotron 3 Ultra",
    "ernie-5.5-flash-preview": "ERNIE 5.5 Flash",
    "nemotron-3.5-super-vl": "Nemotron 3.5 Super VL",
    "dots-3-note-preview": "Dots3 Note",
  };
  const label = known[base] ?? base.split("-").map((part) => part.charAt(0).toUpperCase() + part.slice(1)).join(" ");
  return free ? `${label} · free` : label;
}

export function ModelSwitch({
  config,
  model,
  busy,
  refusals,
  onSwitch,
}: {
  config: DaemonConfig;
  model: string;
  busy: boolean;
  /** How many switches the worker has refused; a new refusal ends "switching…". */
  refusals: number;
  onSwitch: (model: string) => void;
}) {
  const [groups, setGroups] = useState<ModelGroups>({ recommended: [], added: [] });
  const [browsing, setBrowsing] = useState(false);
  const [pending, setPending] = useState<string | null>(null);
  const [fallback, setFallback] = useState("");

  const refresh = () => {
    readSettings(config).then((settings) => {
      const choices = settings.model_choices?.length ? settings.model_choices : sessionModels(settings.allowlists);
      setGroups(groupModels(choices, settings.provider?.recommended_models));
      // A session started without choosing runs on the daemon's default model.
      const daemonDefault = settings.provider && settings.provider.provider !== "openrouter"
        ? settings.provider.models[0] : settings.models?.response;
      setFallback(daemonDefault && daemonDefault !== "(unset)" ? daemonDefault : "");
    }).catch(() => undefined);
  };
  // Re-read on focus too: a provider saved in Settings changes the list.
  useEffect(refresh, [config]);
  useEffect(() => { setPending(null); }, [model, refusals]);

  model = model || fallback;
  const switchTo = (next: string) => {
    if (!next || next === model) return;
    setPending(next);
    onSwitch(next);
  };
  const shown = pending ?? model;
  return (
    <>
    <label className="model-picker" title={busy
      ? "The model can be switched once this turn finishes"
      : "Switch the model for the rest of this conversation; everything said so far carries over"}>
      <select
        aria-label="Session model"
        value={shown}
        disabled={busy}
        onFocus={refresh}
        onChange={(event) => {
          const next = event.target.value;
          if (next === BROWSE_ALL) { setBrowsing(true); return; }
          switchTo(next);
        }}
      >
        {!shown ? <option value="">Daemon default</option> : null}
        <ModelOptions groups={groups} label={pickerLabel} extra={shown || undefined} />
      </select>
      {pending ? <span className="model-picker__pending">Switching…</span> : null}
    </label>
    {browsing ? (
      <ModelCatalogDialog config={config} current={model}
        onCancel={() => setBrowsing(false)}
        onPick={(next) => { setBrowsing(false); refresh(); switchTo(next); }} />
    ) : null}
    </>
  );
}
