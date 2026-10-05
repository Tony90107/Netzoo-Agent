# 第 1 項：分離「工具適合」與「使用者允許執行」

日期：2026-10-05
對應：`docs/diagnostics/2026-10-03-routing-execution/report.zh-TW.md` 的 F1、F2、F7；F3 只有部分緩解。
範圍：只改確定性程式（deterministic code），沒有改任何模型看得到的 prompt 或 schema，也沒有呼叫付費模型。

## 結論

「哪個工具適合」與「使用者是否要求現在做」現在是兩份分開的紀錄：

- 工具適合：沿用 registry 匹配的 `matched_actions`、`recommended_actions`、`candidate_actions`，這次完全沒有改動。
- 操作授權：新增程式自有的 `TaskDecision.operation_authorization`（`OperationAuthorization`）。內容是請求要求了哪些操作、禁止了哪些操作（附原文引用）、是否為「只解釋」、是否要求預覽，以及被拒絕的操作。

原本會把請求「提升」成操作的確定性規則，現在只讀「能授權的文字」。具體來說，下列文字不能授權：

- 否定句（「不要搜尋」、"do not inspect"）
- 引號內的文字
- 轉述他人的話（「老師說…」、"my advisor told me to…"）
- 過去式描述（「上個月已經跑完」）
- 只解釋（「只要解釋」、"explain only"、"guidance only"）

禁止條款則成為否決（veto）：不論是模型、確定性規則、fallback 或 continuation 提出的執行，都會被拒絕。否決只會移除權限，不會增加權限。Plan Evaluator 會從完整原文重新讀一次，不信任上游改寫過的 `should_execute`。

## 各種禁止的意義

| 請求中的文字 | 被禁止的操作 | 理由 |
|---|---|---|
| 不要搜尋 / do not use WEB-SEARCH | `web_search`、`query_context7` 一律拒絕 | 搜尋在本回合就對外發出，不受預覽模式保護（F1） |
| 不要檢查 / do not inspect | `inspect_*` 一律拒絕 | 檢查在本回合就讀取檔案 |
| 不要下載 | `download_string` 一律拒絕 | |
| 不要執行任何東西 / do not execute anything | 所有操作 | |
| 不要執行 PANDA（點名工具） | 只拒絕名稱含該工具的 run（`run_panda`、`run_lioness_panda`） | 「不要跑 LIONESS，跑 PANDA」仍可執行 PANDA |
| 不要執行分析（未點名） | 所有本機分析 | |
| 只解釋 / guidance only | 所有沒有另外正向要求的操作 | F2 |
| 本機分析的禁止，旁邊有 dry-run、preview、準備、預覽 等字 | 不拒絕，意思是「現在不要」 | 見下方說明 |

**為什麼預覽請求旁的「不要執行」不拒絕？** 在這個 harness 裡，一般回合產生的本機分析計畫本來就只是預覽；真正執行要等使用者另外輸入 `/execute` 並回答 yes。`/execute` 會讓 graph 重新讀**同一段原文**。如果在這裡拒絕，「先建立 workflow preview，不要直接執行 PANDA」這類請求就會連日後的 `/execute` 也被擋掉。這類請求在紀錄中有 6 個以上（gene-validation、preview 手動測試）。

## 修改的檔案

- `scripts/netzoo_agent_core/routing/request_scope.py`：`operation_scope()` 把請求拆成三部分：能授權的文字、禁止條款（種類、工具名、原文引用）、只解釋與預覽標記。子句切分沿用既有的 `_scoped_clauses`（歷史範圍判斷）。
- `scripts/netzoo_agent_core/routing/capability.py`：`has_explicit_execution_request`、`has_direct_execution_intent`、`has_direct_retrieval_request`、`is_input_preflight_request` 只讀能授權的文字。其他調整：
  - preflight 的觸發條件拿掉了「不要執行分析」這個負向標記：拒絕一種操作，不等於要求另一種。
  - 新增英文 "check/validate my input files"，與中文「檢查輸入」對稱。
  - `reconcile_request_mode`：如果要求的操作種類整類都被禁止，就不提升。
  - F7：中文動詞後面直接接英文工具名（「請執行PANDA」）也算邊界。
- `scripts/netzoo_agent_core/contracts/authorization.py`、`contracts/decisions.py`：新增 `OperationAuthorization` 型別，以及 `TaskDecision.operation_authorization`。這個欄位未設定時不出現在 dump 中。
- `scripts/netzoo_agent_core/routing/authorization.py`：`read_operation_authorization`、`forbidding_reason`、`enforce_operation_authorization`。
- `scripts/netzoo_agent_core/graph/operation_authority.py`、`graph/routing_planning.py`：classify 節點在 `invoke_router` 的**所有**路由路徑之後套用 gate，並記錄兩種事件：
  - `routing.operation_forbidden`：有執行被拒絕時。
  - `routing.operation_restrictions_read`：讀到限制、但沒有拒絕任何執行時。
  - 刻意不修改 `router_invocation.py`：另一個 session 的 `06d5b48`（Log 376）待 revert，避免衝突。
