# NetZoo Agent Desktop UI 架構設計

狀態：設計稿（尚未實作）
決策前提：Tauri v2 桌面殼層 + Agent 維持在 Docker 容器內執行 + v1 涵蓋「對話與計畫審核／推理時間軸／結果檔案檢視／Session 歷史與設定」四塊。

---

## 1. 目標與非目標

### 目標
1. 用桌面原生視窗取代 `./netzoo-chat` 的終端互動，但**行為完全等價**：同一份狀態機、同一份 trace、同一份 session 檔。
2. 把目前只能用文字排版表達的東西（WorkflowPlan、InputEvidence、dry-run 指令預覽、recovery）變成可點選、可編輯的 UI 元件。
3. 讓「推理過程」可被檢視：把 `.netzoo/traces/` 的 hash-chain 事件即時渲染成時間軸。
4. 讓分析結果（TSV / npz / markdown / 網路圖）不必離開視窗就能看。

### 非目標（v1 明確不做）
- 不做多人協作、不做雲端帳號。Observer 的 share 機制維持現狀，不整併進桌面版。
- 不做 workflow 視覺化編輯器（拖拉節點）。Plan 仍由 router/planner 產生，UI 只做審核與修正。
- 不重寫 agent 的決策邏輯。**任何 prompt 文字、routing 規則、contract 語意都不在本案的變更範圍內。**
- 不支援遠端 daemon。v1 只連本機 `127.0.0.1`。

---

## 2. 現況盤點

### 2.1 可直接重用的資產

| 資產 | 位置 | 在桌面版的角色 |
| --- | --- | --- |
| Pydantic contracts | `scripts/netzoo_agent_core/contracts/` | 直接當成前後端的 wire format（見 §7） |
| `LocalTraceStore` / `TraceRecorder` | `trace_store.py`, `tracing.py` | 推理時間軸的唯一事件來源 |
| Observer FastAPI + SSE + dashboard | `scripts/netzoo_observer/` | 事件串流與 auth 的既有範例；`dashboard/app.js` 的事件渲染邏輯可移植 |
| LangGraph 拓樸 | `graph/topology.py` | 10 個節點名稱直接對映時間軸的階段標籤 |
| Docker 映像與 compose | `Dockerfile`, `docker-compose.yml` | daemon 沿用同一個 image，不另外建環境 |
| `workflow_registry.py` | `scripts/` | UI 的 workflow 目錄、必填輸入欄位、參數表單 schema 來源 |

### 2.2 四個必須先解掉的阻擋點

**B1：對話狀態機與終端 I/O 緊耦合。**
`cli/conversation.py`（711 行）的 `run_conversation()` 在同一個 `while True` 裡同時做四件事：算出該問什麼、用 `reader.read()` 讀終端、呼叫 `invoke_graph_turn_func()`、更新 12 個區域變數當狀態。GUI 無法重用，而**複製一份等於分叉狀態機**——這是最大的長期風險。必須先抽出（§4）。

**B2：`EXECUTE_TOOLS` 是行程全域旗標。**
執行授權目前靠 `configure_runtime(EXECUTE_TOOLS=True)` 在單一 turn 前後開關（`cli/conversation.py` 的 `try/finally`）。若 daemon 用單一行程服務多個 session，A session 按下執行時 B session 也會短暫獲得執行權。解法見 §5（一 session 一 worker 行程），**不去動 runtime 的語意**。

**B3：`app.invoke()` 是同步阻塞、無串流。**
`graph/factory.py:143` 只有 `app.invoke(invocation)`，一個 turn 可能跑數十秒到數小時（`NETZOO_TOOL_TIMEOUT_SECONDS` 預設 86400）。UI 的進度必須走 trace 事件旁路，不能等回傳值。

**B4：host 與 container 的路徑不一致。**
容器內 `PROJECT_ROOT` 是 `/work`，host 上是 `/Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent`。原生檔案選擇器回傳 host 路徑，agent 只認容器路徑。需要一層 PathMapper（§8.3）。

---

## 3. 分層架構

