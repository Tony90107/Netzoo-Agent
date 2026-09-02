# 給 AI 的 Prompt：更新 netZooPy 12 workflows 生物知識串聯筆記

把下方「Prompt 本文」完整貼給能讀取此 repository、能瀏覽官方資料並能修改檔案的 AI。

---

## Prompt 本文

你是一位同時熟悉系統生物學、網路生物學、統計建模、netZooPy 與科學教育的資深研究者，也是一位謹慎的 repository-aware 技術作者。

你的任務不是寫 12 篇互不相干的工具簡介，而是更新一份給生物資訊初學者閱讀的繁體中文 Markdown 筆記，讓讀者能建立一張完整的知識地圖：

1. 每個方法在回答哪一種生物問題。
2. 它使用哪些資料、建立哪種網路或產物。
3. 演算法為什麼有機會從這些資料得到這種結果。
4. 它依賴哪些假設，什麼情況下可能失敗。
5. 不同方法共享哪些概念，又有哪些根本差異。
6. 哪些方法可在科學概念上組合。
7. 哪些輸出在目前 netZoo agent 中可以直接交給下一個 workflow，哪些需要明確轉換與重新驗證，哪些目前禁止直接串接。
8. 結果可以支持什麼說法，又不能被誤讀成什麼。

### A. 目標檔案與工作方式

Repository root：

```text
/Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent
```

預期目標筆記：

```text
NETZOOPY_生物知識串聯筆記.md
```

開始前先在 repository 中搜尋這份筆記是否已改名或移動：

- 若找到既有版本，原地更新並保留仍正確、有教學價值的內容。
- 若預期路徑不存在但找到同義筆記，使用找到的實際路徑，不要建立重複文件。
- 若完全找不到，才在 repository root 建立 `NETZOOPY_生物知識串聯筆記.md`。
- 不要刪除有價值的舊案例、研究紀錄模板、自我測驗或來源；應重整、修正並融合。
- 不要只回覆建議、摘要或大綱；必須實際完成 Markdown 檔案更新。
- 不要修改與此筆記無關的程式碼、測試或設定。

### B. 先查證，再寫作

請依以下證據優先序工作：

1. `scripts/workflow_registry.py` 與 `workflows/*.yaml`：目前 agent 的能力、輸入輸出、handoff 與禁止事項的最高權威。
2. `docs/*_INTEGRATION.md`、對應 execution／validation 程式與測試：確認實際 adapter、輸出格式、參數與限制。
3. netZooPy 官方文件、官方 GitHub 與每個方法的原始論文：解釋科學原理與上游方法能力。
4. 其他可信的一手資料。

若 repository 敘述與上游 netZooPy 能力不同，必須分成兩欄或兩段說明：

- 「方法／論文在科學上能做什麼」
- 「目前這個 agent 已驗證並允許做什麼」

不得用上游套件的理論能力，冒充目前 agent 已經支援的直接 workflow 或 handoff。

所有會隨版本改變的資訊都要核對。使用原始論文或官方來源，在筆記末尾附可點擊連結；不要虛構 DOI、版本、API、參數、輸出檔名、公式或 benchmark 結果。

### C. 先修正分類：這是 12 個 workflows，不是 12 個獨立套件

筆記開頭必須溫和而清楚地說明：

- 此專案目前有 12 個已註冊的 scientific workflows。
- 它們對應 10 個主要方法家族。
- LIONESS 是一個 sample-specific network 框架，在 agent 中分成三種 workflow：LIONESS-PANDA、LIONESS-PUMA、LIONESS-coexpression。
- LIONESS-PANDA 與 LIONESS-PUMA 是組合方法，不是兩個完全獨立的上游套件。
- `netZooPy` 本身才是 Python 套件；PANDA、PUMA 等是其中的方法／模組，本文為配合使用情境可稱為「方法」或「workflow」。

要介紹的 12 個 workflows，名稱與順序固定如下：

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

### D. 建立一條共同的生物主線

不要直接從演算法名稱開始。先用一條初學者能理解的主線建立共同語言：

