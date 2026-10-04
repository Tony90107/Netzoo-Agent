# Log 363 freeze: (a'') recommendations on ties

Frozen before anyone on the implementing side read the ninth held-out set (`heldout9/`),
which an isolated subagent was writing at the same time.

- Frozen change: `a2_frozen.patch` (the whole working-tree diff of `scripts/` and `tests/` against HEAD
  `eed283d`), sha256 `60b6d43fc0d46d89017c234afbf539dfcb4c59b0104f81cae8e926e417aa1e69`.
- What it adds (reply and card only; no decision field, no model call, no prompt change):
  - `interpretation/study_purpose_notes.recommended_actions`: on a tie, when the verified study purpose
    states a conclusion (not causal/prediction) for which some but not all candidates have a declared
    `CLAIM_SUPPORT` cell, recommend those candidates, narrowed by the data the request names: miRNA
    workflows need miRNA/small-RNA named; prior-based workflows need a motif/prior/PPI named and not ruled
    out ("expression only", "no motif", "nothing else"); two named omics layers prefer DRAGON/LIONESS-DRAGON.
  - The purpose paragraph gains "Start with X or Y: with the data you named, these answer it, as below.",
    recommended lines first; a tie's "These all fit; to choose, tell me:" becomes "These fit the result you
    described; for your question, start with X. To choose otherwise, tell me:".
  - Cards: those options get recommended=True and the "Recommended" badge, first, with a point.
  - `workflow_registry.CLAIM_SUPPORT` gains DRAGON/LIONESS-DRAGON cells (draft text, for the user's review).
- Dev check on seen live decisions (seventh and eighth sets, candidate arms, traced purposes): 13
  recommendations, 13 within the labelled acceptable candidates, 0 on controls (an unfiltered first version:
  18, 10 outside).
- Full suite 3268 passed (+ 6 new tests in the patch); fingerprints, condition-recommender prompt hash and
  policy hash unchanged.

Any change after this commit must be declared and reported separately from the ninth held-out results.
