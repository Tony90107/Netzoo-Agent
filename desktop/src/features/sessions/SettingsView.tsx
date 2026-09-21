/**
 * What this daemon is running under.
 *
 * Read-only, deliberately. The model allowlists and the token budget are the
 * limits that stop a stray request reaching an expensive model; a window that
 * could edit them would be a window that could remove them. Changing them is
 * an edit to the environment the container starts with.
 */
import { useEffect, useState } from "react";

import { DaemonConfig } from "../../transport/daemon";
import { EffectiveSettings, readSettings } from "../../transport/files";

function Group({ title, rows }: { title: string; rows: [string, string][] }) {
  return (
    <div className="set__group">
      <div className="set__title">{title}</div>
      <table className="set__table">
        <tbody>
          {rows.map(([label, value]) => (
            <tr key={label}>
              <td className="set__key">{label}</td>
              <td className="set__value">{value}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function SettingsView({ config, onClose }: { config: DaemonConfig; onClose: () => void }) {
  const [settings, setSettings] = useState<EffectiveSettings | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    readSettings(config)
      .then(setSettings)
      .catch((problem) => setError(String(problem)));
  }, [config]);

  return (
    <section className="pane pane--wide">
      <header className="pane__header">
        Settings
        <button className="pane__action" type="button" onClick={onClose}>
          close
        </button>
      </header>
      <div className="pane__scroll set">
        {error ? <div className="fv__error">{error}</div> : null}
        {settings ? (
          <>
            <p className="set__note">
              Reported, not editable. These limits are what the agent enforces;
              changing one means changing the environment the daemon starts with.
            </p>
            <Group
              title="Models"
              rows={Object.entries(settings.models).map(([k, v]) => [k, v])}
            />
            <Group
              title="Allowlists"
              rows={Object.entries(settings.allowlists).map(([k, v]) => [k, v])}
            />
            <Group
              title="Limits"
              rows={Object.entries(settings.limits).map(([k, v]) => [
                k,
                typeof v === "number" ? v.toLocaleString() : String(v),
              ])}
            />
            <Group
              title="Paths"
              rows={Object.entries(settings.paths).map(([k, v]) => [k, v || "(not set)"])}
            />
            <Group
              title="Provider"
              rows={[["OPENROUTER_API_KEY", settings.api_key_present ? "present" : "missing"]]}
            />
          </>
        ) : (
          <div className="pane__empty">Reading settings…</div>
        )}
      </div>
    </section>
  );
}
