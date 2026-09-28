# 評分答案：不得送给被測 agent

日期：2026-09-27。這是待測預期，並非已實跑結果。以下是人工語意評分，不要求逐字匹配。中文輸入的 agent 回覆也預期為英文，符合現有 harness policy。

## 共通通過條件

- 首輪真正模糊時，保留合理候選，以實驗假設/要估計的量追問；工具名可在 agent 回覆出現。
- 說明至少兩條候選路徑的差異，以及哪條線索改變選擇；僅列工具名稱不算辨識成功。
- 輸入必須由生物學角色、形狀、粒度、ID 和假設導出；使用者說有量測不等於資料已提供或已驗證。
- 本盲測不提供檔案、不授權執行，故正確結果是概念方案、缺少證據或 clarification。不能聲稱 ready、成功執行或產生真實結果。
- 格式轉換、統計彙總、關聯檢定、閾值、富集及未註冊串接要標示為另需支援/明確驗證的步驟，不能杜撰可執行 action。
- 每輪只可依當時已揭露線索評分；不得要求 agent 在 T1 猜中 T4 的隱藏目的。T4 合理撤回先前方案也是成功。

## 每份對話 10 分

| 面向 | 分數 | 判定 |
|---|---:|---|
| 意圖与追問 | 0–2 | 0=錯誤/未澄清；1=部分保留候選；2=辨識粒度、實驗問題與關鍵歧義 |
| 演算法與候選差異 | 0–2 | 0=只猜工具/假設錯；1=工具大致正確但理由弱；2=由假設與 estimand 解釋選擇 |
| 輸入契約 | 0–2 | 0=資料角色錯；1=列角色但缺 shape/ID；2=角色、方向、必要確認及驗證正確 |
| 多輪 workflow | 0–2 | 0=非法串接/未更新；1=只完成部分轉換；2=隨新證據更新且辨識 handoff/額外步驟 |
| 輸出與限制 | 0–2 | 0=語意錯/杜撰；1=部分正確；2=產物、粒度、可解讀範圍及停止原因正確 |

8–10 分且無 critical failure：通過；5–7 分：部分；0–4 分：失敗。有任一列出的 critical failure，該份對話標為失敗，原始分数仍保留作診斷。

語言一致性：同一 case 中英皆通過才算 paired pass。請分別報 zh/en pass count、paired pass/10、每個面向的平均分與首輪過早選工具率，不只報總平均。

## Case 01：群體調控轉為個體連線

**隱藏實驗假設：** 以 TF→gene 為節點角色，先採多證據 message passing，再估計個體 wiring；治療反應只是後續關聯目標。

**候選差異範圍：** PANDA、OTTER、GIRAFFE；粒度改變後加入 LIONESS-PANDA。

- **T1：** 不能從共變直接判定調控或因果。詢問是否要 gene–gene 關聯、TF–gene 調控，以及群體或個體結果。
- **T2：** 優先 run_panda；用 message passing 與 OTTER 的目標函數最佳化、GIRAFFE 的共同估計活性區分，列出缺少證據。
- **T3：** 改為 run_lioness_panda；解釋個體 wiring/outdegree 與 TFA 差異。治療反應需另有依 sample ID 對齊的標籤。
- **T4：** 拒絕複製 aggregate 當個體結果。需要原始 cohort 與 priors 重估 all/leave-one-out；aggregate 是 guidance，不是唯一可消費的前置產物。

**輸入／確認需求：** gene×sample 表現量、TF→gene 結合先驗、TF–TF 互作先驗；物種/ID、數值、方向、跨資料相容性；個體模式至少 3 samples。治療反應標籤是後續分析需求。

**預期輸出：** aggregate TF→gene network；個體模式另有各 sample 的 TF→gene 邊權。Outdegree/治療關聯是額外彙總與統計步驟。

**Workflow：** 驗證→PANDA 群體估計（可選先行）→LIONESS-PANDA 由原始資料內部重估→個體 targeting 彙總→治療關聯（後兩步需額外支援）。

