# NetZoo agent 推論與工具選擇測試 Prompt（中英對照）

目的：測試 agent 能不能**從研究情境推論**出該用哪個 netZooPy 演算法。Prompt 裡刻意不寫演算法名稱，也不直接說出意圖。
每一題都附上預期的工具、推理依據、輸入對應、該問的澄清問題和扣分訊號。

- 資料路徑都是 repo 內既有的 `data/*-toy/`，可以直接執行。toy 資料很小，**重點看推理和規劃，不看生物結果**。
- 工具名稱對應 agent 內部的 `run_panda`、`run_puma`、`run_lioness_panda`、`run_lioness_puma`、
  `run_lioness_coexpression`、`run_bonobo`、`run_otter`、`run_giraffe`、`run_cobra`、`run_dragon`、`run_condor`、`run_sambar`。
- 建議用 traced capture 跑，失敗時可以離線 replay 原始 provider I/O。

> **重要：盲測要用中性路徑。**
> `data/bonobo-toy/` 這類目錄名會被 agent 當作使用者點名了工作流程（`named_registered_action` 會讀路徑 token）。這樣 agent 會「答對」，但不是靠推論（見 research log Log 137）。
> 會洩漏答案的目錄名有 bonobo、giraffe、otter、cobra、dragon、condor、sambar。
> 測試前請先複製成中性名稱，再把 prompt 裡的路徑換成對應的 `$B/case-N/`：
>
> ```bash
> B=data/blind-neutral; mkdir -p $B
> for pair in 1:giraffe-toy 2:otter-toy 3:bonobo-toy 4:lioness-toy 5:lioness-toy 6:cobra-toy 7:dragon-toy 8:sambar-official-toy 9:condor-toy; do
>   n=${pair%%:*}; src=${pair#*:}; mkdir -p $B/case-$n; cp data/$src/* $B/case-$n/; done
> ```

## 評分規則（每題 10 分）

| 面向 | 0 | 1 | 2 |
|---|---|---|---|
| A. 工具選擇 | 選錯 | 主工具對，但沒提出合理的替代方案 | 主工具對，並提出 1–2 個替代方案 |
| B. 推理依據 | 沒解釋或只重複檔名 | 解釋得籠統（例如「適合網路分析」） | 用演算法假設說明（例如 message passing、leave-one-out 線性、偏相關、覆蓋矩陣分解） |
| C. 輸入對應與格式檢查 | 檔案角色錯置 | 角色正確，但沒檢查方向或樣本對齊 | 角色正確，也檢查了 genes×samples 方向、樣本 ID 對齊、ID 型別 |
| D. 澄清與不幻覺 | 自己編造缺少的輸入或參數 | 有問，但問得不必要或漏問關鍵 | 只問真正會改變結果的問題 |
| E. 輸出詮釋與下一步 | 沒說明輸出 | 列出檔名 | 說明輸出矩陣的意義，並提出下游分析 |

---

## Case 1：TF 活性 ≠ TF 表現量（GIRAFFE vs PANDA vs OTTER）

**中文**
> 我在 `data/giraffe-toy/` 放了表現量、motif 和蛋白交互作用的表。我懷疑有個轉錄因子在不同樣本之間實際「在做事」的程度不一樣，但它自己的 mRNA 幾乎沒什麼變化。我想知道每個樣本裡哪些調控因子比較活躍，順便看一下調控關係。

**English**
> In `data/giraffe-toy/` I have expression, a motif table, and a protein-interaction table. I suspect one transcription factor is doing different amounts of work across samples even though its own mRNA barely changes. I'd like to know which regulators are more active in each sample, and see the regulatory relationships too.

**預期**
- 主工具：`run_giraffe`
- 推理依據：TF 的 mRNA 量不能代表它的活性（磷酸化、核轉位、輔因子等都發生在轉錄之後）。GIRAFFE 把表現矩陣分解為 G ≈ R · TFA，**同時**估出調控網路 R（TF×gene）和每個樣本的 TF 活性矩陣 TFA（TF×sample）。
- 替代方案：
  - PANDA 或 OTTER 只給一張整體的 TF×gene 網路，沒有每個樣本的活性。
  - LIONESS-PANDA 加 targeting 分數可以當作近似指標，但那是網路拓樸，不是活性。
