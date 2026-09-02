# netZooPy 12 workflows：AI Agent 工程師速讀版

> 給主要負責 AI agent、資料契約、workflow orchestration 與錯誤排查的工程師。  
> 目標不是把你訓練成生物學家，而是讓你看到一個 workflow 時，能回答：它在估計什麼、需要什麼資料、輸出能不能交給下一步，以及結果不能被過度解讀到哪裡。

| 項目 | 內容 |
|---|---|
| 適合讀者 | 建立、維護或除錯 netZoo agent 的工程師 |
| 建議讀法 | 先讀第 1–4 節；遇到特定 workflow 再查第 5 節 |
| 完整參考 | [NETZOOPY_生物知識串聯筆記.md](NETZOOPY_生物知識串聯筆記.md) |
| Repository | /Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent |
| 本版核對日期 | 2026-09-02 |
| 本版定位 | 工程 onboarding／debugging 速查，不取代完整科學筆記或原始論文 |

## 1. 先記住這張圖

~~~
生物資料
  ↓
欄位／ID／shape／sample 對齊驗證
  ↓
workflow estimator
  ↓
具有明確語意的 artifact
  ↓
interpretation 或下一個 workflow
~~~

工程師最需要守住的不是每個公式，而是中間的「語意邊界」：

1. **資料形狀**：gene × sample、sample × feature、TF × gene、source × target 是否正確。
2. **node 語意**：這個 node 是 gene、TF、miRNA、pathway 還是 multi-omic feature。
3. **edge 語意**：這是 regulatory evidence、coexpression、partial correlation，還是 community membership。
4. **粒度**：aggregate、condition-specific、sample-specific 或根本不是 network。
5. **解讀範圍**：模型分數通常是 evidence／association，不自動等於 probability、activity 或 causality。
6. **handoff 契約**：上一個 workflow 的輸出必須符合下一個 workflow 的欄位、方向、ID 與數值要求。

### 讀完本節，你應該能回答

- 為什麼「都是 network」不代表檔案可以互相餵？
- 為什麼 workflow 成功執行，不代表生物學結論一定正確？
- agent 工程師為什麼要同時看科學語意與 artifact contract？

## 2. 最少需要懂的生物與統計詞彙

| 名詞 | 工程師版白話 | 看到它時要注意 |
|---|---|---|
| gene | 被觀測或被調控的基因單位 | 常出現在 expression、coexpression、mutation 與 pathway |
| sample／patient | 一個病人、組織或實驗條件 | 是 sample axis；LIONESS、BONOBO、SAMBAR、DRAGON 都很重視對齊 |
| TF | 可能調節其他 gene 的轉錄因子 | 常是 regulatory network 的 source／regulator |
| miRNA | 可能影響 target mRNA 的小 RNA | PUMA 的 regulator 之一；不能把它的 edge 直接當作抑制百分比 |
| expression | gene 在各 sample 的 mRNA abundance | 通常是 gene × sample；不是 TF activity |
| motif／prior | 「可能有這條調控線」的先驗或起點 | 不是 cohort 已證實的 binding，也不是機率 |
| PPI | 蛋白質之間可能互動的資料 | 常提供 TF-TF 的 network evidence；不是 TF 對 gene 的結果 |
| coexpression | 兩個 gene 是否在 samples 間一起變動 | 是 gene-gene association，不是 TF→gene regulation |
| regulatory network | regulator→target 的關係圖 | edge score 仍通常是模型證據，不自動是因果 |
| TFA | TF activity，TF 實際調控作用的估計 | 不要用 TF expression 直接代替 |
| pathway | 一組具有共同 annotation 或功能的 gene | pathway score 或 membership 不自動證明機制 |
| community | 網路中較密集的一群 node | CONDOR 的 community 不等於 pathway |
| covariance／correlation | 變數一起變動的程度 | 需要確認 estimator；Pearson、Bayesian posterior、adjusted covariance 不同 |
| partial correlation | 控制其他變數後的關聯 | DRAGON 的主要 edge 語意；仍然是 association，不是因果 |

