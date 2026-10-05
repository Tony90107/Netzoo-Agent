# Log 368 freeze (B'): one-result cells that state their condition

Frozen before anyone on the implementing side read the twelfth held-out set (`heldout12/`),
which an isolated subagent writes after this freeze.

- Frozen change: `o_frozen.patch` (the whole working-tree diff of `scripts/` and `tests/` against HEAD
  `d0bb09e`), sha256 `5b365af0dcae`. No contract, prompt, model call or decision change.
  - `ClaimSupport` level `one_result` with `instead`, for individual_change: PANDA, PUMA, OTTER (one network
    from all the samples), COBRA (the co-expression associated with each covariate across all the samples),
    DRAGON (one two-layer network from all the samples); per-sample workflows LIONESS-PANDA, LIONESS-PUMA,
    LIONESS-PANDA, LIONESS-COEXPRESSION and BONOBO, LIONESS-DRAGON. Log 363's four multi-omic cells restored.
  - Reply line, after the workflows that answer, one per output: "- **X**, **Y** — each gives <output> it is
    given. With one sample per individual (per time point), that says nothing about a single individual; a
    result for one individual needs many samples from that individual. Per-sample workflows for the same
    data: ...". Never "cannot" or "does not answer" (Log 366: true only with one sample per individual; Log
    367: the request's words do not reliably say which).
  - Only for the candidates the reply offers (matched, hypothesis, advisory), not an aggregate named because
    its per-sample version also produces it (Log 366, T2-1/T2-2).
  - When no listed workflow has an answering cell, the paragraph comes first (after any gap paragraph). A
    tie's "These all fit; to choose, tell me:" becomes "These fit the result you described; X gives one
    result for all the samples it is given. To choose, tell me:" (not when a gap lead applies).
  - Card: a point ("X gives one result for all the samples: with one sample per individual that cannot show
    ...; Y gives one result per sample from the same data."); when no listed workflow has an answering cell,
    planning steps for the per-sample workflows are added after the card's own steps -- nothing is removed.
- Measuring function: `analyze_cannot.py selftest` 9/9 on the new shapes (live/cannot-selftest.txt).
- Seen data (s7-s10 candidate arms, 384 trials; live/seen-cannot-analysis.txt): one-result lines 45, all on
  individual-change items (P1 45/45); controls 0; added planning steps within acceptable 15/15; cards that
  dropped or reordered a step 0; line-level H2 384/384 (62 changed). Old C1, reported: 44/45 (s10 T2-3 names
  DRAGON, now as a condition). Five decisions fail the card on both sides (a tie of 9+ workflows exceeds the
  method card's 8 options; pre-existing, production skips the card; flagged as a separate task).
- Suite: 3275 passed / 35 skipped (base 3268, 7 new); fingerprints legacy e920bf3b5d57, claims 743b2dd0d73a;
  condition prompt hash c820364a1123; policy hash b0570ff267af -- unchanged.
