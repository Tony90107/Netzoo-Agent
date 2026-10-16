# 待決事項 1：ASK 回覆不再列出兩種答案的結果（2026-10-16）

**決定**：這是設計變更，使用者已同意，並已記入 spec 變更紀錄與第 3 節 ASK 的定義。fact agent 的 ASK 回覆只保留三樣：問題、使用者原話、使它重要的合約原文。`if yes`／`if no` 的結果不再出現在回覆中，但仍記錄在 `FactQuestion` 與 trace，R3 也繼續用它們篩掉不會改變判定的提案。

**理由**：這兩個結果是模型寫的，程式通常無法驗證方向。實測中的錯誤例子：
- p2b C06：「If no: PUMA does it instead」，但 PUMA 同樣需要 TF。
- p2b C36：「If no: no registered workflow」，但 LIONESS-PANDA 做得到。
- p2 C31：連 yes 分支都寫反了。

**不受影響**：舊的 11 種 dimension 的 needs_fact 回覆（例如 p2 的 C36）。它的各分支是程式依 sheet 反事實比對算出的。

**離線驗證**（`replay_p3.py`，用錄製的判定重新渲染，沒有呼叫模型）：

| 錄製回合 | fact agent 的 ASK 回覆 | 仍有結果行或缺引文 | 判定與回覆路徑不一致 |
|---|---|---|---|
| p2（`live/p2-replay-i1`） | 8 | 0 | 0 |
| p3（`live/p3-replay-i1`） | 12 | 0 | 0 |

判定改變的 C19、C56 是已知的重放限制：錄製的判定已經被 `with_core` 清空，重算時會看成路由失敗。

**沒有做的事**：沒有重跑實測。這次只改回覆文字，判定沒有變，所以 spec 允許只用離線重放驗證。
