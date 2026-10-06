# Log 381 freeze: the applicability judgement, redone (plan item 4, second round)

This change was frozen before anyone on the implementing side had read the twenty-first held-out set
(`heldout21/`). An isolated subagent writes that set after this freeze.

## The frozen change

- File: `ar_frozen.patch`, sha256 `3214de009912`.
- It is the diff of 19 files against `161f33d`. These are the same 19 files as Log 380's `b536b95`.
- It is applied in the clean worktree `.worktrees/netzoo-ar-cand`, on top of `d55e0f1`, whose code is identical to `161f33d`.
- It does not touch the regex session's `interpretation/extraction.py`.

## What it is

It is Log 380's candidate (`0a70c15` + amendment `b536b95`), with one change for each failure found in Log 380's results.

1. **Whose data (T1, T2).**
   - The problem: a "stated" reading stood whenever its quote was in the request. That included "My supervisor says we need a motif prior" (T1) and "Last year we used JASPAR motifs … on a different pig cohort" (T2).
   - The change: the quote must now also lie in the user's own, current words, otherwise the reading becomes unstated. "Own, current words" means plan item 1's authority-bearing text (`admissible_request_text`), which leaves out reported speech, quotations and history. Punctuation is ignored in the match, because that text is split at commas.
   - Where: `graph/data_facts_call.verify_data_facts`.
   - Code only: the prompt and schema are unchanged. Data-facts prompt hash `732e9fb607bd`, as in Log 380.
2. **Per-reading replies (G1).** With a data-facts reading, Log 312's "What your data allows" paragraph now also applies to the `hypothesis_routes` reply (Log 248). Without a reading, that reply is unchanged.
3. **Questions no workflow answers (F4).** When the study purpose states only conclusions no registered workflow supports (prediction, causation), no input is asked about. Data the request ruled out is still stated.
   - Where: `input_alternatives.asks_for_data`. The reply and the card both use it.
4. **Fallbacks (T3-3).** A fallback whose workflow the reading judged short of data now leads with the condition. For example: "Fallback candidate: **PUMA**, but it needs a miRNA list, which you said you do not have."

## Tried and withdrawn before this freeze

A fourth reading state, `mentioned_only`, with its prompt lines.
- On seen sets, it fixed T1 (3/3) but not T2 (stated 3/3).
- It also cut ruled-out recall:

  | Set | Ruled-out recall |
  |---|---|
  | heldout16 | 12/27 |
  | heldout17 | 15/27 |
  | heldout18 | 13/27 (was 27/27) |
  | heldout20 | 6/36 |

- That is the prompt-wording fragility (`netzoo-no-prompt-wording-fixes`).
- Its calls are kept as `mo16`–`mo19-calls.json`. Its heldout20 calls were deleted by mistake; the numbers above are from the run's printout.

## Calibration on seen data only (not a verdict)

**Stored readings (Log 380's dev16–19 calls) re-verified with rule 1.** No reading was downgraded on any of these sets:

| Set | Stated | Ruled out |
|---|---|---|
| heldout16 | 36/36 | 18/27 |
| heldout17 | 33/33 | 17/27 |
| heldout18 | 33/33 | 27/27 |
| heldout19 | 45/45 | 24/24 |

heldout19 T2 ("My supervisor said to …", with the user's own TF motif prior and PPI network) stays stated.

**heldout20 re-read with the current prompt** (`dev20b-calls.json`, 96 calls):
- Priors: false stated 0, stated 30/30, ruled out 36/36, unstated kept 30/30.
- T1 and T2: 6/6 "stated" readings downgraded.

**Log 380's candidate sessions replayed** (`ar_dev.py`, s20, with each session's recorded proposal re-verified and routing's applicability step re-run):
- Priors asks where `data_question = priors`: 6/15 → 14/15. T2-1 had no reading at all.
- Asks elsewhere: F4 3 → 0.
- Unconditional offers: T3-3 PUMA → none.
- Ruled out still said 17/17.

## Checks

- Fingerprints: legacy `e920bf3b5d57`, claims `743b2dd0d73a`, unchanged.
- Tests: `test_applicability.py` has 25 tests; 5 are new for this round. One of them checks that a stated quote outside the user's own current words becomes unstated, and that a quote with commas inside them stays.
- Full suite in the clean worktree: 3384 passed / 35 skipped. Base `161f33d` has 3359; the 25 extra are `test_applicability.py`.
