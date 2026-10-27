# j1 gold review

Read: AUTHOR-BRIEF.md, items-author.json, workflows/*.yaml (13), scripts/workflow_registry.py (targeted: BONOBO delta/sparsify, LIONESS-OTTER external reference, sample minimums). All arithmetic recomputed; all calls, also_acceptable, workflows and final_after_* calls kept.

## Changes

- J04, `fact_keywords`: `[..., "put together", "exists"]` -> `["ppi", "protein interaction", "interaction file", "ppi file", "put together"]` (generic "exists" removed; the fact is whether the required input exists: panda.yaml: "required_inputs: [expression_file, motif_file, ppi_file, output_file]").
- J06, `fact_keywords`: `["mirna list", "mirna file", "one per line", "exists", "made"]` -> `["mirna list", "mirna file", "mirna ids", "ever made", "one per line"]` (generic "exists"/"made" removed; lioness-puma.yaml: "Require at least three expression samples and a validated one-ID-per-line miRNA list.").
- J09, `fact_keywords`: `[..., "interaction file", "exists"]` -> `["ppi", "protein interaction", "tf-tf", "interaction file", "ppi file"]` (generic "exists" removed; giraffe.yaml: "required_inputs: [expression_file, motif_file, ppi_file, output_file]").

No prompt or reply changed. No gold call changed.

## Arithmetic re-checked (all correct as written)

- J27: (300+700)=1,000 features, 499,500 pairs x 36 = 17,982,000 <= 20,000,000 -> DO.
- J35: 2,500 features, 3,123,750 pairs x 80 = 249,900,000 > 20,000,000 -> DECLINE.
- J40: 1,200 features, 719,400 pairs; x25 = 17,985,000 (DO), x30 = 21,582,000 (DECLINE).
- J29: 400 genes vs 350 (DO) / 450 (DECLINE); J31 15,000 > 12; J37 15,000 > 200; J38 300 < 500 -> DECLINE.
- J01 2<=6<=150; J08 kmax 12 vs 10/15; J43 kmax 10 > 8; J47 2..5 <= 120.

## Borderline items kept unchanged

- J45 (ASK, same patients vs separate cohorts): dragon.yaml's sample-ID equality check is file-scope ("Layer 2 is reordered to layer 1 only after exact sample-ID set equality is proven."), but the prompt says both tables share an ID format and equal size, so a file check could pass on coincident IDs and would not settle whether the patients are the same. Kept as ASK.
- J46, J48 (ASK, which file): the relevant checks are file-scope (otter.yaml: "It must be a labeled symmetric square gene-by-gene matrix with exact row/column order."; condor.yaml: "Require source and target columns and accept an optional numeric weight column."). No file is attached to the request, so no check can run before the user answers; the two answers give different contract outcomes. Kept as ASK; an assistant that previews and lets the file check decide is arguably defensible but not added to also_acceptable.
- J21 (DO, BONOBO sparsify): registry delta note "With sparsify it must be above 0 and below 1/3" applies to a manual delta; the prompt sets none and the default "empty estimates it per sample". Kept DO.
- J10 (DECLINE, LIONESS-OTTER): registry lists LIONESS-OTTER as "netZooPy, not registered in this agent"; the user named that method, so an unregistered method -> DECLINE, not a redirect to LIONESS-PANDA.
- J03 (DECLINE, CONDOR on raw expression): PANDA -> CONDOR is a registered handoff, but no motif/PPI is stated and the user asks for CONDOR directly on expression (condor.yaml: "CONDOR does not consume the raw expression matrix directly.").
- J16 (ASK, centered): if not centered, BONOBO as named cannot run (bonobo.yaml: "The expression is declared centered; BONOBO requires it."); LIONESS-COEXPRESSION would be an alternative workflow but the user named BONOBO.
- J13 and J24: the outcome-neutral aside is the polite question form of the request itself rather than a separate sentence; allowed by the brief's polite-question example.

## Final counts

V 8 (asked_by_others 2, project_promise 1, something_interesting 1, understand_in_general 2, what_can_it_tell 1, where_to_start 1), U 12 (3 per sub), K1 14, K2 14 (broken_condition 11, out_of_scope 3); dragon_control true 5 K1 + 5 K2. No imbalance introduced.
