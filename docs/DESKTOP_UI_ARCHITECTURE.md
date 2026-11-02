# NetZoo Agent Desktop UI Architecture

Status: implemented (milestones M0-M5 below).
Premises: a Tauri v2 desktop shell, the agent keeps running inside its Docker
container, and v1 covers four areas: conversation and plan review, the
reasoning timeline, output file viewing, and session history and settings.

---

## 1. Goals and non-goals

### Goals
1. Replace the terminal interaction of `./netzoo-chat` with a native desktop
   window that **behaves identically**: the same state machine, the same
   traces, the same session files.
2. Turn things that the terminal can only express as formatted text
   (`WorkflowPlan`, `InputEvidence`, dry-run command previews, recovery) into
   clickable, editable UI components.
3. Make the reasoning process inspectable: render the hash-chained events in
   `.netzoo/traces/` as a live timeline.
4. Let users view analysis results (TSV, npz, Markdown, network tables) without
   leaving the window.

### Non-goals (explicitly out of scope for v1)
- No multi-user collaboration and no cloud accounts. The Observer's share
  mechanism stays as it is and is not merged into the desktop app.
- No visual workflow editor (drag-and-drop nodes). Plans are still produced by
  the Router/Planner; the UI only reviews and corrects them.
- No rewrite of the agent's decision logic. **Prompt text, routing rules, and
  contract semantics are all outside the scope of this work.**
- No remote daemon. v1 only connects to local `127.0.0.1`.

---

## 2. Starting point

### 2.1 Reused assets

| Asset | Location | Role in the desktop app |
| --- | --- | --- |
| Pydantic contracts | `scripts/netzoo_agent_core/contracts/` | the wire format between front end and back end (see §7) |
| `LocalTraceStore` / `TraceRecorder` | `trace_store.py`, `tracing.py` | the only event source for the reasoning timeline |
| Observer FastAPI + SSE + dashboard | `scripts/netzoo_observer/` | prior art for event streaming and auth; the event rendering in `dashboard/app.js` was portable |
| LangGraph topology | `graph/topology.py` | the 10 node names map directly to timeline stage labels |
| Docker image and compose | `Dockerfile`, `docker-compose.yml` | the daemon uses the same image; no separate environment |
| `workflow_registry.py` | `scripts/` | source of the UI's workflow catalog, required input fields, and parameter form schema |

### 2.2 Four blockers that had to be removed first

**B1: the conversation state machine was tightly coupled to terminal I/O.**
`run_conversation()` in `cli/conversation.py` (then about 700 lines) did four
things in one `while True` loop: decide what to ask, read the terminal with
`reader.read()`, call `invoke_graph_turn_func()`, and update 12 local variables
that served as state. A GUI could not reuse it, and **copying it would fork the
state machine**, the largest long-term risk. It had to be extracted first (§4).

**B2: `EXECUTE_TOOLS` is a process-global flag.**
Execution authority is granted by toggling `configure_runtime(EXECUTE_TOOLS=True)`
around a single turn (a `try/finally`). If one daemon process served several
sessions, session B would briefly gain execution authority whenever session A
pressed Run. The fix is one worker process per session (§5), **without changing
the runtime's semantics**.

**B3: `app.invoke()` is synchronous and blocking, with no streaming.**
`graph/factory.py` only calls `app.invoke(invocation)`, and a turn can take
anywhere from tens of seconds to hours (`NETZOO_TOOL_TIMEOUT_SECONDS` defaults
to 86400). UI progress must come from a side channel of trace events, not the
return value.

**B4: host and container paths differ.**
Inside the container `PROJECT_ROOT` is `/work`; on the host it is wherever the
repository is checked out. Native file pickers return host paths, while the
agent only understands container paths. A PathMapper layer handles this
(§8.3).

---

## 3. Layered architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Tauri Shell (Rust)                        desktop/src-tauri │
│  - window, menus, native file dialogs, notifications         │
│  - lifecycle: docker compose up -> health poll -> down       │
│  - sole holder of the daemon token, injected into the WebView│
└───────────────┬─────────────────────────────────────────────┘
                │ Tauri IPC (invoke / event)
