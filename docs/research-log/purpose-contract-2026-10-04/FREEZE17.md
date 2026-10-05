# Log 375 freeze (A'): the priors read by the model, checked only for where the words come from

Frozen before anyone on the implementing side read the seventeenth held-out set (`heldout17/`),
which an isolated subagent writes after this freeze.

- Frozen change: `v_frozen.patch` (the diff of this change's eleven files against HEAD `e027b66`,
  `interpretation/intent_shortlist.py` included), sha256 `10130826014c`. Applied alone in a clean worktree
  (`.worktrees/netzoo-purpose-cand`), where its suite and live round run.
  It is Log 374's change (`t_frozen.patch`, never run) with these differences; reply and card only apart from
  the call's contract field.
  - `_priors_reason`: a priors reading stands when its quote is in the request -- nothing else. Log 374's
    negation and noun lists are removed (they could not accept "the gene count table is the whole of our
    data" or "remain uncharacterised", and let "binding preferences remain uncharacterised" pass as stated).
  - The reply shows the reading in the user's own words: "with the TF motif prior and PPI network you
    mentioned ("<quote>")" when it recommends workflows that need them; "which you said you do not have
    ("<quote>")" beside the ones it does not recommend for that reason.
  - When every candidate needs priors the user ruled out, the reply says none of the suggested workflows works
    without them, lists every candidate with its reason, and asks to be told if they can obtain them; the card
    is unchanged.
- Seen data (design only), heldout16 (Log 374's set), 32 x 3 calls per arm:
  - priors with the new call and quote-only check: stated 36/36, unstated 33/33, ruled_out 15/27 (F3 and T3
    right; F4 "the resulting gene count table is the whole of our data" 12/12 read as unstated). Read as
    stated when not stated: 0.
  - live prompt design 78/78 (false 5), claims 72/78 (false 0); new prompt design 74/78 (false 6), claims 70/78
    (false 0); false gaps 0 both -- within the same-code span measured on heldout15 (up to 5 design, 2-3 claim calls).
- Suite (clean worktree, this change alone): 3291 passed / 35 skipped (base 3275, 16 new); fingerprints legacy
  e920bf3b5d57, claims 743b2dd0d73a; condition prompt hash c820364a1123; policy hash b0570ff267af -- unchanged.
- **Another session's edits in the main working tree.** From 16:15 today, files outside this change were
  modified or added in the main checkout (semantic repair and claim validation: `semantic_repair.py`,
  `claim_invocation.py`, `claim_projection.py` (new), their tests, and others) -- not by this work. A first
  freeze patch taken from the whole working tree included them and was discarded unpublished; the suite
  counts of 3308 and earlier after 16:15 included their tests. The live rounds of Logs 371 and 373 ran at
  12:05 and 12:55-13:00, before those edits. From here this change is measured only in the clean worktree.
