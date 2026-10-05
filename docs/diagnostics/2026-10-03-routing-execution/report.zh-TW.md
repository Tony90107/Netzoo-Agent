# NetZoo Agent 診斷報告
## 意圖理解、Semantic Routing、工具選擇與執行

日期：2026-10-03（Asia/Taipei）  
基準：`evidence-contract-grounding` 工作目錄；HEAD `d0bccdcf46af4da9f1302a81759c82ec76df47fc`。  
方法：Verify 等級、知識圖譜定位、目前原始碼核對、離線重現及選定回歸測試。此次只新增診斷文件與重現腳本，未修正產品程式。

## 核心判斷

目前最優先的問題是：**程式在「修正模型判斷」時，可能把使用者的否定或諮詢重新提升成工具執行；後面的 Plan Evaluator 主要確認計畫結構與資料契約，未攔下本次重現的語意授權錯誤。**

這個問題不能只靠換更強模型解決。本次在模型邊界明確提供 `guidance + answer`，且科學語意證據通過驗證，程式仍將「不要搜尋」改成 `web_search / should_execute=True`，產生 `ready / approved` 計畫。

另一方面，系統已有相當完整的防護：typed registry、輸入／證據檢查、Plan Evaluator、執行後 artifact 驗證、bounded recovery，以及本機命令的 dry-run 和 process timeout。因此建議先修正跨階段契約與例外分支，不宜直接推倒重寫。

| 編號 | 優先度 | 面向 | 已重現問題 | 驗證深度 |
|---|---|---|---|---|
| F1 | P1 | 意圖、工具選擇 | 禁止 WEB-SEARCH 仍產生獲准搜尋計畫 | 模擬模型邊界＋真實 routing／planning／review |
| F2 | P2 | 意圖理解 | 「只解釋／不要分析」被提升為 inspect_inputs | 真實 hydration＋preflight 決策 |
| F3 | P2 | 語意上下文 | 只保留最後 6,000 字元，丟掉開頭限制 | 真實上下文裁切＋intent reconciliation |
| F4 | P2 | 執行結果 | 回傳內文中的 dry-run／traceback 污染工具狀態 | 真實 result normalizer |
| F5 | P2 | 執行控制 | DRAGON API 未受 TOOL_TIMEOUT_SECONDS 約束 | 真實 adapter＋30ms 模擬 API |
| F6 | P2 | Semantic routing | review 預算不足時丟失已驗證第一輪解讀 | 真實 semantic attempt loop＋模擬預算 |
| F7 | P3 | 中英混合意圖 | 「請執行PANDA」和「請執行 PANDA」走不同修正結果 | 真實 intent helpers |

P1：應優先修正的使用者授權／外部操作錯誤。P2：影響正確性、穩定性或可用性。P3：較窄的語言一致性問題。這些等級不是實際發生頻率；本次未量測線上錯誤率。

## 目前流程與問題集中點

一般路徑如下；研究假設比較、已驗證 continuation、STRING acquisition 等有提前分流：

```text
最新使用者訊息（尾端 6,000 字元）
  → semantic interpreter
  → evidence validation／必要時 review 或 patch
  → typed outcome 與 registry matching
  → discriminator
  → deterministic retrieval override
  → intent router
  → deterministic request-mode reconciliation
  → TaskDecision assembly／hydration
  → hypothesis／condition／input-inspection 等補充階段
  → deterministic preflight override
  → memory retrieval
  → Planner
  → Plan Evaluator
  → allowlisted Executor
  → result normalization／artifact validation
  → bounded recovery／response
```

此處的 semantic routing 主要是「LLM 結構化解讀＋證據驗證＋registry 規則匹配」；不能把整段行為簡化成 embedding 相似度選工具。模型、規則與後置修正各自影響最終選擇。依據：[router_invocation.py](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts/netzoo_agent_core/graph/router_invocation.py:147>)、[topology.py](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts/netzoo_agent_core/graph/topology.py:30>)。

## F1 — 否定搜尋被改成獲准執行（P1）

**情境**

> Do not use WEB-SEARCH to search for PANDA papers. Which tool groups patients from somatic mutations using gene length normalization?

第二句是一個正常的方法諮詢；第一句明確禁止網路搜尋。中文否定前綴「不要用 WEB-SEARCH 搜尋 PANDA 文獻。」也能重現。

