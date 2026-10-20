# Attempt 04：ROUND-09 之後重跑（2026-10-20，Claude）

同一份凍結題目，程式 `1ef6a138`（ROUND-09 `899a32d5`），能力核對用 gpt-4o-mini（與 attempt-03 相同）。6 個 session、7 個回合，費用 US$0.0314，沒有執行任何分析。

| 題 | 預期 | attempt-03 | attempt-04 |
|---|---|---|---|
| T01 9 或 17 人 | DO | ASK（多問「至少 3 個嗎？」） | **DO** ✓ |
| T02 1 或 2 個樣本 | DECLINE | DO | DO ✗（讀取三處數量欄位全空，疑問沒被讀到） |
| T03 第一回合 2 或 14 | ASK | DO | **ASK「2 or 14?」** ✓ |
| T03 第二回合 補答 14 | DO | （沒跑到） | **DO** ✓ |
| T04 蛋白 180 或 1,800 | ASK | ASK | ASK ✓ |
| T05 因果 DAG | DECLINE | DECLINE | DECLINE ✓ |
| T06 目標不明 | CLARIFY | CLARIFY | CLARIFY ✓ |

7 個回合中 6 個符合（attempt-03：3/6；attempt-02：1/7，當時 nemotron 404）。

## 新發現的瑕疵

T03 第一回合同一個問題問了兩次：第一次讀取和 re-read 各認出一個結果，兩個結果都等待同一段疑問（「either 2 or 14 samples」與「2 or 14 samples」原文重疊、候選相同），`decide_core` 對每個結果各問一次。判定正確，但回覆重複。尚未修。

## 限制

實作者出題、題目都看過、每題一次，是 smoke，不是盲測。
