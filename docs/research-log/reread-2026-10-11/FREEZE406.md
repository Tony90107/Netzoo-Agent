# Log 406 事前凍結：檢查漏讀的文字再讀一次（只問要什麼結果）（2026-10-11，執行前寫下）

目標：做不到時明確說做不到。三輪現行版本中，負例 22 次沒被明確拒絕；其中 12 次是檢查根本沒把它讀成需求（方法問句、限制性追問、兩段式請求的後半段）。

## 候選與基準

- 基準 `base`：`dd291d4`（上線版，含 Log 405），`.worktrees/netzoo-rr-base`。
- 候選 `cand`：`ce52acd`，`.worktrees/netzoo-rr-cand`。兩臂只差這個 commit。單元測試 3518 passed、35 skipped。
- 規則：程式找出檢查漏讀的段落——(a) 檢查讀完沒讀出任何結果、routing 卻提供了 workflow（方法問題點名已登錄 workflow 時除外）；(b) 有結果引文的句子仍有 ≥ 5 個 4 字母以上的詞沒被任何引文涵蓋——由檢查自己的模型以只有 `asks` 欄位的 schema 再讀一次；與既有結果重疊的新結果丟棄，合併後照常走 full gap 與第二意見。備援模型的讀取不重讀。

## 預先量測（凍結前已做，真實模型呼叫，未標註）

錄製的現行契約 turn 上跑整合後的檢查步驟（`premeasure2.py`）：負例被檢查判定不可做 0 → 22/37；正例被讀成可做 8 → 30/44；原本正確的判定沒有一個被改錯。仍未修好：P1 上傳、VP5q 比對 reads、VU4q、QN6、VP1 dashboard。

## 題組

`heldout14.json`，30 題、30 項需求（正例 17、負例 13），執行前從未跑過：QN 6、QP 6、K 6（KN 3、KP 3，`--resume`）、P 4、M 4（consult；MN 2 點名、MC 2 不點名）、CE 4。

## 回合（依使用者 2026-10-11 要求降低成本）

`r14`：routing 用 mini、檢查用 nemotron，**每題 2 次**，兩臂交錯，`run_heldout14.py r14 2`，共 120 個 session。

## 標註（單人＋我抽查）

一個盲標子代理標全部 session（`LABELING.md`）。我複核「兩臂標註分布不同的題目」的所有 session（`analyze14.py r14 spotcheck` 列出），每個都要在 `live/r14-labels-checked.json` 留下結果（含不變者），更正需寫理由。

## 判定

| 判定 | 條件 |
|---|---|
| V1 | 每臂 provider 錯誤或逾時 ≤ 6；檢查沒成功的 no_tool ≤ 6；120 個 session 齊全；重放相同 |
| G1 | 負例被明確說不可做（NOT_GIVEN）：cand ≥ base + 4 |
| G2 | FC：cand ≤ base |
| G3 | 正例被說可做：cand ≥ base − 2，且 FR：cand ≤ base + 1 |
| G4 | M 題諮詢沒被回答（LISTED_ONLY／REFUSED）：cand ≤ base + 1 |
| G5 | 標註者矛盾：cand ≤ base + 1 |
| A1 | OM：cand ≤ base + 2 |

全部成立才保留；否則撤回，不在本題組上重量。另報：重讀發動的 session 數與增加的秒數（nemotron 每次約 30–120 秒）。

## 事前預測

QN1、QN2、QN3、QN5、KN1、KN2 最可能由誤承諾或含糊變成明確不可做；P 題的後半段（email、3D、kinetic、therapy）不一定被讀到（預先量測中 P1 上傳沒修好）。風險在 QP（問句形式的正例）若被重讀判成不可做；預先量測沒有出現。
