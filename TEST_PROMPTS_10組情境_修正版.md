# NetZoo Agent 10 組情境測試（修正版）

為驗證 NetZoo Agent 在「語意模糊」、「隱含生物學需求」與「多演算法邏輯重疊」情境下的決策與路由能力，設計 10 組情境測試。每組包含：

1. 隱含生物學意圖與挑戰（不提演算法名稱、不提 netZooPy、不提具體檔名）
2. 中／英雙語測試 Prompt（模擬研究者描述問題的方式）
3. 工具抉擇邊界（候選工具在方法上的差異）
4. 預期 Agent 輸出（主動澄清、權衡比較、情境推薦）

> **登錄範圍提醒**：Agent 目前登錄 13 個 workflow（panda、otter、puma、lioness-panda、lioness-puma、lioness-coexpression、lioness-dragon、bonobo、dragon、cobra、condor、giraffe、sambar）。Test 4（SCORPION）、Test 7（SPIDER）、Test 8（ALPACA）的最佳工具**不在登錄範圍內**，預期行為是：說明未登錄、給出可手動串接的路徑，不得假裝可直接執行。

---

## Test 1：Baseline GRN Inference（訊息傳遞 vs. 鬆弛圖匹配）

- **隱含意圖**：使用者有 bulk RNA-seq、TF motif 先驗與 PPI，想建構整體（aggregate）的 TF→基因調控網路。
- **工具邊界**：`PANDA` vs. `OTTER`。兩者輸入相同（表現量、motif 先驗、PPI）。PANDA 以三張網路之間的迭代訊息傳遞更新至收斂；OTTER 把問題寫成具明確目標函數的鬆弛圖匹配（relaxed graph matching），以梯度法求解。
- **Prompt（中）**：
  「我們剛完成一批肺癌組織的轉錄組定序，手邊也有標準的轉錄因子結合基序資料和已知的蛋白質交互作用資料。我們想估計這批組織中每個轉錄因子對靶基因的整體調控強度，並希望同時考慮轉錄因子之間形成複合體的協同作用。請問該用什麼方法建構這樣的網路？」
- **Prompt（EN）**：
  "We just finished RNA-seq on a batch of lung cancer tissues, and we also have standard transcription factor motif binding data and known protein-protein interaction data. We want to estimate how strongly each transcription factor regulates its target genes across these tissues, while also accounting for TFs that cooperate in complexes. What method should we use to build this network?"
- **預期 Agent 輸出**：
  - 識別意圖：整合表現量、motif 先驗與 PPI 的 aggregate TF→基因網路。
  - 候選比較：
    - **PANDA**：在共表現、motif 先驗、PPI 三張網路間迭代傳遞訊息直到收斂；使用最廣，且可直接接 LIONESS 產生每個樣本的網路。
    - **OTTER**：以明確目標函數表述為鬆弛圖匹配，用梯度下降最佳化；通常比 PANDA 快。目標函數一般**非凸**，不保證全域最優。
  - 推薦決策：這是一組 tie，應並列兩者並詢問：之後是否需要每個樣本的網路（→ PANDA，可接 lioness-panda）？或偏好明確目標函數的形式（→ OTTER）？兩者輸出都是 aggregate 網路，不是樣本特異網路。
  - **陷阱**：不得宣稱 OTTER 是凸最佳化、有全域最優保證，或比 PANDA 更耗時。

---

## Test 2：Sample-Specific GRN（單一樣本網路）

- **隱含意圖**：使用者想為每位病患取得專屬網路，但每人只有一個樣本，無法單獨計算相關係數。
- **工具邊界**：`LIONESS` vs. `BONOBO`。LIONESS 以留一法線性內插，從「全體網路」與「去掉第 q 個樣本的網路」推估第 q 個樣本的網路，可包覆任何 aggregate 方法；BONOBO 以貝氏方法直接估計每個樣本的基因–基因共表現網路。
- **Prompt（中）**：
  「我們收集了 40 位心衰竭病患的微陣列表現資料，病人之間的臨床表現差異極大。如果只算整群的平均網路，會把個別差異抹平；但每位病患只有一個時間點的組織樣本，單一病人根本算不出皮爾森相關係數。有沒有辦法從這批資料中，還原出每一位病患各自的分子調控網路？」
- **Prompt（EN）**：
  "We have microarray expression profiles from 40 heart failure patients with highly heterogeneous clinical presentations. A single population-level network would average away individual differences, but each patient contributed only one tissue biopsy, so a per-patient correlation cannot be computed. How can we reconstruct a separate regulatory network for each patient from this cohort?"
