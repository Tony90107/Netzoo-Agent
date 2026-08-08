# LangGraph NetZoo Planner / Executor / Evaluator Agent 使用說明

這個 agent 用同一個 LangGraph workflow 整合 PANDA、PUMA、LIONESS 與 CONDOR。
它不是只做一次工具路由，而是先盤點資料、規劃步驟、執行並評估結果。

## Graph 架構

```text
使用者需求
  -> Project Policy Loader（AGENTS.md + workflows/*.yaml + Python validation）
  -> Memory Retrieval（UserProfile + relevant Episodes）
  -> Intent Classifier
  -> Planner（已提供／workspace 找到／安全預設／仍缺少）
  -> Plan Evaluator（rubric、allowlist、evidence、step order、output safety）
  -> 若有歧義：CLI 留在同一 session 等待補充，再回 Planner
  -> Executor：先 inspect，再執行 NetZooPy 或 CONDOR
  -> Evaluator：通過則進下一步；可修復錯誤則有限次 replan；否則停止
  -> Response：回報完整 evidence ledger 與執行結果
```

## Project Policy Loader

正常啟動時，agent 會先尋找專案 `AGENTS.md`，解析 YAML front matter 的
`policy_version`、project conventions 與 workflow spec directory，再載入
`workflows/*.yaml`。Loader 會 fail closed 驗證：

- policy version 必須是目前支援的 version 1。
- 六個 YAML action 必須完整等於 Python run-action allowlist。
- `required_inputs` 必須與 Python `REQUIRED_INPUTS` 完全一致。
- `validation_steps` 與 `execution_step` 必須與 Python code-enforced registry 一致。
- workflow directory 必須位於 `AGENTS.md` 所在專案內。
- policy text 有大小、欄位與 convention 長度限制。

`AGENTS.md` 本文不會整段注入模型；runtime 只採用經 schema 驗證的 front matter 與
YAML conventions。Router catalog 由 validated YAML 生成；Planner 使用完整 typed
snapshot。這些資料不能新增工具、移除 required inputs、繞過 `/execute` 授權、在
`/test` 後執行工具，或改寫 Executor。Python gate 永遠是最高執行權限。

不需要 OpenRouter API key 即可檢查 effective policy：

```bash
python scripts/netzoo_agent.py --policy-status
```

輸出包含 policy version、SHA-256 hash、`AGENTS.md` 路徑、workflow directory 與六個
已驗證 action。每個 WorkflowPlan 與 compact Episode 也會記錄 policy hash，方便確認
一次任務是依哪一版規則完成。

規則責任分工：

- `AGENTS.md`：人類可讀的跨 workflow 工作慣例。
- `workflows/*.yaml`：可驗證的 NetZoo workflow 規格。
- `scripts/netzoo_agent_core/`：不可繞過的安全、驗證、執行與 recovery；
  `scripts/netzoo_agent.py` 只保留 CLI 與舊 import 相容入口。
- `UserProfileStore`：使用者明確確認的偏好。
- `EpisodeStore`：過去任務的 compact outcome。

Planner 的選擇原則：

- 使用者明確提供的路徑優先。
- 先搜尋 expression 所在資料集目錄，再搜尋專案 `data/`。
- 最佳候選在檔名、所在目錄與 workflow（PANDA 或 PUMA）上明顯勝出時，自主採用。
- 輸出路徑是可逆設定，未提供時使用專案預設。
- 候選接近、互相衝突或完全找不到時，才向使用者提出一個合併問題。
- 「試跑／跑一次／demo／toy」會先尋找完整 dataset bundle，並以跨檔案 ID
  相容性驗證；正式分析不會擅自拿 toy data 代替研究資料。

因此輸入：

```text
我要跑 LIONESS PANDA，expression 是 data/lioness-toy/expression.tsv
```

agent 會說明 expression 是使用者提供、motif/PPI 是從相同資料集找到、兩個 output
是 Planner 推定；Plan Evaluator 通過後，才依序執行 `inspect_inputs` 與
`run_lioness_panda`。它不會先把
所有候選列成選單要求使用者逐項決定。

