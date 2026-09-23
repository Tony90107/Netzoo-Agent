# NetZoo semantic routing：待處理問題清單（交接給下一個 agent）

更新：2026-09-23，round 6 之後
專案：`/Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent`
背景：`docs/research-log/2026-09-23-semantic-routing-handoff.md`（F1–F6）；研究紀錄 `docs/research-log/2026-09-23-semantic-contract-routing-session-report.md` §19–§22（含 F7）

## 開始前必讀

- **工作樹全部未 commit**，混有前一個 session 的修改。不要 reset／checkout／revert 不相關檔案。
- 基線：
  - `~/.venvs/netzoo-qa/bin/python -m pytest -q` → 2094 passed、35 skipped。
  - Ruff：只有 `scripts/netzoo_agent_core/routing/candidate_ranking.py` 一個 HEAD 既存的 F401。
- 專案規則：
  - **禁止以 system prompt 措辭誘導模型行為**；只能改契約形狀、確定性驗證規則、registry／本體宣告或 witness 詞彙。
  - Code discovery 優先用 Codebase Memory MCP（見 `AGENTS.md`）。
  - gpt-4o-mini live round 已預先授權；gpt-4o 要先問使用者。
  - 每次 live round **之前**，把判準（以結構性計數為主）寫進研究紀錄。
  - 分數差 ≤ 4 不下結論：legacy 程式不變時，32 題分數曾跨輪變動 74→70。
  - 使用者以英文操作：**英文失敗優先**，中文題只當回歸防護。
  - 修改 routing／matcher 時，要做「重放已記錄 trace」與「generated grid 前後比對」兩種離線驗證。

## 工具

- Traced live 擷取：
  ```bash
  set -a; . ./.env; set +a
  ~/.venvs/netzoo-qa/bin/python docs/research-log/live-semantic-trace-2026-09-23-harness.py <legacy|claims> 3 <out.json> tests/routing_semantic_families.json [case,ids]
  ```
  一輪（兩契約、原 8 題＋32 題）約 25 分鐘、約 600 次呼叫。
- 最新一輪 trace：`docs/research-log/live-semantic-trace-2026-09-23-round6-{orig8,families32}-{legacy,claims}.json`。每個 trial 的 `_trace` 內有 provider I/O 與 routing events。
- Evaluator summary 已有 `wrong_exact_recommendations`、`wrong_fallback_recommendations`，每輪都要報。
- 語料：原 8 題 `tests/routing_semantic_variants.json`；32 題四家族 `tests/routing_semantic_families.json`；主語料 `tests/routing_scenarios.json`。

## 目前狀態（round 6）

| | Legacy | Claims |
| --- | ---: | ---: |
| 原 8 題 | 22/24 | 20/24 |
| 32 題 | 75/96 | 59/96 |
| 錯誤推薦（exact＋fallback） | 0 | 0 |
| unsafe execution | 0 | 0 |

Claims 仍不升為 production default。

---

## 問題清單（依優先順序）

### P1. 「同時含 miRNA 與 TF 調控」的請求沒有答案（英文，兩契約）

- **現象**：`role-both-agg-en`、`role-both-ss-en` 兩契約都 0/3。F7 之後不再錯推 DRAGON／GIRAFFE，但變成被拒、沒有推薦。
- **已知根因**：模型把 "a network of both miRNA and TF regulation of genes" 判成 `multi_omic_network` 或 `regulatory_network_and_tf_activity`。`stated_roles_conflict` 正確攔下，但 reviewer 沒有把 artifact 改回 `regulatory_network`。
- **待查**：用 round 6 trace 看 reviewer 收到的 `repair_feedback`／`request_facts` 與它的回應，判斷是 feedback 沒指出目標 artifact、reviewer 忽略，還是之後又被別的規則擋。
  - Claims 的結構化 feedback 在 `interpretation/claim_prompt.py::claim_repair_feedback`。
  - Legacy 的在 `interpretation/semantic_repair.py::repair_feedback`。
- **方向**：`stated_roles_conflict` 目前只給 `repairable_fields=[artifact_type]`，沒有目標值。可以研究能否由本體**確定性地**推出「承載所陳述 regulator→target 角色的網路 artifact」，並作為 `required_value` 給出。不要改 prompt 措辭。
- **驗收**：兩題至少 2/3 得到 PUMA／LIONESS-PUMA；錯誤推薦維持 0；`bipartite-communities`（CONDOR）不受影響。

### P2. TF 的 per-sample 請求被判成 TF-activity artifact（英文，主要是 claims）

- **現象**：`role-tf-ss-en`（claims 0/3）、`gran-tf-ss-individual-en`（兩契約都低）。模型選了 `regulatory_network_and_tf_activity`，其本體只允許 aggregate，與 per-sample 衝突。
- **根因之一**：witness 抓不到 "separately in each patient"、"For each individual … their own … network"，所以 `request_facts.granularity` 是空的，reviewer 無從判斷該改粒度還是改 artifact。F6 實測 reviewer 會把粒度降成 `unknown`，結果 ambiguous GIRAFFE。
- **方向**：擴充英文 sample-specific witness（`interpretation/request_integrity.py::_GRANULARITY_PATTERNS`）。**必須用不在語料中的新句子驗證**（正例＋反例），避免照著語料調 regex；還要對三份語料做 witness 稽核（witness 與 expected granularity 不得矛盾）。
- **注意**：不要為了修這題而在 claims patch 後開啟 `align_artifact_constraints`。那會把 TF-activity 誤判直接對齊成 aggregate，變成 GIRAFFE 的錯誤 exact。
- **驗收**：兩題改善；錯誤推薦維持 0；witness 稽核為 0。