- 輸入對應：`expression.tsv` 當表現量（genes×samples），`motif.tsv` 當先驗 R0，`ppi.tsv` 當 TF–TF 交互作用。
- 輸出：調控矩陣 R 和 TFA 矩陣。下一步應建議比較那個 TF 的 TFA 與它 mRNA 的相關性。
- 扣分訊號：只跑 PANDA；把 TF 的表現量直接當成活性；沒提到 TFA。

## Case 2：大規模整體網路，在意效率與收斂（OTTER vs PANDA）

**中文**
> 我要為一個組織建一張共識的調控網路，資料在 `data/otter-toy/`（正式資料會有約 2 萬個基因、1000 個 TF）。上次用類似方法跑到記憶體爆掉、而且迭代很久才停。我比較希望結果對應到一個明確的最佳化目標，而不是一堆迭代更新規則。

**English**
> I need one consensus regulatory network for a tissue. The data is in `data/otter-toy/` (the real data will be ~20k genes and ~1000 TFs). Last time a similar method ran out of memory and took forever to stop iterating. I'd prefer the result to correspond to a well-defined optimization objective rather than a pile of iterative update rules.

**預期**
- 主工具：`run_otter`
- 推理依據：OTTER 把問題寫成一個目標函數：讓 W 同時貼近 PPI（WWᵀ ≈ P）和共表現（WᵀW ≈ C），再用梯度下降求解。計算量比較低，也符合「有明確最佳化目標」的要求。
- 替代方案：PANDA 是 message passing（反覆更新 responsibility 和 availability），做法成熟、文獻多。如果使用者要沿用 PANDA 的結果或和舊結果比較，可以用 `precision='single'`、GPU 或 `save_memory` 減輕記憶體問題。
- 參數：OTTER 的 `lam`、`gamma`、`Iter`、`eta` 應說明並採用預設值，不要亂調。
- 輸出：TF×gene 權重矩陣 W，意義和 PANDA 的 edge weight 相近，但數值尺度不同，**不能直接比較數值**。
- 扣分訊號：沒提到 PANDA 作為替代方案；宣稱兩者輸出可以直接相減。

## Case 3：少數病人、每人各自的共表現、要可信度（BONOBO vs LIONESS-coexpression）

**中文**
> 我只有少數幾個病人的表現資料（`data/bonobo-toy/expression.tsv`），沒有其他先驗檔。我想看每一個病人自己的基因共表現結構有什麼不同，最好還能告訴我哪些連結在那個病人身上是可信的。

**English**
> I only have expression data from a handful of patients (`data/bonobo-toy/expression.tsv`) and no prior files. I want to see how each patient's own gene co-expression structure differs, and ideally know which connections are trustworthy in that particular patient.

**預期**
- 主工具：`run_bonobo`
- 推理依據：BONOBO 是 Bayesian 方法。它用其他樣本建立先驗（inverse-Wishart），估出每個樣本的共變異，並提供 p-value。它不依賴 leave-one-out 的線性內插假設，也比較適合樣本數少的情況。
- 替代方案：LIONESS-coexpression 也能給每個樣本一張網路，但要警告兩件事：n 很小時，拿掉一個樣本對整體影響太大，估計會不穩定；而且 LIONESS 的網路是相對於母體的差異，樣本之間不獨立。
- 關鍵：沒有 motif 和 PPI，所以**不能**選 LIONESS-PANDA 或 GIRAFFE。如果使用者之後想要 TF→gene 的調控，要主動說明需要補哪些先驗檔。
- 扣分訊號：選了需要 motif 的工具；完全不提樣本數；自己編造 motif。

## Case 4：有先驗、要每個樣本的 TF→gene 調控，之後接存活分析（LIONESS-PANDA）

