# Log 408 事前凍結：可執行性判別評分（2026-10-11，執行前寫下）

使用者要求：替 NetZoo agent「分辨任務能不能做」的功能評分——能做的要判為可做，不能做的**不能**判為可做；不誤判是第一優先。

這不是候選比較，只量現行上線版。沒有保留／撤回判定，只有評分。

## 受測版本

- `live`：`ec97bd6`（netzoo-agent/main，含 Log 405 checked match、Log 406 重讀、Log 407 "part" 不認可、confirmed partial tie），`.worktrees/netzoo-score-live`。
- routing 用 gpt-4o-mini，檢查／重讀／第二意見用 nemotron（`.env` 的 `OPENROUTER_CAPABILITY_MODEL`），與上線設定相同。

## 題組

`heldout15.json`，50 題、56 項需求（正例 24、負例 32），執行前從未跑過：

| 族 | 題數 | 內容 |
|---|---:|---|
| PL | 9 | 能做，平鋪直述（每個 workflow 至少一題） |
| PS | 3 | 能做，但需使用者在外部補一步（with_step） |
| PI | 1 | 能做，但輸入沒說齊（問輸入算對） |
| PQ | 3 | 能做，以問句形式 |
| NM | 14 | 不能做，緊鄰已登錄結果（sheet 的 near miss 或 result_forms 之外） |
| NF | 4 | 不能做，與網路方法無關 |
| NV | 6 | 不能做，**新題型**：先前題組沒問過、sheet 也沒列為 near miss |
| MX | 6 | 一項能做＋一項不能做（MX6 為新題型） |
| K | 4 | 第二輪只加限制（KN 不能做、KP 能做，`--resume`） |

金標準依 `scripts/capability_sheet.yaml`（`produces` 封閉世界；with_step 算能做）。多數正例與 NM／NF 題型在舊題組出現過（措辭不同），所以另報「新題型」（NV＋MX6 第二項）分層結果，作為泛化的參考。

## 回合

`x15`：每題 **2 次**，共 100 個 session，`run_heldout15.py x15 2`，5 個並行。

## 標註（單人盲標＋我抽查）

一個盲標子代理標全部 session（`LABELING.md`，與 Log 406 相同的 8 種標籤；不告知金標準）。我複核：(a) 每個被標為誤判的需求（負例 GIVEN／GIVEN_WITH_STEP／GIVEN_IF_INPUT／PARTLY；正例 NOT_GIVEN）；(b) 每個標註矛盾的 session；(c) 其餘 session 隨機 10%（`random.seed(408)`）。更正寫入 `live/x15-labels-checked.json` 並附理由。

## 評分（執行前固定）

每個（session, 需求）依最終標籤歸類：

| 金標準 | 正確 | 未決（安全但不明確） | 部分 | 誤判 |
|---|---|---|---|---|
| 不能做 | NOT_GIVEN | UNCONFIRMED／ASKED／OMITTED | PARTLY（算誤承諾） | GIVEN／GIVEN_WITH_STEP／GIVEN_IF_INPUT |
| 能做 | GIVEN／GIVEN_WITH_STEP／GIVEN_IF_INPUT | UNCONFIRMED／ASKED／OMITTED／PARTLY | — | NOT_GIVEN |

主要指標（附 Wilson 95% 信賴區間）：

1. **誤承諾率 FAR**＝負例被說可做（含 PARTLY）／負例。第一優先。另報不含 PARTLY 的嚴格版。
2. **「可做」判定精確度**＝正例被說可做／所有被說可做（含負例的 PARTLY）。
3. **誤拒絕率 FRR**＝正例被說不可做／正例。
4. 明確度：負例明確拒絕率、正例明確承諾率。
5. 標註矛盾的 session 數。

加權分數（0–100）：成本 負例 NOT_GIVEN 0、未決 1、PARTLY 2、說可做 3；正例 說可做 0、未決或 PARTLY 1、NOT_GIVEN 2。
`S_neg = 1 − 平均成本/3`、`S_pos = 1 − 平均成本/2`、**分數 = 100 × (0.6·S_neg + 0.4·S_pos)**。

等級（誤承諾優先，依序取第一個成立者）：

| 等級 | 條件 |
|---|---|
| A | FAR ≤ 3% 且 FRR ≤ 5% |
| B | FAR ≤ 6% 且 FRR ≤ 10% |
| C | FAR ≤ 12% 且 FRR ≤ 15% |
| D | FAR ≤ 20% |
| F | FAR > 20% |

程式可判的輔助指標（不需標註）：正例中 routing 提供或選定的 workflow 是否含金標準 `by`；檢查（L2）對每項需求的判定與金標準的一致率。

## 有效性

- 100 個 session 齊全、重放與錄製相同、provider 錯誤 ≤ 5。
- 檢查由 nemotron 完成（非備援 mini）的 session ≥ 95%。若今日免費額度用盡導致備援超過 5 個，該批 session 於 08:00 額度重置後重跑，並在結果中註明。