### 2.1 四個最容易搞混的差別

~~~
TF expression  ≠  TF activity
coexpression   ≠  TF-gene regulation
community      ≠  pathway
association    ≠  causality
~~~

PANDA／PUMA／OTTER 的分數通常要叫做 edge score 或 regulatory evidence。除非文件明確定義，不要把它寫成機率、binding probability 或 activation strength。

## 3. 12 個 workflow 的工程地圖

### 3.1 一頁總覽

| Workflow | 它大概在做什麼 | 主要輸入 | 主要輸出 | 粒度 | 工程師先記住 |
|---|---|---|---|---|---|
| PANDA | 整合 motif、PPI、coexpression，估 TF→gene evidence | expression、TF-gene prior、TF-TF PPI | aggregate TF × gene network | aggregate | score 不是 probability；edge list 可供 CONDOR |
| PUMA | PANDA-style regulatory inference，再加入 miRNA | PANDA inputs + miRNA list／prior | aggregate regulator × gene network | aggregate | miRNA biology 不等於 score sign 的固定方向 |
| LIONESS-PANDA | 把 PANDA 變成每 sample 一張 network | PANDA inputs + aggregate／LIONESS outputs | aggregate + sample-specific networks | 兩者 | PANDA 是內部 estimator guidance，不是直接檔案 handoff |
| LIONESS-PUMA | 把 PUMA 變成每 sample 一張 network | PUMA inputs + aggregate／LIONESS outputs | aggregate + sample-specific networks | 兩者 | 不要把 aggregate PUMA 檔案當成唯一輸入再跑 |
| LIONESS-coexpression | 估每 sample 的 gene-gene coexpression | expression + aggregate／LIONESS output paths | aggregate + sample-specific coexpression | 兩者 | 不是 TF-gene network；至少需要足夠 samples |
| CONDOR | 在既有 bipartite network 找兩側 community | weighted source-target edge list | edge、regulator membership、target membership、summary | 不適用 | 不從 raw expression 重新推論 |
| COBRA | 分離 covariates 對 covariance 的影響 | expression + sample covariate design | components + adjusted coexpression | aggregate | adjusted artifact 需重新驗證才能 handoff |
| GIRAFFE | 聯合估計 signed regulation 與 TFA | expression、motif／prior、PPI | regulatory matrix + TF-by-sample TFA | aggregate + sample TFA | current agent 沒有 per-sample TF-gene network |
| BONOBO | Bayesian 估 sample-specific gene-gene coexpression | labeled expression + sample metadata | 每 sample coexpression，可選 p-values | sample-specific | 至少 3 samples；不是直接接 PANDA／PUMA |
| SAMBAR | 把 gene mutation 聚合成 pathway score，再做 subtype | mutation、gene length、cancer genes、GMT | gene／pathway scores + optional clusters | sample × pathway | 是獨立 mutation branch，不是 regulatory network |
| DRAGON | 估兩個 omics layer 的 conditional association | exactly two matched continuous matrices | aggregate undirected network | aggregate | 兩層與 sample 必須嚴格對齊；不可直接接 PANDA／CONDOR |
| OTTER | 以 graph matching 找一致的 TF→gene network | W prior、PPI、expression／coexpression | aggregate TF × gene network | aggregate | 只有驗證過的 edge list 才能接 CONDOR |

### 3.2 用四個問題快速分類

1. **在估 TF→gene 嗎？**  
   先看 PANDA、PUMA、GIRAFFE、OTTER；LIONESS-PANDA／PUMA 是它們的 sample-specific 版本。
2. **在估 gene-gene 關聯嗎？**  
   看 LIONESS-coexpression、BONOBO、COBRA；DRAGON 則是 two-layer multi-omic partial association。
3. **已經有 network，只想分群嗎？**  
   看 CONDOR。
4. **輸入是 mutation，輸出是 pathway／subtype 嗎？**  
   看 SAMBAR。

