# Log 383 freeze: the turn's data-needs plan (plan item 5)

This change was frozen before anyone on the implementing side had read the twenty-second held-out set
(`heldout22/`). An isolated subagent writes that set after this freeze.

## The frozen change

- File: `dp_frozen.patch`, sha256 `02867cff064c`.
- It is the diff of 23 files against `161f33d`.
- It is applied in the clean worktree `.worktrees/netzoo-dp-cand`, on top of `94b03f6`, whose code is identical to `161f33d`.
- The regex session's `interpretation/extraction.py` and `tests/test_path_extraction_speed.py` are not in it.

## What it is (Log 382's recommendation M1)

It starts from plan item 4's code as Log 381 ran it (`2015646`):
- the data-facts reading, with the own-words rule;
- per-workflow applicability, with the conditioned lead and dropped recommendations;
- fallback conditions.

On top of that it adds one per-turn plan (`interpretation/data_plan.py`, `contracts/data_plan.py`, `TaskDecision.data_plan`, `RequestRequirements.data_plan`).

1. **The need is read from the question.** `plan_needs` reads the study purpose's quoted questions first. If none were quoted, it reads the request's own questions: sentences ending in "?", with quoted text left out. Only if there are neither does it use the routing reading.
   - Before this, the need was inferred from the workflows routing listed.
   - A TF, regulator or regulatory word means "a motif prior and a PPI network". A miRNA word means "a miRNA list", plus the priors, which every miRNA workflow also needs.
   - When the only claims are prediction or causation, which no registered workflow supports, nothing is needed.
   - A data sentence ("maps of where transcription factors bind") is never read as a question.
2. **What the request has.** Each needed kind's state comes, in order of precedence, from:
   - a file the request binds;
   - the data-facts reading;
   - the request's words, when nothing read them.

   The reading is now called whenever the question needs a kind it does not bind, as well as when a listed workflow needs one.
3. **One action per kind:**
   - stated → none;
   - ruled out → say so, with that kind's own quote;
   - unstated → ask.

   If the priors are ruled out, miRNA is not asked about, because no miRNA workflow could run without them.
4. **Every reply shows the plan.**
   - Log 312's paragraph asks only what the plan asks.
   - The last step of `respond()`, `with_data_plan_reply`, adds whatever the reply still lacks: a question naming the data, or "… which you said you do not have ("quote")".
   - It applies to every guidance reply kind, the per-reading reply, and the routing-failure reply.
5. **The Log 381 H2 bug is fixed.** The ruled-out quote is taken in a fixed kind order (motif, PPI, miRNA), not from a set.

## Calibration on seen data only (not a verdict)

**The need reading (`plan_eval.py`).** These are the s20 and s21 sessions, 384 across both arms, each with its own recorded routing and purpose:

| Need | Correct | Notes |
|---|---|---|
| TF | 378/384 | The 6 misses are all s21 G4: the purpose read only its causal half, so the question was judged unanswerable |
| miRNA | 384/384 | |

Before the request's own questions were added as a fallback, TF was 365/384.

**The plan with each item's reading** (`dev20b`, `dev21` calls, current prompt):
- Where `data_question = priors`, the plan asks in 30/39 sessions per arm.
- The 9 misses are s21 G1 (×3, "has not shared them with us yet" read as ruled out), s21 T3 (×3, "PlantTFDB and STRING cover tomato" read as stated), and s21 G4 (×3, unanswerable).
- Where `data_question != priors`, it asks 0 times.
- It asks about miRNA where `data_question = mirna` in 3/3 sessions, and never elsewhere.

**Replay of the recorded sessions** (`dp_dev.py`, reply re-rendered and measured with Log 381's analyzer definitions):

| Measure | Recorded base | Recorded cand | With the plan (both arms) |
|---|---|---|---|
| Priors asks where needed | 8/39 | 15/39 | 30/39 |
| Needless priors asks | 20 | 3 | 0 |
| miRNA asks where needed | 0/3 | 0/3 | 3/3 |
| miRNA asks where stated or ruled out | 0 | 0 | 0 |

The two arms' different routing gives identical results.

## Checks

- Fingerprints: legacy `e920bf3b5d57`, claims `743b2dd0d73a`, unchanged.
- Data-facts prompt hash: `732e9fb607bd`, unchanged.
- Full suite in the clean worktree: 3397 passed / 35 skipped. That is 3359 plus 25 (`test_applicability.py`) plus 13 (`test_data_plan.py`).
- `TaskDecision`'s schema digest is updated, with a 2026-10-06 (Log 383) note.

## Known limits (stated before heldout22)

- **Borderline possession.** "Not shared yet" and "the database covers this species" are read as ruled out or stated. M2 in Log 382 would handle these through reply design; that is not in this change.
- **The purpose reading can drop part of a two-part question** (s21 G4).
- **The card.** Its "Inputs" choice follows the paragraph, but a question the last step adds appears in the reply text only.
- **The beginner group-network guidance** (`concept_answers`) still asks about priors on its own.
