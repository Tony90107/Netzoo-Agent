# DRAGON routing validation and semantic-repair record

日期：2026-09-13
範圍：NetZoo agent 的 guidance-only workflow selection  目標 workflow：`run_dragon`

## 摘要

這次修補處理的是兩個不同的 routing failure，而不是把所有含有
`omics`、`miRNA` 或 `precision` 的問題直接導向 DRAGON：

1. 語意 interpreter 將「詢問哪個 workflow」誤判成空的
   `explain/not_applicable` 結果，因而無法保留使用者真正描述的多體學網路目標。
2. semantic reviewer 將「150 個病患樣本」誤放成 network node：
   `entity_type=sample`。這會讓本來可由 DRAGON 處理的 feature network 變成不相容，
   並在 repair 過程中移除 `gene`/`mirna` feature labels。

修補後，兩個 live CLI smoke tests 都回傳唯一的 `DRAGON` path，且沒有執行分析。

## 問題重現與證據

### Case A：paired transcriptomics + metabolomics

Trace：`315c30af-73c2-4709-95a6-f4af7b08856a`

| routing event | 觀察 |
|---|---|
| semantic interpretation rejected | `inconsistent_not_applicable_outcome` |
| accepted evidence dimensions | 只有 `operation` |
| discriminator | `candidate_count=12`，provider 回傳空 `selection_tags` |
| registry match | `status=ambiguous`，`matched_actions=[]`，`hypothesis_actions` 包含全部 12 個 workflow |

因此畫面列出 PANDA、PUMA、LIONESS、CONDOR、COBRA、SAMBAR、DRAGON、OTTER、
GIRAFFE、BONOBO 等所有候選，並詢問 aggregate 或 sample-specific。這不是 DRAGON
能力缺失，而是 terminal scientific result 沒有被語意層保留下來。

### Case B：150 paired tumor samples 的 mRNA + miRNA

Trace：`f42d4793-21d6-4e29-bcd2-a66a9bdb2da0`

| routing event | 觀察 |
|---|---|
| first validation | `missing_evidence:entity_type=sample` |
| repair patch | `entity_types` 被改成 `sample`，並移除 `gene`/`mirna` evidence |
| deterministic restoration | 只清除非 regulatory artifact 的 stale roles |
| registry match | `status=ambiguous`，`hypothesis_actions=[]`，無法保留 DRAGON |

這裡的 `sample` 是觀測單位，不是 network vertex。因而問題不是「miRNA 必須走
PUMA」，而是 output entity schema 被錯誤解讀。

## 實作變更

### 1. 強化 semantic ontology mapping

檔案：`scripts/netzoo_agent_core/llm.py`

新增明確的語意契約：

```text
paired continuous omics
+ joint precision-matrix / partial-correlation / conditional-dependency network
→ operation=infer
→ artifact_type=multi_omic_network
→ granularity=aggregate，除非使用者明確要求每個 sample 各自推論一張 network
```

同一條規則也說明：

- transcriptomics、metabolomics、methylation、mRNA、miRNA 是 measurement layers，
  不是 network `entity_type` 的 assay 名稱。
- `gene`、`mirna`、`protein`、`metabolite` 可以是 feature labels，不能因此被放進
  `regulator_types` 或 `target_types`。
- 「沒有 motif/sequence prior」是排除 prior-dependent regulatory workflows 的負向
  constraint，不是 input artifact，也不會把 output 變成 regulatory network。
- cohort size 或 sample index 不會產生 `entity_type=sample`；network nodes 是 omics
  features。

semantic reviewer 與 field-scoped patch prompt 也加入相同 mapping。當 validator
偵測到 `inconsistent_not_applicable_outcome` 時，repair feedback 會針對符合
multi-omic + precision/conditional-dependency 語意的請求提供
`multi_omic_network` recovery rule。

### 2. 擴大既有 bounded semantic normalization

檔案：`scripts/netzoo_agent_core/interpretation/stated_field_restoration.py`

既有 normalization 已處理 sample-specific co-expression：sample 是選樣本條件，
不是 gene-gene matrix 的 node。這次將同一個 ontology boundary 擴展到
`multi_omic_network`：

- 僅移除誤放的 `sample` entity；保留現有 feature labels。
- 同步移除對應的 `entity_type=sample` evidence，避免 stale evidence 重新觸發
  validation。
- 不新增 artifact、workflow、selection tag，也不根據字詞直接呼叫 DRAGON。
- 若仍為 sample-specific granularity，仍會保留該 granularity；normalization 不會
  把 sample-specific 偷改成 aggregate。

### 3. 回歸測試

新增／更新：

