# Log 365 freeze: "cannot" cells (one result for all the samples, asked about individuals)

Frozen before anyone on the implementing side read the tenth held-out set (`heldout10/`),
which an isolated subagent writes after this freeze.

- Frozen change: `c_frozen.patch` (the whole working-tree diff of `scripts/` and `tests/` against HEAD
  `b138b82`), sha256 `c8ef59f35115`.
- What it adds (reply and card only; no decision field, no model call, no prompt change):
  - `ClaimSupport` gains the level `cannot` and the field `instead`. Five declared cells, all
    `individual_change` for any design: PANDA, PUMA, OTTER (one network from all the samples), COBRA
    (the co-expression associated with each covariate across all the samples), DRAGON (one two-layer
    network from all the samples). Each names the per-sample workflows for the same data
    (LIONESS-PANDA, LIONESS-PUMA, LIONESS-PANDA, LIONESS-COEXPRESSION and BONOBO, LIONESS-DRAGON).
    An undeclared cell still says nothing.
  - Log 363's four reviewed multi-omic cells (DRAGON group difference for groups and paired;
    LIONESS-DRAGON group difference and individual change) are restored.
  - Reply: in the purpose paragraph, after the workflows that answer it, one line per reason:
    "- **X**, **Y** — do not answer this: each gives ..., so when each individual gives one sample (per
    time point) there is no result for an individual. Per-sample workflows for the same data: ...".
    When no listed workflow answers, the paragraph comes first (after any gap paragraph). A tie's
    "These all fit; to choose, tell me:" becomes "These fit the result you described, but X cannot show
    which individuals change or stand out; to choose, tell me:" (not when a gap lead already applies).
  - Card: a point naming the workflows that cannot and the per-sample ones; when no listed workflow
    answers, planning steps for the per-sample workflows (planning still asks before anything runs),
    and no planning step for the one that cannot.
- Measuring function checked before freezing: `analyze_cannot.py selftest` (live/cannot-selftest.txt):
  9/9 synthetic cases judged as intended (additions inside a paragraph, a new first paragraph and the
  declared lead pass; a changed word, a removed or reordered line, an undeclared line and the gap lead fail).
- Seen data (s7-s9 candidate arms, 288 trials; live/seen-cannot-analysis.txt): noted 32; the flagged
  workflow outside the labels' acceptable set 32/32; notes on controls 0; per-sample next steps within
  acceptable 9/9; per-sample workflows named beside others outside acceptable 8/23 (LIONESS-PUMA without
  miRNA data, already a routed candidate); line-level only-adds 288/288 (43 changed).
- Suite: 3273 passed / 35 skipped (base 3268, 5 new); fingerprints legacy e920bf3b5d57, claims
  743b2dd0d73a; condition prompt hash c820364a1123; policy hash b0570ff267af -- unchanged.