**中文**
> `data/lioness-toy/` 有表現量、motif、PPI。我認為每個病人的調控接線方式不一樣，之後想把「每個人身上各 TF 對其目標基因的調控強度」拿去跟存活時間做關聯。

**English**
> `data/lioness-toy/` has expression, motif and PPI files. I believe each patient's regulatory wiring is different, and later I want to relate each person's per-TF regulatory strength over its targets to survival time.

**預期**
- 主工具：`run_lioness_panda`
- 推理依據：LIONESS 用 leave-one-out 線性內插，e_q = N·(e_all − e_{−q}) + e_{−q}，從整體 PANDA 網路反推出每個樣本的 TF×gene 網路，保留了 motif 和 PPI 的先驗。
- 下游：每個樣本算 TF outdegree（targeting 分數），做成 TF×sample 矩陣，再接 Cox 回歸。
- 替代方案：
  - BONOBO 產生每個樣本的共表現，再餵給 PANDA，可以避開線性假設。可以和 Case 3 對照。
  - GIRAFFE 的 TFA（TF×sample）也是合理的讀法：「每個人各 TF 的強度」可以理解成 TF 活性。所以選 GIRAFFE **不算錯**。
- 真正的扣分點是**只給一條路、不說明兩種讀法的差異**：
  - targeting／outdegree 衡量「網路接線強度」，來自 LIONESS-PANDA。
  - TFA 衡量「TF 活性」，來自 GIRAFFE。
  - 應把兩者並列，讓使用者依假設選擇。
- 必要澄清：臨床存活資料沒有提供，應該問；應提醒 toy 資料只有 4 個樣本，LIONESS 網路之間不獨立，統計檢定要小心。
- 扣分訊號：只跑整體 PANDA；自己編造存活資料；把 indegree 和 outdegree 搞混（TF 層級要用 outdegree）。

## Case 5：先驗表裡混有 miRNA（PUMA vs PANDA）

**中文**
> 我的先驗調控表（`data/lioness-toy/prior-puma.tsv`）裡除了轉錄因子，還混了一些小 RNA 對基因的預測標靶，那些小 RNA 的名字列在 `mirna.txt`。表現量和 PPI 用同資料夾的。我想得到一張整體的調控網路。

**English**
> My prior regulatory table (`data/lioness-toy/prior-puma.tsv`) contains not only transcription factors but also predicted targets of some small RNAs; those small RNAs are listed in `mirna.txt`. Use the expression and PPI files in the same folder. I want one overall regulatory network.

**預期**
- 主工具：`run_puma`
- 推理依據：miRNA 在轉錄後調控，不會和 TF 形成蛋白複合體。PUMA 會把 miRNA 在 PPI/cooperativity 矩陣中的部分設為不和其他調控因子合作。如果直接跑 PANDA，就等於錯誤假設 miRNA 能透過 PPI 協同調控。
- 輸入對應：`prior-puma.tsv` 當先驗（TF 和 miRNA → gene），`mirna.txt` 當 miRNA 清單，`ppi.tsv` 只含 TF，`expression.tsv` 當表現量。
- 延伸：如果使用者追問「每個樣本」，應該接 `run_lioness_puma`。
- 扣分訊號：忽略 `mirna.txt`；選 PANDA；把 `motif-panda.tsv` 誤當先驗。

## Case 6：批次效應和共表現（COBRA）

**中文**
> 這批樣本分兩次上機，`data/cobra-toy/design.tsv` 有記錄，表現量在 `expression.tsv`。我想知道共表現結構裡哪些部分是批次造成的，哪些是批次以外的。

**English**
> These samples were sequenced in two runs, recorded in `data/cobra-toy/design.tsv`; expression is in `expression.tsv`. I want to know which parts of the co-expression structure are driven by the batch and which are not.

