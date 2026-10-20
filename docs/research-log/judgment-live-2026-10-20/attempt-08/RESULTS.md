# Attempt 08：句子歸屬順序修正之後重跑（2026-10-21，Claude）

同一份凍結題目。程式為 `a38160c4`，包含 `f65772f2`。能力核對使用 gpt-4o-mini。共 6 個 session、7 個回合，費用 US$0.0275。沒有執行分析。

| 題目 | 預期 | attempt-07 | attempt-08 |
|---|---|---|---|
| T01：9 或 17 人 | DO | ASK ✗ | **DO** ✓ |
| T02：1 或 2 個樣本 | DECLINE | DECLINE | DECLINE ✓ |
| T03 第一回合：2 或 14 | ASK | ASK「2 or 14?」 | ASK「2 or 14?」 ✓ |
| T03 第二回合：補答 14 | DO | DO | DO ✓ |
| T04：蛋白 180 或 1,800 | ASK | ASK | ASK ✓ |
| T05：因果 DAG | DECLINE | DECLINE | DECLINE ✓ |
| T06：目標不明 | CLARIFY | CLARIFY | CLARIFY ✓ |

7 個回合全部符合預期。

T01 這次確實走到了修正的路徑：
- 記錄裡有 `context_candidates` 證據（9 或 17）。
- fact agent 提出的「Do you have at least three expression samples?」被記在 `count_owned`，沒有問出來。

T02 同樣讀到了背景候選，判定為 DECLINE。

## 觀察到、未處理的問題

1. **T01 的理解段落重複列出結果。**「one TF-to-gene network per patient」是第 1 項引文的一部分，卻又被列成第 2 項。判斷沒有受影響（兩項都由 LIONESS-PANDA 提供，結論仍是 DO），只是顯示上重複。
2. **T04 的問題只問了一邊**：「Did you receive the 180-protein panel?」。這句是 fact agent 自己寫的，判斷正確（ASK），但沒有把兩個候選並列出來。
3. **候選只在建立 check 時計算一次。** 如果之後 second opinion 才認可某個結果，候選不會重新計算。這個缺口在 attempt-07 就已發現，仍然存在。
