# j4 gold review

Read: REVIEW-BRIEF.md, AUTHOR-BRIEF.md, items-author.json, workflows/*.yaml, scripts/workflow_registry.py. Output: items.json (48 items; check_format.py passes, all evidence quotes verbatim).

No opening call (`expected_call`) and no `final_after_*` call changed. Counts per group, sub, expected_call and dragon_control are unchanged.

## Changes

- **S08, `names_workflow`**: false -> true. The prompt asks for "a LIONESS co-expression network for each region", which names the registered workflow LIONESS-COEXPRESSION (lioness-coexpression.yaml: "Infer aggregate and sample-specific co-expression networks with LIONESS."). check_format.py's name matcher misses this spelling. FSN has no named/unnamed requirement, so the item still fits.
- **S10, `prompt` + `reply_restate` + `reason` + `evidence`** (prompt changed because the item did not fit V): the opening promised "to find modules in the plasma proteomics and metabolomics". That is a grouping result, and it is the same result `reply_result` picks ("communities of proteins and metabolites"). So the opening already named a concrete result, and no contract produces it from two-layer data (condor.yaml: "CONDOR consumes a weighted source-target bipartite edge list made from a validated regulator-gene network ..."), which makes DECLINE a defensible opening call. The changes:
  - prompt: "promised to find modules in" -> "promised to integrate"; "what it should look like" -> "what the result should look like".
  - reply_restate: "deliver the modules we promised ..." -> "deliver the integration of the proteomics and metabolomics that we promised."
  - reason: now says the user names no concrete result and the two-layer workflows give an aggregate or a per-sample network.
  - evidence: adds lioness-dragon.yaml: "Infer one sample-specific two-layer multi-omic partial-correlation network per sample with LIONESS-DRAGON."
  - Unchanged: the call (CLARIFY), the workflows (DRAGON, LIONESS-DRAGON), reply_result and final_after_result (DECLINE).
  - The V requirement for output-sounding words is still met by S25 ("some network analysis").
- **S13, `fact_keywords`**: ['mutation', 'expression', 'somatic', 'values', 'rna-seq'] -> ['mutation counts', 'somatic mutation', 'gene expression', 'expression levels', 'rna-seq']. "values" and bare "expression" are generic words, which the brief forbids.
- **S19, `evidence`**: removed workflow_registry.py "No registered workflow builds a model that predicts an outcome for new samples." That sentence is about classifiers for new samples, not lagged regulation. The remaining quotes (panda.yaml aggregate network; lioness-panda.yaml "derive sample-specific TF-to-gene networks"; registry "Build one network for each time point on the same genes and priors") decide the item. The call is unchanged.
- **S32, `reply_confirm`** (reply changed): "Yes, it's TPM expression from RNA-seq; we have no mutation calls." -> "Yes, it's TPM expression from RNA-seq." The removed clause was a fact not stated in the opening, and `reply_confirm` may only confirm the stated fact. The outcome is unchanged (sambar.yaml: "incompatible_input_artifacts: [expression_matrix]").

## Arithmetic rechecked (all correct, unchanged)

- S01: F = 300 + 150 = 450; 450*449/2 = 101,025 pairs x 50 = 5,051,250 <= 20,000,000 -> DO.
- S15: 300 genes: F = 500; 124,750 x 60 = 7,485,000 (DO). 800 genes: F = 1,000; 499,500 x 60 = 29,970,000 > 20,000,000 (DECLINE). lioness-dragon.yaml: "runs above 20,000,000 values are refused before they start".
- S43: 40 genes < 96 samples. cobra.yaml: "Expression must be a labeled gene-by-sample matrix with more genes than samples." -> DECLINE.
- S12 (2..5 of 182), S34 (defaults 2..4 of 410), S39 (3..6 of 64). sambar.yaml: "cluster=true requires 2 <= kmin <= kmax <= number of mutation samples." -> DO.
- S44: 2 samples < 3 (lioness-puma.yaml: "Require at least three expression samples ...") -> DECLINE after the reply.
- Sample totals inside prompts are consistent: S16 4x6 = 24, S20 4x4 = 16, S48 20x3 = 60.

## Borderline items kept unchanged

- **S33, S41 (GO, named workflow, DECLINE)**. One could read "each TF must be able to sit in several communities" and "a membership score for each subtype" as PARTIAL shape (a), an option the named workflow has no control for. I kept DECLINE because both ask for a different form of result, not a setting of the same result. S33 makes overlap a hard requirement ("must"); S41 asks for it "rather than one subtype per tumour". Running the plain partition would deliver none of what was asked. Supporting text: workflow_registry.py "CONDOR then gives each node one community and a core score."; sambar.yaml "It produces gene and pathway mutation-score matrices plus optional sample cluster labels."
- **S11 (U, BONOBO log/centered)**. If the answer were raw counts, the user could transform the data first. As asked, though, the run is not possible: bonobo.yaml "The agent requires the caller to declare log_transformed=true and centered=true because BONOBO assumes log-transformed centered expression." So the two answers still lead to different outcomes.
- **S35 (U, which file)**. A shape check could in principle tell a gene-by-gene matrix from a gene-by-sample one. However, the contract states the COBRA refusal as a request-level check, with the comment "no file inspection settles it". I kept ASK.
- **S05 (FN, OTTER -> CONDOR)**. OTTER's handoff needs "disjoint regulator/target IDs". TF genes could also appear as targets, but CONDOR only reports overlaps ("Report overlapping source and target IDs because the network should be bipartite"), and nothing stated breaks the condition. Kept DO.
- **S24 (N, BONOBO with significance per link)**. This needs sparsify + save_pvals, which is a valid combination (bonobo.yaml when {sparsify: true, save_pvals: true}). LIONESS-COEXPRESSION gives per-sample networks without p-values, so exactly one workflow matches. Kept DO.
- **S26 (U, PUMA without miRNA prior)**. After "no" the answer is DECLINE, not PARTIAL: the user asked for one result (a TF+miRNA network), so neither PARTIAL shape applies. An assistant may still suggest PANDA as an alternative.
- **S09 (FSN, aggregate PANDA over 30 regions)**. The FSN brief allows a cohort-level result. `reply_form` says positions do not matter, which the opening implies.