**預期**
- 主工具：`run_cobra`
- 推理依據：COBRA 先對共表現做特徵分解，再用 design matrix 對每個特徵成分做迴歸，得到 covariate-specific 的係數 ψ。每個共變量 k 的共表現成分是 Q·diag(ψ_k)·Qᵀ，所以能把批次的貢獻和基線（intercept）分開。
- 格式檢查（隱藏考點）：`design.tsv` 的樣本順序是 S3、S1…，和表現矩陣的欄位順序不同，**必須先對齊**。另外，`intercept` 欄已經存在，不能再自動加一次截距。
- 替代方案：兩個批次各自算共表現再相減。這樣無法同時調整多個或連續的共變量，統計效率也比較差。
- 輸出：ψ、Q、D、G。應說明 ψ 的 intercept 列對應基線，batch 列對應批次效應。
- 扣分訊號：沒對齊樣本；選 PANDA 或 LIONESS；截距加了兩次。

## Case 7：兩層 omics 的「直接」關聯（DRAGON）

**中文**
> 同一批人我同時有基因表現（`data/dragon-toy/layer1.tsv`）和甲基化（`layer2.tsv`）。我想知道哪些甲基化位點和基因是直接相關，而不是透過其他變數間接連在一起。

**English**
> For the same individuals I have gene expression (`data/dragon-toy/layer1.tsv`) and methylation (`layer2.tsv`). I want to know which methylation sites and genes are directly associated, not linked indirectly through other variables.

**預期**
- 主工具：`run_dragon`
- 推理依據：「直接 vs 間接」對應偏相關，也就是 Gaussian graphical model。DRAGON 對兩層資料分別給收縮參數（λ1、λ2），因為兩層的維度和雜訊不同。
- 格式檢查（隱藏考點）：`layer2.tsv` 的樣本順序（s4、s2…）和 `layer1.tsv` 不同，**必須依 sample_id 對齊**。兩個檔都是 samples×features，不需要轉置。
- 輸出：偏相關矩陣，分為 layer 內和 layer 間兩個區塊。跨層區塊才是使用者要的答案，並應附上 p-value 和 FDR。
- 替代方案：Pearson 相關會把間接關聯也算進去；兩層合併後只用單一收縮參數，則會忽略兩層的差異。
- 扣分訊號：沒對齊樣本；用 PANDA 或共表現；只回報 layer 內的結果。

## Case 8：突變太稀疏，想分群病人（SAMBAR）

**中文**
> 我有一群子宮內膜癌病人的體細胞突變 0/1 表（`data/sambar-official-toy/mut.ucec.csv`），同資料夾還有基因長度、基因清單和一個 pathway gmt。單一基因的突變太稀疏了，我想把病人分群。

**English**
> I have a 0/1 somatic mutation table for a group of endometrial cancer patients (`data/sambar-official-toy/mut.ucec.csv`). The same folder has gene lengths, a gene list and a pathway GMT. Single-gene mutations are too sparse; I want to group the patients.

**預期**
- 主工具：`run_sambar`
- 推理依據：
  - 長基因比較容易累積 passenger 突變，所以先用基因長度（`esizef.csv`）校正。
  - 再依 GMT 把突變匯總到 pathway 層級，解決稀疏問題。
  - 最後用 binomial distance 做階層式分群。
- 輸入對應：`mut.ucec.csv` 是 samples×genes，`esizef.csv` 是基因長度，`genes.txt` 是癌症相關基因清單，`h.all.v6.1.symbols.gmt` 是 pathway。
- 參數：`kmin`、`kmax`（分群數範圍）應詢問，或說明採用預設值。
- 輸出：`mt_out`（校正後的突變分數）、`pt_out`（pathway 分數）、分群結果。
- 扣分訊號：直接對原始 0/1 矩陣分群；忽略基因長度；選 CONDOR。

## Case 9：二分網路中「一起工作」的群體與核心成員（CONDOR）

**中文**
> 我手上有一張調控因子—基因的連結表（`data/condor-toy/bipartite.tsv`）。我想知道有沒有一群調控因子是一起管一群基因的，並找出每一群裡最核心的成員。

