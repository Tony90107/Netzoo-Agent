# Gold review: heldout-h5-2026-10-21

Reviewer read only `.worktrees/netzoo-h5-run/workflows/*.yaml` (13 contracts), `.worktrees/netzoo-h5-run/scripts/workflow_registry.py` and `items-author.json`. Every evidence quote was checked by script as verbatim in the cited file. All arithmetic was recomputed. Result: 48 classes unchanged, 1 item's gold edited, balance unchanged (12 per class, 4 per class x form cell).

## Changes

- **Q40 (vague, run)**
  - `workflows`: `["COBRA", "LIONESS-COEXPRESSION", "BONOBO"]` -> `["COBRA", "LIONESS-COEXPRESSION"]`
  - `reason`: "...fit COBRA or the per-sample co-expression workflows..." -> names COBRA and LIONESS-COEXPRESSION, and says BONOBO is not a candidate as given because the expression file is named as counts.
  - `evidence`: added the BONOBO quote below.
  - `interpretation_facts`: "expression counts file" -> "expression counts file (not declared log-transformed or centered)".
  - Deciding quote, bonobo.yaml: "The agent requires the caller to declare log_transformed=true and centered=true because BONOBO assumes log-transformed centered expression." (log_transformed control: "The expression is declared log-transformed; BONOBO requires it."). `mouse_retina_counts.tsv` is a counts file, and the agent performs no transformation, so BONOBO cannot use it as given. COBRA and LIONESS-COEXPRESSION state no such requirement.

No prompt was changed. Every arithmetic statement in the prompts and golds checks out:
- Q14: 600 features -> 179,700 pairs x 50 = 8,985,000; 1,600 features -> 1,279,200 pairs x 50 = 63,960,000.
- Q27: 3,500 features -> 6,123,250 pairs x 150 = 918,487,500.
- Q45: 700 features -> 244,650 pairs x 40 = 9,786,000.
- Q07: 12 time points x 3 leaves = 36.

## Borderline items kept unchanged

- **Q01 and Q35, `file_checkable: false`.** Both deciding facts are file-scope checks in the contracts:
  - dragon.yaml: "Layer 2 is reordered to layer 1 only after exact sample-ID set equality is proven."
  - sambar.yaml: "...with non-negative numeric values."

  Neither prompt names an input file, so the fact cannot be checked before asking. Kept false. If `file_checkable` is meant as "a fact type the input check verifies", these two would become true.
- **Q06, matrix branch = dont.** condor.yaml says "Require source and target columns". panda.yaml says "Convert that network to a source-target-weight bipartite edge list before handing it to CONDOR". The registry has no network-to-edge-list conversion action, so a TF-by-gene matrix fails as asked.
- **Q17 (ask, BONOBO).** The "not log-transformed" branch is dont for BONOBO. LIONESS-COEXPRESSION, which states no log requirement, would still give per-sample co-expression networks. `workflows` stays `["BONOBO"]` because the user names BONOBO and the deciding fact is BONOBO's requirement. A reply that also points to LIONESS-COEXPRESSION should not count as wrong.
- **Q11 and Q22 (vague, run).** The files fit one family each: DRAGON/LIONESS-DRAGON for Q11 and PUMA/LIONESS-PUMA for Q22. Neither prompt states the granularity, and neither states any uncertainty, so these are not ask items. They stay vague. The registry comment that LIONESS-DRAGON is "Sample-specific only: an aggregate request stays DRAGON's" is a routing note, not a contract condition for an unstated result.
- **Q40 (vague, run), class.** Only COBRA consumes a covariate file, but "run an analysis" names no result. Kept vague.
- **Q44 (vague, named).** "Something network-based" could be read as "any TF-gene network", which would make this a do with OTTER or GIRAFFE. It names no concrete result, though, and does not choose between OTTER's aggregate network and GIRAFFE's TF activity and signed matrix. Kept vague.
- **Q20 vs Q32 candidate lists.**
  - Q20 leaves out the workflows that need priors: none of PANDA, OTTER or GIRAFFE can run without a PPI, and the user has only "these two" inputs.
  - Q32 includes PANDA, LIONESS-PANDA, GIRAFFE and SAMBAR, although motif/PPI priors and SAMBAR's exon-length, cancer-gene and GMT files are not mentioned.
  - Both lists are defensible as candidates. They are not exclusive lists.
- **Q28 (vague, named).** PUMA does not take miRNA expression as a data layer. puma.yaml: "PUMA consumes a gene-by-sample expression matrix plus motif, PPI, and miRNA priors". Only DRAGON and LIONESS-DRAGON use both profiles. PUMA is kept as a candidate because the user names it. The gold reason ("built with priors") is accurate.
- **Q42 (do).** The user does not say "sparsify". Keeping full matrices plus per-sample p-values is exactly the `sparsify=true, save_pvals=true` mode (bonobo.yaml: "upstream retains the full co-expression matrix and writes p-values for downstream thresholding"). delta is left to be estimated, so the delta-with-sparsify range does not apply.
- **Q10 (do).** The user asks for activity "separate from" the TF's own mRNA. The registry is more careful: the TF's mRNA "is not an input to it ... its activity is not tied to its mRNA rather than independent of it". GIRAFFE still returns exactly the requested TF-by-sample activity and signed effects, so the item stays do.
- **Q46 (dont).** The refusal sentence is in lioness-puma.yaml's conventions: "An aggregate COBRA adjusted co-expression artifact is not a direct LIONESS handoff". The same file also gives `input_artifacts: [expression_matrix]`. lioness-puma.yaml's `input_checks`, however, carry no `refuses_input:coexpression_matrix` entry; only lioness-panda.yaml has one. The gold follows the contract text, but a code path that enforces only `input_checks` may not refuse this request.
- **Do items with no output path** (Q05, Q10, Q19, Q21, Q26, Q34, Q42, Q45). Every contract lists `output_file` or `output_dir` as required. This is a path the assistant can propose, not data the user lacks, so these items stay do.
- **Q07 (dont).** Causal proof is the registry's "causal" unsupported claim. `workflows` lists PANDA and GIRAFFE as the closest association alternatives; LIONESS-PANDA or OTTER would be equally acceptable mentions.