**實測**

- scripted semantic result：`request_mode=guidance`，科學 outcome 的 evidence validator 回傳 valid。
- scripted intent：`mode=answer`。
- 最終決策：`action=web_search`、`should_execute=True`。
- Planner：`ready`；Plan Evaluator：`approved`。
- 未呼叫真實搜尋服務。

**根因**

`has_direct_retrieval_request` 只檢查「工具標籤＋搜尋字眼＋不是部分資訊問句」，沒有檢查否定範圍。它同時影響 request mode 和 registry override；之後又把 intent router 的 answer 改成 execute。因此同一條弱規則能改寫工具與授權兩個決策。

Plan Evaluator 的 `intent_and_capability_alignment` 在這條路徑確認 action／workflow 一致，`planner_state_consistency` 再接受 decision 裡的 `should_execute`；沒有獨立否決原句的「不要搜尋」。允許名單只能保證工具存在，無法保證使用者要用它。

**影響**

使用者禁止的查詢可能被送往外部搜尋服務；查詢也可能帶出原本只想在對話中討論的內容。本機科學運算的 `/execute` 保護不能直接當成搜尋防護：retrieval dispatcher 沒有走 `_run_command` 的本機 dry-run 分支。

**修正方向**

先產生可追溯到原文的正向授權／禁止操作欄位；否定範圍優先於工具名稱命中。規則修正不得僅憑提及工具而升級權限。Evaluator 應核對獨立的 authorization evidence，而非只信任已被改寫的 boolean。

**驗收**：中英文否定、引用他人指令、歷史敘述均不得觸發查詢；正向搜尋仍可用。必須測到計畫審核與 mock dispatcher，而非只測 classifier。

來源：[capability.py](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts/netzoo_agent_core/routing/capability.py:308>)、[router_invocation.py](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts/netzoo_agent_core/graph/router_invocation.py:291>)、[router_invocation.py](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts/netzoo_agent_core/graph/router_invocation.py:348>)、[plan_review.py](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts/netzoo_agent_core/evaluation/plan_review.py:121>)、[dispatch.py](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts/netzoo_agent_core/routing/dispatch.py:14>)。

## F2 — 把不做分析誤當成要做輸入檢查（P2）

**情境與實測**

`Only explain input preflight; do not inspect anything. expression_file=demo.tsv`

以及：

`不要執行分析，expression_file=demo.tsv，只要解釋 PANDA。`

兩者先以不執行的決策進入 hydration，再套用 preflight repair，結果都變成 `inspect_inputs`、`should_execute=True`。

**根因**

preflight marker 包含「不要／勿／不直接執行分析」；只要再有檔案欄位，就能觸發 promotion。英文的 `preflight` 提及也未區分是在解釋名詞、引用指令，還是要求實際檢查。負向分析意圖並不等於正向檔案檢查授權。

**影響與邊界**

已確認錯誤工具選擇與授權欄位；本次案例沒有完整有效輸入，仍有 missing inputs，**未證明這兩句會直接完成檔案檢查，更未發生科學分析**。但它會把純解釋帶進錯誤的補檔／預檢流程。

**修正方向與驗收**

要求明確的正向 inspect 意圖，並分開 `explain_preflight`、`inspect_inputs`、`run_analysis`。測試「只解釋」「不要檢查」「檢查但不要分析」三者；只有最後一種可進入 inspect。

來源：[capability.py](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts/netzoo_agent_core/routing/capability.py:143>)、[capability.py](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts/netzoo_agent_core/routing/capability.py:195>)。

## F3 — 長訊息的開頭限制會從 routing 消失（P2）

**實測**

建立 6,099 字元訊息：開頭是 `Do not execute anything; explain only.`，中間為長內容，結尾為 `Run PANDA`。真正的 `latest_user_task` 只留下最後 6,000 字元，開頭限制消失；裁切後的文字可將 answer reconcile 成 execute。

**根因**

使用尾端字元切片控制 context，而不是保留有來源的需求、禁止事項、檔案綁定與引用邊界。classify 用裁切後訊息，Planner 與 Plan Evaluator 則讀取末則完整 message，造成各階段使用的原文不一致。