┌───────────────┴─────────────────────────────────────────────┐
│  WebView UI (React + TypeScript + Vite)                     │
│  - three panes: Sessions | Conversation | Inspector         │
│  - state: TanStack Query (snapshots) + Zustand (streams)    │
│  - types generated from the contracts (§7)                  │
└───────────────┬─────────────────────────────────────────────┘
                │ WebSocket  ws://127.0.0.1:8765/ws/session/{id}
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌ Docker boundary ╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
┌───────────────┴─────────────────────────────────────────────┐
│  Agent Daemon (FastAPI, asyncio)   netzoo_agent_core/server/ │
│  - SessionSupervisor: one worker subprocess per session      │
│  - broadcasts worker trace events to the WebSocket           │
│  - REST: sessions / history / files / outputs / settings     │
└───────────────┬─────────────────────────────────────────────┘
                │ multiprocessing Pipe (JSON lines)
┌───────────────┴─────────────────────────────────────────────┐
│  Session Worker (synchronous Python, one process per session)│
│  - ConversationMachine (§4, shared by CLI and GUI)           │
│  - BroadcastTraceStore -> LocalTraceStore + broadcast        │
│  - invoke_graph_turn(app, invocation)  <- unchanged          │
└───────────────┬─────────────────────────────────────────────┘
                │
        existing 10-node LangGraph / workflow_registry / netZooPy
```

The CLI is not replaced: `./netzoo-chat` is a second adapter on the same
`ConversationMachine`, so both paths share one set of state transitions.

---

## 4. Core refactor: extracting the conversation state machine

This was the **precondition** for everything else; without it, the rest would
have been technical debt.

### 4.1 The implicit state

`run_conversation()` held 12 pieces of state in local variables:

```
clarification_selections   custom_input_selection      preview_task
preview_workflow           preview_plan                preview_plan_evaluation
execution_confirmation_task  input_confirmation_correction  run_paused
queued_task                next_prompt                 follow_up_context
```

plus `conversation / pending_plan / active_usage / run_id` on `runtime`.

### 4.2 Target shape

`scripts/netzoo_agent_core/engine/` (simplified):

```python
# engine/state.py
@dataclass
class ConversationState:
    """The 12 local variables of run_conversation, made explicit and serializable."""
    session_id: str
    profile_id: str
    conversation: list
    pending_plan: WorkflowPlan | None
    next_prompt: NextTurnPrompt
    follow_up_context: FollowUpContext | None
    preview: PreviewState | None          # task/workflow/plan/plan_evaluation
    clarification_selections: dict[str, str]
    custom_input_selection: bool
    input_confirmation_correction: bool
    awaiting_execution_confirmation: bool
    run_id: str | None
    run_paused: bool
    active_usage: dict | None

# engine/machine.py
class ConversationMachine:
    def view(self) -> ViewState:
        """What to ask the user now: prompt kind, question text, options, whether execution is possible."""

    def submit(self, answer: str) -> Iterator[EngineEvent]:
        """Consume one user input and emit 0..n events (notice / turn_started /
        turn_finished / plan_updated / finished). Never prints or reads."""
