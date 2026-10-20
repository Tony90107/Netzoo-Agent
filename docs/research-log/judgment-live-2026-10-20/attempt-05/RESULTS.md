# Attempt 05：一個疑問只問一次之後重跑（2026-10-20，Claude）

同一份凍結題目，程式 `6aaa21b0`（含 `b7347a59`）。能力核對用 gpt-4o-mini。6 個 session、7 個回合，費用 US$0.0296。沒有執行分析。

| 題 | 預期 | attempt-04 | attempt-05 |
|---|---|---|---|
| T01 9 或 17 人 | DO | DO | DO ✓ |
| T02 1 或 2 個樣本 | DECLINE | DO | DO ✗（讀取沒讀到疑問） |
| T03 第一回合 2 或 14 | ASK | ASK（同一題問兩次） | ASK，**只問一次** ✓ |
| T03 第二回合 補答 14 | DO | DO | DO ✓（規劃 run，因檔案不存在在預檢停下，符合設計） |
| T04 蛋白 180 或 1,800 | ASK | ASK | ASK ✓ |
| T05 因果 DAG | DECLINE | DECLINE | DECLINE ✓ |
| T06 目標不明 | CLARIFY | CLARIFY | CLARIFY ✓ |

7 個回合中 6 個符合，與 attempt-04 相同。T03 的重複追問已消失。

## 觀察（未修）

T01 的「我理解的需求」列出三項，其中兩項其實是資料說明：「9 或 17 位病人…」「我們有 motif 和 PPI」。讀取把它們當成要的結果，second opinion 又認可成 LIONESS-PANDA 可做。判定正確，但說明誤導。這是第一次讀取的歸類問題。

## 限制

實作者出題、題目都看過、每題一次；是 smoke，不是盲測。
