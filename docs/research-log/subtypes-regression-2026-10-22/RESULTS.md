# 「亞型」被讀成「可屬多組」：原因是換了讀取模型，不是程式改動（2026-10-22）

費用約 US$0.01（gpt-4o-mini 讀 9 次；nemotron 9 次全部 404，不收費）。沒有做二分搜尋，因為兩端點的測試已經排除程式改動。

## 結論

- 10/18–10/19 錄下的 J22、M45 讀對了，當時能力讀取用的是 **nemotron**（`nvidia/nemotron-3-super-120b-a12b:free`）。
- 10/20 起 nemotron 唯一的供應商回 404，能力讀取改用 `openai/gpt-4o-mini-2024-07-18`（使用者的暫時決定）。之後 Q26、J22、M45 都讀錯。
- **舊程式 `54d08ce7`（錄 J22、M45 那時的版本）配 gpt-4o-mini：9/9 都是「可屬多組」。** 所以錯誤跟著模型走，和 10/18 之後的 commit 無關。
- nemotron 目前仍然 404，無法直接重測。改用已存紀錄比對（stability-round13 harness 的全部讀取）：

| 讀取模型 | 「亞型」類要求 | 「群落」類要求 |
|---|---|---|
| nemotron | 只屬一組 60、跟分組無關 12、**可屬多組 0** | 只屬一組 33、跟分組無關 3、**可屬多組 0** |
| gpt-4o | 只屬一組 8、可屬多組 0 | 只屬一組 6、可屬多組 0 |
| gpt-4o-mini | 跟分組無關 14、沒說 6、**可屬多組 6**、只屬一組 1 | 跟分組無關 17、沒說 4、**可屬多組 2** |

## 為什麼會變成拒絕

四個失敗的 session（h5 Q26-1、nsbase J22、nsfields M45、nsfields Q26）都一樣：

- 整題層級的 `conditions.group_membership` 填了 `several_groups`，但 `group_membership_quote` 是空的，所以程式不採用（要逐字核對過的原文）。
- 每個要求的 `group_membership` 也是 `several_groups`。這一格沒有原文欄位，`_fitting` 卻直接用它把 SAMBAR 亞型或 CONDOR 群落排除掉。

也就是說，排除條件在整題層級要有正面證據，在要求層級卻不用。

## 離線估計：要求層級的排除形式也要有核對過的原文

做法：要求層級的 `several_groups`／`dynamic`／`uses_neighbors`，只有在整題層級同一欄位填了相同的值、而且原文逐字核對通過時才算數；否則當成中性值。在全部已存讀取（1211 份）上重放，不呼叫模型：

- 受影響的讀取 11 份，判定改變 8 個；
- Q26 ×4：誤拒 → 正確；
- M45 ×2：DECLINE → DO（金標 DO：誤拒 → 正確）；
- J22 ×2：DECLINE → DO（金標 ASK：仍是「該問沒問」，原因是樣本數「5 或 9」沒問）；
- **變差 0 個**。nemotron 和 gpt-4o 從沒在沒有原文的情況下填「可屬多組」，所以沒有任何正確拒絕靠這一格。

這只是估計，還沒改程式。

## 檔案

- `read_groups.py`：只做讀取的檢查（指定 checkout 與模型）；
- `old-code-mini.json`：54d08ce7 配 gpt-4o-mini，9/9 可屬多組；
- `current-code-nemotron.json`：nemotron 9/9 都是 404。
