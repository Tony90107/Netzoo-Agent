# NetZoo Agent 三層觀測、即時監看與回放系統設計

日期：2026-08-03
狀態：已完成設計討論，待使用者審閱規格

## 1. 背景

NetZoo Agent 已經保存 resumable session、工具 raw log 與 Router／response model 的
token telemetry，但這些資料目前分散在 `.netzoo/sessions/`、`.netzoo/logs/` 與 graph
state。Session 是為了恢復任務而保存的快照，不是完整事件時間線；Planner、Evaluator、
recovery 與狀態轉移也沒有共用的 append-only audit record。因此，目前資料無法可靠回答：

- Agent 從使用者要求到最終結果實際經過哪些步驟？
- 原計畫與實際路徑第一次在哪裡分歧？
- 某個決策依據了哪些可觀測證據？
- 哪一次模型呼叫或工具執行造成主要成本、延遲或失敗？
- 執行中斷或雲端離線後，是否仍能證明紀錄完整？

本設計新增一條統一、可驗證的事件流。即時 Dashboard 與事後回放只讀取這條事件流，
避免維護兩套互相矛盾的紀錄。

## 2. 目標與非目標

### 2.1 目標

1. 自動記錄每趟 NetZoo Agent 任務的可觀測生命週期。
2. 以 L1 任務、L2 決策、L3 工具與證據三層呈現。
3. 執行中可即時觀看，完成後可逐事件回放。
4. 標示原計畫和實際路徑的第一次可觀測分歧，協助定位可能走歪的起點。
5. 依模型呼叫及 graph node 記錄 token、費用、耗時與估算來源。
6. 在 LLM 呼叫前執行可配置的 token／費用預算 gate。
7. 透過可撤銷、可到期的秘密連結，讓老師或團隊唯讀查看。
8. 雲端不可用時仍保留完整本機紀錄，恢復後可冪等補傳。
9. 讓分享頁只接觸已遮蔽且獲授權的資料。

### 2.2 非目標

- 不記錄或推測模型不可見的逐字 chain-of-thought。
- 不允許從 Dashboard 修改事件、計畫或任務結果。
- 第一版不建立帳號、角色群組或 SSO。
- 第一版不錄製影片；回放是事件狀態的重建。
- 不提供任意本機檔案瀏覽或任意外部 URL 抓取。
- 不取代現有 session checkpoint、EpisodeStore 或工具 raw log；它們仍各自負責恢復、
  compact memory 與本機診斷。

## 3. 核心原則

### 3.1 一條事件流，同時支援即時與回放

所有可觀測狀態變化先寫入本機 append-only event stream。即時畫面顯示剛到達的事件；
事後回放按照相同事件的 `sequence` 重建狀態。即時觀看不建立第二套暫存格式。

### 3.2 Local-first durability

事件必須先在本機成功落盤，才能開始下一個 Agent 邊界操作。雲端傳輸位於背景同步器，
因此網路失敗不會使科學工作依賴 Dashboard 的可用性。

### 3.3 可稽核理由，而非隱藏思考

L2 保存結構化欄位：`decision_summary`、`selected_action`、`reason_codes`、
`evidence_refs`、`alternatives_considered` 與 `state_delta`。這些欄位由節點的 typed input、
output 和既有 deterministic evaluation 產生，不要求模型輸出私密推理過程。

### 3.4 分享權與寫入權分離

Agent credential 只能建立 run、追加事件、上傳已授權 blob 及查詢同步確認序號，不能讀取
trace 內容、修改歷史或刪除資料。管理 credential 才能建立或撤銷分享連結。分享 token
只能讀取單一 run 的 sanitized projection。

## 4. 整體架構

系統由六個彼此隔離的單元組成：

1. **TraceRecorder**
   - 位於 NetZoo Python runtime。
   - 驗證 event schema、配置序號、遮蔽秘密、計算 hash 並原子追加本機事件。
   - 對 graph node 暴露小型介面，不包含 HTTP 或 UI 邏輯。

2. **LocalTraceStore**
   - 每個 run 使用 `.netzoo/traces/<run_id>/events.jsonl`。
   - `manifest.json` 保存 schema version、agent identity、同步進度與 final digest。
   - `blobs/` 保存事件無法內嵌的大型 sanitized log 或附件。