```
┌─────────────────────────────────────────────────────────────┐
│  Tauri Shell (Rust)                        netzoo_desktop    │
│  ・視窗／選單／原生檔案對話框／通知                            │
│  ・生命週期：docker compose up → health poll → down          │
│  ・唯一持有 daemon token，透過 IPC 注入 WebView               │
└───────────────┬─────────────────────────────────────────────┘
                │ Tauri IPC (invoke / event)
┌───────────────┴─────────────────────────────────────────────┐
│  WebView UI (React + TypeScript + Vite)                     │
│  ・三欄版面：Sessions │ Conversation │ Inspector             │
│  ・狀態：TanStack Query(快照) + Zustand(串流累積)             │
│  ・型別由 contracts 自動生成（§7）                            │
└───────────────┬─────────────────────────────────────────────┘
                │ WebSocket  ws://127.0.0.1:8765/ws/session/{id}
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌ Docker 邊界 ╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
┌───────────────┴─────────────────────────────────────────────┐
│  Agent Daemon (FastAPI, asyncio)   netzoo_agent_core/server/ │
│  ・SessionSupervisor：每個 session 一個 worker 子行程          │
│  ・TraceFollower：把 worker 的 trace 事件廣播給 WebSocket      │
│  ・REST：sessions / outputs / workflows / settings / policy   │
└───────────────┬─────────────────────────────────────────────┘
                │ multiprocessing Pipe（JSON lines）
┌───────────────┴─────────────────────────────────────────────┐
│  Session Worker (同步 Python，一 session 一行程)              │
│  ・ConversationMachine（§4，CLI 與 GUI 共用）                 │
│  ・BroadcastTraceRecorder → 既有 LocalTraceStore + 廣播       │
│  ・invoke_graph_turn(app, invocation)  ← 完全不改             │
└───────────────┬─────────────────────────────────────────────┘
                │
        既有 LangGraph 10 節點 / workflow_registry / netzoopy
```

CLI 沒有被取代：`./netzoo-chat` 改成掛在同一個 `ConversationMachine` 上的第二個 adapter，兩條路徑共用同一份狀態轉移。

---

## 4. 核心重構：把對話狀態機抽出來

這是整個專案的**前置條件**，不先做這步，後面全部是技術債。

### 4.1 現況的隱性狀態

`run_conversation()` 內目前用區域變數表達的狀態共 12 項：

```
clarification_selections   custom_input_selection      preview_task
preview_workflow           preview_plan                preview_plan_evaluation
execution_confirmation_task  input_confirmation_correction  run_paused
queued_task                next_prompt                 follow_up_context
```
加上 `runtime` 上的 `conversation / pending_plan / active_usage / run_id`。

### 4.2 目標形狀

新增 `scripts/netzoo_agent_core/engine/`：

```python
# engine/state.py
@dataclass
class ConversationState:
    """把 run_conversation 的 12 個區域變數升格為顯式、可序列化的狀態。"""
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
        """目前該向使用者要什麼：prompt 種類、問題文字、可選項、可否執行。"""

    def submit(self, answer: str) -> Iterator[EngineEvent]:
        """吃一個使用者輸入，吐出 0..n 個事件（notice / turn_started /
        turn_finished / plan_updated / finished）。不做任何 print/input。"""
```

`ViewState` 是 UI 與 CLI 共用的「現在畫面該長怎樣」，它**取代目前散在 `clarification_prompt()` / `input_confirmation_prompt()` / `render_next_turn_prompt()` 的字串組裝**——那些函式改成 `ViewState → str` 的純渲染器，GUI 則用 `ViewState → React 元件`。

### 4.3 兩個 adapter

| Adapter | 位置 | 職責 |
| --- | --- | --- |
| CLI | `cli/conversation.py`（瘦身後約 120 行） | `while True: print(render(m.view())); m.submit(read())` |
| GUI worker | `server/session_worker.py` | `for event in m.submit(answer): pipe.send(event)` |

### 4.4 驗收條件（不可協商）

測試套件在任何環境下都**不是全綠的**（`HANDOFF.md` 記載的既有基準是約 93 個失敗），
所以「全部通過」不是可用的標準。實際採用的是**失敗集合相等**：

1. 重構前先錄下失敗測試的完整 node id 清單，重構後必須**逐行相同**——不是數量相同，
   而是同一批測試、同樣的失敗訊息。且不修改任何既有測試的斷言。
2. 兩個環境都要驗：本機 `python -m pytest tests -q`（`HANDOFF.md` 指定的基準環境），
   以及 `netzoo_agent:latest` + pytest 的容器。**兩者的 skip 集合不同**：
   `test_workflow_continuation.py`（最重壓 `run_conversation` 的檔案）在本機因缺
   langchain 而整檔 skip，只有容器會真的跑它。只驗本機等於沒驗到這個迴圈。
