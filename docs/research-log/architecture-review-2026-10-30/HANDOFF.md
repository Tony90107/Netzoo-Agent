# 交接：架構 C（候選表）離線原型（2026-10-30）

新 session 請先讀完這份文件，再讀 `docs/research-log/architecture-review-2026-10-30/ANALYSIS.md`（在 `architecture-review` 分支上；也可以用 `git show architecture-review:docs/research-log/architecture-review-2026-10-30/ANALYSIS.md` 讀）。

## 0. 這次的任務

照使用者已經同意的設計，做「架構 C：候選表」的**離線原型**，量出它比現行系統好還是差。**不要改動現行系統**，也不要動 app 的 `.env`。原型要先在看過的題目上離線量測，過關後才出新題組做成對比較。

## 1. 為什麼要做（一段話版）

2026-10-29 用新題組 j8 比較 10-28 版本和現在的版本：39 = 39/48，p = 1.0，整體沒有改善。統計 4 次新題組 live 執行的 35 個錯誤（156 題，正確率約 78%），**沒有一個是合約規則錯**：
- 約 59% 是讀題錯：連錯結果、單一欄位讀錯就把正確答案排除、模糊請求判斷錯、疑點沒偵測到；
- 約 34% 是對話流程錯：多問、重複問、多輪狀態遺失；
- 其餘是服務故障。

現行架構的根本弱點有四個：
- mini 一次自由填一張大表，任何一格錯都會否決；
- 拒絕常常只是讀錯的副產品，不是確認違反了某條合約；
- 每一輪從頭重讀；
- 「沒說明」就提問。

逐題補丁已經出現報酬遞減和連鎖相依（Z20 和 Q18 互卡）。

## 2. 已同意的設計（使用者逐點同意，不要改）

**核心：** 任務狀態是一張「候選結果 × 合約條文」的表，每格是「符合／違反／未知 + 引用原話」。範圍來自合約，不來自讀題。判定完全由程式做。

### 2.1 問題只從合約的**結構化欄位**產生，用固定模板，不從說明文字產生

| 合約欄位 | 模板（封閉選項） |
|---|---|
| 結果：能力表 produces 條目 + `granularity` + `produced_artifacts` | 「使用者要的是哪一個？」選項由程式依尺度產生所有說法：尺度含 aggregate 的結果，產生「用全部樣本一個」和「每組、階段、條件各一個（用該組樣本）」；尺度含 sample_specific 的，產生「每個樣本各一個」；外加「都不是」 |
| `required_inputs` / `required_input_groups`（排除 output） | 「使用者說他有 ＿ 嗎？」有／沒有／沒說 |
| `incompatible_input_artifacts` | 「使用者說他手上有哪種資料？」（用 guard 的 `DATA_CRITERIA` 和 `interpretation/data_has.HAS_INSTRUCTIONS`） |
| 能力表的 expectation（control + value，例如 BONOBO log_transformed） | 「使用者說資料已經 ＿ 了嗎？」是／否／沒說 |
| 結果屬性（signed、regulators、layers、time model、spatial、group membership） | 每種屬性一個固定模板，**對整個請求問一次**，再由程式套用到各候選 |
| 數量（樣本、特徵、設定值） | 不問對錯，只抽出「數字 + 原文」；程式核對數字確實在原文中，再用 `workflow_conditions` 的規則計算（min_samples、數值上限、genes > samples、kmax ≤ samples 等） |

合約的 `conventions` 說明文字**只當拒絕理由的引文，不拿來出題**。R01 失敗，就是因為拿說明文字出題，引用到了不相關的那句。

**上線前先做覆蓋測試：** 把 348 題的標準答案理由逐一對應到模板。對應不到的列成已知缺口。Jev 優先連結那輪會在 live 失敗，就是因為選項沒涵蓋「每組一個」，這種問題要在離線時抓出來。

### 2.2 證據強度（依後果分級）