## Pre-execution Plan Evaluator

Planner 產生 `WorkflowPlan` 後不會直接進 Executor。獨立的 `evaluate_plan` graph node
會先用程式碼評估 typed plan，只有 `approved` 才取得工具執行權。Rubric 包含：

| Criterion | 檢查內容 |
|---|---|
| intent_and_capability_alignment | action 是否真的符合使用者授權的 deliverable |
| required_input_evidence | 每個 required input/output 是否都有一致且非 missing 的 evidence |
| step_allowlist | 所有步驟是否都存在 Python action allowlist |
| validation_and_execution_order | 是否依 workflow spec 先 validation、後 execution |
| output_non_overwrite | output 是否與任何 input 路徑衝突 |
| planner_state_consistency | ready、missing inputs、should_execute 與 steps 是否互相一致 |
| project_policy_binding | plan policy hash 是否等於目前驗證過的 project policy |

評估的 source of truth 是 `PlanEvaluationResult` 與 `PlanRubricItem`；Markdown 表格只是
把 typed rubric 顯示給人看的 audit view，程式不會再解析 Markdown 來決定通過與否。
任何 required criterion 為 `fail` 時，狀態為 `rejected`，Executor 完全不執行並顯示
評估表。`needs_input` 或 `needs_confirmation` 則標成 `deferred`，等人類補充後重新規劃。

這個 Plan Evaluator 是獨立 graph role，但不是另一個可以自由擴權的 LLM agent。
目前先採 deterministic evaluator，因為 allowlist、路徑覆寫、required inputs 與 step
order 都應該可重現。未來若加入 LLM Critic，適合只評估「計畫是否充分回答研究目的」
等語意品質；它只能要求修改或否決，不能新增工具、降低 required inputs 或繞過此 gate。

## 這個 agent 在做什麼？

它不是取代 PANDA/PUMA，而是站在使用者和工具中間：

1. 使用者用自然語言說：「我要跑 PANDA」、「我要跑 PUMA」、「幫我看 input 格式」。
2. LLM 透過 OpenRouter 先理解使用者要的 deliverable，再從本 agent 的 capability
   catalog 配對工具；使用者不需要預先知道 PANDA、PUMA 或 LIONESS 的名稱。
3. LangGraph Planner 建立有來源依據的多步計畫。
4. Executor 執行檢查與工具，Evaluator 決定繼續、修復或停止。
5. 工具可以：
   - 檢查 input 檔案的基因/TF/miRNA ID 是否有交集
   - 把 sample×gene 或 gene×sample 整理成 netZooPy expression TSV
   - 執行 PANDA
   - 執行 PUMA
   - 執行 LIONESS-PANDA、LIONESS-PUMA、LIONESS co-expression
   - 透過 Websearch MCP 搜尋目前網頁或文獻資訊
   - 如果資訊不足、任務無關或超出能力範圍，就不執行

PANDA/PUMA 的概念與格式問題由 LLM 直接回答，不需要呼叫工具。

## Websearch MCP

Context7 專門查套件文件；一般 web/literature search 使用 Tavily MCP：

```bash
export TAVILY_API_KEY="你的 Tavily API Key"
export WEBSEARCH_MCP_URL="https://mcp.tavily.com/mcp"
```

例如輸入「搜尋最新的 LIONESS 方法論文」。搜尋結果視為不受信任的外部資料，
只供回答參考，不會取得本機命令或檔案修改權限。

若只需要第一筆乾淨網址，不需要 LLM 摘要：

```bash
docker compose run --rm netzoo web-url \
  "netZooPy LIONESS official documentation" 2>/dev/null
```

`web-url` 不消耗 OpenRouter token，只使用 Tavily Websearch 額度。

## 工具能力邊界

Agent 允許以下工具操作：

