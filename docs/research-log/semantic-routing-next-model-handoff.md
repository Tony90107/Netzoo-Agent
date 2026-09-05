# NetZoo semantic routing：下一個模型的完整交接

更新日期：2026-09-05（Asia/Taipei）  
Repository：`/Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent`  
Git HEAD：`b36226d`  
目前狀態：HEAD 之上有尚未 commit 的 E1 工作樹，再加上已完成的 P0 malformed payload 契約；
一次造成 `TypeError` 的 alias 實驗仍維持撤回，不要重做。  
Live 完整語意驗收：最近可評分的 Q1–Q3 仍為 **0/3**。不要用 fixture 結果改寫此數字。

## 給接手模型的第一個指令

你沒有看過此前對話。請先執行並保存結果：

```bash
cd "/Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent"
git status --short
git rev-parse --short HEAD
```

然後依序閱讀：

1. `AGENTS.md`
2. `docs/research-log/sambar-agent-routing.md`
3. `docs/routing-test-strategy.md`
4. 本文件
5. `tests/routing_scenarios.json`
6. `tests/test_input_completeness.py`
7. `scripts/netzoo_agent_core/interpretation/request_integrity.py`
8. `scripts/netzoo_agent_core/interpretation/outcome_validation.py`
9. `scripts/netzoo_agent_core/interpretation/semantic_repair.py`
10. `scripts/netzoo_agent_core/graph/router_invocation.py`
11. `scripts/netzoo_agent_core/routing/outcome_matching.py`
12. `scripts/netzoo_agent_core/interpretation/verified_guidance.py`
13. `scripts/netzoo_agent_core/llm.py`
14. `scripts/workflow_registry.py`

不要先清除 dirty worktree。它包含上一輪 E1 的測試與實作，不是無關垃圾。特別注意
`scripts/netzoo_agent_core/routing/request_signals.py` 是較早存在的未追蹤檔，目前沒有接入
production；不要因為名稱相似就假設它是本輪方案的一部分。

除非使用者另外明確授權，不要呼叫付費模型。先以真實 SDK + `httpx.MockTransport`、fixture
與 production routing seam 重現問題。

## 產品語言規則

- 使用者輸入：中文或英文都必須接受。
- Agent 對使用者的輸出：只可英文，包括回答、進度、錯誤、clarification 與 Next step。
- Semantic evidence 的 `text_span` 是原文證據，可以保留使用者的中文原句；它不是
  user-facing 回答。
- 目前 prompt 已有全域 English policy，deterministic UI 使用 `_ui_text` 擋中文。
  Free-form response model 的完整語言驗證仍未完成。不要只加一個宣稱能判斷「所有英文」
  的 Unicode regex；它無法辨識使用拉丁字母的非英文文字。

## 科學問題與正確語意

### Q1：校正、途徑聚合、距離與分群

使用者有癌症病患 DNA mutation data，要求校正 gene length 與 patient mutation burden，
聚合成 pathway scores，計算病患距離並分群。

期望：

- current input：`mutation_matrix`
- terminal artifact：`sample_cluster_assignment`
- entity：`sample`
- granularity：`aggregate`
- workflow：`run_sambar`
- `pathway_mutation_matrix` 與 `sample_distance_matrix` 是相關／中間產物，不能取代最終
  病患分群標籤。

### Q2：極度稀疏的 somatic mutation matrix

原文保存在 `tests/routing_scenarios.json` 的 `original-q2`。使用者有 200 位肺癌病患的
somatic mutation matrix，99% 為 0，直接 subtyping 沒有生物意義，詢問適合的工具。

期望：

- current input：`mutation_matrix`
- terminal artifact：`sample_cluster_assignment`
- entity：`sample`
- granularity：`aggregate`
- workflow：`run_sambar`
- 回答需解釋 pathway aggregation 如何緩解基因層次稀疏性，但不能保證生物學分群品質。

### Q3：歷史 RNA-Seq／PANDA 與目前 WES mutation matrix