- `tests/test_workflow_reasoning_prompts.py`
  - 驗證 joint precision / partial-correlation / conditional-dependency 的 canonical
    mapping。
  - 驗證 reviewer recovery feedback 含有 multi-omic recovery rule。
- `tests/test_stated_field_restoration.py`
  - 驗證 `sample` 從 multi-omic network node 移除、feature labels 保留、evidence
    同步清除。
  - 驗證 normalization 後 typed matcher 的結果是唯一 `run_dragon`。

## 為什麼這樣符合科學模型

對兩層 feature vector `X=(X_1, X_2)` 的 Gaussian graphical model，令

\[
\Sigma = \operatorname{Cov}(X), \qquad \Theta = \Sigma^{-1}.
\]

若把 precision matrix 寫成 block matrix：

\[
\Theta =
\begin{bmatrix}
\Theta_{11} & \Theta_{12}\\
\Theta_{21} & \Theta_{22}
\end{bmatrix},
\]

則 `Theta_11` 與 `Theta_22` 對應 layer 內的 conditional associations，
`Theta_12`/`Theta_21` 對應跨 layer associations。對變數 `i`、`j`，

\[
\rho_{ij\mid rest}
= -\frac{\Theta_{ij}}{\sqrt{\Theta_{ii}\Theta_{jj}}}.
\]

在 Gaussian 假設下，精度矩陣的零元素對應在其餘變數條件下的 conditional
independence；因此這種網路是無向 statistical association network。它不等於
causal graph，也不保證僅靠一次估計就證明「所有」間接效應已被排除。

病患是 row/observation，gene、miRNA、metabolite 等是 column/feature。`150`
是 sample size `n=150`，不是一個應加入 precision matrix 的 vertex。這也是
`entity_type=sample` normalization 的科學依據。

DRAGON 的原始方法是針對兩個 paired omics layers 的 multi-omic GGM，並依據各層
feature size、noise 與 edge-density characteristics 校準 shrinkage；agent contract
因此把 `lambda1` 與 `lambda2` 宣告成兩個 layer-specific controls。它們不是一個
任意的 full block-wise Graphical Lasso penalty matrix，也不代表 contract 中存在
可獨立調整的第三個 `lambda_inter`。

## 驗證結果

### Deterministic tests

```text
pytest -q tests/test_workflow_reasoning_prompts.py tests/test_stated_field_restoration.py
37 passed, 1 warning
```

### Live CLI smoke tests

使用與兩個失敗案例科學語意等價的 guidance-only prompts，沒有提供 input files，
也沒有執行 analysis：

| smoke trace | 結果 | semantic attempts |
|---|---|---:|
| `afebcec2-b0b3-49f8-bbce-49b79eee95db` | `matched_actions=[run_dragon]`, `status=exact` | 1 |
| `2232601c-6162-4a5d-9a0a-7440d5c88878` | `matched_actions=[run_dragon]`, `status=exact` | 2（bounded repair 後通過） |

Live success rate：`2/2 = 100%`（本次 smoke sample，非科學效能 benchmark）。

### 非本次變更的 broader-suite 狀態

本機 host 直接執行完整 suite 時，focused tests 之外仍有既有環境／contract failures，
包括未載入 container-only runnable tools、舊 schema digest，以及既有 semantic-review
scope test。這些 failure 不涉及本次修改的五個檔案，不能宣稱整個 repository 已
完全綠燈；本次修補的可重現 routing scope 已由上面的 37 tests 與 live traces 覆蓋。

## 限制與不應過度解讀的地方

1. 這是 workflow selection 與 semantic repair 的修補，不是改變 DRAGON 的統計估計器。
2. DRAGON contract 目前支援兩層輸入；三層以上、任意 block-specific penalty matrix、
   或獨立 `lambda_inter` 仍應被明確說成超出已註冊 contract。
3. `aggregate` 表示 cohort-level joint network；它不代表每個 sample 沒有 row/column
   metadata，而是代表沒有對每個 sample 分別估計一張 network。
4. `multi_omic_network` 的 route 命中不等於 data 已通過 shape、sample-ID pairing、
   missingness 或 scale normalization validation；那些只會在使用者授權 execution
   並提供輸入後檢查。

## 參考資料

- [netZooPy official repository](https://github.com/netZoo/netZooPy)
- [DRAGON: Determining Regulatory Associations using Graphical models on multi-Omic Networks](https://pmc.ncbi.nlm.nih.gov/articles/PMC9943674/)
- [DRAGON preprint](https://arxiv.org/abs/2104.01690)
- [Gaussian graphical models with applications to omics analyses](https://pmc.ncbi.nlm.nih.gov/articles/PMC9672860/)