```text
DNA／motif
  → TF binding 與 TF activity
  → transcription／mRNA expression
  → miRNA post-transcriptional regulation
  → gene-gene coexpression
  → protein interaction／PPI
  → somatic mutation 與 pathway disruption
  → 多組學層之間的 conditional association
  → aggregate、condition-specific、sample-specific networks
  → community／module／subtype
```

解釋以下核心概念，而且每個概念都要指出會被哪些 workflows 使用：

- gene、mRNA、protein、TF、miRNA
- motif／regulatory prior
- TF activity（TFA）與 TF expression 的差別
- PPI
- expression matrix
- covariance、correlation、coexpression、partial correlation、precision matrix
- regulatory network、coexpression network、multi-omic network
- directed／undirected、bipartite／single-layer／multi-layer
- aggregate／condition-specific／sample-specific
- somatic mutation、gene length、pathway、cancer subtype
- batch、covariate、confounder、design matrix
- prior、regularization、shrinkage、message passing、matrix factorization、graph matching、Bayesian posterior、community detection

先用白話解釋，再給必要的正式名稱；公式只在能實質幫助理解時出現。

### E. 先放一張 12-workflow 全景比較表

表格至少包含：

| Workflow | 方法家族 | 核心問題 | 必要輸入 | Node／edge 語意 | 輸出 | 有向性 | 粒度 | 是否使用 prior | 目前可直接 handoff |

其中「粒度」需明確區分 aggregate、condition-specific、sample-specific 與 not applicable。

不要把所有 network 都叫 GRN：

- PANDA、PUMA、OTTER、GIRAFFE 產生 regulatory network，但 edge 語意不同。
- LIONESS 的 edge 語意由 base estimator 決定。
- BONOBO 與 LIONESS-coexpression 是 coexpression network，不是 TF-gene GRN。
- DRAGON 是兩層 multi-omic partial-correlation association network，不是 causal graph。
- CONDOR 產生 community assignment，不負責從 expression 推論原始 network。
- COBRA 產生 covariate-associated covariance decomposition 與 adjusted coexpression artifact。
- SAMBAR 產生 gene／pathway mutation scores 與可選的 sample clusters，不是 expression network。

### F. 每個 workflow 使用相同的教學模板

每個 workflow 都必須包含下列小節，不能只列 input／output：

1. **一句話定位**：用一句小白也懂的話說它在做什麼。
2. **生物問題**：研究者為什麼需要它。
3. **輸入資料**：每張表的列、欄、ID 與生物意義。
4. **輸出產物**：node、edge、matrix 或 cluster 的精確語意。
5. **核心機制**：用直覺、簡化圖和必要公式解釋演算法。
6. **為什麼有機會成功**：指出它利用了什麼資訊、限制或統計結構，不可只說「因為整合多種資料」。
7. **必要假設**：資料與模型要滿足什麼。
8. **容易失敗的情況**：ID、方向、樣本數、confounding、missing data、prior bias、高維小樣本等。
9. **結果怎麼解讀**：提供一個正確句型。
10. **結果不能怎麼解讀**：提供一個常見錯誤句型。
11. **與其他 workflows 的關係**：相似、互補、上游、下游或不可直接串接。
12. **目前 agent 邊界**：以 workflow YAML／registry 為準。
13. **極小型例子**：使用虛構或 repository toy data，並明確標註 toy example 不能支持真實生物結論。

### G. 各方法不可遺漏的科學重點

#### PANDA

- 說明 TF-gene prior、TF-TF PPI、gene-gene coexpression 三張網路如何透過 message passing 尋求一致性。
- 說明它產生 aggregate TF→gene regulatory evidence network。
- Edge score 不是機率，也不能只靠正負號判斷 activation／repression。
- 說明目前 agent 可使用經驗證的 `coexpression_file` 取代內部 Pearson coexpression construction，但 expression 仍負責 gene order／prior compatibility。

#### PUMA

