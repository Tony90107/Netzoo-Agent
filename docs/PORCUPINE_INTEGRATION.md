# PORCUPINE integration

PORCUPINE (kuijjerlab/PORCUPINE, Belova et al.) finds pathways whose
TF-to-gene regulation varies in a coordinated way across a population of
sample-specific networks. It is an R package, not part of netZooPy. It runs in
the image's `netzoo-r` environment, pinned to commit
`96d68c057803473b0a1ee76631c7c0c78872d04c` (`PORCUPINE_REF` in the Dockerfile).

## Where it sits

```
expression + motif + PPI ──LIONESS-PANDA / LIONESS-PUMA──▶ edges x samples table ──PORCUPINE──▶ pathway statistics
                                                             (sample_network_file)   + GMT       + PC1 sample scores
```

`run_lioness_panda` and `run_lioness_puma` declare `handoff_targets: [run_porcupine]`.
PORCUPINE does not build networks. An aggregate PANDA/PUMA network, a
co-expression network (LIONESS co-expression, BONOBO) or an expression matrix
is not a valid input.

## Input contract (`scripts/porcupine_io.py`)

| Role | Format |
| --- | --- |
| `sample_network_file` | Delimited text with a header. **Rows = unique regulator→target edges, columns = samples.** First column `tf`/`regulator`, second `gene`/`target`, an optional third column `prior`/`prior_weight`/`motif` (an edge annotation, not a sample), then one column per unique sample ID. All values must be finite numbers. This is exactly what netZooPy LIONESS-PANDA writes (`tf gene <samples>`) and what the harness writes for LIONESS-PUMA (`regulator gene prior_weight <samples>`). |
| `pathway_file` | GMT: `pathway<TAB>description<TAB>gene…`, unique pathway names, gene IDs in the same namespace as the network target column. |
| `output_dir` | Directory for the artifacts below. |

These are rejected before anything runs:
- gene-gene tables (`gene1 gene2`);
- binary `.npy`/`.mat`/`.h5` LIONESS exports, which have no edge labels;
- duplicate edges or sample IDs;
- non-numeric values;
- fewer than 8 samples;
- a GMT whose genes match no network target (for example symbols against Ensembl IDs);
- no pathway inside `min_pathway_size..max_pathway_size`.

## Preparation step (`scripts/run_porcupine.py`)

1. The labelled table is parsed and validated, and the prior column is dropped.
2. With `scale_data=true`, edges that are constant across samples are dropped (they cannot be scaled), and the count is recorded in the manifest.
3. A `regulator, target, <samples>` TSV is written to a private staging directory and handed to `scripts/porcupine_run.R`.

## R run (`scripts/porcupine_run.R`)

`load_gmt`, then a gene filter equivalent to `filter_pathways`, then
`filter_pathways_size`, `pca_pathway`, random gene sets from the internal
`create_gene_set` (in place of `pca_random`, see below), `porcupine`, BH
adjustment, `get_pathway_ind_scores` and `get_pathway_features_scores`.

The upstream `filter_pathways` depends on plyr's internal column name
`X..i..`, so the same filter (keep the pathway genes that are network targets,
drop empty pathways) is written in base R. `pca_random` is replaced by drawing the
random gene sets with the package's internal `PORCUPINE:::create_gene_set` and running
`pca_pathway` on them. Every other step calls the package's exported functions. The R script uses the `L'Ecuyer-CMRG` generator and draws every random
gene set with `set.seed(seed)` before any PCA runs, so the null gene sets are the same for any `n_cores`
(upstream `pca_random` draws them between PCA calls, where irlba's random start shifts the stream when
`n_cores` is 1). irlba's start vectors differ by worker, which moves PC1 variances only within the solver's
convergence tolerance.

## Controls

| Control | Default | Meaning |
| --- | --- | --- |
| `min_pathway_size` / `max_pathway_size` | 5 / 150 | Pathway size range, counting genes found among network targets; at least 4, because the PCA (irlba, 3 components) needs 4 edges |
| `n_permutations` | 1000 | Random gene sets per distinct pathway size; runtime grows linearly with it |
| `n_cores` | 1 | `mc.cores` for the per-pathway PCA |
| `scale_data` | true | Scale each edge to unit variance (centering is always on) |
| `fdr_threshold` | 0.05 | A pathway is significant when padj < fdr_threshold … |
| `min_effect_size` | 2.0 | … and Cohen's d > min_effect_size. The upstream README's example uses padj <= 0.01, PC1 variance >= 10% and effect size >= 2; these defaults are looser on FDR and have no PC1 filter |
| `seed` | 1 | Seed for the random gene sets |

## Outputs (all TSV, checked by `validate_porcupine_output`)

| File | Orientation |
| --- | --- |
| `porcupine_pathways.tsv` | One row per tested pathway. Columns: `pathway, pathway_size, n_edges, pc1_variance_pct, null_mean_pc1_variance_pct, pvalue, padj, effect_size, significant`. Sorted by padj. |
| `porcupine_random_null.tsv` | One row per random gene set: `pathway_size, n_edges, pc1_variance_pct` |
| `porcupine_pc1_sample_scores.tsv` | **Rows = pathways, columns = samples** (same IDs and order as the input). PC signs are arbitrary. |
| `porcupine_edge_loadings.tsv` | `pathway, regulator, target, pc1_loading, pc2_loading`, for significant pathways only |
| `manifest.json` | Inputs, parameters, package ref, input summary and the orientation of each file |

## Verified

- Unit and contract tests: `tests/test_porcupine_workflow.py`.
- Toy bundle `data/porcupine-toy`: 600 edges × 12 samples with one planted pathway. Only that pathway is significant (padj ≈ 1e-47, d ≈ 8.7).
- Real chain in the image: `run-lioness panda` on `data/official-toy` (1000 genes × 50 samples) produced an 87,000-edge × 50-sample LIONESS-PANDA table. The agent's `run_porcupine` executor ran it unchanged with PORCUPINE's Reactome GMT: 225 pathways tested, 5 significant, and every artifact passed the contract.

## Runtime note

The cost is about (number of distinct pathway sizes × `n_permutations` + number of pathways) truncated PCAs. For a genome-scale LIONESS network (about 600 TFs × 18k genes, 11M edges), the input checks stream the table in 200,000-edge chunks and keep only the edge labels, and the runner streams it into R's input file the same way, so Python stays at a few GB; R then holds the edge-by-sample matrix in memory (11M edges × 50 samples is about 4.4 GB as doubles). Use `n_cores`, and lower `n_permutations` while exploring.
