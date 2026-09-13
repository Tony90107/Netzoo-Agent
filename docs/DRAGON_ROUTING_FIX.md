# DRAGON routing 修復紀錄

- 日期：2026-09-13
- 分支：`evidence-contract-grounding`
- 程式碼提交：`6ff8713e45fe180794ff6b69819a6e14735fb289`
- 範圍：NetZoo agent 的 workflow guidance/routing；沒有讀取病患資料，也沒有執行 DRAGON 統計分析。

## 結論

使用者的問題定義是清楚且科學上與 DRAGON 對應的：同一批樣本的兩個已配對、連續 omics layers，想估計 aggregate、two-layer Gaussian Graphical Model (GGM) 的 precision matrix 與 partial-correlation network，並區分 intra-omics 與 inter-omics conditional associations。這個需求不是 PANDA/PUMA 類的 TF-gene regulatory prior workflow，也不是 causal inference。

修復後，這段 guidance request 已能穩定得到：

```text
Selected path: DRAGON
Workflow: infer an aggregate two-layer multi-omic Gaussian graphical model
Required inputs: omics_layer_1, omics_layer_2
Guidance only: no execution
```

輸出中的 `expression_matrix` 是 routing ontology 中「一種具體的 measured omics input」標籤，不代表第二層 methylation 被誤認成 expression。真正執行時仍然需要兩個分開的 layer files：`omics_layer_1` 與 `omics_layer_2`。

## 問題與根因

原本的 semantic interpreter 已正確產生大致如下的 outcome：

```text
operation: infer
input_artifacts: [expression_matrix]
artifact_type: multi_omic_network
granularity: aggregate
```

但 `run_dragon` 的 registry capability 只宣告 `measurement_dataset`。因此 outcome matching 把使用者明確說出的 RNA-seq expression matrix 視為未被 DRAGON capability 接受的具體輸入，最後產生 `ambiguous`，並退回「請選擇 result type」的泛化追問。這是 capability ontology 不完整，不是使用者的研究問題不清楚，也不是 DRAGON 演算法失敗。

這裡沒有把 `methylation_matrix` 硬塞進 registry，因為目前 agent 的公開 artifact vocabulary 沒有可驗證的 methylation-specific input type；而且 guidance 階段只需要辨識「兩個 measured omics layers」。執行階段的輸入契約仍負責驗證兩個檔案是否真的存在、配對且可轉成數值矩陣。

## 做了什麼改動

### 1. 對齊 typed registry capability

在 [`scripts/workflow_registry.py`](../scripts/workflow_registry.py) 的 `run_dragon` output capability 中，將輸入能力由單一 generic artifact 擴充為：

```python
input_artifacts=frozenset({"measurement_dataset", "expression_matrix"})
```

這表示 `expression_matrix` 是 `measurement_dataset` 的一個 routing-level concrete form。它只擴充語意匹配，不改變 DRAGON executor 的參數、資料運算或輸出格式。

### 2. 同步 YAML workflow contract

在 [`workflows/dragon.yaml`](../workflows/dragon.yaml) 將相同契約寫入：

```yaml
input_artifacts: [measurement_dataset, expression_matrix]
```

Registry 與 YAML 必須同步，否則可能出現「靜態 workflow 文件說可以、runtime registry 說不可以」的漂移。

### 3. 補上最小可重現 regression test

在 [`tests/test_outcome_matching.py`](../tests/test_outcome_matching.py) 新增
`test_guidance_with_current_rnaseq_input_routes_to_dragon`。測試使用目前實際會產生的 outcome：

- `operation = infer`
- `input_artifacts = [expression_matrix]`
- `artifact_type = multi_omic_network`
- `granularity = aggregate`
- `request_mode = guidance`

並要求結果必須是 `status == "exact"` 且 `matched_actions == ["run_dragon"]`。這個測試直接鎖定本次回歸點，不依賴模糊的字串搜尋或人工觀察 UI。

### 4. 補強整合文件的科學與執行邊界

在 [`docs/DRAGON_INTEGRATION.md`](../docs/DRAGON_INTEGRATION.md) 明確區分：

- routing 時可用 `measurement_dataset` 或其具體形式 `expression_matrix`；
- execution 時仍需兩個獨立的 `omics_layer_*` 檔案；
- rows 必須是 samples、columns 必須是 features，兩層 sample IDs 必須完全相同；
- 不會默默做 imputation、log transform 或 normal transform；
- output 是 aggregate、undirected association network，不是 causal graph。

## 為什麼這個修復在科學與軟體契約上是合理的

DRAGON 的原始方法是針對「同一批觀測的兩個 paired omics layers」建立聯合 GGM。對聯合資料向量 `X`，GGM 使用 covariance matrix `Σ` 的 inverse：

\[
\Theta = \Sigma^{-1}
\]

在 Gaussian 假設下，precision matrix 中的零元素對應到給定其他變數後的 conditional independence；非零元素則形成無向 conditional-dependence network。partial correlation 可由 precision matrix 的標準化 off-diagonal 元素取得。這正好對應使用者要求的 intra-layer 與 inter-layer conditional associations。