```

`ViewState` is the shared "what the screen should look like now" for the UI and
the CLI. It **replaces the string assembly that used to be scattered across
`clarification_prompt()`, `input_confirmation_prompt()`, and
`render_next_turn_prompt()`**: those functions became pure `ViewState -> str`
renderers, and the GUI renders `ViewState -> React components`.

### 4.3 Two adapters

| Adapter | Location | Responsibility |
| --- | --- | --- |
| CLI | `cli/conversation.py` (about 120 lines) | `while True: print(render(m.view())); m.submit(read())` |
| GUI worker | `server/session_worker.py` | `for event in m.submit(answer): pipe.send(event)` |

### 4.4 How the extraction was verified

The test suite was not fully green in every environment at the time, so "all
tests pass" was not a usable bar. The criterion was **an identical failure
set**:

1. The full node-id list of failing tests was recorded before the refactor and
   had to be **identical line by line** afterwards: the same tests with the
   same failure messages, not just the same count. No existing assertion was
   changed.
2. Both environments were checked: the local `python -m pytest tests -q` and the
   `netzoo_agent:latest` image with pytest. **Their skip sets differ**:
   `test_workflow_continuation.py`, the file that exercises `run_conversation`
   hardest, is skipped entirely when LangChain is not installed locally, so only
   the container actually runs it.
3. Golden transcripts: fixed inputs were fed to the CLI before and after, and
   **both stdout and the prompt strings passed to `input_func`** had to match
   character for character. Comparing stdout alone would miss most UI text,
   because prompts are passed as `input_func` arguments rather than printed.
4. Zero changes to prompt strings, routing logic, and contract fields in the
   diff, proven by comparing AST-extracted string-constant sets rather than by
   eye.

> Why zero prompt changes: prompt-wording fixes had repeatedly failed in this
> project (a design decision recorded in the research logs), and routing
> measurements are noisy. The UI refactor had to be a purely mechanical
> extraction, or later shifts in routing metrics could not be attributed.

---

## 5. Session worker process model

### 5.1 Why one process per session

`runtime.MUTABLE_RUNTIME_NAMES` has 14 members, all process-global:

```
EXECUTE_TOOLS  TEST_DATA_MODE  TRACE_ENABLED  VERBOSE_OUTPUT  TRANSIENT_TRACE
PRESENTATION_MODE  TRANSIENT_TRACE_MIN_SECONDS  TOOL_TIMEOUT_SECONDS
PROJECT_ROOT  SESSION_ROOT  TOOL_LOG_ROOT  TRACE_ROOT  PROFILE_ROOT  EPISODE_ROOT
```

It is not only `EXECUTE_TOOLS`. `TEST_DATA_MODE` (`/test`) is also per-session
user state; with a shared process, one window entering Synthetic Test mode
would relax gene-label validation in another window too. Turning these into
per-invocation parameters would touch every graph node, a much larger risk than
running a few more processes. **Trading process isolation for zero semantic
change** is the right call here.

### 5.2 Division of work

| Component | Process | Sync/async | Responsibility |
| --- | --- | --- | --- |
| `SessionSupervisor` | daemon | asyncio | create and reap workers, health, reap after 30 idle minutes |
| `SessionWorker` | one per session | synchronous | holds `CliRuntime` and `ConversationMachine`, runs `app.invoke()` |
| `Channel` | cross-process | JSON lines over a Pipe | upstream events, downstream commands |
| broadcast relay | daemon | asyncio | forwards the worker's broadcast trace events to the WebSocket |

### 5.3 Flow of execution authority

```
User presses "Run" in the UI
  -> WS: {"type":"approve_execution","plan_hash":...}
  -> daemon checks plan_hash against the worker's current preview plan
  -> worker: configure_runtime(EXECUTE_TOOLS=True) -> invoke -> reset in finally
