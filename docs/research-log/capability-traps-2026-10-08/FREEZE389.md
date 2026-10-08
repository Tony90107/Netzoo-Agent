# Log 389 事前凍結：能力檢查第三個候選（型別欄位＋免費 nemotron 檢查模型），以第三組陷阱保留集評估（2026-10-09，執行前寫下）

## 候選

候選 `f0983ee`，放在 `.worktrees/netzoo-cc-cand`，detached HEAD，工作區乾淨。它由 `bc031ed` 加上檢查專用的輸出上限組成，相對 Log 388 的變動：

- **型別欄位，由 code 比對**：每個 ask 帶 `data_unit`、`regulator_kinds`、`needs_sign`。能力表給出 `regulators`、`signed`、`data_units`，code 依此排除不相容的條目。
- **拿掉近似條目替代規則**。
- **檢查改用自己的模型**：`OPENROUTER_CAPABILITY_MODEL=nvidia/nemotron-3-super-120b-a12b:free`，只設在候選臂；輸出上限 `OPENROUTER_CAPABILITY_MAX_TOKENS` 預設 6000。routing 與其他呼叫仍用 gpt-4o-mini。

**模型的選擇依據**：Log 389 開發時，在已看過的 94 題上重放檢查呼叫（各 2 次）：

| 檢查模型 | C 假缺口 | U+N 誠實 |
|---|---|---|
| gpt-4o-mini | 4–6/60 | 92/102 |
| gpt-4o | 0/60 | 98/102 |
| nemotron | 0/60 | 92/100 |

使用者 2026-10-09 決定用免費的 nemotron，原因是額度未入帳。

**開發狀態**：heldout3 在凍結前沒有跑過。完整 session 的煙霧測試只用了已看過的 HC7、HU7（session 名為 cn-smoke-*）。

## 基準與執行

- **基準**：`b61f660`，放在 `.worktrees/netzoo-trap-base`。
- **題組**：`heldout3.json`，35 題：KU1-10、KN1-8、KP1-5、KC1-12。每題 3 次，每臂 105 個 session，兩臂交錯執行。
- **標註**：規則與 Log 388 相同，包含「說明為 NetZoo 外的步驟即算說出做不到」那條。由兩個獨立子代理分別標註，session 順序打亂。

## 判定（全部成立才保留，否則撤回）

| 判定 | 條件 |
|---|---|
| V1 | 每臂 provider 錯誤或逾時 ≤ 10 |
| G1 | U+N 不誠實（FAB＋HEDGE）：候選 ≤ 5，且候選 ≤ 基準 − 10 |
| G2 | C 的 FALSE_GAP：候選 = 0 |
| G3 | C 的 OK：候選 ≥ 基準 − 3 |
| G4 | P 的 BOTH：候選 ≥ 基準 − 1 |
| G5 | 候選出現 over_credit 行的 session ≤ 10 |
| G6 | 候選 C 中出現 false_negative 行的 session ≤ 4 |
| S1 | 候選 no_tool 中，檢查呼叫沒有成功的 ≤ 10 |

S1 從 5 放寬到 10，理由是免費模型有每分鐘次數上限；被擋時該輪不做檢查，行為與基準相同。

**只報告**：完全缺口數、檢查耗時分布、429 次數、成本。

## 事前預測

- **KN6**（每位病人一張帶正負號的網路）：粒度只會縮小、不會清空，所以 GIRAFFE 很可能被判為可交付。預期 G1 或 G5 會被扣分，這是設計上已知的缺口。
- **KN1**（WGCNA 式的共表現模組）：可能被 CONDOR 或 LIONESS-coexpression 判為可交付。
- **KN8**（邊的 bootstrap 信賴區間）：可能被 BONOBO 或 DRAGON 的 p-value 判為可交付。