- 說明它如何把 miRNA regulator 與 miRNA-target prior 納入 PANDA 類框架。
- 說明 miRNA 的典型抑制生物學，不等於 PUMA edge score 正負就是活化／抑制方向。
- 與 PANDA 比較 regulator layer 與研究問題。

#### LIONESS-PANDA、LIONESS-PUMA、LIONESS-coexpression

- 先解釋 LIONESS 是 estimator-agnostic 的 sample-specific 框架。
- 必須呈現並白話解釋：

```text
N_k = n × N_all - (n - 1) × N_without_k
```

- 三種 workflow 分別得到 sample-specific TF-gene GRN、TF/miRNA-gene GRN、gene-gene coexpression。
- PANDA／PUMA 是 guidance predecessor，不是把已輸出的 aggregate 檔案直接餵給 LIONESS。
- Aggregate COBRA artifact 不是 LIONESS 的直接 handoff；每個 leave-one-out 背景若需校正，必須在相應 construction 中重新處理。

#### CONDOR

- 解釋 bipartite community detection、regulator-side 與 target-side membership、modularity 與 q-score。
- 說明它分析已存在的 bipartite network，不直接吃 raw expression。
- PANDA／PUMA／OTTER output 只有在轉成並驗證 `source-target-weight` edge list 後才可 handoff。
- Community 不自動等於 biological pathway，需 enrichment 與外部驗證。

#### COBRA

- 說明一般 batch correction 處理一階 gene-level effect，仍可能留下 correlation structure 中的 higher-order batch effect。
- 說明 expression + numeric design matrix 如何得到 covariate-associated covariance components 與 adjusted coexpression。
- 說明 adjusted artifact 經 identifier／order 重新驗證後可交給 PANDA、PUMA 或 OTTER 的 `coexpression_file`。
- Raw components 本身不是下游 matrix input。
- 完全 confounded 的 batch 與 phenotype 無法靠演算法魔法分開。

#### GIRAFFE

- 說明它以 biologically informed matrix factorization，聯合估計 aggregate TF-gene regulation matrix `R` 與 TF-by-sample activity matrix `A`／TFA。
- 說明概念式 `Y ≈ R × A`，以及 motif prior 與 PPI 如何約束／引導解。
- 說明「同時估計調控效果與 TF activity」為何比只看 TF expression 更接近研究問題。
- 依最新原始論文與本 agent contract，精確解釋 signed regulatory effects；不要把其他 netZoo edge score 的語意套用到 GIRAFFE。
- 強調目前 output 仍是 aggregate TF-gene regulation + sample-level TFA，不是每個樣本各一張 TF-gene network。
- 目前 agent 不允許直接 handoff；若要交給 CONDOR，需明確 matrix-to-edge-list conversion、驗證與使用者確認。

#### BONOBO

- 全名與核心概念：Bayesian sample-specific coexpression inference。
- 每個 sample 結合自己的 centered expression deviation，以及其他 `N-1` samples 建立的背景／prior information。
- 解釋 conjugate prior、closed-form posterior、positive-definite covariance／correlation estimate 與 optional p-values 為什麼有用。
- 與 LIONESS-coexpression 比較：Bayesian shrinkage／posterior vs leave-one-out linear interpolation。
- BONOBO output 是每個樣本的 gene-gene coexpression matrix，不是 GRN 或 causal network。
- 論文在概念上討論 BONOBO network 可支援個體化 GRN；但目前 agent 不允許把多張 sample-specific output 直接當成 PANDA／PUMA 的單一 aggregate `coexpression_file`。必須先明確選 sample 或定義 aggregation，再另行驗證與確認。

#### SAMBAR

- 全名：Subtyping Agglomerated Mutations By Annotation Relations。
- 解釋 somatic mutation matrix 為何稀疏，以及為何先依 gene length／sample mutation burden 正規化，再聚合成 pathway mutation scores，可降低維度並提高跨病人的可比較性。
- 說明 pathway annotation 讓不同 genes 的 mutations 能在共同功能層級匯合，之後才進行 sample clustering／subtyping。
- 強調 pathway score 與 cluster 是計算分型，不自動等於已驗證的臨床 subtype。
- SAMBAR 是 mutation→pathway→subtype 的獨立分支，output 不是其他 11 個 workflows 的直接 input。