**English**
> I have a regulator–gene link table (`data/condor-toy/bipartite.tsv`). I'd like to know whether groups of regulators jointly control groups of genes, and who the most central members of each group are.

**預期**
- 主工具：`run_condor`
- 推理依據：這是二分網路的社群偵測（Barber bipartite modularity）。每個社群同時包含 regulator 和 gene。core score（qscore）衡量節點對所屬社群 modularity 的貢獻，可以用來找核心成員。
- 應說明：不應把二分網路投影成單一模式網路再做社群偵測，因為會失去資訊。如果輸入是 PANDA 的輸出，應先取正權重或 top edges 再跑 CONDOR。
- 格式：檔案開頭有 `#` 註解行，要正確跳過；欄位是 source、target、weight。
- 扣分訊號：再跑一次 PANDA；投影成單一模式網路；解析註解行失敗。

## Case 10：只有表現矩陣，需求模糊（澄清能力）

**中文**
> 我只有這個表現矩陣 `data/blind-tests/case-1/expression.tsv`，幫我建一個網路看看。

**English**
> All I have is this expression matrix, `data/blind-tests/case-1/expression.tsv`. Build me a network and let's see.

**預期**
- **不應**直接執行，也**不應**自己編造 motif。
- 應提出的關鍵澄清：
  1. 網路的邊要代表什麼？
     - 基因—基因共表現：PANDA 不給 motif 時會退化成共表現網路，或用 `run_lioness_coexpression`、`run_bonobo`。
     - TF→gene 調控：需要 motif 先驗。
  2. 要整體一張網路，還是每個樣本各一張？
- 隱藏考點：同資料夾其實有 `motif.tsv` 和 `ppi.tsv`。好的 agent 會主動發現它們，並**詢問**是否要一起使用，而不是自動拿來用。
- 扣分訊號：直接跑 PANDA 並自動抓同資料夾的檔案、不告知使用者；編造先驗；問了一大串無關的問題。

---

## 進階加分題

### Bonus A：腫瘤 vs 正常的差異網路（三方選擇：PANDA×2 相減 / COBRA / 樣本層級網路＋檢定）

**中文**
> 我想比較腫瘤和正常組織的調控差異，看哪些 TF 重新接線了。病人年齡和性別差很多。

**English**
> I want to compare regulation between tumor and normal tissue and see which TFs got rewired. The patients differ a lot in age and sex.

**預期**：沒有給資料，應該進入規劃和澄清，不能執行。應依假設分三條路線推薦：

| 假設 | 路線 |
|---|---|
| 兩組各有一個代表性的網路，差異在群組層級 | 兩組各跑 PANDA，再比較 edge weight 和 targeting 差異 |
| 需要調整年齡、性別等混雜因子 | COBRA（把 tumor/normal、age、sex 放進 design），可再把校正後的共表現接進 PANDA |
| 組內異質性大，需要每個樣本的統計檢定 | LIONESS-PANDA 或 BONOBO→PANDA，再用 limma 或迴歸（共變量放 age、sex）逐邊檢定 |

- 因為使用者提到年齡和性別，推薦應**偏向後兩者**，並詢問各組樣本數。
- 扣分訊號：只給 PANDA×2 相減，完全忽略混雜因子。

### Bonus B：錯誤前提的反駁

**中文**
> 用 `data/lioness-toy/` 幫我做每個樣本的調控網路，然後直接拿這四張網路做 t 檢定比較前兩個和後兩個樣本。

**English**
> Use `data/lioness-toy/` to build a regulatory network for each sample, then run a t-test comparing the first two samples' networks with the last two.

**預期**
- 可以規劃 `run_lioness_panda`，但**必須指出**兩個問題：
  - 每組只有 n=2，檢定幾乎沒有統計效力。
  - LIONESS 的網路來自同一個整體網路，彼此不獨立，這違反 t 檢定的假設。
- 應建議增加樣本，或改成描述性比較。
- 扣分訊號：照做而且沒有任何警告。