## 4. 工程師真正要守的 contract

### 4.1 通用檢查順序

~~~
檔案存在
  → delimiter／header 正確
  → row／column orientation 正確
  → identifier 可對齊
  → sample order 一致
  → numeric／finite
  → node type 與 edge direction 正確
  → output artifact 通過 validator
  → 才能解讀或 handoff
~~~

### 4.2 常見資料形狀

| 資料 | 常見形狀 | 常見錯誤 |
|---|---|---|
| expression | gene × sample | 把 sample × gene 傳入；把 metadata 欄混入 |
| sample covariate design | sample × covariate | sample index 不一致；categorical 欄未按 contract 處理 |
| TF-gene prior | TF × gene 或 source-target-weight | TF／gene 順序或 ID namespace 不一致 |
| PPI | TF × TF | 送入 gene-gene 或含未對齊 TF |
| coexpression | gene × gene 或 source-target-weight | 把 gene-gene 矩陣誤當 TF-gene network |
| mutation | sample × gene | 把 mutation count、binary mutation 與 expression 混用 |
| two-layer omics | 兩個 sample × feature tables | sample 不同、feature layer 混合或多於／少於兩層 |
| CONDOR edge list | source-target-weight | source／target 兩側未分清，或 weight 非 numeric |

### 4.3 兩種「不能只看檔名」的情況

- coexpression 可能是 Pearson、Bayesian posterior、COBRA adjusted artifact，不能只依副檔名判斷。
- network 可能是 TF-gene directed bipartite、gene-gene undirected，或 DRAGON 的 layer-qualified association；必須讀 manifest／欄位與 producer。

## 5. 12 個 workflow 速查卡

以下每張卡只保留工程師第一次接觸時最有用的資訊。完整的科學背景、固定 13 欄模板與論文脈絡，請回到完整筆記。

### 5.1 PANDA

- **定位**：把 TF-gene motif／prior、TF-TF PPI 與 gene-gene coexpression 透過 message passing 整合成 aggregate TF→gene regulatory evidence。
- **需要**：gene-by-sample expression、TF-gene prior、TF-TF PPI、output_file；可選已驗證的 coexpression_file。
- **產出**：aggregate weighted TF-by-gene network。
- **解讀**：高分代表在輸入 evidence 與模型假設下較一致；不是 probability、不是直接 binding，也不是因果。
- **容易失敗**：TF／gene ID 對不上、expression 軸反了、PPI 與 prior 的 TF 集合不同、coexpression 被誤傳成 TF-gene。
- **handoff**：輸出轉成並驗證 source,target,weight edge list 後可交給 CONDOR；COBRA 的 adjusted coexpression 可作 coexpression input，但必須先驗證。
- **不要混淆**：PANDA edge score 不是 TFA；PANDA 也不是 sample-specific，除非使用 LIONESS-PANDA。

### 5.2 PUMA

- **定位**：在 PANDA-style regulatory inference 中加入 miRNA regulator。
- **需要**：expression、motif、PPI、one-ID-per-line miRNA list，以及 output；可選 coexpression。
- **產出**：aggregate weighted TF／miRNA-by-gene regulatory evidence。
- **解讀**：看 regulator-to-gene 關係在整合後的相對分數與網路結構；不能把分數直接當作 miRNA 抑制百分比。
- **容易失敗**：miRNA ID、target prior、TF ID namespace 不一致；將 miRNA 的生物學背景直接套到 score 正負號。
- **handoff**：驗證後的 regulator-target edge list 可交給 CONDOR；COBRA adjusted coexpression 需先轉換／驗證。
- **不要混淆**：PUMA 的 miRNA repression biology 不代表所有負分都能直接命名為 repression effect。

### 5.3 LIONESS-PANDA