使用者過去成功以 RNA-Seq 跑 PANDA；目前拿到同批病患的 WES somatic mutation matrix，
詢問能否交給 PANDA／LIONESS，最後目標仍是病患 subtyping。

期望：

- 歷史資料：RNA-Seq，只是背景，不能成為目前 input。
- current input：`mutation_matrix`
- 提議但不相容的方法：`run_panda`、`run_lioness_panda`
- terminal artifact：`sample_cluster_assignment`
- workflow：`run_sambar`
- 回答必須明確說明 PANDA／LIONESS-PANDA 的 registered input contract 不接受 mutation
  matrix；不能建議把 mutation matrix 改格式後假裝成 expression data。

完整 labels 與必要／禁止回答文字以 `tests/routing_scenarios.json` 為準。

## 已確認的問題鏈

### 1. 空輸入會讓方法不相容檢查失去依據

此前 live Q1–Q3 都曾保存 `input_artifacts=[]`。已確認的程式路徑是：

```text
input_artifacts=[]
→ rejected_methods_for() 沒有目前輸入可比較
→ rejected_methods=[]
→ Q3 回答沒有 PANDA／LIONESS-PANDA 拒絕說明
```

`exact` 只代表 capability match 狀態，不能代表完整語意正確。空 input 不可視為 compatibility
confirmed。

### 2. 原 validation 只容易檢查「填錯」，不容易檢查「完全漏填」

`_required_evidence()` 主要從 outcome 已填欄位建立證據要求。若 input 與 input evidence
一起被省略，單靠這個機制不一定能知道原文其實明確提過資料。

目前 E1 工作樹新增了 bounded request witnesses，用來對 mutation/expression 的目前、歷史、
假設、否定與 proposed-output mentions 產生 diagnostic。它不自動填 outcome、不選工具，也
不授權執行。

### 3. 主要目標與中間產物曾被混淆

- Q1 曾保存 `sample_distance_matrix`，遺失最終病患分群目標。
- Q3 曾保存 `multi_omic_network`／`sample_specific`，遺失病患分群及 mutation compatibility。

目前 E1 validator 對原文明說的病患分群加入 terminal-goal conflict，但這仍是有界防線。

### 4. Reviewer repair 成功與完整語意正確是兩個指標

Schema-valid review 仍可能漏掉 input、選錯 terminal artifact 或產生不一致 evidence。報告中
必須分開保存：

- schema/evidence validation success
- review repair correctness against gold labels
- route/match status
- final answer assertions
- progress/answer/Next step consistency

### 5. 受測 SDK 沒有刪除 root required fields

真實 SDK + intercepted HTTP body 已確認 structured-output schema 保留 root-level required
fields。不要再次把問題預設成 SDK 刪欄位，也不要放寬 schema。

## 已撤回的失敗實驗：不要重做同一方案

在上一個工作樹之上曾加入一個 `InputModality -> ArtifactType` alias 查表，試圖在
`semantic_payload()` 取得 SDK raw tool-call arguments 後，把 `somatic_mutation` 轉成
`mutation_matrix`。同一實驗也加入 free-response 的非英文 script guard。

使用者 live 測試後，Q2 在第二次 semantic attempt 拋出 `TypeError`，Router 完全不可用。
Session 與 run：

- session：`a822c3b4`
- run：`8a855968-a085-4249-bedc-f088425e50a1`

Trace：

```text
attempt 1 rejected:
  hypothesis[0].missing_current_input:mutation_matrix
  hypothesis[0].conflicting_evidence:input_artifact=mutation_matrix

attempt 2 failed:
  error_type=TypeError
  validation_issues=[]
```

第一輪 provider call 有正常 usage；第二輪沒有 provider request id、output tokens 為 0，表示
錯誤發生在本地 reviewer processing。已撤回的正規化程式對每個 `input_artifacts` item 直接
執行 dict `.get(item, item)`。如果 malformed provider payload 的 item 是 dict/list，就會因
unhashable value 先拋 `TypeError`，繞過原本 Pydantic validation。Raw reviewer arguments
沒有持久保存，因此「item 確實是 dict/list」仍是強假設，不是已直接觀察的原始值。

