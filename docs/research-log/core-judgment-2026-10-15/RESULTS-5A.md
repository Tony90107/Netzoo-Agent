# 第 5a 階段：routing 失敗時，已確認的目標不明判 CLARIFY（2026-10-16）

## 結論

- **5a 的離線驗證通過**，結果與 spec 第 13.5 節的預期相同：
  - 和錄製時的 live 判定相比，只有 C10 的 4 個回合（p2、p3、p4b、p4c）從 UNCHECKED 改為 CLARIFY。
  - 其他判定 0 改變，m3 也是 0 改變。
- 重新產生的回覆都由 CLARIFY 的 view 回答，判定與回覆路徑 0 不一致。
- 估計分數：p4b 92.2 → **93.1**，p4c 80.8 → **81.6**，太模糊類各多 1 題。這是重放估計，不是實測。
- 程式改動只有一處：`decide_core` 第一條規則多一個例外。

## 改了什麼

`decide_core` 的第一條規則是「routing 失敗、沒有任何路由結果 → UNCHECKED」。現在有兩種例外：

- 能力檢查已確認完全缺口（原有）；
- `goal_unclear(check)` 為真（新增）。

`goal_unclear` 本身已要求確認過的讀取與逐字驗證過的引文，所以備援讀取的目標不明仍判 UNCHECKED。

## 離線驗證

`offline_both_wrong.py calls --no-rejudge`：同一份錄製決策分別交給 5a 之前的程式（`e839297d` 的暫時 worktree）和這份程式判定。範圍是 p0、p1、p2、p3、p4b、p4c 與 m3，共 456 個 session。

| 改變 | 回合 | 說明 |
|---|---|---|
| UNCHECKED → CLARIFY | C10 p2、p3、p4b、p4c | 預期中的改變；4 個都是太模糊類，從 unchecked 變成 correct |
| UNCHECKED → CLARIFY | C19 p1、p2 | 重放的假象，不是行為改變。live 時兩輪都已經是 CLARIFY：語意讀取真的失敗了，但當時的決策還有路由動作。`with_core` 清掉這些動作後，舊程式的重放才把它讀成 routing 失敗；新程式的重放和 live 一致 |

和錄製的 live 判定相比，偏離 live 的只有 C10 的 4 個回合；回到 live 的是 C19 的 2 個。

`replay_p3.py` 重新產生 p2、p3、p4b、p4c 的回覆：

- 4 輪都是 0 不一致，0 錯誤。
- C10 的回覆：
  - 先說還不確定要哪個結果、沒有選 workflow；
  - 列出各 workflow 能給的結果，不說哪個適合；
  - 問想要的結果和手上的資料；
  - 最後說明沒有選任何東西、也沒有執行。
- 因為 routing 沒讀到輸入，13 個 workflow 全部列出（第 13.2 節的已知限制）。

其他幾題的判定和錄製時不同（p3 的 C27、C56，p4b、p4c 的 C31），但 5a 之前和之後的重放都一樣，所以不是 5a 造成的。

## 測試

- 新增兩個單元測試：
  - routing 失敗加上已確認的目標不明（`purpose_only`，以及「COBRA or CONDOR」的 `method_named`）→ CLARIFY；
  - 加上備援讀取的目標不明、或讀到具名結果 → UNCHECKED。
- 全套測試：3,854 個通過。

## 費用

沒有呼叫任何模型。
