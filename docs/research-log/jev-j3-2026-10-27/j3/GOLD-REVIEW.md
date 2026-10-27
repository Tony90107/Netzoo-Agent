# j3 gold review

Read: REVIEW-BRIEF.md, AUTHOR-BRIEF.md, items-author.json, workflows/*.yaml, scripts/workflow_registry.py. All arithmetic recomputed; evidence quotes verified verbatim with check_format.py.

## Changes

- **R20 (GO, go_named)**, `prompt`: before "I'd like CONDOR modules, and for each gene a score of how strongly it belongs to every module, since genes are often shared between modules." -> after "I'd like CONDOR modules in which every gene gets a score for how strongly it belongs to each of the modules, since genes are often shared between modules." The original phrasing reads as two distinct results (modules + per-module membership scores), which matches PARTIAL shape (b) rather than the GO group's single soft grouping; the rewrite asks for one soft grouping, so DECLINE follows. Decisive text: workflow_registry.py "CONDOR then gives each node one community and a core score."
- **R20**, `reply_restate`: "...plus every gene's strength of belonging to each module." -> "...where every gene has a strength of belonging to each module." (matches the rewritten single-result request; adds nothing).
- **R20**, `reason`: reworded to "CONDOR gives each node one community and a core score within it; no registered workflow returns each gene's strength of membership in every module." Call, workflows and evidence unchanged.

No other gold, prompt or reply changed.

## Borderline items kept unchanged

- **R46, R48 (GO, named)**: name a grouping workflow and ask for overlap / membership weights. Not PARTIAL shape (a): overlap changes the result itself, it is not a side setting such as format or hardware with the workflow still producing what was asked. DECLINE kept (workflow_registry.py "CONDOR then gives each node one community and a core score."; sambar.yaml "Hierarchical-clustering linkage method (a scipy name).").
- **R07, R37 (U, which_file)**: the file check (sample count / "exact sample-ID set equality is proven") would run on whichever file is used, but cannot decide which file the user means; ASK kept.
- **R11 (U, input_exists)**: without the miRNA files a TF-only network would be possible, but the request is a single TF+miRNA result, not two results, so the not-doable answer is DECLINE, not PARTIAL (puma.yaml required_inputs includes mirna_file).
- **R47 (GT, named)**: OTTER edge list given to CONDOR without saying weights are non-negative. The non-negative-weight note in workflow_registry.py names PANDA/LIONESS networks, and otter.yaml lists "handoff_targets: [run_condor]"; DO kept.
- **R03 (V)**: reply asks per-sample TF-gene networks from 2 samples; every per-sample workflow requires at least three samples (lioness-panda.yaml "Require at least three expression samples before execution."), so DECLINE kept.
- **R35 (U, count)**: recomputed 500 features -> 124,750 pairs x 100 = 12,475,000 (DO); 900 features -> 404,550 x 100 = 40,455,000 > 20,000,000 (DECLINE). Correct as written.
- **R22, R36**: 150 features -> 11,175 x 80 = 894,000; 100 features -> 4,950 x 70 = 346,500; both under the limit. Correct.
- **R29, R40 (GL, k range)**: kmax above the sample count is a value outside the stated range of an exposed setting -> DECLINE, not PARTIAL (sambar.yaml "cluster=true requires 2 <= kmin <= kmax <= number of mutation samples.").