**影響與邊界**

長研究說明、貼入資料說明或腳本時，前文的否定、研究目標、物種或檔案選擇可能遺失。本次證明裁切與 intent helper 的結果，**沒有執行完整長訊息圖或宣稱本機分析必然會啟動**。CLI continuation 可處理部分多輪情境，因此也不能據此說所有多輪對話都失效。

**修正方向與驗收**

統一傳遞 `RequestContext`：原文識別、截斷狀態、目標、禁止事項及其 spans。超長輸入要保留限制或明確要求縮短；不要把失去上下文的尾句當成完整授權。測試 5,999／6,000／6,001 字元與首尾衝突案例。

來源：[llm.py](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts/netzoo_agent_core/llm.py:91>)、[routing_planning.py](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts/netzoo_agent_core/graph/routing_planning.py:22>)、[routing_planning.py](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts/netzoo_agent_core/graph/routing_planning.py:68>)。

## F4 — 工具「內容」被當成執行「狀態」（P2）

**實測：對 web_search 的 normalizer 提供正常文件內文**

| 工具回傳文字 | 得到的狀態 |
|---|---|
| Search documentation: dry-run is supported. | dry_run |
| The documentation explains how to debug a traceback. | failed |
| Documentation was retrieved successfully. | success |

**根因**

`structure_tool_result` 在整段 `raw_output` 搜尋 `traceback` 等失敗字串，以及 `dry-run`。外部文件或工具說明中的字眼，因此能改變執行狀態。Retrieval 回傳的外部文字會進入相同 normalizer。

**影響**

查詢成功卻被報成失敗或未執行，後續回應與 evaluator 判斷失準。另外，程式在 `dry_run=True` 時略過 artifact 驗證；這是相同設計對寫檔工具的潛在延伸影響，本次沒有重現偽造 artifact。

**修正方向與驗收**

adapter 直接回傳 typed envelope，包含 `status`、`exit_code`、`execution_mode`、`artifacts`、`content`；內容不得改寫狀態。文字 parser 僅用於明確的 legacy protocol 欄位。加入含錯誤教學文字、引用 exception 與 dry-run 文件的回歸案例。

來源：[results.py](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts/netzoo_agent_core/routing/results.py:79>)、[retrieval.py](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts/netzoo_agent_core/routing/retrieval.py:284>)、[execution.py](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts/netzoo_agent_core/graph/execution.py:90>)。

## F5 — Python API 工具與 subprocess 的逾時契約不同（P2）

**實測**

把 `TOOL_TIMEOUT_SECONDS` 設成 0.001 秒。替 DRAGON 的計算 API 放入固定睡眠 0.03 秒的 stub，並模擬輸入與輸出寫入；真正的 `run_dragon.invoke` 仍等待完成並回傳 execution completed。耗時約 0.03–0.04 秒，沒有 timeout。

**根因**

subprocess 路徑用 `process.wait(timeout=...)` 並終止 process group；DRAGON 則直接在 Python 內呼叫數值 API，未經同一 deadline 控制。OTTER 也有直接 API 呼叫，但本次動態重現範圍是 DRAGON。

**影響與邊界**

設定的工具時限對不同工具不一致；長時間數值運算可能持續占用 worker。此次沒有測大型資料、硬中斷延遲或整個 supervisor 的取消行為，不能宣稱 UI 永遠無法取消。

**修正方向與驗收**

把可能長時間運算的 API 放進可終止的 worker process，共用 deadline、取消與結果封裝。以阻塞 stub 驗證準時終止、沒有遺留 worker、沒有把部分產物當成成功。

來源：[command.py](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts/netzoo_agent_core/command.py:127>)、[execution.py](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts/netzoo_agent_core/execution.py:736>)、[execution.py](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts/netzoo_agent_core/execution.py:785>)。

## F6 — 第二輪 review 無預算時，已驗證解讀被丟棄（P2）

**實測**

在 `review_policy=always` 下，第一輪使用既有 SAMBAR 諮詢 fixture，通過 evidence validation，事件紀錄為 `semantic_interpreter: success`，preliminary registry match 為 exact。讓第二輪 preflight 回傳 blocked 後：