- **定位**：用 LIONESS leave-one-out construction，從 PANDA estimator 推出每個 sample 的 TF→gene network。
- **需要**：PANDA 所需的 expression、prior、PPI，以及 aggregate output／LIONESS output 設定。
- **產出**：aggregate PANDA network + sample-specific TF-gene networks。
- **核心公式**：N_k = n × N_all − (n − 1) × N_without_k。
- **解讀**：比較不同 sample 的 edge score 或網路結構；不是在單一 sample 上重新獨立估一個完整 PANDA 模型。
- **容易失敗**：sample 太少、leave-one-out estimator 不穩、aggregate 與 without-k 的 node order 不一致。
- **handoff**：PANDA 是內部 guidance predecessor，不是可直接餵下一個 workflow 的檔案 handoff。
- **不要混淆**：sample-specific 不代表臨床因果，也不代表每條 edge 都有單 sample 實驗驗證。

### 5.4 LIONESS-PUMA

- **定位**：用 LIONESS 將 PUMA 的 regulator-to-gene inference 展開到 sample 層級。
- **需要**：PUMA 的 expression、motif、PPI、miRNA list，以及 aggregate／LIONESS output 設定。
- **產出**：aggregate PUMA network + sample-specific TF／miRNA-to-gene networks。
- **解讀**：可比較 sample 間 regulator network 的相對差異。
- **容易失敗**：miRNA list 與 sample／gene identifiers 不一致；aggregate 與 leave-one-out input 產生不同 node universe。
- **handoff**：PUMA 是內部 guidance predecessor，不作 direct file handoff。
- **不要混淆**：不是把已輸出的 aggregate PUMA 矩陣當成另一個獨立 workflow 的唯一 input。

### 5.5 LIONESS-coexpression

- **定位**：從 aggregate Pearson coexpression 推出每個 sample 的 gene-gene coexpression。
- **需要**：gene-by-sample expression、aggregate output 與 LIONESS output；需要足夠 samples，current contract 以至少 3 samples 為基本檢查。
- **產出**：aggregate gene-gene coexpression + sample-specific networks。
- **解讀**：比較樣本間 gene pair 的 coexpression 結構；仍是 association。
- **容易失敗**：sample 數不足、expression scale／center 不一致、gene order 或 sample order 被改變。
- **handoff**：不直接 handoff 到 PANDA／PUMA／CONDOR；它是 gene-gene，不是 TF-gene。
- **不要混淆**：某個 gene pair 在 sample-specific network 分數高，不等於它們形成直接分子作用。

### 5.6 CONDOR

- **定位**：對既有的 weighted bipartite network 做兩側 community detection。
- **需要**：合格的 weighted source-target-weight edge list、output directory、可選 prefix。
- **產出**：prefix-edges.tsv、prefix-reg_memb.tsv、prefix-tar_memb.tsv、prefix-summary.txt。
- **解讀**：regulator side 與 target side 的 community／membership；需搭配 enrichment 或外部資料才可命名生物功能。
- **容易失敗**：輸入不是 bipartite、source／target 混邊、weight 非 numeric、空圖或 edge ID 未對齊。
- **handoff**：PANDA／PUMA／OTTER 的 aggregate network 經 exact validation 後可接 CONDOR。
- **不要混淆**：CONDOR 不從 raw expression 推論 regulatory edge，也不會把 community 自動變成 pathway。

### 5.7 COBRA

- **定位**：估計 sample covariates 如何影響 covariance structure，並產生 adjusted coexpression。
- **需要**：gene-by-sample expression、numeric sample-by-covariate design、output directory。
- **產出**：components.npz、summary.tsv、adjusted_coexpression.tsv／.npz、manifest.json。
- **解讀**：adjusted artifact 是去除或分離特定 covariate 影響後的 gene-gene coexpression；components 是模型分解，不是可直接當 matrix 的 raw network。
- **容易失敗**：sample metadata 對不上、design matrix rank／欄位有問題、covariate 與 phenotype 完全重疊、把 components 當成 adjusted matrix。
- **handoff**：adjusted coexpression 重新通過 identifier、shape、direction 與 numeric validation 後，可作 PANDA／PUMA／OTTER 的 coexpression input。
- **不要混淆**：COBRA 不會自動消除所有 confounding，也不產生 TF→gene network。

