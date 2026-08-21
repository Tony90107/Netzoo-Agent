# NetZoo Agent 從頭到尾如何運作

## 核心概念

這份 NetZoo agent 不是讓 LLM 自由決定並執行指令，而是一條「有規則、有證據、有執行
門禁」的 workflow pipeline：

```text
使用者需求
→ 載入政策與記憶
→ 理解意圖
→ 建立有證據的計畫
→ 程式碼審核計畫
→ 逐步執行
→ 每一步評估
→ 必要時進行有限修復
→ 保存結果
→ 回覆使用者
```

最重要的設計是：

> Planner 只能提出計畫，不能批准自己的計畫。只有 Plan Evaluator 通過後，
> Executor 才能取得執行權。

---

## 一、Agent 從哪裡開始？

使用者執行：

```bash
python scripts/netzoo_agent.py
```

外層的 `scripts/netzoo_agent.py` 只負責兩件事：

1. 保留舊 CLI 與 `import netzoo_agent` 相容性。
2. 把控制權交給 `netzoo_agent_core/cli.py`。

真正的 agent 邏輯位於：

```text
scripts/netzoo_agent_core/
```

CLI 會先解析：

- 使用者 task
- 是否使用 `--execute`
- Router model 與 response model
- token budget
- profile
- session／resume
- memory 與 retention 設定
- verbose／quiet 顯示模式

預設沒有 `--execute` 時，agent 只能產生 command preview，不能真的執行 PANDA、PUMA、
LIONESS 或 CONDOR。

---

## 二、建立 LangGraph

CLI 接著呼叫 `netzoo_agent_core/graph.py` 的 `build_graph()`。

完整 graph 是：

```text
START
  ↓
apply_project_policy
  ↓
retrieve_memory
  ↓
classify
  ↓
plan
  ↓
evaluate_plan
  ├─ approved → execute_tool
  └─ rejected/deferred → consolidate_memory
                         ↓
execute_tool → evaluate ─┬─ continue → execute_tool
                         ├─ replan → recover → execute_tool
                         └─ completed/failed → consolidate_memory
                                                ↓
                                             respond
                                                ↓
                                               END
```

整個流程共用一個 `AgentState`，它會保存：

- 對話 messages
- Router decision
- WorkflowPlan
- PlanEvaluationResult
- current step
- ToolExecutionResult
- 最終 EvaluationResult
- profile 與 episodes
- project policy
- token usage
- recovery 次數

這些資料都有 typed contract，不是隨意拼接的文字。

---

## 三、第一關：載入 Project Policy

Agent 先讀取：

```text
AGENTS.md
workflows/*.yaml
scripts/workflow_registry.py
```

三者的角色不同：

- `workflow_registry.py`：真正的 Python 權限來源。
- `workflows/*.yaml`：每個 workflow 的可驗證規格。
- `AGENTS.md`：跨 workflow 的人類可讀慣例。

`ProjectPolicyLoader` 會確認：

- policy version 是否受支援。
- YAML action 是否完整對應 Python allowlist。
- required inputs 是否完全一致。
- validation steps 是否一致。
- execution action 是否一致。
- workflow directory 是否仍位於專案內。

如果 YAML 想移除 required input、加入未知工具，或放寬 Python 規則，agent 會直接拒絕
啟動。

驗證成功後，系統會建立：

- `ProjectPolicySnapshot`
- SHA-256 `policy_hash`

之後每個 plan 都可以綁定這個 policy hash，確認它是依哪一版政策建立的。

---

## 四、第二關：載入使用者記憶

`retrieve_memory` 會載入兩種記憶。

### 4.1 UserProfile

只保存使用者明確確認過的長期偏好，例如：

- 預設 output directory
- 是否允許 demo autofill
- 是否重用上次 inputs
- 偏好的 workflow

LLM 不能直接寫入偏好。它只能提出 proposal，之後必須由使用者回答 `yes`。

### 4.2 Episode

Episode 是過去任務的精簡結果，例如：

- 跑了哪個 workflow
- 成功、失敗或 dry-run
- 使用了哪些 input roles
- 產生哪些 artifacts
- 遇到什麼錯誤
- 是否做過 recovery

它不保存完整 dataset，也不把完整 stdout 放進長期記憶。

---

## 五、第三關：Router 理解使用者需求

例如使用者說：

```text
請用 data/study/expression.tsv、motif.tsv 和 ppi.tsv 跑 PANDA
```

Router LLM 不會直接產生 shell command。它只輸出一個小型 `RouterDecision`：

```text
action
in_scope
intent_type
confidence
reason
recommended_actions
```

例如：

```text
action = run_panda
intent_type = run_analysis
confidence = 0.96
```