這次 alias normalization、English response boundary、相關三項新測試與錯誤的 Log 08 已經
撤回。回退後 E1 focused gate 恢復 139 passed。不要再把 provider raw payload 當成可信、
已符合型別的資料做 lookup。

較安全的下一步是先新增 regression：讓 raw `input_artifacts` 包含 string、dict、list、null
與未知 enum，驗證任何 malformed value 都只會成為可診斷的 schema failure，絕不能升級成
`TypeError` 或 router unavailable。是否需要 alias correction，必須在看到原始 payload 或
更精確錯誤後再決定；不要因 registry 有兩套名稱就直接建立自動轉換。

## 目前 E1 工作樹做了什麼

主要檔案：

- `scripts/netzoo_agent_core/interpretation/request_integrity.py`
  - bounded mutation/expression mention witnesses
  - 區分 current、historical、uncertain、negated、proposed output
- `scripts/netzoo_agent_core/interpretation/outcome_validation.py`
  - `missing_current_input`
  - `noncurrent_input`
  - `terminal_goal_conflict`
- `scripts/netzoo_agent_core/interpretation/semantic_repair.py`
  - 把具體問題與原文 request facts 交給 reviewer
- `scripts/netzoo_agent_core/routing/outcome_matching.py`
  - fallback 使用同一套 current-input witnesses
- `scripts/netzoo_agent_core/interpretation/verified_guidance.py`
  - 空 input 時明示 compatibility `not_assessed`
- `tests/test_input_completeness.py`
  - Q1–Q3、歷史／目前、假設、否定、未提 input、terminal goal、method rejection 與
    surface consistency 對照

這些測試是 scripted semantic replies，不是 live-model accuracy。

## 目前已知 live 歷史

### `b36226d` 後、E1 前的三題

- Q1、Q2 UI 顯示 `exact`；Q3 `fallback`。
- 三題都推薦 SAMBAR。
- 三題保存的 `input_artifacts` 都是 `[]`。
- Q1 保存 distance，而不是 terminal cluster assignment。
- Q3 保存 multi-omic network，且 `rejected_methods=[]`。
- 依完整 gold fields 計算仍是 0/3。

### E1 工作樹上的 Q1–Q3（alias 實驗前）

- Q1 run：`55c38bc5-207d-4fe5-9386-254384307c06`
- Q2 run：`1c5285fa-a68e-4857-8a8a-5f5ff307fce8`
- Q3 run：`4fbe959b-55f4-406d-b2dd-27c2b04c8a16`
- 三題最後都 fallback SAMBAR；Q3 fallback 能顯示 PANDA／LIONESS-PANDA 不相容。
- Q1／Q2 reviewer attempt 在 `input_artifacts.0` 出現 `literal_error`。
- Q3 第二次仍有 missing input、artifact granularity、conflicting input evidence 與 missing
  sample entity evidence。
- 仍不能算完整語意成功。

### 已撤回 alias 實驗上的最新 Q2

- session `a822c3b4`，run `8a855968-a085-4249-bedc-f088425e50a1`
- 第一輪正確觸發 missing input，但第二輪本地 `TypeError`，比原本 strict-validation fallback
  更差。
- 此結果是決定回退的直接原因。

`.netzoo/sessions` 與 `.netzoo/traces` 是本機 ignored runtime records；如果交接到另一台機器，
它們可能不存在。以上已保存可攜帶的必要 observation，但不要把沒有 raw payload 的推論
寫成確定事實。

## 建議改進順序

### P0：先維持可診斷失敗，禁止本地 TypeError（已完成，2026-09-05）

四項要求都已實作並有 red→green 測試，見 Log 08 與
`tests/test_malformed_payload_contract.py`（93 項）。摘要：