3. Golden transcript：固定輸入餵給重構前後的 CLI，**stdout 與傳給 `input_func` 的
   prompt 字串**都要逐字元相同。只比對 stdout 會漏掉大部分 UI 文字，因為提示詞是
   透過 `input_func` 的參數送出的，不是印出來的。
4. `git diff` 中 prompt 字串、routing 邏輯、contract 欄位的變更量為零，用 AST
   抽出字串常數集合對比來證明，不靠肉眼看 diff。

> 為什麼堅持零 prompt 變更：這個專案已經有六次「改 prompt 措辭」的失敗紀錄，routing 的可量測性本來就薄弱。UI 重構必須是純粹的機械式抽取，否則之後任何 routing 指標波動都無法歸因。

---

## 5. Session Worker 程序模型

### 5.1 為什麼是「一 session 一行程」

`runtime.MUTABLE_RUNTIME_NAMES` 共 14 個成員，全部是行程全域值：

```
EXECUTE_TOOLS  TEST_DATA_MODE  TRACE_ENABLED  VERBOSE_OUTPUT  TRANSIENT_TRACE
PRESENTATION_MODE  TRANSIENT_TRACE_MIN_SECONDS  TOOL_TIMEOUT_SECONDS
PROJECT_ROOT  SESSION_ROOT  TOOL_LOG_ROOT  TRACE_ROOT  PROFILE_ROOT  EPISODE_ROOT
```

不只 `EXECUTE_TOOLS`。`TEST_DATA_MODE`（`/test`）同樣是每個 session 各自的使用者狀態，
共用行程會讓一個視窗進入合成測試模式時，另一個視窗的 gene label 驗證也一起放寬。
把這些改成 per-invocation 參數會觸及 graph 的每個節點——風險遠大於多開幾個行程。
**用行程隔離換取零語意變更**是這裡的正確取捨。

### 5.2 分工

| 元件 | 行程 | 同步／非同步 | 責任 |
| --- | --- | --- | --- |
| `SessionSupervisor` | daemon | asyncio | 建立／回收 worker、health、閒置 30 分鐘後回收 |
| `SessionWorker` | 每 session 一個 | 同步 | 持有 `CliRuntime` 與 `ConversationMachine`，跑 `app.invoke()` |
| `WorkerChannel` | 跨行程 | JSON lines over Pipe | 上行事件、下行指令 |
| `TraceFollower` | daemon | asyncio | 把 worker 廣播的 trace 事件轉發到 WebSocket |

### 5.3 執行授權的流向

```
UI 按下「執行」
  → WS: {"type":"approve_execution","run_id":...,"plan_hash":...}
  → daemon 檢查 plan_hash 與 worker 目前的 preview plan 一致
  → worker: configure_runtime(EXECUTE_TOOLS=True) → invoke → finally 關掉
```
`plan_hash` 是必要的：UI 顯示的計畫與 worker 手上的計畫之間隔著網路，使用者有可能對著舊卡片按執行。對不上就拒絕並要求重新預覽。

### 5.4 取消

`app.invoke()` 無法中途取消。v1 的取消 = 對 worker 送 `SIGINT`，沿用既有的 `AgentTurnInterrupted` 路徑（`graph/factory.py:147`），trace 會寫入 `run.interrupted`。UI 顯示「已中止，未完成的步驟不會被回報為完成」——與 CLI 現有訊息一致。

---

## 6. 通訊協定

### 6.1 為什麼是 WebSocket 而非 SSE

Observer 用 SSE 是因為它單向唯讀。桌面版需要雙向（送出回答、核准執行、取消），且需要在同一條連線上維持 turn 的因果順序。

### 6.2 訊息信封

```jsonc
{ "v": 1, "type": "...", "session_id": "...", "seq": 42, "payload": { } }
```
`seq` 由 daemon 單調遞增；UI 重連時帶 `?since=seq` 補齊漏掉的事件（daemon 為每個 session 保留最近 500 筆環形緩衝）。

### 6.3 Client → Server