接著 deterministic Python code 會再進行三個步驟。

### 5.1 Hydration

`hydrate_router_decision` 會：

- 從使用者原文解析 paths。
- 解析 web query 或 docs query。
- 解析 preference proposals。

### 5.2 Repair

`repair_router_decision` 會：

- 修正已知的 LLM routing 漏判。
- 區分「我想知道怎麼做」與「請你現在執行」。
- 將 sample-specific miRNA network 等目標映射到 PUMA＋LIONESS-PUMA。

### 5.3 Capability gate

`enforce_capability_gate` 會檢查：

- action 是否受支援。
- confidence 是否達到門檻。
- 使用者是否真的授權執行。
- 使用者是否只是詢問概念。

因此，LLM 即使分類錯誤，後面仍有 deterministic repair 與 capability gate。

---

## 六、第四關：Planner 建立計畫

Planner 的主要 interface 是：

```python
build_workflow_plan(...) -> WorkflowPlan
```

它接收：

- `TaskDecision`
- 使用者原始 task
- UserProfile
- retrieved Episodes
- ProjectPolicySnapshot

並產生一份 typed `WorkflowPlan`。

### 6.1 Planner 如何尋找 inputs？

優先順序是：

1. 使用者明確提供的 path。
2. Router 解析出的 path，但該 literal 必須真的出現在使用者原文。
3. 使用者已確認允許時，重用成功 episode 的 inputs。
4. 明確 demo/test request 才能尋找 coherent demo bundle。
5. 從 expression 所在 dataset directory 尋找相關檔案。
6. 再搜尋專案 `data/`。
7. 只有候選明顯唯一時才自動採用。
8. 無法安全判斷時標為 `missing`。

這可以防止 Router 幻覺出一條 workspace path，然後把它冒充成使用者提供的資料。

### 6.2 Evidence ledger

每個 required field 都必須有來源證據：

| Evidence status | 意義 |
|---|---|
| `provided` | 使用者原文真的提供 |
| `selected` | 使用者從候選中明確選擇 |
| `discovered` | Planner 找到明確最佳候選 |
| `demo_bundle` | 明確 demo request 的完整相容資料組 |
| `defaulted` | 只用於可逆的 output location |
| `missing` | 無法安全決定 |

例如：

```text
expression_file: provided
motif_file: discovered
ppi_file: discovered
output_file: defaulted
```

每筆 evidence 都包含：

- field
- value
- reason
- candidates

### 6.3 Planner 的四種結果

`WorkflowPlan.status` 可能是：

- `ready`：inputs 完整，可以送審。
- `needs_input`：仍缺必要資料。
- `needs_confirmation`：等待使用者確認長期偏好。
- `respond_only`：只回答問題，不需執行工具。

如果有 missing input：

```text
should_execute = false
steps = []
status = needs_input
```

因此 missing plan 不可能直接進入 Executor。

### 6.4 Ready plan

PANDA 通常會產生：

```text
1. inspect_inputs
2. run_panda
```

PUMA：

```text
1. inspect_inputs
2. run_puma
```

CONDOR：

```text
1. inspect_condor_inputs
2. run_condor
```

Planner 只能放入 typed action，不能直接插入任意 bash command。

---

## 七、Planner 如何把計畫交給 Plan Evaluator？

這是整個系統最重要的 seam。

Planner 不會傳 Markdown，也不會傳一段「我覺得這個計畫很好」的自然語言。

它傳的是：

```python
{
    "plan": plan.model_dump(),
    "decision": plan.decision,
    "current_step": 0,
    "tool_results": [],
    "replan_count": 0,
}
```

下一個 `evaluate_plan` node 會重新驗證：

```python
plan = WorkflowPlan.model_validate(state["plan"])
```

然後呼叫：

```python
evaluate_workflow_plan(
    plan,
    user_task,
    project_policy,
)
```

也就是說，Plan Evaluator 收到的是：

- 經 Pydantic 驗證的 `WorkflowPlan`
- 使用者原始 task
- active project policy

而不是 Planner 顯示給人看的 Markdown。

### 7.1 Plan Evaluator 檢查九件事

#### 1. `intent_and_capability_alignment`

使用者目標是否真的授權這個 action。

#### 2. `required_input_evidence`

每個 required input/output 是否都有一致 evidence。

#### 3. `evidence_provenance_contract`

- `provided` path 是否真的出現在使用者原文。
- demo data 是否只用於明確 demo request。
- default 是否只用於 output。

#### 4. `path_hygiene`

Path 是否混入句號等 parsing artifact。

#### 5. `step_allowlist`

每個 step 是否位於 Python allowlist。

