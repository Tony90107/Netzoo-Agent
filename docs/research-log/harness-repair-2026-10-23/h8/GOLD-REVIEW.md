# h8 gold review

Reviewer read only `items-author.json`, `AUTHOR-BRIEF.md`, `workflows/*.yaml` (all 13) and `scripts/workflow_registry.py`. No model was called. A script confirmed that every evidence quote appears verbatim in the file it names, that all prompts are ASCII, and that `items.json` parses with 24 items (Y01-Y24).

## Changes

None. No gold field (call, also_acceptable, workflows, reason, evidence, deciding_fact, missing_core, uncertainty) and no prompt was changed. `items.json` = `items-author.json` + `review_note`.

Arithmetic I recomputed:
- Y02: F = 200 + 300 = 500 -> 124,750 pairs x 120 = 14,970,000 (<= 20,000,000, DO); F = 200 + 900 = 1,100 -> 604,450 x 120 = 72,534,000 (> 20,000,000, DECLINE). lioness-dragon.yaml: "runs above 20,000,000 values are refused before they start".
- Y07: F = 150 + 250 = 400 -> 79,800 x 70 = 5,586,000 (under the cap, so the per-biopsy branch is DO).
- Y19: 96 genes < 150 samples fails, 18,000 > 150 passes. cobra.yaml: "Expression must be a labeled gene-by-sample matrix with more genes than samples."
- Y17: 2 <= 2 <= 6 <= 120. sambar.yaml: "cluster=true requires 2 <= kmin <= kmax <= number of mutation samples."
- Y04: 2 samples < 3. lioness-coexpression.yaml: "Require at least three samples"; bonobo.yaml also needs "at least three total samples".

## Borderline items kept unchanged

- **Y13 (ASK)**: under the whole-cohort answer, OTTER and GIRAFFE also give an aggregate TF-to-gene result from the same inputs, so that branch is a method choice inside DO. The deciding fact (cohort-wide vs per patient) still separates PANDA from LIONESS-PANDA. panda.yaml: "granularities: [aggregate]"; lioness-panda.yaml: "granularities: [aggregate, sample_specific]". `workflows` kept as [PANDA, LIONESS-PANDA].
- **Y14 (ASK)**: the shared prior carries miRNA-target edges. On the GIRAFFE branch, GIRAFFE's identifier check may need a TF-only prior (giraffe.yaml: "all TF IDs must match the motif/prior TF set"; "identifier mismatches are rejected before the API call"). That is a file-scope check (`scope: file`), so it does not settle the question and does not change the call. Both branches still lead to different workflows.
- **Y19 (ASK)**: only one of the two matrices passes COBRA's rule, so the assistant may add a recommendation. But the user says which analysis set is meant is unknown, and no contract default picks it. ASK kept.
- **Y21 (ASK)**: the comparison branch is DECLINE, not PARTIAL. It is one result, and the registry marks per-network CONDOR as an approximation only. workflow_registry.py: "Not registered here; ALPACA is in netZooR. CONDOR run on each network is only an approximation."
- **Y22 (DO)**: whether the COBRA matrix and the OTTER priors share identifiers is a file check, not a request-level refusal. otter.yaml: "Only COBRA's adjusted co-expression artifact after this exact identifier/order validation may hand off to OTTER"; cobra.yaml: "handoff_targets: [run_panda, run_puma, run_otter]". OTTER accepts the co-expression matrix alone: "required_input_groups: [[expression_file, coexpression_file]]".
- **Y23 (PARTIAL)**: the user explicitly distrusts the defaults, but the requested settings are not exposed at all, which is the brief's PARTIAL shape (a), not an out-of-range exposed value. giraffe.yaml: "controls: []".
- **Y18 (DO)**: per-donor p-values need sparsify together with save_pvals. delta is left empty and is estimated, so the sparsify delta range is not triggered. bonobo.yaml: "Write each sample's edge p-value matrix; requires sparsify."
- **Y04 (DECLINE)**: `workflows` could also list BONOBO, which the reason cites as failing the same minimum. That is optional for DECLINE, so it is kept as [LIONESS-COEXPRESSION].
- **Y01, Y24 (CLARIFY)**: the candidate lists are illustrative, not exhaustive. Any registered workflow that takes the stated data is a valid candidate.
- **Y20, Y05, Y04 (R)**: the closing clauses ("so I can rank TFs", "For the survival analysis", "to see which gene pairs differ") state purpose, not a second result asked of the assistant, so PARTIAL shape (b) does not apply.

## Counts after review (unchanged from the author's set)

- Category: R 6, F 6, C 6, K 6.
- Sub: R doable 3 / input_source 1 / not_doable 2; F number 2 / deliverable 2 / scale 2; C or 1 / or_maybe+two_sentences 1 / either+three 1 / versus 1 / stated_result 2; K vague 3 / one_sentence 3.
- expected_call: DO 8, CLARIFY 7, ASK 6, DECLINE 2, PARTIAL 1.
