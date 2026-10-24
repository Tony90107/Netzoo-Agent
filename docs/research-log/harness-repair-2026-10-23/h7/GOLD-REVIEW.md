# h7 gold review

Reviewer read only `AUTHOR-BRIEF.md`, `items-author.json`, `workflows/*.yaml` and `scripts/workflow_registry.py`.
Output: `items.json` (36 single, 14 multi; `author_note` kept, `review_note` added).

## Changes

No `expected_call`, `also_acceptable`, `workflows`, `final_call`, `final_workflows`, `new_request_call` or
`new_request_workflows` changed. Two scripted replies were edited; no prompt changed.

- **M05**, `deciding_fact.answer` (reply; answer_form `natural`)
  - before: "I only need to see which metabolites and cytokines rise and fall together in each patient once the others are accounted for; proving what causes what is for our follow-up experiments."
  - after: "I only need to see which metabolites and cytokines rise and fall together in each patient once the others are accounted for; working out the mechanisms is for our follow-up experiments."
  - why: a `natural` answer must imply one side "without the option words" (AUTHOR-BRIEF.md: "2 answer in natural words that imply one side without the option words"); the turn-1 options are "cause and effect" vs "which levels are linked", and "causes" is the first option's word (also in `match_keywords` as "cause"). The answer still implies the association side, so the final gold is unchanged: lioness-dragon.yaml: "partial correlations are conditional associations, not causal relationships." (40 + 25 = 65 features, 65*64/2 = 2,080 pairs x 90 = 187,200 values, under the 20,000,000 cap.)
- **M10**, `deciding_fact.answer` (reply; internal inconsistency)
  - before: "Every volunteer gave one blood draw, and the plasma from that draw was split between the two labs."
  - after: "Every volunteer gave one blood draw, and the serum from that draw was split between the two labs."
  - why: turn 1 says the proteins are "serum proteins"; a reply saying the plasma was split contradicts it. Meaning for the deciding fact is unchanged (same volunteers in both tables), so the gold stays DO with DRAGON: dragon.yaml: "DRAGON consumes exactly two paired sample-by-feature continuous omics tables".
- **M10**, `final_reason`: "Split plasma from one draw ..." -> "Split serum from one draw ..." (wording only, to match the edited reply).

## Confirmed (recomputed)

- LIONESS-DRAGON cap (lioness-dragon.yaml: "runs above 20,000,000 values are refused before they start"): S24 1,000 features -> 499,500 x 60 = 29,970,000 (DECLINE); S29 600 -> 179,700 x 60 = 10,782,000 (DO); M01 filtered 210 -> 21,945 x 80 = 1,755,600, full 2,100 -> 2,203,950 x 80 = 176,316,000; M05 65 -> 2,080 x 90 = 187,200.
- COBRA (cobra.yaml: "more genes than samples"): S03 1,800 > 140; S22 384 > 150 vs 96 < 150; M09 2,000 > 300 vs 250 < 300.
- SAMBAR (sambar.yaml: "cluster=true requires 2 <= kmin <= kmax <= number of mutation samples."): S12 kmax 8 vs 7/15; S13 6 <= 140; S31 5 <= 85; M08 6 <= 160.
- Sample minimums: S25/S32 three vs two (lioness-coexpression.yaml: "Require at least three samples"); S33 four vs two; M11 three vs two (bonobo.yaml: "at least three total samples").
- Settings: S27 lam 0.1, gamma 0.5, iterations 100, edge_list all inside OTTER's declared ranges; S36 delta 0.5 with sparsify (bonobo.yaml: "With sparsify it must be above 0 and below 1/3") -> DECLINE; M11 lambdas 0.3/0.6 in [0, 1]; M12 lam 1.3 > maximum 1 -> DECLINE.
- PARTIAL shapes: (a) S02 (puma.yaml: "controls: []"), S30 (otter.yaml: "The verified API has no independent sparsity penalty or threshold parameter."); (b) S28, S34, M08 (one result produced, the other produced by no workflow).
- Pairs: P1/P2/P3 differ by one key fact each (word-level diff) with different calls; Q1/Q2 keep the same call.
- Every evidence string is a verbatim substring of the file it names; all text is ASCII.

## Borderline, kept unchanged

- **S14 (and M06 turn 1)**: LIONESS-PANDA also writes the aggregate network (lioness-panda.yaml: "description: Infer aggregate PANDA and sample-specific LIONESS-PANDA networks."), so a LIONESS-PANDA run would cover either answer. Kept ASK with empty `also_acceptable`: the user says they have not decided which result they need, the answers select different workflows (PANDA vs LIONESS-PANDA), and starting N+1 PANDA runs on an undecided request is not the request as asked.
- **S19**: the two-layer network alone is doable; the undecided third layer is not (dragon.yaml: "no sample_metadata, motif, PPI, expression-matrix, or three-layer argument"). Kept ASK: which network the user wants is still open and the two answers give DO vs DECLINE. An answer that says two layers work and asks whether to proceed is the expected shape.
- **M10 turn 1**: sample-ID equality is also a file-scope check (dragon.yaml: "Layer 2 is reordered to layer 1 only after exact sample-ID set equality is proven."), but no files are named and the user states the doubt, so ASK stands. Same for **M01** (feature counts readable from tables that are not named) and **M07** (overlapping source/target IDs would show in a file that is not named).
- **S16 / M02**: log-transformation might be guessed from value ranges, but the contract asks for a declaration (bonobo.yaml: "The agent requires the caller to declare log_transformed=true"), so `file_checkable` false stands.
- **S20**: PANDA TF IDs can also appear as targets; CONDOR only reports overlaps (condor.yaml: "Report overlapping source and target IDs because the network should be bipartite.") and PANDA -> CONDOR is registered (panda.yaml: "handoff_targets: [run_condor]"). DO kept.
- **S33**: whether every miRNA appears in prior column one is a file-scope check (lioness-puma/puma conventions), not a request-level fact; the sample count stays the one deciding fact.
- **S12 / S31 / M08**: the GMT source only sets `gmt_msigdb`, which accepts either value; not a deciding fact.
- **M04**: binarized 0/1 calls are finite numbers; DECLINE rests on the continuous requirement (dragon.yaml: "Values must be finite continuous numeric measurements."; "accepted_input_modalities: [multi_omic_continuous]").
- **M03 / M14** `match_keywords` include the generic word "only"; kept because turn 1 leaves one open fact, so a question it matches is very likely the deciding-fact question.
- **M06**: "24 zebrafish fins" with "one per fish" reads as one fin per fish; consistent enough, not changed.
- **Cross-part reuse**: several multi-turn items reuse a single-turn deciding-fact pattern (BONOBO log-transformation, COBRA panel size, SAMBAR somatic vs germline, PANDA vs PUMA regulators, PANDA vs LIONESS-PANDA granularity, QC'd sample count). The brief's no-reuse rule is stated for Part 1 only and each item's gold is independently right, so nothing was changed; noted for whoever scores per-pattern results.

## Counts after review (unchanged from the author's)

- single: do/dont/ask/vague 9 each, each 3 named / 3 goal / 3 run; DO 9, PARTIAL 4 (shape a 2, shape b 2), DECLINE 5, ASK 9 (explicit 7, silent 2), CLARIFY 9; irrelevant-uncertainty DO items 3; minimal pairs 3, paraphrase pairs 2.
- multi: answer 4 (option words 2, natural 2), volunteer 2, correct 3, switch 2, unknown 3; t1 ASK 12, CLARIFY 2.
