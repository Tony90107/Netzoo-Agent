"use strict";

const $ = (selector) => document.querySelector(selector);
const state = {
  runId: null,
  events: [],
  visible: [],
  selectedId: null,
  level: "l1",
  anomaliesOnly: false,
  query: "",
  playing: false,
  speed: 1,
  timer: null,
  source: null,
};

const labels = {
  "run.started": "Run started",
  "run.resumed": "Run resumed",
  "run.paused": "Waiting for more input",
  "run.finished": "Run finished",
  "policy.loaded": "Project rules loaded",
  "memory.retrieved": "Relevant memory retrieved",
  "decision.recorded": "Routing decision recorded",
  "plan.created": "Execution plan created",
  "plan.evaluated": "Execution plan checked",
  "tool.started": "Tool call started",
  "tool.completed": "Tool call completed",
  "tool.failed": "Tool call failed",
  "artifact.validated": "Output files validated",
  "evaluation.recorded": "Result evaluated",
  "recovery.selected": "Recovery path selected",
  "llm.completed": "Model call completed",
  "budget.warning": "Token usage warning",
  "budget.blocked": "Blocked by token limit",
  "node.started": "Node started",
  "node.finished": "Node finished",
  "error.recorded": "Error recorded",
};

function eventTitle(event) {
  return labels[event.event_type] || event.event_type.replaceAll(".", " / ");
}