1. malformed raw payload matrix regression 已建立，涵蓋 17 種形狀 × 兩個 contract、
   production routing 與真 SDK `parsed=None` 路徑。
2. `contracts/outcomes.py` 的 `OutcomeHypothesis` normalizer 與 `semantic_payload()`
   都在 lookup 前做型別檢查。
3. 未知形狀原樣交給 strict Pydantic validation；兩輪皆失敗時 `match_basis` 不再是
   `provider_unavailable`。
4. `_validation_issue_types()` 追加 `input_type`（僅型別名稱）。

重要更正：造成 `TypeError` 的六種形狀來自 `contracts/outcomes.py`，**`b36226d` 就已存在**，
不是 alias 實驗獨有。但這不代表已撤回的 alias 實驗當時的 `TypeError` 就是同一行；
原始 arguments 沒有保存，兩者只是同一類缺陷。

仍未解決：`input_type` 只會在**未來**的失敗中累積證據，無法回溯解釋既有 trace；
Q1／Q2 先前 `literal_error` 的實際值仍然未知。

### P1：將 data mentions 變成明確語意契約

目前 bounded regex 無法涵蓋任意回指、跨句時態、複雜否定與所有資料模態。較完整的設計
方向是讓 semantic interpretation/review 明確產生 data-mention inventory，例如：

```text
text span
canonical artifact or unknown
role = current_input | historical | hypothetical | negated | proposed_output
resolved reference / rationale
```

再由 deterministic validator 檢查：所有 `current_input` mentions 必須出現在 outcome
`input_artifacts`，其他角色不得被放入目前輸入。這仍不能證明模型沒有漏掉 mention，因此需
保留獨立 reviewer 與原文 evidence audit。Schema 變更要先寫 failing tests，不能用 optional
field 假裝完成。

### P2：終端科學目標與多產物關係

目前只有一個 primary `artifact_type`，中間產物主要靠 assumptions/guidance 表達。需要明確
決定是否加入 typed deliverable relationship，例如 terminal、intermediate、supporting，並
用 Q1「距離後分群」、只要距離的反例、Q3「網路只是提議方法」測試。不要用 workflow 的
default output 覆寫使用者目標。

### P3：方法不相容必須依 current input

只有經語意契約確認的 current input 才能觸發 method rejection。方法名稱不能推導 input；
歷史 RNA-Seq 不能覆寫目前 WES。缺 input 時應顯示 `not_assessed`，而不是空陣列後靜默視為
相容。

### P4：中英文輸入、英文輸出

保留 global prompt policy 與 deterministic `_ui_text` guard。對 free-form response 建立完整
production-boundary tests，至少包含：

- 中文輸入、英文 model output：通過。
- 英文輸入、英文 model output：通過。
- 中文或英文輸入、中文 model output：不得顯示中文。
- router/provider error、clarification、progress、Next step 都是英文。
- 科學符號、gene names 與原文 evidence 不應被錯殺。

若沒有可靠的英文語言辨識器，不要宣稱 Unicode script check 能保證所有輸出都是英文。

### P5：更新過時的完整測試基線

完整環境在 `b36226d` 已有 16 個失敗；E1 工作樹也是相同 16 個 ID。它們包含 graph
integration expectations、response ownership 與 BONOBO argument defaults。這些失敗會降低
新回歸的辨識力，應另開工作清理，但不要在 semantic fix 中順便大改。

## 2026-09-05 第二輪之後的狀態更新

- P0 已完成（見 Log 08）。
- 從本機 `.netzoo/traces` 回收到兩項先前認為無法回溯的事實：已撤回 alias 實驗的
  `TypeError` 確實發生在 `semantic_payload()` 內（`raw` 未指派、無 provider request id），
  且 **E1 的 validator 在真實模型上三題都正確觸發**。剩餘 live 阻塞點只有
  reviewer 對 `input_artifacts.0` 回覆非法 literal。原始 arguments 沒有保存，該值仍未知。