3. **TraceSyncWorker**
   - 從最後確認的 `sequence` 批次上傳。
   - 使用 `run_id + sequence` 作為冪等鍵。
   - 指數退避加隨機 jitter；不阻塞 Agent 主流程。

4. **Collector API**
   - FastAPI 服務負責 Agent authentication、schema／大小驗證、序號連續性、hash 驗證、
     budget 設定及 share administration。
   - PostgreSQL 保存 run、event、budget、price snapshot 與 share metadata。
   - S3-compatible object storage 保存大型 sanitized blob。

5. **Live Event Gateway**
   - 以 Server-Sent Events 提供單向即時更新。
   - Client 傳回最後 `sequence`；重連時從下一筆事件補送。

6. **Replay Dashboard**
   - React + TypeScript SPA。
   - 只依 event schema 建立 L1、L2、L3 projection，不依賴 NetZoo Python internals。
   - Prompt、tool output 與 log 一律以純文字呈現。

第一版以 Docker images 交付。共享環境採一台雲端 VM 上的 Docker Compose：Caddy 負責
TLS 與安全 headers，FastAPI、PostgreSQL、MinIO-compatible object storage 與靜態前端
各自使用獨立 service。映像與設定不依賴特定雲端供應商，之後可無資料格式變更地改接
managed PostgreSQL 或 managed S3。

## 5. TraceRecorder 介面與整合點

Recorder 提供三個主要操作：

```python
recorder.start_run(run_context) -> run_id
recorder.append(event_type, payload, *, parent_event_id=None) -> TraceEvent
recorder.finish_run(status, summary) -> RunManifest
```

Graph builder 為每個 node 加入薄 instrumentation wrapper，避免 tracing 散落在業務邏輯。
需要更細資訊的節點可額外發送 domain event。整合點如下：

| NetZoo 邊界 | 主要事件 |
|---|---|
| CLI／session | `run.started`、`run.resumed`、`run.finished` |
| Project policy | `policy.loaded`、`policy.rejected` |
| Memory | `memory.retrieved`、`memory.consolidated` |
| Router | `node.started`、`decision.recorded`、`llm.completed`、`node.finished` |
| Planner | `plan.created`、`input.required` |
| Plan Evaluator | `plan.approved`、`plan.rejected` |
| Executor | `tool.started`、`tool.completed`、`artifact.recorded` |
| Result Evaluator | `evaluation.recorded`、`recovery.selected` |
| Budget | `budget.warning`、`budget.blocked` |
| Failure | `error.recorded`、`run.interrupted` |

現有 `token_usage`、session 與 tool result 仍維持相容；Recorder 消費相同 typed contract，
但事件成為 Dashboard 的 source of truth。

## 6. Event schema

所有事件共用 immutable envelope：

```json
{
  "schema_version": 1,
  "event_id": "uuid",
  "run_id": "uuid",
  "sequence": 17,
  "event_type": "tool.completed",
  "occurred_at": "2026-08-03T08:00:00.000Z",
  "recorded_at": "2026-08-03T08:00:00.012Z",
  "node": "execute_tool",
  "parent_event_id": "uuid-or-null",
  "visibility": "shareable",
  "payload": {},
  "previous_hash": "sha256",
  "event_hash": "sha256"
}
```

規則：

- 排序只依 `sequence`，不依不同主機可能飄移的時間。
- `occurred_at` 表示動作時間，`recorded_at` 表示落盤時間。
- Hash 使用 canonical JSON；計算時排除 `event_hash` 本身。
- `visibility` 只有 `shareable`、`restricted`、`local_only`。
- Share API 僅投影 `shareable` payload；restricted blob 不因擁有 run link 自動開放。
- 單一 JSONL event 有明確大小上限；超過時 payload 改存 blob 並以 digest 參照。
- Schema 不相容時 fail closed，不靜默忽略未知的安全相關欄位。

Run 完成時，manifest 保存最後 sequence、最後 event hash、事件總數、blob digest 清單與
完成狀態。雲端 append API 不提供 update 或 delete-single-event；retention 刪除以整個 run
為單位。