- reviewer 沒有被呼叫；
- 最終 interpretation 為 None；
- budget_exhausted 為 True；
- 第一輪可用結果沒有保留。

**根因**

attempt loop 的 budget-blocked 分支直接 `return None`，沒有採用函式內已儲存的 `validated`。這與函式註解「review 是第二意見，不是必要前提」及其他錯誤復原分支的保留策略不一致。

**適用範圍**

這個重現使用可配置的 `always` policy。production factory 預設 `when_needed`，完整單一 exact match 可以跳過 review，所以**不能把此問題說成每個正常請求都會發生**。仍進入第二輪的請求有同一 budget return 分支；其影響須依具體第一輪有效程度判斷。

**修正方向與驗收**

在預算不足時保留已驗證的 guidance，標示 review 未完成；需要 review 才能決定的部分維持 unresolved，不能因此取得額外執行權限。測試第一輪 valid／partial／invalid 三種狀況，分別驗證退化策略。

來源：[semantic_attempts.py](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts/netzoo_agent_core/graph/semantic_attempts.py:94>)、[semantic_attempts.py](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts/netzoo_agent_core/graph/semantic_attempts.py:193>)、[semantic_attempts.py](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts/netzoo_agent_core/graph/semantic_attempts.py:669>)、[factory.py](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts/netzoo_agent_core/graph/factory.py:47>)。

## F7 — 中英文相接時的 word boundary 不一致（P3）

**實測**

| 原句 | has_explicit_execution_request | has_direct_execution_intent | 將 answer reconcile 後 |
|---|---|---|---|
| 請執行PANDA | False | True | answer |
| 請執行 PANDA | True | True | execute |

**根因**

中文動詞後套用 Unicode regex 的 `\b`。漢字與英文字母都可算 word character，因此「行P」之間沒有 word boundary；另一個 direct intent helper 的規則不同，產生分歧。

**影響與邊界**

一個空格會改變 deterministic fallback／reconciliation，造成同義指令行為不一致。LLM 仍可能正確辨識無空格指令，因此這不是已測得的整體中文成功率下降。

**修正方向與驗收**

統一 intent cue 的解析規則，對中文與英文字標籤使用合適的邊界；加入無空格、全形標點、中英混寫的成對測試。

來源：[capability.py](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts/netzoo_agent_core/routing/capability.py:127>)、[capability.py](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts/netzoo_agent_core/routing/capability.py:279>)、[capability.py](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts/netzoo_agent_core/routing/capability.py:322>)。

## 設計層面的診斷

### 1. 工具辨識、科學匹配、執行授權需要各自的真實來源

目前多階段都能修改 `action`、`request_mode`、`should_execute`。F1、F2 說明：只檢查每一階段的輸出 schema 不夠，還需要跨階段 invariant。

建議維持三個獨立概念：

- **Scientific request**：想回答的問題、產物、granularity、科學假設。
- **Capability decision**：相容候選、選中工具、匹配依據、未解決限制。
- **Action authorization**：允許／禁止的操作、目前 session 狀態、原文證據。

後置修正可以補充候選與說明，但若沒有新的正向授權證據，就不能把 answer 升級成 execute。尤其「能做」「適合做」「允許現在做」不能共用一個 boolean。

### 2. exact match 不宜同時承擔多種含義

matcher 內的註解已明示：exact 可能代表「只有一個相容能力」，也可能是 specificity ranking 在數個相容能力中選出一個；此外還有 named-workflow match。雖然程式已有消歧保護，對外仍應分清：

`unique_semantic_match`、`explicit_method_selection`、`ranked_recommendation`、`unresolved_candidates`。

這是可維護性與可解釋性建議，**本次未另宣稱重現一個現存的 specificity 誤選工具案例**。依據：[outcome_matching.py](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts/netzoo_agent_core/routing/outcome_matching.py:794>)。

### 3. 測試通過與自然語言可靠度是兩種證據

本次選定的 **429 項既有測試全部通過**，但額外 probe 仍能重現上述問題。這代表目前測試保護了不少既定契約，卻不能據此推論否定、長上下文和跨階段授權一定可靠。

專案已有 raw-prompt evaluation harness，且清楚區分 fixture 與 live 評估。應繼續利用它，而不是另造只有 happy path 的測試。建議增加：

