# Log 372 freeze: tie replies led by the stated question, asking about data the answer depends on

Frozen before anyone on the implementing side read the fourteenth held-out set (`heldout14/`),
which an isolated subagent writes after this freeze.

- Frozen change: `r_frozen.patch` (the whole working-tree diff of `scripts/` and `tests/` against HEAD
  `99a2378`, `interpretation/intent_shortlist.py` included), sha256 `c10edc8d7134`.
  It is Log 370's change (`c5d65d4`, reverted in Log 371) with these differences; reply and card only.
- The TF motif prior and PPI network are a fact, never guessed (Log 371, B4; and the user's point that
  requiring a mention misses other wordings): `priors_status` is "named" (motif, prior, PPI, protein
  interaction, binding sites), "ruled_out" ("expression only", "nothing else", "no priors" ...) or "unknown".
  - named: workflows that need them can be recommended; ruled out: they are not ("needs ..., which you said you
    do not have");
  - unknown, and it changes what is recommended: the reply says the answer depends on it, gives "If you have a
    TF motif prior and a PPI network:" and "With only the data you named:" (or that none of the suggested
    workflows answers it without them), and asks; the card's question becomes "Do you have a TF motif prior
    and a PPI network?" with "Yes, I have ..." / "No, only the expression data" and an own answer. Otherwise
    nothing is asked.
  - Log 370's "needs an input the request never names" exclusion is dropped (it guessed "absent").
- miRNA workflows are recommended only when miRNAs are mentioned; with two named omics layers only the
  workflows that use both are (unchanged). These are never asked about.
- Several recommended workflows each say when to pick it first, from their registered prefer_when
  conditions not shared by the others ("Pick it first if you have only a handful of samples or you need a
  p-value for each edge."); the agent never maps a number to a cohort size (user decision, Log 315).
- Lines say why each fits the question, never how the algorithm works (user decision, Log 370).
- Seen data (s7-s13 candidate arms, 576 trials; live/seen-intent-analysis.txt): fired 133; recommended for the
  named data within acceptable 130/133 (s13 T5 x3: LIONESS-COEXPRESSION beside BONOBO for nine children, which
  the heldout13 label excluded by cohort size); against recommended_subset 38 labelled: exact 18, overlap 17,
  disjoint 3 (s13 A4, descriptive-only wording); controls/causal/prediction 0; candidates missing 0; other
  replies changed 0; cards changing options without a data question 0. Data questions 14, all in requests
  naming no prior with a TF-level question or only prior-based candidates (s8 R1, R2, T2, T3; s13 B4).
- Suite: 3283 passed / 35 skipped (base 3275, 8 new); fingerprints legacy e920bf3b5d57, claims 743b2dd0d73a;
  condition prompt hash c820364a1123 -- unchanged.