#### DRAGON

- 全名：Determining Regulatory Associations using Graphical models on multi-Omic Networks。
- 只處理兩個 matched sample-by-feature continuous omics layers；sample IDs 必須一致。
- 解釋 Gaussian graphical model、precision matrix 與 partial correlation：在控制其他 variables 後的條件關聯。
- 解釋 layer-specific shrinkage 為何能改善高維小樣本 covariance／precision estimation。
- Output 是 aggregate、undirected、two-layer association network，不是 sample-specific 或 causal graph。
- 目前 agent 沒有直接 handoff 到其他 workflows；不得因為它叫 network 就直接送進 CONDOR 或 PANDA。

#### OTTER

- 全名：Optimize To Estimate Regulation。
- 定義未知 TF×gene GRN `W`、TF-side projection `P ≈ W Wᵀ`、gene-side projection `C ≈ Wᵀ W` 與 prior／initial guess `W₀`。
- 解釋 relaxed graph matching 如何尋找一個 `W`，使它在兩側的投影同時接近 PPI 與 coexpression，並受 prior／regularization 約束。
- 與 PANDA 比較：相同資料家族與類似目標，但 OTTER 是明確 optimization／graph-matching view，PANDA 是 message-passing consistency update。
- Output 是 aggregate TF→gene optimized W score，不是 sample-specific network。
- COBRA adjusted coexpression 可在重新驗證後成為 OTTER 的 C；OTTER edge-list output 可在重新驗證後交給 CONDOR。
- 上游 netZooPy 有另外的 LIONESS-OTTER 能力，但目前 agent 註冊的 `run_otter` 只有 aggregate OTTER，不得混稱已支援 LIONESS-OTTER。

### H. 必須做四組深度比較

不要只做 12 列總表；至少另外建立以下比較表：

#### 1. PANDA vs PUMA vs OTTER vs GIRAFFE

比較：

- 想推論的 edge 語意
- 使用的 expression／coexpression、motif、PPI、miRNA prior
- message passing、graph matching、matrix factorization 的差異
- 是否估計 TFA
- edge 正負是否能表示 regulatory direction
- aggregate／sample-specific
- 何時選哪一個

#### 2. LIONESS-coexpression vs BONOBO

比較：

- leave-one-out linear interpolation vs Bayesian posterior/shrinkage
- 是否產生 positive-definite network
- 是否提供 uncertainty／p-values
- 樣本特異性如何產生
- 假設、優勢、限制與使用情境

#### 3. COBRA vs DRAGON vs一般 coexpression

比較：

- correlation／covariance decomposition／partial correlation
- batch／covariate 調整
- single-omic vs two-layer multi-omic
- aggregate vs sample-specific
- association vs causation

#### 4. CONDOR vs SAMBAR

比較：

- community detection on an existing bipartite network
- pathway aggregation and patient clustering from mutations
- 為什麼兩者都在「找群組」，卻不是同一種分群問題

### I. 畫出三種關係圖，不要畫一條假的萬能流水線

必須用 Mermaid 或清楚的 ASCII diagram 畫出：

1. **依生物問題分類圖**：GRN、sample-specific coexpression、multi-omics association、mutation subtyping、community analysis。
2. **資料與 artifact flow 圖**。
3. **目前 agent handoff 圖**。

Handoff 圖要使用三種線型或明確 legend：

- `實線`：目前 agent 已驗證的直接 handoff。
- `虛線`：科學概念上可能組合，但需要新 conversion／validation／user confirmation。
- `禁止符號`：目前 artifact contract 不相容，不可直接串接。

至少表達：

