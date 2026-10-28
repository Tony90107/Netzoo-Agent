# j6 gold review

Read: REVIEW-BRIEF.md, AUTHOR-BRIEF.md, items-author.json, workflows/*.yaml, scripts/workflow_registry.py. Output: items.json (30 items, check_format.py passes, all evidence quotes found verbatim).

## Changes

- **X04, `uncertainty`**: `none` -> `explicit`. The opening request says in so many words that the user is not sure which result they want. AUTHOR-BRIEF.md: `uncertainty` is "explicit" when the opening request "states the user is unsure of something". Call stays CLARIFY.
- **X10, `workflows`**: `["PANDA", "OTTER"]` -> `["PANDA", "OTTER", "GIRAFFE"]`. GIRAFFE also builds one aggregate TF-to-gene network from expression, motif and PPI, so it also fits the doable part. giraffe.yaml: "produced_artifacts: [regulatory_network, tf_activity_matrix]", and its handoff_contract says it "returns the aggregate TF-by-gene R matrix". `reason` was updated to name all three, and the GIRAFFE quote was added to `evidence`. Call stays DO.
- **X12, `prompt`** (fixes an internal inconsistency): "We infected 12 mice with influenza and collected lung tissue at day 0, day 3 and day 7" -> "We infected mice with influenza and collected lung tissue from 12 mice at each of day 0, day 3 and day 7". The old text had each of 12 animals giving lung tissue at three time points. Lung harvest ends the animal, so that cannot happen. The 36-sample total, the call (DO, LIONESS-PANDA) and the replies are unchanged. lioness-panda.yaml: "Require at least three expression samples before execution."

## Borderline items kept unchanged

- **X27 `names_workflow` = false**: the prompt says "LIONESS" together with co-expression. That points at LIONESS-COEXPRESSION, but it is not one of the exact registered names, and check_format.py also counts it as not named. The flag stays false. The ASK gold is the same either way (lioness-coexpression.yaml: "Require at least three samples"; 2 fails, 5 passes).
- **X25 `uncertainty` = none**: "haven't settled" says the user has not decided, not that they are unsure of a fact. It is not as direct as X04's "not sure which".
- **X21 (N, DO, COBRA)**: the numeric table is described as holding the fibrosis score. Batch is stated as four batches but not said to be coded as numbers. cobra.yaml: "Design rows must use exactly the expression sample IDs and numeric covariates." Coding a known batch label as numbers is routine, and nothing stated breaks the condition. 15,000 genes > 200 samples.
- **X15 (FSN, DO)**: BONOBO also gives per-sample co-expression. It is left out of `workflows` because it needs log-transformed and centered values to be declared ("BONOBO requires it"), and the prompt does not state either. LIONESS-COEXPRESSION fits as stated.
- **X23 (FD) evidence**: it quotes granularities only. No contract states that it refuses dynamic models, so the DECLINE rests on "no contract produces it", which matches the DECLINE definition.
- **X17 (P)**: cross-layer penalty 0.2. It is a setting the contract does not expose ("does not expose a separately tunable third cross-layer penalty such as lambda_inter"), not a value outside an exposed setting's range, so PARTIAL shape (a) stands.
- **X08 (U, data_property)**: if the values are not log-transformed, the answer is DECLINE for the BONOBO run the user named, even though LIONESS-COEXPRESSION would not need that declaration.
- Arithmetic checked: X07 500*499/2*80 = 9,980,000 (< 20M); X22 550*549/2*100 = 15,097,500 and 800*799/2*100 = 31,960,000; X05 2 <= 2 <= 5 <= 140; X02 18,000 > 90; X21 15,000 > 200; X03 1 < 2 (GIRAFFE).
