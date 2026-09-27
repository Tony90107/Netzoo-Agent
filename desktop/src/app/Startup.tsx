/**
 * What the user sees before the agent can take a question.
 *
 * The failure screen is the point of this file. "Could not connect" tells
 * someone nothing; the daemon has a small number of ways to not start, each
 * with exactly one thing that fixes it, so each one says that thing.
 */
import { Phase } from "../transport/daemon";

const RETRY_LABEL: Record<string, string> = {
  docker_not_running: "I started Docker — retry",
  docker_missing: "Retry",
  port_in_use: "Retry",
  compose_timeout: "Retry",
  health_timeout: "Retry",
};

export function Startup({ phase, onRetry, onEnvironment }: { phase: Phase; onRetry: () => void; onEnvironment: () => void }) {
  if (phase.name === "failed") {
    const { fault } = phase;
    return (
      <div className="startup startup--failed">
        <div className="startup__card">
          <h1 className="startup__title">{fault.message}</h1>
          <p className="startup__remedy">{fault.remedy}</p>
          {fault.detail ? (
            <details className="startup__detail">
              <summary>Technical detail</summary>
              <pre>{fault.detail}</pre>
            </details>
          ) : null}
          <button className="startup__retry" type="button" onClick={onRetry}>
            {RETRY_LABEL[fault.kind] ?? "Retry"}
          </button>
          <button className="btn btn--quiet" type="button" onClick={onEnvironment}>Check environment</button>
        </div>
      </div>
    );
  }

  const step = phase.name === "starting" ? phase.step : "Starting";
  const elapsed = phase.name === "starting" ? phase.sinceMs : 0;
  return (
    <div className="startup">
      <div className="startup__card">
        <div className="startup__spinner" aria-hidden="true" />
        <h1 className="startup__title">Starting NetZoo Agent</h1>
        <p className="startup__step">{step}…</p>
        {elapsed > 8000 ? (
          <p className="startup__slow">
            Taking longer than usual. The first launch builds the container image,
            which can take several minutes.
          </p>
        ) : null}
      </div>
    </div>
  );
}