### 5.8 GIRAFFE

- **定位**：以生物先驗引導的 matrix factorization，聯合估計 signed TF-gene regulatory effects 與 TF-by-sample TFA。
- **需要**：expression、motif／prior、PPI、output file。
- **產出**：regulation matrix，以及同 stem、同 suffix 的 TF-by-sample TFA 檔案。
- **解讀**：regulatory effect 的正負與 TFA 要依 GIRAFFE 方法語意讀；signed effect 仍需結合輸入與模型假設。
- **容易失敗**：prior／PPI 與 expression node 不一致、TFA 檔名或 stem 推導錯誤、把 regulation matrix 與 TFA 矩陣混傳。
- **handoff**：current agent 沒有註冊的 direct handoff；不要自行宣稱可接 PANDA／CONDOR／OTTER。
- **不要混淆**：原始方法的 signed regulatory effects 不等於 current agent 支援 per-sample TF-gene networks；current agent 目前只有 aggregate TF-gene regulation + TF-by-sample TFA。

### 5.9 BONOBO

- **定位**：用 Bayesian model 估計 sample-specific gene-gene coexpression。
- **需要**：labeled gene-by-sample expression；至少 3 samples；明確的 log_transform／center 設定；可選 sparsify 與 p-values。
- **產出**：每個選定 sample 的 gene-gene coexpression，並由 manifest 記錄輸出；若啟用且支援可另存 p-values。
- **解讀**：posterior coexpression 是個體化的關聯估計；p-value 只有在實際 sparsify 並保存時才是可用 artifact。
- **容易失敗**：expression 未標註、sample 少、log／center 設定不清、將 p-values 口頭宣稱存在但沒有檔案。
- **handoff**：不直接交給 PANDA／PUMA；若要轉換，必須先定義 aggregation、格式轉換、provenance 與目標 validator。
- **不要混淆**：BONOBO 的 gene-gene posterior 不是 regulatory network，也不是因果個體化模型。

### 5.10 SAMBAR

- **定位**：把稀疏 somatic mutation 從 gene 層級聚合到 pathway，再進行 patient subtype 分析。
- **需要**：sample-by-gene mutation CSV、gene-length CSV、cancer-gene list、GMT pathway。
- **產出**：mt_out.csv、pt_out.csv，可選 clustergroups.csv、dist_matrix.csv、manifest.json。
- **解讀**：pathway mutation score 可用於樣本比較與 clustering；高分不自動等於 driver gene、致病性或臨床風險。
- **容易失敗**：gene length／gene ID 對不上、GMT annotation 不完整、mutation encoding 不符、sample order 被改變。
- **handoff**：是獨立的 mutation → pathway → subtype 分支，不直接接 regulatory network。
- **不要混淆**：SAMBAR 的 pathway score 不是 PANDA edge、不是 expression level，也不是 pathway 活性實驗測量。

### 5.11 DRAGON

- **定位**：用 two-layer Gaussian graphical model 估兩個 omics layer 在控制其他變數後的 conditional association。
- **需要**：exactly two 個 matched、sample-by-feature、continuous omics tables。
- **產出**：labeled symmetric matrix 或 edge list，含 partial correlation／precision 等 aggregate association。
- **解讀**：edge 表示在模型條件下的 undirected association；沒有時間方向，不自動是跨層因果。
- **容易失敗**：不是剛好兩層、sample 不匹配、資料非 continuous、layer label 遺失、把 symmetric matrix 當 directed edge list。
- **handoff**：current contract 禁止直接送 PANDA／PUMA／CONDOR 等 regulatory／bipartite workflow。
- **不要混淆**：DRAGON 的 shrinkage／precision estimation 與 motif／PPI prior 是不同概念。

### 5.12 OTTER