| type | payload | 對應 CLI 行為 |
| --- | --- | --- |
| `answer` | `{text}` | 所有一般輸入：主提示、clarification、bundle 選擇、slash 指令 |
| `answer`（不回音） | `{text}` | 模式切換：UI 送 `/planning` / `/test`，但不把它當成一句話放進對話串 |
| `approve_execution` | `{plan_hash}` | 執行確認的 `y` |
| `decline_execution` | `{}` | 執行確認的 `n` |
| `cancel` | `{}` | Ctrl-C |
| `ping` | `{}` | 無（daemon 直接回 `pong`，不轉給 worker） |

原設計把 `submit` / `answer_prompt` / `select_bundle` / `slash` 分成四種。實作時合併成
一個 `answer`：狀態機對這四者的處理**本來就是同一個 `submit(text)`**，分開只會讓
daemon 重新推導「現在是哪一種提示」，也就是把 §6.4 明令的「`view` 是唯一真相」破壞掉。
UI 仍然照 `view.prompt_kind` 決定要畫哪種輸入元件。

`approve_execution` 是唯一的例外，而且是刻意的：終端問 `[y/N]` 然後相信下一行輸入，但
UI 離它看到的那份計畫有一個網路來回的距離。所以它必須指名自己核准的是哪一份計畫，
hash 對不上就拒絕。在執行確認提示上送 `answer` 會被拒絕（`ExecutionApprovalRequired`），
兩段確認（先預覽、再核准）在兩個 driver 上都成立。

**WebSocket 的 token 走 subprotocol，不走 query string。** 瀏覽器不能在 WebSocket 上設
Authorization header，而 query string 會被 uvicorn 的 access log 原封不動記下來
（`docker logs` 就讀得到）。`["netzoo.bearer", <token>]` 是 WebSocket 協定為此提供的
機制，不會被記錄。非瀏覽器客戶端仍可用 Authorization header。

**模式是狀態，所以用控制項而非打字。** 終端只能靠 `/planning` / `/test`，那是終端唯一
的手段；在視窗裡打字會把指令留在對話紀錄裡，而且兩則訊息之間看不出目前是什麼模式。
UI 仍然把指令送給 engine（`TEST_DATA_MODE` 與 `EXECUTE_TOOLS` 是 engine 的，視窗不得
自己設），只是不回音；agent 自己那段說明照常進入對話串，因為它帶著「合成結果不是生物
證據」這句警告。

**`view` 多帶三個欄位**：`target_field`、`choosing_bundle`、`preflight_correction`。
計畫本身說不出精靈正在問哪一個輸入——已收集的答案在 machine 裡而不在 plan 上——去解析
提示詞的散文等於再造一個沉默的狀態機。

### 6.4 Server → Client

| type | payload | UI 去處 |
| --- | --- | --- |
| `ready` | `{session_id}` | worker 已啟動 |
| `view` | `{prompt_kind, text, menu_enabled, mode, plan, plan_hash, next_prompt}` | 驅動輸入區的形態（唯一真相） |
| `message` | `{text}` | 對話串（agent 的最終回覆） |
| `notice` | `{text}` | 對話串中的系統訊息 |
| `progress` | `{text}` | 進度列（見下） |
| `trace` | `TraceEvent` | Inspector 的 Timeline 分頁 |
| `turn_started` / `turn_finished` | `{task, execute_once}` / `{}` | 忙碌狀態 |
| `usage` | `LLMUsage` | 底部成本列 |
| `error` | `{error_type, message}` | 錯誤卡片 |
| `stopped` | `{exit_code}` | session 結束 |

`plan` 沒有獨立事件：它跟著 `view` 走。計畫只在「該問使用者什麼」改變時才有新版本，
拆成兩個事件會讓 UI 需要自己對齊兩者的先後。`artifact` 留到 M5 檔案檢視再加。

`progress` 是 §4.4 提到的那個邊界：`_trace` 與 `_clear_transient_trace` 直接寫
stdout，因為終端是它們的原生輸出。worker 行程把自己的 stdout 重導向成 `progress`
事件——**這件事由行程做，不是 driver 做**，因為 `sys.stdout` 是行程層級的，driver
去改會連帶蓋掉同一個直譯器裡的其他輸出。

**原則：`view` 是唯一決定「現在能輸入什麼」的訊息。** UI 不自行推導狀態，避免 GUI 與 CLI 的狀態機漂移。

---

## 7. 型別同步

單一真相是 Pydantic contracts，禁止手寫 TS interface。

```
contracts/*.py  --(pydantic .model_json_schema())-->  schemas/*.json
                --(json-schema-to-typescript)-->      ui/src/generated/contracts.ts
```