- 檢查現有 PANDA/PUMA input
- 整理 expression 方向或建立 co-expression matrix
- 執行 PANDA regulatory network inference
- 執行 PUMA regulatory network inference
- 執行三種 LIONESS 試跑
- 讀取 Context7 文件與 Websearch 結果

下列任務即使同屬生物資訊，也不會呼叫任何工具：

- 找基因突變、variant calling
- sequence alignment
- differential expression
- enrichment analysis
- raw FASTQ preprocessing
- protein structure prediction
- 實際下載或分析文獻附件（但可搜尋文獻資訊）

例如：

```text
幫我使用工具找到基因突變
```

Agent 應回覆這不屬於 PANDA/PUMA 的功能，並明確表示沒有執行工具。

能力閘門仍採保守策略：任務必須明確符合工具功能，而且模型信心至少為 `0.80`。
必要路徑不完整時不再直接降級成 `no_tool`；Planner 會先嘗試從 workspace 補齊，
只有無法安全判斷的欄位才詢問使用者。

## Goal-first 工具選擇

Router 現在不再以「使用者有沒有說出工具名稱」當作主要條件，而是依序判斷：

1. 使用者要取得的實際結果是什麼。
2. capability catalog 中有哪些本地工具可以完成它。
3. 這一輪是在詢問做法，還是授權 agent 立即執行。
4. 執行所需資料能否由 Planner 安全解析；不能時才集中追問。

例如：

```text
假設我要做一個 sample specific 的 miRNA 基因調控網路，我要怎麼做才好？
```

這是做法詢問，因此 agent 不會直接執行，但答案必須先指出專案已有的
`PUMA + LIONESS-PUMA` 組合：PUMA 建立 aggregate TF/miRNA-gene network，
LIONESS-PUMA 再建立每個 sample 的 network；接著只列出啟動該 workflow 所需的
expression、TF/miRNA prior、PPI、miRNA list 與輸出位置。不能再只回答「蒐集資料、
找 target、建網路、驗證」這類沒有連結到 agent capabilities 的一般步驟。

若改成直接指令：

```text
請幫我建立 sample-specific miRNA gene regulatory networks。
```

Router 會選擇端到端的 `run_lioness_puma`，即使句子中完全沒有提到 PUMA 或
LIONESS。Planner 之後會解析資料與輸出、先驗證 inputs，再建立 command preview，或在
目前互動 session 輸入 `/execute` 後實際執行。相反地，「幫我用這些檔案推論網路」仍過於模糊，不足以
唯一對應 PANDA、PUMA 或其他 workflow，因此不會猜測執行。

## Context7 MCP：自動取得較新的套件文件

Agent 會區分穩定的 workflow 知識與需要最新文件的問題：

- 「PANDA 需要哪些 inputs？」等穩定需求由本地 validated workflow registry
  與回答模型處理，不會為此額外查文件。
- 版本、相容性、CLI flags、安裝、升級、deprecated API、錯誤排除或明確要求文件時，
  才使用 Context7。
- LangChain、LangGraph、OpenRouter、Pydantic、pandas 的目前 API 問題也使用 Context7。

例如：

```text
PUMA 的 -i 參數現在應該放什麼格式？
```

Agent 會先透過 Context7 MCP 查詢，再根據查到的內容回答。Context7 是唯讀文件來源：
它不會執行分析、不會自行修改專案，也不會繞過 PANDA/PUMA capability gate。

Context7 API key 不是必填，但官方建議設定以取得較高 rate limit：

```bash
export CONTEXT7_API_KEY="你的 Context7 API Key"
```

重新建立含 MCP client 的 Docker image：

```bash
docker compose build
```

測試自動查詢：

```bash
docker compose run --rm \
  -e OPENROUTER_API_KEY="$OPENROUTER_API_KEY" \
  netzoo python scripts/netzoo_agent.py \
  --task "PUMA 的 -i 參數應該使用什麼格式？"
```

一般資料執行、天氣、生物資訊分析或不需要套件文件的問題不會呼叫 Context7。

