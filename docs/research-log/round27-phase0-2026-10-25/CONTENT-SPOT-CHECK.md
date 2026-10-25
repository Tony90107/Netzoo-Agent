# C1 內容標註的抽查與裁定（2026-10-25）

- **標註：** 1 位盲標 subagent，依 `CONTENT-BRIEF.md` 標註，輸出 `content-labels.json`：300 題中 286 題有 `has`，共 687 個單位。
- **抽查：** 用 `spot_sample.py`，`random.Random(27)` 抽 10%，共 69 個單位。我逐一對照請求全文判斷。

## 抽查結果

| 欄位 | 可接受 | 說明 |
|---|---|---|
| `content` | 69/69 | 「my two HepG2 samples」標 `not_stated`，依 brief「只標原話說的」是對的。一段話涵蓋兩份資料時（J13 的 motif 加 miRNA prior），依 brief 標主要那份 |
| `made_by` | 69/69 | 公開資源有點名的（STRING、MSigDB）標 `outside`，沒點名的檔案標 `not_stated`，前後一致 |
| `certainty` | 65/69 | 4 個不同意：C39#4、C50#0、M36#0、Q06#0 |

## `certainty` 的標法和 brief 不一致：全部 53 個 unsure 都重看

- **brief 的定義：** 只有使用者不確定「這份資料**是什麼**或**從哪裡來**」時，才標 `unsure`。
- **標註者的做法：** 只要使用者對資料有任何不確定，就標 `unsure`。例如：
  - 樣本數或基因數有兩個可能；
  - 有沒有做 log 轉換；
  - 是不是同一批人；
  - 檔案存成矩陣還是 edge list；
  - 單細胞還是 bulk。
- **抽到的 4 個分歧都屬於這種**，所以不是零星的錯誤，而是整批的標法問題。我把 53 個 `unsure` 全部重看。

**裁定規則：** 使用者給的幾個可能，如果對應到**不同的 `content` 或不同的 `made_by`**，才算 C1 的 unsure。這條規則是 brief 定義的直接寫法，不是看了 C1 的結果才定的（C1 還沒寫）。

**結果：**
- 53 個 unsure 中，**14 個**符合 C1 的定義，記為 `certainty_c1 = unsure`。
  - 包含普查的目標 C20、C21，以及 H13、L22（TF–基因網路還是基因–基因網路）；
  - 5 個是體細胞還是生殖細胞突變。這個區分已經有 typed 的 `mutation_origin` 欄位，C1 和它會重疊，量測時分開報告。
- 其餘 39 個記為 `stated`，並註明「不確定的不是內容或來源」。這些不確定原本就由其他 typed 欄位或 fact agent 處理。
- **原始標註保留不動。** `adjudicate.py` 輸出 `content-labels-adjudicated.json`，新增 `certainty_c1` 與 `c1_note` 兩個欄位。

**沒查的方向：** 標成 `stated`、但其實應該是 unsure 的單位。抽到的 69 個裡沒有這種情況，所以沒有再全面重看。

## 數量（裁定後）

- **content：** expression 234、tf_gene_prior 100、protein_interactions 99、other_omics 76、gene_annotation 74、sample_annotation 31、somatic_mutation 30、not_stated 12、mirna_prior 11、regulator_gene_network 10、coexpression_matrix 8、other 2。
- **made_by：** outside 399、not_stated 278、PANDA 5、COBRA 4、DRAGON 1。
- **certainty_c1：** stated 673、unsure 14。

## 對 C1 量測的影響

- **衍生資料很少。** 共表現矩陣只有 8 個、調控網路只有 10 個，由 NetZoo workflow 產生的只有 10 個。
  - C-G1（捏造率）會主要由「原始資料被標對」決定，對 C 類錯誤的鑑別力有限。
  - 所以 C-G1 要另外報告**衍生資料子集**的數字，但不改門檻。
- **h10 的 D、U 兩組就是為這種情況設計的。** 開發題組的不足由 h10 補上。
