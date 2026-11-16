/**
 * What the agent remembers between sessions, and a way to make it forget.
 *
 * Confirmed preferences are written only when you confirm one in a
 * conversation; episodes are compact records of earlier runs that planning may
 * reuse (their input files only under the "reuse my last inputs" preference,
 * and only after the same sha256 check "Check inputs" runs here).
 */
import { useCallback, useEffect, useState } from "react";

import { DaemonConfig } from "../../transport/daemon";
import { EpisodeCheck, MemorySnapshot, checkEpisode, forgetEpisode, forgetPreference, readMemory } from "../../transport/files";

const STATE_WORDS: Record<string, string> = {
  unchanged: "same file",
  rules_changed: "same file, rules changed",
  changed: "changed",
  missing: "missing",
  unverified: "not fingerprinted",
};

export function MemoryView({ config }: { config: DaemonConfig }) {
  const [memory, setMemory] = useState<MemorySnapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [checks, setChecks] = useState<Record<string, EpisodeCheck | "checking">>({});

  const load = useCallback(() => {
    readMemory(config).then(setMemory).catch((problem) => setError(String(problem)));
  }, [config]);
  useEffect(load, [load]);

  const act = async (work: Promise<unknown>) => {
    setError(null);
    try { await work; } catch (problem) { setError(problem instanceof Error ? problem.message : String(problem)); }
    load();
  };

  if (!memory) return error ? <div className="fv__error">{error}</div> : <div className="pane__empty">Reading memory…</div>;
  return (
    <div className="set__group mem">
      <div className="set__title">Memory</div>
      <p className="set__note">
        What the agent carries from one session to the next (profile <code>{memory.profile_id}</code>).
        Removing an item takes effect from the next turn.
      </p>
      {error ? <div className="fv__error">{error}</div> : null}

      <div className="mem__heading">Confirmed preferences</div>
      {memory.preferences.length === 0 ? <div className="mem__empty">None. A preference is saved only when you confirm one in a conversation.</div> : (
        <ul className="mem__list">
          {memory.preferences.map((item) => (
            <li key={item.key} className="mem__item">
              <div><strong>{item.label}</strong>: <code>{String(item.value)}</code>
                {item.source ? <div className="mem__meta">Why: {item.source}</div> : null}</div>
              <button className="btn btn--small" type="button" onClick={() => {
                if (window.confirm(`Forget the preference "${item.label}"?`)) void act(forgetPreference(config, item.key));
              }}>Forget</button>
            </li>
          ))}
        </ul>
      )}

      <div className="mem__heading">Past runs ({memory.episode_count})</div>
      <div className="mem__meta">
        Kept {memory.retention_days.completed} days when completed, {memory.retention_days.failed} when failed,
        {" "}{memory.retention_days.dry_run} as dry runs; at most {memory.max_episodes}.
      </div>
      {memory.episodes.length === 0 ? <div className="mem__empty">No runs remembered yet.</div> : (
        <ul className="mem__list">
          {memory.episodes.map((episode) => {
            const check = checks[episode.episode_id];
            return (
              <li key={episode.episode_id} className="mem__item">
                <div>
                  <strong>{episode.workflow}</strong> · {episode.status} · {new Date(episode.created_at * 1000).toLocaleString()}
                  <div className="mem__meta">{episode.task_summary}</div>
                  {Object.keys(episode.inputs).length ? (
                    <ul className="mem__inputs">
                      {Object.entries(episode.inputs).map(([field, path]) => {
                        const state = check && check !== "checking" ? check.inputs[field] : undefined;
                        return (
                          <li key={field}><code>{field}</code> {path}
                            {state ? <span className={`mem__state mem__state--${state.state}`} title={state.detail}> — {STATE_WORDS[state.state] ?? state.state}</span> : null}
                          </li>
                        );
                      })}
                    </ul>
                  ) : null}
                </div>
                <div className="mem__actions">
                  {Object.keys(episode.inputs).length ? (
                    <button className="btn btn--small" type="button" disabled={check === "checking"} onClick={() => {
                      setChecks((current) => ({ ...current, [episode.episode_id]: "checking" }));
                      checkEpisode(config, episode.episode_id)
                        .then((result) => setChecks((current) => ({ ...current, [episode.episode_id]: result })))
                        .catch((problem) => { setError(String(problem)); setChecks((current) => { const next = { ...current }; delete next[episode.episode_id]; return next; }); });
                    }}>{check === "checking" ? "Checking…" : "Check inputs"}</button>
                  ) : null}
                  <button className="btn btn--small" type="button" onClick={() => {
                    if (window.confirm(`Forget this ${episode.workflow} run? Planning will no longer reuse it.`)) void act(forgetEpisode(config, episode.episode_id));
                  }}>Forget</button>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