> 截至 2026-06-23，Context7 尚未收錄 `netZooPy`。Agent 仍會自動嘗試查詢，
> 並在查不到時明確說明；LangChain、LangGraph 等已收錄套件可正常取得文件。
> 未來 Context7 收錄 netZooPy 後，不需要修改 Agent 程式即可開始使用。

## 為什麼要用 LangGraph？

一般 Python script 是固定流程：

```text
讀參數 -> 跑 PANDA
```

本專案的 LangGraph 是有狀態、多步且帶評估回圈的流程：

```text
classify -> plan -> execute -> evaluate
                    ^             |
                    |__ continue _|
                          |
                    complete / failed -> respond
```

## 先設定 OpenRouter key

到 OpenRouter 建立 API key 後，在 shell 設定：

```bash
export OPENROUTER_API_KEY="sk-or-v1-..."
# 回答模型
export OPENROUTER_MODEL="openai/gpt-4o-mini"
# Router 固定使用獨立、便宜且 allow-listed 的模型
export OPENROUTER_ROUTER_MODEL="openai/gpt-4o-mini"
export NETZOO_ROUTER_MODEL_ALLOWLIST="openai/gpt-4o-mini"
export NETZOO_RESPONSE_MODEL_ALLOWLIST="openai/gpt-4o-mini"
export NETZOO_MAX_TASK_TOKENS=20000
```

也可以參考 [.env.example](.env.example)。

## 在 Docker 裡使用

先 build：

```bash
docker compose build
```

互動模式：

```bash
docker compose run --rm \
  -e OPENROUTER_API_KEY="$OPENROUTER_API_KEY" \
  -e OPENROUTER_MODEL="$OPENROUTER_MODEL" \
  netzoo python scripts/netzoo_agent.py
```

互動模式會保留有界的 session 訊息歷史，但 Router 只接收最新使用者 turn。
若 Planner 缺少無法安全判斷的路徑，canonical continuation capsule 會保留
`PREVIOUS_ACTION` 與已選 inputs，因此不必把整段舊對話重新送進模型。輸入
`exit`、`quit` 或 `離開` 結束。

### Outcome-aware follow-up prompt

互動 CLI 不再於每輪固定詢問 `What NetZoo task would you like to run?`。第一次啟動會問
較中性的 `What would you like to accomplish with NetZoo?`，之後依上一輪 structured
outcome 產生下一個問題：

| 上一輪結果 | 下一個問題的方向 |
|---|---|
| 推薦了本地 workflow | 詢問是否繼續該 workflow，並提示第一個 required input |
| `needs_input` | 逐欄位顯示候選並保存選擇；全部確認後才重新規劃 |
| command preview / dry-run | 詢問要調整 inputs、探索其他 workflow，並提示在目前 session 輸入 `/execute` |
| workflow completed | 詢問要檢查／調整結果或啟動其他 workflow |
| tool failed | 詢問要修正 inputs 或改用其他 workflow |
| plan rejected | 詢問要修改被拒絕的 plan 或描述不同 deliverable |
| unsupported | 詢問要查看 supported capabilities 或換一個目標 |
| docs/web retrieval | 詢問要追問來源或連接到 NetZoo workflow |

Follow-up 不只是顯示文字，也保存 `continuation_action` 與 `expected_field`。例如回答完
sample-specific miRNA network 的做法後，CLI 會問是否繼續 `LIONESS-PUMA`：

```text
Would you like to continue with the recommended LIONESS-PUMA workflow?
Reply yes to start, provide the expression matrix path, or type a new request.
Controls: Enter/back = main prompt | exit = close
> yes
```

`yes` 會轉成前一個推薦 workflow 的 canonical continuation；直接輸入
`data/patient/expression.tsv` 則會同時延續 `run_lioness_puma` 並填入
`expression_file`。輸入一個新的完整目標時仍會交給 Router 當成新任務。

每個 outcome follow-up 都提供一致的導覽方式：

