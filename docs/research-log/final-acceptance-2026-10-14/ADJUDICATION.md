# accept24 標準答案裁定（2026-10-14，執行前）

出題者原稿：`accept24-writer.json`。獨立複核：`gold-review.json`（153 項中同意 147 項）。以下為我的裁定，執行前完成。

| 項目 | 裁定 | 理由 |
|---|---|---|
| U09 | needs_fact -> excluded | Two correct behaviours: LIONESS-PANDA writes the cohort and the per-patient networks, so asking first and offering it directly are both right (gold review). |
| P25 R2 | supported -> with_step | PANDA/OTTER output must be thresholded to a non-negative edge list before CONDOR; no executor does it (panda.yaml, CONDOR notes). Both classes are positive. |
| P11 R2 | by: drop BONOBO | BONOBO needs the data declared log-transformed and centred (data/bonobo.py:201-209); the question asks for one tool giving both. |
| P13 | by: add GIRAFFE | GIRAFFE fits its matrices by minimising a loss, not by message passing. |
| P32 R1 | by: add GIRAFFE | consistent with P02/P25/P28/U12 for an aggregate TF-gene network. |
| U04 | by: add OTTER, GIRAFFE (TF-only branch) | consistency. |

**保留原標準答案、但註記：**
- P17「每條邊的 p 值」：特徵數遠大於樣本數時 DRAGON 的 p 值估計可能失敗（data/dragon.py:153-165），屬執行層的注意事項，不影響能力判定，仍為 supported。
- MX13 R1：LIONESS-DRAGON 有 2,000 萬個值的上限，但題目沒有說特徵數，屬執行層的注意事項，仍為 supported。
- MX12 R2「出版品質的圖」：沒有任何執行器會畫圖，仍為 not_supported（複核者認為也可算 with_step，屬邊界題）。
- N03／MX15 R2：標籤正確；出題者註記中「LIONESS-PANDA 的邊沒有正負號」的說法有誤（邊有正負號，但不代表活化或抑制）。
- N14：標籤依方法定義（CONDOR 只用於二部圖）；執行器對重疊節點只發警告。
- 出題者讀過 registry 的 `OUTSIDE_STEPS`（允許讀的檔案），所以 N01、N15、MX17 的主題與系統既有說明重疊。

**相似度：** 與所有舊題組逐字比對，19/120 題相似度 ≥ 0.55、2 題 ≥ 0.7（K08、N06）。
