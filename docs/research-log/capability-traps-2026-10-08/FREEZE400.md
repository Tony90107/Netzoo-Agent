# Log 400 事前凍結：只上 mini 備援，以 heldout9 和三種模擬評估（2026-10-10，執行前寫下）

## 候選

候選為 `48112e5`，放在 `.worktrees/netzoo-cc-cand`，detached，乾淨。基準是上線版本 `856a2c7`，放在 `.worktrees/netzoo-trap-base`。差異只有 `graph/capability_check_call.py`，共 19 行：

- 檢查呼叫：自己的模型（nemotron）不論因為什麼失敗，第二次嘗試都改用 semantic 模型（gpt-4o-mini）。
- 第二意見：自己的模型沒有回答時，也用 semantic 模型再問一次。

這是 Log 399 撤回的候選中的 B 部分，原封不動取出，只把註解改成 Log 400。Log 399 的量測中，B 部分本身的結果是：完整回合觸發 1 次並成功；模擬下檢查成功 70／70，對照題 0 個缺口。當時 SB3 失敗，原因在 A1，不在 B。

## 題組

`heldout9.json`，共 35 題，凍結前從未跑過（`111702e`）。陳述句與問句混合，核心內容都沒有在 heldout1-8 或 traps 中出現過：

- RU1-8（做不到）
- RN1-10（近似題）
- RP1-5（部分做得到）
- RC1-12（對照題）

**設定**：routing 用 mini，檢查用 nemotron（`.env`）。

## 量測與判定（全部成立才保留，否則撤回）

**A. 完整回合**：每題 3 次，兩臂交錯，tag `h9`。標註規則與 Log 399 相同，由兩個獨立子代理各盲標一半。分析用 `analyze400.py h9`。

B 只在自己的模型失敗時才有作用。這種失敗大約每 100 次出現 1 次，所以完整回合要回答的問題是「有沒有退步」。容許範圍取同一份程式碼重跑時的波動，約 3-4 次。

| 判定 | 條件 |
|---|---|
| V1 | 每臂 provider 錯誤 ≤ 10 |
| G1 | U+N 的 FAB＋HEDGE：候選 ≤ 基準 + 3 |
| G2 | C 的 FALSE_GAP：候選 ≤ 基準 |
| G3 | C 的 OK：候選 ≥ 基準 − 3 |
| G4 | P 的 BOTH：候選 ≥ 基準 − 2 |
| G5 | 含 over_credit 行的 session：候選 ≤ 基準 + 3 |
| G6 | C 中含 false_negative 行的 session：候選 ≤ 基準 + 2 |
| S1 | no_tool session 中沒有任何一次檢查呼叫成功的：候選 ≤ 1，且候選 ≤ 基準 |
| S2 | 候選中，自己的模型失敗後沒有接著 mini 嘗試的 session = 0 |

**B. 模擬**：heldout9，每題 2 次，routing 視為失敗。分析用 `analyze400_sims.py`。

- `sf9`：候選程式碼，檢查照常用 nemotron（`sim_routing_failure.py`）。
- `sb9`：候選程式碼，自己的模型每次呼叫都失敗，只能由 mini 回答（`sim_check_fallback.py`）。
- `sb9-base`：上線程式碼，在同樣的強制失敗下執行。

| 判定 | 條件 |
|---|---|
| SB1 | `sb9` 的 C 完全缺口 ≤ `sf9` 的 C 完全缺口 + 1（備援不能多製造假缺口） |
| SB2 | `sb9` 的檢查成功 ≥ 66／70 |
| SB3 | `sb9` 的 U+N 完全缺口 ≥ `sf9` 的 U+N 完全缺口 − 4（備援找出缺口的能力和 nemotron 相差不大） |
| SB4 | `sb9` 的檢查成功次數 > `sb9-base`（上線版本在同樣情況下應該是 0） |

## 事前預測

- 完整回合兩臂應該幾乎相同。差異主要來自 routing 和 nemotron 的隨機波動，備援大概只會觸發 0 到 3 次。
- SB3 的風險：在 Log 387-388 中，mini 當檢查模型時，對做不到的題目判得比 nemotron 寬鬆。如果 mini 把近似題直接認列給 workflow，`sb9` 的 U+N 缺口會明顯少於 `sf9`。
- SB1 的風險：mini 在對照題上可能給出白卷，因而判成缺口；routing 失敗時沒有 exact 比對可以觸發第二意見。
