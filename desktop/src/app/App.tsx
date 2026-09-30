import { useCallback, useEffect, useRef, useState } from "react";

import { Conversation } from "../features/conversation/Conversation";
import { FilesPane } from "../features/files/FilesPane";
import { EnvironmentPane } from "../features/help/EnvironmentPane";
import { NetZooPyGuide } from "../features/help/NetZooPyGuide";
import { PlanPane } from "../features/plan/PlanPane";
import { CompareView } from "../features/sessions/CompareView";
import { NewSessionDialog } from "../features/sessions/NewSessionDialog";
import { SessionsPane } from "../features/sessions/SessionsPane";
import { SettingsView } from "../features/sessions/SettingsView";
import { TagEditor } from "../features/sessions/TagEditor";
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
  NewSessionOptions,
  SessionSocket,
  SessionState,
  createSession,
  emptySession,
} from "../transport/session";
import { Splitter, usePaneSize } from "./Splitter";
import { Startup } from "./Startup";

type LayoutChoice = "auto" | "focus" | "inspector";
function savedLayout(): LayoutChoice {
  try { const value = localStorage.getItem("netzoo.layout.view"); return value === "focus" || value === "inspector" ? value : "auto"; }
  catch { return "auto"; }
}

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
  const [outputPath, setOutputPath] = useState<string | undefined>();
  const [historyOutputPath, setHistoryOutputPath] = useState<string | null>(null);
  const [outputReturn, setOutputReturn] = useState<"conversation" | "activity" | null>(null);
  const [layout, setLayout] = useState<LayoutChoice>(savedLayout);
  const [startupEnvironment, setStartupEnvironment] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [centerTab, setCenterTab] = useState<"conversation" | "outputs" | "guide" | "environment" | "activity">("conversation");
  // An earlier session being read. Reading one never touches the live session.
  const [viewingSessionId, setViewingSessionId] = useState<string | null>(null);
  const [compareIds, setCompareIds] = useState<string[] | null>(null);
  const [newSessionOpen, setNewSessionOpen] = useState(false);
  const [sessionTags, setSessionTags] = useState<string[]>([]);
  const [sessionModel, setSessionModel] = useState<string>("");

  // Pane sizes, remembered per divider. Minimums keep any pane from being
  // dragged out of existence.
  const [sidebarWidth, setSidebarWidth] = usePaneSize("sidebar", 240, 170, 520);
  const [inspectorWidth, setInspectorWidth] = usePaneSize("inspector", 340, 260, 760);
  const [planHeight, setPlanHeight] = usePaneSize("plan", 330, 120, 1000);
  const [session, setSession] = useState<SessionState | null>(null);
  const socket = useRef<SessionSocket | null>(null);
  const connectionGeneration = useRef(0);
  const startedAt = useRef(0);

  const connect = useCallback(async (resume?: string, options: NewSessionOptions = {}) => {
    setHistoryOutputPath(null); setOutputReturn(null); setViewingSessionId(null); setShowSettings(false);
    setCompareIds(null); setSessionTags(options.tags ?? []); setSessionModel(options.model ?? "");
    const generation = ++connectionGeneration.current;
    socket.current?.close();
    socket.current = null;
    startedAt.current = Date.now();
    setPhase({ name: "starting", step: "Starting", sinceMs: 0 });
    try {
      const { config } = await startDaemon((step) =>
        generation === connectionGeneration.current && setPhase({
          name: "starting",
          step,
          sinceMs: Date.now() - startedAt.current,
        }),
      );
      if (generation !== connectionGeneration.current) return;
      const sessionId = await createSession(config, resume, options);
      if (generation !== connectionGeneration.current) {
        // This launch created the unused session. Retire it without touching
        // the current one or the daemon shared by the desktop shell.
        void fetch(`${config.baseUrl}/v1/sessions/${encodeURIComponent(sessionId)}`, {
          method: "DELETE", headers: { Authorization: `Bearer ${config.token}` },
        }).catch(() => undefined);
        return;
      }
      setSession(emptySession(sessionId));
      socket.current = new SessionSocket(config, sessionId, (apply) =>
        setSession((current) => (current?.sessionId === sessionId ? apply(current) : current)),
      );
      socket.current.open();
      setPhase({ name: "ready", config, tookMs: Date.now() - startedAt.current });
    } catch (fault) {
      if (generation !== connectionGeneration.current) return;
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
    return () => {
      connectionGeneration.current += 1;
      socket.current?.close();
      window.removeEventListener("beforeunload", onUnload);
    };
  }, [connect]);

  if (phase.name !== "ready" || !session) {
    return startupEnvironment ? (
      <div className="startup-environment"><EnvironmentPane config={null} onClose={() => setStartupEnvironment(false)} /></div>
    ) : <Startup phase={phase} onRetry={connect} onEnvironment={() => setStartupEnvironment(true)} />;
  }

  const plan = session.view?.plan ?? null;
  const inspectorVisible = layout === "inspector" || (layout === "auto" && !showSettings && !viewingSessionId && !compareIds && centerTab === "conversation");
  const openSession = (sessionId: string) => {
    setShowSettings(false); setCompareIds(null); setHistoryOutputPath(null); setOutputReturn(null);
    if (sessionId === session.sessionId) { setViewingSessionId(null); setCenterTab("conversation"); return; }
    setCenterTab("conversation"); setViewingSessionId(sessionId);
  };
  const openLiveOutput = (path: string, from: "conversation" | "activity") => {
    setViewingSessionId(null); setShowSettings(false); setHistoryOutputPath(null);
    setOutputPath(path); setOutputReturn(from); setCenterTab("outputs");
  };

  return (
    <div
      className="shell"
      style={{
        gridTemplateColumns: `${sidebarWidth}px 5px minmax(0, 1fr)${inspectorVisible ? ` 5px ${inspectorWidth}px` : ""}`,
      }}
    >
      <aside className="sidebar" style={{ width: sidebarWidth }}>
        <div className="sidebar__brand">NetZoo Agent</div>
        <SessionsPane
          config={phase.config}
          currentId={session.sessionId}
          selectedId={viewingSessionId}
          refreshToken={session.busy}
          onOpen={(sessionId) => {
            setShowSettings(false); setCompareIds(null);
            setCenterTab("conversation");
            setViewingSessionId(sessionId);
            setHistoryOutputPath(null); setOutputReturn(null);
          }}
          onCompare={(sessionIds) => {
            setShowSettings(false); setViewingSessionId(null); setHistoryOutputPath(null); setOutputReturn(null);
            setCompareIds(sessionIds);
          }}
          onResume={(sessionId) => {
            setViewingSessionId(null);
            setCenterTab("conversation");
            socket.current?.close();
            void connect(sessionId);
          }}
        />
        <nav className="sidebar__links">
          <button
            type="button"
            onClick={() => {
              setViewingSessionId(null);
              setHistoryOutputPath(null); setOutputReturn(null); setCenterTab("conversation");
              setShowSettings((value) => !value);
            }}
          >
            {showSettings ? "Conversation" : "Settings"}
          </button>
          <button
            type="button"
            title="Start a new experiment: choose its model and tags"
            onClick={() => setNewSessionOpen(true)}
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

      <main className="workspace">
        <header className="workspace__context">
          <div><span>{viewingSessionId ? "Saved session" : "Current session"}</span><code>{viewingSessionId ?? session.sessionId}</code>{viewingSessionId ? <span className="workspace__readonly">Read only</span> : null}
            {!viewingSessionId ? <>
              {sessionModel ? <span className="workspace__model" title="The model this session runs under">{sessionModel.split("/").pop()}</span> : null}
              <TagEditor config={phase.config} sessionId={session.sessionId} tags={sessionTags} onSaved={setSessionTags} />
            </> : null}
          </div>
          <label>Layout<select aria-label="Workspace layout" value={layout} onChange={(event) => {
            const value = event.target.value as LayoutChoice; setLayout(value);
            try { localStorage.setItem("netzoo.layout.view", value); } catch { /* Keep the choice for this window. */ }
          }}><option value="auto">Automatic</option><option value="focus">Focus view</option><option value="inspector">Show inspector</option></select></label>
        </header>
        {historyOutputPath || (centerTab === "outputs" && outputReturn) ? <div className="workspace__return">
          <button className="btn btn--quiet btn--small" type="button" onClick={() => {
            if (historyOutputPath) setHistoryOutputPath(null);
            else { setCenterTab(outputReturn!); setOutputReturn(null); }
          }}>{historyOutputPath ? "← Back to saved Activity" : outputReturn === "activity" ? "← Back to Activity" : "← Back to conversation"}</button>
          <span>Output preview · {historyOutputPath ?? outputPath}</span>
        </div> : null}
        {!showSettings && !viewingSessionId && !compareIds ? (
          <nav className="workspace__tabs" role="group" aria-label="Workspace views">
            <button
              type="button"
              aria-pressed={centerTab === "conversation"}
              onClick={() => { setOutputReturn(null); setCenterTab("conversation"); }}
            >
              Conversation
            </button>
            <button
              type="button"
              aria-pressed={centerTab === "outputs"}
              onClick={() => { setOutputReturn(null); setOutputPath(undefined); setCenterTab("outputs"); }}
            >
              Outputs
            </button>
            <button
              type="button"
              aria-pressed={centerTab === "guide"}
              onClick={() => { setOutputReturn(null); setCenterTab("guide"); }}
            >
              Method guide
            </button>
            <button type="button" aria-pressed={centerTab === "environment"} onClick={() => { setOutputReturn(null); setCenterTab("environment"); }}>Environment</button>
            <button type="button" aria-pressed={centerTab === "activity"} onClick={() => { setOutputReturn(null); setCenterTab("activity"); }}>Activity</button>
          </nav>
        ) : null}
        <div className="workspace__content">
          {showSettings ? (
            <SettingsView config={phase.config} onClose={() => setShowSettings(false)} />
          ) : compareIds ? (
            <CompareView
              config={phase.config}
              sessionIds={compareIds}
              onClose={() => setCompareIds(null)}
              onOpenSession={openSession}
              onOpenOutput={(path) => { setCompareIds(null); openLiveOutput(path, "conversation"); }}
            />
          ) : viewingSessionId ? (
            <>
            <div className="workspace__page" hidden={historyOutputPath !== null}>
            <TranscriptView
              key={viewingSessionId}
              config={phase.config}
              sessionId={viewingSessionId}
              onOpenOutput={setHistoryOutputPath}
              onClose={() => { setViewingSessionId(null); setHistoryOutputPath(null); }}
              onResume={(sessionId) => {
                setViewingSessionId(null);
                setCenterTab("conversation");
                socket.current?.close();
                void connect(sessionId);
              }}
            />
            </div>
            {historyOutputPath ? <FilesPane key={`history-${historyOutputPath}`} config={phase.config} initialPath={historyOutputPath} onOpenSession={openSession} /> : null}
            </>
          ) : centerTab === "outputs" ? (
            <FilesPane key={session.sessionId} config={phase.config} initialPath={outputPath} onOpenSession={openSession} />
          ) : centerTab === "environment" ? (
            <EnvironmentPane config={phase.config} />
          ) : centerTab === "guide" ? (
            <NetZooPyGuide />
          ) : null}
          <div className="workspace__page" hidden={showSettings || !!viewingSessionId || !!compareIds || centerTab !== "activity"}>
            <Timeline key={`activity-${session.sessionId}`} trace={session.trace} entries={session.entries} sessionId={session.sessionId} busy={session.busy} incomplete={session.missedEvents} onOpenOutput={(path) => openLiveOutput(path, "activity")} />
          </div>
          <div className="workspace__page" hidden={showSettings || !!viewingSessionId || !!compareIds || centerTab !== "conversation"}>
            <Conversation
              key={session.sessionId}
              session={session}
              onAnswer={(text) => socket.current?.answer(text)}
              onSlash={(command) => socket.current?.answer(command, false)}
              onApprove={(hash) => socket.current?.approveExecution(hash)}
              onDecline={() => socket.current?.declineExecution()}
              onCancel={() => socket.current?.cancel()}
              onOpenOutputs={(paths) => { if (paths[0]) openLiveOutput(paths[0], "conversation"); }}
            />
          </div>
        </div>
      </main>

      {inspectorVisible ? <Splitter
        orientation="vertical"
        label="Resize the inspector"
        onDelta={(delta) => setInspectorWidth(inspectorWidth - delta)}
      /> : null}

      <aside className="inspector" aria-label="Current session inspector" hidden={!inspectorVisible} style={{ width: inspectorWidth }}>
        <div className="inspector__context">Current session · <code>{session.sessionId}</code></div>
        <div className="inspector__slot" style={{ height: planHeight }}>
          <PlanPane plan={plan} hash={session.view?.plan_hash ?? null} />
        </div>
        <Splitter
          orientation="horizontal"
          label="Resize the plan"
          onDelta={(delta) => setPlanHeight(planHeight + delta)}
        />
        <div className="inspector__slot inspector__slot--rest">
          <Timeline key={session.sessionId} trace={session.trace} entries={session.entries} sessionId={session.sessionId} busy={session.busy} incomplete={session.missedEvents} onExpand={() => { setViewingSessionId(null); setShowSettings(false); setHistoryOutputPath(null); setOutputReturn(null); setCenterTab("activity"); }} onOpenOutput={(path) => openLiveOutput(path, "conversation")} />
        </div>
      </aside>

      {newSessionOpen ? (
        <NewSessionDialog
          config={phase.config}
          onCancel={() => setNewSessionOpen(false)}
          onStart={(options) => {
            setNewSessionOpen(false);
            setViewingSessionId(null);
            setShowSettings(false);
            setCenterTab("conversation");
            socket.current?.close();
            void connect(undefined, options);
          }}
        />
      ) : null}

      <StatusBar
        session={session}
        port={phase.config.port}
        onNewSession={() => {
          setCenterTab("conversation");
          void connect();
        }}
      />
    </div>
  );
}

export type { DaemonConfig };
