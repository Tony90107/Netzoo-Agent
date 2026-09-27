import { useEffect, useRef, useState } from "react";
import type { DaemonConfig } from "../../transport/daemon";
import { checkHostEnvironment, checkRuntimeEnvironment, type EnvironmentCheck, type EnvironmentReport } from "../../transport/environment";

function Checks({ checks }: { checks: EnvironmentCheck[] }) {
  return <ul className="env__checks">{checks.map((check, index) => (
    <li className={`env__check env__check--${check.status}`} key={`${check.key}-${index}`}>
      <div className="env__check-head"><strong>{check.label}</strong><span className={`state state--${check.status}`}>{check.status}</span></div>
      <p>{check.detail}</p>
      {check.remedy ? <p className="env__remedy">{check.remedy}</p> : null}
    </li>
  ))}</ul>;
}

export function EnvironmentPane({ config, onClose }: { config: DaemonConfig | null; onClose?: () => void }) {
  const [host, setHost] = useState<EnvironmentCheck[]>([]);
  const [runtime, setRuntime] = useState<EnvironmentReport | null>(null);
  const [busy, setBusy] = useState(false);
  const [checkedAt, setCheckedAt] = useState("");
  const [error, setError] = useState("");
  const generation = useRef(0);

  async function refresh() {
    const request = ++generation.current;
    setBusy(true); setError("");
    const results = await Promise.allSettled([
      checkHostEnvironment(),
      config ? checkRuntimeEnvironment(config) : Promise.resolve(null),
    ]);
    if (request !== generation.current) return;
    const [hostResult, runtimeResult] = results;
    setHost(hostResult.status === "fulfilled" ? hostResult.value : [{
      key: "host", label: "Host environment", status: "unknown", detail: String(hostResult.reason),
      remedy: "Check again or run docker info in a terminal.",
    }]);
    setRuntime(runtimeResult.status === "fulfilled" ? runtimeResult.value : null);
    if (runtimeResult.status === "rejected") setError(String(runtimeResult.reason));
    setCheckedAt(new Date().toLocaleTimeString()); setBusy(false);
  }

  useEffect(() => {
    void refresh();
    return () => { generation.current += 1; };
    // Each config identifies a daemon; stale checks cannot overwrite a later one.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [config]);

  return (
    <section className="pane env" aria-labelledby="environment-title" aria-busy={busy}>
      <header className="pane__header">
        <span id="environment-title">Environment</span>
        <button className="pane__action" type="button" disabled={busy} onClick={() => void refresh()}>{busy ? "Checking…" : "Check again"}</button>
        {onClose ? <button className="pane__action" type="button" onClick={onClose}>Back</button> : null}
      </header>
      <div className="pane__scroll env__scroll">
        <p className="env__intro">Check the environment before preparing an analysis. These checks do not run a workflow.</p>
        <p className="env__checked" role="status">{busy ? "Checking Docker, the image, and the agent environment…" : checkedAt ? `Last checked at ${checkedAt}` : ""}</p>
        <h2>Host Docker and image</h2>
        <Checks checks={host} />
        <h2>Agent environment</h2>
        {error ? <p className="fv__error" role="alert">{error}</p> : null}
        {runtime ? <>
          <Checks checks={runtime.checks} />
          {runtime.source_ref ? <p className="env__ref">netZooPy source commit: <code>{runtime.source_ref}</code></p> : null}
          <p className="env__intro">{runtime.note}</p>
        </> : !busy && !error ? <p className="env__intro">The agent is not connected. Start it to check its Python package and output directory.</p> : null}
        <p className="env__intro">In Conversation, <code>/doctor</code> reports the agent environment. A GitHub account is not required to run the installed workflows.</p>
      </div>
    </section>
  );
}
