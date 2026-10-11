# Log 405 事前凍結：routing 沒有主張時，採用檢查認可的單一 workflow（2026-10-11，執行前寫下）

對應 P1 第 3 項尚未解決的部分：回覆的理解段落讀檢查的判定，正文與卡片卻跟 routing 的選擇（Log 404 `RESULTS404.md`：兩臂各 10 個標註矛盾，多數是這一類）。

## 診斷（錄製資料，未呼叫模型）

n11＋b12（現行檢查契約）中，routing 提供的 workflow 與檢查認可的 workflow 完全不重疊的 turn 有 19 個：

| routing 狀態 | 次數 | 金標準 |
|---|---:|---|
| fallback（KP2）或輸出驗證失敗（BP1、BP6、VC7s） | 12 | 檢查 12/12 對，且都由單一 workflow 涵蓋全部結果 |
| 平手（VM4s，組合流程） | 6 | 各對一半 |
| exact（VT1-2） | 1 | routing 對 |

舊契約錄製（h1–h10）同條件 47 次，檢查 33 對、14 錯（近似但不支援的需求被過度認可：調控者種類、hypergraph、角色反轉、miRNA 正負號、重疊社群、動態、多一個不支援的步驟、非領域）。這 47 次中，理解段落本來就已寫出檢查的 workflow，所以本候選主要讓回覆一致，承諾程度大致不變；正文原本的保留語氣會消失，FC 可能小幅上升（G2 量）。

## 候選與基準

- 基準 `base`：`709dda2`（上線版），`.worktrees/netzoo-cm-base`。
- 候選 `cand`：`1f52ab1`，`.worktrees/netzoo-cm-cand`。兩臂只差這個 commit。單元測試 3512 passed、35 skipped。
- 規則（`interpretation/checked_match.py`）：no_tool；routing 狀態不是 exact 或 ambiguous；沒有使用者陳述的假設；不是 part D 的 unknown reading；檢查已確認、不是 full gap、沒有未讀句子；每項結果都是 available 或 with_step，且恰有一個已登錄 workflow 涵蓋全部結果 → 該 workflow 成為 exact match（`match_basis: capability_check`），routing state 的候選同步更新。

## 離線證據（凍結前已量）

錄製重放套用規則：n11＋b12 觸發 12 次（KP2×6、BP1×2、BP6、VC7s×3），回覆變成 "Selected path: **DRAGON／CONDOR／SAMBAR／LIONESS-PANDA**"，卡片可規劃該 workflow，render／card 錯誤 0。程式衝突偵測（`collect13.conflicts`：理解段落寫 "available from W"，正文 fallback、未選或選了別的）在 b12 的 204 個錄製回覆中只抓到這 9 個 session（KP2×6、BP1×2、BP6），沒有誤判。

## 題組

`heldout13.json`，30 題、39 項需求（正例 25、負例 14），執行前從未跑過：

- CP 12：同一 workflow 的較少見產出（p 值、enrichment、core 貢獻、activity 檢定、survival、covariate 占比），其中 4 題是第二輪追加（`--resume`）。
- CN 10：舊錄製中檢查過度認可的類型，換新寫法（1 題兩輪）。
- P 4：一個支援、一個不支援。
- CE 4：routing 應 exact 的一般請求（對照）。

## 回合

`m13`：routing 用 mini、檢查用 nemotron，每題 3 次，兩臂交錯，`run_heldout13.py m13 3`。

## 標註

同 Log 404：兩個獨立盲標子代理標全部 session，我複核所有不一致並保存理由。

## 指標

FC（負例被說可做）、FR（正例被說沒有）、正例被說可做的次數、OM、標註者矛盾、程式偵測的檢查／routing 衝突、候選中規則發動次數與其正確性（採用的 workflow 是該題每項需求金標準 `by` 之一，且該題沒有不支援的需求）。

## 判定

| 判定 | 條件 |
|---|---|
| V1 | 每臂 provider 錯誤或逾時 ≤ 10；檢查沒成功的 no_tool ≤ 10；兩臂 90 個 session 齊全；重放相同 |
| G1 | 標註者矛盾：cand ≤ 0.6 × base（base < 4 時無資訊） |
| G1c | cand 程式偵測的檢查／routing 衝突 = 0 |
| G2 | FC：cand ≤ base + 1 |
| G3 | 正例被說可做：cand ≥ base − 1，且 FR：cand ≤ base + 1 |
| G4 | 規則發動 ≥ 3 次時，正確 ≥ 90%（< 3 次無資訊） |
| G5 | CE 對照正例被說可做：cand ≥ base |
| A1 | OM：cand ≤ base + 2 |

保留：所有判定成立或無資訊；任一不成立則撤回（`git revert 1f52ab1`），不在本題組上重量。

## 事前預測

- 規則可能發動在 CP1、CP7（p 值，routing 讀成 pvalue_matrix 而 fallback）、KP1–KP4（第二輪），以及隨機的驗證失敗。
- CN 題若檢查仍過度認可單一 workflow、routing 又 fallback，規則會把錯的檢查判定變成 exact——G2、G4 會擋。
- routing exact 與檢查衝突（不在本候選範圍）仍會留下矛盾，G1 可能因此達不到 0.6。
