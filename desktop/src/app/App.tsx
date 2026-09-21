/**
 * The three-pane shell.
 *
 * M3 fills the middle pane and the Plan tab. Timeline and Files still carry
 * their placeholders; the trace events are already arriving and accumulating
 * in session state, so M4 is a rendering job rather than a plumbing one.
 */
import { useCallback, useEffect, useRef, useState } from "react";

import { Conversation } from "../features/conversation/Conversation";
import { FilesPane } from "../features/files/FilesPane";
import { PlanPane } from "../features/plan/PlanPane";
import { SessionsPane } from "../features/sessions/SessionsPane";
import { SettingsView } from "../features/sessions/SettingsView";
import { TranscriptView } from "../features/sessions/TranscriptView";
import { Timeline } from "../features/timeline/Timeline";
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
import { Splitter, usePaneSize } from "./Splitter";
import { Startup } from "./Startup";

function connectionText(session: SessionState | null, port: number): string {
  if (!session) return "Connecting…";
  switch (session.connection) {
    case "open":
      return `Session ${session.sessionId} · port ${port}`;
    case "reconnecting":
      return "Reconnecting…";
    case "closed":
      return session.closedReason ?? "Disconnected.";
    default:
      return "Connecting…";
  }
}

function StatusBar({
  session,
  port,
  onNewSession,
}: {
  session: SessionState | null;
  port: number;
  onNewSession: () => void;
}) {
  const usage = session?.usage;
  return (
    <footer className="statusbar">
      <span
        className={`statusbar__dot${
          session?.connection === "open"
            ? ""
            : session?.connection === "reconnecting"
              ? " is-warn"
              : " is-idle"
        }`}
        aria-hidden="true"
      />
      <span>{connectionText(session, port)}</span>
      {session?.missedEvents ? (
        <span
          className="statusbar__warn"
          title="The daemon could only replay its most recent events, so the timeline above is missing part of this run."
        >
          timeline incomplete
        </span>
      ) : null}
      {session?.connection === "closed" ? (
        <button className="btn btn--quiet btn--small" type="button" onClick={onNewSession}>
          Start a new session
        </button>
      ) : null}
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
  const [showSettings, setShowSettings] = useState(false);
  // An earlier session being read. Reading one never touches the live session.
  const [viewingSessionId, setViewingSessionId] = useState<string | null>(null);

  // Pane sizes, remembered per divider. Minimums keep any pane from being
  // dragged out of existence.
  const [sidebarWidth, setSidebarWidth] = usePaneSize("sidebar", 240, 170, 520);
  const [inspectorWidth, setInspectorWidth] = usePaneSize("inspector", 340, 260, 760);
  const [planHeight, setPlanHeight] = usePaneSize("plan", 330, 120, 1000);
  const [timelineHeight, setTimelineHeight] = usePaneSize("timeline", 260, 120, 1000);
  const [session, setSession] = useState<SessionState | null>(null);
  const socket = useRef<SessionSocket | null>(null);
  const startedAt = useRef(0);

  const connect = useCallback(async (resume?: string) => {
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
      const sessionId = await createSession(config, resume);
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
    <div
      className="shell"
      style={{
        gridTemplateColumns: `${sidebarWidth}px 5px minmax(0, 1fr) 5px ${inspectorWidth}px`,
      }}
    >
      <aside className="sidebar" style={{ width: sidebarWidth }}>
        <div className="sidebar__brand">NetZoo Agent</div>
        <SessionsPane
          config={phase.config}
          currentId={session.sessionId}
          selectedId={viewingSessionId}
          onOpen={(sessionId) => {
            setShowSettings(false);
            setViewingSessionId(sessionId);
          }}
          onResume={(sessionId) => {
            setViewingSessionId(null);
            socket.current?.close();
            void connect(sessionId);
          }}
        />
        <nav className="sidebar__links">
          <button
            type="button"
            onClick={() => {
              setViewingSessionId(null);
              setShowSettings((value) => !value);
            }}
          >
            {showSettings ? "Conversation" : "Settings"}
          </button>
          <button
            type="button"
            onClick={() => {
              setViewingSessionId(null);
              setShowSettings(false);
              socket.current?.close();
              void connect();
            }}
          >
            New session
          </button>
        </nav>
      </aside>

      <Splitter
        orientation="vertical"
        label="Resize the session list"
        onDelta={(delta) => setSidebarWidth(sidebarWidth + delta)}
      />

      <main className="conversation">
        {showSettings ? (
          <SettingsView config={phase.config} onClose={() => setShowSettings(false)} />
        ) : viewingSessionId ? (
          <TranscriptView
            config={phase.config}
            sessionId={viewingSessionId}
            onClose={() => setViewingSessionId(null)}
            onResume={(sessionId) => {
              setViewingSessionId(null);
              socket.current?.close();
              void connect(sessionId);
            }}
          />
        ) : (
        <Conversation
          session={session}
          onAnswer={(text) => socket.current?.answer(text)}
          onSlash={(command) => socket.current?.answer(command, false)}
          onApprove={(hash) => socket.current?.approveExecution(hash)}
          onDecline={() => socket.current?.declineExecution()}
          onCancel={() => socket.current?.cancel()}
        />
        )}
      </main>

      <Splitter
        orientation="vertical"
        label="Resize the inspector"
        onDelta={(delta) => setInspectorWidth(inspectorWidth - delta)}
      />

      <aside className="inspector" style={{ width: inspectorWidth }}>
        <div className="inspector__slot" style={{ height: planHeight }}>
          <PlanPane plan={plan} hash={session.view?.plan_hash ?? null} />
        </div>
        <Splitter
          orientation="horizontal"
          label="Resize the plan"
          onDelta={(delta) => setPlanHeight(planHeight + delta)}
        />
        <div className="inspector__slot" style={{ height: timelineHeight }}>
          <Timeline trace={session.trace} />
        </div>
        <Splitter
          orientation="horizontal"
          label="Resize the timeline"
          onDelta={(delta) => setTimelineHeight(timelineHeight + delta)}
        />
        <div className="inspector__slot inspector__slot--rest">
          <FilesPane config={phase.config} />
        </div>
      </aside>

      <StatusBar
        session={session}
        port={phase.config.port}
        onNewSession={() => void connect()}
      />
    </div>
  );
}

export type { DaemonConfig };