- **預期 Agent 輸出**：
  - 識別意圖：單一樣本網路重建（single-sample network reconstruction）。
  - 候選比較：
    - **LIONESS**：e⁽q⁾ = N·(e⁽α⁾ − e⁽α−q⁾) + e⁽α−q⁾，其中 N 為樣本數、e⁽α⁾ 為全體網路邊權重、e⁽α−q⁾ 為去掉樣本 q 後的邊權重。包覆 Pearson 共表現 → lioness-coexpression；包覆 PANDA → lioness-panda（需 motif 先驗與 PPI）。
    - **BONOBO**：以其餘樣本作為先驗，貝氏估計每個樣本的基因–基因共表現網路；輸出是 gene–gene，不是 TF→gene。
  - 推薦決策：使用者**沒有說明**是否有 motif/PPI，且「調控網路」可指 gene–gene 或 TF→gene，應先詢問。只有表現量 → lioness-coexpression 或 BONOBO；有 motif + PPI 且要 TF→gene → lioness-panda。並提醒 LIONESS 需要對 40 個樣本各重跑一次 aggregate 方法的計算成本。

---

## Test 3：Bipartite Community Detection（二分網路模組）

- **隱含意圖**：使用者已有 TF→基因網路，想找調控模組；網路是二分圖（TF 與基因兩類節點），不適合直接套用單一節點類型的社群偵測。
- **工具邊界**：`CONDOR` vs. 一般社群偵測（如 Louvain/Leiden）。
- **Prompt（中）**：
  「我們已經算好了轉錄因子到靶基因的調控邊權重矩陣，現在想把網路切成幾個緊密的調控模組，看看哪些轉錄因子群共同主導哪一群基因。我們試過一般的模組劃分方法，但它把轉錄因子和靶基因當成同一種節點，忽略了這是一張兩類節點的二分網路。有沒有專門處理這種兩類節點社群結構的方法？」
- **Prompt（EN）**：
  "We have finished computing the TF-to-target regulatory edge weights. We now want to partition this network into tightly connected regulatory modules to see which groups of TFs jointly control which sets of target genes. Standard community detection treats all nodes as the same type and ignores that this is a bipartite network. What method properly detects communities across two distinct node types?"
- **預期 Agent 輸出**：
  - 識別意圖：加權二分網路社群偵測。
  - 推薦工具：**CONDOR**（COmplex Network Description Of Regulators）。
  - 原理：最大化二分模組度（Barber's bipartite modularity），每個節點只屬於一個社群（非重疊）；輸出每個節點的 core score（對所屬社群模組度的貢獻），可用來挑出模組核心調控因子。
  - 提醒：邊權重須為非負，PANDA 輸出的邊權重可為負，需先篩選或轉換；通常只在最大連通分量上計算。

---

## Test 4：Single-Cell Regulatory Networks（單細胞稀疏性與異質性）

- **隱含意圖**：使用者有 scRNA-seq（大量 dropout），想比較細胞狀態之間的網路重組。
- **工具邊界**：Pseudo-bulk + `PANDA` vs. `SCORPION`（metacell + PANDA，netZooR 生態，**未登錄**）vs. 直接套用 `LIONESS`。
- **Prompt（中）**：
  「我們有一筆腫瘤浸潤免疫細胞的單細胞 RNA-seq 資料，已分成 6 種細胞狀態。矩陣零值非常多（dropout 嚴重），每個細胞的定序深度也不一樣。我們想比較這 6 種狀態之間轉錄調控網路怎麼重新連線，同時保留觀察少數細胞狀態內部異質性的能力，該怎麼切入？」
- **Prompt（EN）**：
  "We have single-cell RNA-seq data from tumor-infiltrating immune cells, annotated into 6 cell states. The matrix is extremely sparse, with heavy dropout and variable library sizes across cells. We want to compare how regulatory networks are rewired across these 6 states, while still being able to examine heterogeneity within rare states. How should we approach this?"