function formatTime(value, withDate = false) {
  const date = new Date(value);
  if (Number.isNaN(date.valueOf())) return "—";
  return new Intl.DateTimeFormat("en-US", {
    ...(withDate ? { month: "2-digit", day: "2-digit" } : {}),
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).format(date);
}

function formatDuration(milliseconds) {
  if (!Number.isFinite(milliseconds) || milliseconds < 0) return "—";
  if (milliseconds < 1000) return `${milliseconds} ms`;
  const seconds = Math.round(milliseconds / 1000);
  if (seconds < 60) return `${seconds} s`;
  const minutes = Math.floor(seconds / 60);
  return `${minutes} min ${seconds % 60} s`;
}

function number(value) {
  return new Intl.NumberFormat("en-US").format(value || 0);
}

function isAnomaly(event) {
  const type = event.event_type.toLowerCase();
  const payload = event.payload || {};
  return (
    type.includes("error") ||
    type.includes("failed") ||
    type.includes("blocked") ||
    payload.status === "failed" ||
    payload.status === "blocked" ||
    payload.approved === false
  );
}

function eventLevel(event) {
  const type = event.event_type;
  if (type.startsWith("tool.") || type.startsWith("artifact.") || type.startsWith("llm.")) return "L3";
  if (
    type.startsWith("run.") ||
    type.startsWith("decision.") ||
    type.startsWith("plan.") ||
    type.startsWith("evaluation.") ||
    type.startsWith("recovery.")
  ) return "L1";
  return "L2";
}

function belongsToLevel(event, level) {
  const type = event.event_type;
  if (level === "l3") {
    return type.startsWith("tool.") || type.startsWith("artifact.") || type.startsWith("llm.");
  }
  if (level === "l1") {
    return (
      type.startsWith("run.") ||
      type.startsWith("decision.") ||
      type.startsWith("plan.") ||
      type.startsWith("evaluation.") ||
      type.startsWith("recovery.") ||
      isAnomaly(event)
    );
  }
  return true;
}

function payloadSummary(event) {
  const payload = event.payload || {};
  const preferred = [
    payload.reason,
    payload.action,
    payload.workflow,
    payload.tool,
    payload.status,
    payload.model,
    payload.current_step,
    payload.evaluation_status,
  ].find((value) => value !== undefined && value !== null && String(value).trim());
  if (preferred !== undefined) return String(preferred);
  const keys = Object.keys(payload).filter((key) => key !== "redactions").slice(0, 3);
  return keys.length ? keys.join(" · ") : "No extra data";
}

function setConnection(status, label) {
  $("#connection-badge").dataset.state = status;
  $("#connection-label").textContent = label;
}

function showToast(message) {
  const toast = $("#toast");
  toast.textContent = message;
  toast.classList.add("is-visible");
  window.setTimeout(() => toast.classList.remove("is-visible"), 2200);
}

function setEmpty(title, detail, error = false) {
  $("#trace-empty").hidden = false;
  $("#empty-title").textContent = title;
  $("#empty-detail").textContent = detail;
  $("#trace-empty").classList.toggle("is-error", error);
}

function deriveStatus() {
  const lastRunEvent = [...state.events].reverse().find((event) => event.event_type.startsWith("run."));
  if (!lastRunEvent) return "running";
  if (lastRunEvent.event_type === "run.finished") return lastRunEvent.payload?.status || "completed";
  if (lastRunEvent.event_type === "run.paused") return "pending";
  return "running";
}

function updateSummary() {
  const events = state.events;
  if (!events.length) return;
  const first = events[0];
  const last = events[events.length - 1];
  const started = new Date(first.occurred_at).valueOf();
  const ended = new Date(last.occurred_at).valueOf();
  const llmCalls = events.filter((event) => event.event_type === "llm.completed");
  const inputTokens = llmCalls.reduce((sum, event) => sum + Number(event.payload?.input_tokens || 0), 0);
  const outputTokens = llmCalls.reduce((sum, event) => sum + Number(event.payload?.output_tokens || 0), 0);
  const totalTokens = llmCalls.reduce((sum, event) => sum + Number(event.payload?.total_tokens || 0), 0);
  const costCalls = llmCalls.filter((event) => Number.isFinite(Number(event.payload?.cost_micro_usd)));
  const costMicroUsd = costCalls.reduce((sum, event) => sum + Number(event.payload.cost_micro_usd), 0);
  const anomalies = events.filter(isAnomaly);
  const startPayload = first.payload || {};
  const task = startPayload.task || startPayload.workflow || startPayload.profile_id;
  const status = deriveStatus();

  $("#run-short").textContent = String(state.runId).slice(0, 8);
  $("#mission-title").textContent = task ? `Trace: ${task}` : "NetZoo Agent trace";
  $("#mission-subtitle").textContent = `Started ${formatTime(first.occurred_at, true)}. Select an event to inspect the evidence recorded at that point.`;
  $("#run-status").textContent = status.toUpperCase();
  $("#run-status").dataset.status = status;
  $("#integrity-label").textContent = "Server verified event sequence and hash chain";
  $("#metric-tokens").textContent = llmCalls.length ? number(totalTokens) : "—";
  $("#metric-token-detail").textContent = llmCalls.length ? `Input ${number(inputTokens)} · output ${number(outputTokens)}` : "No model usage events yet";
  $("#metric-cost").textContent = costCalls.length ? `$${(costMicroUsd / 1_000_000).toFixed(4)}` : "—";
  $("#metric-cost-detail").textContent = costCalls.length ? `${costCalls.length} with a cost source` : "Not reported by provider or not yet estimated";
  $("#metric-duration").textContent = formatDuration(ended - started);
  $("#metric-event-count").textContent = `${number(events.length)} events`;
  $("#metric-anomalies").textContent = number(anomalies.length);
  $("#metric-anomaly-detail").textContent = anomalies.length ? "Filter and replay them one by one" : "No failed or blocked events";
}

function filteredEvents() {
  const query = state.query.trim().toLocaleLowerCase("en-US");
  return state.events.filter((event) => {
    if (!belongsToLevel(event, state.level)) return false;
    if (state.anomaliesOnly && !isAnomaly(event)) return false;
    if (!query) return true;
    const haystack = `${event.event_type} ${event.node} ${JSON.stringify(event.payload)}`.toLocaleLowerCase("en-US");
    return haystack.includes(query);
  });
}

function createEventNode(event) {
  const item = document.createElement("li");
  item.className = "trace-event";
  item.dataset.eventId = event.event_id;
  item.classList.toggle("is-anomaly", isAnomaly(event));
  item.classList.toggle("is-selected", event.event_id === state.selectedId);

  const button = document.createElement("button");
  button.type = "button";
  button.className = "event-button";
  button.addEventListener("click", () => selectEvent(event.event_id));

  const sequence = document.createElement("span");
  sequence.className = "event-sequence";
  sequence.textContent = `#${String(event.sequence).padStart(3, "0")} · ${formatTime(event.occurred_at)}`;

  const main = document.createElement("span");
  main.className = "event-main";
  const title = document.createElement("b");
  title.textContent = eventTitle(event);
  const detail = document.createElement("small");
  detail.textContent = payloadSummary(event);
  main.append(title, detail);

  const node = document.createElement("span");
  node.className = "event-node";
  node.textContent = event.node;
  button.append(sequence, main, node);
  item.append(button);
  return item;
}

function renderTimeline({ preserveSelection = true } = {}) {
  state.visible = filteredEvents();
  const list = $("#trace-list");
  list.replaceChildren(...state.visible.map(createEventNode));
  $("#visible-count").textContent = `${state.visible.length} / ${state.events.length}`;
  $("#trace-scrubber").max = Math.max(0, state.visible.length - 1);
  $("#trace-empty").hidden = state.visible.length > 0;
  if (!state.visible.length) {
    setEmpty("No matching events", "Switch level, turn off the anomaly filter, or clear the search text.", false);
    clearInspector();
    updatePlaybackPosition();
    return;
  }
  const selectedStillVisible = state.visible.some((event) => event.event_id === state.selectedId);
  if (!preserveSelection || !selectedStillVisible) state.selectedId = state.visible[0].event_id;
  selectEvent(state.selectedId, false);
}

function clearInspector() {
  $("#inspector-title").textContent = "Select an event";
  $("#inspector-time").textContent = "—";
  ["sequence", "node", "level", "visibility", "hash"].forEach((key) => {
    $(`#fact-${key}`).textContent = "—";
  });
  $("#payload-view").textContent = "No event selected";
}

function selectEvent(eventId, scroll = true) {
  const event = state.events.find((candidate) => candidate.event_id === eventId);
  if (!event) return;
  state.selectedId = eventId;
  document.querySelectorAll(".trace-event").forEach((item) => {
    item.classList.toggle("is-selected", item.dataset.eventId === eventId);
  });
  $("#inspector-title").textContent = eventTitle(event);
  $("#inspector-time").textContent = new Date(event.occurred_at).toLocaleString("en-US", { hour12: false });
  $("#fact-sequence").textContent = `#${event.sequence}`;
  $("#fact-node").textContent = event.node;
  $("#fact-level").textContent = eventLevel(event);
  $("#fact-visibility").textContent = event.visibility;
  $("#fact-hash").textContent = `${event.event_hash.slice(0, 10)}…${event.event_hash.slice(-6)}`;
  $("#payload-view").textContent = JSON.stringify(event.payload, null, 2);
  const index = state.visible.findIndex((candidate) => candidate.event_id === eventId);
  if (index >= 0) $("#trace-scrubber").value = index;
  updatePlaybackPosition();
  if (scroll) document.querySelector(`.trace-event[data-event-id="${CSS.escape(eventId)}"]`)?.scrollIntoView({ block: "nearest", behavior: "smooth" });
}

function updatePlaybackPosition() {
  const index = state.visible.findIndex((event) => event.event_id === state.selectedId);
  $("#playback-position").textContent = state.visible.length ? `${Math.max(0, index) + 1} / ${state.visible.length}` : "0 / 0";
}

function stopPlayback() {
  state.playing = false;
  window.clearInterval(state.timer);
  state.timer = null;
  $("#play-toggle").textContent = "▶";
  $("#play-toggle").setAttribute("aria-label", "Play events");
}

function startPlayback() {
  if (!state.visible.length) return;
  stopPlayback();
  state.playing = true;
  $("#play-toggle").textContent = "Ⅱ";
  $("#play-toggle").setAttribute("aria-label", "Pause replay");
  state.timer = window.setInterval(() => {
    const current = state.visible.findIndex((event) => event.event_id === state.selectedId);
    const next = current + 1;
    if (next >= state.visible.length) {
      stopPlayback();
      return;
    }
    selectEvent(state.visible[next].event_id);
  }, 1300 / state.speed);
}

function addEvent(event) {
  if (state.events.some((existing) => existing.event_id === event.event_id)) return;
  state.events.push(event);
  state.events.sort((left, right) => left.sequence - right.sequence);
  updateSummary();
  renderTimeline();
}

async function exchangeFragmentToken(shareId) {
  const fragment = new URLSearchParams(window.location.hash.slice(1));
  const token = fragment.get("token");
  if (!token) return;
  const response = await fetch("/v1/share/exchange", {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ share_id: shareId, token }),
  });
  window.history.replaceState(null, document.title, window.location.pathname);
  if (!response.ok) throw new Error("This viewer link is invalid, expired, or was revoked by an administrator.");
}