- 生成腳本 `scripts/generate_ui_types.py`，輸出進 git（方便 review contract 變更）。
- CI 測試 `tests/test_ui_contract_sync.py`：重新生成後 `git diff --exit-code`，漂移即失敗。
- 需要生成的型別：`WorkflowPlan` `InputEvidence` `InputBundleOption` `WorkflowStep` `NextTurnPrompt` `LLMUsage` `TraceEvent` `FollowUpContext` `ViewState`。

---

## 8. Docker 執行模型

### 8.1 新增 compose service

```yaml
  netzoo-daemon:
    extends: { service: netzoo }        # 沿用同一 image 與全部環境變數
    command: python -m netzoo_agent_core.server --host 0.0.0.0 --port 8765
    ports: ["127.0.0.1:8765:8765"]      # 只綁 loopback
    environment:
      NETZOO_DESKTOP_TOKEN: ${NETZOO_DESKTOP_TOKEN}
```
`netzoo-chat` 的 `ensure_observer_env()` 產生隨機 observer 密鑰的技巧照抄，避免舊 `.env` 擋住啟動。

### 8.2 Tauri 的生命週期

```
啟動  → 產生一次性 NETZOO_DESKTOP_TOKEN（記憶體，不落地）
      → docker compose up -d netzoo-daemon
      → poll GET /health（最多 60s；逾時顯示可操作的錯誤，含 docker 未啟動的判斷）
      → 建立 WebSocket，Authorization: Bearer <token>
關閉  → 對所有 worker 送 graceful shutdown → docker compose stop netzoo-daemon
```
Docker Desktop 未啟動是最常見的失敗，UI 要明確指出而不是顯示「連線失敗」。

### 8.3 PathMapper

```python
class PathMapper:
    """host 絕對路徑 ↔ 容器 /work 路徑的雙向轉換，落在 PROJECT_ROOT 之外一律拒絕。"""
    def to_container(self, host_path: str) -> str: ...
    def to_host(self, container_path: str) -> str: ...
```
- 規則：`<HOST_PROJECT_ROOT>/X` ↔ `/work/X`，其餘拒絕。
- 轉換後仍要過既有的 `path_safety.py`，**PathMapper 不取代任何既有檢查**。
- UI 一律顯示 host 路徑（使用者在 Finder 看得到的那個），送進 agent 前才轉換。
- Tauri 的檔案拖放與原生對話框回傳 host 路徑，是這層的主要入口。

---

## 9. UI 資訊架構

### 9.1 版面

```
┌──────────────┬────────────────────────────────┬──────────────────────┐
│ Sessions     │ Conversation                   │ Inspector            │
│              │                                │                      │
│ ▸ 今天       │  [user] 用 toy 資料跑 PANDA     │ ┌ Plan ─┬ Timeline ┐ │
│   · panda…   │                                │ │ Files │ Cost     │ │
│   · lioness… │  [agent] 訊息…                 │ ├──────────────────┤ │
│ ▸ 本週       │                                │ │ workflow: panda  │ │
│              │  ┌ Plan Card ──────────────┐   │ │ status: needs_…  │ │
│ ─────────    │  │ PANDA · needs_input     │   │ │ evidence 表格    │ │
│ ⚙ 設定       │  │ 缺 motif_path           │   │ │ steps 清單       │ │
│ 📁 outputs   │  │ [選擇檔案] [用 toy 資料] │   │ │                  │ │
│              │  └─────────────────────────┘   │ └──────────────────┘ │
│              │  ┌ 輸入區（由 view 決定形態）┐  │                      │
└──────────────┴────────────────────────────────┴──────────────────────┘
```

### 9.2 輸入區的形態由 `ViewState` 決定

| `NextTurnPrompt.kind` / plan status | 輸入區元件 |
| --- | --- |
| `initial` | 多行自由輸入；模式切換是標頭上的控制項，不是打字 |
| plan `needs_input`（有 bundle options） | Bundle 卡片選擇器 + 「自訂」 |
| plan `needs_input`（逐欄） | 針對 `missing_inputs[0]` 的欄位表單；路徑欄位掛原生檔案選擇器 |
| plan `needs_confirmation` | 輸入清單確認（是／否／改路徑） |
| `dry_run` | 指令預覽（等寬字、可複製）+ 主要按鈕「執行」+ 二次確認 |
| `completed` | 自由輸入 + 後續問題建議 |
| `failed` / `plan_rejected` / `unsupported` | 錯誤卡片 + 重試／換目標 |
| `retrieval` / `clarify_outcome` / `alternative_outcome` | 選項按鈕 + 自由輸入 |