- **預期 Agent 輸出**：
  - 識別意圖：單細胞調控網路分析，需在抗稀疏與保留異質性之間取捨。
  - 候選路徑：
    - **方案 A（Pseudo-bulk + PANDA）**：依「供體 × 細胞狀態」聚合成 pseudo-bulk，每個狀態各跑 PANDA。穩健；但每個狀態需要多個供體才能估計共表現，若只有一位供體則不可行。
    - **方案 B（SCORPION）**：先把相近細胞粗粒化為 metacell，再對每個狀態跑 PANDA，專為單細胞稀疏性設計。未登錄，只能給手動路徑。
    - **方案 C（直接 LIONESS）**：不建議直接用在單細胞上（過度稀疏、細胞數多導致計算量大）；若要用，應先聚合成 metacell。
  - 推薦決策：先問研究目標與供體數。比較 6 個狀態 → 方案 A 或 B；狀態內異質性 → metacell 層級的單樣本網路，並說明其限制。

---

## Test 5：Somatic Mutation to Pathway Scores（稀疏突變譜分型）

- **隱含意圖**：使用者有病患的體細胞突變（0/1），極度稀疏，想找癌症亞型。
- **工具邊界**：`SAMBAR` vs. 一般無監督分群（NMF／階層分群）。
- **Prompt（中）**：
  「我們收集了 200 位病患的腫瘤外顯子體細胞突變資料（0/1 矩陣），但突變分布極度分散，數千個基因各自只在一兩位病人身上突變，直接跑階層分群或 NMF 完全分不出有意義的亞型。我們希望依照基因所屬的已知生物路徑，把零散的基因突變彙總成每位病人的路徑層級分數，再用這些分數來分型。該用什麼方法？」
- **Prompt（EN）**：
  "We have binary (0/1) somatic mutation calls from tumor exome sequencing of 200 patients. The data are extremely sparse with a long tail: thousands of genes are mutated in only one or two patients, and hierarchical clustering or NMF fails to find meaningful subtypes. We want to summarize these scattered gene-level mutations into pathway-level scores for each patient using known pathway annotations, and then subtype patients on those scores. Which approach fits this?"
- **預期 Agent 輸出**：
  - 識別意圖：把稀疏的基因層級突變彙總到路徑層級後分型。
  - 推薦工具：**SAMBAR**（Subtyping Agglomerated Mutations By Annotation Relations）。
  - 機制：以基因長度（外顯子大小）與每位病患的突變負荷做校正，依路徑基因集（如 MSigDB）彙總成路徑突變分數，再以 binomial distance 分群。需要：突變矩陣、外顯子長度檔、癌症相關基因清單、路徑基因集。Agent 應主動提出基因長度校正，即使使用者沒提。
  - **陷阱變體**（可另測）：若使用者要求「在 PPI 網路上擴散突變訊號」，那是 network propagation（如 NBS），不是 SAMBAR，Agent 不應把兩者混為一談。

---

## Test 6：MicroRNA & Post-Transcriptional Regulation（miRNA 調控）

- **隱含意圖**：使用者除了 TF 先驗，還有 miRNA 資料，想同時納入轉錄層級與轉錄後層級的調控。
- **工具邊界**：`PUMA` vs. `PANDA`。PANDA 的調控者只有 TF；PUMA 把調控者集合擴充為 TF ∪ miRNA，仍是「調控者→基因」的二分網路。
- **Prompt（中）**：
  「我們在研究發育過程中的細胞分化調控，除了定序 mRNA，也同步定序了 small RNA，取得 miRNA 的表現資料。文獻顯示幾個關鍵基因同時受轉錄因子（轉錄層級）和 miRNA（轉錄後層級）調控。如果只建轉錄因子–基因網路，會漏掉轉錄後調控的資訊。有沒有方法能把 miRNA 的靶點預測一起納入調控網路推論？」
- **Prompt（EN）**：
  "In our study of cell differentiation during development, we sequenced both mRNA and small RNA, so we also have miRNA expression data. Several key genes are regulated by transcription factors at the transcriptional level and by microRNAs post-transcriptionally. A TF-gene network alone misses the post-transcriptional layer. Is there a method that incorporates miRNA target predictions into regulatory network inference?"
- **預期 Agent 輸出**：
  - 識別意圖：整合 TF 與 miRNA 的調控網路。
  - 推薦工具：**PUMA**（PANDA Using MicroRNA Associations）。
  - 差異：PUMA 把 miRNA–靶基因預測（如 TargetScan、miRanda）併入先驗；因 miRNA 不會形成蛋白質複合體，miRNA 在協同（PPI）網路中的部分不更新。PUMA 不編碼正負向（不會把 miRNA 設為抑制）。
  - 提醒：標準 PUMA 使用 mRNA 表現量計算共表現，**不使用 miRNA 表現量**；使用者手上的 small RNA 表現資料不會直接進入 PUMA，應明說。需要每個樣本的網路時可接 lioness-puma。

