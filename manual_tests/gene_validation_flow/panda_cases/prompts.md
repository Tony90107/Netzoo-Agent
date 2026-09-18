# PANDA input-case prompts

These fixtures are intended for an authority-backed lookup, not the seeded fixture
cache. The text inside each prompt deliberately describes an ordinary PANDA
dry-run and does not reveal the test labels or expected statuses.

## Before each run

Use a new cache for each case. Because `netzoo-chat` runs inside Docker, a
container-local `/tmp` path is intentionally fresh for that run:

```bash
export NETZOO_GENE_CACHE_PATH="/tmp/netzoo-live-$(date +%s).sqlite3"
export NETZOO_GENE_ONLINE_LOOKUP=on
./netzoo-chat
```

Do not use the seeded `fixture_gene_cache.sqlite3`; that cache would hide the
live NCBI/Ensembl normalization path.

## Prompt 1 — case alpha

Paste only the following block to the agent:

```text
請執行 PANDA 的 dry-run，目標是 aggregate TF-to-gene regulatory network。
請在結果摘要中列出每個輸入軸的 identifier status、canonical gene ID、authority source，以及 expression、motif、PPI 的對應關係。
僅產生 dry-run，不進入實際分析階段；不要輸入 /execute。

expression_file=/work/manual_tests/gene_validation_flow/panda_cases/case_alpha/expression.tsv
motif_file=/work/manual_tests/gene_validation_flow/panda_cases/case_alpha/motif.tsv
ppi_file=/work/manual_tests/gene_validation_flow/panda_cases/case_alpha/ppi.tsv
taxon=Homo sapiens
output_file=/work/outputs/manual/gene_existence/panda_case_alpha.tsv
```

Tester-only expectation:

- NCBI numeric IDs in expression, symbols in motif, and Ensembl IDs in PPI are all real human genes.
- The robust expected result is `valid` for every label and canonical overlap of `4/4` targets and `2/2` TFs.
- If the current implementation reports no motif-TF/PPI overlap, that exposes the source-native `ncbi_gene:*` versus `ensembl_gene:*` canonical mismatch.

## Prompt 2 — case beta

Paste only the following block to the agent:

```text
請執行 PANDA 的 dry-run，目標是 aggregate TF-to-gene regulatory network。
請在結果摘要中逐一列出每個輸入軸的 identifier status、canonical gene ID、authority source，以及任何需要人工處理的項目；不要自動修改輸入檔案。
僅產生 dry-run，不進入實際分析階段；不要輸入 /execute。

expression_file=/work/manual_tests/gene_validation_flow/panda_cases/case_beta/expression.tsv
motif_file=/work/manual_tests/gene_validation_flow/panda_cases/case_beta/motif.tsv
ppi_file=/work/manual_tests/gene_validation_flow/panda_cases/case_beta/ppi.tsv
taxon=Homo sapiens
output_file=/work/outputs/manual/gene_existence/panda_case_beta.tsv
```

Tester-only expectation:

- `7157`, `4609`, `1956`, and `672` should be valid NCBI Gene IDs.
- `999999999` should be reported as an NCBI invalid label, not silently repaired.
- `NOTAREALGENEZZZ2026` should be reported as an invalid NCBI symbol lookup.
- `ENSG99999999999` should be reported as an invalid Ensembl gene ID.
- The valid motif targets should still have complete canonical coverage against expression; invalid labels, not a missing valid target, should be the reason strict mode blocks the plan.
- Strict mode should not produce an execution-ready PANDA plan; repair hints must remain advisory.

## Expected authority cross-checks

| Symbol | NCBI Gene ID | Ensembl gene ID |
|---|---:|---|
| TP53 | 7157 | ENSG00000141510 |
| MYC | 4609 | ENSG00000136997 |
| EGFR | 1956 | ENSG00000146648 |
| BRCA1 | 672 | ENSG00000012048 |

These identifiers were checked against current NCBI Gene records on
2026-09-17; the corresponding Ensembl stable IDs are also accepted by the
Ensembl `/lookup/id` endpoint. The run itself should still be done with live
lookup so the agent reports its own source, status, cache hits, and online query
counts.