#### 6. `validation_and_execution_order`

Steps 是否完全符合 workflow spec。

#### 7. `output_non_overwrite`

Output 是否會覆寫 input。

#### 8. `planner_state_consistency`

`ready`、`should_execute`、missing inputs 和 steps 是否一致。

#### 9. `project_policy_binding`

Plan policy hash 是否等於 active policy hash。

Evaluator 回傳：

```text
approved
deferred
rejected
```

只有同時符合：

```python
evaluation.status == "approved"
and plan.status == "ready"
and plan.steps
```

Graph 才會走向 Executor。

所以 Planner 沒有辦法批准自己的計畫。

---

## 八、Executor 如何執行？

Executor 一次只處理一個 `WorkflowStep`。

它會：

1. 從 state 取出 `current_step`。
2. 從 `plan.decision` 重建 `TaskDecision`。
3. 把 action 改成目前的 step action。
4. 套用該 step 的 typed arguments。
5. 呼叫 `execute_selected_tool()`。
6. 將文字輸出轉成 `ToolExecutionResult`。

### 8.1 Dry-run

沒有 `--execute` 時：

```text
EXECUTE_TOOLS = False
```

Input inspection 仍可執行，但 PANDA、PUMA、LIONESS、CONDOR 分析只會產生 command
preview。

### 8.2 真正執行

有 `--execute` 時，adapter 才會呼叫 subprocess。

即使 process exit code 是 0，Executor 還會確認預期 output 是否真的建立或更新。沒有產物
仍會被視為失敗。

---

## 九、ToolExecutionResult

Executor 不會把 raw terminal text 直接丟給 Evaluator 猜測，而是先轉成：

```text
action
status
summary
artifacts
metrics
warnings
errors
retryable
recovery_hint
log_file
raw_output
```

`status` 只有：

- `success`
- `dry_run`
- `failed`

過長 stdout 會被截斷，完整內容寫入 private log，避免 graph state 和 LLM context
無限制增長。

---

## 十、Result Evaluator 決定下一步

`evaluate_step_result()` 讀取 typed result 後，可能回傳：

| 狀態 | 下一步 |
|---|---|
| `continue` | 執行下一個 planned step |
| `completed` | workflow 完成 |
| `failed` | 停止 |
| `replan` | 進入 allow-listed recovery |

例如 PANDA：

```text
inspect_inputs 成功
→ continue
→ run_panda
→ completed
```

如果 input validation 失敗：

```text
inspect_inputs failed
→ failed
→ 不執行 run_panda
```

### 10.1 Recovery

目前有一個具體 recovery：

```text
PUMA 不接受 expression header
```

Agent 可以插入：

```text
format_expression
→ inspect_inputs
→ retry run_puma
```

但 recovery：

- 只能使用固定 allowlist。
- 最多兩次。
- 修復後必須重新驗證。
- LLM 不能自由發明 shell command。

---

## 十一、保存 Episode

Workflow `completed` 或 `failed` 後，`consolidate_memory` 才會保存 compact episode。

以下情況不會被誤記成完成的分析：

- `needs_input`
- `needs_confirmation`
- rejected plan
- 純概念問答

Episode 可以協助未來檢索，但不能擴張工具權限。

---

## 十二、如何產生最後回答？

### 12.1 本機 workflow

PANDA、PUMA、LIONESS、CONDOR 有 structured results 時，優先使用 deterministic
renderer。

它會忠實顯示：

- 使用了哪些 inputs
- inputs 是 provided、discovered 還是 demo
- validation 是否通過
- 是 dry-run 還是真執行
- command preview
- outputs
- errors 和 logs

這樣即使 response LLM provider 故障，已完成的本機分析也不會因摘要失敗而被錯誤宣稱
為未完成。

### 12.2 概念問題或 Websearch

這類工作可以交給 response LLM，但 context 被分成：

- trusted typed harness state
- user task
- untrusted external retrieval content

Websearch 或文件內容不能變成 system instruction，也不能要求 agent 執行額外工具。

---

## 十三、缺資料時如何續跑？

如果 Planner 回傳 `needs_input`：

1. CLI 保存 session。
2. 顯示 clarification wizard。
3. 使用者選擇候選或輸入 path。
4. 系統產生 canonical continuation。
5. 重新走 Router、Planner 和 Plan Evaluator。

它不會直接修改舊 plan 後跳過審核。

使用者也可以執行：

```bash
python scripts/netzoo_agent.py --resume latest
```

繼續未完成的 session。

---

## 十四、用一個 PANDA 範例串起完整流程

使用者說：

```text
請用 data/study/expression.tsv 跑 PANDA
```

完整過程是：