### P3. Claims reviewer 以「降級」化解本體衝突

- **現象**（F6，研究紀錄 §21.4）：本體衝突類 review 通過驗證 13/25，但真正修對只有 4/25。Reviewer 把被陳述的值改成 `unknown`，或刪掉 evidence。例：`hist-expression-then-mutation-en` 的 artifact 改對了，粒度卻給 `unknown` 而不是 `aggregate`，結果只是 fallback SAMBAR。
- **方向（二擇一或並用，需先寫判準）**：
  1. 若 review 把一個有 request witness 支持的維度降成 `unknown`，或刪掉其 evidence，就丟棄該 review（可沿用 `interpretation/outcome_downgrade.py`）。
  2. 當 artifact 已由確定性 witness 確認（例如 `terminal_goal_conflict` 的目標），才對該 artifact 本體只允許單一值的欄位做對齊。只在這種有 witness 確認的情況做，見 P2 的注意事項。
- **驗收**：本體衝突類 review 的「修對」數上升，不只是「通過驗證」數；錯誤推薦維持 0。

### P4. Legacy 原 8 題的 review 失敗（原因未明）

- **現象**：legacy 原 8 題各輪依序為 20、22、23、18、22。Round 5 的 `mirna-case-lower` 0/3 走 `registry_guidance_fallback`，issue 是 `conflicting_evidence:entity_type=gene`，另有 review 無 issue 卻失敗。當時確認與 F7 無關。
- **待查**：用 round 5 trace（`live-semantic-trace-2026-09-23-round5-orig8-legacy.json`）重放 legacy reviewer 輸出，找出 `conflicting_evidence:entity_type=gene` 與無 issue 失敗的來源。先不要修，先確認根因。

### P5. Claims 的 unmatched evidence 仍遠高於 legacy

- **現象**：32 題 claims 約 60–70 個 unmatched、legacy 0–7。最大宗是 `operation` 的引文，模型把句子改寫後標成 explicit。
- **需要使用者先決定**：guidance 模式的 matching 本來就把 `operation` 抹成 unknown。是否讓 guidance 模式下 `operation` 的引文錯誤不再使整個 interpretation 失效？這是驗證政策，**不要未經同意就實作**；可以先用 trace 估算影響範圍給使用者參考。

### P6. F5（`sample` 不當網路節點）缺少 live 證據

- F5 在 live 上幾乎沒有觸發機會。可以寫一組會誘發 `sample` 節點的**英文** prompt（例如 "one regulatory network per sample where each sample is a node"），加入語料或做小型 targeted round，確認 F5 觸發且行為正確。

### P7. 讓 evaluator 內建 trace 擷取

- 目前 raw provider I/O 只能靠 scratch harness 取得。建議在 `scripts/evaluate_routing.py` 加 `--trace-out <path>`，行為同 harness：記錄 schema、messages、raw tool-call args、parsing_error、finish_reason、usage、invalid_tool_calls、events；system prompt 可以用 hash 取代。
- 加測試，並確認不記錄任何憑證。這是純工程題，可以先做。

### P8. 需要使用者決定的事項（不要自行處理）

- 前一個 session 未 commit 的 claims reviewer prompt 措辭（`interpretation/claim_prompt.py` 中 "Do not return an empty patch … Do not translate or paraphrase a quote"）違反專案規則，traced 結果也顯示無效。是否撤回，由使用者決定。
- F1 反轉了 `tests/test_exact_needs_a_stated_discriminator.py` 原本的設計決定：stated aggregate 現在會選 PUMA。若使用者不同意，要整體回退 F1。
- Commit 分組：本輪修改與前一個 session 的修改要分開。

### P9. 低優先（中文）

- Claims 對中文 `operation` 的壓縮引用（例如 `建立調控網路的方法` 對原文 `建立一張調控網路的方法`）。
- `zh-tf-ss`、`hist-expression-then-mutation-zh`、`zh-compare-patients-ss` 跨輪不穩。
- 只作回歸防護；除非使用者要求，不要優先處理。

## 已修好、不要重做

- F1：stated aggregate 選 PUMA。
- F2：中文否定詞與 witness 假陽性。
- F3：witness 取代弱的 granularity evidence。
- F4：claims repair 改為單一 `hypothesis_index`，重複 index 與 1,200 token 截斷歸零。
- N1：hypothetical 分群目標。
- F6：claims 結構化 feedback。
- F7：`stated_roles_conflict`（無角色網路，或本體排除所陳述的 regulator）、`undecided_granularity`（interpretation 層級）、名詞化角色 witness "X regulation of genes"、錯誤推薦計數。

細節與驗證證據都在研究紀錄 §19–§22。