- 直接輸入另一個完整需求：不退出程式，立刻開始新任務。
- 按空白 Enter，或輸入 `back`、`menu`、`new`：返回主提示
  `What would you like to accomplish with NetZoo?`。
- 輸入 `exit`、`quit`：關閉整個 `netzoo-chat` process。

`Would you like ...?` 並非禁用句型；規則是每輪只能有一個 next-turn question。回答模型
不自行追加第二個 call-to-action，下一步互動統一由 CLI 的單一自然問句負責。Runtime
另有保守清理，只移除回答最末段以
`Would you like`、`Do you want`、`Shall I` 等開頭的重複問題，不會移除一般內容或科學
問題。這能避免回答與 CLI 各問一次，再疊加一大段 navigation 說明，同時保留自然語氣。

dry-run 預設維持在 `/test` 模式。只有使用者在目前互動 session 明確輸入 `/execute`
才會開啟執行授權；空白 Enter 或一般回答不會靜默開啟，輸入 `/test` 則會立即撤銷授權。
啟用後，重新提交 preview task 就會執行；若只想繼續詢問或跑其他 dry-run，不需要離開，
直接輸入新任務或按 Enter 回主提示即可。

## 受治理的長期記憶

Agent 現在把「未完成任務」與「跨任務記憶」分開：

- `.netzoo/sessions/` 是短期 checkpoint，用來繼續 `needs_input` 或
  `needs_confirmation` 的工作。
- `.netzoo/memory/profiles/` 只保存已經由使用者確認的長期偏好。
- `.netzoo/memory/episodes/` 保存精簡的完成／dry-run／失敗 outcome，不複製 dataset
  或完整 stdout。

每一輪 graph 會先執行 Memory retrieval，載入同 profile 的確認偏好與最多三筆相關
episode；執行結束後由 Memory consolidation 保存 compact outcome。Episode 依 profile
分目錄保存，搜尋不需要掃描其他 profile。中文查詢會建立中文字詞片段，也能辨識
「沿用上次」、「之前」與「重跑」等跨任務語意。

Episode 會在新增、搜尋、列出及 CLI 啟動時自動維護，預設規則如下：

- failed 保留 30 天，dry-run 保留 60 天，completed 保留 180 天。
- 每個 profile 最多 200 筆、約 10 MiB。
- 超過筆數或容量時，每個 workflow 最新一筆未過期的 completed episode 具有最高保留
  優先權；但筆數與容量仍是硬上限，額度不足時也會淘汰。
- 過期規則是硬限制；即使是 workflow 最新成功紀錄，滿 180 天仍會刪除。
- 舊版平面 episode 檔會自動遷移到 profile 分區；損壞檔案先隔離，30 天後清除。

可用 `NETZOO_EPISODE_RETENTION_DAYS`、`NETZOO_EPISODE_MAX_COUNT` 與
`NETZOO_EPISODE_MAX_MB` 調整 completed 保存天數、筆數與容量。failed/dry-run
仍採較短上限，避免低價值紀錄擠壓可重用的成功經驗。

目前支援的偏好為 `default_output_dir`、`allow_demo_autofill`、
`reuse_last_inputs` 與 `preferred_workflow`。偏好必須由使用者明確要求記住，Planner
會停在 `needs_confirmation`；只有 CLI 收到 `y` 或 `yes` 才會寫入。例如：

```text
Remember that my default output directory is outputs/alice.
Save these long-term preferences? [y/N]
- default_output_dir = outputs/alice
Confirmation > yes
```

`reuse_last_inputs` 預設關閉。即使已確認開啟，也只會重用相同 workflow 的成功 episode，
且在執行前重新驗證檔案存在與 identifier 相容性。失敗 episode 只用來辨識重複錯誤，
不會變成偏好或直接重播。

使用固定 profile，不需要記住 session id：

```bash
python scripts/netzoo_agent.py --profile alice --task "Run LIONESS PANDA"
```

查看或刪除記憶不需要 OpenRouter API key：

