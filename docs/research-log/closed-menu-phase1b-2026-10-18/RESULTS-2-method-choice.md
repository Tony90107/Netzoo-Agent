# 第 1b 階段第 2 步：結果讀取加入「在 workflow 之間選擇」（2026-10-18）

## 結論

- 結果欄位的「點名了什麼」多了一個值：`choice_between_workflows`，意思是使用者在兩個以上 workflow 之間選擇，沒有點名結果。
- 程式把它轉成「結果未定、沒有列出選項」→ `decide_menu` 問目標（CLARIFY），選項是那些 workflow 的結果。
- **決策表配合改了一處**：
  - 結果是「沒有列出選項的不確定」時，即使只點名一個 workflow 也要問目標（「COBRA 還是別的？」）。
  - 以前只點名一個 workflow 時會直接當成要跑它。
  - 第 0 階段門檻仍是 56/56。
- 開發集上幾乎量不到：85 題只有 1 次用到這個值，而且用錯了（accept24:U18 是兩種結果之間的選擇，不是方法選擇，但判定一樣是追問）。開發集沒有 vague 類題目。
- 第 1 階段的 C10、C26（「COBRA 還是 CONDOR」）屬於這一類，要在第 6 步的新題組上量。

## 檔案

- `menu_reader.py`：`Names` 加入 `choice_between_workflows`，`_result` 轉換。
- `menu_decision.py`：`_ask` 的條件。
- 測試：`test_a_choice_between_workflows_is_asked_as_the_goal`（兩個名字與一個名字都判 CLARIFY）。
