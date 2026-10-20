# ROUND-06：讀到 CSV，執行仍用 .h5（2026-10-20）

計畫：`collab/ROUND-06-PLAN.md`。程式：`97327997`（分支 `closed-menu-phase0`，沒有推送）。$0，沒有呼叫模型。

## 原因（從已存 session 確認）

| 原因 | 題目 | 說明 |
|---|---|---|
| A | h3 L15、C40 p1/p2/p3 | 在 guidance turn 採用使用者要求的 run（`_with_requested_run`）時，完全不綁定能力核對讀到的設定。只有 routing 自己規劃的 run（`_on_run_verdict`）會綁定。 |
| B | C40 p3/p5r | 設定的值只寫在名稱原文裡（「saved as .csv files」，值欄位空）。綁定只看值欄位，於是當成「沒有值」靜默略過。 |
| B′ | C40 p1/p2/p5r | 樣本清單「only write networks for samples MS_03, MS_11 and MS_19」也一樣被略過，run 會替 27 個樣本全部寫出網路。 |

## 修正

1. `_bind_run_settings`：兩條 run 路徑共用同一個綁定。採用路徑遇到不能綁定的設定時，改為保留並提供確認（`hold_run`），和一般 run 路徑一樣。
2. `run_setting_value`：值欄位空時，從設定自己的原文取值，條件如下：
   - 原文只點名一個允許值，或只有一個數字（名稱裡的數字，如 lambda1 的 1，不算）；
   - 而且通過能力核對同一套範圍與允許值檢查。
3. 清單或名稱類設定無法帶進 run 時，run 等待，不再靜默略過。這一輪不從散文解析清單。
4. 綁定與能力核對對同一句話的判讀對齊：數字類設定的值字詞裡沒有數字（J11「leave lambda1 and lambda2 empty so they're estimated」→ 值 "empty"），兩邊都當成「沒有指定值」，用預設（估計），不擋下 run。
   - 第一版沒有這條。採用路徑一套用舊規則，J11（金標 do）就被擋下；重放時發現後修正。

## 重放（180 個已存 run turn，`replay.py`、`compare.txt`）

10 個改變，沒有其他變化：

| 題 | 路徑 | 之前 → 之後 |
|---|---|---|
| C40 p1、p2 | 採用 | 沒綁定 → `.csv`；樣本清單 → run 等待 |
| C40 p3 | 採用 | 沒綁定 → `.csv` |
| C40 p5r | run | `.csv` 補上；樣本清單 → run 等待 |
| L15 | 採用 | 沒綁定 → sparsify、confidence 0.01、save_pvals、delta 0.3、`.csv` |
| P11-2（OTTER） | 採用 | 沒綁定 → cpu、double、iterations 75、edge_list |
| M40（h4、h4smoke） | 採用 | 沒綁定 → lambda1 0.3、matrix |
| M38 smoke（SAMBAR） | run | kmin 2、kmax 10 原本遺失，現在綁定 |
| C52 g4o2 | run | 補上 genes_axis=rows（「genes in rows and sample IDs in the header」） |

測試：新增 7 個；全套 4716 passed、51 skipped。

## 對分數的影響（要誠實說）

C40 的金標是 do。修正前它被判 DO，但真的執行的話會寫 `.h5`、而且寫出全部 27 個樣本。修正後，有讀到樣本清單的回合（p1、p2、p5r）會等待使用者確認。

**所以照核心分數，C40 會從「對」變成「錯」。** 行為比以前誠實，但還不是金標要的結果。要做到 DO，需要把清單（MS_03, MS_11, MS_19）從設定原文帶進 run。BONOBO 執行前會檢查樣本 ID 是否在表頭裡，打錯會在執行前被擋下，不會靜默跑錯。不過「不從散文讀清單」是既有規則，要不要改由使用者決定。

## 沒做

- 不從散文解析清單。
- 沒有 live 驗證：這些 session 都在輸入預檢（找不到檔案）就停了，真正執行時的參數只能從決策欄位推定。