**執行仍維持兩段確認**（預覽 → 明確核准），與 CLI 的 `/execute` + `y/N` 一致。UI 不得提供「一鍵直接執行」的捷徑。

### 9.3 Plan Card 的內容

直接對映 `WorkflowPlan`：`workflow` / `objective` / `status` 當標題列；`evidence` 表格顯示 `field · status · value · reason`，其中 `missing` 的列可直接就地編輯；`steps` 顯示為可展開的指令清單；`memory_notes` 與 `policy_notes` 折疊在底部；`recovery_action` 出現時以警示樣式顯示第幾次重試。

---

## 10. 推理時間軸

### 10.1 事件來源

worker 用 `BroadcastTraceRecorder` 包住既有的 `TraceRecorder`：

```python
class BroadcastTraceRecorder(TraceRecorder):
    """先落地到 LocalTraceStore（hash chain 不變），再推一份到 UI 佇列。"""
    def append(self, run_id, event_type, node, payload, **options):
        event = super().append(run_id, event_type, node, payload, **options)
        self._sink(event)
        return event
```
落地順序不能反過來：**UI 看到的事件必須是已經寫入 hash chain 的事件**，否則時間軸會出現 trace 檔裡不存在的內容。

### 10.2 事件 → 時間軸的映射

| 事件 | 呈現 |
| --- | --- |
| `node.started` / `node.finished` | 主階段列（10 個節點名 → 中文標籤），含 `duration_ms` |
| `routing.*`（約 20 種） | 折疊在 `classify`／`plan` 階段底下的細節列 |
| `plan.created` | 產生一張 Plan 快照，可回看歷史版本 |
| `llm.completed` | 該階段右側的 token 徽章 |
| `tool.started` / `tool.completed` | 執行階段的指令列 + 即時輸出 |
| `memory.retrieved` / `policy.loaded` | 前置階段的次要列 |
| `error.recorded` | 紅色列 + 展開 `error_type` / `message` |
| `run.paused` / `run.resumed` / `run.interrupted` | 時間軸分隔線 |

預設只顯示主階段列，`routing.*` 細節收合——這些事件對除錯 routing 很關鍵，但對一般使用者是雜訊。

---

## 11. 結果與檔案檢視

| 類型 | 檢視器 | 說明 |
| --- | --- | --- |
| `.tsv` / `.csv` | 虛擬滾動表格 | 只讀前 N 行 + 串流分頁；PANDA 輸出動輒數十萬列，禁止全載 |
| `.npz` | 陣列摘要 | 列出 key、shape、dtype、數值摘要，不做完整渲染 |
| `execution-*.md` | Markdown 檢視 | 既有的執行報告格式 |
| 網路邊表 | 圖檢視（可選，v1.5） | 依權重取 top-K 邊，超過門檻只顯示摘要 |
| `manifest.json` | 結構化檢視 | 對應 `outputs/demo/manifest.json` |

檔案樹以 `outputs/` 為根，透過 daemon 的 REST 讀取（不讓 WebView 直接碰檔案系統），路徑一律經 PathMapper + `path_safety`。

---

## 12. 安全模型

1. **綁定範圍**：daemon 只綁 `127.0.0.1:8765`，不對 LAN 開放。
2. **Token**：Tauri 每次啟動產生一次性 bearer token，經環境變數傳給容器，不寫入 `.env`、不出現在日誌。
2b. **跨來源**：視窗是瀏覽器，它的請求是跨來源的——打包後的 Tauri 是
   `tauri://localhost`（Windows 為 `http://tauri.localhost`），Vite dev server 是
   `http://localhost:5173`。daemon 必須對這幾個 origin 開 CORS，否則殼層能透過 IPC
   把容器叫起來，卻連不上它，畫面上看起來就像 daemon 從來沒啟動。
   這不是放寬：綁定仍是 loopback、除 `/health` 外每條路由仍要 bearer token，且
   **刻意不允許 credentials**，避免任何頁面靠環境 cookie 搭便車。WebSocket 不受
   CORS 管轄，但 REST 受，所以兩者都要驗。