## 7. 三層資訊模型

### 7.1 L1：整趟任務

L1 顯示：

- 使用者目標、workflow、profile、run status。
- 開始／完成時間、wall-clock duration、目前節點。
- 成功、失敗、等待輸入、中斷或預算停止。
- token、實際／估算費用、工具耗時及總耗時。
- 輸出 artifact、validation 結果與分享狀態。
- 全程 timeline；正常、警告、重試、分歧與錯誤使用不同語意標記。

### 7.2 L2：每一步的判斷

L2 以 graph node／decision 為單位顯示：

- 節點收到的安全摘要與引用的 evidence event。
- 選擇、reason code、替代方案及 state delta。
- node duration、LLM call、token 和成本。
- 原計畫與實際動作的差異。

「可能走歪的起點」不是因果判決。系統以 deterministic 規則標記最早符合下列條件的
event，並讓使用者查看之後發生的事件：

1. 實際 action 或安全化 arguments 與 `plan.created` 的對應 step 不一致。
2. 插入未出現在原計畫的 recovery step。
3. Evaluator 首次回傳 retry、replan、rejected 或 failed。
4. Validation 首次產生 error 或高嚴重度 warning。
5. Budget gate 首次 warning 或 blocking。
6. Node 首次超過 timeout 或重試上限。

### 7.3 L3：工具與證據

L3 顯示：

- tool action、allowlist identity、arguments、工作目錄與 execution mode。
- 開始／結束時間、exit status、attempt id、retryability。
- stdout／stderr 安全摘要及完整 sanitized log blob。
- artifact path 的安全顯示值、size、content type、checksum 與 validation。
- error、warning、recovery hint、superseded status。

分享頁不能解除遮罩，也不能下載 restricted 或 local-only blob。

## 8. 即時觀看與回放互動

Dashboard 首次載入先取得截至目前 sequence 的 snapshot projection，再訂閱 SSE。Snapshot
與增量事件都有 sequence boundary，避免載入期間漏接或重複顯示。

回放控制包含：

- 播放、暫停、上一事件、下一事件。
- 0.5x、1x、2x、5x 速度。
- 拖曳 timeline 到指定 sequence。
- 只看異常、分歧、費用、LLM、工具或 artifact。
- 選中事件時顯示當時累計 token、成本、state delta 和相關 log。

L1、L2、L3 是同一頁的 progressive disclosure。由任務總覽展開 node，再展開工具證據，
不讓使用者在三個互不相干的頁面間失去時間位置。桌面使用 timeline + detail inspector；
窄螢幕改為單欄 timeline 與可收合 detail sheet。

視覺延續參考圖的深色底與橘色層級標誌，但背景採低對比深灰、橘色只表示層級與目前
位置；success、warning、error 另使用具語意且符合對比要求的顏色。動畫尊重
`prefers-reduced-motion`。

## 9. Token、費用與預算 gate

### 9.1 計量

每次 LLM call 保存：

- node／role、model、provider request id。
- input、output、cache read／write 與 total tokens（provider 支援時）。
- usage 是 provider actual 或 local estimate。
- provider 回報的 actual cost；若無，保存計算所用的 input／output rate 與 pricing snapshot。
- call duration、timeout、成功或失敗。

歷史費用不能用今天的價格回算。每個估算 call 必須引用呼叫當時的 immutable price
snapshot；沒有可信價格時顯示「尚無法估算」，金額不填零。

### 9.2 第一版預設

- 每任務 hard limit：20,000 tokens。
- 14,000（70%）：yellow warning。
- 17,000（85%）：red warning 並顯示主要耗用節點。
- 保留 1,500 tokens 給安全收尾、停止說明或必要澄清。
- Preflight 使用 `consumed + estimated_prompt + max_output_reservation`；若會越過可用額度，
  不送出 request，追加 `budget.blocked`。
- 進行中的 deterministic 科學工具不因 token gate 被殺掉；完成並記錄後才停止下一個
  LLM-dependent step。

Token limit 與 currency limit 同時存在時採較嚴格者。專案 daily／monthly currency limit
在第一週只發警告。累積至少七天後，以成功任務 P95 token、每日任務量與實際模型價格
產生建議；只有管理者明確套用後才成為 hard limit。