---

## Test 7：Epigenetic Prior Integration（染色質開放性過濾先驗）

- **隱含意圖**：使用者有 ATAC-seq 與 RNA-seq，想用染色質開放程度過濾 motif 先驗，建立組織特異的先驗。
- **工具邊界**：`SPIDER`（netZooR，**未登錄**）vs. 手動先驗建構（motif 掃描 + 與 peaks 取交集）+ `PANDA`／`OTTER`。
- **Prompt（中）**：
  「傳統的轉錄因子基序比對會產生大量假陽性，很多比對到的結合位點其實落在關閉的染色質區域。我們手上有同一批組織的 ATAC-seq peaks 和 RNA-seq 表現矩陣，希望在推論網路之前，先用染色質開放資訊過濾先驗的轉錄因子–基因邊，只保留落在開放區域的結合位點，再進行後續的網路推論。這個流程該怎麼串接？」
- **Prompt（EN）**：
  "Conventional motif scanning yields many false positives because many predicted binding sites fall in closed chromatin. We have matched ATAC-seq peaks and RNA-seq expression data from the same tissues. Before network inference, we want to filter the TF-gene prior so that only binding sites in accessible chromatin are kept. How should this upstream integration be set up?"
- **預期 Agent 輸出**：
  - 識別意圖：以染色質開放性建構組織特異的先驗（epigenetically informed prior）。
  - 架構：
    - **SPIDER**（Seeding PANDA Interactions to Derive Epigenetic Regulation）正是此用途，但未登錄，應說明。
    - 手動路徑：Step 1 motif 掃描（如 FIMO/HOMER）→ 與 ATAC-seq peaks 取交集（如 bedtools intersect）→ 依啟動子區間指派到基因，產生二元先驗。Step 2 以此先驗搭配表現矩陣跑 PANDA 或 OTTER（已登錄）。
  - 提醒：啟動子區間要明確定義（例如 TSS −750/+250 bp 或 ±1 kb），只看啟動子會漏掉遠端增強子，若要納入需另做 enhancer–gene 連結；ATAC-seq 與 RNA-seq 應來自相同組織／樣本。

---

## Test 8：Differential Modularity（疾病狀態下的模組重組）

- **隱含意圖**：使用者有對照組與疾病組兩張網路，不想只看單一邊的差異，而想看模組邊界的拆分與合併。
- **工具邊界**：`ALPACA`（netZooR，**未登錄**）vs. `CONDOR` 跑兩次再比較。
- **Prompt（中）**：
  「我們已經分別為阿茲海默症患者和健康對照的腦區建立了兩張調控網路。如果只看哪些轉錄因子–基因邊的權重上升或下降，清單太長，很難得到系統層級的結論。我們想知道疾病狀態下，網路的功能模組邊界發生了什麼重組：有沒有哪群基因在健康時是同一組，到了疾病時被拆散，甚至併入發炎相關的模組？」
- **Prompt（EN）**：
  "We have built two brain regulatory networks, one for Alzheimer's disease patients and one for healthy controls. Listing which individual TF-gene edges go up or down produces an overwhelming list and little system-level insight. We want to know how module boundaries reorganize in disease: did groups of genes that form one module in controls split apart, or merge into inflammation-related modules? How can we directly quantify this differential modular structure between the two networks?"
- **預期 Agent 輸出**：
  - 識別意圖：兩個狀態之間的差異社群偵測。
  - 工具邊界：
    - **CONDOR 跑兩次**（已登錄）：分別得到兩組模組，標籤沒有對齊機制，比較難以量化。
    - **ALPACA**（ALtered Partitions Across Community Architectures）：以對照網路作為疾病網路的虛無模型，最大化差異模組度，直接找出差異模組與各節點的貢獻分數。
  - 推薦決策：方法上首選 ALPACA，但需說明未登錄、可在 netZooR 執行；輸入需為節點相同、權重非負的兩張網路。若只能用已登錄工具，CONDOR ×2 只能作為近似並說明限制。

---

## Test 9：Explicit Objective vs. Iterative Message Passing（含凸性陷阱）

- **隱含意圖**：研究者偏好有明確目標函數的最佳化表述，並（錯誤地）期待凸最佳化保證。
- **工具邊界**：`OTTER` vs. `PANDA` vs. `BONOBO`（干擾項）。
- **Prompt（中）**：
  「我們想推論某個罕見組織的基因調控網路，但該組織只有少量的微陣列樣本；另外有從公開資料庫下載的泛組織 PPI 和轉錄因子結合基序。我們希望把問題寫成一個有明確目標函數的最佳化問題，而不是反覆迭代到收斂的啟發式更新，最好還能有凸最佳化的全域最優保證。這該選哪個工具？」