- `scripts/netzoo_agent_core/evaluation/plan_review.py`：新增必要項目 `operation_authorization`，從完整訊息重讀；STRING 下載分支也有檢查。
- `tests/test_contracts_package.py`：TaskDecision schema digest 依慣例更新，附日期註記。
- `tests/test_operation_authorization.py`：新增 46 項測試。

## 驗證

**測試**
- HEAD（`a8cd3f2`）加上本次檔案，不含其他未提交修改：3,337 通過、35 跳過、0 失敗。可以單獨提交。
- 主工作樹，含 Codex 未提交的第 1 到 4 項：本次的 46 項全數通過。
  - 唯一的失敗是 `test_interpretation_children_are_responsibility_sized`，來自同時進行中的 `extraction.py` regex 修正（檔案超過行數上限），與本項無關。
  - 修改前基準為 3,308 通過、35 跳過。

**驗收情境**（46 項測試涵蓋 router、Planner、Plan Evaluator、完整 graph，並使用 mock dispatcher）

| 情境 | 修改前 | 修改後 |
|---|---|---|
| F1：Do not use WEB-SEARCH…（中英文各一） | `web_search` / ready / approved | `no_tool` / respond_only；dispatcher 從未被呼叫 |
| 正向對照：請使用 WEB-SEARCH 搜尋…TP53。不要執行 PANDA。 | `web_search` 執行 | 相同（dispatcher 被呼叫 1 次） |
| F2：只解釋 preflight，不要檢查 / 不要執行分析，只要解釋 | 提升為 `inspect_inputs` | `no_tool` |
| 檢查但不要分析（中英文各一） | 英文沒有提升 | `inspect_inputs` 可執行，`run_*` 被拒絕 |
| 模型自己說 execute，但請求寫「do not run it yet」 | 會執行 | gate 拒絕；`matched_actions` 保留 SAMBAR |
| 上游規則全被繞過，直接交出 ready 的 `web_search` 計畫 | approved | Plan Evaluator rejected |
| F7：請執行PANDA / 請執行 PANDA | answer / execute（兩者不一致） | 都是 execute |
| CLI：「Prepare the preview… but do not run it yet」 | — | 與未加禁止時相同：確認輸入 → approved 預覽 |
| CLI 對照：「…but do not run it」（沒有預覽字樣） | — | respond_only，並記錄 `blocked_action` |
| F3：開頭禁止、6,100 字後才要求搜尋 | 路由只看到尾端，會搜尋 | 路由仍看不到開頭，但 Plan Evaluator 讀全文後拒絕，dispatcher 未被呼叫 |

**Codex 的 probe**：重跑結果存於 `probe-observations-after.json`。F1、F2、F7 已改變；F3 的 routing 截斷、F4 到 F6 不在本項範圍，維持原狀。

**紀錄重播**（`replay.py`，離線執行）
- 982 個已記錄的使用者請求中，確定性輔助函式的結果有 12 處改變，都是修正錯誤。例如「請推薦適合的內建工具，不要執行」，以及 "I already finished my PANDA run last month…"，以前被算成直接執行意圖。
- 另有 1 處只改變 request mode，最終仍是 `inspect_inputs`。
- 18 個已記錄、實際會執行的決策中，現在會拒絕 2 個，兩個都是正確的拒絕：「請先只做 inspect_inputs / preflight，不要執行 PANDA」當時被記錄成 `run_panda`。

**模型看得到的內容**：prompt/schema fingerprint 不變（legacy `e920bf3b5d57`、claims `743b2dd0d73a`；有無本次檔案都相同）。

## 限制與界線

- 禁止與正向提示的判斷用字詞規則實作，但只用在兩處：
  - 否決：只能減少執行。
  - 確定性提升的門檻：原本沒有否定判斷，現在只有更嚴，沒有更寬。

  它不負責理解意圖（理解仍由模型負責），也不宣稱召回率。沒抓到的寫法，例如單獨用 "not" 的 "I'd prefer you not run it"，會維持原本的行為。本次沒有用 held-out 問題集或 live 模型做評估。
- 本次只讀「最新一則訊息」。跨回合或跨階段的限制屬於第 2 項（共用需求物件）。
- F3（路由只讀尾端 6,000 字元）沒有修。目前靠 Plan Evaluator 讀全文來補，但 router 本身仍可能產生錯誤的中間決策。
- 另外發現一個與本項無關的效能問題：一則 6 KB 的訊息，會讓 `extraction._reverse_named_path` 在一個回合內花約 15 秒做 regex。已另開任務，沒有在這裡修。
- 執行 Codex 的 `probes.py` 時，它會覆寫 `2026-10-03-routing-execution/observations.json`。這個目錄未提交，原檔已被覆寫。現在的檔案是用「修改前的程式」在 scratch 副本重新產生的：F1 到 F7 的觀察與原報告一致，但 `source_sha256` 是 2026-10-05 的工作目錄，不是 2026-10-03 的 HEAD。

## 重現指令

```sh
python -m pytest -q tests/test_operation_authorization.py
python -m pytest -q
python docs/diagnostics/2026-10-05-operation-authorization/replay.py --base <修改前的工作樹>
```