```text
1. Policy Loader
   確認 PANDA 規格需要 expression、motif、PPI、output。

2. Memory Retrieval
   載入 profile 和相關 episode。

3. Router
   判定 action=run_panda、intent=run_analysis。

4. Deterministic Hydration
   從原文取得 expression path。

5. Planner
   expression = provided
   motif = 從同資料夾 discovered
   PPI = 從同資料夾 discovered
   output = defaulted

6. Planner 建立 steps
   inspect_inputs → run_panda

7. Plan Evaluator
   檢查 evidence、allowlist、順序、output collision、policy hash。

8. 若 approved
   Executor 執行 inspect_inputs。

9. Result Evaluator
   validation 成功 → continue。

10. Executor
    無 --execute：產生 PANDA command preview。
    有 --execute：執行 PANDA。

11. Result Evaluator
    最後一步成功 → completed。

12. Memory Consolidation
    保存 compact PANDA episode。

13. Response
    回報 inputs、validation、dry-run/execute 狀態與 outputs。
```

---

## 十五、為什麼要這樣設計？

這個 agent 處理的不是單純聊天，而是可能接觸研究資料並啟動分析程式。

如果只使用：

```text
User → LLM → Shell
```

風險包括：

- LLM 猜錯檔案。
- 漏掉 required input。
- 把 toy data 當正式資料。
- 跳過 validation。
- 覆寫 input。
- 誤判 command 成功。
- 無限制 retry。

目前架構將責任拆成：

```text
LLM 負責理解
Planner 負責提出計畫
Plan Evaluator 負責授權
Executor 負責照計畫執行
Result Evaluator 負責控制下一步
```

因此每個角色都只有有限權限。

---

## 十六、常見問題

### 1. 如果 Router LLM 判斷錯誤怎麼辦？

後面仍有：

- deterministic hydration
- repair
- capability gate
- Planner evidence contract
- Plan Evaluator

Router 的輸出不是最終執行授權。

### 2. Evaluator 也是 LLM 嗎？

目前不是。

Plan Evaluator 與 Result Evaluator 主要由 deterministic Python code 執行，因為 required
inputs、step order、path collision 和 exit status 都應該可重現。

### 3. 這已經能完全無人監督執行大型研究嗎？

還不能。它目前是 robust research prototype，仍缺：

- LangGraph node-level durable checkpoint
- 長任務取消與資源限制
- 完整 reproducibility manifest
- 更深入的科學產物品質驗證
- 真實研究 dataset 的 golden tests

---

## 十七、兩分鐘口頭報告版本

這份系統的核心不是讓 LLM 自由執行工具，而是把 LLM 放進一條有門禁的研究 workflow。

使用者輸入需求後，agent 會先驗證專案政策，再載入使用者已確認的偏好與過去任務記憶。
接著 Router 只負責判斷使用者想做 PANDA、PUMA、LIONESS、CONDOR，還是只想詢問概念。
Router 不直接產生 shell command；它的結果還會經過 deterministic Python code 修正與
能力檢查。

之後 Planner 會建立一份 `WorkflowPlan`。這份 plan 不只列出步驟，也會為每個 input
記錄來源：是使用者提供、系統發現、demo bundle、安全預設，還是仍然缺少。只要缺少
必要資料，plan 就不會包含可執行步驟。

最關鍵的是，Planner 不能批准自己的 plan。Plan 會以 typed object 交給獨立的 Plan
Evaluator。Evaluator 會檢查使用者授權、required inputs、evidence 來源、工具 allowlist、
執行順序、output 是否覆寫 input，以及 policy hash。只有全部必要條件通過，Executor
才能執行。

Executor 每次只執行一個 approved step，然後把結果整理成 `ToolExecutionResult`。
Result Evaluator 再決定要繼續下一步、完成、停止，或進行次數受限的修復。最後系統保存
compact episode，並用 structured result 回覆使用者。

所以這個 agent 最重要的價值不是「會呼叫很多工具」，而是每次工具執行都有來源、有
計畫、有審核、有結果驗證，而且可以追蹤為什麼做出每一個決定。

---

## 最短心智模型

```text
User task
→ validated policy + confirmed memory
→ small LLM routing decision
→ deterministic TaskDecision hydration/repair
→ evidence-backed WorkflowPlan
→ typed Plan Evaluator gate
→ one allow-listed step at a time
→ structured ToolExecutionResult
→ deterministic Result Evaluator
→ bounded recovery or completion
→ compact memory + truthful response
```

一句話總結：

> Planner 負責提出有證據的計畫，Plan Evaluator 負責授予執行權，Executor 只執行核准
> 的 typed step，而 Result Evaluator 只根據 structured result 決定下一步。
