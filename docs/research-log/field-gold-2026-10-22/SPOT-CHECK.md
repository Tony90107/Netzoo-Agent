# Field gold spot check (ROUND-26 phase 0, 1.2)

I check about 10% per set: 5 items per 48-item set and 6 for core, drawn with `random.Random(26)`. I read each
prompt and each label against `vocabulary.md` and the YAMLs.

## h1 (H13, H14, H28, H43, H48)

All 5 are acceptable. Two properties of the labels matter for scoring:

- **H43, "the overall one".** `produces` lists every aggregate TF-gene entry: PANDA, OTTER,
  `giraffe.signed_regulation`, and `lioness_panda.per_sample_networks`. In context, the user means LIONESS-PANDA's
  aggregate network, so the list is broader than one reading of the request. `produces` is therefore an
  **acceptable set**: a reader's credit counts as right when it falls inside the set. An over-wide set makes the
  results metric lenient, never strict.
- **H48, "Execute COBRA on ...".** The request names only the method, so no result words are labelled. The results
  field has no unit for such a request. The linking metric covers only result words a labeller found.

The other three are right as labelled:

- H13: "modules" links to `condor.communities`. The edge list goes to `network_file`, both as `has` and as `source`.
- H14: `causal_proof`, with the two omics layers.
- H28: `lioness_dragon.per_sample_networks`. "Every pair kept" is not a setting.

## h3 (L13, L14, L28, L43, L48)

All 5 are acceptable.

- **The convention differs between labellers.** L14 "I want DRAGON", L28 "Set up BONOBO" and L43 "run LIONESS-PANDA"
  use the method's name as the result quote, linked to that workflow's result. h1's H48 labelled no result for such
  a request.
  - Scoring treats a result whose quote is only the method name (with a run verb) as a *named-method* unit and
    reports it apart from result-word units, so neither convention changes the result-word metric.
- **L13, "the cohort matrix".** The acceptable set holds LIONESS-DRAGON's entry and `dragon.two_layer_network`. This
  is wide, as in h1's H43.
- **L28** is thorough. The settings labelled are log_transformed, centered, sparsify, bonobo_confidence, delta, output
  format and genes_axis "rows", with the delta-with-sparsify limit noted.
- **L48** is right. Its `lacks` is `network_file`, its `source` is `expression_file`, and its result is
  `condor.communities`.

## h5 (random Q13, Q14, Q28, Q43, Q48; plus the six target items Q09, Q10, Q15, Q26, Q42, Q46)

All 11 are acceptable. The labeller worked blind, and its labels on the six target items agree with my own
diagnosis of the h5 readings in `output/thesis/2026-10-22_論文段落_評估與讀題瓶頸.md`, table 4-2:

| Item | Labels | What it confirms |
|---|---|---|
| Q42 | "keep the full matrices and save a p-value matrix for every sample" → `BONOBO.sparsify` = true and `BONOBO.save_pvals` = true, citing the `conditional_outputs` entry | The live reading missed this link: it read `keep_in_memory`, or nothing |
| Q09 | "sparsify switched on" → `BONOBO.sparsify` = true | The live reading missed this setting |
| Q10 | "whether each TF activates or represses its targets" → `giraffe.signed_regulation` | The live reading gave no credit |
| Q15 | has `mutation_file`; lacks `expression_file`; the source of the TF-gene network is `mutation_file` | Field c has what code needs to decide |
| Q46 | has `coexpression_file`; source `coexpression_file` for `lioness_puma.per_sample_networks` | Code can compare this with LIONESS-PUMA's required `expression_file` |
| Q26 | `sambar.subtypes`; kmin 2 and kmax 5 | Field gold does not type group membership; Q26's error is a typed attribute, outside the three fields |

Points to note:

- **Q26.** The labeller also read "an MSigDB pathway GMT" as `SAMBAR.gmt_msigdb` = true. This is defensible, but it is
  a declaration, not a requested option. Settings scoring should report declared-data settings (log_transformed,
  centered, gmt_msigdb) apart from requested options.