- **定位**：用 relaxed graph matching 找一個 TF-gene network，使其兩側 projection 同時接近 TF-TF PPI 與 gene-gene coexpression。
- **需要**：TF-gene seed／prior W、TF-TF PPI P、expression 或已驗證 coexpression C、output file。
- **產出**：aggregate TF-by-gene optimized network；可轉成完整的 source,target,weight edge list。
- **解讀**：W 是 graph matching 後的 regulatory score；不是 TFA，不是 probability，也不保證因果。
- **容易失敗**：W／P／C 的 node order 不一致、C 被誤當 TF-gene、矩陣不完整或 edge list 遺漏 zero／required IDs。
- **handoff**：只有 exact validation 通過的 edge list 才能交給 CONDOR；COBRA adjusted C 必須先驗證。
- **不要混淆**：目前 agent 只有 aggregate OTTER；即使上游生態存在 LIONESS-OTTER，也不能因此宣稱 agent 已支援。

## 6. Handoff：哪些可以接，哪些不要接

### 6.1 目前 contract 支援的路徑

~~~
COBRA adjusted coexpression
        │  exact validation：gene IDs、shape、direction、finite numeric、provenance
        ├──────────────→ PANDA
        ├──────────────→ PUMA
        └──────────────→ OTTER

validated aggregate PANDA edge list ─┐
validated aggregate PUMA edge list  ─┼──→ CONDOR
validated aggregate OTTER edge list ─┘
~~~

### 6.2 目前不要當成 direct handoff 的路徑

| 路徑 | 原因 |
|---|---|
| LIONESS-PANDA／PUMA → 下一個 workflow | predecessor 是內部 guidance，不是通用檔案 handoff |
| BONOBO → PANDA／PUMA | BONOBO 是 sample-specific gene-gene posterior，需要先定義轉換 |
| GIRAFFE → PANDA／CONDOR | current registry 沒有 direct handoff contract |
| DRAGON → PANDA／CONDOR | two-layer undirected partial association 與 regulatory bipartite edge 不同 |
| SAMBAR → regulatory workflow | mutation pathway subtype 是獨立分析分支 |
| LIONESS-coexpression → PANDA | gene-gene sample-specific network 不是已驗證的 regulatory coexpression contract |

### 6.3 Handoff checklist

在 agent 裡允許 handoff 前，至少確認：

- producer 與 consumer 的 node type 相容。
- source／target 方向明確，不能只依欄位名稱猜。
- gene／TF／miRNA identifiers 已對齊且 namespace 一致。
- matrix row／column order 與 edge list 內容一致。
- sample-specific 與 aggregate 粒度沒有被混用。
- weight／score 是 finite numeric，沒有把 p-value、membership 或 cluster label 當 weight。
- manifest 記錄 producer、參數、輸入摘要與轉換步驟。
- consumer validator 已實際通過；不能只因檔案存在就算成功。

## 7. 失敗排查決策樹

~~~
執行失敗或結果很奇怪
        │
        ├─ 檔案不存在／格式錯？
        │       └─ 查 path、delimiter、header、suffix、manifest
        │
        ├─ row／column 或 sample 對不上？
        │       └─ 查 orientation、sample order、ID intersection
        │
        ├─ workflow 類型是否選錯？
        │       ├─ gene-gene 被送到 TF-gene？
        │       ├─ undirected 被當 directed？
        │       └─ pathway score 被當 network？
        │
        ├─ output 有但解讀怪？
        │       └─ 先查 score／association／activity／causality 是否被混稱
        │
        └─ 想接下一步？
                └─ 回到 handoff checklist 與 consumer validator
~~~

### 7.1 錯誤訊息的工程解讀

| 現象 | 優先檢查 |
|---|---|
| missing required input | registry／YAML 的 required inputs 與實際 command mapping |
| shape mismatch | matrix orientation、node order、sample order |
| identifier mismatch | TF／gene／miRNA namespace、大小寫、版本後綴 |
| non-numeric | index／header 是否被讀成資料；空字串、NA、文字 label |
| output 檔存在但 validator fail | producer artifact 語意與 consumer contract 不相容 |
| network 很稀疏或全相同 | sample 數、variance、regularization、center／transform、prior overlap |
| TFA 與 expression 看起來相反 | TFA 不是 expression；先依方法定義讀，不要自行修正方向 |