**Critical failures：**

- 把 gene correlation 當 TF regulation
- T3 仍只給 aggregate
- 複製群體網路當個體網路
- 宣稱已完成治療關聯

**合格最終回覆示例（英文；仍须配合前輪完整解釋）：**

> I would use LIONESS-PANDA for patient-specific wiring, rather than copy the aggregate network. It recomputes the cohort network with each sample omitted. I still need the expression and compatible biological priors; treatment-response association is a separate step.

## Case 02：非蛋白質控制者與個體網路

**隱藏實驗假設：** miRNA target prior 與 TF evidence 共同整合；未量測 miRNA abundance 不等於不能推論 target-based 網路。

**候選差異範圍：** PANDA、PUMA、DRAGON；T4 為 LIONESS-PUMA。

- **T1：** 詢問遗漏控制者的生物類型，不能自行假定 miRNA。
- **T2：** 選 run_puma，保留 TF 與 miRNA regulator 身分；不是 PANDA TF-only 或兩個連續 omics layer 的 DRAGON。
- **T3：** 說明可利用 miRNA-target prior 與 target-gene coexpression，不強制索取 miRNA expression；miRNA 清單需與 combined prior 相容，不能把所有 regulator 都解讀成 PPI 蛋白質。邊權不是直接量測的抑制係數。
- **T4：** 改為 run_lioness_puma；需要原始 cohort、combined prior、TF PPI 與 miRNA identities，不能僅拆分 PUMA aggregate。

**輸入／確認需求：** gene×sample expression；TF/miRNA→gene 合併 prior；TF PPI；每行一個 miRNA 的身份清單且每個 ID 出現在 prior regulator 軸；個體模式至少 3 samples。

**預期輸出：** 群體及個體 regulator→gene 加權網路，regulator 類型可追溯。不是 miRNA activity 或 signed repression coefficient。

**Workflow：** 驗證角色→PUMA aggregate（可選）→LIONESS-PUMA 內部 all/leave-one-out→個體比較（另行統計）。

**Critical failures：**

- 刪除 miRNA 後選 PANDA
- 強迫提供未量測的 miRNA abundance 才能計畫
- 把 miRNA 當蛋白質互作節點
- 把所有負權當抑制證據

**合格最終回覆示例（英文；仍须配合前輪完整解釋）：**

> PUMA can integrate short-RNA target priors without measured short-RNA abundance. For patient-specific networks I would switch to LIONESS-PUMA, keeping both regulator types. I need compatible target-expression and prior evidence, and the short-RNA identities.

## Case 03：每位病人的調控強度歧義

**隱藏實驗假設：** 觀察目標表現推估 TF activity，而非邊權加總；共同 regulatory effects 與 sample-varying activity。

**候選差異範圍：** GIRAFFE、LIONESS-PANDA、PANDA。

- **T1：** 必須揭露 activity 與 wiring/outdegree 兩種解讀，以一個能區分假設的問題追問，不能只因每人一值就選 LIONESS。
- **T2：** 優先 run_giraffe；解釋 activity 未被綁定於 TF 自身 mRNA，而非統計上保證完全獨立。
- **T3：** 說明共同矩陣 R 與 TF×sample TFA，Y≈R|TFA|；R 的 signed partial effects 與 PANDA/OTTER 權重不同。TFA 是非負活性，不是每個 sample 一張 signed GRN。
- **T4：** 拒絕因果死亡結論；預後分析需 follow-up time、event、covariates 與獨立統計設計，這些不是 run_giraffe 的參數。

**輸入／確認需求：** gene×sample expression、TF→gene prior、TF–TF PPI，精確 TF/gene ID 相容性与必要格式轉換。預後需另有 sample-keyed follow-up/event/covariates。

**預期輸出：** aggregate TF×gene signed R 與 TF×sample 非負 TFA，兩個產物都驗證。Cox/因果推論未由這個 workflow 完成。

**Workflow：** 驗證→GIRAFFE joint fit→TFA 與臨床資料對齊→另行預後關聯設計；因果主張無法由此直接推出。

