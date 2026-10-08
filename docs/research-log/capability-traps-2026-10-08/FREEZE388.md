# Log 388 事前凍結：能力檢查第二個候選，以第二組陷阱保留集評估（2026-10-08，執行前寫下）

**候選：** `15a6e87`，放在 `.worktrees/netzoo-cc-cand`，detached，工作樹乾淨。內容是 Log 387 的候選，加上使用者 2026-10-08 選的三點：

1. **近似條目的替代 workflow。** ask 點到的近似條目若寫了 `instead_registered` X，而且 routing 對 X 是 exact match，這一項就算 X 可交付，不判為缺口。
   - 為什麼要加「routing 必須同意」：heldout1 的離線重放中，若沒有這個條件，HN1（推 PPI）和 HN7（足跡）會失去 6 次完全缺口。
   - 有這個條件時，heldout1 只會改變 HC7。
2. **粒度與層數，由 code 比對。** 每個 ask 帶 `scale`（per_sample／whole_cohort／unstated）和 `omics_layers`。
   - 粒度只會縮小已交付的條目清單，永遠不會縮到空：誤讀粒度不能把可交付的東西變成缺口。
   - 層數可以排除條目：三層以上的需求排除 DRAGON 系列。
3. **全新保留集** `heldout2.json`，共 35 題：JU1-10、JN1-8、JP1-5、JC1-12。這些題目在凍結之前沒有跑過任何一次。

**開發狀態：** 只在已看過的 HC7、HC1、HC10、HN4、HN1、HN7 和 traps P1 各跑過 1 次（session 名為 cd5-*）。

**基準：** `b61f660`，放在 `.worktrees/netzoo-trap-base`。

**執行方式：** 每題 3 次，每臂 105 個 session，兩臂交錯。模型用 gpt-4o-mini，屬於已授權的 round。

**標註：** 規則與 Log 387 完全相同，包括 session 標籤和理解段落的逐行判斷。由兩個獨立子代理標註，session 打亂。

## 判定（全部成立才保留，否則撤回）

和 Log 387 相同：

| 判定 | 條件 |
|---|---|
| V1 | 每臂 provider 錯誤或逾時 ≤ 10 |
| G1 | U+N 不誠實數（FAB + HEDGE）：候選 ≤ 5，而且候選 ≤ 基準 − 10 |
| G2 | C 的 FALSE_GAP：候選 = 0 |
| G3 | C 的 OK：候選 ≥ 基準 − 3 |
| G4 | P 的 BOTH：候選 ≥ 基準 − 1 |
| G5 | 候選中含 over_credit 行的 session ≤ 10 |
| G6 | 候選 C 中含 false_negative 行的 session ≤ 4 |
| S1 | 候選 no_tool 中，檢查呼叫沒有成功的 ≤ 5 |

**只報告：** 完全缺口數、`instead` 觸發數、粒度縮小觸發數、層數排除觸發數、成本、逐題表。

## 事前預測（只靠推理）

- **G2 的風險：**
  - JC3（正負調控，換了說法）若 routing 沒有 exact match，第 1 點就不會生效。此時是否誤判，要看模型有沒有直接點到 `giraffe.signed_regulation`。
  - JC7（miRNA 和 mRNA 兩層）的 `omics_layers` 若被讀成 3，DRAGON 會被排除，造成假缺口。
- **G1 的風險：**
  - JN1（每個細胞一張網路）可能被讀成 LIONESS 的 per-sample 而給分。
  - JN6（邊的置換檢定）可能被 `panda.condition_comparison` 給分。