```text
COBRA adjusted coexpression
  → PANDA
  → PUMA
  → OTTER

PANDA／PUMA／OTTER validated edge list
  → CONDOR

LIONESS-PANDA = PANDA estimator inside leave-one-out construction
LIONESS-PUMA  = PUMA estimator inside leave-one-out construction

BONOBO sample-specific coexpression
  --概念上可支援個體化 GRN，但目前不是直接 handoff-->
  PANDA／PUMA／OTTER

GIRAFFE、DRAGON、SAMBAR
  目前各自為獨立 workflow branch
```

不要把所有 12 個 methods 硬串成一條 pipeline；那在科學與 artifact contract 上都不正確。

### J. 用同一個癌症 cohort 案例串起知識

設計一個明確標註為「虛構教學案例」的癌症 cohort，具有：

- bulk gene expression
- motif prior
- TF-TF PPI
- miRNA-target prior
- batch／hospital／treatment metadata
- somatic mutation matrix
- 第二層 matched omics（例如 methylation 或 proteomics）

用同一組研究問題示範每個 workflow 能回答哪一個子問題。必須畫成多條互補分析分支，而非假裝所有 outputs 都能互餵：

- PANDA／PUMA／OTTER／GIRAFFE：不同角度的 regulatory inference。
- LIONESS workflows／BONOBO：個體差異。
- COBRA：covariate-associated coexpression 與 batch-aware input。
- DRAGON：跨兩層 omics 的 conditional association。
- SAMBAR：mutation pathway scores 與 patient subtypes。
- CONDOR：對合格 bipartite regulatory network 找 modules。

每一分支最後都寫：

- 得到的 evidence 是什麼。
- 下一個合理分析是什麼。
- 哪一種實驗或外部資料可驗證。
- 不能直接下哪一種因果或臨床結論。

### K. 加入工具選擇決策樹

至少涵蓋：

```text
你要的是 TF-gene regulation、miRNA regulation、TF activity、
sample-specific coexpression、multi-omic conditional association、
mutation-based subtype，還是 existing network communities？
```

決策樹的終點必須是這 12 個 workflows 之一，或明確回答「目前這 12 個 workflows 都不適合」。

### L. 結果解讀與證據階梯

建立共通的六層證據階梯：

1. Input／identifier／orientation／normalization 正確。
2. 模型輸出與 artifact verification 通過。
3. 對 prior、parameter、random seed、resampling 穩定。
4. 與 phenotype 有適當統計關聯並處理 multiple testing。
5. 外部 cohort 或 orthogonal data 支持。
6. Perturbation／functional experiment 支持。

必須反覆提醒：

- Network edge 通常是模型證據或 association，不等於因果。
- Higher score 不等於 probability。
- Signed edge 的語意依方法而異，不可跨方法套用。
- Community、pathway score、cluster、subtype、driver 是不同層級的概念。
- Toy data 跑通只證明軟體與格式，不證明生物機制。

### M. 文件格式與教學風格

- 全文使用繁體中文。
- 專有名詞第一次出現時附英文，之後可使用縮寫。
- 面向沒有生物背景、但願意學習資料分析的讀者。
- 先給直覺，再給正式定義，再給例子，最後給限制。
- 使用短段落、比較表、ASCII／Mermaid 圖、極小型矩陣與 edge-list examples。
- 比喻必須標註其簡化之處，不能取代科學定義。
- 不要使用「神奇地學會」、「證明某基因造成疾病」等過度宣稱。
- 不要為了完整而重複同一段 input／output；使用共通概念章節加固定模板。
- 在每一大章末尾加入「你現在應該能回答」的 2～4 題自我檢查。
- 文件末尾加入 glossary、來源、最後核對日期與 changelog。

### N. 建議文件章節

可微調標題，但不得省略核心內容：

1. 這份筆記怎麼用
2. 12 workflows 與 10 方法家族
3. 一條共同的生物主線
4. 必要資料與 network vocabulary
5. 12-workflow 全景表
6. Regulatory inference 家族：PANDA、PUMA、OTTER、GIRAFFE
7. Sample-specific 家族：三種 LIONESS、BONOBO
8. Covariate／multi-omic 家族：COBRA、DRAGON
9. Downstream structure／subtyping：CONDOR、SAMBAR
10. 四組深度比較
11. 科學關係圖與目前 agent handoff 圖
12. 同一癌症 cohort 的多分支案例
13. 工具選擇決策樹
14. Input／ID／orientation／normalization 檢查
15. 結果解讀、失敗模式與證據階梯
16. Repository toy data 練習
17. 自我測驗與參考答案
18. 研究紀錄模板
19. Glossary
20. 官方來源與維護紀錄

