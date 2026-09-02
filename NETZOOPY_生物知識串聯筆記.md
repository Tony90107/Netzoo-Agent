# netZooPy 12 workflows 生物知識串聯筆記

> 給第一次接觸網路生物學、但願意學習資料分析的讀者。本文把 repository 裡的 12 個 scientific workflows 放在同一張生物知識地圖上，並把「論文方法能做什麼」與「目前這個 netZoo agent 已驗證、允許做什麼」分開。

| 項目 | 本筆記紀錄 |
|---|---|
| Repository | /Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent |
| 目前核對日期 | 2026-08-29 |
| agent contract 最高權威 | scripts/workflow_registry.py、workflows/*.yaml、對應 integration／validation code 與 tests |
| 上游 runtime | repository contract 對需要 Docker 的方法固定使用 netZooPy 0.11.0；實際 revision 由各 integration 文件記錄 |
| 讀法 | 先讀共同主線與全景表，再讀對應 workflow；最後用 handoff 圖與證據階梯解讀結果 |

## 章節導覽

- [怎麼使用本筆記](#how-to-read)
- [12 workflows 與 10 個方法家族](#workflow-families)
- [共同生物主線](#biological-thread)
- [必要資料與 network vocabulary](#vocabulary)
- [12-workflow 全景比較表](#panorama)
- [Regulatory inference：PANDA、PUMA、OTTER、GIRAFFE](#regulatory-family)
- [Sample-specific：LIONESS 與 BONOBO](#sample-specific-family)
- [Covariate／multi-omic：COBRA 與 DRAGON](#covariate-multiomic-family)
- [CONDOR 與 SAMBAR](#downstream-family)
- [Handoff、癌症案例與決策樹](#relationship-maps)
- [證據階梯與失敗模式](#evidence-ladder)
- [toy data、測驗與研究紀錄](#practice-and-records)
- [Glossary、來源與 changelog](#sources-and-changelog)

<a id="how-to-read"></a>
## 1. 這份筆記怎麼用

### 1.1 先記住三個層次

每個結果都要同時問三件事：

1. **生物問題**：研究者究竟想知道什麼，例如「哪些 TF 可能調節哪些基因」或「不同病人的共表現結構是否不同」。
2. **統計產物**：演算法實際產生的是 edge score、相關矩陣、partial-correlation network、pathway score，還是 community label。
3. **agent 邊界**：目前 repository 是否已驗證輸入方向、輸出格式與下一個 workflow 的 artifact contract。

同一個詞「network」不代表同一種東西。PANDA 的 TF→gene regulatory evidence、BONOBO 的 gene-gene coexpression、DRAGON 的兩層 partial-correlation association、CONDOR 的 community assignment，不能只因為都畫成圖就互相替換。

### 1.2 本文的證據標籤

- **[科學]**：來自方法論文、官方 netZooPy 文件或官方 repository 的方法說明。
- **[agent]**：來自目前 repository 的 registry、YAML、adapter、integration doc、artifact validator 或測試。
- **[教學推論]**：為了幫助理解而做的簡化；不應被當成新的 benchmark 或生物學事實。

若 [科學] 與 [agent] 不同，以研究問題而言要讀 [科學]，以這個 repository 實際能執行什麼而言要讀 [agent]。

### 1.3 三種 handoff 語意

本文的「可直接 handoff」不是指把任何一個輸出檔案的路徑直接塞給下一個 command，而是指 registry 已聲明目標，且輸出已通過目標所需的 identifier、方向、形狀與語意驗證。

| 標記 | 意義 |
|---|---|
| 實線 | 目前 agent contract 已允許的 handoff；仍須完成目標 validator。例：COBRA 的 adjusted coexpression → PANDA 的 coexpression_file。 |
| 虛線 | 科學概念上可以組合，但目前需要明確 conversion、provenance、重新驗證與／或使用者確認。 |
| 禁止 | 目前 artifact contract 或 node 語意不相容；不能把檔案直接當下一個 workflow 的輸入。 |

### 1.4 一個必要的科學安全句

本文所說的「推論」「證據」「association」都不是自動等於「因果」。除非另有獨立的 perturbation、時間序列、準實驗設計或功能實驗支持，network edge 通常只是模型在特定輸入、prior 與假設下得到的關係證據。

### 你現在應該能回答

1. 為什麼同一個 network 名詞不能代表同一種生物產物？
2. [科學] 方法能力與 [agent] 目前可執行能力有什麼差別？
3. 什麼條件下本文的 association 才可能逐步升級為較強的生物學 claim？

<a id="workflow-families"></a>
## 2. 12 workflows 與 10 個方法家族

這個專案目前有 **12 個已註冊 scientific workflows**，但不是 12 個互不相干的套件；它們對應 **10 個主要方法家族**：PANDA、PUMA、LIONESS、CONDOR、COBRA、GIRAFFE、BONOBO、SAMBAR、DRAGON、OTTER。

netZooPy 本身是 Python 套件；PANDA、PUMA 等是套件中的方法／模組。本文為了配合 agent 的使用情境，也會把每個註冊項目稱為 workflow。

LIONESS 是一個可套在 network estimator 外面的 sample-specific framework。在本 agent 中分成三種 workflow：

- LIONESS-PANDA：PANDA estimator 放進 leave-one-out construction。
- LIONESS-PUMA：PUMA estimator 放進 leave-one-out construction。
- LIONESS-coexpression：Pearson coexpression estimator 放進 leave-one-out construction。

因此 LIONESS-PANDA 與 LIONESS-PUMA 是**組合方法**，不是兩個獨立的上游套件；它們也不是「把已輸出的 aggregate PANDA/PUMA 檔案直接再跑一次」。

### 固定介紹順序

1. PANDA
2. PUMA
3. LIONESS-PANDA
4. LIONESS-PUMA
5. LIONESS-coexpression
6. CONDOR
7. COBRA
8. GIRAFFE
9. BONOBO
10. SAMBAR
11. DRAGON
12. OTTER

### 10 個方法家族

| 方法家族 | 本 agent 中的 workflows | 主要產物 |
|---|---|---|
| PANDA-style regulatory inference | PANDA | aggregate TF→gene regulatory evidence |
| miRNA-aware regulatory inference | PUMA | aggregate TF／miRNA→gene regulatory evidence |
| LIONESS sample-specific estimator | LIONESS-PANDA、LIONESS-PUMA、LIONESS-coexpression | aggregate 參考網路與 sample-specific network |
| Bipartite community analysis | CONDOR | regulator-side／target-side community assignment |
| Covariate-aware coexpression | COBRA | covariance components 與 adjusted coexpression artifact |
| Biologically informed factorization | GIRAFFE | aggregate regulatory effects 與 TF-by-sample TFA |
| Bayesian sample-specific coexpression | BONOBO | 每個選定 sample 的 gene-gene coexpression 與可選 p-values |
| Mutation pathway subtyping | SAMBAR | gene／pathway mutation scores 與可選 patient clusters |
| Two-layer graphical model | DRAGON | aggregate、undirected、multi-omic partial-correlation network |
| Relaxed graph matching | OTTER | aggregate TF→gene optimized regulatory network |

### 你現在應該能回答

1. 為什麼 12 workflows 不是 12 個獨立套件？
2. LIONESS 的三種 workflow 分別把哪個 estimator 放進 sample-specific framework？
3. 哪些 workflow 屬於 regulatory inference，哪些屬於 downstream community 或 mutation subtyping？

<a id="biological-thread"></a>
## 3. 一條共同的生物主線

~~~text
DNA sequence / motif
        ↓
TF binding potential 與 TF activity
        ↓
transcription / mRNA expression
        ↓
miRNA post-transcriptional regulation
        ↓
gene-gene coexpression
        ↓
protein interaction / PPI
        ↓
somatic mutation 與 pathway disruption
        ↓
多組學層之間的 conditional association
        ↓
aggregate、condition-specific、sample-specific networks
        ↓
community / module / subtype
~~~

這是一條**教學主線**，不是所有 workflow 都必須依序執行的 pipeline。實際上它會分成多條互補分析分支。

### 3.1 從 DNA 到 TF-gene regulation

DNA 上的 motif 是某個 transcription factor（轉錄因子，TF）可能結合的序列訊號。它回答的是「這個 TF 是否有可能接近這個基因的調控區」，不是「在本 cohort 裡 TF 一定正在調節該基因」。

- PANDA 把 motif-derived TF-gene prior 與 TF-TF PPI、gene-gene coexpression 一起整合。
- PUMA 在 regulatory layer 再加入 miRNA，處理 miRNA→gene prior。
- OTTER 把 TF-gene prior 當作初始／seed matrix，並要求未知的 TF-gene network 同時符合兩側 projection。
- GIRAFFE 把 prior 當作生物引導，並聯合估計 regulation effect 與 TFA。
- 三種 LIONESS workflow 讓相同 estimator 進入 sample-specific leave-one-out construction。

### 3.2 從 expression 到 coexpression

gene expression matrix 記錄每個 gene 在多個 samples 中的 mRNA abundance。把不同 gene 的變化放在一起，可得到 covariance、correlation 或 coexpression network。

- 一般 coexpression：描述兩個 gene 在樣本間是否一起變動。
- LIONESS-coexpression：從 aggregate Pearson coexpression 推出每個 sample 的 network。
- BONOBO：用 Bayesian model 把某一個 sample 的 centered deviation 與其他 samples 的背景資訊結合。
- COBRA：把 sample covariates 對 covariance structure 的影響拆出來，產生 adjusted coexpression artifact。
- PANDA、PUMA、OTTER：把 coexpression 當作 regulatory inference 的 gene-side evidence，但它不會因此變成直接的 TF-gene causal effect。

### 3.3 從 expression 到 TF activity

TF expression 只是 TF 轉錄本的 abundance；**TF activity（TFA）**問的是 TF 實際在多大程度上施展調控能力。蛋白修飾、核定位、蛋白複合體與抑制因子都可能讓 TF expression 與 TFA 不一致。

- GIRAFFE 直接輸出 TF-by-sample TFA。
- PANDA／PUMA 的 edge score 可支持 regulatory evidence，但不可把 edge score 自動叫成 TFA。
- OTTER 的 W 是 optimized TF-gene network，不是 TFA matrix。

### 3.4 從 mutation 到 pathway subtype

somatic mutation matrix 往往很稀疏：單一病人的某個 gene 可能只有 0/1 突變，而兩個病人的 driver gene 未必相同。SAMBAR 依 gene length、sample mutation burden 與 pathway annotation 把 gene-level mutations 聚合到 pathway level，接著才做 patient clustering／subtyping。

### 3.5 從兩個 omics layer 到 conditional association

DRAGON 只處理兩個 matched sample-by-feature continuous omics layers。它使用 Gaussian graphical model（GGM）估計 precision matrix，再轉成 partial correlation；這表示在模型中的其他變數條件下的關聯，不是時間方向或因果方向。

### 3.6 從 existing network 到 community

CONDOR 不負責從 raw expression 推論網路。它接收已存在且合格的 weighted bipartite edge list，分別在 regulator side 與 target side 找 community。community 不是 pathway 的同義詞；需要 enrichment、外部資料或實驗才能給出功能解釋。

### 你現在應該能回答

1. motif、expression、PPI 與 mutation 分別位於共同主線的哪個位置？
2. TF expression 為什麼不能直接當成 TF activity？
3. 為什麼 DRAGON 的 conditional association 與 SAMBAR 的 pathway score 不是同一種 network？

<a id="vocabulary"></a>
## 4. 必要資料與 network vocabulary

### 4.1 生物實體

| 名詞 | 白話意思 | 正式語意 | 本 agent 會在哪裡用到 |
|---|---|---|---|
| gene | DNA 上的一個功能單位／座位 | 可被轉錄或參與調控的基因 ID | 所有 expression、TF-gene、coexpression、mutation、pathway workflow |
| mRNA | gene 被轉錄後的 RNA 量 | expression matrix 中通常觀察到的 transcript abundance | PANDA、PUMA、LIONESS、COBRA、GIRAFFE、BONOBO、OTTER |
| protein | 由 mRNA 翻譯的蛋白質 | 可能作為 enzyme、受體或 TF | PPI prior；不能直接把 mRNA 當 protein activity |
| TF | transcription factor | 能與 DNA 調控區互動、影響靶基因轉錄的 regulator | PANDA、PUMA、LIONESS-PANDA/PUMA、GIRAFFE、OTTER、CONDOR |
| miRNA | microRNA | 常透過 post-transcriptional 機制抑制或改變 target mRNA 的穩定性／翻譯 | PUMA、LIONESS-PUMA |
| sample / patient | 一個病人、組織或實驗條件的觀測單位 | expression／omics matrix 的 sample axis | LIONESS、BONOBO、SAMBAR、DRAGON、GIRAFFE TFA |
| pathway | 一組有共同生物功能或 annotation 的 genes | external pathway gene set；不是由 SAMBAR 自動證明的機制 | SAMBAR、下游 enrichment |

### 4.2 資料與網路

| 名詞 | 白話意思 | 必須避免的誤讀 | workflows |
|---|---|---|---|
| motif / regulatory prior | 從 DNA sequence、motif scan 或其他實驗得到的「可能有連線」起點 | 不是目前 cohort 中已發生的 binding，也不是 probability | PANDA、PUMA、GIRAFFE、OTTER、LIONESS-PANDA/PUMA |
| PPI | TF 與 TF 蛋白互相作用的 network | 不等於兩個 TF 必然同時調控同一 gene | PANDA、PUMA、GIRAFFE、OTTER |
| expression matrix | gene × sample 的 mRNA 數值表 | 行列反了或 sample metadata 混進去會改變模型意義 | 多數 workflow |
| coexpression network | gene-gene 的相關或 covariance 關係 | 不等於 TF→gene GRN，也不等於 causal network | LIONESS-coexpression、BONOBO、COBRA；也作 PANDA/PUMA/OTTER 輸入 |
| regulatory network / GRN | regulator→target 的網路 | edge score 仍常是模型證據，不自動是因果 | PANDA、PUMA、LIONESS-PANDA/PUMA、GIRAFFE、OTTER |
| multi-omic network | 兩個資料層的 feature 之間與層內的 association | DRAGON 的 edge 是 conditional association，不是 causal graph | DRAGON |
| community assignment | 每一側節點所屬的網路群組 | community 不自動等於 biological pathway | CONDOR |
| mutation score | gene 或 pathway 的突變強度／聚合分數 | score 高不自動等於 driver 或臨床風險 | SAMBAR |

### 4.3 統計與模型詞彙

| 名詞 | 直覺 | 這裡的正式用途 |
|---|---|---|
| covariance | 兩個變數是否一起偏離平均值 | COBRA 拆解 covariate-associated covariance；coexpression 可由 covariance 正規化得到 |
| correlation | covariance 除以尺度後的無單位關聯 | Pearson coexpression；數值通常在 -1 到 1 |
| coexpression | 生物語境中的 gene-gene 一起變動 | 不限單一 estimator；需寫清楚是 Pearson、Bayesian posterior 或 adjusted artifact |
| partial correlation | 控制其他變數後兩變數的關聯 | DRAGON 從 precision matrix 得到；仍是 association |
| precision matrix | covariance matrix 的 inverse | GGM 中非對角元素描述條件關聯的核心量 |
| prior | 分析前的生物或統計資訊 | motif、miRNA target 或 Bayesian background；prior 不是結果 |
| regularization | 對模型複雜度加限制 | OTTER 的 gamma、DRAGON 的 shrinkage 等；不要把所有 regularization 都叫同一種 sparsity |
| shrinkage | 把不穩定的高維估計往較穩定的方向收縮 | BONOBO posterior 與 DRAGON layer-specific covariance／precision estimation |
| message passing | 在多張 network 間反覆交換資訊 | PANDA、PUMA 的一致性更新直覺 |
| matrix factorization | 把觀測矩陣拆成較小的潛在矩陣乘積 | GIRAFFE 的 regulation × TFA 觀點 |
| graph matching | 讓兩個 graph 的 projection 互相吻合 | OTTER 找 TF-gene W，使 WWᵀ 接近 P、WᵀW 接近 C |
| Bayesian posterior | prior 與觀測資料合併後的信念分布 | BONOBO 的 sample-specific coexpression 與 optional uncertainty |
| community detection | 讓群組內連線比隨機基準更集中 | CONDOR 的 bipartite modularity／q-score |
| design matrix | 每個 sample 的 covariate 數值表 | COBRA 的 batch、hospital、treatment 等 covariates；不是 expression matrix |
| confounder | 同時影響變數與結果、造成假關聯的因素 | batch、hospital、treatment 若與 phenotype 完全重疊，無法靠演算法辨識真相 |

### 4.4 方向、二分圖與粒度

- **directed**：TF → gene 有角色方向；PANDA、PUMA、OTTER、GIRAFFE 的 regulatory output 可用 regulator／target 分區，但 edge 的正負意義依方法而定。
- **undirected**：gene — gene 或 feature — feature 沒有 source/target 的生物方向；coexpression 與 DRAGON 多屬此類。
- **bipartite**：兩側 node type 不應混在同一側；TF／miRNA 是 regulator side，gene 是 target side。CONDOR 依此分別輸出 membership。
- **single-layer**：所有 node 來自同一種 entity，例如 gene-gene coexpression。
- **two-layer multi-omic**：DRAGON 的 layer1 與 layer2 feature 保持來源層標籤，不能因 ID 相同就合併。
- **aggregate**：一張代表整個 cohort／條件的網路。
- **condition-specific**：某個組織、treatment、subtype 或條件的網路；本 agent registry 主要以 aggregate／sample-specific 標記，不自動把 cohort 分組當 condition-specific contract。
- **sample-specific**：每個 sample 一張網路或分數；不等於從 aggregate 網路挑一個 node。
- **not applicable**：CONDOR 的 community assignment 不是 network 粒度；SAMBAR 的 pathway score／cluster 也不是 aggregate regulatory network。

### 你現在應該能回答

1. expression matrix 的 row／column 方向在主要 workflow 中如何不同？
2. directed、undirected、bipartite、two-layer network 的差別是什麼？
3. prior、regularization 與 shrinkage 為什麼不能互相當成同義詞？

<a id="panorama"></a>
## 5. 12-workflow 全景比較表

| Workflow | 方法家族 | 核心問題 | 必要輸入 | Node／edge 語意 | 輸出 | 有向性 | 粒度 | 是否使用 prior | 目前可直接 handoff |
|---|---|---|---|---|---|---|---|---|---|
| PANDA | message passing regulatory inference | 哪些 TF→gene 關係在多種 evidence 下較一致？ | gene-by-sample expression、TF-gene motif/prior、TF-TF PPI、output_file；可選 validated coexpression_file | TF→gene regulatory evidence；不是 probability | aggregate weighted TF-by-gene network | directed / bipartite | aggregate | 是：motif、PPI | 是，轉成並驗證 source-target-weight edge list 後 → CONDOR；COBRA adjusted coexpression 可作 coexpression_file |
| PUMA | PANDA + miRNA | miRNA 如何與 TF 一起參與 gene regulation？ | expression、motif、PPI、one-ID-per-line miRNA list、output_file；可選 coexpression | TF/miRNA→gene regulatory evidence | aggregate weighted regulator-by-gene network | directed / bipartite | aggregate | 是：motif、PPI、miRNA target prior | 是，合格 edge list → CONDOR；COBRA adjusted coexpression 可作 coexpression_file |
| LIONESS-PANDA | LIONESS + PANDA | 每個 sample 的 TF→gene regulatory network 有何差異？ | expression、motif、PPI、aggregate output_file、lioness_output | edge 語意沿用 PANDA；sample-specific network 由 leave-one-out estimator 得到 | aggregate PANDA + sample-specific TF→gene networks | directed / bipartite | aggregate + sample-specific | 是：PANDA 的原始 prior | 否；PANDA 是內部 guidance predecessor，不是直接檔案 handoff |
| LIONESS-PUMA | LIONESS + PUMA | 每個 sample 的 TF/miRNA→gene regulatory network 有何差異？ | expression、motif、PPI、miRNA list、aggregate output、lioness_output | edge 語意沿用 PUMA；不能把 miRNA edge sign 叫抑制強度 | directed / bipartite | aggregate + sample-specific | aggregate + sample-specific | 是：PUMA 的 prior | 否；PUMA 是內部 guidance predecessor |
| LIONESS-coexpression | LIONESS + Pearson coexpression | 每個 sample 的 gene-gene coexpression 結構有何差異？ | gene-by-sample expression、aggregate output_file、lioness_output；至少 3 samples | gene-gene coexpression | aggregate Pearson network + sample-specific networks | undirected | aggregate + sample-specific | 否 | 否；不是 TF-gene network |
| CONDOR | bipartite community detection | 已有 regulatory／association network 中哪些兩側 node 形成 modules？ | validated weighted source-target-weight edge list、output_dir、可選 prefix | existing bipartite edge；輸出兩側 membership，不重新推論 edge | prefix-edges.tsv、prefix-reg_memb.tsv、prefix-tar_memb.tsv、prefix-summary.txt | edge 保留 input contract；community 本身無方向 | not applicable | 不需要 biological prior；依 input network | 無 registry target；可接收 PANDA/PUMA/OTTER 的合格 edge list |
| COBRA | covariate-aware coexpression | batch／hospital／treatment 是否改變 covariance structure？ | gene-by-sample expression、numeric sample-by-covariate design、output_dir | covariate-associated covariance components；adjusted gene-gene coexpression artifact | components.npz、summary.tsv、adjusted_coexpression.tsv/.npz、manifest.json | undirected coexpression artifact | aggregate | 使用 design matrix，不是 motif prior | 是；adjusted artifact 重新驗證後 → PANDA/PUMA/OTTER 的 coexpression_file |
| GIRAFFE | biologically informed matrix factorization | 哪些 TF-gene 關係有 signed regulatory effect？每個 sample 的 TFA 如何？ | expression、motif/prior、PPI、output_file | signed TF-gene partial regulatory effects；另有 TF-by-sample activity | regulation matrix + output-stem.tfa-same-suffix | directed / bipartite | aggregate（加 sample-level TFA） | 是：motif、PPI | 否；未註冊 direct handoff |
| BONOBO | Bayesian sample-specific coexpression | 如何用每個 sample 的 expression 與 cohort background 估計個體化 coexpression？ | labeled gene-by-sample expression、output_dir；可選 sample names、sparsify、p-values 等 | gene-gene posterior coexpression；optional p-values | 每 sample 一個 .h5/.hdf/.txt/.csv + manifest.json，可有 p-values | undirected | sample-specific | Bayesian background prior | 否；需先選 sample 或定義 aggregation、轉換、驗證、確認 |
| SAMBAR | mutation pathway aggregation | 稀疏 somatic mutations 能否在 pathway 層級比較並做 subtyping？ | samples-by-genes mutation CSV、gene-length CSV、cancer-gene list、GMT pathway、output_dir | gene／pathway mutation score；cluster label | mt_out.csv、pt_out.csv、可選 clustergroups.csv、dist_matrix.csv、manifest.json | 不適用於 regulatory edge | not applicable（sample-by-pathway score） | 使用 gene length、pathway annotation、可選 cancer-gene subset | 否；獨立 mutation→pathway→subtype branch |
| DRAGON | two-layer GGM | 兩個 matched omics layer 在控制其他變數後有哪些 conditional associations？ | exactly two sample-by-feature continuous tables、output_file；可選 lambda1／lambda2 | layer-qualified feature—feature partial correlation／precision | labeled symmetric matrix 或 source,target,partial_correlation,precision edge list | undirected | aggregate | 使用 layer-specific shrinkage，不是 motif/PPI prior | 否；禁止直接送 PANDA／CONDOR 等 |
| OTTER | relaxed graph matching | 哪個 TF-gene W 同時符合 PPI projection 與 gene coexpression projection？ | OTTER W seed/prior、TF-TF PPI、expression 或 validated coexpression C、output_file | optimized aggregate TF→gene W score | labeled TF-by-gene matrix 或 complete source,target,weight edge list | directed / bipartite | aggregate | 是：W0／motif；P、C 是 projection evidence | 是，只有 validated edge list → CONDOR；COBRA adjusted C 可經驗證後使用 |

### 你現在應該能回答

1. 哪些 output 是 aggregate、哪些是 sample-specific、哪些是 not applicable？
2. 哪些 network 是 TF→gene regulatory，哪些只是 gene-gene 或 feature-feature association？
3. 為什麼 PANDA/PUMA/OTTER 的 handoff 需要 edge-list 或 adjusted coexpression validation？

<a id="regulatory-family"></a>
## 6. Regulatory inference 家族：PANDA、PUMA、OTTER、GIRAFFE

四者都可能回答「TF 與 gene 如何形成 regulatory network」，但它們的 edge score 不是同一個量。PANDA／PUMA 偏向多張 network 的一致性 evidence；OTTER 明確把 problem 寫成 projection matching；GIRAFFE 則把 regulation effect 與 TFA 放在同一個 factorization 中，並依最新原始論文把 signed partial regulatory effect 解讀為方向與強度。

### 6.1 PANDA

#### 一句話定位

PANDA（Passing Attributes between Networks for Data Assimilation）把 TF-gene prior、TF-TF PPI 與 gene-gene coexpression 反覆傳遞資訊，得到一張代表 cohort／條件的 aggregate TF→gene regulatory evidence network。

#### 生物問題

motif 只告訴我們「TF 可能接近 gene」，但可能有 false positive；expression 只告訴我們 gene 如何一起變動；PPI 提供 TF 可能組成複合體的資訊。PANDA 要問的是：哪些 TF→gene 關係能同時與三種 evidence 保持較一致？

#### 輸入資料

| 輸入 | 列／欄 | 生物意義 |
|---|---|---|
| expression_file | gene rows × sample columns | gene order、sample expression，以及在沒有 coexpression_file 時用於建立 Pearson coexpression |
| motif_file | regulator、gene、weight 的 edge list，或相容的 prior 表 | TF 是否有 motif／binding prior |
| ppi_file | TF、TF、weight 的 edge list | TF-TF protein interaction |
| coexpression_file（可選） | 有 label 的對稱 gene-by-gene matrix | 目前 agent 可用已驗證的 adjusted coexpression 取代內部 Pearson construction |
| output_file | 輸出路徑 | 不能與 input collision |

目前 agent 仍需要 expression_file，即使使用 coexpression_file；expression 供 gene order 與 prior compatibility 檢查，不會被「預先計算的 coexpression」完全取代。

#### 輸出產物

output_file 是 aggregate weighted TF-by-gene regulatory network。edge 表示「在此模型、prior、expression／coexpression 與 PPI 下的 regulatory evidence score」。它不是機率，也不是每個 sample 各一張網路。

#### 核心機制

~~~text
motif prior F (TF × gene) ─┐
                            ├─ message passing / consistency updates ─→ final TF × gene score
TF-TF PPI P ────────────────┤
gene-gene coexpression C ───┘
~~~

直覺上，若一個 TF 與某些 TF 有 PPI，而這些 TF 的 target gene 又呈現一組一致的 coexpression pattern，更新可提高某些 TF-gene edge 的一致性；反之，若 prior 與其他 evidence 長期衝突，edge score 可能被降低。這是「讓多張資料網路互相約束」的簡化說法，不是把三個數字簡單相乘。

#### 為什麼有機會成功

它利用三種互補資訊：sequence prior 限定候選範圍、PPI 描述 regulator side 的協同可能性、coexpression 提供 target side 的資料訊號。對高維 expression 而言，prior 也能減少完全無約束搜尋的空間。

#### 必要假設

- TF、gene、PPI 與 expression 的 identifier 能被精確對齊。
- motif prior 雖有誤差，仍含有足夠的候選關係。
- gene-gene coexpression 對所研究條件有可用訊號，且樣本數足以估計它。
- PPI 的 TF IDs 與 motif 的 regulator IDs 語意一致。
- batch、hospital、treatment 等主要 confounder 已被適當處理或納入研究設計。

#### 容易失敗的情況

- gene／TF ID 的版本、大小寫或 alias 不一致。
- expression 軸向反了，或把 sample metadata 當成 gene column。
- prior 過度偏斜：所有重要的真實 edge 都不在候選集合內。
- 高維小樣本造成 coexpression 不穩定。
- 完全 confounded 的 batch 與 phenotype 被當成可分離的 effect。
- 把 score 的正負直接解讀成 activation／repression，或把絕對值當 probability。

#### 結果怎麼解讀

> 「在指定 expression／coexpression、motif prior、PPI 與模型設定下，TF TF1→gene G1 的 PANDA score 較其他候選 edge 高，因此它是較強的整合式 regulatory evidence；仍需外部資料驗證。」

#### 結果不能怎麼解讀

> 「PANDA score = 0.9，所以 TF1 有 90% 機率活化 G1，且已證明 TF1 造成疾病。」

#### 與其他 workflows 的關係

- 與 PUMA：PANDA 的 regulator layer 只有 TF；PUMA 再加入 miRNA。
- 與 OTTER：資料家族相近，但 PANDA 以 message passing 描述一致性，OTTER 以 graph matching／optimization 描述 projection。
- 與 COBRA：COBRA 的 adjusted coexpression 經 identifier／order／shape／finite value 驗證後，可進 coexpression_file。
- 與 LIONESS-PANDA：LIONESS 在 construction 內部重跑 aggregate PANDA 與 leave-one-out PANDA；不是把已寫出的 PANDA 檔案當 input。
- 與 CONDOR：合格 PANDA network 必須明確轉成 source-target-weight bipartite edge list。

#### 目前 agent 邊界

**[agent]** registry run_panda 要求 expression_file、motif_file、ppi_file、output_file；可選 coexpression_file。YAML 明確寫出 adjusted coexpression 只取代 Pearson construction，不能取代表達矩陣。PANDA output 可在轉換與驗證後交給 run_condor。PANDA 不會自動做 batch correction、normalization 或 identifier harmonization。

#### 極小型例子

repository 的官方 toy bundle：data/official-toy/ToyExpressionData.txt、ToyMotifData.txt、ToyPPIData.txt。它展示 expression、TF-gene prior、TF-TF PPI 的檔案角色；把它跑通只代表檔案與 runtime contract 可用，不能支持任何真實 TF-gene 或疾病結論。

### 6.2 PUMA

#### 一句話定位

PUMA（PANDA Using MicroRNA Associations）把 TF 與 miRNA 都放在 regulator side，整合 TF motif、TF-TF PPI、miRNA-target prior 與 gene-gene coexpression，得到 TF／miRNA→gene regulatory evidence network。

#### 生物問題

只看 TF 可能漏掉 post-transcriptional regulation。PUMA 要問的是：在同一個 regulatory network 裡，TF 與 miRNA 是否能共同解釋 gene-level expression pattern，以及哪些 regulator-target 關係較有整合式 evidence？

#### 輸入資料

| 輸入 | 角色 |
|---|---|
| expression_file | gene-by-sample expression；目前 legacy PUMA wrapper 要求不含 header 的執行格式，若需要可先用 format_expression |
| motif_file | TF-gene motif/prior edge；miRNA target prior 依目前 adapter 的檔案契約與 miRNA list 對齊 |
| ppi_file | TF-TF PPI |
| mirna_file | 一行一個 miRNA identifier；不能用 positional index |
| coexpression_file（可選） | labeled、symmetric gene-by-gene matrix；經驗證後取代 Pearson construction |
| output_file | aggregate regulator-to-gene output |

#### 輸出產物

輸出是 aggregate、weighted、TF／miRNA-to-gene bipartite regulatory network。miRNA 在生物學上常見抑制 target mRNA 的機制，但 PUMA edge score 的正負不應直接翻譯成「活化／抑制方向」；它仍是 PUMA message-passing framework 的 score。

#### 核心機制

~~~text
TF-gene motif prior ─────┐
miRNA-gene target prior ─┤
TF-TF PPI ────────────────┼─ PANDA-like message passing ─→ TF/miRNA → gene scores
gene coexpression ───────┘
~~~

PUMA 把 regulator side 擴張成兩類節點；因此它不是「先跑 PANDA，再把 miRNA 欄位貼上去」。miRNA prior、TF prior、PPI 與 gene-side coexpression 在同一個一致性架構中共同影響結果。

#### 為什麼有機會成功

它能把 transcriptional 與 post-transcriptional evidence 放在同一個 bipartite network 中，讓同一組 target expression pattern 受 TF 與 miRNA 的互補資訊約束。這對 miRNA 的 gene-level effects 通常比單看 miRNA abundance 更接近 network-level 問題。

#### 必要假設

- mirna_file 的 ID 與 prior 的 regulator 欄位一致。
- motif、PPI、expression 的 TF／gene IDs 正確對齊。
- miRNA target prior 的來源與 cohort／物種相容。
- coexpression 不只是 batch 或 cell-composition 的假象。

#### 容易失敗的情況

- 把 miRNA list 當成矩陣，或一行包含多個 ID。
- PUMA legacy expression header 格式未先處理。
- miRNA alias、gene version、species 不一致。
- 把典型 miRNA repression biology 直接套成每條 PUMA edge 的 sign。
- 高維小樣本與 prior bias 造成 regulator ranking 不穩定。

#### 結果怎麼解讀

> 「在此 PUMA prior 與 expression/coexpression evidence 下，miRNA miR-1 與 gene G1 的 edge score 相對較高，表示模型認為這個 regulator-target 關係值得優先驗證。」

#### 結果不能怎麼解讀

> 「miR-1→G1 的 PUMA score 為負，所以已證明 miR-1 直接抑制 G1 並造成治療抗性。」

#### 與其他 workflows 的關係

- PANDA：只有 TF regulator layer；PUMA 加入 miRNA。
- LIONESS-PUMA：同時使用原始 expression、motif、PPI、miRNA prior，在 leave-one-out construction 內部重算 PUMA。
- COBRA：adjusted coexpression 可經驗證後作 PUMA 的 coexpression_file，但不能直接拿 raw components。
- CONDOR：PUMA network 轉成並驗證 bipartite edge list 後可分析 communities。

#### 目前 agent 邊界

**[agent]** run_puma 要求 expression、motif、ppi、miRNA list、output；可選 labeled adjusted coexpression。legacy PUMA execution 不接受 expression header，agent 會要求 bounded formatting；這是目前 adapter contract，不是對 PUMA 科學方法的普遍限制。PUMA 可在合格 edge-list conversion 後 → CONDOR。

#### 極小型例子

data/official-toy/ToyMiRList.txt 是 one-ID-per-line 的 miRNA list；data/lioness-toy/prior-puma.tsv 則示範 TF／miRNA 與 gene 的 prior edge。toy run 只能驗證 ID、格式與流程，不代表 miR-1 在任何真實樣本中確實調控某 gene。

### 6.3 OTTER

#### 一句話定位

OTTER（Optimize To Estimate Regulation）把未知的 TF×gene network W 看成兩個 observed graph projection 的共同解，透過 relaxed graph matching 找到與 PPI 與 gene coexpression 都較吻合的 aggregate regulatory network。

#### 生物問題

我們通常觀察到 TF-TF PPI 與 gene-gene coexpression，卻沒有完整且可靠的 TF-gene network。OTTER 問的是：哪一個 TF-gene W 能讓 TF-side projection 和 gene-side projection 同時接近 observed data？

#### 輸入資料

| 輸入 | 矩陣／檔案語意 |
|---|---|
| motif_file | OTTER 的 TF-by-gene seed/prior W0；目前 adapter 讀 TF、gene、weight edge list |
| ppi_file | TF-TF edge list；identifier set 必須等於 W 的 TF set；adapter 形成 P |
| expression_file（二選一） | gene-by-sample expression；adapter 由 gene rows 計算 C |
| coexpression_file（二選一） | labeled symmetric gene-by-gene C；目前 agent adapter 額外支援 |
| lam | coexpression 與 PPI projection 的相對權重，必須在 [0,1] |
| gamma | regularization；目前不能稱為獨立 sparsity threshold |

W、P、C 的概念形狀是：W: TF × gene、P: TF × TF、C: gene × gene。

#### 輸出產物

目前 agent 可輸出：

- labeled TF-by-gene matrix；或
- complete source,target,weight TF→gene edge list。

weight 是 optimized OTTER W score，為 aggregate regulatory artifact，不是 sample-specific network，也不等於 probability。

#### 核心機制

~~~text
unknown W (TF × gene)
   ├─ W Wᵀ  ≈  P   （TF-side projection / PPI）
   └─ Wᵀ W  ≈  C   （gene-side projection / coexpression）
~~~

概念上的 objective 可寫成：

~~~text
min_W  (1 - λ) ||W Wᵀ - P||² / 4
     + λ       ||Wᵀ W - C||² / 4
     + γ       ||W||² / 2
~~~

公式是教學化寫法；實際輸入 preprocessing、PPI transformation、初始化與版本細節要以 pinned runtime 與 docs/OTTER_INTEGRATION.md 為準。lam 越高表示比較重視 C；current agent 對 gamma 的 contract 是 regularization，不提供獨立 sparsity／threshold argument。

#### 為什麼有機會成功

它利用「同一個 TF-gene network 的兩側 projection 應該互相一致」這個結構性限制。當 PPI 與 coexpression 各自 noisy，但仍含有共同 network signal 時，matching objective 比只用單一資料來源更有機會得到穩定候選 network。

#### 必要假設

- W、P、C 的 TF／gene ID 與順序精確一致；目前 adapter 不做 implicit intersection 或 reorder。
- PPI 的 TF set 等於 W 的 regulator set，TF 與 gene partitions 不重疊。
- C 是有效的 gene-gene coexpression，且與 W 的 gene axis 相同。
- PPI、coexpression 可作為 W 的 noisy projections，而非完全不同生物層的量。

#### 容易失敗的情況

- W、P、C 的 identifier mismatch、空列、重複 pair、NA 或非有限值。
- 把 PPI 或 C 誤當成 PANDA 的 motif prior。
- 把 official reader 的 permissive merging 當成安全的自動對齊。
- 把 gamma 說成「自動得到稀疏 network」，或把 output sign 當 activation／repression。
- expression 與 coexpression_file 同時提供但 order 不一致。

#### 結果怎麼解讀

> 「OTTER 找到一個 aggregate W，使 TF-side projection 與 gene-side coexpression 在指定 lam、gamma 與初始化下較一致；W(TF1,G1) 是需要外部 binding／perturbation 資料驗證的 regulatory hypothesis。」

#### 結果不能怎麼解讀

> 「OTTER 的 W score 是 TF1 binding G1 的機率，而且已證明 TF1 是 G1 的上游因果 regulator。」

#### 與其他 workflows 的關係

- PANDA：同樣使用 motif／PPI／coexpression 資料家族；PANDA 是 message passing，OTTER 是 explicit optimization／graph matching。
- COBRA：adjusted coexpression 在重新驗證後可成為 C。
- CONDOR：只有 validated edge-list output 能交給 CONDOR；matrix 必須先 conversion。
- LIONESS-OTTER：上游 netZooPy 另有 LionessOtter／otterlioness；目前 agent 只註冊 aggregate run_otter，不可混稱已支援 LIONESS-OTTER。

#### 目前 agent 邊界

**[agent]** run_otter 需要 motif、PPI、output，並可由 expression 或 validated coexpression 提供 C；current runtime 只啟用 CPU。output_format=matrix 或 edge_list 會被嚴格驗證。只有 source-target-weight edge-list export 可 → CONDOR；GIRAFFE、DRAGON、BONOBO、LIONESS 等沒有直接 handoff。

#### 極小型例子

data/otter-toy/expression.tsv、motif.tsv、ppi.tsv 是可檢查 W/P/C 對齊的小型 bundle。它的目的是驗證形狀與輸入角色，不是建立可發表的 GRN。

### 6.4 GIRAFFE

#### 一句話定位

GIRAFFE 以 biologically informed matrix factorization 同時估計 aggregate TF-gene regulatory effects 與每個 sample 的 TF activity（TFA）。

#### 生物問題

研究者通常想知道兩件互相關聯但不相同的事：

1. 某 TF 對某 gene 的 regulatory effect 是什麼方向、強度如何？
2. 在每個 sample 中，這個 TF 的整體活動程度如何？

只看 TF mRNA expression 未必能回答第二題，因為 activity 受蛋白層、complex、localization 與 post-translational regulation 影響。

#### 輸入資料

| 輸入 | current agent contract |
|---|---|
| expression_file | gene-by-sample numeric table；第一欄 unique gene IDs，header 提供 samples |
| motif_file | 三欄 regulator/gene/weight edge list，或 labeled TF-by-gene prior matrix |
| ppi_file | TF edge list 或 labeled square TF matrix；edge-list 會被 adapter symmetrize 並補 unit diagonal，再驗證 symmetry |
| output_file | regulation matrix 路徑；TFA 會寫在同 stem 的 sibling path |

adapter 會轉成 source API 所需的 arrays：expression genes × samples、prior TFs × genes、PPI TFs × TFs。

#### 輸出產物

- regulation：aggregate TF-by-gene matrix。
- TFA：與 output_file 同 stem、加上 .tfa 與相同 suffix，是 TF-by-sample matrix。

最新 GIRAFFE 原始論文把 regulation edge 描述為 **signed partial regulatory effects**；在該方法語境中 magnitude 與 sign 可分別支持調控強度與 direction。這個語意不能跨方法套給 PANDA、PUMA 或 OTTER。

要留意矩陣記號的方向：若用 expression Y 表示 gene × sample，教學上可把 R 定義成 gene × TF、A 定義成 TF × sample，寫成：

~~~text
Y ≈ R × A
~~~

而 current agent 儲存的 regulation artifact 是 TF × gene，因此若要做乘法必須明確轉置；不能因為檔案標題叫 regulation 就忽略 axis。

#### 核心機制

~~~text
observed expression Y (gene × sample)
              ≈ R (gene × TF) × A (TF × sample)

motif prior + TF-TF PPI ──約束／引導 R 與 A 的 biologically informed factorization
~~~

這讓 model 不只問「TF 和 gene 是否有 edge」，也嘗試讓多個 target genes 的 expression pattern 由 latent TF activity 與 regulatory coefficients 共同解釋。

#### 為什麼有機會成功

它把 TFA 當成 latent factor，而不是把 TF expression 當 activity 的替代品；motif prior 限定潛在 connection，PPI 讓相互作用 TF 可能共享 complex／調控結構的資訊進入 model。這是一種比單看 TF expression 更接近「functional activity」問題的建模方式。

#### 必要假設

- expression、prior、PPI 的 IDs 與 orientation 可被精確對齊。
- 矩陣 factorization 的近似對研究資料仍有合理解釋。
- motif prior 與 PPI 足以提供有用的 biological guidance，而不是嚴重誤導。
- sample expression 的 normalization、batch 與 covariate 處理已在適當層級完成。

#### 容易失敗的情況

- motif 的 gene set 與 expression 不相同。
- PPI edge list 不對稱、TF IDs 不完整或 diagonal 不合 contract。
- 把 TFA 當成 TF expression；或把 regulation matrix 當成每個 sample 一張 GRN。
- 高維小樣本導致 factorization 不穩定；prior bias 被誤當成 data discovery。
- 把 signed GIRAFFE partial regulatory effect 的 sign 套到其他方法的 score。

#### 結果怎麼解讀

> 「GIRAFFE 在 pinned version 與指定 input 下估計 TF1→G1 的 signed partial regulatory effect，並在 sample S1 給出 TF1 的 TFA；兩者是 aggregate regulation 與 sample-level activity 的不同產物，需用 perturbation 或 orthogonal data 驗證。」

#### 結果不能怎麼解讀

> 「TFA 高代表 TF1 的 mRNA 一定高；regulation sign 也能直接套用成 PANDA 的 activation／repression score。」

#### 與其他 workflows 的關係

- 與 PANDA：都用 motif、PPI、expression，但 GIRAFFE 著重 signed effects + TFA；PANDA 著重整合 evidence network。
- 與 COBRA：repository 目前沒有 GIRAFFE coexpression_file handoff；COBRA 的 adjusted coexpression 不是 GIRAFFE 的 declared input。
- 與 CONDOR：科學上可把 regulation matrix 轉 edge list，但 current agent 沒有 direct handoff，需 user-confirmed conversion。
- 與 LIONESS：目前不會因為有 sample-level TFA 就變成 sample-specific TF-gene network。

#### 目前 agent 邊界

**[agent]** current workflow 使用 Docker pinned netZooPy 0.11.0；host Python 不會偷偷安裝另一份 netZooPy。run_giraffe 只呼叫 verified Giraffe(expression, prior, ppi)、get_regulation() 與 get_tfa()，並驗證兩個 output。registry 明確沒有 direct handoff 到 PANDA、PUMA、LIONESS、CONDOR 或其他 workflow。

#### 極小型例子

data/giraffe-toy/expression.tsv、motif.tsv、ppi.tsv 展示最小 coherent bundle；tests/test_giraffe_workflow.py 還驗證 output regulation 與 sibling TFA 的 contract。toy run 不支持真實 signed regulatory conclusion。

<a id="sample-specific-family"></a>
## 7. Sample-specific 家族：三種 LIONESS、BONOBO

這一章的核心問題是「為什麼同一個 cohort 的 network 可以因 sample 而不同」。sample-specific 不代表有一張觀測到的個體 network；它是用 estimator、背景樣本與模型假設從 cohort data 推導出來的產物。

### 7.1 LIONESS 的共同直覺與公式

LIONESS（Linear Interpolation to Obtain Network Estimates for Single Samples）是一個 estimator-agnostic framework。對 sample k：

~~~text
N_k = n × N_all - (n - 1) × N_without_k
~~~

其中：

- N_all：全體 n 個 samples 建出的 network。
- N_without_k：拿掉 sample k 後重新建出的 network。
- N_k：估計 sample k 對 network 的貢獻。

白話說，若拿掉 k 後某條 edge 大幅改變，線性外插會把這個 sample 的 network contribution 拉出來。它不是把 sample 的單一 expression vector 直接算成一張可靠 correlation matrix；背景樣本提供估計 coexpression／regulatory structure 所需的資訊。

教學例子：假設 n=4、某 edge 的 N_all=0.40、N_without_k=0.30，則 N_k = 4×0.40 - 3×0.30 = 0.70。這只展示公式，不代表 0.70 是 probability，也不代表實際 biology。

**重要邊界：** LIONESS-PANDA/PUMA 的 PANDA/PUMA 是 **guidance predecessor**；agent 會在每個 leave-one-out construction 中使用原始 expression 與 prior 內部重建 estimator，不是把已輸出的 aggregate PANDA/PUMA file 直接餵給 LIONESS。Aggregate COBRA artifact 也不是 LIONESS 的 direct handoff；若 leave-one-out 背景要做 COBRA adjustment，必須在相應 construction 裡重新處理。

### 7.2 LIONESS-PANDA

#### 一句話定位

LIONESS-PANDA 用 PANDA 作為 base estimator，產生 aggregate PANDA network 與每個 sample 的 TF→gene regulatory network。

#### 生物問題

同一癌症 cohort 裡，不同病人的 TF regulatory wiring 是否不同？某個 sample 是否有特定 TF-target pattern，而這個 pattern 在 aggregate network 被平均掉？

#### 輸入資料

需要 expression_file、motif_file、ppi_file、aggregate output_file、sample-specific lioness_output。expression 需至少 3 samples，讓每次 leave-one-out 後仍有至少 2 samples 可估計 correlation。legacy wrapper 對 expression/header 與 output suffix 有額外限制；agent 可先做 bounded format preparation。

#### 輸出產物

output_file 是 aggregate PANDA network；lioness_output 是 sample-specific PANDA network artifact。兩者要保持不同 path，也要明確記錄 sample identity。sample-specific edge 的 semantics 沿用 PANDA，但粒度改成 sample-specific。

#### 核心機制

~~~text
原始 expression + motif + PPI
        ├─ PANDA(all samples)       → N_all
        └─ PANDA(remove sample k)    → N_without_k
                         ↓
              N_k = nN_all − (n−1)N_without_k
~~~

#### 為什麼有機會成功

它把一個 sample 對 cohort-level estimator 的影響轉成 network scale 的估計；因此能保留 sample-level heterogeneity，而不是只比較兩張 aggregate network。

#### 必要假設

- leave-one-out 後的 base estimator 仍可穩定估計。
- samples 可視為同一研究問題下的可比較觀測。
- sample-specific 差異不是純粹 batch、hospital 或 sequencing depth artifact。
- prior 對所有 sample 的使用方式一致且沒有把某一組 sample 系統性偏好。

#### 容易失敗的情況

- 少於 3 samples。
- outlier sample 讓 N_all 與 N_without_k 差異極端。
- 把 aggregate COBRA output 當成每個 leave-one-out 的 adjusted C。
- 把 output 當成直接可餵 CONDOR 的 artifact，卻未選定 sample 與檢查 bipartite edge schema。

#### 結果怎麼解讀

> 「sample S1 的 LIONESS-PANDA TF1→G1 edge 相對 cohort aggregate 偏高，表示 S1 對 PANDA network estimate 的 model-based contribution 較強；需用重抽樣與外部 evidence 檢查穩定性。」

#### 結果不能怎麼解讀

> 「S1 的 edge 高，所以在 S1 的細胞裡已直接觀察到 TF1 binding G1。」

#### 與其他 workflows 的關係

與 LIONESS-coexpression 共享 leave-one-out machinery，但 edge semantics 完全不同；與 BONOBO 都是 sample-specific coexpression／network 思維，卻使用不同 estimator；不是 BONOBO→LIONESS 的直接串接。

#### 目前 agent 邊界

registry 的 guidance_predecessors 是 run_panda，沒有 handoff_targets。因此 PANDA 是方法指引，不是 required aggregate file input；COBRA adjusted artifact 也不是 direct input。

#### 極小型例子

data/lioness-toy/expression.tsv、motif-panda.tsv、ppi.tsv 可用來檢查 PANDA-LIONESS 的 file roles。樣本數只有 toy 規模，不能用來宣稱 sample-specific biology。

### 7.3 LIONESS-PUMA

#### 一句話定位

LIONESS-PUMA 將 PUMA 放進 leave-one-out construction，產生 aggregate PUMA 與每個 sample 的 TF/miRNA→gene network。

#### 生物問題

不同病人的 transcriptional 與 post-transcriptional regulation 是否有不同？某個 sample 是否呈現特定 miRNA-target network pattern？

#### 輸入資料

需要 expression、motif、PPI、one-ID-per-line mirna_file、aggregate output_file 與 lioness_output。agent 要求至少 3 expression samples，並保留 miRNA prior／ID validation。

#### 輸出產物

aggregate output 是 PUMA regulator-to-gene network；lioness_output 是 sample-specific TF/miRNA-to-gene network。miRNA edge 的 score 仍沿用 PUMA semantics，不因 sample-specific 就自動變成直接抑制效果。

#### 核心機制

~~~text
原始 expression + TF prior + miRNA prior + PPI
        ├─ PUMA(all samples)       → N_all
        └─ PUMA(remove sample k)    → N_without_k
                         ↓
              N_k = nN_all − (n−1)N_without_k
~~~

#### 為什麼有機會成功

它保留 PUMA 對 miRNA regulator layer 的建模，同時讓 leave-one-out 差異呈現 sample-level heterogeneity。這能把「cohort 平均上有 miRNA evidence」與「某個 sample 的估計 network 偏離平均」分開。

#### 必要假設

- 每個 leave-one-out PUMA run 的 prior 與 ID contract 相同。
- miRNA-target prior 具備足夠的 cohort／species relevance。
- sample-specific differences 不是缺失值、batch 或 composition 的產物。

#### 容易失敗的情況

- miRNA list 未與 prior 對齊、ID 重複或格式錯誤。
- 少於 3 samples；或把 sample index 當 name 傳入。
- aggregate COBRA adjusted C 被誤當成 leave-one-out adjusted C。
- 把 edge sign 直接解讀成 miRNA inhibition magnitude。

#### 結果怎麼解讀

> 「sample S2 的 miR-1→G1 PUMA-LIONESS score 高於 aggregate，表示模型估計 S2 對此關係的 network contribution 較強；它是候選 hypothesis，不是直接 binding observation。」

#### 結果不能怎麼解讀

> 「S2 的 miR-1→G1 score 高，所以 miR-1 一定在 S2 直接抑制 G1。」

#### 與其他 workflows 的關係

與 PUMA 共享 base estimator、與 LIONESS-PANDA 共享 framework；和 BONOBO 的 sample-specific network 不可混接；可將特定 sample 的 edge list 另行轉換後做 community analysis，但目前沒有 direct registry handoff。

#### 目前 agent 邊界

run_lioness_puma 的 guidance predecessor 是 run_puma，沒有 direct handoff target。PUMA 不是一個要先產生再交給 LIONESS 的 aggregate file。

#### 極小型例子

data/lioness-toy/prior-puma.tsv 與 mirna.txt 示範 TF／miRNA prior 的最小 schema；它只支持格式與 teaching flow。

### 7.4 LIONESS-coexpression

#### 一句話定位

LIONESS-coexpression 以 Pearson coexpression 作為 base estimator，輸出 aggregate gene-gene coexpression 與 sample-specific gene-gene coexpression。

#### 生物問題

某個 sample 是否使一對 gene 的共同變動 pattern 特別強或特別弱？aggregate correlation 是否掩蓋了個體差異？

#### 輸入資料

需要 gene-by-sample expression_file、aggregate output_file、sample-specific lioness_output。current wrapper 至少要求 3 samples；expression 可能先被自動格式化成 legacy LIONESS 所需格式。

#### 輸出產物

output_file 是 aggregate Pearson coexpression；lioness_output 是 sample-specific gene-gene coexpression。兩者都是 single-layer、undirected、gene-gene 關係，不是 TF-gene GRN。

#### 核心機制

~~~text
Pearson(expression_all)       → N_all
Pearson(expression_without_k) → N_without_k
N_k = n × N_all − (n − 1) × N_without_k
~~~

#### 為什麼有機會成功

它使用相同 Pearson estimator 在 full 與 leave-one-out data 上的差異，能把 sample-specific contribution 表示成 network-level edge。它的透明之處是公式簡單；限制是線性外插與 correlation estimator 的假設也會被帶進結果。

#### 必要假設

- 每次 correlation matrix 都用相容的 gene order、normalization 與 sample subset。
- leave-one-out 後仍有足夠樣本估計 correlation。
- expression 中的共變動不是主要由 batch、hospital 或 cell mixture 造成。

#### 容易失敗的情況

- N 太小、outlier 影響 correlation、missing values 或 gene variance 為零。
- 把 edge 當成 causal interaction 或 regulatory direction。
- 把 output 直接當 PANDA/PUMA/OTTER 的 TF-gene network。

#### 結果怎麼解讀

> 「S3 的 G1-G2 LIONESS coexpression 比 aggregate 值高，表示在 Pearson leave-one-out 模型下，S3 對此 gene pair 的共同變動估計有較大貢獻。」

#### 結果不能怎麼解讀

> 「G1-G2 在 S3 有高 coexpression，所以 G1 直接調控 G2。」

#### 與其他 workflows 的關係

與 BONOBO 都輸出 sample-specific gene-gene network；與 COBRA 都處理 coexpression，但 COBRA 是 covariate-aware covariance decomposition；可作為 PANDA/PUMA/OTTER 的 conceptual gene-side evidence，但 current registry 沒有 direct handoff。

#### 目前 agent 邊界

run_lioness_coexpression 沒有 validation_steps，execution wrapper 仍要求至少 3 samples 並驗證 expression；registry 的 handoff targets 為空。aggregate 與 sample-specific output 必須保持不同。

#### 極小型例子

data/lioness-toy/expression.tsv 是 3 genes × 4 samples 的小表；它非常適合手算 axis 與 leave-one-out 公式，但不適合估計穩定網路。

### 7.5 BONOBO

#### 一句話定位

BONOBO（Bayesian Optimized Networks Obtained By assimilating Omics data）對每個 sample 使用自己的 centered expression deviation 加上其餘 N-1 samples 的 background／prior information，以 Bayesian posterior 推估 sample-specific gene-gene coexpression。

#### 生物問題

如果每個病人的 molecular interaction structure 不完全相同，如何在單一 sample 資料很少的情況下，仍得到比單純樣本內 correlation 更穩定的個體 network？

#### 輸入資料

- expression_file：必須是 labeled、gene-by-sample、第一欄 unique gene ID、其餘欄 unique sample ID。
- 至少 3 samples；數值 finite、complete。
- agent 要求 caller 明確宣告 log_transformed=true 與 centered=true。
- 可選 sample_names 是實際 sample ID，不是 positional index。
- 可選 .h5/.hdf/.txt/.csv output format、sparsify、confidence、save_pvals 等。

#### 輸出產物

每個 selected sample 一個 gene-by-gene coexpression matrix，並寫 manifest.json 保存 gene order 與 sample-to-file mapping。若 sparsify=true 且 save_pvals=true，才會產生對應 p-value files。這些是 sample-specific coexpression，不是 aggregate prior、TF-gene GRN 或 causal network。

#### 核心機制

~~~text
sample k 的 centered expression deviation
                +
其他 N−1 samples 的 background / conjugate prior
                ↓
      closed-form Bayesian posterior
                ↓
      sample k 的 positive-definite coexpression estimate
~~~

Gaussian model、conjugate prior 與 closed-form posterior 讓估計可把個體訊號與背景資訊結合；positive-definite covariance／correlation estimate 對後續矩陣操作也較穩定。p-value 是 optional artifact，不能因為存在就把 edge 變 causal。

#### 為什麼有機會成功

它用 shrinkage／prior information 降低 single-sample network 的不穩定性，不把單一 sample 當成有足夠 observations 可以獨立估計完整 gene-gene covariance。這對高維、小樣本與個體化 network 問題特別重要。

#### 必要假設

- expression 的 log-transformed、centered 狀態符合模型 contract。
- Gaussian approximation 與 conjugate prior 對資料足夠合理。
- 其他 samples 的 background 對 sample k 仍有參考價值。
- gene IDs、sample names、輸出 manifest 一致。

#### 容易失敗的情況

- 未 log transform、未 center、header／gene axis 錯誤。
- 少於 3 samples、missing/non-finite values 或 duplicate sample names。
- 把 save_pvals=true 在 sparsify=false 下使用；agent 會拒絕。
- 把多張 sample-specific matrix 未經選樣本／aggregation 就當單一 aggregate coexpression_file。

#### 結果怎麼解讀

> 「BONOBO 的 sample S1 matrix 對 G1-G2 給出較高 posterior coexpression，表示在指定 log-centered data、background 與 Bayesian model 下，S1 的 gene-pair association estimate 較高。」

#### 結果不能怎麼解讀

> 「BONOBO 的 G1-G2 高，所以 G1 調控 G2；或把所有 sample matrix 平均後宣稱那就是 agent 已驗證的 PANDA input。」

#### 與其他 workflows 的關係

- 與 LIONESS-coexpression：BONOBO 是 Bayesian posterior／shrinkage，LIONESS 是 leave-one-out linear interpolation。
- 與 PANDA/PUMA/OTTER：論文概念上可支援個體化 GRN，但 current agent 不允許多張 BONOBO output 直接當單一 aggregate coexpression file。
- 與 COBRA：BONOBO 沒有 current direct COBRA handoff；若要做 covariate adjustment 必須先定義新的 validated construction。

#### 目前 agent 邊界

run_bonobo 透過 pinned netZooPy 0.11.0 public API，要求 labeled gene-by-sample matrix。registry handoff_targets=[]；integration doc 明確說沒有 aggregate/prior output，也不直接 handoff 到 PANDA/PUMA/LIONESS/CONDOR/COBRA/DRAGON/OTTER。若未來要交給 regulatory workflow，至少要明確選一個 sample 或定義 aggregation、補 row labels、重新檢查 gene order，並取得使用者確認。

#### 極小型例子

data/bonobo-toy/expression.tsv 是 labeled 3 genes × 4 samples 表；docs/BONOBO_INTEGRATION.md 說明 output file 沒有 row labels，因此 agent manifest 很重要。toy run 只能驗證 reader、sample mapping 與 artifact contract。

### 7.6 LIONESS-coexpression vs BONOBO 深度比較

| 面向 | LIONESS-coexpression | BONOBO |
|---|---|---|
| 樣本特異性來源 | N_all 與 N_without_k 的 leave-one-out linear interpolation | sample deviation + 其他 samples background／conjugate prior 的 Bayesian posterior |
| 基本 estimator | Pearson coexpression | Gaussian／conjugate Bayesian coexpression model |
| 穩定化方式 | 依 full 與 leave-one-out network 的線性外插；不自動提供 Bayesian shrinkage | posterior／shrinkage；官方概念為 positive-definite estimate |
| positive-definite | 不應假設 LIONESS 外插後一定保證 positive-definite | 模型設計可產生 positive-definite covariance／correlation estimate |
| uncertainty／p-values | current LIONESS workflow contract 沒有 p-value artifact | optional p-values；需同時 sparsify=true、save_pvals=true，仍非因果證據 |
| 輸入前提 | 至少 3 samples；依 wrapper 可能需要 legacy format | 至少 3 samples；明確 log-transformed、centered、labeled matrix |
| 優勢 | 公式透明、可套在多種 base estimator、容易理解 sample contribution | 以 prior/background 穩定高維 sample-specific covariance，並保存 sample mapping |
| 主要限制 | 小樣本、outlier、線性外插與 correlation noise | Gaussian／prior 假設、background relevance、輸出不是 aggregate network |
| 結果類型 | sample-specific coexpression | sample-specific posterior coexpression |
| 能否直接作 PANDA/PUMA coexpression_file | 否，current registry 沒有 direct handoff | 否；要先選 sample 或定義 aggregation、conversion、validation、confirmation |
| 適合問題 | 想量化某 sample 對 Pearson network 的 influence | 想在 sample-specific covariance 中引入 Bayesian stabilization |

本表的「positive-definite」是模型層的性質，不代表任何 downstream inference automatically valid；仍需檢查輸入、輸出、穩定性與外部驗證。

### 本章你現在應該能回答

1. 為什麼 LIONESS-PANDA 不是「讀取 aggregate PANDA file 再切成 sample」？
2. LIONESS-coexpression 與 BONOBO 的 sample-specific network 是用哪兩種不同機制產生？
3. 為什麼 BONOBO 的 p-value file 不能直接變成 GRN causal evidence？
4. 為什麼 aggregate COBRA artifact 不能直接代表每個 leave-one-out 背景都已校正？

<a id="covariate-multiomic-family"></a>
## 8. Covariate／multi-omic 家族：COBRA、DRAGON

### 8.1 COBRA

#### 一句話定位

COBRA（Co-expression Batch Reduction Adjustment）不是單純把每個 gene 的平均值調好；它要處理 batch、hospital 或其他 covariate 仍可能藏在 gene-gene covariance／correlation structure 中的 higher-order effect。

#### 生物問題

standard batch correction 多半針對 gene-level marginal effect，但 batch 仍可能改變 gene pair 的共同變動。COBRA 要問：在給定 sample covariates 後，哪些 covariance components 可能是 covariate-associated？調整後的 gene-gene coexpression 是否更適合作為下游 network inference input？

#### 輸入資料

| 輸入 | 方向與要求 |
|---|---|
| expression_file | labeled gene-by-sample；目前驗證要求 genes > samples、至少 2 samples、值為 numeric |
| design_file | sample rows × numeric covariate columns；第一欄 sample ID 必須精確匹配 expression columns，順序可由 adapter 對齊 |
| output_dir | 產生一組可追溯 artifacts |

類別 covariate 必須先編碼成 numeric design。intercept 會被檢查／加入；不能讓 batch 與 phenotype 完全 confounded 後再期待 COBRA 分辨不可識別的 effect。

#### 輸出產物

current wrapper 會產生：

- components.npz：raw components psi、Q、d、g；不是直接下游 matrix input。
- summary.tsv：component eigenvalue 與 covariate impact summary。
- adjusted_coexpression.tsv：labeled gene-by-gene correlation artifact。
- adjusted_coexpression.npz：對應的數值 artifact。
- manifest.json：input checksum、sample order、covariates、adjustment formula、adjusted artifact metadata。

#### 核心機制

~~~text
expression X (gene × sample) + numeric design D (sample × covariate)
                         ↓
        covariate-associated covariance components
                         ↓
        選定 intercept component 建立 adjusted coexpression
~~~

repository manifest 記錄的教學化公式是：

~~~text
Q @ diag(psi[intercept, :]) @ Q.T
→ normalize to correlation
~~~

它與「先對每個 gene 做 batch correction，再算 Pearson」的想法不同：後者不一定消除 correlation structure 裡的 higher-order covariate effect。

#### 為什麼有機會成功

它直接對 covariance structure 建模，而不是假設只要移除每個 gene 的一階平均差異就足夠。對需要把 coexpression 當作 PANDA/PUMA/OTTER gene-side evidence 的情境，這可減少明顯的 batch-driven association，前提是 design matrix 正確。

#### 必要假設

- expression sample IDs 與 design rows 一一對應。
- covariates 被正確編碼且沒有把主要 biological effect 誤放進要刪除的 covariate。
- genes > samples 的高維設定符合 adapter contract。
- adjusted artifact 的 gene IDs、順序、對稱性與有限值都被下游再次驗證。

#### 容易失敗的情況

- design sample IDs 缺失、多餘或順序誤讀。
- categorical covariate 沒有 numeric encoding。
- batch 與 phenotype 完全 confounded：沒有資料支持分離兩者。
- 誤把 components.npz 傳給 PANDA/PUMA/OTTER；它不是 labeled gene-gene matrix。
- 調整後的 correlation 被當成已消除所有 confounding 的證明。

#### 結果怎麼解讀

> 「在指定 design matrix 下，COBRA 產生一個以 intercept component 為基礎的 adjusted gene-gene coexpression artifact；其適用性要再依 PANDA/PUMA/OTTER 的 identifier/order contract 驗證。」

#### 結果不能怎麼解讀

> 「COBRA 把所有 batch effect 都消除了，因此 adjusted coexpression 的每條 edge 都是真正生物關係。」

#### 與其他 workflows 的關係

- 直接可組合：adjusted coexpression → PANDA、PUMA、OTTER，先做 exact ID／order／shape／symmetry／finite validation。
- 不直接給 LIONESS：sample-specific COBRA adjustment 要在每個 leave-one-out construction 內重新定義。
- 與 DRAGON 不同：COBRA 處理 covariate-associated coexpression decomposition；DRAGON 是兩個 omics layer 的 GGM partial correlation。

#### 目前 agent 邊界

registry run_cobra required inputs 是 expression、design、output_dir，handoff targets 是 run_panda、run_puma、run_otter。只有 labeled adjusted artifact 可透過 coexpression_file 被下游使用；raw components 本身不能當 matrix input。PANDA/PUMA/OTTER 不會由 COBRA 自動啟動，必須另行規劃與驗證。

#### 極小型例子

data/cobra-toy/expression.tsv 是 5 genes × 4 samples；data/cobra-toy/design.tsv 的 sample rows 順序故意不同，示範 adapter 依 sample ID 對齊，而不是依位置硬貼。toy data 只能驗證格式與對齊。

### 8.2 DRAGON

#### 一句話定位

DRAGON（Determining Regulatory Associations using Graphical models on multi-Omic Networks）用兩個 matched continuous omics layers 建立 aggregate、undirected 的 two-layer Gaussian graphical model。

#### 生物問題

研究者可能想問：在 methylation、proteomics 或另一個 omics layer 的其他 feature 被控制後，某個 layer1 feature 與 layer2 feature 是否仍有條件關聯？

#### 輸入資料

必須正好兩張 sample-by-feature 表：

- 第一欄是 unique sample ID。
- 其餘欄是 unique feature IDs。
- layer1 與 layer2 的 sample ID set 必須完全相同；adapter 只在證明 set 相等後重排 layer2。
- measurement 必須 finite、continuous、numeric、complete；不能期待 adapter 自動 impute、log transform 或 normal transform。
- current contract 至少 3 samples；zero-variance feature、duplicate ID、missing／non-numeric 都會被拒絕。
- sample metadata、motif、PPI、expression-matrix 不是 verified DRAGON API 的輸入。

#### 輸出產物

output_format=matrix：

- 第一欄 node_id。
- node IDs 帶有 layer1:: 或 layer2:: prefix。
- labeled、square、symmetric matrix，zero diagonal。

output_format=edge_list：恰好為：

~~~text
source, target, partial_correlation, precision
~~~

每個 undirected pair 只出現一次。

#### 核心機制

Gaussian graphical model 先估計 covariance／precision；precision matrix 的非對角元素經標準化可得到 partial correlation：

~~~text
precision matrix Ω = covariance matrix Σ 的 inverse
partial correlation(i,j) = 在控制其他變數後的條件關聯
~~~

DRAGON 用 layer-specific shrinkage 改善高維、小樣本 covariance／precision estimation，再產生 GGM network。這個「控制其他 variables」是統計條件化，不是實驗控制，也不是因果方向。

#### 為什麼有機會成功

相比直接反轉 noisy covariance，shrinkage 讓高維估計更穩定；explicitly accounting for two layers 也避免把所有 feature 當同一種測量誤差與尺度。對 continuous data，在適當 transformation 後，GGM 可提供跨 omics layer 的條件關聯視角。

#### 必要假設

- 兩層 samples 真的是 matched，且 sample IDs 可精確對齊。
- feature measurements 是適合 GGM 的 continuous data，或已先做合理 transformation。
- zero variance、missingness、technical confounders 已處理。
- 只輸入兩層；多於兩層不是 current run_dragon contract。

#### 容易失敗的情況

- layer2 sample set 不同、重複 sample ID 或錯誤 reorder。
- 把 gene-by-sample expression 當成 DRAGON 所需的 sample-by-feature table。
- 把 partial_correlation 說成 causal effect。
- 把 layer-qualified undirected edge list 當成 TF-gene bipartite edge list。
- 以為 sample_metadata、motif、PPI 或 third layer 會被 API 自動使用。

#### 結果怎麼解讀

> 「在兩層 matched data、選定 shrinkage lambda 與 GGM 假設下，layer1::gene_a 與 layer2::methyl_a 有 partial-correlation association；這表示控制模型中其他 feature 後仍有關聯，需用外部或縱向資料驗證。」

#### 結果不能怎麼解讀

> 「methylation edge 指向 gene expression，所以 methylation 已證明造成 gene silencing。」

#### 與其他 workflows 的關係

- 與 COBRA：兩者都可能產生 covariance／association artifact，但 COBRA 以 covariate design 做 coexpression adjustment；DRAGON 以 two-layer GGM 做 partial correlation。
- 與 CONDOR：CONDOR 需要 regulator-target bipartite edge；DRAGON output 是 undirected multi-omic feature network，不相容。
- 與 PANDA/PUMA/OTTER：node types 與 artifact schema 不同，不能直接當 expression/coexpression/prior。

#### 目前 agent 邊界

registry 與 docs/DRAGON_INTEGRATION.md 都明確沒有 direct handoff 到 PANDA、PUMA、LIONESS、CONDOR、BONOBO、OTTER。若未來要做轉換，必須定義 conversion artifact、保留 provenance、重新驗證 node semantics，並取得確認；current agent 不會默默串接。

#### 極小型例子

data/dragon-toy/layer1.tsv 與 layer2.tsv 的 layer2 sample 順序不同，展示 adapter 會依 exact sample IDs 對齊。它不是 methylation biology 的證據。

### 8.3 COBRA vs DRAGON vs 一般 coexpression

| 面向 | 一般 coexpression | COBRA | DRAGON |
|---|---|---|---|
| 主要量 | Pearson correlation 或其他 gene-gene covariance summary | covariate-associated covariance components + adjusted coexpression | two-layer GGM partial correlation + precision |
| 資料層 | 通常一個 expression layer | 一個 expression layer + design matrix | 正好兩個 matched sample-by-feature continuous layers |
| batch／covariate | 若不另行處理，可能留下 spurious association | 直接把 numeric covariates 放進 covariance decomposition | sample_metadata 不是 current input；需先做外部 validated preprocessing |
| 是否 partial correlation | 通常不是 | adjusted covariance/correlation，不等於 GGM partial correlation | 是 |
| 粒度 | aggregate 或搭配其他方法可 sample-specific | current artifact aggregate | aggregate |
| node semantics | gene-gene | adjusted gene-gene | layer-qualified feature-feature |
| 是否 causal | 否 | 否 | 否 |
| 可否直接交給 PANDA/PUMA/OTTER | 需符合 labeled coexpression contract | adjusted artifact 可，raw components 不可 | 不可；artifact 與 node contract 不同 |

### 本章你現在應該能回答

1. 為什麼 standard batch correction 之後仍可能有 higher-order batch effect？
2. 為什麼 COBRA 的 components.npz 不能直接作 coexpression_file？
3. DRAGON 的 partial correlation 和因果方向差在哪裡？
4. 為什麼 DRAGON 不能因為輸出叫 network 就送給 CONDOR？

<a id="downstream-family"></a>
## 9. Downstream structure／subtyping：CONDOR、SAMBAR

### 9.1 CONDOR

#### 一句話定位

CONDOR（COmplex Network Description Of Regulators）在一張既有的 weighted bipartite network 上找 community，不從 raw expression 重新推論 regulatory edge。

#### 生物問題

如果已經有 TF／gene 或其他兩側的 network，哪些 regulators 與 targets 形成相對緊密的 module？這些 modules 是否可能對應共同的調控程式？

#### 輸入資料

network_file 需是至少包含下列欄位的 edge list：

~~~text
source,target,weight
TF1,GeneA,1.0
TF1,GeneB,0.8
TF2,GeneA,0.7
~~~

weight 可是 numeric；source 與 target IDs 應維持 bipartite 分區，不應同一 ID 同時出現在兩側。current validator 會報告 overlapping source／target IDs，並拒絕不合 schema 的輸入。

#### 輸出產物

給定 prefix=condor 與 output directory，current agent 預期：

- condor-edges.tsv：輸入 edge 的 validated/staged representation。
- condor-reg_memb.tsv：regulator-side membership。
- condor-tar_memb.tsv：target-side membership。
- condor-summary.txt：edge/source/target counts、initialization／optimization method，以及可用的 modularity／Q 欄位。

modularity 或 q-score 是 community assignment 的結構品質指標，不是 biological pathway probability。

#### 核心機制

CONDOR 的核心是 bipartite community detection。它可用 bipartite modularity，並透過一側 projection 與快速 modularity optimization 找分群。要保留兩個 membership：regulator side 與 target side；不能只留下單一 gene cluster 就假裝完成 bipartite 分析。

#### 為什麼有機會成功

它利用 existing network 的 topology：若一群 regulators 共享的 target 比 null model 預期更集中，或一群 targets 被一組相似 regulators 連接，community assignment 可能抓到 network-level organization。這不等於 pathway enrichment 已經成立。

#### 必要假設

- input edge list 確實是 bipartite，source/target role 清楚。
- weight 的尺度、方向與缺失處理適合 modularity。
- upstream network 的 edge semantics 可被 community analysis 合理保留。
- community 結果要用 enrichment、外部 network 或實驗做 biological validation。

#### 容易失敗的情況

- 把 raw expression、coexpression matrix、DRAGON matrix 或 SAMBAR score 當 edge list。
- source 與 target ID overlap，破壞 bipartite assumption。
- matrix output 沒有先轉成 source-target-weight。
- 只報 q-score 就宣稱發現 pathway 或 driver。

#### 結果怎麼解讀

> 「CONDOR 將這張已驗證的 TF-gene bipartite network 分成 regulator-side 與 gene-side communities；community 3 的 target genes 可進一步做 pathway enrichment 與外部驗證。」

#### 結果不能怎麼解讀

> 「CONDOR community 3 就是癌症 pathway 3，而且其中的 TF 是已證明的 master regulator。」

#### 與其他 workflows 的關係

- 上游可來自 PANDA、PUMA、OTTER，但必須是 validated source-target-weight edge list。
- GIRAFFE 科學上可轉換，但 current agent 沒有 direct handoff，需 user-confirmed conversion。
- LIONESS sample-specific regulatory network 理論上可逐 sample 分群，但 current registry 沒有 direct handoff。
- DRAGON 是 undirected multi-omic network，SAMBAR 是 mutation pathway score；兩者都不是 CONDOR 的 declared input。

#### 目前 agent 邊界

run_condor required inputs 是 network_file 與 output_dir；可選 prefix。它會先做 CONDOR input inspection，再以 current Docker wrapper 嘗試已驗證的 API constructors／methods，並驗證兩側 membership。registry 本身沒有 handoff_targets，handoff 是上游 artifact 到 CONDOR 的 contract。

#### 極小型例子

data/condor-toy/bipartite.tsv 與 data/teacher-demo/condor-bipartite.tsv 都用 TF-like source 與 gene-like target，適合理解兩側 membership。toy community 不自動代表真實 module。

### 9.2 SAMBAR

#### 一句話定位

SAMBAR（Subtyping Agglomerated Mutations By Annotation Relations）把稀疏 somatic mutations 先聚合成 gene／pathway mutation scores，再可用 sample clustering 做計算分型。

#### 生物問題

不同病人可能在同一 pathway 的不同 genes 上各自出現 mutation。若逐 gene 比較，矩陣稀疏且跨病人的 shared signal 不明顯；SAMBAR 要問的是：哪些 pathway-level mutation pattern 可以區分 sample groups？

#### 輸入資料

| 輸入 | current agent contract |
|---|---|
| mutation_file | CSV；samples rows、genes columns；值 non-negative numeric |
| exon_size_file | pinned implementation 所需的一列 CSV；gene IDs 是 columns，length 必須 positive numeric |
| cancer_gene_file | 一個 non-empty tab-delimited line 的 gene IDs |
| pathway_file | GMT：pathway name、description、至少一個 gene ID |
| optional parameters | norm_patient、kmin、kmax、gmt_msigdb、subset_cancer_genes、distance、linkage、cluster |

四個 input 的 gene identifier 必須有非空 intersection；cluster=true 時 2 ≤ kmin ≤ kmax ≤ sample count。

#### 輸出產物

- mt_out.csv：gene-level mutation score matrix。
- pt_out.csv：pathway-level mutation score matrix。
- clustergroups.csv：cluster=true 時的 sample cluster labels。
- dist_matrix.csv：cluster=true 時的 sample distance matrix。
- manifest.json：輸入、參數與 artifacts。

這些是 gene/pathway mutation scores 與 cluster labels，不是 expression network、TF-gene GRN 或 CONDOR edge list。

#### 核心機制

~~~text
somatic mutation matrix（稀疏）
        ↓ gene length／sample mutation burden normalization
gene mutation scores
        ↓ pathway annotation aggregation + pathway representation correction
pathway mutation scores
        ↓ optional distance + clustering
sample groups / computational subtypes
~~~

依 gene length／sample mutation burden 調整，能降低「gene 越長越容易被打到」或「某 sample 整體 mutation burden 高」造成的不可比性。pathway annotation 把不同 gene 的 mutation 放進共同功能層級；這是降維與知識聚合，不是自動發現 driver mechanism。

#### 為什麼有機會成功

它把稀疏 gene-level signal 匯合到 curated pathway，使不同病人即使突變的 gene 不完全相同，也可能在 pathway level 顯示共同 pattern。這利用了外部 biological annotation 作為 prior，代價是結果會依 annotation completeness 與 pathway definition 改變。

#### 必要假設

- mutation coding、gene IDs、gene lengths、cancer gene list 與 GMT 使用相容 namespace。
- mutation values 的含義一致且 non-negative。
- pathway annotation 對研究 cohort 有合理 coverage。
- cluster 數量、distance、linkage 與 sample size 相容。

#### 容易失敗的情況

- exon-size 檔案方向誤讀；把 gene rows 當 columns。
- mutation matrix 的 sample／gene axis 反了。
- pathway、cancer gene、mutation、length 沒有四方 overlap。
- cluster labels 被直接叫 clinical subtype，或 pathway score 被叫 driver score。
- cancer gene subset 或 pathway DB choice 改變後，沒有做 sensitivity analysis。

#### 結果怎麼解讀

> 「SAMBAR 在指定 gene length、pathway annotation、normalization、distance 與 clustering 設定下，將 samples 分成計算上的 mutation-pattern groups；這些 groups 可進一步與 phenotype、外部 cohort 或 functional data 比對。」

#### 結果不能怎麼解讀

> 「SAMBAR cluster 2 就是已驗證的臨床 subtype，且 pathway score 高代表 pathway 已被功能性啟動。」

#### 與其他 workflows 的關係

SAMBAR 是 mutation→pathway→subtype 的獨立 branch；它的 output 不是其他 11 個 workflow 的 direct input。可以在同一 cohort 之後把 subtype label 作為外部 phenotype，分別比較 PANDA／LIONESS／DRAGON 等結果，但這是新的統計分析，不是 artifact handoff。

#### 目前 agent 邊界

registry required inputs 是四個資料檔與 output_dir；current wrapper 將固定名稱 outputs 從 private staging directory 驗證後發布。YAML 明確禁止直接餵 PANDA、PUMA、LIONESS-PANDA、LIONESS-PUMA、CONDOR、COBRA；其他 workflow 也沒有 declared direct handoff。

#### 極小型例子

data/sambar-toy/mutation.csv、exon_size.csv、cancer_genes.txt、pathways.gmt 是四方 ID-compatible fixture；data/sambar-toy/README.md 明示它只用於 planning/test coverage。toy cluster 不能支持臨床分型。

### 9.3 CONDOR vs SAMBAR

| 面向 | CONDOR | SAMBAR |
|---|---|---|
| 已有的東西 | 一張 weighted bipartite network | 一個 samples-by-genes somatic mutation matrix + annotations |
| 找的群組 | network topology 中的 regulator-side／target-side communities | patient/sample 的 pathway mutation pattern clusters |
| 是否重新推論 regulatory edge | 否，分析既有 edge | 否，先聚合 mutation score；不是 GRN inference |
| 核心統計／結構 | bipartite modularity、q-score、projection-based community detection | gene length／mutation burden normalization、pathway aggregation、distance／linkage clustering |
| 輸出 | memberships、modularity summary | gene／pathway score、cluster labels、distance matrix |
| pathway 是否自動成立 | 否，需 enrichment／外部驗證 | pathway annotation 是 input，score 高仍不等於 pathway 功能已啟動 |
| sample 粒度 | not applicable；若 input 是 sample-specific network，可另行逐 sample 分析 | sample-level clusters |
| 能否互相直連 | SAMBAR output 不是 CONDOR edge list | CONDOR output 不是 SAMBAR mutation input |

兩者都可能在最後出現「群組」，但 CONDOR 分的是**網路兩側的節點**，SAMBAR 分的是**病人的 mutation profile**。

### 本章你現在應該能回答

1. CONDOR 為什麼不直接吃 raw expression？
2. 為什麼 CONDOR 必須保留 regulator-side 與 target-side memberships？
3. SAMBAR 的 pathway aggregation 如何降低 mutation matrix 稀疏性？
4. 為什麼 CONDOR community 與 SAMBAR patient subtype 都叫「群組」，卻不能互換？

## 10. 四組深度比較

### 10.1 PANDA vs PUMA vs OTTER vs GIRAFFE

| 面向 | PANDA | PUMA | OTTER | GIRAFFE |
|---|---|---|---|---|
| 核心目標 | TF→gene regulatory evidence | TF/miRNA→gene regulatory evidence | 由 projection matching 找 TF→gene W | 同時估計 regulation effect 與 TFA |
| regulator layer | TF | TF + miRNA | TF | TF |
| gene-side data | expression 內建 Pearson，或 validated coexpression_file | 同 PANDA | expression 計 C，或 validated coexpression C | expression Y |
| prior／PPI | motif prior + TF-TF PPI | TF motif + miRNA target prior + PPI | W0/motif、PPI projection、C projection | motif prior + TF-TF PPI |
| 主要觀點 | message passing / consistency | PANDA-like message passing with miRNA | relaxed graph matching / optimization | biologically informed matrix factorization |
| edge semantics | integrated regulatory evidence；非 probability | regulator-gene evidence；miRNA biology 不等於 score sign | optimized W score；非 probability | signed partial regulatory effect；依 GIRAFFE 語境可談 strength/direction |
| 是否估計 TFA | 否，edge score 不是 TFA | 否 | 否 | 是，TF-by-sample TFA |
| 粒度 | aggregate | aggregate | aggregate | aggregate regulation + sample-level TFA |
| 正負能否直接叫 activation/repression | 不能 | 不能 | 不能在 current contract 中如此宣稱 | 依 GIRAFFE paper 的 signed effect 語意，但仍要遵守 model context |
| 何時選 | 需要整合 TF prior/PPI/coexpression 的 cohort GRN evidence | 明確要加入 miRNA regulator layer | 要明確控制 PPI vs coexpression projection weight | 要同時取得 signed regulation 與 TFA |
| 目前 agent handoff | 合格 edge list → CONDOR；COBRA C 可用 | 合格 edge list → CONDOR；COBRA C 可用 | 合格 edge list → CONDOR；COBRA C 可用 | 無 direct handoff，轉換需確認 |

選擇原則：如果研究問題是「證據一致的 TF-gene network」，先考慮 PANDA；若要把 miRNA 放入同一 regulator layer，考慮 PUMA；若要把兩側 projection 明確寫進 optimization，考慮 OTTER；若要把「regulatory effect 的方向」與 sample-level TFA 一起建模，考慮 GIRAFFE。

### 10.2 LIONESS-coexpression vs BONOBO

見第 7.6 節。最重要的差別是：LIONESS 用 leave-one-out linear interpolation；BONOBO 用 Bayesian posterior／shrinkage。兩者都不應被不加驗證地稱為 causal network。

### 10.3 COBRA vs DRAGON vs 一般 coexpression

見第 8.3 節。最重要的差別是：COBRA 的核心是 covariate-associated covariance decomposition；DRAGON 的核心是 two-layer precision／partial correlation；一般 coexpression 只是描述一起變動，不自動含 batch adjustment 或 conditional association。

### 10.4 CONDOR vs SAMBAR

見第 9.3 節。最重要的差別是：CONDOR 以 existing bipartite network 的兩側 topology 找 communities；SAMBAR 以 mutation→pathway 的 patient profiles 做 subtyping。

### 你現在應該能回答

1. PANDA、PUMA、OTTER、GIRAFFE 的 edge semantics 哪些可以互相比較，哪些不能直接互換？
2. LIONESS-coexpression 與 BONOBO 的 sample-specific estimator 有何根本差異？
3. COBRA、DRAGON、一般 coexpression 的輸入與輸出為何不相同？
4. CONDOR 與 SAMBAR 各自在分哪一種群組？

<a id="relationship-maps"></a>
## 11. 科學關係圖與目前 agent handoff 圖

### 11.1 依生物問題分類

~~~mermaid
flowchart TD
    Q[研究問題]
    Q --> R[TF-gene / miRNA regulation]
    Q --> S[sample-specific network]
    Q --> M[multi-omics conditional association]
    Q --> U[mutation subtyping]
    Q --> C[community analysis]

    R --> P[PANDA]
    R --> PM[PUMA]
    R --> O[OTTER]
    R --> G[GIRAFFE: regulation + TFA]

    S --> LP[LIONESS-PANDA]
    S --> LPM[LIONESS-PUMA]
    S --> LC[LIONESS-coexpression]
    S --> B[BONOBO]

    M --> D[DRAGON]
    M --> CB[COBRA: covariate-aware coexpression]
    U --> SA[SAMBAR]
    C --> CO[CONDOR]
~~~

### 11.2 資料與 artifact flow

~~~mermaid
flowchart LR
    E[gene × sample expression]
    F[TF-gene motif / prior]
    PPI[TF-TF PPI]
    MI[miRNA-target prior / miRNA list]
    D[design matrix: batch / hospital / treatment]
    MUT[samples × genes somatic mutation]
    ANN[gene length + cancer genes + GMT]
    X1[omics layer 1]
    X2[omics layer 2]

    E --> PA[PANDA aggregate TF→gene]
    F --> PA
    PPI --> PA
    E --> PU[PUMA aggregate TF/miRNA→gene]
    F --> PU
    PPI --> PU
    MI --> PU

    E --> LL[LIONESS constructions]
    F --> LL
    PPI --> LL
    MI --> LL
    LL --> SS[sample-specific regulatory / coexpression artifacts]

    E --> CB[COBRA covariance components]
    D --> CB
    CB --> AC[labeled adjusted coexpression]

    E --> GI[GIRAFFE]
    F --> GI
    PPI --> GI
    GI --> GR[aggregate regulation]
    GI --> TFA[TF-by-sample TFA]

    E --> BO[BONOBO]
    BO --> BC[one coexpression matrix per sample]

    MUT --> SA[SAMBAR]
    ANN --> SA
    SA --> PS[pathway mutation scores]
    PS --> CL[optional sample clusters]

    X1 --> DR[DRAGON]
    X2 --> DR
    DR --> MC[aggregate two-layer partial-correlation network]

    F --> OT[OTTER W]
    PPI --> OT
    AC --> OT
    E --> OT
    OT --> OW[aggregate TF→gene W]

    PA --> EL[validated source-target-weight edge list]
    PU --> EL
    OW --> EL
    EL --> CO[CONDOR memberships]
~~~

### 11.3 目前 agent handoff

~~~mermaid
flowchart LR
    CB[COBRA adjusted coexpression]
    PA[PANDA validated edge list]
    PU[PUMA validated edge list]
    OT[OTTER validated edge list]
    CO[CONDOR]
    P[PANDA]
    PM[PUMA]
    O[OTTER]
    LP[LIONESS-PANDA]
    LPM[LIONESS-PUMA]
    BON[BONOBO sample-specific C]
    GI[GIRAFFE]
    DR[DRAGON]
    SA[SAMBAR]

    CB -->|實線：coexpression_file + exact revalidation| P
    CB -->|實線：coexpression_file + exact revalidation| PM
    CB -->|實線：C + exact revalidation| O

    PA -->|實線：source-target-weight| CO
    PU -->|實線：source-target-weight| CO
    OT -->|實線：source-target-weight| CO

    P -.->|guidance predecessor；不是 file handoff| LP
    PM -.->|guidance predecessor；不是 file handoff| LPM
    BON -.->|概念可支援個體化 GRN；須選樣本／aggregation／conversion／確認| P
    GI -.->|轉 matrix→edge list、驗證與 user confirmation| CO

    BON -.->|禁止：多張 sample-specific matrix 不是單一 aggregate C| PM
    DR -.->|禁止：undirected multi-omic artifact 不合 TF-gene bipartite contract| CO
    DR -.->|禁止：不是 PANDA/PUMA/OTTER coexpression/prior| P
    SA -.->|禁止：mutation/pathway score 不是 expression network| P
    GI -.->|目前無 direct registry handoff| P
~~~

**圖例：** 實線是目前已聲明且需驗證的 direct handoff；虛線是概念組合或 guidance relation；標註「禁止」的箭頭表示目前不能直接串接。這張圖不是一條萬能流水線。

### 你現在應該能回答

1. COBRA adjusted coexpression 哪三個 workflow 可以接收？
2. 為什麼 PANDA→LIONESS-PANDA 在圖上是 guidance relation 而不是 file handoff？
3. 哪些箭頭看似合理，但因 artifact contract 不相容而被標成禁止？

## 12. 同一個癌症 cohort 的多分支案例

以下是**虛構教學案例**，不代表真實資料或 benchmark。

### 12.1 Cohort 設定

假設有 24 位腫瘤病人 P01–P24，來自兩家醫院、兩個 sequencing batch、兩種 treatment。每個 sample 有：

- bulk gene expression：gene × sample。
- motif prior：TF-gene。
- TF-TF PPI。
- miRNA-target prior 與 miRNA list。
- metadata：hospital、batch、treatment、age、sex、tumor purity。
- somatic mutation matrix：sample × gene。
- matched methylation layer：sample × CpG／gene-linked feature。

### 12.2 研究問題與分支

| 分支 | workflow | 得到的 evidence | 下一個合理分析 | 外部／實驗驗證 | 不能直接下的結論 |
|---|---|---|---|---|---|
| A | PANDA | cohort-level TF→gene integrated evidence | 比較 treatment 或 subtype 的 network topology；合格 edge list 才可 CONDOR | ChIP-seq、ATAC-seq、TF perturbation、independent cohort | 不是 binding probability，也不是 causal disease mechanism |
| B | PUMA | TF/miRNA→gene integrated evidence | 對 miRNA/TF target set 做 enrichment，或比較 treatment-specific input | CLIP-seq、miRNA perturbation、qPCR／protein measurement | 不是每個 negative score 都是 inhibition |
| C | OTTER | projection-consistent aggregate TF→gene W | 與 PANDA 比較一致 edge；轉 edge list 後可 CONDOR | ChIP／perturbation／orthogonal PPI | W score 不是 probability；不是 sample-specific |
| D | GIRAFFE | aggregate signed regulation + sample-level TFA | 用 TFA 與 treatment/phenotype 做統計模型 | TF knockout／overexpression、reporter assay | TFA 不是 TF mRNA；目前不是每 sample 一張 GRN |
| E | LIONESS-PANDA/PUMA | 個別病人的 regulatory network contribution | 比較 sample-specific edge、treatment interaction、network rewiring | independent cohort、single-cell／spatial、perturbation | leave-one-out contribution 不是直接 binding observation |
| F | LIONESS-coexpression | 個別病人的 Pearson coexpression contribution | 與 phenotype 做 association；檢查 outlier／batch sensitivity | external cohort、protein／functional assay | gene-gene coexpression 不是 TF causal direction |
| G | BONOBO | Bayesian sample-specific coexpression + optional p-values | 先固定 sample selection 或 aggregation rule，再做個體化分析 | independent cohort、protein interaction、functional assay | 多張 output 不能直接當 aggregate PANDA/PUMA C |
| H | COBRA | covariate-associated components + adjusted gene-gene coexpression | exact revalidation 後作 PANDA/PUMA/OTTER coexpression_file | held-out batch、replicate、technical controls | 無法從完全 confounded design 分離 batch 與 phenotype |
| I | DRAGON | methylation／expression two-layer conditional associations | 檢查 layer-specific stability、與 phenotype 做 multiple-testing corrected association | longitudinal data、methylation perturbation、independent cohort | partial correlation 不是 causal methylation→expression |
| J | SAMBAR | gene/pathway mutation scores + sample clusters | 與 treatment、survival、expression subtype 做獨立統計比較 | external cohort、clinical endpoints、functional pathway test | cluster 不是自動驗證的 clinical subtype，score 不是 driver |
| K | CONDOR | 合格 regulatory edge list 的 regulator／target modules | pathway enrichment、module preservation、cross-cohort replication | ChIP／CRISPR、known pathway databases、replication | community 不自動等於 pathway 或 master regulator |

### 12.3 案例中的合法分析分支

~~~text
expression + batch/hospital design
        └─ COBRA ──(adjusted coexpression，重新驗證)──→ PANDA / PUMA / OTTER

expression + motif + PPI
        ├─ PANDA ──(validated edge list)──→ CONDOR
        ├─ PUMA  ──(validated edge list)──→ CONDOR
        ├─ OTTER ──(validated edge list)──→ CONDOR
        └─ GIRAFFE ──→ regulation + TFA（目前獨立 branch）

expression + same priors
        ├─ LIONESS-PANDA
        ├─ LIONESS-PUMA
        ├─ LIONESS-coexpression
        └─ BONOBO

expression + matched methylation
        └─ DRAGON ──→ two-layer aggregate association

mutation + gene lengths + cancer genes + pathways
        └─ SAMBAR ──→ pathway mutation scores + sample clusters
~~~

### 12.4 這個案例的最低分析紀錄

每一分支至少記錄：input checksum、ID namespace、row／column orientation、normalization／log／center declarations、batch/design formula、method version、parameters、random seed（若有）、output format、artifact validation report、下一步的 statistical test、multiple-testing strategy 與 external validation plan。

### 你現在應該能回答

1. 同一 cohort 為什麼要拆成 regulatory、sample-specific、covariate、multi-omic、mutation 等互補分支？
2. 哪些 branch output 可以進下一個 registered workflow，哪些只能作為 phenotype 或外部 evidence？
3. 每一分支至少要保留哪些 provenance 與 validation record？

## 13. 工具選擇決策樹

~~~mermaid
flowchart TD
    S[你最想回答什麼？]
    S --> TF{TF-gene regulation?}
    TF -->|只要 TF regulatory evidence| PAN[PANDA]
    TF -->|要把 miRNA 也放進 regulator layer| PUM[PUMA]
    TF -->|要明確 matching PPI/C projections| OTT[OTTER]
    TF -->|要 signed effects + TF activity| GIR[GIRAFFE]

    S --> SS{要 sample-specific network?}
    SS -->|TF-gene| LP[LIONESS-PANDA]
    SS -->|TF/miRNA-gene| LPM[LIONESS-PUMA]
    SS -->|gene-gene coexpression，linear leave-one-out| LC[LIONESS-coexpression]
    SS -->|gene-gene coexpression，Bayesian posterior| BON[BONOBO]

    S --> MM{要 multi-omic conditional association?}
    MM -->|正好兩個 matched continuous layers| DR[DRAGON]
    MM -->|要調 batch/covariate 對 gene covariance 的影響| COB[COBRA]

    S --> MU{要 mutation-based subtype?}
    MU --> SAM[SAMBAR]

    S --> EC{已有合格 bipartite network，要找 communities?}
    EC --> CON[CONDOR]

    S --> NO[以上都不是]
    NO --> N[目前這 12 個 workflows 都不適合；先定義 artifact 與研究問題]
~~~

### 13.1 快速選擇規則

- 「我想要 TF-gene regulation」不是單一答案：看你要 evidence、miRNA、projection optimization，還是 signed effect + TFA。
- 「我想要個體差異」若是 gene-gene coexpression，再選 LIONESS-coexpression 或 BONOBO；若是 regulatory network，選 LIONESS-PANDA/PUMA。
- 「我有 batch」不代表直接選 DRAGON；若問題是單一 expression layer 的 covariate effect，先看 COBRA。
- 「我有一張 network 想找 modules」才選 CONDOR；若手上是 mutation matrix，選 SAMBAR。
- 「我有三個 omics layers」current DRAGON contract 不會自動接受三層；需做已驗證的 pairwise design 或承認目前不適合。

### 你現在應該能回答

1. 想要 TF activity 時，為什麼終點是 GIRAFFE 而不是任意 TF-gene network？
2. 想找 existing network modules 與想做 mutation subtype 時，為什麼分別選 CONDOR 與 SAMBAR？
3. 什麼情況下決策樹應該回答「目前這 12 個 workflows 都不適合」？

## 14. Input／ID／orientation／normalization 檢查

### 14.1 通用檢查清單

在任何 run 前先回答：

- ID 是 gene symbol、Ensembl、TF symbol、miRNA accession，還是混用？
- row 是 gene 還是 sample？column 是 sample 還是 feature？
- 第一欄是 label 還是第一個 numeric observation？
- 數值是否 numeric、finite、complete？是否需要 log transform、center 或 normal transform？
- sample IDs 是否與 design／第二 omics layer 完全相同？
- edge 是否 directed、undirected、bipartite？weight 的語意是什麼？
- output 是否會覆寫 input，或把 aggregate 與 sample-specific 檔案混在同一路徑？
- current agent 是否真的聲明這個 artifact 可以 handoff？

### 14.2 重要 workflow 的方向表

| Workflow | 主要 orientation | 常見錯誤 |
|---|---|---|
| PANDA/PUMA/LIONESS regulatory | expression gene × sample；prior regulator × gene；PPI TF × TF | 把 expression sample × gene 餵給 legacy wrapper；把 PPI 當 motif |
| LIONESS-coexpression | gene × sample；輸出 gene × gene | 把單一 sample vector 當可獨立估計 correlation matrix |
| COBRA | expression gene × sample；design sample × covariate | design rows 依位置而非 sample ID 對齊；category 未 numeric encode |
| GIRAFFE | expression gene × sample；prior TF × gene；PPI TF × TF | 把 output TF × gene 與概念上的 gene × TF R 混為一談 |
| BONOBO | labeled gene × sample | 未宣告 log-centered；sample_names 用 index；忘記 manifest gene order |
| SAMBAR | mutation sample × gene；exon-size 一列且 genes 作 columns；GMT gene set | mutation 軸向反了；四方 gene overlap 為空 |
| DRAGON | 每層 sample × feature；第一欄 sample ID | 用 gene × sample expression；兩層 sample set 不一致 |
| OTTER | W TF × gene；P TF × TF；C gene × gene | W/P/C implicit intersection；把 gamma 當 threshold |
| CONDOR | edge list source × target × weight，兩側分離 | 直接餵 matrix、coexpression 或 overlapping IDs |

### 14.3 Repository 中已核對的 toy／示例資料

| 目的 | 已核對路徑 |
|---|---|
| PANDA/PUMA 官方 toy | data/official-toy/ToyExpressionData.txt、ToyMotifData.txt、ToyPPIData.txt、ToyMiRList.txt |
| LIONESS | data/lioness-toy/expression.tsv、motif-panda.tsv、prior-puma.tsv、ppi.tsv、mirna.txt |
| COBRA | data/cobra-toy/expression.tsv、design.tsv |
| CONDOR | data/condor-toy/bipartite.tsv、data/teacher-demo/condor-bipartite.tsv |
| GIRAFFE | data/giraffe-toy/expression.tsv、motif.tsv、ppi.tsv |
| BONOBO | data/bonobo-toy/expression.tsv |
| SAMBAR | data/sambar-toy/mutation.csv、exon_size.csv、cancer_genes.txt、pathways.gmt |
| DRAGON | data/dragon-toy/layer1.tsv、layer2.tsv |
| OTTER | data/otter-toy/expression.tsv、motif.tsv、ppi.tsv |

所有 toy data 都只證明格式、ID、orientation 或 software path 可跑；不能支持真實生物機制、臨床 subtype 或 causal claim。

### 你現在應該能回答

1. 在 run 前，為什麼要先確認 ID namespace、orientation 與 output collision？
2. 哪兩個 toy data 特別示範 sample ID reorder，而不是位置對齊？
3. 哪些資料清理可以由 agent contract 驗證，哪些 normalization／biological decision 仍要由研究者定義？

<a id="evidence-ladder"></a>
## 15. 結果解讀、失敗模式與證據階梯

### 15.1 六層證據階梯

~~~text
1. Input / identifier / orientation / normalization 正確
        ↓
2. 模型 output 與 artifact verification 通過
        ↓
3. prior、parameter、random seed、resampling 穩定
        ↓
4. 與 phenotype 有適當統計關聯，並處理 multiple testing
        ↓
5. 外部 cohort 或 orthogonal data 支持
        ↓
6. Perturbation / functional experiment 支持
~~~

每往上一層，claim 的可信度增加；第 1–2 層不能代替第 5–6 層。

### 15.2 共通反誤讀規則

- higher score 不等於 probability。
- network edge 通常是 model evidence 或 association，不等於 causation。
- signed edge 的語意依方法而異；GIRAFFE 的 signed partial regulatory effect 不能套到 PANDA/PUMA/OTTER。
- community、pathway score、cluster、subtype、driver 是不同層級的概念。
- sample-specific 不等於直接觀測到該 sample 的完整 molecular network。
- partial correlation 的「控制其他變數」不等於實驗控制。
- toy data 跑通只證明軟體與格式，不證明生物機制。
- 把 batch 與 phenotype 完全 confounded 後，不能宣稱 algorithm 已將兩者分開。

### 15.3 常見失敗模式與補救

| 失敗 | 可能原因 | 安全補救 |
|---|---|---|
| 大量 ID missing | alias、species、版本或 symbol namespace 不同 | 先建立明確 ID mapping，保存 mapping table 與丟失比例；不要默默取 intersection |
| network 稀疏到沒有訊號 | 樣本太少、prior 過窄、missingness 或 variance 問題 | 檢查 sample size、prior coverage、variance、normalization；做 sensitivity analysis |
| edge sign 不穩 | 方法的 sign 不具 activation semantics，或模型受 prior／noise 影響 | 先看方法 contract；用 perturbation／orthogonal assay 驗證 |
| aggregate 與 sample-specific 混用 | output path、manifest 或 sample selection 不清楚 | 分開命名、保存 sample IDs；BONOBO 先選 sample／aggregation 再轉換 |
| COBRA handoff 失敗 | 傳入 raw components 或 gene order 不符 | 使用 adjusted_coexpression.tsv/.npz，再跑下游 validator |
| CONDOR input 失敗 | source/target overlap、缺 weight、把 matrix 直接傳入 | 產生 source-target-weight，確認 bipartite partitions |
| DRAGON 結果難解讀 | layer ID 未加 prefix、sample unmatched、資料非 continuous | 保留 layer1::／layer2::，先 exact-align，必要時預先 transformation |
| SAMBAR cluster 不穩 | pathway DB、normalization、distance/linkage 或 k 改變 | 做 parameter／annotation sensitivity、external cohort validation |

### 你現在應該能回答

1. 六層證據階梯中，artifact verification 與 functional experiment 各自處於哪一層？
2. 為什麼 higher score、community、cluster、partial correlation 都不能自動變成 causal claim？
3. 完全 confounded 的 batch 與 phenotype 為什麼不能靠 COBRA 分開？

<a id="practice-and-records"></a>
## 16. Repository toy data 練習

以下練習以 repository 已核對的檔案為準；不需要修改任何程式碼。

### 練習 1：先辨認 artifact

將下列物件分類為「expression matrix、regulatory edge、coexpression matrix、mutation matrix、community assignment、multi-omic network」：

1. data/official-toy/ToyMotifData.txt
2. data/cobra-toy/design.tsv
3. data/dragon-toy/layer1.tsv
4. data/sambar-toy/pathways.gmt
5. data/condor-toy/bipartite.tsv

參考答案：1 是 regulatory prior edge；2 是 design matrix；3 是 sample-by-feature omics layer；4 是 pathway annotation；5 是 existing bipartite edge list。

### 練習 2：手算 LIONESS 一條 edge

若 n=4、N_all=0.40、N_without_k=0.30，計算 N_k：

~~~text
N_k = 4×0.40 − 3×0.30 = 0.70
~~~

這個 0.70 是 model-specific network estimate，不是 probability。

### 練習 3：辨識合法 handoff

判斷下列動作是否 current agent direct handoff：

| 動作 | 判斷 |
|---|---|
| COBRA/components.npz → PANDA coexpression_file | 禁止；raw components 不是 matrix input |
| COBRA/adjusted_coexpression.tsv，通過 exact ID/order/symmetry validation → OTTER | 可以；registry 已聲明 |
| BONOBO 的 24 張 sample matrices 全部直接交給 PUMA | 禁止；先定義 sample selection 或 aggregation，另行確認 |
| OTTER validated source-target-weight edge list → CONDOR | 可以 |
| DRAGON edge list → CONDOR | 禁止；undirected multi-omic schema 不等於 bipartite regulatory edge |

### 練習 4：用 toy input 找 orientation

- data/dragon-toy/layer2.tsv 的 sample 順序與 layer1 不同，但 sample IDs 相同；所以 adapter 可安全 reorder layer2。
- data/cobra-toy/design.tsv 的 sample 順序也與 expression 不同；COBRA 依 IDs 對齊。
- data/sambar-toy/exon_size.csv 是一列、gene IDs 作 columns；這是 current pinned SAMBAR implementation 的契約。

### 練習 5：寫一個不過度宣稱的句子

將「DRAGON 發現 methylation 造成 G1 表達下降」改成：

> 「在兩層 matched continuous data、指定 shrinkage 與 GGM 假設下，methylation feature 與 G1 expression feature 呈現 partial-correlation association；方向與因果仍需 longitudinal、perturbation 或 orthogonal evidence。」

## 17. 自我測驗與參考答案

### 題目

1. 這個 repository 有幾個 registered workflows？幾個主要方法家族？
2. 為什麼 LIONESS-PANDA 不等於一個獨立 upstream package？
3. PANDA 的三種主要 network evidence 是什麼？
4. PUMA 比 PANDA 多了哪一類 regulator？
5. 哪個 workflow 直接輸出 TF-by-sample TFA？
6. 哪個 workflow 要求正好兩個 matched sample-by-feature continuous omics layers？
7. COBRA 哪一個 output 可以給 PANDA/PUMA/OTTER 的 coexpression_file？
8. 為什麼 COBRA raw components 不能直接給 PANDA？
9. LIONESS 公式中的 N_without_k 是什麼？
10. BONOBO 與 LIONESS-coexpression 的核心 estimator 差別是什麼？
11. CONDOR 的 input 為什麼必須是 bipartite edge list？
12. SAMBAR 的 cluster 是否自動等於臨床 subtype？
13. DRAGON 的 partial correlation 是否 causal effect？
14. OTTER 的 W、P、C 分別代表什麼？
15. 哪三類 output 目前是獨立 branch、沒有 direct handoff？
16. 如果某 batch 完全對應某 phenotype，COBRA 是否能靠演算法魔法分離兩者？
17. GIRAFFE 的 signed edge semantics 能否套到 PANDA？
18. toy data 跑通最少能支持什麼？

### 參考答案

1. 12 個 workflows、10 個方法家族。
2. LIONESS 是 estimator-agnostic sample-specific framework；PANDA 是它在 leave-one-out construction 中使用的 base estimator。
3. TF-gene motif/prior、TF-TF PPI、gene-gene coexpression。
4. miRNA；PUMA 的 regulator layer 是 TF + miRNA。
5. GIRAFFE。
6. DRAGON。
7. labeled adjusted_coexpression.tsv 或對應 validated artifact；不是 components.npz。
8. raw components 不是 labeled、square、gene-by-gene coexpression matrix。
9. 拿掉 sample k 後重新估計的 network。
10. LIONESS 是 leave-one-out linear interpolation；BONOBO 是 Bayesian posterior／shrinkage。
11. 因為它要分別維持 source/regulator side 與 target/gene side 的 community assignment。
12. 不是；它是 computational grouping，需要 clinical／external validation。
13. 不是；它是控制模型中其他 variables 後的 association estimate。
14. W 是 TF×gene seed／unknown regulatory matrix，P 是 TF×TF PPI projection，C 是 gene×gene coexpression projection。
15. GIRAFFE、DRAGON、SAMBAR；BONOBO 也沒有 direct handoff，需明確 conversion／aggregation。
16. 不能；完全 confounded 時沒有資訊辨識兩者。
17. 不能；GIRAFFE 的 signed partial regulatory effect 是該方法自己的 semantics。
18. 軟體、檔案格式、ID／orientation 與 artifact validator 可按預期工作；不支持真實生物機制或臨床結論。

## 18. 研究紀錄模板

複製以下模板到每次分析的紀錄中，並把「未驗證」保留為未驗證，不要用推測填空。

~~~markdown
# [日期] [workflow] 分析紀錄

## 研究問題
- 生物問題：
- 預先定義的主要 endpoint：
- 不要宣稱的內容：

## Repository 與 runtime
- repository commit：
- workflow YAML：
- registry action：
- netZooPy version / pinned revision：
- runtime（host / Docker）：

## Inputs
- expression / omics / mutation path：
- prior / motif / PPI / miRNA / pathway path：
- design / metadata path：
- ID namespace：
- row orientation：
- column orientation：
- sample count / feature count：
- missing / non-finite / duplicate checks：
- normalization / log transform / centering：
- batch / covariate / confounding assessment：

## Parameters
- method parameters：
- random seed：
- resampling plan：
- output format：

## Artifact verification
- output files：
- shape／symmetry／direction／partition check：
- manifest／checksum：
- direct handoff target（若有）：
- conversion performed（若有）：
- user confirmation（若 required）：

## 結果
- 主要 model evidence：
- uncertainty／stability：
- multiple-testing method：
- phenotype association：
- external／orthogonal evidence：

## 下一步與限制
- 下一個合理分析：
- 可做的實驗驗證：
- 尚未驗證的能力：
- 不可下的 causal／clinical claim：
~~~

## 19. Glossary

| 縮寫／名詞 | 全名或定義 |
|---|---|
| PANDA | Passing Attributes between Networks for Data Assimilation |
| PUMA | PANDA Using MicroRNA Associations |
| LIONESS | Linear Interpolation to Obtain Network Estimates for Single Samples |
| CONDOR | COmplex Network Description Of Regulators |
| COBRA | Co-expression Batch Reduction Adjustment |
| GIRAFFE | 本文以最新原始論文的 GIRAFFE 方法名使用；核心是 biologically informed matrix factorization |
| BONOBO | Bayesian Optimized Networks Obtained By assimilating Omics data |
| SAMBAR | Subtyping Agglomerated Mutations By Annotation Relations |
| DRAGON | Determining Regulatory Associations using Graphical models on multi-Omic Networks |
| OTTER | Optimize To Estimate Regulation；官方文件也常以 Optimization To Estimate Regulation 描述 |
| TF | transcription factor；轉錄因子 |
| TFA | transcription factor activity；轉錄因子活性，不等於 TF expression |
| PPI | protein-protein interaction |
| GRN | gene regulatory network |
| prior | 分析前提供的候選關係或背景資訊 |
| coexpression | gene-gene 一起變動的統計描述；需明確 estimator |
| covariance | 兩變數共同偏離平均值的尺度化前量 |
| correlation | 正規化後的 covariance |
| partial correlation | 控制其他 variables 後的條件關聯 |
| precision matrix | covariance matrix 的 inverse |
| GGM | Gaussian graphical model |
| shrinkage | 對高維不穩定估計施加穩定化的收縮 |
| message passing | 多張 network 間反覆傳遞資訊以更新一致性 |
| matrix factorization | 將觀測矩陣拆成較小矩陣乘積 |
| graph matching | 令不同 graph 或其 projection 互相吻合的 optimization view |
| community | network topology 上的群組，不自動等於 pathway |
| pathway score | 將 gene-level mutation 等資訊聚合到 pathway 的數值 |
| subtype | 由特定資料與 clustering 定義的群組；不自動等於臨床分類 |
| driver | 需要額外功能／因果證據支持的生物學角色，不是任一高分節點的同義詞 |
| aggregate | 代表 cohort／condition 的單一產物 |
| condition-specific | 特定 tissue、treatment、subtype 等條件的產物 |
| sample-specific | 每個 sample 各自估計的產物 |
| artifact contract | 輸入／輸出檔案的 shape、ID、orientation、欄位與語意契約 |
| handoff | 把已驗證、語意相容的 artifact 交給下一個 workflow |

<a id="sources-and-changelog"></a>
## 20. 官方來源與維護紀錄

### 20.1 官方與原始來源

以下連結是本筆記撰寫時核對的最低來源集合。論文頁面提供方法的科學背景；repository 的 YAML、registry 與 integration docs 才決定本 agent 的現行輸入／輸出與 handoff。

- [netZooPy GitHub repository](https://github.com/netZoo/netZooPy)
- [netZooPy stable documentation](https://netzoopy.readthedocs.io/en/stable/)
- [PANDA: Passing Attributes between Networks for Data Assimilation](https://pmc.ncbi.nlm.nih.gov/articles/PMC3669401/)
- [PUMA: PANDA Using MicroRNA Associations](https://pmc.ncbi.nlm.nih.gov/articles/PMC7750953/)
- [LIONESS: Linear Interpolation to Obtain Network Estimates for Single Samples](https://pmc.ncbi.nlm.nih.gov/articles/PMC6815019/)
- [CONDOR／bipartite community detection](https://pmc.ncbi.nlm.nih.gov/articles/PMC8099108/)
- [COBRA: Co-expression Batch Reduction Adjustment](https://pmc.ncbi.nlm.nih.gov/articles/PMC11441315/)
- [BONOBO: Bayesian sample-specific coexpression](https://pmc.ncbi.nlm.nih.gov/articles/PMC10680741/)
- [SAMBAR: Subtyping Agglomerated Mutations By Annotation Relations](https://pmc.ncbi.nlm.nih.gov/articles/PMC5988673/)
- [DRAGON: multi-omic Gaussian graphical models](https://pmc.ncbi.nlm.nih.gov/articles/PMC9943674/)
- [OTTER: Gene regulatory network inference as relaxed graph matching](https://pmc.ncbi.nlm.nih.gov/articles/PMC8546743/)
- [GIRAFFE: Large-scale, interpretable gene regulatory network inference through biologically informed matrix factorization](https://pubmed.ncbi.nlm.nih.gov/42523370/)
- [The Network Zoo: a multilingual package for inference and analysis of gene regulatory networks](https://pmc.ncbi.nlm.nih.gov/articles/PMC9999668/)

### 20.2 Repository 查證索引

本次撰寫查閱並以其作為 [agent] 證據的檔案包括：

- scripts/workflow_registry.py
- workflows/panda.yaml
- workflows/puma.yaml
- workflows/lioness-panda.yaml
- workflows/lioness-puma.yaml
- workflows/lioness-coexpression.yaml
- workflows/condor.yaml
- workflows/cobra.yaml
- workflows/giraffe.yaml
- workflows/bonobo.yaml
- workflows/sambar.yaml
- workflows/dragon.yaml
- workflows/otter.yaml
- docs/BONOBO_INTEGRATION.md
- docs/DRAGON_INTEGRATION.md
- docs/GIRAFFE_INTEGRATION.md
- docs/OTTER_INTEGRATION.md
- scripts/netzoo_agent_core/execution.py
- scripts/netzoo_agent_core/execution_bonobo.py
- scripts/netzoo_agent_core/data/cobra.py
- scripts/netzoo_agent_core/data/sambar.py
- scripts/netzoo_agent_core/data/dragon.py
- scripts/netzoo_agent_core/data/giraffe.py
- scripts/netzoo_agent_core/data/otter.py
- scripts/netzoo_agent_core/data/bonobo.py
- scripts/netzoo_agent_core/data/artifacts.py
- scripts/run_cobra.py
- scripts/run_sambar.py
- docker/run-condor
- 相關 workflow tests 與 data/*-toy/ fixtures

### 20.3 尚存在的不確定性

1. 上游 netZooPy GitHub master 是 moving branch；本筆記對 agent runtime 以 repository 文件記載的 pinned 0.11.0／revision 為準，不把 moving branch 的新能力冒充 current agent capability。
2. GIRAFFE 的最新原始論文描述 signed partial regulatory effects；current agent 已驗證的是 pinned Docker API、輸入轉換與兩個 output artifact，尚未因為論文 benchmark 就宣稱本 agent 對任一真實 cohort 有同等表現。
3. 上游 netZooPy 有 LIONESS-OTTER 相關能力，但 current registry 只有 aggregate run_otter；本文不把它寫成已支援 workflow。
4. BONOBO sample-specific matrices 在科學上可能支援後續個體化 GRN 研究，但 current agent 沒有一條不需明確 aggregation／conversion／validation／confirmation 的 direct handoff。
5. 未在 repository contract 中聲明的 conversion、third-layer DRAGON chaining、GIRAFFE→CONDOR 或 sample-wise COBRA→LIONESS，都應視為待設計能力，而不是現成能力。

### 20.4 Changelog

| 日期 | 變更 |
|---|---|
| 2026-08-29 | 新增本筆記：建立 12 workflows／10 方法家族分類、共同生物主線、全景表、固定 workflow 教學模板、四組深度比較、三張 Mermaid 圖、虛構癌症 cohort、多分支 handoff、決策樹、輸入檢查、六層證據階梯、toy data 練習、自我測驗、研究紀錄模板、glossary 與官方來源。 |

> 維護原則：每次 registry、workflow YAML、pinned netZooPy version、integration doc 或 artifact validator 改動，都要同步重新核對本文的「目前 agent 邊界」、output paths、handoff 圖與 changelog 日期。
