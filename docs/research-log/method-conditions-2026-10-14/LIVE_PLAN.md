# M1 Step 4.3：小型 live 擷取測試（開跑前寫定，2026-10-14）

候選版本：`.worktrees/netzoo-mc-cand`，6348d26 起。題組：`live_m1.json`，共 24 題、24 個 session、27 個回合（K06、K09、K10 各兩回合），每題跑 1 次。執行：`run_live_m1.py <tag>`；分析：`analyze_m1.py <tag>`。

| 組別 | 題目 | 用途 |
|---|---|---|
| 負例（6） | N11、MX05、N36、N12、N13、N22 | M1 要判為不可做的 6 類 |
| 配對正例（6） | K06、P19、P20、P09、MX18、N36P（新題：指定 GIRAFFE 推 TF activity） | 必須維持可做 |
| accept24 對照（8） | P12、P21、P33、K09、K10、P17、MX04、P10 | 有方法名、參數或數量，最可能被誤讀成新的誤拒絕 |
| 新措辭（4） | F1 PANDA alpha、F2 GENIE3、F3 兩個樣本的 LIONESS-PANDA、F4 SAMBAR kmax 6 | 不是開發題，檢查擷取是否泛化 |

N35 依使用者決定移到 M2，不在本輪。

## 判準（全部都要達成）

1. **擷取正確率 ≥ 90%**：每題的 `m1_target` 是決定該題的欄位（負例：決定拒絕的那個方法、參數或數量；正例：沒有讀出會造成拒絕的值）。驗證後的欄位（`CheckedRequirement.method`）與 target 一致，才算正確。分母是 24 題，扣掉能力檢查沒由主模型完成的題目（provisional／unavailable，另外列出）。
2. **6 個負例判為不可做**：目標需求是 `not_available`，而且有 M1 的理由（`limits`）。MX05、MX04 的 R1、N11 允許以「X itself can still run」提出同一個 workflow 作為替代。MX18 的 R2 也要判為不可做。
3. **沒有新增誤拒絕**：配對正例、accept24 對照與 F4 的可做需求，都不能因為 M1 的理由被判為不可做；MX05、MX04 的 R1 要以替代方式明說 workflow 本身可以跑。a24b 裡原本就沒給的（例如 P09 在 a24b 是 UNCONFIRMED），只要不是 M1 造成，就另外記錄、不算。
4. run 回合記錄 CLI 的「✓ Workflow — X」、run 判定與是否擋下。

不達成時：先看錯在擷取（模型）還是規則（程式），規則錯就修程式後離線重播；擷取錯不改提示措辭（使用者規則），只調整契約形狀，或撤回該欄位。

## 費用估計

- gpt-4o-mini：約 27 回合 × 5 次呼叫，約 US$0.03–0.06。付費餘額約 US$4.2。
- nemotron 免費額度：每回合 1–5 次，共約 60–130 次。今天 08:00 後已用約 280 次（上限 1000 次）。
- 時間：5 個並行，約 10–15 分鐘。

## 第二輪 m1b（使用者決定：全部重跑，2026-10-14）

m1a 後的修正（3feb464、3dee444）：未註冊的 LIONESS 版本、無法對應結果時提供 workflow 自己的設定、每個控制項的說明進契約、請求層的指定方法與設定、讀取類呼叫的預算計算。契約對每題都改了，所以 24 題全部重跑，另加兩題新措辭：F5（OTTER gamma 0.5、80 iterations，應維持可做）、F6（LIONESS-PANDA 方法內的稀疏門檻，應判不可做）。共 26 個 session、29 個回合，判準同上，分母 26 題扣掉 provisional／unavailable。