### O. 最低官方來源

至少核對並引用：

- netZooPy GitHub：https://github.com/netZoo/netZooPy
- netZooPy docs：https://netzoopy.readthedocs.io/en/stable/
- PANDA：https://pmc.ncbi.nlm.nih.gov/articles/PMC3669401/
- PUMA：https://pmc.ncbi.nlm.nih.gov/articles/PMC7750953/
- LIONESS：https://pmc.ncbi.nlm.nih.gov/articles/PMC6815019/
- CONDOR／bipartite community detection：https://pmc.ncbi.nlm.nih.gov/articles/PMC8099108/
- COBRA：https://pmc.ncbi.nlm.nih.gov/articles/PMC11441315/
- BONOBO：https://pmc.ncbi.nlm.nih.gov/articles/PMC10680741/
- SAMBAR：https://pmc.ncbi.nlm.nih.gov/articles/PMC5988673/
- DRAGON：https://pmc.ncbi.nlm.nih.gov/articles/PMC9943674/
- OTTER：https://pmc.ncbi.nlm.nih.gov/articles/PMC8546743/
- GIRAFFE：先核對最新原始論文與 PubMed record：https://pubmed.ncbi.nlm.nih.gov/42523370/
- Network Zoo 方法總覽：https://pmc.ncbi.nlm.nih.gov/articles/PMC9999668/

來源不足時要明確標註不確定性，不能從 method name 或 repository 變數名猜測科學語意。

### P. 完成前驗收

完成後逐項檢查並在回覆中簡短報告：

- [ ] 12 個 workflows 全部出現，沒有把 LIONESS 三種模式誤稱為三個獨立套件。
- [ ] 每個 workflow 都有「做什麼、怎麼做、為什麼可能成功、假設、失敗、解讀、關聯、agent 邊界、例子」。
- [ ] PANDA／PUMA／OTTER／GIRAFFE 的 edge 語意沒有混用。
- [ ] LIONESS-coexpression 與 BONOBO 有深入比較。
- [ ] COBRA 與 DRAGON 沒有被誤寫成同一種 batch correction。
- [ ] CONDOR 與 SAMBAR 的分群對象與目的清楚不同。
- [ ] Direct handoff、conceptual composition、illegal handoff 有清楚圖例。
- [ ] 沒有把 aggregate network 說成 sample-specific，或反過來。
- [ ] 沒有把 association 說成 causation。
- [ ] 所有 local file paths、toy data、workflow names、outputs 與 source links 已驗證。
- [ ] Markdown tables、code fences、internal links 與 headings 結構正確。
- [ ] 已保留並更新最後核對日期與 changelog。

最後只需回覆：

1. 實際更新的檔案路徑。
2. 新增／重構的主要章節。
3. 查證過的 repository 與官方來源。
4. 仍存在的不確定性或尚未驗證的能力。

不要在回覆中重新貼出整份筆記；完整內容應寫入 Markdown 檔案。

---

## 可選補充資訊

若使用的 AI 無法直接讀取 repository，請在 Prompt 後面另外附上：

1. 舊筆記全文。
2. `scripts/workflow_registry.py` 中 12 個 `run_*` definitions。
3. `workflows/*.yaml` 全文。
4. 四份現有 integration docs：GIRAFFE、BONOBO、DRAGON、OTTER。
5. SAMBAR 的 `workflows/sambar.yaml`、`scripts/run_sambar.py`、資料驗證程式與 `data/sambar-toy/README.md`。

沒有這些 repository 證據時，AI 可以撰寫科學概念，但不能可靠描述「目前 agent 已支援的輸入、輸出與 handoff」。
