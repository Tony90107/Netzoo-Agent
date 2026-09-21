/**
 * The three-pane shell.
 *
 * M3 fills the middle pane and the Plan tab. Timeline and Files still carry
 * their placeholders; the trace events are already arriving and accumulating
 * in session state, so M4 is a rendering job rather than a plumbing one.
 */
import { useCallback, useEffect, useRef, useState } from "react";

import { Conversation } from "../features/conversation/Conversation";
import { PlanPane } from "../features/plan/PlanPane";
import {
  DaemonConfig,
  DaemonFault,
  Phase,
  startDaemon,
  stopDaemon,
} from "../transport/daemon";
import {
  SessionSocket,
  SessionState,
  createSession,
  emptySession,
} from "../transport/session";
import { Startup } from "./Startup";

function Pane({ title, hint }: { title: string; hint: string }) {
  return (
    <section className="pane">
      <header className="pane__header">{title}</header>
      <div className="pane__empty">{hint}</div>
    </section>
  );
}

function StatusBar({ session, port }: { session: SessionState | null; port: number }) {
  const usage = session?.usage;
  return (
    <footer className="statusbar">
      <span
        className={`statusbar__dot${session?.connection === "open" ? "" : " is-idle"}`}
        aria-hidden="true"
      />
      <span>
        {session?.connection === "open"
          ? `Session ${session.sessionId} · port ${port}`
          : "Connecting…"}
      </span>
      <span className="statusbar__spacer" />
      {usage ? (
        <span>
          {usage.total_tokens.toLocaleString()} / {usage.budget_tokens.toLocaleString()} tokens
        </span>
      ) : null}
    </footer>
  );
}

export function App() {
  const [phase, setPhase] = useState<Phase>({ name: "idle" });
  const [session, setSession] = useState<SessionState | null>(null);
  const socket = useRef<SessionSocket | null>(null);
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
      const sessionId = await createSession(config);
      setSession(emptySession(sessionId));
      socket.current = new SessionSocket(config, sessionId, (apply) =>
        setSession((current) => (current ? apply(current) : current)),
      );
      socket.current.open();
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
      socket.current?.close();
      void stopDaemon();
    };
    window.addEventListener("beforeunload", onUnload);
    return () => window.removeEventListener("beforeunload", onUnload);
  }, [connect]);

  if (phase.name !== "ready" || !session) {
    return <Startup phase={phase} onRetry={connect} />;
  }

  const plan = session.view?.plan ?? null;

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="sidebar__brand">NetZoo Agent</div>
        <Pane title="Sessions" hint="Conversation history arrives in M5." />
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
        <Conversation
          session={session}
          onAnswer={(text) => socket.current?.answer(text)}
          onSlash={(command) => socket.current?.answer(command, false)}
          onApprove={(hash) => socket.current?.approveExecution(hash)}
          onDecline={() => socket.current?.declineExecution()}
          onCancel={() => socket.current?.cancel()}
        />
      </main>

      <aside className="inspector">
        <PlanPane plan={plan} hash={session.view?.plan_hash ?? null} />
        <Pane
          title={`Timeline (${session.trace.length})`}
          hint="Trace events are arriving; M4 renders them."
        />
        <Pane title="Files" hint="Outputs and result viewers (M5)." />
      </aside>

      <StatusBar session={session} port={phase.config.port} />
    </div>
  );
}

export type { DaemonConfig };