```bash
python scripts/netzoo_agent.py --profile alice --memory-status
python scripts/netzoo_agent.py --memory-cleanup
python scripts/netzoo_agent.py --profile alice --forget-memory
```

`--memory-cleanup` 會立即執行遷移、權限修復與所有 profile 的 episode 淘汰，並輸出
`migrated`、`expired`、`overflow`、`corrupt` 與 `deleted` 計數。Profile、episode、
session 與 tool log 皆以目錄 `0700`、檔案 `0600` 儲存；profile 每次載入也會重新驗證
workflow allowlist、boolean 型別與 output 路徑限制。

這是 persistent adaptive memory，不是 fine-tuning。Agent 能跨 session 記得已確認偏好與
過往 outcome，但不會因一次錯誤自行修改 Python policy。完整架構與待補能力見
[NETZOO_HARNESS_ARCHITECTURE.md](NETZOO_HARNESS_ARCHITECTURE.md)。

即使帶了 `--task`，只要結果是 `needs_input` 且 stdin 是互動終端，CLI 也不會退出：

```text
? The Planner requires additional input
Select input 1 of 2: Expression matrix (expression_file)
Enter a candidate number or a full path.
1. data/lioness-toy/expression.tsv
Selection > 1

Select input 2 of 2: PPI network (ppi_file)
Selections so far:
- expression_file: data/lioness-toy/expression.tsv
1. data/lioness-toy/ppi.tsv
2. data/manual-tests/ppi.tsv
Selection > 2
```

互動 wizard 在所有欄位選完前不會呼叫 LLM 或開始 workflow，因此 `1` 只會選擇目前
畫面上的欄位。進階使用者仍可用 `expression_file=1 ppi_file=2` 一次完成。補充完成後
會沿用原 workflow 重新規劃。不要對 Docker Compose 加 `-T`，因為 `-T`
會停用互動 stdin；在 CI 等非互動環境，agent 會保存 checkpoint、回傳 exit code 2，
並提示如何用 `--resume SESSION_ID` 繼續。

## CLI progress 與 session checkpoint

直接執行 `python scripts/netzoo_agent.py` 時，預設 CLI 使用 compact progress 與 compact
result，只顯示對一般使用者有直接價值的 workflow、input validation、執行／command preview
狀態、重要 inputs、outputs 與下一步。`./netzoo-chat` 則預設使用可讀、永久保留的 activity
timeline，在最終結果前列出 planning、tool、result 與 evaluation 摘要：

```text
◆ LIONESS-PANDA · dry run
→ Validating inputs
✓ Input validation passed
→ Preparing LIONESS-PANDA command
○ Command preview ready
```

可直接從 Python CLI 開啟同一種 timeline：

```bash
python scripts/netzoo_agent.py --timeline --task "Run LIONESS PANDA"
```

完整 evidence ledger、Router confidence、每個 LangGraph node、Evaluator decision、
memory retrieval/consolidation、session id 與成功時的 log path 改由 `--verbose` 顯示：

```bash
python scripts/netzoo_agent.py --verbose --task "Run LIONESS PANDA"
```

Timeline 與 `--verbose` 的資訊都是 structured state、tool status 與可稽核的決策摘要，
不是模型私有 chain-of-thought。只想看 compact 最終回答、不顯示進度事件則加 `--quiet`：

```bash
python scripts/netzoo_agent.py --quiet --task "Run LIONESS PANDA"
```

`--timeline`、`--verbose` 與 `--quiet` 不能同時使用。失敗時，compact result 仍會顯示 error、必要的
diagnostic log 與下一步；dry-run 一定顯示實際 command，避免精簡後失去 command preview
的核心資訊。

Agent 的所有使用者可見輸出固定為英文，與輸入語言無關。中文、日文或混合語言仍可
正常理解，但 Router reason、Planner ledger、CLI prompt、Evaluator 與最終回覆都使用英文。