- 已補上封閉 artifact 詞彙（prompt／schema／repair feedback 三處，全部由 ontology 導出）
  與只限識別字形狀的 `input_value` 診斷，見 Log 09。
- `executor_arguments` 的非文字選填參數型別缺陷已修（真實 BONOBO 執行路徑會失敗），
  並刪除 DRAGON 專屬分支。
- 既有 16 個失敗已處理 13 個；剩 3 個需要產品判斷，列於 Log 09。
- **live Q1–Q3 仍未重測，完整語意仍為 0/3。** 詞彙介入是否有效只能由 live 判定。

## 不可接受的修正

- 不要一律把 input 填成 `mutation_matrix`。
- 不要從 SAMBAR、PANDA、LIONESS 等工具名稱推導目前 input。
- 不要把歷史 RNA-Seq 當成目前 WES input。
- 不要用 SAMBAR 專屬 if/else 取代通用語意契約。
- 不要把空 input 視為 compatibility confirmed。
- 不要放寬 schema、吞掉 Pydantic error 或跳過 strict validation。
- 不要在 strict validation 前對未檢查型別的 raw provider value 做 dict/set lookup。
- 不要用工具預設產物覆寫 terminal scientific goal。
- 不要把 fixture success 宣稱為 live model accuracy。
- 不要因 UI 顯示 `exact` 就判定完整語意通過。
- 不要未經使用者明確授權呼叫付費模型。
- 不要刪除或重寫失敗研究紀錄；新增 observation 應追加並保留當時狀態。

## 測試方法與目前基線

使用既有 acceptance environment：

```bash
/private/tmp/netzoo-schema-qa.AW2MQ5/venv/bin/python -m pytest -q \
  tests/test_malformed_payload_contract.py \
  tests/test_input_completeness.py \
  tests/test_agent_module_boundaries.py \
  tests/test_outcome_validation.py \
  tests/test_routing_evaluation.py \
  tests/test_semantic_provider_wire.py \
  tests/test_missing_required_repair.py \
  tests/test_terminal_pty.py \
  tests/test_terminal_input.py \
  tests/test_semantic_repair_interaction.py \
  --fail-on-skip
```

目前結果：**232 passed、0 failed、0 skipped**（P0 前為 139）。

完整非 Docker 套件：

- `b36226d` baseline：842 passed、16 failed、0 skipped
- E1 工作樹：881 passed、16 failed、0 skipped
- E1 + P0（目前）：974 passed、16 failed、0 skipped
- 三者失敗 ID 相同，保存在 `docs/research-log/e1-offline-validation.json` 與
  `docs/research-log/p0-malformed-payload-validation.json`

Opt-in Docker scientific test 尚未執行。Ruff 與 `git diff --check` 應在每次修改後執行。

## 下一輪建議的第一個 TDD 任務

上一輪的第一個 TDD 任務（P0 malformed payload 安全底座）已完成，不需重做。下一個是 P1：
把 data mentions 變成明確語意契約。仍然不要立刻直接調 routing accuracy。

建議做法：先寫 failing tests，要求 semantic interpretation/review 產生 typed data-mention
inventory（text span、canonical artifact 或 unknown、role、resolved reference），再由
deterministic validator 檢查 current_input 的完整性與非 current 角色的排除。schema 變更
不可用 optional field 假裝完成。

仍然不要先假設 Q1／Q2 的 literal error 一定是 `somatic_mutation`；現有 trace 沒有保存
原始值。是否需要任何 canonical 名稱對映，必須等 `input_type` 在真實失敗中累積證據之後
再決定。

完成離線測試後，回報應分開列出：

- 根因證據與仍屬推論的部分
- failing test 的原始失敗
- 修正後 focused/full 結果
- baseline failures 與 skips
- 是否呼叫 live model，以及明確呼叫數
- live Q1–Q3 是否真的重測
- 尚未解決的語言與語意泛化風險

在使用者授權 live 測試以前，正確結論仍是：「離線安全契約改善，真實模型完整語意為最近
觀察的 0/3，尚未證明 E1 完成。」