3. **API key 隔離**：`OPENROUTER_API_KEY` 只存在於容器環境，WebView 與 Rust 端都拿不到。
4. **Tauri capability**：完全不掛 shell / fs / http plugin。`docker compose` 由 Rust 端用
   `std::process::Command` 執行，只透過具名的 `start_daemon` / `stop_daemon` command
   暴露給 webview——renderer 能要求「啟動 daemon」，但無法指定要跑什麼命令。這比開
   shell plugin 再用白名單過濾更緊。
5. **CSP**：WebView 禁止外部來源；所有資產內嵌。
6. **檔案存取**：UI 不直接讀檔，一律走 daemon REST，重用既有的 `path_safety` 與 trace redaction。
7. **執行授權**：僅 `approve_execution` 能開啟 `EXECUTE_TOOLS`，作用域限單一 turn，且需 `plan_hash` 相符。

---

## 13. 目錄結構

```
netzoo_agent/
├── desktop/                         # 新增：桌面應用
│   ├── src-tauri/
│   │   ├── src/main.rs              # 視窗、選單、docker 生命週期、token
│   │   ├── src/docker.rs            # compose up/health/stop
│   │   └── tauri.conf.json          # capability 白名單、CSP
│   ├── src/                         # React + TS
│   │   ├── app/                     # 版面與路由
│   │   ├── features/
│   │   │   ├── conversation/        # 對話串、輸入區形態機
│   │   │   ├── plan/                # Plan Card、evidence 編輯
│   │   │   ├── timeline/            # trace 事件時間軸
│   │   │   ├── files/               # outputs 瀏覽與檢視器
│   │   │   └── sessions/            # 歷史、resume、設定
│   │   ├── transport/               # WebSocket client、重連、seq 補齊
│   │   └── generated/contracts.ts   # 由 §7 自動生成，勿手改
│   └── package.json
├── scripts/netzoo_agent_core/
│   ├── engine/                      # 新增：共用對話狀態機（§4）
│   │   ├── state.py
│   │   ├── machine.py
│   │   └── view.py
│   ├── server/                      # 新增：daemon
│   │   ├── __main__.py
│   │   ├── app.py                   # FastAPI、WS、REST
│   │   ├── supervisor.py            # SessionSupervisor
│   │   ├── session_worker.py        # worker 行程進入點
│   │   ├── channel.py               # JSON lines over Pipe
│   │   ├── broadcast_recorder.py
│   │   └── path_mapper.py
│   └── cli/conversation.py          # 瘦身為 engine 的 adapter
└── docs/DESKTOP_UI_ARCHITECTURE.md  # 本文件
```

---

## 14. 里程碑

| 里程碑 | 內容 | 驗收 |
| --- | --- | --- |
| **M0 狀態機抽取** ✅ 已完成 | `engine/` 落地，CLI 改為 adapter | 失敗集合在本機（83）與容器（107）皆與重構前逐行相同、13 個 golden transcript 逐字元相同、使用者可見字串零遺失 |
| **M1 Daemon 骨架** ✅ 已完成 | FastAPI + supervisor + worker 行程 + WS | 容器內實跑一輪 planning turn：routing → PANDA → evidence ledger → clarification，`view` 帶完整 plan 與 hash；同一個 prompt 走 CLI 得到相同結果；19 個新測試（含真行程隔離驗證） |
| **M2 Tauri 殼層** ✅ 已完成 | 視窗、docker 生命週期、token、三欄空版面 | 冷啟動 2.7s（門檻 15s）；每次啟動新鑄 token、舊 token 立即失效；Docker 三種失敗各有專屬補救訊息 |
| **M3 對話與計畫審核** ✅ 已完成 | 對話串、輸入區形態機、Plan Card、兩段執行確認、模式切換器 | 原生視窗實跑完整 PANDA toy：提問 → preflight 失敗 → Test 模式 → 修正輸入 → 確認 → Ready 計畫 → 兩段核准 → 寫出 3.1MB 網路；19 個 UI 測試 |
| **M4 推理時間軸** | BroadcastTraceRecorder、時間軸、事件折疊 | 一次 run 的時間軸事件數與 `.netzoo/traces/` 內的筆數一致 |
| **M5 結果與 Session** | 檔案樹、TSV/npz/md 檢視、session 歷史、設定頁、成本列 | 12 個 workflow 的輸出都能在視窗內開啟 |