DRAGON 論文也明確描述：它同時使用兩個 omics layers、假設 paired samples，並以 layer-specific shrinkage parameters \(\lambda_1\) 與 \(\lambda_2\) 處理不同 omics layer 的尺度、feature size 與 edge-density 特性。高維情境下，sample covariance 可能 singular 或不穩定；shrinkage 讓 covariance 更適合反矩陣化。這也是 registry 中 `lambda1`、`lambda2` 與 DRAGON workflow controls 存在的統計理由。

本次 patch 沒有改動上述 estimator。它只修正「研究問題已被解析成 `expression_matrix` 時，registry 是否承認這是 DRAGON 可接受的 measured omics input」這個軟體邊界。因此它不會把 correlation 變成 causation，也不會把 methylation 當作先驗網路；它只讓正確的科學方法可以被正確選出來。

執行分析前仍須注意 Gaussian GGM 的資料假設：RNA-seq 與 beta-value 的原始尺度不一定近似 multivariate normal。DRAGON 原文指出可先使用適當的 continuous-data transformation（例如 nonparanormal transformation）使資料近似 Gaussian；agent 不會替使用者默默做這一步。兩層也必須以 sample ID 正確配對，不能只依照檔案列順序假設配對。

## 量化驗證

### Routing 行為

| 指標 | 修復前 | 修復後 |
|---|---:|---:|
| semantic outcome | 已產生 | 已產生 |
| `input_artifacts` | `expression_matrix` | `expression_matrix` |
| DRAGON accepted input artifacts | `measurement_dataset` | `measurement_dataset`, `expression_matrix` |
| outcome matching status | `ambiguous` | `exact` |
| matched action | `[]` | `[run_dragon]` |
| guidance action | `[]` | `[run_dragon]` |
| analysis execution | 0 次 | 0 次 |

修復後直接 replay 同一份 saved session，得到 `status=exact`、`matched_actions=["run_dragon"]`、`guidance_actions=["run_dragon"]`。這證明修復發生在預期的 capability matching seam，而不是靠 fallback 硬編一個 DRAGON 回覆。

### 測試與提交統計

- DRAGON/registry/policy/outcome matching 相關測試：`19 passed, 1 warning`。
- 擴大的 registry/matching filtered run：`25 passed, 42 deselected, 1 warning`。
- 完整 suite 在首次 failure-fast 執行中：`216 passed, 14 skipped, 1 failed, 2 warnings`，耗時約 `6.61 s`；失敗點是既有 semantic-review 行為測試 `test_a_reading_that_resolves_a_capability_still_skips_it`，不是本次 DRAGON matching regression test。該 failure 不應被誤報為「全 suite 綠燈」。
- `git diff --check`：本次相關檔案無 whitespace error。
- 程式碼提交：`62 files changed, 3522 insertions(+), 70 deletions`。這個 commit 包含本輪 working tree 中累積的 typed contracts、policy/planning、handoff、Bonobo 與多個 workflow/test 變更；上面的 DRAGON routing patch 是其中針對本次對話的最小修復。

## 對最新對話結果的判讀

最新結果是正確的 workflow guidance：

1. 語意解析成功，抓到 `infer + aggregate + multi_omic_network`。
2. registry matching 成功選到 `DRAGON`。
3. 產生的 required inputs 是兩個 omics layers，而不是 motif/PPI prior。
4. `lambda1`、`lambda2` 與 `output_format` 被列為 controls，符合 DRAGON 的兩層 shrinkage 與輸出需求。
5. 系統明確說明沒有執行分析，符合使用者的授權範圍。

因此，這一輪的核心問題已修復。若下一步要真的執行，應另行確認兩個檔案的 sample-ID 對齊、特徵數與樣本數、缺失值、連續性與近似 Gaussian preprocessing；那是資料與統計 validity 檢查，不應在 workflow selection 階段假裝已完成。

## 參考資料

1. Shutta et al., *DRAGON: Determining Regulatory Associations using Graphical models on multi-Omic Networks*, [PMC full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC9943674/)；方法中說明 precision matrix、conditional independence、paired two-layer data、covariance shrinkage、partial correlation 與 observational undirected limitation。
2. Shutta et al., [arXiv version](https://arxiv.org/abs/2104.01690)；摘要與 simulation 結果說明 DRAGON 對 paired multi-omic GGM、layer-specific regularization 與 edge recovery 的設計。
3. [Official netZooPy repository](https://github.com/netZoo/netZooPy)；NetZooPy 的官方套件與 DRAGON 入口說明。
4. Ledoit & Wolf, *A well-conditioned estimator for large-dimensional covariance matrices*, [Journal of Multivariate Analysis DOI](https://doi.org/10.1016/S0047-259X(03)00096-4)；說明高維 covariance shrinkage 對可逆性與條件數的動機。
