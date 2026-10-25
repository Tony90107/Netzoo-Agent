# h10 gold review

Reviewer read only `items-author.json`, `AUTHOR-BRIEF.md`, `workflows/*.yaml` (13 files) and `scripts/workflow_registry.py`. All 36 opening calls, the 8 `final_after_fact` and the 6 `final_after_result` golds were re-derived from contract text. Every evidence quote was checked by script to be a verbatim substring of the file it names. No call, `workflows` list, prompt or reply changed. Group, sub, call and `dragon_control` counts are unchanged.

## Changes (3 gold fields, 0 prompts or replies)

- **W14 `fact_keywords`**: `["cobra", "bonobo", "per-sample", "adjusted", "co-expression matrix", "which"]` -> `["cobra", "bonobo", "per-sample", "adjusted", "co-expression matrix", "batch study"]`.
  "which" is a generic word that fits any question, against brief item 3 ("fact_keywords are specific to that fact"). "batch study" is the provenance the prompt itself gives for the COBRA option. The decision is unchanged: otter.yaml: "Only COBRA's adjusted co-expression artifact after this exact identifier/order"; bonobo.yaml: "CONDOR, COBRA, DRAGON, or OTTER either."
- **W26 `evidence`**: removed `lioness-coexpression.yaml: "Infer aggregate and sample-specific co-expression networks with LIONESS."`.
  That quote cites a workflow that is not in this item's candidate `workflows` (PANDA, LIONESS-PANDA, OTTER, GIRAFFE). Co-expression is not a regulation result, so I kept the list and dropped the quote. The CLARIFY call is unchanged; the remaining quotes support it: panda.yaml: "Infer an aggregate TF-to-gene regulatory network with PANDA."; giraffe.yaml: "produced_artifacts: [regulatory_network, tf_activity_matrix]".
- **W33 `deciding_fact`**: "... or was never made (not doable: mirna_file is a required PUMA input)." -> "... or was never made (DECLINE: mirna_file is a required PUMA input)."
  The other seven U items name the call for both branches, so this one now does too. puma.yaml: "required_inputs: [expression_file, motif_file, ppi_file, mirna_file, output_file]".

## Checked and confirmed (arithmetic)

- W15: F = 280 + 120 = 400. 400 x 399 / 2 = 79,800 pairs x 60 = 4,788,000, which is at most 20,000,000. DO.
- W30: F = 1,500 + 500 = 2,000. 2,000 x 1,999 / 2 = 1,999,000 x 80 = 159,920,000, which is over 20,000,000. DECLINE. lioness-dragon.yaml: "runs above 20,000,000 values are refused before they start"
- W21: 220 genes > 180 samples (DO); 220 < 260 (DECLINE). W22: 18,000 genes > 80 samples. cobra.yaml: "Expression must be a labeled gene-by-sample matrix with more genes than samples."
- SAMBAR: W06 2 <= 2 <= 5 <= 120; W13 2 <= 2 <= 4 <= 85; W35 2 <= 2 <= 6 <= 150 (all DO); W19 kmax 12 > 9 samples (DECLINE). sambar.yaml: "cluster=true requires 2 <= kmin <= kmax <= number of mutation samples."
- W27: 4 samples meet the three-sample minimum, 2 do not. W20: delta 0.5 is not below 1/3 with sparsify. W32: lambda2 1.8 is outside [0, 1]. W16: 0.2 and 0.6 are both set and both in [0, 1].

## Borderline items kept unchanged

- **W01 (ASK), gene-by-sample vs COBRA gene-by-gene file.** A file inspection could in principle notice a square gene-by-gene matrix. The contract classes this refusal as request-level, not file-checkable: lioness-panda.yaml "An aggregate COBRA adjusted co-expression artifact is not a direct LIONESS handoff" is listed with `scope: request` and the comment "no file inspection settles it". I kept ASK.
- **W14 (ASK), COBRA vs per-sample BONOBO matrix.** A raw BONOBO export has no row labels and might fail OTTER's file check ("It must be a labeled symmetric square gene-by-gene matrix with exact row/column order."). A labelled export would pass, though, and only the user knows whether the matrix is aggregate or per-sample. OTTER accepts only aggregate inputs (otter.yaml: "accepted_input_granularities: [aggregate]"). I kept ASK.
- **W04 (ASK, DRAGON), continuous beta vs 0/1 calls.** Binary 0/1 values pass DRAGON's file-scope checks (missing, non-numeric and duplicate values). Only the convention dragon.yaml "Values must be finite continuous numeric measurements." rules them out, so the fact has to come from the user. I kept ASK.
- **W25 (DECLINE), OTTER "the LIONESS way".** I considered PARTIAL shape (a). Per-sample OTTER networks are a different result from an unregistered method, not an unexposed setting. Aggregate OTTER is not part of what was asked. otter.yaml: "aggregate only and does not silently label its output LIONESS-OTTER."; workflow_registry.py: "netZooPy, not registered in this agent". I kept DECLINE with no also_acceptable.
- **W28 and W33 (input_exists).** A missing required input counts as not doable as asked, so the call is DECLINE. In W28, if the network was never built, CONDOR cannot take expression (condor.yaml: "CONDOR does not consume the raw expression matrix directly."), and with no motif or PPI file no TF-gene network can be built first. In W33 the miRNA list is a required PUMA input. Both U answers lead to different outcomes.
- **W21 and W27 (count).** A file could reveal the sample count once supplied, but the contract marks both limits as request-scope (`scope: request`, `limit: "relation:features>samples"` / `"min_samples"`). The prompt gives two candidate values, so ASK stands.
- **W18 (DECLINE), clustering samples from expression.** The registry describes a route through per-sample features plus an outside clustering step. It also states workflow_registry.py: "No registered workflow assigns samples to clusters from expression.", so no registered workflow produces the requested result. I kept DECLINE.
- **W26 `final_after_result` (DECLINE), causal proof.** The reply asks for causation and nothing else. workflow_registry.py: "Registered workflows estimate associations; they can describe what changes, not prove its cause." This is DECLINE, not PARTIAL.
