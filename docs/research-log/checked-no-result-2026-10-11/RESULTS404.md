# Log 404 結果：部分 1 撤回、部分 2 保留（未發動）（2026-10-11）

事前凍結：`FREEZE404.md`（`3461798`）。回合 `b12`：heldout12 34 題 × 2 臂 × 3 次，204 個 session，全部重放與錄製相同；provider 錯誤 0、檢查失敗 0。候選臂 MN3-3 第一次執行因既有的 renderer 錯誤崩潰（見下），在凍結的候選程式上重跑該 session 一次。

## 標註

兩位盲標子代理各標全部 204 個 session／114 項需求＋M 題 consult。只有 4 個 session 不一致（S097、S114、S124、S188），我逐一複核，四個都取對候選不利的一側（理由在 `live/b12-labels-resolved.json`）：MC3-1 的未確認列表碰巧寫出 core score 定義，仍定 LISTED_ONLY；MN3-3 只列 OTTER 輸入與參數，定 LISTED_ONLY；PN1-3、PN3-2 記為矛盾。重複抽樣是同一題的重複觀測，不是獨立題目。

## 數字

| 指標 | base | cand |
|---|---:|---:|
| QN＋KN 負例 FC | 2 | 0 |
| P 負例 FC | 0 | 0 |
| 全部 FR | 0 | 0 |
| QP＋KP 正例 SR（未確認／未給／部分／遺漏） | 3 | 7 |
| UC 未確認 | 5 | 14 |
| M 題 CL（只列 workflow 或拒絕） | 12 | 14 |
| MN（點名方法）CL | 6 | 5 |
| B 題 FR＋軟拒絕 | 0 | 0 |
| 程式偵測矛盾 | 8 | 0 |
| 標註者矛盾 | 10 | 10 |
| 檢查讀不到結果的 turn | 18 | 19 |
| 部分 2 第二意見發動 | — | 0 |

判定：V1 PASS；1-G1 無資訊（base FC 2 < 4）；**1-G2 FAIL**（7 > 3+2）；**1-G3 FAIL**（14 > 12+1）；1-G4 PASS；2-G1 PASS；2-G2 PASS；A-G1 PASS。

## 決定

- **部分 1 撤回。** 代價集中而且確定：KP3（第二輪「Our regulators also include miRNAs」）3/3 由 GIVEN_IF_INPUT 變成 UNCONFIRMED；MC3（概念題）3/3 由 EXPLAINED 變成 LISTED_ONLY；QP3 1 次變 UNCONFIRMED。效益沒有重現：base 在 QN＋KN 只有 2 次誤承諾，標註者矛盾不變（10／10）。檢查讀不到結果時，routing 的候選常常是對的；把整個 turn 改成未確認，等於拿正確的回答換取少數誤承諾。以 `2eee5e3` 的三個檔案還原（`unconfirmed_routes.py`、`reply_cards/builder.py`、`cli/follow_up.py`）。
- **部分 2 保留。** 依凍結規則（不造成傷害＋錄製證據），本輪 0 次發動，所以沒有實測效益；heldout11 VC4s-2 的錄製重放是它唯一的證據。

## 本輪找到並修正的產品錯誤（與候選分開提交）

- `332af36`：`--resume` 接續已完成的一次性 session 會因 trace 封存而崩潰；修好後上一輪的 token 被帶進新的一輪，routing 因預算不足失效。這也表示 Log 403 heldout11 的 T 題（`--session` 每輪重開）從未真正多輪。
- `ad4cb2e`：`unknown` reading 下推薦了 workflow 時，精簡 catalog 少了 `accepted_input_modalities`／`transformations`，回覆以 KeyError 崩潰（上線版 `2eee5e3` 可重現）。

## 下一步（P1 第 3 項尚未解決的部分）

兩臂各 10 個標註矛盾中，大多是同一類：理解段落用檢查的判定（"available from DRAGON／CONDOR／SAMBAR"），正文或卡片卻跟著 routing 的選擇（"Fallback recommendation: BONOBO"、"no workflow was selected"、為 enrichment 提供 DRAGON、"GIRAFFE fits" 對上 "partly available"）。KP2 兩臂都是 3/3。冒煙測試的 COBRA 對 SAMBAR 也是這一類；錄製資料中 routing exact 的 408 個 turn 有 16 個與檢查認可的 workflow 不一致。下一個候選應讓回覆與卡片在兩者衝突時讀同一個逐項判定，而不是再加一層 renderer 規則；需要新的未見題組（heldout12 已見）。