- **「要的是這個結果」**：必須有原話，而且原話確實存在於請求中，否則不算 DO。
- **「違反」**：原話 + 信心 ≥0.7 → 可以拒絕；有原話但信心不足 → 問是非確認題（引用原話）。
- **必要輸入「沒說」**：不構成阻擋，**也不問**（使用者同意）。真正執行前，系統本來就會要求指定檔案並檢查。
- **必要輸入「說沒有」**：有原話 → 違反（例如 j7 Y14「組裡沒有 PPI 表」）。
- **使用者說「不確定」**：這格是「未知」，而且是決定性的 → 問。
- **原則：沉默不構成阻擋；阻擋一定要有原話；拒絕一定有一條確認違反的合約條文。**

### 2.3 只重讀「決定性格子」

程式對每一格做反事實計算：這格的值反過來，判定會不會改變？會改變的就是決定性格子，通常只有 1–3 格。這幾格由第二個讀者再讀一次（第一次用 Jev 就換 mini，反之亦然）：
- 一致 → 採用；
- 不一致 → 這格變成「未知」：結果格就請使用者說清楚（列出兩個候選），條件格就請使用者確認（引用原話）。

注意：ROUND-15 撤回過「mini 整份讀兩次取一致」。這次是單格、只限決定性格子，不同，但一樣要量。

### 2.4 多輪：原始請求只讀一次，之後只讀新回覆

- 每個提問都綁定一個格子；回覆只用那一格的封閉選項去讀。
- 回覆裡的新資訊，用同一組模板只讀這段回覆，只更新在回覆裡有原話的格子。已經由原話確立的格子，除非回覆明確更正，否則不覆寫；更正時舊值標成已取代並保留。
- 新目標或追問的判斷，沿用現有的分類器。

### 2.5 判定規則（純程式）

- 只剩一個候選結果完全符合（結果格有原話、沒有確認違反、數量檢查通過）→ **DO**
- 有一格未知、而且是決定性的 → **ASK**，只問那一格
- 所有被要求的候選都有確認違反的條文 → **DECLINE**，理由是使用者原話 + 合約條文
- 沒有任何候選被要求 → **CLARIFY**
- 部分可做、部分不可做 → 照現行的 PARTIAL 定義

### 2.6 讀者分工（使用者同意）

- **Jev**（`typesafe/jev-1.13`，`netzoo_agent_core/jev_client.decide`）負責封閉選擇題。
- **gpt-4o-mini**（`OPENROUTER_CAPABILITY_MODEL`）負責抽原話和數字，並當決定性格子的第二讀者。

## 3. 建議的實作步驟（每一步都先寫 ROUND 和 gate 再寫程式）

1. **P0 覆蓋測試**（不呼叫模型）：寫出模板產生器，從合約產生每個候選的格子；用 348 題標準答案理由檢查覆蓋率，列出缺口。
2. **P1 填表器**（研究腳本，放在 `docs/research-log/candidate-table-2026-10-xx/`，**先不要放進 `scripts/`**）：對每題開場請求，用 Jev 或 mini 填表，結果快取在資料夾內。成本估計：一題大約 10–20 個 Jev 封閉題加少量 mini 抽取，348 題約 US$0.5–1。
3. **P2 判定器 + 決定性格子重讀**：純程式判定，算出決定性格子並做第二次讀取。
4. **P3 離線評估（只看第一輪）**：跟標準答案比，算答對數、誤放行、誤拒絕、該問沒問、多問、**錯誤理由數**。基準是現行系統在同一批題目上錄下的第一輪判定（j5a、j6a、j7off、j8new 的 trace，以及 j1–j4 的錄製）。
5. **P4 多輪模擬**：用題目裡的腳本回覆（`reply_fact`、`reply_form`、`reply_confirm`、`reply_result`、`reply_restate`），離線模擬第 2、3 輪的格子更新。
6. **P5 新題組成對比較**（使用者同意後）：出全新封閉題組，現行系統對架構 C，各跑 3 次，事先宣告符號檢定。架構 C 要接進 app 時，必須放在 flag 後面。