## 8. 結果解讀的安全邊界

### 可以說

- 「在這組輸入資料與模型假設下，這條 edge 的 evidence 較高。」
- 「不同 samples 的 network score／coexpression 結構不同。」
- 「這些 regulator／target 在 bipartite graph 中被分到同一 community。」
- 「這兩個 omics feature 在控制其他變數後呈現 conditional association。」
- 「這些 samples 的 mutation pattern 在 pathway 層級較相似。」

### 不要直接說

- 「這一定是直接 binding。」
- 「這條 edge 是 activation／repression 的百分比。」
- 「這個 network 已證明因果。」
- 「community 就是 pathway。」
- 「TF expression 高，所以 TF activity 一定高。」
- 「pathway mutation score 高，所以該 pathway 已被功能性啟動。」
- 「workflow 跑完且沒有 exception，所以生物結論可靠。」

## 9. 一個虛構癌症 cohort 的最小理解

假設有 100 位病人：

- RNA expression：gene × 100 samples
- TF motif prior：TF × gene
- TF PPI：TF × TF
- somatic mutation：100 patients × genes
- pathway GMT：pathway → genes

可以這樣選：

| 想回答的問題 | 優先 workflow | 產物 |
|---|---|---|
| cohort 整體可能有哪些 TF→gene regulatory patterns？ | PANDA | aggregate TF-gene evidence |
| miRNA 是否也參與 regulator network？ | PUMA | aggregate TF／miRNA-gene evidence |
| 哪些病人的 regulatory network 不同？ | LIONESS-PANDA／PUMA | sample-specific regulatory networks |
| 哪些 gene pair 的 coexpression 受 hospital／batch 影響？ | COBRA | adjusted coexpression |
| 哪些 regulator／target 形成 network modules？ | CONDOR | 兩側 community membership |
| 哪些病人的 mutation pattern 可形成 pathway subtype？ | SAMBAR | pathway score／cluster |
| RNA 與另一 omics layer 有哪些 conditional associations？ | DRAGON | undirected multi-omic network |

重點是：這些問題互補，但不是一條必須全跑完的 pipeline。工程 orchestration 應先確認研究問題，再選 estimator 與 artifact，而不是依 workflow 名稱順序串接。

## 10. 工程師 onboarding checklist

### 第一次接觸 repository