## 10. 分享、安全與隱私

### 10.1 Secret redaction

Recorder 在本機落盤前執行 allowlist-first serialization，再依 key name 與 value pattern
遮蔽 API key、Authorization、cookie、password、private key 和敏感環境變數。Blob 上傳前
再執行一次 scanner。Redaction 產生欄位級 reason code，但不保存被遮蔽原值。

現有 `.netzoo/logs/` 可能包含 Recorder 啟用前的 raw log；SyncWorker 不會直接上傳它，
而是讀取後產生 sanitized copy。若 scanner 無法解析或檔案超過安全上限，blob 維持
`local_only`。

### 10.2 Credential separation

- Agent write key：create run、append event、upload authorized blob。
- Admin key：管理 budget、retention 與 share link；不能作為 Agent runtime key。
- Share token：單一 run sanitized read-only access。

Keys 不進 URL query、事件、application log 或 analytics。

### 10.3 Share link

- 產生至少 256-bit 隨機 token，資料庫只保存 keyed hash。
- Token 放在 URL fragment；SPA 讀取後以 POST 交換短效、限 run 的 HttpOnly session。
- 原始 fragment 隨即從 browser history 可見 URL 移除。
- 預設七天到期，可自訂期限、撤銷及 rotate。
- Share response 使用 `Cache-Control: no-store`、`Referrer-Policy: no-referrer`，頁面設
  `noindex`。
- 依 token／IP 做 rate limit；access audit 不保存完整 share token。

知道有效連結的人都能查看安全版本，這是免帳號分享的明確限制。UI 必須持續顯示到期
時間，管理命令可立即撤銷。

### 10.4 Web 與檔案安全

- 所有 prompt、Markdown、stdout、stderr 與 log 以 escaped plain text 呈現。
- 設置嚴格 Content Security Policy；預覽器使用 sandbox，禁止 script 和 top navigation。
- Blob 只能由 server-side object id 解析，不接受事件中的任意 filesystem path 或 URL。
- API 執行 schema、content type、大小、壓縮比與 rate limit 檢查。
- 使用 TLS；資料庫與 object storage 採 at-rest encryption；高敏感 blob 使用 envelope
  encryption。

### 10.5 Retention

雲端 run 預設保存 90 天。到期或管理者要求刪除時，以整個 run 為範圍刪除 events、blob、
budget projection 與 share token，並保存不含內容的刪除稽核結果。刪除前可匯出含 manifest
與 digest 的 JSONL audit package。本機 trace 依 NetZoo 現有 retention 命令延伸管理。

## 11. 失敗語意與恢復

### 11.1 Recorder preflight

Run 開始前驗證 trace path、permissions、可用空間、schema 與 atomic append。Preflight
失敗時不開始 Agent 工作，CLI 顯示可操作的修復訊息。

### 11.2 本機寫入失敗

本機 durability 是稽核底線。若 append 在步驟間失敗，Agent 不開始下一個 node。正在
執行的 subprocess 可安全完成；runtime 嘗試把 completion 寫入 emergency append file，
然後將 run 標示為 `trace_degraded` 並暫停。不得默默 fail open。

### 11.3 雲端或 SSE 失敗

Cloud failure 不阻塞 Agent。SyncWorker 保存 acknowledged sequence 並重試。Server 對
重複 `run_id + sequence` 回傳既有 digest；若 digest 不同則拒絕並記錄 integrity error。
若收到 sequence gap，server 回報下一個需要的 sequence。

Dashboard 以最後 sequence 重連；無法重連時顯示「畫面暫停更新」，不把最後狀態誤顯示
為任務完成。

### 11.4 Crash／resume

Session resume 沿用原 `run_id`，先驗證本機 hash chain，再追加 `run.resumed`。若 session
存在但 trace 缺失，Agent 要求使用者建立新的 run 或修復 trace，不能假裝舊過程完整。

## 12. API 邊界

第一版 API 僅包含：