**Critical failures：**

- T1 不承認 activity/wiring 歧義
- 把 TFA 當個體 GRN
- 把 activity 當 TF mRNA
- 宣稱因果或虛構 Cox 執行

**合格最終回覆示例（英文；仍须配合前輪完整解釋）：**

> Your clarification points to GIRAFFE: shared signed regulatory effects and TF activity varying by patient. The activity matrix is not a patient-specific wiring network. A survival association needs follow-up, event status and covariates; these outputs alone do not establish causality.

## Case 04：固定運算预算與網路模組

**隱藏實驗假設：** 固定 gradient 步數、明確 relaxed graph matching objective，再做二分圖模組分析；效率需求本身不是充分證據。

**候選差異範圍：** PANDA、OTTER、GIRAFFE；後續 CONDOR。

- **T1：** 列候選並追問停止規則/輸出語意。不能只憑時間短就保證某工具更快或更省記憶體。
- **T2：** 推薦 run_otter；解釋 W/P/C 的圖匹配最佳化、lam 權衡 C/P、gamma regularization 與 iterations 固定停止；避免承諾收斂。
- **T3：** 規劃 OTTER→合規 source,target,weight export→run_condor，矩陣需明確轉換與雙側角色/權重驗證。
- **T4：** 拒絕 gamma=稀疏保證、內建 edge p-values、aggregate=per-patient。此 agent 未註冊 LIONESS-OTTER；不能因 upstream 有功能就宣稱可執行。

**輸入／確認需求：** TF×gene seed W、TF–TF PPI P、expression 或 labeled gene×gene C；W/P/C identifier/order 精確對齊。CONDOR 另驗證兩側不混淆、可接受權重與 edge-list 格式。

**預期輸出：** aggregate optimized W scores；CONDOR regulator/gene community assignments。不是 p-values、稀疏保證或個體網路。

**Workflow：** 驗證 W/P/C→OTTER→edge-list export/驗證→CONDOR；額外顯著性、閾值與個體推論需獨立方法/支援。

**Critical failures：**

- 僅因 timeout 選 OTTER 並保證更快
- gamma 當 L1 sparsity
- 杜撰 OTTER p-values 或 LIONESS-OTTER action
- 矩陣無轉換直接給 CONDOR

**合格最終回覆示例（英文；仍须配合前輪完整解釋）：**

> OTTER matches your fixed-step optimization preference, followed by a validated bipartite export for CONDOR. Its regularization does not guarantee sparsity or supply edge p-values. The registered OTTER workflow is aggregate only, so I cannot label its result as patient-specific.

## Case 05：技術共變與生物差異的可識別性

**隱藏實驗假設：** covariate-associated covariance decomposition 與 downstream regulation；完全混淆不可識別、aggregate 不能冒充 leave-one-out input。

**候選差異範圍：** COBRA、PANDA、DRAGON；個體延伸 LIONESS-PANDA 有額外限制。

- **T1：** 追問醫院/疾病是否交叉分布與目標是均值還是 covariance，不能默認可消除技術效應。
- **T2：** 選 run_cobra；須確認 numeric design 的編碼、intercept/reference、sample IDs 和可識別性。不能把它當雙 omics DRAGON。
- **T3：** 規劃 COBRA→adjusted coexpression 驗證→run_panda，仍需要 expression/motif/PPI。說明目前 adapter 用 intercept component，不保證自動保留所有 biological components；先界定需要保留的 estimand/重建方式。
- **T4：** 停止保證性校正：hospital/disease 完全混淆不能分辨。aggregate adjusted C 不能直接供 LIONESS-PANDA，需每個 leave-one-out 子集重做 adjustment 並有受支援實作。

**輸入／確認需求：** gene×sample expression（genes>samples）；sample×numeric-covariate design，sample set 相同；full-rank/混淆檢查與 biological/nuisance coding；後續 TF priors。

**預期輸出：** covariance components、summary/manifest、intercept-based adjusted labeled C；下游 aggregate regulatory network。不能宣稱 adjusted expression 或自動保留所有病理訊號。

