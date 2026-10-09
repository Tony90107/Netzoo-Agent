# Log 402 事前凍結：重疊成員、時間動態、空間鄰點是沒有 workflow 給的結果形式（2026-10-10，執行前寫下）

## 候選

候選為 `75b45ed`，放在 `.worktrees/netzoo-forms-cand`，detached，乾淨。基準是上線版本 `856a2c7`，放在 `.worktrees/netzoo-trap-base`。

這個候選不包含 Log 401。兩者分別量測；如果都保留，再合併。

改動內容：

- **能力表**新增 `result_forms`，列出所有登錄結果允許的形式：
  - `group_membership: [one_group, not_about_groups]`：CONDOR 只把每個節點分到一個社群。
  - `time_model: [not_dynamic]`：沒有 workflow 建模時間點之間的變化。把每個樣本的結果與時間點、分期、追蹤資料做比較或關聯，不算動態。
  - `spatial: [not_spatial]`：沒有 workflow 使用樣本的空間位置或鄰點。
  - 載入時若遇到未知欄位或形式，fail closed。
- **檢查的 ask** 多三個必填欄位：`group_membership`、`time_model`、`spatial`。
- **程式比對**：形式不在 `result_forms` 中的 ask，所有條目都會被排除，與單細胞的作法相同。第二意見沒有條目可問，缺口成立。
- **來源**：heldout7 ON5、heldout8 QN5／QN8／QN10，以及 heldout9 RN5。檢查本身直接把這些題目認列給 CONDOR、LIONESS-PUMA 或 LIONESS-PANDA，表上沒有欄位能排除它們。

**開發檢查**：只有單元測試（3451 passed），沒有在已看過的題組上重播。nemotron 額度要留給正式回合。

## 題組

`heldout10.json`，共 35 題，凍結前從未跑過，與 Log 401 共用：

- **SN1-8**：針對這次修改的近似題，包括模糊或重疊成員、時間轉移、領先落後、訪視之間的動態、空間平滑、空間鄰近、空間連續社群。
- **SN9-10**：其他近似題，包括增強子當調控者、激酶當調控者。
- **SC1、SC2、SC4、SC6、SC7、SC8、SC9、SC10**：帶時間點、分期、區域等字眼的對照題，其實都做得到。這些是誤判的陷阱。

**設定**：一般情況，routing 用 mini，檢查用 nemotron。每題 3 次，兩臂交錯，tag `f10`（`CAND_WORKTREE=netzoo-forms-cand`）。標註規則同 Log 400，由兩個獨立子代理各盲標一半。分析用 `analyze402.py f10`。

**模擬**：`sim_routing_failure.py heldout10.json`，每題 2 次，基準和候選程式碼各跑一次（`sf10-base`、`sf10-cand`）。分析用 `analyze402_sims.py`。

## 判定（全部成立才保留，否則撤回）

| 判定 | 條件 |
|---|---|
| V1 | 每臂 provider 錯誤 ≤ 10 |
| T1 | SN1-8（每臂 24 次）的 HONEST：候選 ≥ 基準 + 6 |
| G1 | U+N 的 FAB＋HEDGE：候選 ≤ 基準 |
| G2 | C 的 FALSE_GAP：候選 ≤ 基準 |
| G3 | C 的 OK：候選 ≥ 基準 − 2 |
| G4 | P 的 BOTH：候選 ≥ 基準 − 2 |
| G5 | 含 over_credit 行的 session：候選 ≤ 基準 |
| G6 | C 中含 false_negative 行的 session：候選 ≤ 基準 + 2 |
| S1 | no_tool session 中沒有成功檢查的：候選 ≤ 基準 + 2 |
| SF1 | 模擬中 C 的完全缺口：候選 ≤ 基準 + 1 |
| SF2 | 模擬中 U+N 的完全缺口：候選 ≥ 基準 |

**額度**：這一輪大約需要 370 次 nemotron 呼叫（兩臂各 105 個 session，加上第二意見與兩組模擬），低於每日 1000 次。Log 401 不使用 nemotron。

## 事前預測

- **T1**：SN1、SN2、SN6、SN7、SN8 最可能轉成 HONEST。SN3 到 SN5 要看模型會不會把「從一週到下一週」讀成 dynamic。
- **G2 的風險**：
  - SC1「每位病人在三個時間點之一取樣，檢驗哪些邊隨時間點不同」、SC6「各時間點的 TF 活性」可能被讀成 dynamic。
  - SC4「同一腫瘤的四個區域」可能被讀成 spatial。
  - SC3「每個基因只在一個社群」應該讀成 one_group。