- **Q42.** "Per-sample co-expression networks" lists BONOBO and LIONESS-COEXPRESSION, although the request says "With
  BONOBO". The acceptable set is wide, as in h1 and h3.
- **Q43.** "Launch OTTER" is a named-method unit, as in h3.

## h2 (J13, J14, J28, J43, J48)

All 5 are acceptable.

| Item | Label |
|---|---|
| J43 | Signed regulation links to `giraffe.signed_regulation`, the same request form as h5's Q10 |
| J13 | "Aggregate network" in a LIONESS-PUMA run gives the set {PUMA, LIONESS-PUMA} |
| J14 | A named-method unit |
| J28 | Both COBRA results link to `cobra.covariate_components` |
| J48 | The undecided sample count is noted |

The h2 labeller wrote down two conventions that narrow its sets compared with h1, h3 and h5:

- A whole-cohort request lists LIONESS outputs only when the request names a LIONESS run.
- A TF-only request leaves out the PUMA family.

So the width of the acceptable sets differs between batches. A before/after comparison on the same gold is not
affected. Absolute linking accuracy is reported per set, not pooled as one number.

## h4 (M13, M14, M28, M43, M48)

All 5 are acceptable.

| Item | Label |
|---|---|
| M13 | DRAGON lambda1 0 and lambda2 1, edge_list output, `dragon.two_layer_network` |
| M14 | The aggregate PANDA network inside a LIONESS-PANDA run gives the set {PANDA, LIONESS-PANDA} |
| M28 | Survival goes to slot `none` |
| M48 | The miRNA-target prior goes to `motif_file` (PUMA's prior holds them); the ID list goes to `mirna_file` |

**M43, "a regulatory network perspective".** M43 is a vague request, yet it is labelled as a result whose acceptable
set holds every regulatory network entry (7 ids). Under the "inside the set" rule a set this wide credits almost any
reading. Scoring therefore reports apart any result unit whose set holds more than 3 ids.

## core (C13, C14, C28, C43, C48, C59)

All 6 are acceptable.

| Item | Label |
|---|---|
| C14 | The L1 penalty is an `unregistered` setting |
| C13 | OTTER lam = 1.5; seed_W goes to `motif_file` |
| C28 | Both COBRA results link to `cobra.covariate_components` |
| C43 | The uncertainty about the file's columns is noted |
| C48 | DRAGON, with the sample-matching doubt noted |
| C59 | The miRNA-target prior goes to `motif_file` |

**`source` density.** The core labeller fills `source` for every file of a run request (62 links), while h1 fills
12. Field c scoring therefore uses `has` and `lacks` for what the user holds. It uses `source` only where the data
named as a source is not what the result's workflow takes.

**The labeller opened `vocabulary.json`.** It reports looking at the key names. That file is `vocabulary.md`'s
content in JSON, built by `vocabulary.py`, so the labeller saw nothing beyond its allowed sources.

## Totals (labellers' reports)

| Set | Items | Results | Settings | Has | Lacks | Source | Results with no produces | Items with notes |
|---|---|---|---|---|---|---|---|---|
| core | 60 | 61 | 40 | 130 | 6 | 62 | 12 | 43 |
| h1 | 48 | 37 | 45 | 108 | 3 | 12 | 3 | 37 |
| h2 | 48 | 49 | 45 | 113 | 1 | 7 | 4 | 20 |
| h3 | 48 | 48 | 46 | 101 | 4 | 6 | 5 | 41 |
| h4 | 48 | 46 | 45 | 119 | 1 | 26 | 6 | 27 |
| h5 | 48 | 40 | 24 | 116 | 1 | 33 | 3 | 21 |
| **all** | **300** | **281** | **245** | **687** | **16** | **146** | **33** | **189** |

The spot check covers 31 items, 10%: 5 random per set, 6 for core, and h5's six target items. All 31 are
acceptable. No label was wrong; the notes above are scoring conventions.