async function loadSnapshot() {
  const response = await fetch(`/v1/share/runs/${state.runId}`, { credentials: "same-origin" });
  if (!response.ok) {
    if (response.status === 401) throw new Error("No valid viewer access found. Reopen the full share link, or ask an administrator for a new one.");
    throw new Error(`Failed to load trace data (HTTP ${response.status}).`);
  }
  const snapshot = await response.json();
  state.events = snapshot.events || [];
  updateSummary();
  renderTimeline({ preserveSelection: false });
}

function connectLiveStream() {
  if (state.source) state.source.close();
  state.source = new EventSource(`/v1/share/runs/${state.runId}/events`);
  state.source.addEventListener("open", () => setConnection("live", "Live trace connected"));
  state.source.addEventListener("trace", (message) => {
    try { addEvent(JSON.parse(message.data)); } catch { setConnection("error", "Received an invalid event"); }
  });
  state.source.addEventListener("error", () => setConnection("loading", "Reconnecting"));
}

function bindControls() {
  document.querySelectorAll(".level-tab").forEach((button) => {
    button.addEventListener("click", () => {
      state.level = button.dataset.level;
      document.querySelectorAll(".level-tab").forEach((candidate) => {
        const active = candidate === button;
        candidate.classList.toggle("is-active", active);
        candidate.setAttribute("aria-selected", String(active));
      });
      stopPlayback();
      renderTimeline({ preserveSelection: false });
    });
  });
  $("#trace-search").addEventListener("input", (event) => {
    state.query = event.target.value;
    renderTimeline({ preserveSelection: false });
  });
  $("#anomaly-filter").addEventListener("click", (event) => {
    state.anomaliesOnly = !state.anomaliesOnly;
    event.currentTarget.setAttribute("aria-pressed", String(state.anomaliesOnly));
    renderTimeline({ preserveSelection: false });
  });
  $("#trace-scrubber").addEventListener("input", (event) => {
    const selected = state.visible[Number(event.target.value)];
    if (selected) selectEvent(selected.event_id);
  });
  $("#play-toggle").addEventListener("click", () => state.playing ? stopPlayback() : startPlayback());
  $("#speed-toggle").addEventListener("click", () => {
    state.speed = state.speed === 1 ? 2 : state.speed === 2 ? 4 : 1;
    $("#speed-toggle").textContent = `${state.speed}×`;
    if (state.playing) startPlayback();
  });
  $("#copy-run").addEventListener("click", async () => {
    if (!state.runId) return;
    await navigator.clipboard.writeText(state.runId);
    showToast("Run ID copied");
  });
  $("#copy-payload").addEventListener("click", async () => {
    await navigator.clipboard.writeText($("#payload-view").textContent);
    showToast("Event JSON copied");
  });
}

async function start() {
  bindControls();
  const parts = window.location.pathname.split("/").filter(Boolean);
  const shareId = parts.at(-1);
  try {
    await exchangeFragmentToken(shareId);
    const exchangeRun = await fetch(`/v1/share/resolve/${shareId}`, { credentials: "same-origin" });
    if (!exchangeRun.ok) throw new Error("Could not determine which run this link belongs to.");
    state.runId = (await exchangeRun.json()).run_id;
    await loadSnapshot();
    setConnection("live", "Live trace connected");
    connectLiveStream();
  } catch (error) {
    setConnection("error", "Link unavailable");
    setEmpty("Could not open this trace", error.message || "Viewer access check failed.", true);
    $("#run-status").textContent = "NO ACCESS";
    $("#run-status").dataset.status = "failed";
  }
}

start();