- [ ] 找到 scripts/workflow_registry.py。
- [ ] 對照 workflows/*.yaml 的 input／output／validation。
- [ ] 先確認 workflow 是 aggregate、sample-specific 或非 network。
- [ ] 讀對應的 integration document 與 tests。
- [ ] 確認輸出的實際檔名、欄位與 manifest。
- [ ] 確認目前 agent contract，不用上游論文能力推測 agent 已支援的能力。

### 執行前

- [ ] 所有必要檔案存在。
- [ ] sample ID、gene ID、TF ID、miRNA ID 可對齊。
- [ ] matrix orientation 符合 workflow。
- [ ] numeric data 沒有未處理的 NA／Inf。
- [ ] 有記錄 transform、center、sparsify、shrinkage 或其他關鍵參數。

### 執行後

- [ ] output artifact 存在且不是空檔。
- [ ] shape、header、identifier、finite numeric 通過 validator。
- [ ] manifest 能追溯 producer、輸入與參數。
- [ ] 解讀時分清 score、p-value、activity、membership 與 association。

### handoff 前

- [ ] consumer 接受同一種 node／edge 語意。
- [ ] 必要 conversion 已明確記錄。
- [ ] 沒有把 sample-specific 輸出冒充 aggregate。
- [ ] consumer validator 實際通過。
- [ ] 尚未支援的路徑有清楚回報，而不是靜默轉換。

## 11. 五題自我測驗

1. COBRA 的 components.npz 可以直接當 PANDA 的 coexpression matrix 嗎？
2. DRAGON 的 partial-correlation edge 可以直接丟給 CONDOR 嗎？
3. PANDA 的高 edge score 是否代表該 TF 已經直接 binding 該 gene？
4. 為什麼 BONOBO 不應直接接到 PANDA？
5. 如果要找 mutation-driven patient subtype，應先看哪個 workflow？

### 答案

1. 不可以直接假設；應使用 adjusted coexpression artifact，並通過 PANDA contract 的 shape、ID、direction 與 numeric validation。
2. 目前不可以；DRAGON 是 two-layer undirected conditional association，不是已驗證的 regulatory bipartite edge list。
3. 不代表。它是在 prior、PPI、coexpression 與模型假設下的 regulatory evidence。
4. BONOBO 的輸出是 sample-specific gene-gene posterior；需要先定義 aggregation 與轉換，不能把它當作 PANDA 需要的 regulatory coexpression。
5. SAMBAR；它處理 mutation → pathway score → patient subtype。

## 12. 需要深入完整筆記的時機

| 你正在做的事 | 回到完整筆記看 |
|---|---|
| 只想知道 workflow 選擇 | 第 2、3、5 節 |
| 要寫 input validator | 第 4 節與各 workflow 的「輸入資料／必要假設」 |
| 要實作 handoff | 完整筆記的 handoff、artifact、registry 與 validation 章節 |
| 要解釋科學結果 | 完整筆記各 workflow 的「核心機制、結果怎麼解讀、不能怎麼解讀」 |
| 遇到 GIRAFFE、BONOBO、DRAGON、OTTER 的細節 | 完整筆記的 integration 文件對照段落 |
| 要讀論文或做研究設計 | 完整筆記的官方來源、toy example 與研究紀錄模板 |

## 13. 工程與科學來源

### Repository contract 優先順序

以目前 agent 能做什麼為準時，優先讀：

1. scripts/workflow_registry.py
2. workflows/*.yaml
3. 對應 integration／validation code
4. artifact validators、tests 與 execution code
5. 官方 netZooPy repository、官方文件與原始論文

### 官方來源

- [netZooPy GitHub](https://github.com/netZoo/netZooPy)
- [netZooPy documentation](https://netzoopy.readthedocs.io/en/stable/)
- [PANDA 原始論文](https://pmc.ncbi.nlm.nih.gov/articles/PMC3669401/)
- [PUMA 原始論文](https://pmc.ncbi.nlm.nih.gov/articles/PMC7750953/)
- [LIONESS 原始論文](https://pmc.ncbi.nlm.nih.gov/articles/PMC6815019/)
- [CONDOR 原始論文](https://pmc.ncbi.nlm.nih.gov/articles/PMC8099108/)
- [COBRA 原始論文](https://pmc.ncbi.nlm.nih.gov/articles/PMC11441315/)
- [GIRAFFE 原始論文與 PubMed](https://pubmed.ncbi.nlm.nih.gov/42523370/)
- [BONOBO 原始論文](https://pmc.ncbi.nlm.nih.gov/articles/PMC10680741/)
- [SAMBAR 原始論文](https://pmc.ncbi.nlm.nih.gov/articles/PMC5988673/)
- [DRAGON 原始論文](https://pmc.ncbi.nlm.nih.gov/articles/PMC9943674/)
- [OTTER 原始論文](https://pmc.ncbi.nlm.nih.gov/articles/PMC8546743/)
- [Network Zoo 方法總覽](https://pmc.ncbi.nlm.nih.gov/articles/PMC9999668/)

## 14. Changelog

### 2026-09-02

- 新增 AI Agent 工程師速讀版。
- 將 12 workflows 濃縮為總覽、contract、速查卡、handoff、debugging 與 onboarding checklist。
- 保留完整筆記作為科學背景、固定模板、論文與研究練習的參考來源。
- 明確標示目前 agent 支援的 handoff 與不可直接串接的路徑。
