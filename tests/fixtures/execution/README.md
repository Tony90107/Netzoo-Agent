# Recorded outputs from pinned workflow runs

Reference artifacts for the execution-layer contract checks in
`tests/test_execution_artifact_contracts.py`. They are **recorded outputs of real
runs**, not synthesised examples, copied from the untracked `outputs/` directory
so the checks work on a fresh clone.

| File | Method | Declared artifact | Kept |
| --- | --- | --- | --- |
| `sambar.pathway_mutation_matrix.csv` | SAMBAR | `pathway_mutation_matrix` | complete |
| `sambar.gene_mutation_scores.axes.json` | SAMBAR | `gene_mutation_scores` | **axis labels only** (the full matrix is 1 MB and only its axes are contracted) |
| `cobra.aggregate_coexpression_network.tsv` | COBRA | `coexpression_network`, aggregate | complete |
| `lioness_puma.sample_specific_regulatory_network.tsv` | LIONESS-PUMA | `regulatory_network`, sample_specific | complete |
| `puma.aggregate_regulatory_network.tsv` | PUMA | `regulatory_network`, aggregate | complete |
| `panda.aggregate_regulatory_network.head.tsv` | PANDA | `regulatory_network`, aggregate | **header + first 200 rows** (the full edge list is 3 MB) |
| `sambar.manifest.json` | SAMBAR | — | provenance: inputs, parameters, artifacts |

Distilled files are marked above and the checks that use them assert only
properties the distillation preserves: column contracts and axis identity, never
row counts of the full artifact.

**These verify structure, not biology.** Identifier families, axis orientation,
sample coverage and required/forbidden columns are checked. Numeric values are
not compared against references and no biological claim is made from them.