建議的 gate 方向（新 session 自己宣告，宣告後不能改）：
- 誤放行不得多於現行系統；
- **每個拒絕都對應一條確認違反的條文**，錯誤理由 = 0；
- 答對數要明顯高於現行系統；
- 多問的次數要報告。

## 4. 可以重用的東西

| 用途 | 位置 |
|---|---|
| 合約結構化欄位 | `scripts/workflow_registry.py` 的 `ACTION_DEFINITIONS`（`required_inputs`、`required_input_groups`、`controls`、`output_capability`：`granularities`、`input_artifacts`、`incompatible_input_artifacts`、`produced_artifacts`、`handoff_targets`）；`workflows/*.yaml`（`input_checks`，帶 `limit` 的是數量規則） |
| 能力表結果與屬性 | `scripts/capability_sheet.yaml`；`netzoo_agent_core/capability_sheet.py`（`sheet_entries`、`entry`：granularity、regulators、signed、layers、input_network、groups、`aggregate_entry`） |
| 宣告類條件 | `netzoo_agent_core/interpretation/expects.py`（`expectations(action)`：control + value） |
| 數量規則 | `netzoo_agent_core/workflow_conditions.py`（`conditions_for`、`data_issue`、`combination_issues`、`setting_issue`） |
| 數字抽取與驗證 | `interpretation/method_conditions.verified_method`、`count_words.py`（`stated_numbers`、`side_by_side`、混合寫法規則） |
| Jev 呼叫 | `jev_client.decide`；guard 的 `DATA_CRITERIA`、`judge_answer`、`ruled_out`、`_typed_contracts`（`graph/jev_guard_call.py`） |
| 「使用者手上有哪種資料」題目 | `interpretation/data_has.py`（已凍結） |
| 合約句錨定 | `interpretation/answer_anchor.anchored` |
| 任務狀態 | `contracts/task_state.py`（v2：`pending`、`facts`、`asked`） |
| 有標準答案的題目 | `docs/research-log/**/j1`…`j8/items.json`（`expected_call`、`workflows`、`reason`、各種 `reply_*`、`final_after_*`）。`data-has-2026-10-29/measure.py` 的 `items()` 可以直接讀全部 348 題 |
| 影子量測範本 | `jev-first-links-2026-10-29/shadow.py`（讀題、Jev 快取、計分）；`data-has-2026-10-29/measure.py` |
| 現行系統的 live 紀錄（基準） | `jev-j5-2026-10-28/live/j5a`、`jev-j6-2026-10-29/live/j6a`、`jev-links-first-2026-10-29/live/j7off`、`j8-paired-2026-10-29/live/j8new`、`j8old`；錯誤分類在 `architecture-review-2026-10-30/wrong.json` |
| live 執行器 | `j8-paired-2026-10-29/run_j8.py`（支援用不同 worktree 跑不同版本）；`score_j8.py`（含符號檢定） |
| 重播 | `docs/research-log/check-reserve-2026-10-28/run_replay.sh OUT off`，跟 `sa-off.json` 比，應逐位元組相同 |

## 5. 目前狀態

- **main = `78071415`**，已推到 `netzoo-agent`（Tony90107/Netzoo-Agent）。這兩天合併的內容：per_group 尺度、per-group-base、agent-answer-anchor、asked-history、has-incompatible（flag 預設關）、confirmed-reason。
- **app `.env`**（`netzoo_agent/.env`，屬於使用者）：`NETZOO_JEV_GUARD`、`NETZOO_JEV_OVERLAP`、`NETZOO_JEV_FORMS`、`NETZOO_AGENT_ANSWERS` 都是 on；`NETZOO_JEV_DATA_HAS` 沒設定（關閉，docker-compose 也還沒傳這個變數）。檢查模型是 `openai/gpt-4o-mini-2024-07-18`。
- **worktree：** `.worktrees/netzoo-j5` 是上一個 session 用的，目前在 `architecture-review` 分支。`.worktrees/netzoo-old` 是 7ad2367f 的舊版（給 j8 比較用的，可以保留）。新 session 請**自己開一個新的 worktree**，例如 `git worktree add ../.worktrees/netzoo-ct -b candidate-table netzoo-agent/main`。
- `netzoo-j5/docs/research-log/check-reserve-2026-10-28/` 底下有幾個沒追蹤的舊重播 json（`ac-off`、`dn-off`、`sa-off` 等）。**`sa-off.json` 是重播比對的基準，不要刪。**
- **所有題組都已看過**（j1–j8、h 系列）。P5 必須出新題組。出題流程照 j6、j7、j8：盲出題子代理 + 盲審子代理 + SHA-256 封存，範本在 `j8-paired-2026-10-29/j8/AUTHOR-BRIEF.md`、`REVIEW-BRIEF.md`、`check_format.py`。

