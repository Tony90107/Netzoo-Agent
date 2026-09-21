/**
 * The three-pane shell.
 *
 * M2 fills none of the panes: this milestone is about the window existing, the
 * daemon coming up behind it, and the failure path being something a person
 * can act on. The panes carry their intended content as labelled placeholders
 * so the next milestones have somewhere to land.
 */
import { useCallback, useEffect, useRef, useState } from "react";

import {
  DaemonConfig,
  DaemonFault,
  Phase,
  startDaemon,
  stopDaemon,
} from "../transport/daemon";
import { Startup } from "./Startup";

type PaneProps = { title: string; hint: string; wide?: boolean };

function Pane({ title, hint, wide }: PaneProps) {
  return (
    <section className={wide ? "pane pane--wide" : "pane"}>
      <header className="pane__header">{title}</header>
      <div className="pane__empty">{hint}</div>
    </section>
  );
}

function StatusBar({ config, tookMs }: { config: DaemonConfig; tookMs: number }) {
  return (
    <footer className="statusbar">
      <span className="statusbar__dot" aria-hidden="true" />
      <span>Daemon ready on port {config.port}</span>
      <span className="statusbar__spacer" />
      <span>cold start {(tookMs / 1000).toFixed(1)}s</span>
    </footer>
  );
}

export function App() {
  const [phase, setPhase] = useState<Phase>({ name: "idle" });
  const startedAt = useRef(0);

  const connect = useCallback(async () => {
    startedAt.current = Date.now();
    setPhase({ name: "starting", step: "Starting", sinceMs: 0 });
    try {
      const { config } = await startDaemon((step) =>
        setPhase({
          name: "starting",
          step,
          sinceMs: Date.now() - startedAt.current,
        }),
      );
      setPhase({ name: "ready", config, tookMs: Date.now() - startedAt.current });
    } catch (fault) {
      setPhase({
        name: "failed",
        fault: fault as DaemonFault,
        tookMs: Date.now() - startedAt.current,
      });
    }
  }, []);

  useEffect(() => {
    void connect();
    const onUnload = () => {
      void stopDaemon();
    };
    window.addEventListener("beforeunload", onUnload);
    return () => window.removeEventListener("beforeunload", onUnload);
  }, [connect]);

  if (phase.name !== "ready") {
    return <Startup phase={phase} onRetry={connect} />;
  }

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="sidebar__brand">NetZoo Agent</div>
        <Pane title="Sessions" hint="Conversations appear here once M5 lands." />
        <nav className="sidebar__links">
          <button type="button" disabled>
            Settings
          </button>
          <button type="button" disabled>
            Outputs
          </button>
        </nav>
      </aside>
      <main className="conversation">
        <Pane
          title="Conversation"
          hint="The task prompt, plan card and execution approval land here in M3."
          wide
        />
      </main>
      <aside className="inspector">
        <Pane title="Plan" hint="Workflow, evidence ledger and steps (M3)." />
        <Pane title="Timeline" hint="Trace events from the run (M4)." />
        <Pane title="Files" hint="Outputs and result viewers (M5)." />
      </aside>
      <StatusBar config={phase.config} tookMs={phase.tookMs} />
    </div>
  );
}