自動 one-shot session 成功後會刪除 checkpoint，不會永久累積；`needs_input`、失敗、
互動模式或明確命名的 session 才會保留。直接啟動新的互動模式不會自動接續舊任務；
要恢復最近的 pending session，可使用 `--resume latest`，不需要記住 id：

```bash
python scripts/netzoo_agent.py --resume latest
```

指定固定 id、強制保留 one-shot session：

```bash
python scripts/netzoo_agent.py --session patient-001 --task "執行 LIONESS PANDA"
python scripts/netzoo_agent.py --resume patient-001
python scripts/netzoo_agent.py --keep-session --task "執行 LIONESS PANDA"
```

自動產生且已完成的舊 session，以及 tool logs，預設保留 30 天後清理；named session
與 pending session 最長保留 180 天，避免永久累積。可用 `--retention-days`／
`NETZOO_RETENTION_DAYS` 調整一般期限，並用 `--session-hard-retention-days`／
`NETZOO_SESSION_HARD_RETENTION_DAYS` 調整所有 session 的硬期限。

## 結構化執行與修復

Executor 會把既有工具文字統一轉成 `ToolExecutionResult`，包含 `status`、
`artifacts`、`metrics`、`warnings`、`errors`、`retryable` 與 `recovery_hint`。
Evaluator 不再直接依賴 LLM 判讀工具輸出。已允許的自動修復會限制最多兩次；例如
PUMA expression header 不相容時，可插入 `format_expression -> inspect_inputs ->
run_puma`。無法安全修復的 ID mismatch 會停止，不會盲目重跑。

本機執行型 workflow 的最終結果由 deterministic renderer 產生，不會把完整 stdout
再次送給 OpenRouter。這避免分析已成功後，因 provider 400、context size 或回答模型
暫時失敗而讓 CLI traceback。每個工具的完整輸出保存在 `.netzoo/logs/`；CLI 與模型
只接收有界摘要。文件查詢等仍需要 LLM 的節點也有 exception fallback。外部
Context7/Websearch 內容使用低信任 data message，不會與 system policy 合併。

每次 Router／回答模型呼叫會保存 `token_usage`；provider 沒提供 usage metadata 時會
以字元數估算並標記 `estimated=true`。`NETZOO_MAX_TASK_TOKENS` 是跨 clarification 的
任務預算，Router 與回答模型另有 `NETZOO_ROUTER_MAX_TOKENS`、
`NETZOO_RESPONSE_MAX_TOKENS` 與 `NETZOO_LLM_TIMEOUT_SECONDS`。`--verbose` 會顯示
本次 input、output、total 與 budget。LLM request 預設 30 秒且不做 provider retry；
Router timeout 後會採 deterministic fallback，避免一次 provider 故障累積成數分鐘。
Router structured output 不建立 parallel raw-response branch，因此 Ctrl-C 不會等待
LangChain thread pool 重複 shutdown。Router 與 response model 透過 `ChatOpenAI`
直接連到 OpenRouter 的 OpenAI-compatible endpoint；不要改回目前會錯置 timeout 單位、
並在 zero-retry 時啟用長時間 SDK retry 的 `ChatOpenRouter` adapter。

## 本機三層 trace 基礎

每趟任務會先建立 `.netzoo/traces/<run_id>/events.jsonl`，再開始下一個 Agent 邊界。
事件使用遞增 `sequence`、`previous_hash` 與 `event_hash`，包含 graph node、typed decision、
plan gate、tool、Evaluator、recovery、LLM usage 與 budget event。這些是可稽核的結構化
理由與狀態差異，不是模型的隱藏 chain-of-thought。

事件在第一次本機寫入前會遮蔽 API key、Authorization、cookie、password、private key
與常見 credential。Trace 目錄權限為 `0700`，JSONL、manifest 與 quarantine 檔案為
`0600`。雲端 Dashboard 尚未連接時，本機 JSONL 仍是完整 source of truth。

不需 API key 即可驗證或匯出 trace：