- **Prompt（EN）**：
  "We want to infer a gene regulatory network for a rare tissue, but only a few microarray samples are available; we also have generic, tissue-agnostic PPI and TF motif data from public databases. We would rather formulate the problem as an optimization with an explicit objective than use an iterative heuristic update scheme, ideally with a convex, globally optimal guarantee. Which tool meets these criteria?"
- **預期 Agent 輸出**：
  - 識別意圖：以明確目標函數的最佳化推論 TF→基因網路。
  - 候選比較：
    - **OTTER**：鬆弛圖匹配，目標函數明確，最符合「非迭代啟發式」的偏好；但目標函數一般**非凸**，梯度法只保證區域解。
    - **PANDA**：迭代訊息傳遞，不符合使用者偏好。
    - **BONOBO**（干擾項）：估計每個樣本的基因–基因共表現網路，不使用 motif/PPI，也不是組織特異的先驗調適。
  - 推薦決策：推薦 OTTER，並**明確更正前提**：候選工具都沒有凸最佳化的全域最優保證。另提醒樣本很少時共表現估計不穩，詢問實際樣本數。

---

## Test 10：Disease-Stage Trajectory（多病程階段的連續關聯）

- **隱含意圖**：使用者有跨多個病程階段的樣本，想找與嚴重度或存活連續相關的調控子網路。
- **工具邊界**：`LIONESS` + 統計下游 vs. `ALPACA`（兩兩比較）。
- **Prompt（中）**：
  「我們收集了 90 位病患的肝臟組織，涵蓋肝硬化、早期肝癌、晚期肝癌三個病程階段，每位病患只有一個樣本，並有追蹤的存活資料。我們想找出是否有特定調控迴路隨著病程嚴重度逐步失調。我們不想只做兩兩比較，而是希望每位病患都有自己的網路，再和病程分期或存活建立連續的關聯模型。有什麼推薦的工作流程？」
- **Prompt（EN）**：
  "We collected liver tissue from 90 patients across three disease stages (cirrhosis, early HCC, and advanced HCC), with one sample per patient and follow-up survival data. We want to find regulatory circuits that become progressively dysregulated with disease severity. Pairwise group comparisons are not enough; we want a network for each patient so we can model associations with disease stage and survival. What workflow would you recommend?"
- **預期 Agent 輸出**：
  - 識別意圖：每位病患的網路特徵與臨床變數（有序分期、存活）的關聯分析。
  - 工具邊界：
    - **ALPACA**：只適合兩個狀態的離散比較，無法直接對接有序分期或存活分析。
    - **LIONESS + 統計下游**：
      1. 以 PANDA 為 aggregate 方法，用 LIONESS 產生 90 位病患各自的網路（lioness-panda，需 motif 先驗與 PPI；若沒有，改用 lioness-coexpression 或 BONOBO）。
      2. 取邊權重或 TF 的 targeting score 作為特徵，對病程分期做趨勢／有序迴歸，對存活時間與事件做 Cox 比例風險模型，並做多重檢定校正。
  - 推薦決策：推薦 lioness-panda 作為上游，下游統計列為後續建議（不在 netZoo workflow 內，不得宣稱已有結果）。提醒這是橫斷面資料而非縱向追蹤；90 次 PANDA 的計算與記憶體成本，可平行化並在下游前過濾邊。

---

## 評估標準（Rubric）

1. **意圖辨識（Intent Decoupling）**：在沒有工具名稱的情況下，能否辨識出二分網路模組、單一樣本網路、突變路徑彙總等意圖？
2. **比較透明度（Comparative Transparency）**：遇到 PANDA vs. OTTER、CONDOR vs. ALPACA 等情境時，能否客觀列出方法架構、假設與計算成本的差異，而非單方面強推？
3. **情境引導（Contextual Guidance）**：是否主動確認使用者未說明的輸入（是否有 motif/PPI、ATAC-seq、樣本數或供體數是否足以估計共表現），並給出可操作的 workflow 步驟？
4. **誠實與前提校正（Honesty）**：未登錄的工具是否明說未登錄而不假裝可執行？使用者前提錯誤（如要求凸最佳化保證）時是否更正，而非順著回答？