```

`plan_hash` is required: the plan shown in the UI and the plan held by the
worker are separated by a network hop, and the user might press Run on a stale
card. On a mismatch the approval is refused and a new preview is required.

### 5.4 Cancellation

`app.invoke()` cannot be cancelled midway. In v1, cancel means sending `SIGINT`
to the worker, reusing the existing `AgentTurnInterrupted` path in
`graph/factory.py`; the trace records `run.interrupted`. The UI says the run was
stopped and that unfinished steps are not reported as completed, matching the
CLI's existing message.

---

## 6. Protocol

### 6.1 Why WebSocket rather than SSE

The Observer uses SSE because it is one-way and read-only. The desktop app needs
two-way traffic (sending answers, approving execution, cancelling) and needs to
keep each turn's causal order on a single connection.

### 6.2 Envelope

```jsonc
{ "v": 1, "type": "...", "session_id": "...", "seq": 42, "payload": { } }
```

`seq` increases monotonically per daemon. On reconnect, the UI passes
`?since=seq` to receive the events it missed (the daemon keeps a 500-event ring
buffer per session).

### 6.3 Client -> server

| type | payload | Equivalent CLI behavior |
| --- | --- | --- |
| `answer` | `{text}` | every ordinary input: main prompt, clarification, bundle choice, slash command |
| `answer` (not echoed) | `{text}` | mode switch: the UI sends `/planning` or `/test` but does not add it to the conversation |
| `approve_execution` | `{plan_hash}` | `y` at the execution confirmation |
| `decline_execution` | `{}` | `n` at the execution confirmation |
| `cancel` | `{}` | Ctrl-C |
| `ping` | `{}` | none (the daemon answers `pong` itself without forwarding to the worker) |

An earlier design split `submit`, `answer_prompt`, `select_bundle`, and `slash`
into four types. The implementation merged them into one `answer`: the state
machine **already handles all four with the same `submit(text)`**, and
splitting them would force the daemon to re-derive "what kind of prompt is
this", breaking the rule in §6.4 that `view` is the single source of truth. The
UI still uses `view.prompt_kind` to decide which input component to draw.

`approve_execution` is the one deliberate exception. The terminal asks `[y/N]`
and trusts the next line, but the UI is one network round trip away from the
plan it shows. So the approval must name the plan it approves, and is refused if
the hash does not match. Sending `answer` at the execution confirmation prompt
is rejected (`ExecutionApprovalRequired`), so the two-step confirmation (preview
first, then approve) holds for both drivers.

**The WebSocket token travels in a subprotocol, not the query string.**
Browsers cannot set an Authorization header on a WebSocket, and query strings
are logged verbatim in uvicorn's access log (readable through `docker logs`).
`["netzoo.bearer", <token>]` is the WebSocket mechanism intended for this and is
not logged. Non-browser clients may still use the Authorization header.

**Mode is state, so it is a control, not typed text.** In the terminal,
`/planning` and `/test` are the only means available; typing them in a window
would leave commands in the conversation and make the current mode invisible
between messages. The UI still sends the command to the engine
(`TEST_DATA_MODE` and `EXECUTE_TOOLS` belong to the engine; the window must not
set them), just without echoing it. The agent's own explanation still enters the
conversation, because it carries the warning that synthetic results are not
biological evidence.

**`view` carries three extra fields**: `target_field`, `choosing_bundle`, and
`preflight_correction`. The plan alone cannot say which input the wizard is
asking for (collected answers live in the machine, not on the plan), and
parsing the prompt prose would rebuild a silent second state machine.

### 6.4 Server -> client

| type | payload | Where it goes in the UI |
| --- | --- | --- |
| `ready` | `{session_id}` | worker has started |
| `view` | `{prompt_kind, text, menu_enabled, mode, plan, plan_hash, next_prompt}` | drives the shape of the input area (single source of truth) |
| `message` | `{text}` | conversation (the agent's final reply) |
| `notice` | `{text}` | system message in the conversation |
| `progress` | `{text}` | progress line (see below) |
| `trace` | `TraceEvent` | the Inspector's Timeline tab |
| `turn_started` / `turn_finished` | `{task, execute_once}` / `{}` | busy state |
| `usage` | `LLMUsage` | cost bar at the bottom |
| `error` | `{error_type, message}` | error card |
| `stopped` | `{exit_code}` | session ended |

`plan` has no event of its own; it travels with `view`. A plan only gets a new
version when "what to ask the user" changes, and splitting it into two events
would force the UI to reconcile their order.

`progress` is the boundary mentioned in §4.4: `_trace` and
`_clear_transient_trace` write straight to stdout, because the terminal is
their native output. The worker process redirects its own stdout into
`progress` events. **The process does this, not the driver**, because
`sys.stdout` is process-wide and a driver replacing it would also capture any
other output in the same interpreter.

**Rule: `view` is the only message that decides what can be entered now.** The
UI never derives state on its own, so the GUI and CLI state machines cannot
drift apart.

---

## 7. Type synchronization

The single source of truth is the Pydantic contracts; hand-written TypeScript
interfaces are not allowed.

```
contracts/*.py  --(walk the Pydantic models)-->  desktop/src/generated/contracts.ts
```

- The generator is `scripts/generate_ui_types.py`; its output
  `desktop/src/generated/contracts.ts` is committed, so contract changes are
  visible in review.
- `tests/test_ui_contract_sync.py` regenerates and compares; any drift fails the
  test (adding a field to a contract makes it fail).
- **It walks the Pydantic models, not the JSON Schema.** `RequestedOutcome` has a
  `__get_pydantic_json_schema__` hook that expands into one conditional branch
  per artifact type; that is right for guiding a model and disastrous for
  generating interfaces.
- The generator **raises instead of guessing** when a type cannot be expressed
  honestly. Unparameterized `dict` (`decision`, `arguments`, a trace's
  `payload`) maps to `Record<string, unknown>`.
- Generated types include `WorkflowPlan`, `InputEvidence`, `InputBundleOption`,
  `WorkflowStep`, `NextTurnPrompt`, `LLMUsage`, `TraceEvent`,
  `FollowUpContext`, and `ViewState`.

---

## 8. Docker execution model

### 8.1 Compose service

`docker-compose.yml` defines `netzoo-daemon`, which extends the `netzoo`
service (same image and environment), binds only to loopback
(`127.0.0.1:${NETZOO_DAEMON_PORT:-8765}:8765`), and runs
`python -m netzoo_agent_core.server --host 0.0.0.0 --port 8765`. It receives
`NETZOO_DESKTOP_TOKEN` and `NETZOO_HOST_PROJECT_ROOT` from the shell and sets
`PYTHONPATH` so the mounted working tree, not the code baked into the image, is
what runs. `netzoo-chat`'s `ensure_observer_env()` trick of generating a random
Observer secret is reused, so an old `.env` does not block startup.

### 8.2 Tauri lifecycle

```
start -> mint a one-time NETZOO_DESKTOP_TOKEN (in memory, never written to disk)
      -> docker compose up -d netzoo-daemon
      -> poll GET /health (up to 60 s; on timeout show an actionable error,
         including detection of Docker not running)
      -> open the WebSocket with the bearer token
close -> graceful shutdown of all workers -> docker compose stop netzoo-daemon
```

Docker Desktop not running is the most common failure; the UI must say so
explicitly rather than show "connection failed".

### 8.3 PathMapper

```python
class PathMapper:
    """Two-way mapping between host absolute paths and container /work paths; anything outside PROJECT_ROOT is rejected."""
    def to_container(self, host_path: str) -> str: ...
    def to_host(self, container_path: str) -> str: ...
```

- Rule: `<HOST_PROJECT_ROOT>/X` <-> `/work/X`; everything else is rejected.
- Mapped paths still go through the existing `path_safety.py`. **PathMapper
  replaces no existing check.**
- The UI always shows host paths (the ones the user can find in Finder) and
  converts them only before sending to the agent.
- Tauri file drag-and-drop and native dialogs return host paths and are the
  main entry points to this layer.

### 8.4 Browser build (`netzoo-web`)

The same front end also runs as a plain web page, so the app needs nothing on
the host but Docker:

- The `web-ui` stage of the `Dockerfile` runs `npm run build` in `desktop/`
  and copies `dist/` to `/opt/netzoo-web` in the image.
- The `netzoo-web` compose service is the daemon with `NETZOO_WEB_UI_DIR` set.
  `create_app` then mounts that directory at `/`, after every API route. The
  page is same-origin, so it needs no CORS entry, and every `/v1` and `/ws`
  route still requires the bearer token. The service publishes
  `127.0.0.1:${NETZOO_WEB_PORT:-8080}`, so it never collides with the desktop
  app's daemon.
- `./netzoo-web` mints a token for each launch, starts the service and opens
  `http://localhost:<port>/#token=<token>`. `transport/daemon.ts` moves the
  fragment into localStorage and clears it from the address bar. The fragment
  is never sent to the server, so it does not appear in access logs. A token
  that the daemon rejects is forgotten, and the page asks for a fresh link.
- Host-only features fall back in the browser: the host Docker check shows as
  unknown, log export becomes a browser download, and external links open
  normally.

---

## 9. UI information architecture

### 9.1 Layout

```
┌──────────────┬────────────────────────────────┬──────────────────────┐
│ Sessions     │ Conversation                   │ Inspector            │
│              │                                │                      │
│ > Today      │  [user] Run PANDA on toy data  │ ┌ Plan ─┬ Timeline ┐ │
│   - panda…   │                                │ │ Files │ Cost     │ │
│   - lioness… │  [agent] message…              │ ├──────────────────┤ │
│ > This week  │                                │ │ workflow: panda  │ │
│              │  ┌ Plan Card ──────────────┐   │ │ status: needs_…  │ │
│ ─────────    │  │ PANDA · needs_input     │   │ │ evidence table   │ │
│ Settings     │  │ missing motif_path      │   │ │ steps list       │ │
│ outputs      │  │ [Choose file] [Toy data]│   │ │                  │ │
│              │  └─────────────────────────┘   │ └──────────────────┘ │
│              │  ┌ Input area (shape set by view) ┐                   │
└──────────────┴────────────────────────────────┴──────────────────────┘
```

### 9.2 The input area's shape is decided by `ViewState`

| `NextTurnPrompt.kind` / plan status | Input component |
| --- | --- |
| `initial` | multi-line free text; mode switching is a header control, not typed |
| plan `needs_input` (with bundle options) | bundle card picker + "Custom" |
| plan `needs_input` (field by field) | a form for `missing_inputs[0]`; path fields use the native file picker |
| plan `needs_confirmation` | input-list confirmation (yes / no / change path) |
| `dry_run` | command preview (monospace, copyable) + primary "Run" button + second confirmation |
| `completed` | free text + suggested follow-up questions |
| `failed` / `plan_rejected` / `unsupported` | error card + retry / change goal |
| `retrieval` / `clarify_outcome` / `alternative_outcome` | option buttons + free text |

**Execution keeps the two-step confirmation** (preview, then explicit
approval), matching the CLI's `/execute` + `y/N`. The UI must never offer a
one-click "run now" shortcut.

### 9.3 Plan Card contents

It maps directly to `WorkflowPlan`: `workflow`, `objective`, and `status` form
the title bar; the `evidence` table shows `field · status · value · reason`,
with `missing` rows editable in place; `steps` is an expandable command list;
`memory_notes` and `policy_notes` are collapsed at the bottom; when
`recovery_action` is present it is shown as a warning with the retry number.

---

## 10. Reasoning timeline

### 10.1 Event source

The worker wraps `LocalTraceStore` in a `BroadcastTraceStore`
(`server/broadcast_recorder.py`):

```python
class BroadcastTraceStore(LocalTraceStore):
    def append(self, *args, **kwargs):
        event = super().append(*args, **kwargs)   # persist to the hash chain first
        self._sink(event.model_dump(mode="json")) # then push to the UI
        return event
```

The order cannot be reversed: **every event the UI shows must already be in the
hash chain**, or the timeline could show content that does not exist in the
trace file.

**Wrap the store, not the recorder.** The first version wrapped
`TraceRecorder`, but `pause_run` and `finish_run` call the store's `append`
directly and bypass the recorder, so a paused run reached the window with one
fewer `run.paused` event than its own trace file. The event-count acceptance
check caught this, and `tests/test_broadcast_covers_the_chain.py` pins it.

### 10.2 Events to timeline

| Event | Presentation |
| --- | --- |
| `node.started` / `node.finished` | main stage rows (the 10 node names mapped to readable labels), with `duration_ms` |
| `routing.*` (about 20 kinds) | detail rows collapsed under the `classify` / `plan` stages |
| `plan.created` | a Plan snapshot; earlier versions can be reviewed |
| `llm.completed` | a token badge to the right of the stage |
| `tool.started` / `tool.completed` | command row of the execution stage + live output |
| `memory.retrieved` / `policy.loaded` | secondary rows of the setup stages |
| `error.recorded` | red row, expandable to `error_type` / `message` |
| `run.paused` / `run.resumed` / `run.interrupted` | timeline separators |

By default only the main stage rows are shown and `routing.*` details are
collapsed: they matter for debugging routing but are noise for most users.

---

## 11. Results and file viewing

| Type | Viewer | Notes |
| --- | --- | --- |
| `.tsv` / `.csv` | virtualized table | reads only the first N rows + streamed paging; PANDA outputs can have hundreds of thousands of rows, so never load everything |
| `.npz` | array summary | lists keys, shapes, dtypes, and numeric summaries; no full rendering |
| `execution-*.md` | Markdown viewer | the existing execution report format |
| `manifest.json` | structured view | matches `outputs/demo/manifest.json` |
| network edge table | graph view (optional, v1.5) | top-K edges by weight; above a threshold only a summary is shown |

Implementation notes:
- The pane is called **Outputs**, not Files: "Files" does not say these are
  results the agent produced. The path bar **appears only once you navigate
  into a folder** (at the root it would just repeat the pane title), and every
  segment is clickable, so no `..` row is needed.
- **Every divider is draggable**; sizes are kept in localStorage and survive a
  restart. Each pane has a minimum size, and dragging past it stops: a pane
  dragged to zero width would lose its handle and could never be dragged back.
  Dividers have `role="separator"` and respond to arrow keys; a layout that
  only a mouse can change is, for some people, a layout they cannot change.
- A sidebar session opens as a **read-only conversation**
  (`GET /v1/history/{id}`). Viewing history never touches the live session;
  the socket lives above the view. Resume is offered only when the agent is
  waiting on a question; otherwise the UI says nothing is waiting, instead of
  showing a button that would fail. `save_session` compacts long
  conversations, so the view labels what it shows as the part the agent kept
  rather than presenting trimmed history as complete.
- A session id must be a bare id: anything containing a separator is not a
  session and is rejected before it can refer to a path.
- The file tree only serves `outputs/`; paths are always resolved through the
  file system, so a symlink pointing outside the tree is caught rather than
  trusted by name, and any escape returns 403 instead of being clamped to the
  root.
- `.npz` shapes are read from the archive header; **no array is loaded**.
- Some NetZoo outputs have a space-separated header but tab-separated data rows,
  which would read as a single cell. The viewer re-splits the header only when
  the re-split column count exactly matches the data rows; otherwise it shows
  the header as-is rather than guessing to make the table look nice.

The file tree is rooted at `outputs/` and read through the daemon's REST API
(the WebView never touches the file system); paths always go through
PathMapper and `path_safety`.

---

## 12. Security model

1. **Binding**: the daemon binds only to `127.0.0.1:8765` and is not exposed to
   the LAN.
2. **Token**: Tauri mints a one-time bearer token at every launch and passes it
   to the container through an environment variable; it is never written to
   `.env` and never appears in logs.
3. **Cross-origin**: the window is a browser, so its requests are cross-origin.
   The packaged Tauri app is `tauri://localhost` (`http://tauri.localhost` on
   Windows) and the Vite dev server is `http://localhost:5173`. The daemon must
   allow CORS for these origins, or the shell could start the container over
   IPC but never reach it, which looks exactly like a daemon that never
   started. This is not a relaxation: the binding is still loopback, every
   route except `/health` still requires the bearer token, and **credentials
   are deliberately not allowed**, so no page can ride on ambient cookies.
   WebSockets are not subject to CORS but REST is, so both are checked.
4. **API key isolation**: `OPENROUTER_API_KEY` exists only in the container
   environment; neither the WebView nor the Rust side can read it.
5. **Tauri capabilities**: no shell, fs, or http plugin is loaded. Rust runs
   `docker compose` with `std::process::Command` and exposes it to the webview
   only through the named `start_daemon` / `stop_daemon` commands; the renderer
   can ask to start the daemon but cannot choose what command runs. This is
   tighter than enabling the shell plugin and filtering with an allowlist.
6. **CSP**: the WebView forbids external sources; all assets are bundled.
7. **File access**: the UI never reads files directly; everything goes through
   the daemon's REST API, reusing the existing `path_safety` and trace
   redaction.
8. **Execution authority**: only `approve_execution` can turn on
   `EXECUTE_TOOLS`; its scope is a single turn and it requires a matching
   `plan_hash`.

---

## 13. Directory layout

```
.
├── desktop/                         # desktop application
│   ├── src-tauri/
│   │   ├── src/main.rs              # entry point
│   │   ├── src/lib.rs               # window, menus, start_daemon/stop_daemon, token
│   │   ├── src/docker.rs            # compose up / health / stop, failure classification
│   │   └── tauri.conf.json          # capability allowlist, CSP
│   ├── src/                         # React + TS
│   │   ├── app/                     # layout, splitters, startup
│   │   ├── features/
│   │   │   ├── conversation/        # conversation, input-area state machine
│   │   │   ├── plan/                # Plan Card, evidence editing
│   │   │   ├── timeline/            # trace event timeline
│   │   │   ├── files/               # outputs browser and viewers
│   │   │   ├── sessions/            # history, resume, settings
│   │   │   └── help/                # in-app help
│   │   ├── transport/               # WebSocket client, reconnect, seq catch-up
│   │   └── generated/contracts.ts   # generated per §7; do not edit by hand
│   └── package.json
├── scripts/netzoo_agent_core/
│   ├── engine/                      # shared conversation state machine (§4)
│   │   ├── state.py
│   │   ├── machine.py
│   │   └── view.py
│   ├── server/                      # daemon
│   │   ├── __main__.py
│   │   ├── app.py                   # FastAPI, WebSocket, REST
│   │   ├── supervisor.py            # SessionSupervisor
│   │   ├── session_worker.py        # worker process entry point
│   │   ├── channel.py               # JSON lines over a Pipe
│   │   ├── protocol.py              # envelope, message types, plan_hash
│   │   ├── broadcast_recorder.py
│   │   └── path_mapper.py
│   └── cli/conversation.py          # thin adapter over the engine
└── docs/DESKTOP_UI_ARCHITECTURE.md  # this document
```

---

## 14. Milestones

| Milestone | Scope | Acceptance |
| --- | --- | --- |
| **M0 state machine extraction** (done) | `engine/` in place, CLI turned into an adapter | identical failure sets locally and in the container, golden transcripts identical character for character, no user-visible string lost |
| **M1 daemon skeleton** (done) | FastAPI + supervisor + worker processes + WebSocket | a real planning turn in the container (routing -> PANDA -> evidence ledger -> clarification) with the full plan and hash in `view`; the same prompt through the CLI gives the same result; real process-isolation tests |
| **M2 Tauri shell** (done) | window, Docker lifecycle, token, empty three-pane layout | a fresh token at every launch with the old one invalidated immediately; a dedicated remedy message for each of the three Docker failure modes |
| **M3 conversation and plan review** (done) | conversation, input-area state machine, Plan Card, two-step execution confirmation, mode switcher | a full PANDA toy run in the native window: question -> preflight failure -> Test mode -> corrected input -> confirmation -> ready plan -> two-step approval -> network written |
| **M4 reasoning timeline** (done) | event broadcast, stage timeline, collapsed details, contract type generation | UI event count equals trace-file event count; broadcast-coverage and type-drift tests |
| **M5 results and sessions** (done) | PathMapper, outputs tree, TSV/npz/Markdown viewers, session history and resume, read-only settings page, cost bar | streamed paging of a multi-MB network, npz header-only reads, resume restores a paused PANDA plan |

M0 was a hard prerequisite. M1 and M2 could run in parallel. M4 depended on M1.

---

## 15. Testing strategy

| Layer | Method |
| --- | --- |
| engine | existing CLI tests + golden-transcript comparison |
| protocol | contract snapshot test (the schema-drift check in §7) |
| daemon | `httpx` + `pytest-asyncio`, with a fake worker to check supervisor create/reap/cancel |
| process isolation | dedicated test: two concurrent sessions; when A approves execution, assert that B's `EXECUTE_TOOLS` is still False |
| UI | Vitest (`ViewState` -> component mapping) + Playwright (the full PANDA toy flow from M3) |
| end to end | comparison test: the same inputs through the CLI and the GUI, comparing the final `WorkflowPlan` and trace event sequence |

### 15.1 Container test environment

`netzoo_agent:latest` does not include pytest, so container tests add a layer
(`Dockerfile.test`):

```
FROM netzoo_agent:latest
USER root
RUN micromamba run -n netzoo python -m pip install --no-cache-dir "pytest>=8,<9" pytest-asyncio
USER $MAMBA_USER
```

```bash
docker build -t netzoo_agent:test -f Dockerfile.test .
docker run --rm -v "$PWD:/work" -w /work netzoo_agent:test python -m pytest tests -q
```

The local and container skip sets differ, so run both.

### 15.2 Daemon smoke test

```bash
docker run -d --name netzoo-daemon-smoke \
  -v "$PWD:/work" -w /work -p 127.0.0.1:8765:8765 \
  --env-file .env -e NETZOO_DESKTOP_TOKEN=smoke-token \
  -e PYTHONPATH=/work/scripts:/opt/netZooPy:/opt/netzoo-harness \
  netzoo_agent:test python -m netzoo_agent_core.server --host 0.0.0.0 --port 8765
```

`PYTHONPATH` must be set explicitly. The image bakes `scripts/` into
`/opt/netzoo-app/scripts` and puts it on the default `PYTHONPATH`; without the
override you would run the code from the last image build, not the mounted
`/work`.

### 15.3 Desktop shell

```bash
cd desktop
npm install
npm run tauri dev                    # development
npm run tauri build -- --bundles app # build the .app
cd src-tauri && cargo test -- --test-threads=1
```

The Rust tests really invoke `docker` and point `DOCKER_HOST` at a nonexistent
socket to check the error classification and remedy message for "Docker Desktop
is not running". They change process environment variables, so they must run
single-threaded.

---

## 16. Risks and open questions

| Risk | Impact | Mitigation |
| --- | --- | --- |
| A long run (tool timeout 86400 s) outlives the window | the user thinks the work is lost | the worker is an independent process and survives; reattaching to a running turn by `run_id` after reopening is not implemented yet |
| A large TSV overwhelms the WebView | crash | always stream with paging; the daemon caps rows per response |
| Other process-global values | cross-session leakage | all 14 are listed in §5.1; `TEST_DATA_MODE` and `EXECUTE_TOOLS` both need isolation, verified with real-process tests |

**Known limitations of the shell**
- The packaged `.app` uses `project_root()` to walk up from the executable to
  find `docker-compose.yml`. This works when the app lives inside the project
  directory; when installed to `/Applications` you must set
  `NETZOO_PROJECT_ROOT`. An installable product would need to store the project
  path in app settings and provide a picker.
- Development mode needs `devCsp`: Vite injects an inline React-refresh preamble
  and an HMR WebSocket, neither of which exists in the shipped bundle, so dev
  has its own looser policy and the production policy stays untouched.

**Decided**
- **The settings page is read-only.** The model allowlist and token caps are
  exactly the limits that stop a misdirected request from hitting an expensive
  model; a window that can change them is a window that can remove them. The
  settings page reports effective values (including the project root on both
  the container and host sides) and reports only whether `OPENROUTER_API_KEY`
  is present; the key never leaves the daemon. To change settings, change the
  container's environment at launch.

**Still open**
- Whether the timeline needs a "replay" mode (stepping through an old run's
  trace file).
- Whether the Observer's share feature should be triggerable from the desktop
  app.
