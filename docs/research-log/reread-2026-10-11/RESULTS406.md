# Log 406 結果：保留（所有凍結判定成立）（2026-10-11）

事前凍結：`FREEZE406.md`（`0a2420c`）。回合 `r14`：heldout14 30 題 × 2 臂 × 2 次，120 個 session，全部重放相同；provider 錯誤 0、檢查失敗 0。標註：單一盲標子代理（4 個 packet；因 Claude 使用額度中斷一次，packet 02、03 額度恢復後重標），我複核兩臂分布不同的 11 題共 40 個 session（`live/r14-labels-checked.json`）。

## 抽查更正（3 處，都對候選不利）

- S008（cand KN2-2）：與 S092／S094／S102 回覆文字完全相同，統一為 GIVEN_WITH_STEP＋矛盾（原 NOT_GIVEN）。
- S061、S063（cand MN2）：與基準 S001／S012 回覆相同，統一為 LISTED_ONLY（原 OTHER）。
- S054（cand QN4-2）：理解段落寫 "available from DRAGON or LIONESS-DRAGON"、卡片列 6 個網路方法，改為 GIVEN＋矛盾（原 PARTLY）。這裡重讀沒有發動，是檢查本身過度認可。

## 數字

| 指標 | base | cand |
|---|---:|---:|
| 負例被明確說不可做 | 13/26 | 17/26 |
| FC 誤承諾 | 4 | 4 |
| 正例被說可做 | 31/34 | 31/34 |
| FR 誤拒絕 | 0 | 0 |
| OM | 3 | 2 |
| 諮詢沒被回答 | 4 | 4 |
| 標註者矛盾 | 11 | 9 |
| 重讀發動 | — | 12 session，共 115 秒（平均 9.6 秒） |

判定：V1、G1（17 ≥ 13+4）、G2、G3、G4、G5、A1 全部成立 → 保留。

## 觀察

- 改善來自 KN1（限制性追問：GIVEN×2 → NOT_GIVEN×2）、QN3（UNCONFIRMED → NOT_GIVEN）、P2（3D rendering OMITTED → NOT_GIVEN）、QN4 一次。本題組的 QN 問句在基準多半已被讀成需求（Log 403 `asked_as`），所以重讀在 QN 很少需要發動。
- 候選的 4 次 FC 中，KN3-1（DRAGON 三層）來自 routing 隨機的 exact 匹配，重讀發動但回傳空的需求清單，未改變判定；QN4-2 是檢查本身過度認可（重讀未發動）。這兩類（過度認可、兩段式後半被略過）仍是剩下的主要問題：P1 的 email 兩臂都 OMITTED。
- 增加的延遲小：本日 nemotron 每次重讀約 10 秒。
