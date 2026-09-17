# Expanded gene-identifier prompts

這組 prompt 用來擴充 gene-label validation 的測試範圍：多物種、Ensembl gene IDs、NCBI Gene IDs、舊 symbol、alias、大小寫變化、版本後綴與不同錯字型態。

## 使用規則

- 下面的「貼給 agent 的 prompt」只描述一般 PANDA 工作，不揭露真正測試的 identifier 類型。
- 「測試者觀察」不要貼給 agent。
- 每個案例建議使用新 cache，避免前一個案例的 cache hit 掩蓋 taxon ambiguity 或 authority 狀態。
- Docker 互動模式使用 `/work/...` 路徑；若直接在 host 執行，請將 `/work` 換成 repository 根目錄。
- 除了 synthetic typo case 外，優先使用 strict/Planning mode。只有想測試軟體流程而非生物學存在性時才輸入 `/test`。

```bash
export NETZOO_GENE_CACHE_PATH="/tmp/netzoo-ge-$(date +%s).sqlite3"
./netzoo-chat
```

## Prompt 1：跨物種與 taxon disambiguation

現有 fixture：`manual_tests/gene_validation_flow/taxon_ambiguous/`。

### 貼給 agent 的 prompt

```text
請執行 PANDA 的 dry-run，目標是 aggregate TF-to-gene regulatory network。
請先完成 input preflight，檢查 schema、gene namespace，以及 expression、motif、PPI 的對應關係。
僅產生 dry-run，不進入實際分析階段；不要輸入 /execute。

expression_file=/work/manual_tests/gene_validation_flow/taxon_ambiguous/expression.tsv
motif_file=/work/manual_tests/gene_validation_flow/taxon_ambiguous/motif.tsv
ppi_file=/work/manual_tests/gene_validation_flow/taxon_ambiguous/ppi.tsv
output_file=/work/outputs/manual/gene_existence/multi_species.tsv
```

### 測試者觀察

- 未指定物種時，`QSOX1` 應呈現 `ambiguous` 或要求補充 taxon，不應直接說 gene 不存在。
- 接著可另開一輪，加入 `taxon=Homo sapiens`，預期 ambiguity 消失並通過 preflight。
- 可記錄：`ambiguous_count`、`taxon_required_count`、指定物種後的 `valid_count`。

## Prompt 2：Ensembl gene IDs 與跨 namespace canonical matching

現有 fixture：`manual_tests/gene_validation_flow/valid_canonical_match/`。

### 貼給 agent 的 prompt

```text
請執行 PANDA 的 dry-run，目標是 aggregate TF-to-gene regulatory network。
請先完成 input preflight，並在檢查結果中列出每個輸入軸的 identifier status、canonical gene ID 與資料來源。
僅產生 dry-run，不進入實際分析階段；不要輸入 /execute。

expression_file=/work/manual_tests/gene_validation_flow/valid_canonical_match/expression.tsv
motif_file=/work/manual_tests/gene_validation_flow/valid_canonical_match/motif.tsv
ppi_file=/work/manual_tests/gene_validation_flow/valid_canonical_match/ppi.tsv
taxon=Homo sapiens
output_file=/work/outputs/manual/gene_existence/ensembl_canonical.tsv
```

### 測試者觀察

- expression 與 PPI 使用 Ensembl gene IDs，motif 使用 symbols；應透過 canonical gene ID 完成匹配。
- 應通過 `3/3` expression genes 的 authority validation，以及 motif target／PPI regulator 的跨檔案匹配。
- 不應把 Ensembl transcript ID 當成 gene ID。
- 可記錄：`ensembl_valid_count`、`canonical_match_count`、`cross_file_overlap_rate`。

## Prompt 3：NCBI Gene numeric IDs

此案例需要先建立一組 NCBI-ID fixture，例如：

- expression gene IDs：`7157`、`4609`、`4149`。
- motif：使用相同 numeric IDs 作為 regulator 與 target。
- PPI：使用 `4609` 與 `4149`。
- 指定 `taxon=9606`。

建議路徑：`manual_tests/gene_existence_extended/ncbi_ids/{expression,motif,ppi}.tsv`。這些檔案目前不是 repository 既有 fixture，建立後再貼下列 prompt。

### 貼給 agent 的 prompt

```text
請執行 PANDA 的 dry-run，目標是 aggregate TF-to-gene regulatory network。
請先完成 input preflight，確認三個檔案中的 identifiers 可以互相匹配，並回報每個輸入軸的 validation status。
僅產生 dry-run，不進入實際分析階段；不要輸入 /execute。

expression_file=/work/manual_tests/gene_existence_extended/ncbi_ids/expression.tsv
motif_file=/work/manual_tests/gene_existence_extended/ncbi_ids/motif.tsv
ppi_file=/work/manual_tests/gene_existence_extended/ncbi_ids/ppi.tsv
taxon=9606
output_file=/work/outputs/manual/gene_existence/ncbi_numeric.tsv
```

### 測試者觀察

- numeric labels 應走 NCBI Gene ID lookup，而不是 symbol endpoint。
- `7157`、`4609`、`4149` 若 authority 可用，應得到 `ncbi_gene:<id>` canonical records。
- 若 endpoint 不可用，狀態應是 `unverified`／authority unavailable，而不是直接判定 invalid。
- 可記錄：`ncbi_id_valid_count`、`authority_unavailable_count`、`cache_hit_count`。