## 6. 常規（必須遵守）

- **用繁體中文回覆使用者**；程式、commit、測試題目用英文。
- **每一輪先寫 ROUND.md 和 gate 並提交，才寫程式。** 先離線測，live 前先問使用者。宣告的硬性 gate 沒過就照停損規則撤回，**事後絕不改 gate**。
- **live 前先列出費用。** gpt-4o-mini 已預先同意；用 gpt-4o 要先問。Jev 很便宜，但也要設上限。
- **不靠改 prompt 措辭修問題**，要改合約或結構的形狀。模板凍結後不再改寫。
- **最高原則：不給錯誤資訊。** 理由無法驗證時，就說「檢查了什麼」，不要說固定的「找不到對應」句子。
- **精簡測試：** 不暴力重跑；先修缺陷，用離線重播和單元測試；live 每次最多約 20 段對話、每題 1 次，並事先告知。
- **flag 預設關閉**；app 的 `.env` 由使用者決定。
- **推送到 `netzoo-agent`，不是 `origin`**，只用快轉合併。合併需要使用者同意。
- **app 資料夾 `netzoo_agent` 裡有使用者大量未提交的檔案（約 2200 行狀態），絕對不要碰。** 合併前確認 `git log netzoo-agent/main..HEAD` 是空的、要改的檔案在 app 資料夾都沒有被修改，然後 `git merge --ff-only`。
- **跑整套測試**：`cd scripts && env -i HOME="$HOME" PATH="$PATH" python3 -m pytest -q -p no:cacheprovider ../tests`。已知有 2 個跟環境有關的失敗（`explicit_panda` characterization、`history_says_which_sessions_can_be_resumed`）。跑完會產生 `scripts/outputs/`，live 前要刪掉，因為 live 執行器會檢查程式是否乾淨。
- **`router_invocation.py`、`capability_check.py` 接近 1000 行上限**（有模組大小測試）。新程式請放在新模組裡。
- **跟 jev-guard session 協調。** 那個 session 叫「Workflow 選擇模糊狀況與 JEV 模型」，負責 `graph/jev_guard_call.py`、`jev_forms_call.py`、Jev 相關模組。改它的檔案前要先問；合併前請它審查。它不在線時，就把審查請求寫成文件，範例：`confirmed-reason-2026-10-30/REVIEW-REQUEST-jev-guard.md`。

## 7. 已知風險和未解問題（給原型參考）

- **讀數貼近門檻：** Q18 的「手上有哪種資料」讀數在 0.70–0.81 之間；W17 的現行資料讀數是 0.69。
- **系統性誤讀模板救不了：** 例如 j6 X07 的「type 2 diabetes」被當成候選樣本數，要靠數字抽取規則處理。
- **V 組（沒指定結果的請求）的標準答案本身有判斷空間。**
- **服務故障：** OpenRouter 520 約佔 1–2%，計分時要列成故障，不算錯。
- **還沒合併的研究分支：** Z20 的 carry-links 已撤回（`carry-links-2026-10-29`），架構 C 的多輪設計會自然取代它。
- **jev-guard 提過一個它自己要修的問題：** accepted-input 那條規則，應該排除有合法前置工作流程可以串接的情況（W17 的 PANDA → CONDOR）。目前還沒做。
