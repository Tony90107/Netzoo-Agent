# Network Zoo 工具導覽

整理日期：2026-06-02  
來源主站：[https://netzoo.github.io/](https://netzoo.github.io/)

## Network Zoo 簡介

Network Zoo，也常寫作 `netZoo{R,Py,M,C}`，是一組用來推論與分析生物網路的工具集合，重點放在基因調控網路（gene regulatory networks, GRNs）、共表現網路、多組學網路、樣本特異網路、社群偵測與網路差異分析。

你可以把它想成一條分析管線：

1. 先處理表現資料：`YARN`、`COBRA`
2. 建立整體或情境特異的調控網路：`PANDA`、`PUMA`、`OTTER`、`SPIDER`、`EGRET`、`DRAGON`、`TIGER`
3. 需要每個樣本自己的網路時：`LIONESS`、`BONOBO`
4. 比較、解釋或萃取網路結構：`CONDOR`、`ALPACA`、`CRANE`、`BLOBFISH`、`MONSTER`、`SAMBAR`
5. 網路太大、計算太慢時：`gpuZoo`

## 套件與入口

Network Zoo 不是單一語言工具，而是多語言生態系：

| 入口 | 適合誰 | 說明 |
|---|---|---|
| `netZooR` | R 使用者、生物資訊分析流程、vignette 教學 | 功能最完整之一，包含 PANDA、LIONESS、ALPACA、CONDOR、SAMBAR、MONSTER、OTTER、YARN、COBRA、DRAGON、TIGER 等 |
| `netZooPy` | Python 使用者、批次運算、命令列流程 | 包含 PANDA、PUMA、LIONESS、BONOBO、CONDOR、SAMBAR、DRAGON、COBRA 等部分工具 |
| `netZooM` | MATLAB 使用者 | 包含部分 PANDA 系列與 GPU 加速實作 |
| `netZooC` | 需要 C/C++ 實作或效能的人 | 早期與高效能版本工具 |
| Netbooks | 不想安裝的人 | 雲端教學 notebook，可直接跑官方範例 |
| netZooCloud | Web 介面使用者 | 以網頁方式使用部分方法 |

## 安裝速查

R：

```r
install.packages("remotes")
remotes::install_github("netZoo/netZooR", build_vignettes = TRUE)
library(netZooR)
```

Python：

```bash
git clone https://github.com/netZoo/netZooPy.git
cd netZooPy
pip3 install -e .
```

或使用 conda：

```bash
conda install -c netzoo -c conda-forge netzoopy
```

如果只是想快速理解流程，優先看官方 Netbooks，不必先處理本機環境。

## 快速選工具

| 你的問題 | 優先看 |
|---|---|
| RNA-seq 資料很多、跨組織或批次，需要 QC/標準化 | `YARN` |
| 想修正 co-expression 網路裡殘留的 batch/covariate 影響 | `COBRA` |
| 想用 expression + motif + PPI 推論 TF-gene 調控網路 | `PANDA` |
| 想把 miRNA 調控也納入網路 | `PUMA` |
| 想用圖匹配/最佳化角度推論 GRN | `OTTER` |
| 想加入 DNase-seq / chromatin accessibility 資訊 | `SPIDER` |
| 想建立個體 genotype-specific GRN | `EGRET` |
| 想找 bipartite network 的社群/模組 | `CONDOR` |
| 想比較健康 vs 疾病、兩種狀態的模組變化 | `ALPACA` |
| 想評估差異模組或網路差異是不是穩健 | `CRANE` |
| 想從大網路中抽出連接指定基因集合的小子網路 | `BLOBFISH` |
| 想為每個樣本建立一張調控網路 | `LIONESS` |
| 想用 Bayesian 方法建立樣本特異 co-expression network | `BONOBO` |
| 想找細胞狀態或疾病轉換中的 TF driver | `MONSTER` |
| 想用 mutation + pathway 做癌症 subtype | `SAMBAR` |
| 想把 PANDA/PUMA/LIONESS 類方法跑快 | `gpuZoo` |
| 想整合兩層 omics 做 multi-omic GGM / partial correlation network | `DRAGON` |
| 想估計 TF activity 並同時更新 context-specific GRN | `TIGER` |

## 各工具用途與用法

### YARN

**用途**：大型、異質、多組織 RNA-seq 資料的前處理、品質控制、基因過濾與 normalization。

**典型輸入**：RNA-seq count/expression matrix、sample annotation、組織或群組標籤。

**怎麼用**：在 R 中使用 YARN 相關函式，例如 `filterLowGenes()`、`checkMisAnnotation()`、`normalizeTissueAware()`、`plotCMDS()`。通常先檢查樣本標註是否合理，再過濾低表現基因，最後做 tissue-aware normalization。

**輸出**：乾淨、標準化後的 expression matrix，可作為 PANDA、COBRA、DRAGON、TIGER 或其他 downstream analysis 的輸入。

**適合情境**：GTEx 類型資料、跨組織 RNA-seq、大量樣本但組織組成複雜的研究。

### COBRA

**用途**：修正 co-expression 或 covariance network 中殘留的 batch effect / covariate effect。它處理的是基因之間的共同變動，不只是每個基因自己的平均值或變異。

**典型輸入**：expression matrix、batch label、連續或類別 covariates。

**怎麼用**：在 R 使用 `cobra()`，或在 Python 使用 netZooPy 對應實作。先提供表現矩陣與 covariate 設定，讓 COBRA 估計 conditional covariance，產生更適合下游網路推論的 corrected co-expression matrix。

**輸出**：batch/covariate-corrected co-expression 或 covariance matrix。

**適合情境**：你已經做過常規 batch correction，但擔心 correlation network 仍被批次效應污染。

### PANDA

**用途**：Network Zoo 的核心 GRN 推論方法之一。用 message passing 整合 expression、TF binding motif prior、TF-TF PPI，推論 TF-gene 調控網路。

**典型輸入**：

- gene expression matrix
- TF-gene motif prior 或 binding prior
- TF-TF PPI network

**怎麼用**：

R 可用 `pandaPy()` 呼叫 Python 實作，或使用 R 版 PANDA 函式。Python 可用 `Panda(...)` 類別或命令列：

```bash
python run_panda.py \
  -e ToyExpressionData.txt \
  -m ToyMotifData.txt \
  -p ToyPPIData.txt \
  -o panda_network.txt
```

**輸出**：weighted TF-gene regulatory network。邊權重代表 TF 調控 target gene 的證據強度。

**適合情境**：想從 bulk expression 建立 condition-specific GRN，例如組織、癌症 subtype、疾病狀態的 TF-gene 網路。

### PUMA

**用途**：PANDA 的 miRNA 延伸版，把 miRNA-target prior 加入調控網路，推論 TF/miRNA 到 gene 的調控關係。

**典型輸入**：

- gene expression matrix
- TF-gene motif 或 binding prior
- TF-TF PPI network
- motif/prior 檔可合併 TF-gene 與 miRNA-target prior，例如 TargetScan 或 miRanda 預測
- 一欄式 miRNA 名稱清單，用來標示 prior 中哪些 regulator 是 miRNA

**怎麼用**：R 使用 `puma()`，Python 可用 `Puma(...)` 或命令列：

```bash
python run_puma.py \
  -e ToyExpressionData.txt \
  -m ToyMotifData.txt \
  -p ToyPPIData.txt \
  -i ToyMiRList.txt \
  -o puma_network.txt
```

**輸出**：包含 TF 與 miRNA regulator 的 weighted regulatory network。

**適合情境**：研究 post-transcriptional regulation、miRNA 對組織特異或疾病特異調控的影響。

### OTTER

**用途**：用 relaxed graph matching 的觀點推論 GRN。它把 PPI 與 gene co-expression 視為 TF-gene bipartite GRN 的兩種投影，透過最佳化找出最合理的 TF-gene network。

**典型輸入**：

- initial TF-gene prior 或 motif matrix `W0`
- TF-TF PPI matrix `P`
- gene-gene co-expression matrix `C`

**怎麼用**：R 使用 `otter()`。通常先準備 PPI、co-expression、motif prior，再選擇 regularization 與資料權重設定，輸出優化後的 GRN。

**輸出**：weighted TF-gene regulatory network。

**適合情境**：想以比 PANDA 更明確的最佳化框架建立 GRN，或想調整 PPI 與 co-expression 的相對信任度。

### SPIDER

**用途**：將 epigenetic data，尤其是 DNase-seq / open chromatin 資訊，加入 PANDA 類 GRN 推論。

**典型輸入**：

- DNase-seq 或 chromatin accessibility 資訊
- TF motif prior
- expression matrix
- TF-TF PPI network

**怎麼用**：R 使用 `spider()`。先從 DNase-seq 取得可及染色質區域，建立可用 binding site 的 mask，再疊加到 motif prior，最後進入 PANDA/message passing 類推論。

**輸出**：epigenetically informed TF-gene regulatory network。

**適合情境**：要建立 cell line、cell type、tissue-specific GRN，且有 chromatin accessibility 資料。

### EGRET

**用途**：建立 genotype-specific gene regulatory network。EGRET 把個體基因型、eQTL、variant 對 TF binding 的影響納入 PANDA-like message passing。

**典型輸入**：

- individual genotype data
- eQTL data
- variant effect on TF binding 的預測
- TF motif prior
- expression matrix
- TF-TF PPI network

**怎麼用**：R 使用 `runEgret()`。流程通常先建立 genotype-informed TF-gene prior，再與 expression、PPI 整合，為每個人或每個 genotype context 產生調控網路。

**輸出**：genotype-specific 或 individual-specific TF-gene GRN。

**適合情境**：研究遺傳變異如何改變 TF binding、基因調控與疾病風險。

### CONDOR

**用途**：bipartite network 的 community detection。特別適合兩種節點類型的網路，例如 SNP-gene、TF-gene、drug-target、patient-feature。

**典型輸入**：bipartite edge list，通常包含 `source`、`target`、`weight`。

**怎麼用**：R 中先用 `createCondorObject()` 或 `condorCreateObject()` 建立物件，再用 `condorRun()` / `condorCluster()` 找社群，也可用 `condorQscore()` 找各社群的核心節點。

**輸出**：節點的 community membership、modularity、q-score、可視化 heatmap 或 community plot。

**適合情境**：想知道 TF-gene 或 SNP-gene 網路中有哪些功能模組。

### ALPACA

**用途**：比較兩張網路的 community structure，找出 phenotype-driven 或 condition-specific differential modules。

**典型輸入**：兩張具有可比節點與邊的 weighted network，通常整理成四欄：`from`、`to`、control/reference weight、case/perturbed weight。

**怎麼用**：R 使用 `alpaca(net.table, file.stem, verbose = FALSE)`。先建立 reference network 與 perturbed network，再讓 ALPACA 最大化 differential modularity。

**輸出**：differential modules、每個節點對差異模組的 contribution score。

**適合情境**：比較健康 vs 疾病、治療前後、不同 subtype、不同組織之間的調控模組差異。

### CRANE

**用途**：評估網路差異或差異模組是否穩健。它透過 constrained random networks 建立 null distribution，再比較觀察到的 differential features。

**典型輸入**：

- reference network
- perturbed network
- 要檢驗的差異特徵，例如 degree change、centrality change、ALPACA module score

**怎麼用**：R 可用 `craneBipartite()` 或 `craneUnipartite()` 產生固定 node strength 的隨機化網路，再用 null distribution 計算 empirical p-value。

**輸出**：差異特徵的穩健度、empirical p-values、顯著節點或模組。

**適合情境**：ALPACA 找到差異模組後，想知道結果是不是可能來自網路推論噪音。

### BLOBFISH

**用途**：從大型 bipartite network 或多個 observation-specific networks 中，找出連接指定基因集合的精簡子網路。

**典型輸入**：

- genes of interest
- 一組 full bipartite networks，通常每個樣本一張
- null distribution 或 statistical cutoff
- hop constraint

**怎麼用**：R 使用 `RunBLOBFISH()`。先計算邊的顯著性，再用 constrained breadth-first search 尋找 seed genes 之間的顯著連接路徑。

**輸出**：連接目標基因集合的 compact subnetwork，可用 `PlotNetwork()` 視覺化。

**適合情境**：你已有大型 GRN，但只想解釋某個 pathway、DEG list 或文獻基因集合背後的調控脈絡。

### LIONESS

**用途**：從 aggregate network 反推每個樣本的 sample-specific network。它本身是一個框架，可搭配 PANDA、PUMA、correlation network 等網路推論方法。

**典型輸入**：

- full dataset 建出的 aggregate network
- leave-one-out 建出的 network
- 或可重新計算網路的原始資料

**怎麼用**：

R 使用 `lioness()` 或 `lionessPy()`。Python 可用 `Lioness(...)` 或命令列：

```bash
python run_lioness.py \
  -e expression.npy \
  -m motif.npy \
  -p ppi.npy \
  -n panda.npy \
  -o lioness_output \
  -f npy
```

**輸出**：每個 sample 一張 network，邊代表該樣本對整體網路的特異貢獻。

**適合情境**：precision medicine、heterogeneous cohort、想把網路特徵拿去做臨床關聯或 subtype 分析。

### BONOBO

**用途**：用 Bayesian framework 建立 sample-specific co-expression networks。

**典型輸入**：log-transformed、centered gene expression matrix，以及從其他樣本建立的 prior distribution。

**怎麼用**：Python 使用 netZooPy 的 BONOBO 實作。概念上是為每個樣本估計一張 co-expression matrix，並以 Bayesian posterior 方式整合該樣本資訊與群體 prior。

**輸出**：sample-specific co-expression matrices。

**適合情境**：想專注於每個人的 co-expression 差異，而不是 TF-gene regulatory network。

### MONSTER

**用途**：分析網路狀態轉換，找出從一種狀態到另一種狀態時，哪些 TF 或 regulator 是 driver。

**典型輸入**：兩個狀態的 network，例如 healthy GRN 與 disease GRN，或 time point A 與 time point B 的 network。

**怎麼用**：R 使用 `monster()`。它會估計 transition matrix，描述初始網路如何轉換成目標網路，再用 off-diagonal weights 等指標找出 driver regulators。

**輸出**：transition matrix、driver TF ranking、狀態轉換視覺化。

**適合情境**：疾病進展、細胞分化、治療反應、時間序列狀態轉換。

### SAMBAR

**用途**：用 somatic mutation data 與 pathway annotation 進行癌症 subtype 分析。它把稀疏的 gene-level mutation 轉換成 pathway-level mutation score。

**典型輸入**：

- sample-by-gene mutation matrix
- pathway gene sets，例如 GMT
- gene length 或 pathway representation 修正資訊

**怎麼用**：R 使用 `sambar()`，也可搭配 `sambarConvertgmt()`、`sambarCorgenelength()`、`sambarDesparsify()`。先把 gene mutation 聚合到 pathway，再做 sample clustering / subtype discovery。

**輸出**：pathway mutation score matrix、癌症 subtype、與 subtype 相關的 pathway 或 phenotype association。

**適合情境**：mutation data 很稀疏，想用 biological pathway 增加可解釋性並找 subtype。

### gpuZoo

**用途**：PANDA、PUMA、LIONESS 類方法需要大量矩陣運算，gpuZoo 用 GPU 加速這些計算以降低時間與成本。

**典型輸入**：與對應方法相同，例如 PANDA 的 expression、motif、PPI，或 PUMA 的 miRNA prior。

**怎麼用**：使用 netZooPy 或 netZooM 中的 GPU 實作。適合在有 GPU 的伺服器或雲端環境跑大型 TF-gene network。

**輸出**：與原方法相同的 network 結果，但計算速度更快。

**適合情境**：大規模人類轉錄體、數萬 genes / transcripts、多 tissue 或多 cohort 批次推論。

### DRAGON

**用途**：用 Gaussian Graphical Model 整合兩層 omics data，建立 multi-omic partial correlation network。

**典型輸入**：同一批樣本上的兩種 continuous omics matrices，例如 transcriptome + methylome。

**怎麼用**：R 使用 `dragon()`，Python 使用 netZooPy 的 DRAGON。通常先把資料轉換成較接近常態分佈，再估計 sparse covariance / precision matrix。

**輸出**：multi-omic GGM / partial correlation network，邊代表在控制其他變數後仍存在的條件關聯。

**適合情境**：想找 gene expression 與 methylation、proteomics、metabolomics 等兩層資料之間的 regulatory associations。

### TIGER

**用途**：同時估計 TF activity 與 context-specific regulatory network。它會利用 prior TF-gene knowledge，同時允許 activation/inhibition 與網路邊權重在不同 context 下調整。

**典型輸入**：

- gene expression matrix
- prior TF-gene regulatory network 或 regulon
- 可選的 edge sign / confidence

**怎麼用**：R 使用 `tiger()`。先準備 expression 與 prior network，必要時用 `priorPp()` 過濾低信心邊，再估計 TF activity 與 GRN。

**輸出**：TF activity estimates、context-specific GRN、更新後的 TF-gene edge weights。

**適合情境**：大型 cohort，例如 TCGA，想推論 TF 活性而不只看 TF 本身表現量。

## 常見分析路線

### 路線 A：建立一張 condition-specific GRN

1. 用 `YARN` 或自己的流程整理 expression matrix。
2. 若擔心 batch/covariate 影響 co-expression，先用 `COBRA`。
3. 準備 motif prior 與 PPI。
4. 用 `PANDA` 或 `OTTER` 推論 TF-gene network。
5. 用 `CONDOR` 找模組，或用 `BLOBFISH` 抽出目標基因子網路。

### 路線 B：比較健康與疾病網路

1. 分別對 healthy 與 disease 建立 GRN。
2. 用 `ALPACA` 找 differential modules。
3. 用 `CRANE` 檢查差異模組是否穩健。
4. 用 `MONSTER` 分析從 healthy 到 disease 的 driver regulators。

### 路線 C：做 precision network medicine

1. 用 `PANDA` 建立 aggregate GRN。
2. 用 `LIONESS` 產生每個樣本的 sample-specific GRN。
3. 對每個樣本提取 network features，例如 TF outdegree、gene indegree、module score。
4. 與 phenotype、survival、drug response 或 disease subtype 做關聯。

### 路線 D：多組學網路

1. 若是 transcriptome + methylome / proteome 這類 paired omics，先看 `DRAGON`。
2. 若重點是 mutation subtype，先看 `SAMBAR`。
3. 若重點是 genotype 對 regulation 的影響，先看 `EGRET`。
4. 若重點是 TF activity，先看 `TIGER`。

## 輸入資料準備提醒

- Expression matrix 的 sample/gene 方向要確認。不同函式可能要求 rows/columns 不同。
- TF 名稱、gene 名稱、motif prior、PPI 的 identifier 必須能對上。
- PANDA 類工具需要三種資料彼此重疊；缺失節點的處理模式會影響結果。
- 大型矩陣很吃記憶體；先用 toy data 或少量基因測試流程。
- 有 sample-specific network 時，輸出檔案可能非常大，建議先規劃儲存格式與分析指標。

## 官方資料來源

- Network Zoo 主站：[https://netzoo.github.io/](https://netzoo.github.io/)
- 工具清單與 papers：[Zoo animals](https://netzoo.github.io/zooanimals/)
- 安裝說明：[How to install](https://netzoo.github.io/contribute/install/)
- `netZooR` 文件與函式索引：[netZooR reference](https://netzoo.github.io/netZooR/reference/index.html)
- `netZooPy` 文件與函式索引：[netZooPy functions](https://netzoopy.readthedocs.io/en/latest/functions/)
- `netZooPy` 安裝：[netZooPy install](https://netzoopy.readthedocs.io/en/latest/install/)
- 雲端教學 notebooks：[Netbooks](https://netbooks.networkmedicine.org/)