## Prompt 4：舊 symbol、alias 與大小寫變化

此案例需要一組由目前 NCBI/Ensembl record 事先確認過的 fixture，例如：同一批 gene 分別以 canonical symbol、歷史 symbol、官方 synonym 與不同大小寫寫入 expression、motif、PPI。建議路徑：`manual_tests/gene_existence_extended/aliases_case/{expression,motif,ppi}.tsv`。

### 貼給 agent 的 prompt

```text
請執行 PANDA 的 dry-run，目標是 aggregate TF-to-gene regulatory network。
請先完成 input preflight，保留檔案中的原始 gene labels，並回報每個 label 的 status、canonical ID、原始寫法與 authority source；不要先替我改寫檔案。
僅產生 dry-run，不進入實際分析階段；不要輸入 /execute。

expression_file=/work/manual_tests/gene_existence_extended/aliases_case/expression.tsv
motif_file=/work/manual_tests/gene_existence_extended/aliases_case/motif.tsv
ppi_file=/work/manual_tests/gene_existence_extended/aliases_case/ppi.tsv
taxon=Homo sapiens
output_file=/work/outputs/manual/gene_existence/aliases_case.tsv
```

### 測試者觀察

- authority 支援的 alias／舊 symbol 應被保留原始 label，並映射到相同 canonical gene ID。
- 純大小寫變化不應被錯誤視為不同 gene；但若 authority 本身不承認該 alias，應明確顯示 `invalid` 或 `unverified`。
- Agent 不應只因字串相似就自行改名並放行。
- 可記錄：`alias_resolved_count`、`casefold_match_count`、`distinct_canonical_ids`、`unverified_count`。

## Prompt 5：版本後綴與多種 typo 型態

此案例需要一組混合 fixture，例如：

- 可驗證的 Ensembl gene ID version suffix，例如 `ENSG00000141510.<version>`。
- 已確認的 canonical symbol／alias。
- deletion、insertion、substitution、transposition 等 typo；每個 typo 都要先由獨立 authority lookup 或人工答案卡確認為不存在。

建議路徑：`manual_tests/gene_existence_extended/identifier_variants/{expression,motif,ppi}.tsv`。

### 貼給 agent 的 prompt

```text
請執行 PANDA 的 dry-run，目標是 aggregate TF-to-gene regulatory network。
請先完成 input preflight，逐一回報每個 identifier 的 validation status、canonical ID、authority source，以及任何需要人工處理的項目；不要自動修改輸入檔案。
僅產生 dry-run，不進入實際分析階段；不要輸入 /execute。

expression_file=/work/manual_tests/gene_existence_extended/identifier_variants/expression.tsv
motif_file=/work/manual_tests/gene_existence_extended/identifier_variants/motif.tsv
ppi_file=/work/manual_tests/gene_existence_extended/identifier_variants/ppi.tsv
taxon=Homo sapiens
output_file=/work/outputs/manual/gene_existence/identifier_variants.tsv
```

### 測試者觀察

- version suffix 若被支援，應顯示 canonical ID 的正規化結果；若不支援，應明確為 `unverified`／`invalid`，不能靜默剝除後放行。
- typo 不應因為與既有 symbol 相似而自動通過；repair hint 只能是 advisory。
- strict mode 下，至少一個真正 invalid typo 應阻擋 Work Plan；若只想檢查其餘軟體流程，可先輸入 `/test`，但結果必須標為 `test_only`，不能當作生物學證據。
- 可記錄：`version_resolved_count`、`typo_rejection_count`、`false_accept_count`、`test_only_count`。

## 建議的量化報表

每個案例至少保存以下欄位：

| 欄位 | 定義 |
| --- | --- |
| `n_labels` | 去重前或去重後的 label 數，兩者都應記錄 |
| `valid_count` | authority 明確確認存在的 labels |
| `invalid_count` | authority 明確確認不存在的 labels |
| `ambiguous_count` | 多個 taxon／canonical match 且尚未消歧的 labels |
| `unverified_count` | 因服務不可用、無 taxon 或非權威 fallback 而未能確認的 labels |
| `canonical_match_count` | 跨檔案以 canonical ID 成功匹配的 labels |
| `invalid_report_coverage` | 被回報的 invalid label occurrences / 答案卡中的 invalid occurrences |
| `false_accept_count` | strict mode 下被錯誤放行的已知 invalid labels |
| `cache_hit_count` / `online_query_count` | 可重現性與成本指標 |

若有人工答案卡，可計算描述性指標：

```text
label-level sensitivity = valid labels accepted / known valid labels
label-level specificity = invalid labels rejected / known invalid labels
invalid-report coverage = reported invalid occurrences / known invalid occurrences
false-accept rate = invalid labels accepted in strict mode / known invalid labels
```

這些數字應標示 fixture 數量、查詢日期、authority endpoint、cache 狀態與是否使用 `/test`。五個 prompt 的結果適合作為 regression／mechanism evidence，不足以宣稱跨物種或跨命名系統的普遍準確率。
