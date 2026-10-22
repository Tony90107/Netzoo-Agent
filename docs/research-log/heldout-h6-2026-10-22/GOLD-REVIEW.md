# h6 gold review

Sources read: `items-author.json`, `workflows/*.yaml` (13), `scripts/workflow_registry.py` (netzoo-h6-run worktree), and `field-gold-2026-10-22/vocabulary.md` for Part B. Nothing else was opened and no model was called.

Checks: each class re-derived from contract text; all LIONESS-DRAGON value counts recomputed (F(F-1)/2 x samples, and cross-layer only); every evidence quote re-verified as a substring of its source after whitespace collapsing; class/form balance recounted (12 per class, 4 per class x form, unchanged).

## Changes

- **R06** (ask, goal)
  - `workflows`: `[PANDA, PUMA]` -> `[PANDA, OTTER, GIRAFFE, PUMA]`. In the TF-only branch the request ("one regulatory network" from a regulator-target prior plus PPI) is met by every TF-to-gene workflow that takes expression + motif + PPI, not only PANDA. otter.yaml: "Infer an aggregate TF-to-gene regulatory network with OTTER"; giraffe.yaml: "It returns the aggregate TF-by-gene R matrix and a TF-by-sample TFA matrix."; vocabulary `otter.tf_gene_network` / `giraffe.signed_regulation`. For ask items the gold lists the workflows the deciding fact chooses between.
  - `deciding_fact`: "TFs only -> PANDA; includes miRNAs -> PUMA (with a miRNA list)." -> "TFs only -> do, one TF-to-gene network with PANDA (OTTER or GIRAFFE also fit the same three inputs); includes miRNAs -> PUMA (with a miRNA list)."
  - `reason`: rewritten to name the TF-only workflows (same class and deciding fact).
  - `evidence`: added the two quotes above.

No class, form, prompt, file_checkable, missing_core or interpretation_facts changed.

## Borderline items kept unchanged

- **R12** (ask): the gene-gene branch is judged dont. condor.yaml only says it will "Report overlapping source and target IDs because the network should be bipartite"; the refusal rests on the declared input: "CONDOR consumes a weighted source-target bipartite edge list made from a validated regulator-gene network" and `input_artifacts: [regulatory_network]`. Kept.
- **R18, R20, R30** (ask): the dont branch is "dont as given" -- a fix (centring, numeric recoding, ID mapping) would be done outside NetZoo. The contracts state the conditions ("BONOBO requires it" for centred; "numeric covariates"; "identifier mismatches are rejected before the API call"), so the two branches differ in contract outcome. Kept.
- **file_checkable** (R05, R06, R20, R21, R29, R30 false; R08, R12, R18, R26, R38 true; R25 false): kept the author's convention that it is true only when the deciding fact sits in a file the prompt names by filename. In the false cases with file content (sample IDs, prior IDs, coding, feature count, sample count, ID system), the fact could be read from a file once one is provided, but none is named. R25's fact (provenance) is not reliably readable from file content.
- **R43** (do): `sparsify=true` with `save_pvals=true` is a valid combination, but per bonobo.yaml it "retains the full co-expression matrix ... and writes a matching p-value matrix ... it does not also emit an already-thresholded network in this mode". The request sets these options and asks for per-sample networks, not for pre-thresholded networks, so it stays do. A reply should say that thresholding at 0.01 is applied from the saved p-values.
- **R46** (vague): "LIONESS" names a family (per-sample TF-gene or co-expression networks), not one result, and the user asks what to run. Kept vague.
- **R02, R16, R22** (vague, named): workflows are named only inside a which-to-use / worth-it question; no result is named. Kept vague.
- **R24** (vague): "send me whatever you get" is read as the usual way of asking for results back, not as a delivery request (vocabulary `delivery` covers e-mail, upload, publication or showing results to others outside the analysis). Kept vague.
- **R11** (do): only LIONESS-COEXPRESSION gives both a cohort-wide and a per-sample co-expression network from expression alone ("Infer aggregate and sample-specific co-expression networks with LIONESS."); BONOBO "has no aggregate/prior output" and COBRA needs a design file. Kept.
- **R06** (ask, after the change): the miRNA branch needs a miRNA list the prompt does not mention; the deciding fact already says "(with a miRNA list)". The class stays ask because the regulator class alone separates the TF-only workflows from PUMA.
- **R44** (do): no sample count is given; puma.yaml states no sample minimum, so nothing fails. Kept.
- **R31** (dont): no expression file is named either, but the single stated failing condition is the refused handoff ("An aggregate COBRA adjusted co-expression artifact is not a direct LIONESS handoff"). Kept.