```bash
python scripts/netzoo_agent.py --trace-status RUN_ID
python scripts/netzoo_agent.py --trace-export RUN_ID audit.tar.gz
```

匯出不會覆蓋既有檔案。已 sealed 的 trace 預設保存 90 天，可用
`--trace-retention-days` 或 `NETZOO_TRACE_RETENTION_DAYS` 調整；pending、未 sealed、
corrupt 與 `trace_degraded` run 不會被自動刪除。

每任務 token hard limit 預設是 20,000：14,000 顯示第一級警告，17,000 顯示第二級警告，
並保留 1,500 tokens 給必要收尾。呼叫前若預測會超過可用額度，系統寫入
`budget.blocked` 並不送出 provider request。Provider 回報的 token／cost 標示為
`actual`；依 `NETZOO_MODEL_PRICING_JSON` 快照計算者標示為 `estimated`；沒有可信價格時
標示為 `unavailable`，不會填入假的零成本。

價格設定以 exact model name 為 key，金額單位為每百萬 tokens 的 micro-USD：

```json
{
  "openai/gpt-4o-mini": {
    "input_micro_usd_per_million": 150000,
    "output_micro_usd_per_million": 600000,
    "effective_at": "2026-08-03T00:00:00Z"
  }
}
```

直接給任務，但先不真的執行工具：

```bash
docker compose run --rm \
  -e OPENROUTER_API_KEY="$OPENROUTER_API_KEY" \
  netzoo python scripts/netzoo_agent.py \
  --task "我要用 data/expression.tsv data/motif.tsv data/ppi.tsv 跑 PANDA，輸出到 outputs/panda.tsv"
```

真的執行必須進入互動模式，明確切換後再輸入任務：

```bash
./netzoo-chat
```

```text
[TEST] What would you like to accomplish with NetZoo?
> /
Select NetZoo mode
❯ Test mode — preview commands only
  Execute mode — run validated commands

↑/↓ move · Enter select · Esc cancel
```

Press `/` at an empty prompt to open this primary mode selector. `/execute` and
`/test` remain typed alternatives. Path prompts intentionally do not open the
menu, so absolute paths can be typed without being interpreted as commands.

`--task` 是非互動 preview-only 介面，不接受 `--execute`。

PUMA 的 `miRNA` 檔案是每行一個 regulator 名稱的清單；miRNA-target 邊應放在
motif/prior 檔案中，清單內的名稱必須出現在 motif/prior 第一欄。

格式 gate 也會拒絕 miRNA header、空白行、重複 ID、多欄資料，以及不存在於
motif/prior 第一欄的 ID。PUMA 與 legacy LIONESS 的 expression 必須是無 header、
gene 在 rows、sample 在 columns，且 LIONESS 至少需要三個 samples。

## 安全設計

預設不執行工具，只回傳它會執行的 command。這是為了避免 LLM 誤解任務時直接跑很久或覆蓋 output。

互動 session 的安全控制：

```text
/execute
/status
/test
```

## Harness scenario evaluation

固定情境集位於 `tests/harness_scenarios.json`，可在不呼叫 LLM 的情況下回歸測試
Planner policy：

```bash
python scripts/evaluate_harness.py
python scripts/evaluate_harness.py --json
```

報告包含 scenario pass rate、plan-status accuracy、input-resolution accuracy、
missing-input accuracy、unnecessary-question count 與 unsafe-autofill count。完整
LangGraph loop 與 `--task -> needs_input -> 使用者補充 -> 繼續執行` 則由 Docker
integration tests 驗證。

## 跟 expression data preprocessing 的關係

expression data 要經過處理才能拿到基因表現 ：

```text
raw FASTQ
  -> QC
  -> trimming
  -> alignment / pseudoalignment
  -> quantification
  -> gene ID mapping
  -> filtering
  -> normalization
  -> expression matrix
  -> PANDA/PUMA
```

PANDA/PUMA 不吃原始 FASTQ。它們吃的是已經整理好的 gene expression matrix。
