# Log 379 freeze: the research purpose decides among the tied tools (plan item 3)

Frozen before anyone on the implementing side read the nineteenth held-out set (`heldout19/`).
An isolated subagent writes that set after this freeze.

**Frozen change:** `pf_frozen.patch`, sha256 `7a3fccc68099`.
- It is the diff of `scripts/` and `tests/` against `5a12dea`, new files included, and covers 15 files.
- It is applied in the clean worktree `.worktrees/netzoo-item3-cand`.
- It does not touch the regex task's uncommitted `interpretation/extraction.py`.

**What it does:**
- **Order.** The study purpose (b‴'s verified design and claims, prompt unchanged) is read before routing. Before this change it was read after routing and only for the reply.
- **Registry typing (Python-only).** Each `CLAIM_SUPPORT` cell gets three new fields:
  - `evidence`: `direct`, `tested`, `descriptive` or `one_result`.
  - `quantity`: `same` or `other`. `other` applies only to GIRAFFE's group and individual cells.
  - `stronger`: the registered per-sample workflow that the cell's own text names.

  The cell texts are unchanged.
- **Selection (`routing/purpose_selection.py`).** It runs on a method tie that has one reading, no stated research hypotheses, no earlier recommendation, and a supported conclusion. Causation and prediction keep their gap.
  - Pool: the candidates plus the `stronger` workflows their cells name.
  - Every candidate must have a declared cell; undeclared means unknown (CC1).
  - Score: same quantity first, then evidence (direct > tested > descriptive > one result).
  - A workflow can be picked only if the inputs it needs beyond expression are stated:
    - TF priors: the Log 376 data-facts call reads "stated" (the prompt is unchanged, `93cd57a96d46`), or the files are bound.
    - miRNA: a quoted miRNA regulator reading, or a bound file.
    - COBRA's design matrix: a verified two-group design, or a bound file.
  - The pick must be the single best and must beat at least one candidate. Otherwise there is no pick.
- **The pick.** It becomes the decision's `advisory_recommendation`, with an `AdvisoryCondition` of axis `study_purpose` and the quoted conclusion.
  - The picked workflow is added to `hypothesis_actions` if it was not already a candidate. No candidate is removed.
  - The condition recommender is skipped for that turn.
  - The question is the same as the condition recommender's: "Should I use X, or does another listed option fit your study better?".
  - Event: `routing.purpose_selection`, with every workflow's fit. State: `purpose_selection` and `data_facts`. `RequestRequirements.purpose` records the chain.
- **The reply.** A compact form under the user's Log 370 rule (why for your question, no algorithm text):
  - "Based on what you said — "<quote>" — **X** fits better: <registry reason>."
  - The registry's other-reading note.
  - Concerns only when they are stated.
  - The existing stage-1 lines "For your question (…)" for every listed workflow.
  - The question.
- **The card.** The pick is marked Recommended, with "Fits what you said: <registry reason>".
- **The data-facts call** runs only when a workflow that needs priors could be picked. "unstated" and "ruled_out" both withhold the pick. This fixes Log 377's never-ask bug class by construction: no question is asked, so nothing can wrongly skip one.

**Seen data only (calibration, not a verdict):**
- Log 378's 27 baseline decisions (priors taken from the prompt): picks are A1 → LIONESS-PANDA ×3 and B1 → COBRA ×3. Every other prompt gets no pick.
- `pf_dev.py` over the recorded live decisions of sets 7–18:
  - 552 sessions; PF applies to 162 and picks in 9.
  - Of the 9 picks, 6 are in `recommended_subset` and 3 are acceptable only (s10 F2d → COBRA, subset empty).
  - 0 picks are unacceptable, and 0 fall on items where no recommendation is expected.
  - The no-pick reasons are: inputs not stated 83, an undeclared candidate 37, more than one best 33.
  - For sets other than 18, the priors are the annotation's (an oracle), and sets 10, 12 and 15 have no priors label at all.

**Checks:**
- Clean worktree: 3382 passed / 35 skipped. The base `9f95e14` had 3359; 23 tests are new, in `test_purpose_selection.py`. Updated tests pin the new call order.
- Fingerprints: legacy `e920bf3b5d57`, claims `743b2dd0d73a`.
- Study-purpose prompt and schema: `e2af95adf863` and `83461bb34d77`. All unchanged.
