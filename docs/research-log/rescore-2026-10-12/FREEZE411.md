# Log 411 事前凍結：用新題組重新評分可執行性判別（2026-10-12，執行前寫下）

使用者要求：Log 409（單一判定）與 Log 410（多輪追問）上線後，用新題組重跑一次 Log 408 的評分。這只是評分，不比較候選，也沒有保留或撤回。

## 受測版本

- `live`：`abca35e`（netzoo-agent/main），`.worktrees/netzoo-score2-live`。
- routing 用 gpt-4o-mini；檢查、重讀、第二意見用 nemotron；追問解析器用 mini。都與上線設定相同。

## 題組

`heldout17.json`，51 題、57 項需求（正例 25、負例 32），執行前從未跑過。各族與 heldout15 相同（PL 9、PS 3、PI 1、PQ 3、NM 14、NF 3、NV 6、MX 6），只有 K 由 4 題增為 6 題（KN 3、KP 3），因為 Log 410 改的就是多輪追問。

- 與所有舊題組逐字比對：9/51 題相似度 ≥ 0.55（heldout15 為 19 題 ≥ 0.5），多是常見的正例說法。
- NV 6 題與 MX6 的第二項是新題型：先前題組沒問過，sheet 也沒列為 near miss。

## 回合

`r17`：每題 2 次，共 102 個 session。執行 `run_heldout17.py r17 2`：K 題第一輪用 `--session`，第二輪用 `--resume`。有了 Log 410，第二輪會經追問解析器，與互動路徑相同。若檢查改由備援 mini 執行的 session 超過 5 個，這些 session 在額度重置後重跑。

## 標註（單人盲標＋我抽查）

- 每個 packet 由一位盲標子代理標註，標籤與 Log 408 相同（`LABELING.md`）。
- K 題看最後一輪的回覆。packet 顯示的是使用者原話。
- 我複核以下 session，更正寫入 `live/r17-labels-checked.json` 並附理由：
  - 每個誤判的需求；
  - 每個標註矛盾的 session；
  - 其餘 session 隨機抽 10%（`random.seed(411)`）。

## 評分（與 FREEZE408 完全相同）

**主要指標**（附 Wilson 95% 信賴區間）：

| 指標 | 定義 |
|---|---|
| FAR（誤承諾率） | 負例被說可做的比例，含 PARTLY。另報不含 PARTLY 的嚴格版 |
| 「可做」精確度 | 被說可做的需求中，真正可做的比例 |
| FRR（誤拒絕率） | 正例被說做不到的比例 |
| 明確度 | 負例被明確拒絕、正例被明確承諾的比例 |
| 矛盾 | 標註為前後矛盾的 session 數 |

**加權分數**：`100 × (0.6·S_neg + 0.4·S_pos)`，其中 `S = 1 − 平均成本／最大成本`。

| 金標準 | 標籤 | 成本 |
|---|---|---:|
| 負例 | NOT_GIVEN | 0 |
| 負例 | 未決（UNCONFIRMED／ASKED／OMITTED） | 1 |
| 負例 | PARTLY | 2 |
| 負例 | 說可做（GIVEN 類） | 3 |
| 正例 | 說可做（GIVEN 類） | 0 |
| 正例 | 未決或 PARTLY | 1 |
| 正例 | NOT_GIVEN | 2 |

負例最大成本 3，正例最大成本 2。

**等級**（由 A 往下，取第一個成立者）：

| 等級 | 條件 |
|---|---|
| A | FAR ≤ 3% 且 FRR ≤ 5% |
| B | FAR ≤ 6% 且 FRR ≤ 10% |
| C | FAR ≤ 12% 且 FRR ≤ 15% |
| D | FAR ≤ 20% |
| F | 其餘 |

**另報**：
- 依族分層，包括 K 族與新題型（NV＋MX6 第二項）；
- 程式層的「正例 routing 提供了正確 workflow」與「檢查判定和金標準一致」比例；
- 與 Log 408（heldout15，`ec97bd6`：FAR 3/64、FRR 2/48、94.7 分、B）並列。兩者題組不同，只能當參考，不能相減。

## 有效性

102 個 session 齊全；重放與錄製相同；provider 錯誤 ≤ 5；檢查由 nemotron 完成的 session ≥ 95%。
