# 第二意見認可結果之後，重新計算候選數量（2026-10-21，Claude）

## 問題

使用者給的候選數量（例如「1 或 2 個樣本」）原本只在建立 check 時計算一次，`count_update` 只對當時已認可 workflow 的結果起作用。

如果第一次讀取沒有認可任何 workflow，之後才由 second opinion 認可 LIONESS-PANDA，候選數量就不會被計算。結果是「1 或 2 個樣本」會判成 DO。

## 修改

- 新增 `weigh_credited_counts`（`count_alternatives.py`）。second opinion 認可某個結果後，用同一個 `count_update` 重新計算候選數量：
  - 每個候選都不符合 → 不可做；
  - 候選有分歧 → 程式問「2 or 14?」；
  - 每個候選都符合 → 不變。
  - 用來計算的 entry 是 second opinion 認可、資料量判斷之前的那些。
  - 結果數量依原文段落計算，重疊的字算同一段。
- `apply_second_opinion` 多了一個選填參數 `task`，router 會傳入請求原文。沒有原文時行為和修改前相同。

## 離線重放（不呼叫模型）

`replay_so.py`：所有有回答的 second opinion，共 97 份。

做法：
- 用目前程式重建 check；
- 套上當時記錄的 pairs 與回答，分成兩次：不給原文（等於修改前）、給原文（修改後）；
- 接著跑 `wait_on_asked` 與 `decide_core`。
- 5 份的 pair 和重建後的 check 對不上，不套用。

結果：
- 有候選數量的 7 份，全部是 live T01（9 或 17，兩個候選都符合），判定都沒變。
- 判定改變：0 份。
- 有金標的 69 份：答對 55 → 55。

`perturb.py`：把 7 份 live T01 讀取的「nine or seventeen」換掉，原文和讀取一起換，其餘照上面的流程跑。

| 換成 | 修改前 | 修改後 |
|---|---|---|
| nine or seventeen（原樣） | DO ×7 | DO ×7 |
| one or two | **DO ×7**（缺口） | DECLINE ×7 |
| 2 or 14 | ASK「至少 3 個嗎？」×7 | ASK「Which of these is right: 2 or 14?」×7 |

單元測試：`test_candidates_are_weighed_for_a_result_the_second_opinion_credits`（3 種情況，加上沒給原文時不計算）。全套測試 4801 passed、51 skipped。

## 沒做

- 沒有 live 測試。
- condition check 與 redirect 認可的結果，沒有重新計算候選。目前錄到的資料裡沒有這種例子。