- `POST /v1/runs`：以 Agent key 建立 run。
- `POST /v1/runs/{run_id}/events:batch`：連續、冪等 append。
- `POST /v1/runs/{run_id}/blobs`：上傳已授權 sanitized blob。
- `GET /v1/runs/{run_id}/sync-status`：查詢 acknowledged sequence。
- `POST /v1/admin/runs/{run_id}/shares`：建立分享 token。
- `DELETE /v1/admin/shares/{share_id}`：撤銷分享。
- `POST /v1/share/exchange`：fragment token 換短效唯讀 session。
- `GET /v1/share/runs/{run_id}`：取得 L1 snapshot。
- `GET /v1/share/runs/{run_id}/events`：依 sequence 分頁取得 sanitized events。
- `GET /v1/share/runs/{run_id}/stream`：SSE live events。
- `GET /v1/share/blobs/{blob_id}`：只讀取明確 shareable blob。

Admin API 僅供本機管理 CLI 或受保護的管理環境，不暴露在 share UI。

## 13. 測試策略

### 13.1 單元測試

- Event schema、canonical JSON、sequence 與 hash chain。
- Typed payload 到 sanitized projection。
- Secret key／value pattern redaction，並驗證不保存原值。
- Token accumulator、actual／estimated provenance、price snapshot。
- 70%、85%、reserve 與 hard budget preflight。
- 原計畫／實際路徑的 earliest divergence 判定。

### 13.2 整合測試

- NetZoo graph 的 run、policy、router、plan、evaluation、tool、response 事件順序。
- Validation failure、bounded recovery、budget block 與 final status。
- 網路離線、本機 queue、補傳、duplicate batch 與 sequence gap。
- CLI crash／resume 以及 hash chain 驗證。
- Snapshot 與 SSE 訂閱交界不漏事件。
- Share expiry、revoke、rotate 與 restricted blob denial。

### 13.3 安全測試

- Prompt／log 中的 script、HTML、Markdown link 與 control characters。
- Path traversal、object id substitution、超大檔案、zip bomb 與錯誤 content type。
- Agent／admin／share credential 權限互斥。
- URL、access log、application log、event 和 error message 不含 token。
- CSP、security headers、rate limit 與 session cookie attributes。

### 13.4 端對端與視覺測試

使用 deterministic fake LLM usage 加 NetZoo toy workflow 執行成功、失敗、recovery 與
budget stop 四條路徑。確認即時顯示與 reload 後回放一致、L1 加總等於 L2／LLM calls、
earliest divergence 正確且分享頁只能看到 sanitized projection。

視覺測試涵蓋桌面與手機寬度、鍵盤操作、焦點狀態、色彩對比、長 log、空狀態、斷線狀態
及 reduced motion。

## 14. 第一版交付範圍與順序

1. 定義 versioned event contracts、redaction 與 LocalTraceStore。
2. 將 Recorder wrapper 接到現有 graph 與 session resume。
3. 擴充 LLM usage，加入價格來源與 budget preflight events。
4. 建立 Collector API、PostgreSQL schema、blob storage 與 SyncWorker。
5. 建立 L1/L2/L3 Dashboard、SSE 與回放 reducer。
6. 加入 share CLI、fragment exchange、expiry 與 revoke。
7. 完成故障、安全、端對端與視覺驗證。
8. 以 Docker Compose 部署共享環境並執行 toy workflow 驗收。

## 15. 驗收標準

第一版完成時必須同時符合：

1. 每個可觀測 graph node、LLM call、tool attempt、evaluation 與 recovery 都有連續事件。
2. 即時頁面與同一 run 的事後回放產生相同狀態。
3. 原計畫和實際路徑第一次可觀測分歧能被 deterministic 標記並解釋規則。
4. 每個 LLM call 的 token 加總等於 run total，費用標明 actual、estimated 或 unavailable。
5. 預測越過 hard limit 的 request 不會送到 provider，並留下 `budget.blocked`。
6. 雲端中斷不產生事件缺口；恢復後補傳且不重複。
7. 本機 Recorder 失敗時 Agent 不會繼續進入未記錄的新步驟。
8. Share link 只能讀取單一 run 的 sanitized、shareable projection，過期或撤銷後立即失效。
9. API key、share token、cookie 與其他已定義秘密不出現在 trace、blob 或 application log。
10. Toy workflow 的成功、失敗、recovery、resume 和 budget stop 均通過端對端測試。