**Workflow：** 設計/混淆評估→COBRA→確認 adjusted C 的估計目標→驗證→PANDA；T4 新證據需撤回「可分開醫院與疾病」計畫。

**Critical failures：**

- 把 covariance decomposition 當基因均值批次校正
- 自動保留疾病的保證
- 完全混淆仍產出確定疾病效應
- aggregate C 直接串 LIONESS

**合格最終回覆示例（英文；仍须配合前輪完整解釋）：**

> The corrected records make hospital and disease inseparable in this design. I cannot guarantee removal of one while preserving the other. COBRA’s current adjusted artifact is intercept-based, and an aggregate artifact also cannot replace the repeated subset adjustment needed for patient-specific inference.

## Case 06：個體共變的估計假設

**隱藏實驗假設：** 個體 gene–gene coexpression，偏好由 all vs omitted network 插值；不是 n=1 Pearson，也不是調控方向。

**候選差異範圍：** LIONESS-COEXPRESSION、BONOBO、COBRA。

- **T1：** 候選 LIONESS-coexpression/BONOBO；問要 cohort-contribution 還是 Bayesian individual covariance/confidence，不能因 sample-specific 唯一選工具。
- **T2：** 說明 cohort-based inference 可用其他樣本估個體網路，不能將單點 Pearson 假裝可估；仍未足以唯一區分兩法。
- **T3：** 推薦 run_lioness_coexpression；說明 N_k=nN_all−(n−1)N_without_k、至少 3 samples；BONOBO 是 posterior covariance 且不產 aggregate reference。
- **T4：** 拒絕 activation/causal 與任意二分；gene–gene network 不是 CONDOR 的 regulator/target bipartite 輸入，無 direct handoff。

**輸入／確認需求：** 完整 numeric gene×sample expression、至少 3 samples、sample IDs、biological identifier 相容性。無需因 TF/motif/PPI 不在場而阻擋 gene coexpression。

**預期輸出：** aggregate gene–gene reference 與 sample-specific gene–gene edge estimates。非 TF–gene、因果或內建 edge p-values。

**Workflow：** 驗證→LIONESS-coexpression→逐人/逐邊比較（另行統計）；不直接串 CONDOR。

**Critical failures：**

- 每個人一點直接 Pearson
- 只因 sample 數多就斷言唯一工具
- 要求 TF prior 才能共表現
- 共表現改名調控並任意二分

**合格最終回覆示例（英文；仍须配合前輪完整解釋）：**

> LIONESS co-expression fits your cohort-contribution question: compare the full-cohort network with networks omitting each person. These are gene–gene association estimates, not activation effects, and they cannot be passed directly to a regulator–target bipartite community workflow.

## Case 07：個體共變可信度與保留完整結果

**隱藏實驗假設：** Bayesian prior/posterior 個體 covariance 與 approximate p-values；保留 p-values 模式不等於已 threshold；粒度不可偷換。

**候選差異範圍：** BONOBO、LIONESS-COEXPRESSION、COBRA。

- **T1：** 六人本身不是充分選擇理由；詢問所需 uncertainty 與 individual-estimation 假設。
- **T2：** 推薦 run_bonobo；說明背景 prior 與 sample update 的 Bayesian 假設；p-values 是近似檢定值，非邊為真的 posterior probability。
- **T3：** 規劃 sparsify=true, save_pvals=true，保留完整網路+pvalues，network_sparsified=false、pvalue_thresholding_required=true；驗證前處理宣告和至少 3 samples，不能默認已通過。
- **T4：** 可 keep_in_memory=false；拒絕宣稱已删边，尚須另作 pvalue threshold/multiple-testing 決策；個體 C 不能當 aggregate PANDA/PUMA/OTTER input，需 explicit 合規準備與 priors。

**輸入／確認需求：** labeled gene×sample finite complete expression、至少 3 samples、唯一 sample names；確認 log_transformed/centered=true。sample_names 用身份不是位置。

