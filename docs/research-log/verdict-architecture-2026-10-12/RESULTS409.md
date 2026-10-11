# Log 409 第 1 步結果：單一判定決定正文的 workflow（2026-10-12，保留）

分析見 `ANALYSIS409.md`。候選：`interpretation/checked_match.py`（Log 405 規則推廣）。單元測試 3528 passed、35 skipped。

## 證據（確定性，離線重放；未呼叫模型）

`replay409.py` 把 6 輪已標註回合的 1024 個錄製 decision，各自套上一版的 routing 後判定步驟與 renderer，重新產生回覆與卡片：基準為上線的 `ec97bd6`（`.worktrees/netzoo-score-live`），候選為本工作樹。基準重放 x15 的 100 個回覆與錄製逐字相同。

候選改變了 31 個 session 的回覆或卡片：9 個換了 workflow，其餘 22 個只是丟掉不適用的 routing 結果解讀。把新舊兩版混在一起打亂，交給一位盲標者（62 個回覆，`replay/packet.md`，標籤 `replay/labels-A.json`），比較結果見 `compare409.py` 與 `replay/compare.txt`：

| 31 個受影響 session | base | cand |
|---|---:|---:|
| 明確（負例 NOT_GIVEN／正例說可做） | 32 | 45 |
| 含糊（UNCONFIRMED 等） | 13 | 0 |
| 誤承諾 | 1 | 1 |
| 誤拒絕 | 0 | 0 |
| 標註矛盾 | 15 | 0 |

- 主要改善（13 個）：一半可做、一半不可做的請求。之前寫 "available from X" 加上 "Fallback recommendation … not a verified match"，現在改成 "Selected path: X"，不可做的部分仍列為不可做。這 13 個是 m13 P2 ×6、r14 P3 ×2、P4、b12 PN1、x15 MX2 ×2、MX3。
- 衝突改判：x15 PS1-2、PS3-2 由 GIRAFFE 改為 LIONESS-PANDA，MX6 由 GIRAFFE 改為 PANDA，標籤不變、矛盾消失。
- 唯一的誤承諾 m13 CN9-2（負例）兩版都在：檢查本身把它認給 GIRAFFE，routing 選 LIONESS-PANDA，兩邊都錯；屬於架構點 5。
- 已在 Log 405 下採用的 KP1/KP2 ×12、x15 PS1-1：丟掉 routing 的結果解讀。例如原本寫 "Your question asks for a p-value matrix. **DRAGON** fits"，PS1-1 原本寫 "cohort-level TF activity matrix … LIONESS-PANDA fits"，卡片改為描述該 workflow 實際產出的東西。

## 決定

保留。改動只決定如何使用錄下的 routing 與檢查結果，離線重放就是直接證據，比照 Log 407 不另跑真實回合。沒有任何回覆變差。

## 沒有解決的（下一步）

- 架構點 2（每輪單獨判斷）：本步沒有碰。x15 KN1 的錄製中，檢查沒有讀出結果，所以本規則不會觸發，SAMBAR 仍會出現。
- 架構點 3（沒有判定 = 放行）、架構點 5（檢查模型判錯）。