M0 是硬性前置。M1–M2 可並行。M4 依賴 M1。

---

## 15. 測試策略

| 層級 | 方法 |
| --- | --- |
| engine | 既有 CLI 測試沿用 + golden transcript 對拍 |
| 協定 | contract 快照測試（§7 的 schema drift 檢查） |
| daemon | `httpx` + `pytest-asyncio`，用假 worker 驗證 supervisor 的建立／回收／取消 |
| 行程隔離 | 專門測試：兩個 session 同時進行，A 核准執行時斷言 B 的 `EXECUTE_TOOLS` 仍為 False |
| UI | Vitest（形態機的 `ViewState` → 元件對映）+ Playwright（M3 的完整 PANDA toy 流程） |
| 端到端 | 對照測試：同一組輸入分別走 CLI 與 GUI，比對最終 `WorkflowPlan` 與 trace 事件序列 |

### 15.1 容器測試環境

`netzoo_agent:latest` 沒有裝 pytest，所以容器測試要先疊一層：

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

本機與容器的 skip 集合不同，兩邊都要跑。目前基準：本機 83 失敗 / 容器 107 失敗。

### 15.2 Daemon 冒煙測試

```bash
docker run -d --name netzoo-daemon-smoke \
  -v "$PWD:/work" -w /work -p 127.0.0.1:8765:8765 \
  --env-file .env -e NETZOO_DESKTOP_TOKEN=smoke-token \
  -e PYTHONPATH=/work/scripts:/opt/netZooPy:/opt/netzoo-harness \
  netzoo_agent:test python -m netzoo_agent_core.server --host 0.0.0.0 --port 8765
```

`PYTHONPATH` 必須明寫。映像把 `scripts/` 烘進 `/opt/netzoo-app/scripts` 並放在
預設 `PYTHONPATH`，不覆寫的話跑到的是建置當下那份舊程式碼，不是掛載進來的 `/work`。

### 15.3 桌面殼層

```bash
cd desktop
npm install
npm run tauri dev                    # 開發
npm run tauri build -- --bundles app # 產出 .app
cd src-tauri && cargo test -- --test-threads=1
```

Rust 測試會真的呼叫 `docker`，並用 `DOCKER_HOST` 指向不存在的 socket 來驗證
「Docker Desktop 沒開」這條路徑的錯誤分類與補救訊息。因為要改行程環境變數，必須
單執行緒跑。

---

## 16. 風險與未定案

| 風險 | 影響 | 對策 |
| --- | --- | --- |
| ~~M0 抽取時不慎改動行為~~（已驗證） | — | 失敗集合雙環境逐行相同、golden transcript 逐字元相同、AST 字串集合零遺失 |
| 長時間執行（tool timeout 86400s）跨越視窗關閉 | 使用者以為工作遺失 | worker 為獨立行程可存活；重開後用 `run_id` 重新附著（M5 之後） |
| 大型 TSV 撐爆 WebView | 當機 | 一律串流分頁，daemon 端限制單次回傳列數 |
| ~~Rust 工具鏈缺席~~（已排除） | — | 已確認本機有 `cargo` 1.x、Docker 29.5.3、Xcode CLT，M2 無環境前置阻擋 |
| ~~還有別的行程全域值~~（已盤點） | — | 14 個全部列於 §5.1，全是行程全域；`TEST_DATA_MODE` 與 `EXECUTE_TOOLS` 同樣需要隔離，已用真行程測試驗證 |

**M2 已知限制**
- 打包後的 `.app` 用 `project_root()` 從執行檔往上找 `docker-compose.yml`。放在專案
  目錄內可用；真正安裝到 `/Applications` 後必須設 `NETZOO_PROJECT_ROOT`。要做成可
  安裝的產品，M5 之後得改成把專案路徑存在應用設定裡並提供選擇器。
- 開發模式需要 `devCsp`：Vite 會注入 inline 的 React-refresh preamble 與 HMR
  websocket，兩者都不存在於出貨的 bundle，所以 dev 有自己的一份較寬政策，不去動
  產品實際執行的那份。

**未定案（待 M2 後再決定）**
- 時間軸是否需要「重播」模式（讀舊 run 的 trace 檔逐步播放）。
- Observer 的 share 功能要不要從桌面版一鍵觸發。
- 設定頁能改到多深（模型 allowlist、token 上限是否開放 UI 修改，或維持唯讀顯示 `.env`）。
