# Log 374 freeze: the priors read by the study-purpose call, for the tie replies that ask about them

Frozen before anyone on the implementing side read the sixteenth held-out set (`heldout16/`),
which an isolated subagent writes after this freeze.

- Frozen change: `t_frozen.patch` (the whole working-tree diff of `scripts/` and `tests/` against HEAD
  `8a8f4cf`, `interpretation/intent_shortlist.py` included), sha256 `aabbb6750b74`.
  It is Log 372's change (`7a5f280`, reverted in Log 373) plus:
  - `StudyPurposeProposal.priors` ("stated" / "ruled_out" / "unstated") and `priors_span`, with a paragraph in
    `STUDY_PURPOSE_SYSTEM` (contract shape, not a rewording).
  - Loose verification (`_priors_reason`): the quote is in the request; "stated" names a prior noun (motif,
    prior, PPI, protein interaction, binding, interactome, regulon, TF targets, JASPAR, STRING ...) and has no
    negation in the quote; "ruled_out" has a negation or an "only" in its sentence, beside a prior noun, a
    TF/binding/interaction/regulation word or the expression data. A rejected reading is "unstated".
  - `StudyPurpose.priors` / `priors_quote` in state and traces; the tie reply uses the call's reading and
    falls back to Log 372's word lists only when nothing read it (the witnesses, an older state).
- Seen data (design only), heldout15 (Log 373's set), 32 x 3 calls per arm, two runs each:
  - priors: identical in both runs -- C1-C4 and T3 ("no transcription factor motif(s) or protein interaction
    ...") ruled_out 15/15; D, E, T6, T7 stated; A, B, F, T1, T2, T4, T5, T8 unstated.
  - live prompt (baseline worktree, b_eval) design 66/84 and 65/84, claims 71/78 and 70/78; new prompt design
    68/84 and 73/84, claims 68/78 and 70/78; false 0 and false gaps 0 in all four. The same-code span is up to
    5 design and 2-3 claim calls.
- Suite: 3293 passed / 35 skipped (base 3275; 18 new; Log 370's 4 pinned tie tests and the pinned state test
  updated); fingerprints legacy e920bf3b5d57, claims 743b2dd0d73a; condition prompt hash c820364a1123 --
  unchanged.
