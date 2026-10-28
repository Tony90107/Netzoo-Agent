# j5 gold review

## Changes

- **W01**, `workflows`: `["PANDA"]` -> `["PANDA", "OTTER", "GIRAFFE"]`; `reason` updated to match. The prompt gives expression, motif and PPI and asks for one aggregate TF-to-gene network per group. Other contracts produce the same result from the same inputs: otter.yaml: "It produces an aggregate TF-to-gene network whose edge weight is the optimized OTTER W score."; giraffe.yaml: "TF-by-gene R matrix and a TF-by-sample TFA matrix." (GIRAFFE `produced_artifacts: [regulatory_network, tf_activity_matrix]`). Call unchanged (DO).
- **W12**, `workflows`: `["PANDA"]` -> `["PANDA", "OTTER", "GIRAFFE"]`; `reason` updated to match. Same reasoning and quotes as W01: one aggregate TF-to-gene network from expression, motif and PPI. Call unchanged (DO).
- **W04**, `uncertainty`: `none` -> `explicit`. The opening request says the user is not sure what to produce. AUTHOR-BRIEF.md: uncertainty is "explicit" when "the opening request states the user is unsure of something". Call unchanged (CLARIFY).

No prompt or reply was changed.

## Borderline items kept unchanged

- **W17** (GT, PANDA then CONDOR): kept as DO. panda.yaml: "handoff_targets: [run_condor]" and "Convert that network to a source-target-weight bipartite edge list before handing it to CONDOR." The registry note on thresholding to non-negative weights describes a preparation step inside the registered chain, not a refusal.
- **W15** (GO named): kept as DECLINE, not PARTIAL. The user requires overlapping membership ("must be allowed"), and CONDOR gives one community per node (workflow_registry.py: "CONDOR then gives each node one community and a core score."). Plain CONDOR communities are not the request as asked, and the setting is not something a named workflow fails to expose, so PARTIAL shape (a) does not apply.
- **W16** (U which_file): kept. bonobo.yaml: "The agent requires the caller to declare log_transformed=true and centered=true". This is a caller declaration, not a file check. Per-edge p-values come only from BONOBO, so raw counts lead to DECLINE and the log/centred file leads to DO.
- **W47** (U input_exists): kept DECLINE for the "no miRNA files" branch, not PARTIAL. The request is for one network that has both TF and miRNA regulators. A TF-only network is not a separate requested result, so PARTIAL shape (b) does not apply.
- **W41** (V): the wording says the user has not decided. That states an open choice, not an uncertainty, so `uncertainty` stays `none`. "Multi-omic modules" picks no producible output: dragon.yaml: "Direct handoffs to PANDA, PUMA, LIONESS, CONDOR, BONOBO, and OTTER are illegal". So CLARIFY stands.
- **W33** (N decline) and **W43** (V, not-doable reply): both fail on two samples. bonobo.yaml: "at least three total samples"; lioness-coexpression.yaml: "Require at least three samples". Kept.
- **W27 / W26 / W39** (U count): recomputed. COBRA: 150 < 400 fails and 1,500 > 400 passes. LIONESS-DRAGON: F=800, so 319,600 pairs; 19,176,000 values at 60 samples is under the cap and 22,372,000 at 70 is over it. LIONESS-PANDA: 2 samples fail and 4 pass the three-sample minimum. All correct.
- **W24** (TC same samples): F=250 gives 31,125 pairs x 50 = 1,556,250 values, under 20,000,000. Correct.