| 評估層 | 應量測什麼 |
|---|---|
| 意圖 | 正向／否定／假設／引用／只規劃／只解釋；false execution rate |
| Semantic extraction | 產物、granularity、entity roles 的正確率；review 是否遺失已知資訊 |
| 工具選擇 | 候選集合召回、單一工具 precision、unsupported 拒絕、合理 abstention |
| 跨階段 | 初始理解與最終 action 的差異及理由；未經授權的 promotion 次數 |
| 執行 | ready→approved→實際工具的一致性、timeout、artifact 正確性、狀態污染 |
| 對話 | 改口、撤銷、前文選擇、指代、多輪限制持續有效 |
| 成本 | 每角色呼叫數、tokens、p50／p95 latency、budget fallback 比例 |

固定模型、prompt／registry 版本和資料集版本，留出未參與修正的測試集，對 live prompt 重複取樣。此次沒有執行 live 模型測試，因此不提供準確率百分比。

依據：[evaluate_routing.py](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts/evaluate_routing.py:1>)、[test_routing_evaluation.py](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/tests/test_routing_evaluation.py:1>)。

## 建議修正順序

1. **先處理 F1、F2**：修正否定／授權判斷，補從 router 到 approved plan 的整合測試。
2. **處理 F3、F4**：統一 RequestContext 與 ToolResult envelope，避免原文限制與執行狀態在傳遞中失真。
3. **處理 F5、F6**：統一 deadline 與 graceful degradation，避免較複雜請求失去回應或已知結果。
4. **處理 F7 並擴充 corpus**：用語言變體、改口與反例測試檢查規則，而不是逐句添加例外。
5. **再評估模型或 prompt 變更**：先建立分層量測，才能判斷瓶頸來自模型解讀、規則覆蓋、候選能力描述或執行契約。

## 驗證記錄與限制

### 已執行回歸測試

```bash
python -m pytest -q \
  tests/test_routing_registry_invariants.py \
  tests/test_outcome_routing.py \
  tests/test_routing_evaluation.py \
  tests/test_workflow_continuation.py \
  tests/test_command_processes.py \
  tests/test_execution_artifact_contracts.py
# 184 passed, 1 warning, 7.60s

python -m pytest -q \
  tests/test_agent_gate.py \
  tests/test_semantic_attempt_bound.py \
  tests/test_semantic_patch_repair.py \
  tests/test_guidance_routing_fixes.py \
  tests/test_cli_slash_commands.py
# 245 passed, 1 warning, 9.55s
```

兩批 warning 均為相依套件 pytz 的 datetime deprecation，不是測試失敗。使用既有 `/opt/anaconda3/bin/python`；未安裝套件。

### 重跑診斷

在專案根目錄：

```bash
python docs/diagnostics/2026-10-03-routing-execution/probes.py
```

- [probes.py](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/docs/diagnostics/2026-10-03-routing-execution/probes.py>)：離線重現腳本；不呼叫真實 LLM、搜尋或科學運算。DRAGON 的 API 與寫檔均為 stub。
- [observations.json](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/docs/diagnostics/2026-10-03-routing-execution/observations.json>)：本次結果及主要證據檔案 SHA-256。
- [graph-coverage.json](</Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/docs/diagnostics/2026-10-03-routing-execution/graph-coverage.json>)：圖譜 coverage／freshness 查核。

### 範圍限制

- 圖譜 generation 是 `2026-09-21T13:19:20Z`。ready 不代表原始碼仍新鮮：多個核心檔案為 metadata_changed，semantic_attempts 為 not_tracked。因此圖譜僅用來定位，實質結論以目前原始碼與 probe 為準；不是全庫完整稽核。
- 工作目錄本來有未提交變更，且檢查期間仍有其他修改增加。此次未更動那些檔案；以 observations 的檔案雜湊作為重現對照，不將所有工作目錄內容等同 HEAD。
- 沒有測 production API、真實 provider outage、大型資料的運算時間、端到端桌面 UI、全部 workflow 的數值結果或真實使用者對話分布。
- F1 到計畫審核層；F2/F3/F7 是明確限定的決策邊界 probe；F4 是結果解析；F5 是 adapter timeout；F6 是預算控制流。這些證據不可混稱為七個完整線上事故。

