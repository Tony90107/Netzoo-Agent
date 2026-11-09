# SCORPION integration

SCORPION (kuijjerlab/SCORPION; Osorio, Capasso & Kuijjer 2024, *Nat Comput Sci*) builds PANDA gene regulatory
networks from single-cell RNA-seq. It merges similar cells into super-cells (about `gamma_value` cells each, on a
PCA k-nearest-neighbour graph), then runs PANDA's message passing with a TF motif prior and a PPI network on the
super-cells. With a cell metadata table it builds one network per group of cells (`runSCORPION`), all on the same
priors, and `testEdges` tests which edges differ between two sets of those networks.

It is an R package. The image installs it into the `netzoo-r` environment, pinned to commit
`5c0fff00eb08c4b49b807150566e0a31ff592ab4` (version 1.3.5, "Make PANDA match netZooPy"; CRAN has 1.3.4).

## Where it sits

```
single-cell counts + motif + PPI (+ cell metadata) ──SCORPION──▶ edges x networks table ──PORCUPINE (8+ networks)
                                                              └──▶ testEdges table (two groups compared)
```

`run_scorpion` declares `handoff_targets: [run_porcupine]`: its networks file has the header `tf, target, <networks>`,
which PORCUPINE reads like LIONESS output when there are one network per donor or sample.

## Routing: single cells go to SCORPION, and only single cells

SCORPION and PANDA both build TF-to-gene networks, so a typed reading of the result cannot tell them apart. The data
unit can, and code reads it from the request's own words (`routing/data_unit.py`):

- **Single cells**: single-cell, scRNA-seq, snRNA-seq, single nuclei, 10x, scATAC, 單細胞, or SCORPION named.
- **Not single cells**: pseudo-bulk ("we summed the cells per donor"), or a negated mention ("bulk, not single-cell").

A single-cell request is matched against SCORPION and the workflows that read no expression matrix (CONDOR,
PORCUPINE, SAMBAR). Every other request is matched exactly as before: `OUTPUT_CAPABILITIES` iterates without
SCORPION (a lookup by action still finds it), the capability check's prompt and schema leave its entries out, and the
full-catalog guidance leaves it out. The capability sheet gives each workflow its own `data_units`; SCORPION's are
`[single_cells]`, CONDOR's and PORCUPINE's `[bulk_samples, single_cells]`.

A bulk workflow named for single-cell data ("Run PANDA on my scRNA-seq") is not selected by its name. A reply that
still lists a bulk workflow beside single-cell data carries the `single_cell` note (SCORPION is the single-cell
workflow; per-cell LIONESS or BONOBO networks are not advised; pseudo-bulk is the bulk route). "A network for each
cell" is declined with `scorpion.no_per_cell`: SCORPION gives one network per group of cells, never per cell.

## Input contract (`scripts/scorpion_io.py`, `netzoo_agent_core/data/scorpion.py`)

| Role | Format |
| --- | --- |
| `cell_expression_file` | Genes as rows, cells as columns: a table (`.tsv/.txt/.csv`, optionally `.gz`; header `gene, <cell IDs>`) or a 10x Matrix Market directory (`matrix.mtx[.gz]`, `features.tsv[.gz]` or `genes.tsv[.gz]`, `barcodes.tsv[.gz]`). `.h5ad`, `.h5`, `.rds` and `.loom` are refused with the export to use. |
| `motif_file` | Three-column TF, gene, weight edge list (the PANDA motif format). |
| `ppi_file` | Three-column protein, protein, weight edge list. |
| `cell_metadata_file` | Needed with `group_by`: a header, the cell IDs in the first column (or a `cell_id`/`cell`/`barcode` column), and the grouping columns. |

Refused before anything runs: fewer than 10 genes or 30 cells; negative or non-finite values; no motif target among
the expression genes, or no motif TF in the PPI (the message names the identifier mismatch); a `group_by` column the
metadata lacks; no group with at least `max(min_cells, 30)` cells; a comparison with fewer than two built networks
on either side (the message says to add a replicate column such as the donor); a paired comparison with fewer than
two matched pairs. Values that are not whole numbers are noted, because `normalize_data` log-normalizes counts.

For a 10x directory, the gene IDs come from the features column (Ensembl ID or symbol) that shares more genes with
the motif targets; duplicated symbols are summed into one row. Cells without a metadata row, without a group value,
or with no counts are dropped and counted in the manifest.

## Run (`scripts/run_scorpion.py`, `scripts/scorpion_run.R`)

Every network comes from `runSCORPION`: without `group_by` every cell is in one group (`all_cells`), so one network
and many go through the same log normalization, cell minimum and super-cell step. With `compare_by`, `group1` and
`group2`, the networks whose `compare_by` value is `group1` are tested against those with `group2` by `testEdges`
(two-sample; `paired` matches them on their other `group_by` values).

## Controls

| Control | Default | Meaning |
| --- | --- | --- |
| `group_by` | none | Metadata columns; one network per combination of their values |
| `compare_by`, `group1`, `group2` | none | The `group_by` column and the two values testEdges compares (log2 fold change is group1 minus group2) |
| `paired` | false | Pair the two sides on their other `group_by` values (the same donor) |
| `normalize_data` | true | Counts per 10,000, then log1p; false for already normalized values |
| `gamma_value` | 10 | Cells per super-cell |
| `n_pc` | 25 | Principal components for the cell kNN graph |
| `assoc_method` | pearson | pearson, spearman or pcNet between super-cells |
| `alpha_value` | 0.1 | PANDA update rate |
| `min_cells` | 30 | Fewest cells for a network; SCORPION never uses fewer than 30 |
| `z_scaling` | true | z-scored edge weights; false gives the 0-1 scale |
| `n_cores` | 1 | Networks built in parallel |
| `seed` | 1 | R seed (the super-cell step uses its own fixed seed) |

## Outputs

| File | Orientation |
| --- | --- |
| `scorpion_networks.tsv` | `tf, target`, then one column per network (`group_by` values joined by `--`, or `all_cells`) |
| `scorpion_network_cells.tsv` | `network_id, n_cells, built` for every requested network |
| `scorpion_differential_edges.tsv` | With a comparison: testEdges statistics per edge, sorted by `pAdj` |
| `manifest.json` | Inputs, parameters, package ref, cell and network counts, the networks on each side |

## Verified (2026-11-08)

- Toy bundle `data/scorpion-toy`: SCORPION's own `scorpionTest` (300 genes x 1,954 colorectal cancer cells; 3 donors x
  tumour/border/normal) as a 10x directory, with the motif prior limited to those genes. Nine donor x region
  networks (538 TFs x 281 genes, 151,178 edges each) in about 18 s with `n_cores` 1; tumour vs normal (3 vs 3
  networks) gave 2,304 edges with pAdj < 0.05. Without `group_by`, one `all_cells` network.
- Unit and routing tests: `tests/test_scorpion_workflow.py`.
