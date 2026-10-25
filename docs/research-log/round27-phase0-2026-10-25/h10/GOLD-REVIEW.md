# h10 gold review

## Changes

- **Y32, prompt** (prompt only, gold unchanged): "Our rare-disease study only has RNA-seq from two patient fibroblast lines." -> "Our rare-disease study only has one RNA-seq library from each of two patient fibroblast lines, so two samples in total." Reason: a "line" could carry several libraries, which would leave the sample count (and so the minimum-sample check) open. Deciding quotes unchanged: lioness-coexpression.yaml: "Require at least three samples"; bonobo.yaml: "at least three total samples".

No gold field (call, also_acceptable, workflows, reason, evidence, deciding_fact, missing_core, uncertainty) was changed.

Arithmetic rechecked: Y08 F=650, 650*649/2 = 210,925 x 45 = 9,491,625 (under the cap, so only the lambda pairing rule decides); Y20 F=600 -> 179,700 x 80 = 14,376,000 (allowed), F=1,100 -> 604,450 x 80 = 48,356,000 (refused); Y15 kmax 12 > 9 samples; Y27 2 <= 3 <= 6 <= 140; Y40 45 < 60 < 2,000; Y02 3,000 > 150; Y10 delta 0.5 >= 1/3 with sparsify.

## Borderline items kept unchanged

- **Y34** (DECLINE): a per-sample TF-gene network from these inputs exists through LIONESS-PANDA, but the request names OTTER, whose registered action is aggregate only (otter.yaml: "This agent's registered OTTER action is aggregate only and does not silently label its output LIONESS-OTTER."). Kept as an unregistered-method DECLINE; a reply may mention LIONESS-PANDA as the alternative.
- **Y47** (ASK): lioness-puma.yaml lists `handoff_targets: []`, but condor.yaml covers per-sample regulator-gene networks ("For sample-specific networks, run community detection per sample and keep regulator-side and gene-side memberships distinct."), so the LIONESS-PUMA branch is DO and the co-expression branch is not a regulator-gene input. Kept.
- **Y26** (ASK): the DRAGON edge list natively has partial_correlation/precision columns, not "weight"; a renamed export is plausible and CONDOR's file check only reports overlapping IDs ("Report overlapping source and target IDs"), so no file check settles origin. Kept.
- **Y33** (CLARIFY): "modules" sounds like an output, but no result or network is chosen for this two-omics data; matches the brief's CLARIFY description. Kept.
- **Y08** (DECLINE): "regularization strength" describes the layer shrinkage by effect without its name; the one-layer manual value breaks "a manual value needs lambda1 and lambda2 together". Kept as DECLINE (invalid setting combination), not PARTIAL.
- **Y12 / Y23** (DO): wording ("significance level", "one line for each pair of features") is close to contract text but paraphrased, not a setting name or parameter spelling. Kept.
- **Y48** (ASK): log_transformed/centered default to null and must be declared, so neither a default nor a file check settles it. Kept.