**預期輸出：** 每人完整 gene×gene coexpression、對應 pvalue matrix、manifest 與 sample-output mapping。P-values 非自動 multiple-testing-adjusted；不產 aggregate GRN。

**Workflow：** 確認前處理→BONOBO full networks+pvalues（逐人落盤）→另作閾值/多重檢定→gene network 比較；direct aggregate-GRN handoff 被阻擋。

**Critical failures：**

- 六人就是必選 BONOBO
- pvalue 當 posterior probability
- save_pvals 模式聲稱已 threshold
- 個體 C 直接當群體 C
- pvalues 宣稱已做 FDR

**合格最終回覆示例（英文；仍须配合前輪完整解釋）：**

> BONOBO can retain full individual co-expression matrices and matching approximate p-values. In this mode weak edges have not yet been removed; filtering and multiple-testing choices remain separate. Writing results per person saves retained memory, but does not make an individual matrix a cohort-wide regulatory input.

## Case 08：雙組學條件關聯與因果誘惑

**隱藏實驗假設：** 雙連續 omics Gaussian graphical model，兩個 layer-specific shrinkage，conditional association 不是因果。

**候選差異範圍：** DRAGON、COBRA、PANDA。

- **T1：** 確認 paired samples、資料型態與要 marginal/conditional/causal 哪種關係。
- **T2：** 推薦 run_dragon；partial correlation accounting for modeled features，區分 COBRA sample-covariate decomposition 與 TF prior regulation。
- **T3：** 樣本集合證明相同後才按 ID 對齊；lambda1/lambda2 留空可資料驅動估計，手動需兩者同時提供；missing/non-finite 阻擋，預處理不隱式執行。
- **T4：** 拒絕三層一次執行、獨立第三個 cross-layer penalty 與因果箭頭；可討論三次 pairwise 分析但不等同 joint three-layer model，需確認新 estimand。

**輸入／確認需求：** 恰好兩個 sample×feature 連續 numeric tables，header/unique IDs/finite complete values，sample set 相等、分層 feature names；評估近似 Gaussian 假設與前處理。

**預期輸出：** aggregate undirected partial-correlation network，layer-qualified IDs；edge export 的 partial_correlation/precision，不是 sample-specific 或 causal graph。

**Workflow：** 資料/假設驗證→兩層 DRAGON（估計兩個 shrinkage）→within/cross-layer conditional association 解讀；三層要求需新方案。

**Critical failures：**

- 蛋白質資料當 PPI
- 按 row position 對齊
- 自行填 missing values
- 杜撰 lambda_inter 或三層 API
- conditional correlation 當因果

**合格最終回覆示例（英文；仍须配合前輪完整解釋）：**

> DRAGON estimates a two-layer conditional-association network with two layer-specific shrinkage parameters. I would align the paired measurements by sample ID and estimate both parameters from the data. The registered workflow cannot fit three layers or an independent third penalty, and its edges do not establish causal direction.

## Case 09：稀疏事件、功能相似與病人亞型

**隱藏實驗假設：** somatic mutations 經 gene-length/patient-burden/pathway representation normalization 聚合；分群單位是病人。

**候選差異範圍：** SAMBAR、CONDOR、PANDA；不可因 functional score 與 module 字眼互換。

- **T1：** 詢問問題是 somatic alterations 還是 expression，與分組單位是病人還是網路節點，不能 T1 過早唯一選擇。
- **T2：** 推薦 run_sambar，說明 gene length 與 patient mutation burden normalization，列長度/基因集合/功能成員證據需求。
- **T3：** cluster=false，只規劃 gene/pathway mutation scores；說明 pathway size/gene repeated representation 校正。輸出沒有 cluster assignment，不能提前命名亞型。
- **T4：** 更新 cluster=true,kmin=2,kmax=4，驗證至少4樣本與區間合法，不保证某 k 最佳；拒絕 pathway mutation scores 直接當 TF→gene inference input。

