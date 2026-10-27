# j2 gold review

Read: REVIEW-BRIEF.md, AUTHOR-BRIEF.md, items-author.json, workflows/*.yaml, targeted greps of scripts/workflow_registry.py. Every call, workflows list, final_after_* object, count and evidence quote was checked; all evidence quotes appear in the named files.

## Changes

- Q32, fact_keywords: `["how many patients","100","200","second batch","patients"]` -> `["how many patients","100","200","second batch","patient count"]`. "patients" alone is generic (it would appear in almost any question about this cohort). Deciding text: lioness-dragon.yaml: "runs above 20,000,000 values are refused before they start" (500 features -> 124,750 pairs; x100 = 12,475,000, x200 = 24,950,000, recomputed and correct).
- Q42, fact_keywords: `["how many genes","genes","120","2,000","filtered"]` -> `["how many genes","gene count","120","2,000","filtered"]`. "genes" alone is generic. Deciding text: cobra.yaml: "Expression must be a labeled gene-by-sample matrix with more genes than samples."

No call, also_acceptable, workflows, reason, evidence, deciding_fact, missing_core or final_after_* value was changed. No prompt or reply was changed.

## Borderline items kept unchanged

- Q28 (U, DRAGON layers same or different patients): dragon.yaml has a file-scope check, "Layer 2 is reordered to layer 1 only after exact sample-ID set equality is proven." Kept as ASK because that check proves ID-set equality, not that the individuals are the same (two recruitment waves can reuse an ID scheme), so the file check does not reliably settle the user's stated doubt; both answers still lead to different outcomes.
- Q02 (U, SAMBAR mutation vs expression table) and Q05 (U, GIRAFFE gene-by-sample vs gene-by-gene matrix): the file-scope checks (sambar.yaml "Mutation rows are unique sample IDs ... with non-negative numeric values"; giraffe.yaml identifier checks) would not reliably reject the wrong table (non-negative counts / gene IDs in header pass), so no automatic check settles it. Kept ASK.
- Q27 (U): names_workflow is true because the prompt names COBRA (as the source of the adjusted matrix), though the requested workflow is not named; consistent with the brief's definition. lioness-panda.yaml marks the COBRA refusal as request-level ("no file inspection settles it").
- Q38 (V, "modules" with a TF-gene edge list) and Q36 (V, "what could this toolkit tell me" with SAMBAR inputs): only one workflow takes the stated data, but neither prompt asks for a result (CONDOR communities; SAMBAR scores vs subtypes with which cluster range), so CLARIFY kept; "modules" is the intended output-sounding trap word.
- Q21 (U, PUMA): the user calls the miRNA input a "target prediction file" while puma.yaml's mirna_file is "one miRNA identifier per line"; the question about whether the miRNA file exists still decides DO vs DECLINE via puma.yaml required_inputs. Kept.
- Q22 (U, BONOBO log-transformed): bonobo.yaml "The agent requires the caller to declare log_transformed=true and centered=true"; no file check detects log scale, so ASK kept and "not log-transformed" -> DECLINE as asked.
- Q41 (T, CONDOR from raw expression): the prompt also says no priors; that is part of the single stated data fact ("only an expression table"), condor.yaml "CONDOR does not consume the raw expression matrix directly." Kept.
- Q01 / Q08 are near-duplicate CONDOR situations in different groups (N vs TC); both golds correct.
