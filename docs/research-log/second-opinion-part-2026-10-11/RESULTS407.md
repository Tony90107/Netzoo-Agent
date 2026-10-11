# Log 407：第二意見的 "part" 不再認可（2026-10-11，保留）

## 診斷

heldout11–14 的現行契約錄製中，檢查過度認可（負例被認可）25 筆，其中 16 筆是第二意見推翻了檢查原本「不可做」的判定。依第二意見的回答分：

| 回答 | 負例（錯） | 正例 |
|---|---:|---:|
| part（任何來源） | 13 | 4（同一需求都另有別的 workflow 答 all） |
| all，只由 typed 屬性推論的 workflow | 6 | 1 |
| all，routing／平手來源 | 3 | 20 |

"part" 是 Log 403 為「一個引文同時含可做與不可做的結果」加的；但 178 個兩項需求的 session 中，檢查從未把可做與不可做合成一個引文（0 次）。模型把 "part" 用在「單一結果只部分符合」：每個 tumor 的正負號（GIRAFFE 只有全體層級）、miRNA 正負號與 enhancer-promoter 迴圈（DRAGON）。

## 候選 `fa45cec`

`apply_second_opinion` 只有 "all" 認可；"part" 視同 "none"。provider schema 不變（移除選項可能讓模型改答 "all"）。

## 證據（確定性，離線重放；未呼叫模型）

`replay_so.py`：把錄製的檢查提案、重讀與第二意見回答餵回 `c2df644`（基準）與 `fa45cec`（候選）的檢查步驟並渲染回覆，以金標準逐項評分。52 個有第二意見紀錄的現行契約 session（1 個因配對與錄製不同略過）：

| | base | cand |
|---|---:|---:|
| 負例被檢查判定不可做 | 26/41 | 36/41 |
| 正例被判定可做 | 12/12 | 12/12 |
| 回覆改變 | — | 10，全部由錯變對（CN9×2、CN4、KN2×3、QN4、QN5×3），0 個改壞 |

例：QN5 由「partly available: GIRAFFE gives part of it … GIRAFFE fits your goal」變成「not available here: no registered workflow produces this. GIRAFFE does not give it: the regulatory matrix is one for all samples; only activity is per sample.」，卡片一致。

## 決定

保留。改動只決定如何使用已錄下的第二意見回答，離線重放即為直接證據；依使用者降低量測成本的要求，不另跑真實回合。已知風險：一個引文同時含可做與不可做結果、且第二意見答 "part" 時，現在整題判為不可做（錄製中 0/178）。

## 剩下

只由 typed 屬性推論、第二意見答 "all" 的認可（6 錯 1 對：QN4 enhancer 迴圈、CN4 miRNA 正負號 → DRAGON）仍在；拿掉會讓 VC3q 一次誤拒絕，留待新的契約設計。
