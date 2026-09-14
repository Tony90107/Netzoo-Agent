# Prompts

以下 prompt 使用 Docker 的 `/work` 路徑。若直接在 host 執行，將 `/work` 替換成 repository 根目錄。

## 1. Canonical matching 應該通過

```text
請執行 PANDA 的 dry-run，目標是 aggregate TF-to-gene regulatory network。
在 dry-run 前先自動執行 input preflight，檢查 schema、gene header、gene namespace，以及 expression、motif、PPI 之間的 gene matching。
僅產生 dry-run，不進入實際分析階段；不要輸入 `/execute`。

expression_file=/work/manual_tests/gene_validation_flow/valid_canonical_match/expression.tsv
motif_file=/work/manual_tests/gene_validation_flow/valid_canonical_match/motif.tsv
ppi_file=/work/manual_tests/gene_validation_flow/valid_canonical_match/ppi.tsv
output_file=/work/outputs/manual/gene_validation_flow/valid_canonical_match.tsv
```

預期：preflight 先通過，接著顯示 PANDA dry-run plan，但不可執行分析。expression 使用 Ensembl、motif 使用 symbol、PPI 使用 Ensembl，應透過 canonical gene ID 匹配。

## 2. Expression 與 motif target 衝突

```text
請執行 PANDA 的 dry-run，目標是 aggregate TF-to-gene regulatory network。
在 dry-run 前先自動執行 input preflight，特別確認 motif target 是否都存在於 expression gene 集合。
僅產生 dry-run，不進入實際分析階段；不要輸入 `/execute`。

expression_file=/work/manual_tests/gene_validation_flow/expression_motif_conflict/expression.tsv
motif_file=/work/manual_tests/gene_validation_flow/expression_motif_conflict/motif.tsv
ppi_file=/work/manual_tests/gene_validation_flow/expression_motif_conflict/ppi.tsv
output_file=/work/outputs/manual/gene_validation_flow/expression_motif_conflict.tsv
```

預期：preflight 拒絕，且不要進入 PANDA dry-run，因為 motif target 與 expression gene 沒有可接受的 exact 或 canonical overlap。

## 3. Motif TF 與 PPI 衝突

```text
請執行 PANDA 的 dry-run，目標是 aggregate TF-to-gene regulatory network。
在 dry-run 前先自動執行 input preflight，特別確認 motif 第一欄的 TF/regulator 是否出現在 PPI nodes 中。
僅產生 dry-run，不進入實際分析階段；不要輸入 `/execute`。

expression_file=/work/manual_tests/gene_validation_flow/motif_ppi_conflict/expression.tsv
motif_file=/work/manual_tests/gene_validation_flow/motif_ppi_conflict/motif.tsv
ppi_file=/work/manual_tests/gene_validation_flow/motif_ppi_conflict/ppi.tsv
output_file=/work/outputs/manual/gene_validation_flow/motif_ppi_conflict.tsv
```

預期：preflight 拒絕，且不要進入 PANDA dry-run，因為 motif TF 與 PPI node 沒有可接受的 overlap。

## 4. 明確的 invalid gene

先執行 `seed_cache.py` 並設定 `NETZOO_GENE_CACHE_PATH`，再貼上：

```text
請執行 PANDA 的 dry-run，目標是 aggregate TF-to-gene regulatory network。
在 dry-run 前先自動執行 input preflight，並確認 gene identifier 是否被 authority cache 明確標記為 invalid。
僅產生 dry-run，不進入實際分析階段；不要輸入 `/execute`。

expression_file=/work/manual_tests/gene_validation_flow/unknown_gene/expression.tsv
motif_file=/work/manual_tests/gene_validation_flow/unknown_gene/motif.tsv
ppi_file=/work/manual_tests/gene_validation_flow/unknown_gene/ppi.tsv
taxon=Homo sapiens
output_file=/work/outputs/manual/gene_validation_flow/unknown_gene.tsv
```

預期：拒絕，report 應指出 authority 不認識該 gene。

## 5. Taxon 可以消除 ambiguity

第一次不要指定物種：

```text
請執行 PANDA 的 dry-run，目標是 aggregate TF-to-gene regulatory network。
在 dry-run 前先自動執行 input preflight，並注意 QSOX1 是否有多個物種的 authority match。
僅產生 dry-run，不進入實際分析階段；不要輸入 `/execute`。

expression_file=/work/manual_tests/gene_validation_flow/taxon_ambiguous/expression.tsv
motif_file=/work/manual_tests/gene_validation_flow/taxon_ambiguous/motif.tsv
ppi_file=/work/manual_tests/gene_validation_flow/taxon_ambiguous/ppi.tsv
output_file=/work/outputs/manual/gene_validation_flow/taxon_ambiguous.tsv
```

預期：可以看到 `ambiguous` warning；如果其他輸入都通過，agent 仍可能顯示 PANDA dry-run plan，但不會自動執行分析。

接著指定 human：

```text
請用 `Homo sapiens` 作為 taxon，執行 PANDA 的 dry-run，目標是 aggregate TF-to-gene regulatory network。
在 dry-run 前先自動執行 input preflight；僅產生 dry-run，不進入實際分析階段；不要輸入 `/execute`：

expression_file=/work/manual_tests/gene_validation_flow/taxon_ambiguous/expression.tsv
motif_file=/work/manual_tests/gene_validation_flow/taxon_ambiguous/motif.tsv
ppi_file=/work/manual_tests/gene_validation_flow/taxon_ambiguous/ppi.tsv
taxon=Homo sapiens
output_file=/work/outputs/manual/gene_validation_flow/taxon_ambiguous_human.tsv
```

預期：QSOX1 變成 valid，且不再出現跨物種 ambiguity。

## 6. Cache hit

在同一個 cache 設定下，再次貼上第 1 個 prompt。

預期：report 應該顯示 cache hit；不需要為相同 identifier 再次呼叫 Websearch。

## 7. Cache miss 時的 Websearch fallback

這個案例需要已設定 Websearch MCP。請先把 `NETZOO_GENE_CACHE_PATH` 指向一個新的空 SQLite 路徑，而且該路徑要在 repository mount 內，例如 `/work/.netzoo/empty-gene-cache.sqlite3`，並設定：

```bash
export NETZOO_GENE_ONLINE_LOOKUP=always
```

然後貼上第 1 個 prompt。

預期：agent 會對 cache miss 做 bounded online lookup；若可信搜尋結果能精確對應，report 會出現 valid；若搜尋服務沒有回傳足夠證據，應該是 `unverified` warning，而不是直接宣稱 invalid。
