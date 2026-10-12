# Log 414 結果：保留（所有凍結判定成立）（2026-10-12）

事前凍結：`FREEZE414.md`（`7861d44`）。候選 `0f1b504`。

- 回合 `u19`：heldout19，30 題 × 2 臂 × 2 次，共 120 個 session。全部重放相同，provider 錯誤 0。備援檢查 base 2 次、cand 0 次。
- 標註：4 位盲標者分標 5 個 packet。我複核 50 個指定 session，全部維持原標，沒有更正。

## 數字

| | base | cand |
|---|---:|---:|
| 目標負例（UN＋KN，20）誤承諾（含 PARTLY） | 11 | **3** |
| 目標負例明確拒絕 | 5 | **15** |
| 目標負例含糊 | 4 | 2 |
| 正例（UP＋HP＋KP＋XP，34）明確說可做 | 32 | **32** |
| 正例誤拒絕 | 2 | **2** |
| 正例含糊 | 0 | 0 |
| XN 誤承諾 | 0 | 0 |
| 檢查沒有成功 | 2 | 0 |
| 矛盾 session | 6 | 6 |

判定：V1、G0（32 ≥ 32 且 2 ≤ 2）、G1（3 ≤ 11−3）、G2、G3 全部成立 → 保留。正例沒有任何一個由可做變成未確認或被拒絕。

## 逐題

**cand 修好的**（base 共 9 次誤承諾 → cand 0）：
- UN3「必須用 k-means」
- UN5「必須用 Louvain」
- UN6「每條連結要有 bootstrap 信賴區間」
- UN7「miRNA 邊要依測得的 miRNA 豐度加權」
- UN8「每個樣本的網路只能用該樣本估計」

**兩臂相同**：
- UN4、KN1、XN 都正確拒絕。
- KN2「請用 Leiden 演算法」兩臂都是 OMITTED：解析器要求使用者補充細節。

**cand 剩下的 3 次誤承諾**：
- UN2 ×2「邊要由調控者指向目標」：檢查把「共表現網路」錯認給 LIONESS-PANDA／PUMA。TF 網路的邊確實有方向，所以條件檢查判「符合」，這一步是對的。錯在檢查本身的認可（架構點 5）。正文另外推薦 LIONESS-COEXPRESSION／BONOBO，因此造成矛盾。
- UN1-2「不能用 motif 資訊」：回覆說 PANDA 需要 motif prior、而使用者表示沒有，標為 GIVEN_IF_INPUT。base 同一題也是這樣。

**兩臂都誤拒的既有 bug（不是本 Log 造成）**：UP1「我們提供的 motif prior 必須納入估計」，兩臂 4 次都標為 NOT_GIVEN。這句觸發了談「建模哲學」的回覆："Yes, in principle, data can weaken an unreliable TF-binding prior … No qualified registered workflow fully matches the requested modeling philosophy"。也就是說，這個 renderer 把「用到 prior」讀成要求貝氏的 prior 可靠度模型。值得另外修。

## 改動摘要

- `conditions.other_requirements`：附原話與類別。只檢查 how_computed、what_it_contains 兩類，原話必須在請求中，且所在句子不含任何需求。
- 條件檢查（satisfies／violates／unrelated）：只有 violates 移除該 workflow；已認可的全被移除時，改問 routing 提供的其他 workflow，satisfies 的改認它；呼叫失敗時不改任何東西。
- 檢查輸出上限 6000 → 9000 token。
- sheet 的 `inputs` 載入並顯示給條件檢查。