**輸入／確認需求：** sample×gene nonnegative somatic mutation values；單列 gene-column positive exon lengths；cancer gene list；pathway membership GMT。四者 gene overlap 非空；分群2≤kmin≤kmax≤n。

**預期輸出：** T3: mt_out.csv gene mutation scores、pt_out.csv pathway×sample scores、manifest。T4 加 dist_matrix.csv、clustergroups.csv；不是 TF→gene regulation。

**Workflow：** 驗證→SAMBAR normalization/pathway scoring（不分群）→啟用距離/cluster range→後續 subtype interpretation；GRN 另需 expression/priors。

**Critical failures：**

- 突變當 expression
- 分群工具選 CONDOR
- cluster=false 虛構 labels
- 把 pathway score 直接餵 PANDA
- 宣稱2-4群必有最佳答案

**合格最終回覆示例（英文；仍须配合前輪完整解釋）：**

> SAMBAR matches the somatic-event hypothesis and the need to account for gene length, mutation burden and pathway representation. I would first return scores without clustering, then enable the requested cluster range after checking sample count. Those mutation scores are not regulatory-network inputs.

## Case 10：找群落的歧義與資料角色衝突

**隱藏實驗假設：** 社群分析依賴既有二分圖，role identity 與 file content 大於名字/前輪假定。

**候選差異範圍：** CONDOR、SAMBAR、DRAGON；infer 與 analyze 必須分辨。

- **T1：** 必須追問被分組的 entity 與資料是 measurement 還是已有 edges；不唯一選工具。
- **T2：** 推薦 run_condor；消費已驗證 bipartite edges，不冗餘呼叫 PANDA/OTTER。
- **T3：** 揭露 source/target ID overlap，要求明確可追溯的 role namespace/映射後再驗證；不靜默改名、不合併兩側、不任意切分單層圖。
- **T4：** 撤回 ready/可執行的 CONDOR 計畫；measurement 非 edge list，名稱不能覆蓋內容。追問量測型態及是否先推論/另提供既有網路；不可假裝 transpose 就是轉 edges。

**輸入／確認需求：** source,target 與 optional numeric weight edge list，真實雙側語意、duplicate/weights/ID checks；overlap 要先解決身份 namespace。T4 沒有這些證據，needs_input 或重新澄清。

**預期輸出：** 每個 network 的雙側 community assignments；不是病人 labels。T4 不應新產生任何 network/community artifact。

**Workflow：** 已有 edges→角色/內容驗證→CONDOR；若內容是 measurements，停在缺少 network，重新確定上游推論需求。

**Critical failures：**

- T1 猜定工具
- T2 重推論已存在網路
- 重名節點合併
- 任意雙分單層圖
- T4 相信檔名並執行
- 測量矩陣轉置就當 edges

**合格最終回覆示例（英文；仍须配合前輪完整解釋）：**

> The inspected content changes the plan: these are patient measurements, not the bipartite relationships CONDOR requires. I would stop this community step and clarify the measurement type or obtain a validated existing network. A result-like label does not establish the input’s role.

## 依據與版本邊界

工具契約以建立時 checkout 的 `scripts/workflow_registry.py`、`workflows/*.yaml` 與 `AGENTS.md` 為準；重點是本 agent 的註冊能力，不是上游所有可能的功能。

演算法背景參考 [netZooPy 官方儲存庫](https://github.com/netZoo/netZooPy)。具體 BONOBO conditional outputs、COBRA intercept artifact、OTTER 註冊粒度與 DRAGON controls 由本地契約核對；這些 adapter 限制不是對演算法所有可能實作的通用限制。

Codebase graph generation 為 `2026-09-21T13:19:20Z`。Coverage 指出 registry 的 filesystem metadata 已變更，graph snippet 的位置也未對應當前 source，因此已直接讀取當前 registry 的相關 action blocks；沒有依過時 snippet 推論能力。此工作沒有重建索引或修改 agent。

本測試未跑模型或生物分析，因此不報 accuracy，也不預填 edge weights、群落數、最佳 k、effect sizes 或 p-values。
