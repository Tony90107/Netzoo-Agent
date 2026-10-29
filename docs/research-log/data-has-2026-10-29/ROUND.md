# What data the user says they have, read as its own closed question (2026-10-29, user "修 Q18")

## Problem

j2 Q18: "subtype ... by how strongly each pathway is hit by mutations ... What we have is a bulk RNA-seq expression
matrix" (gold DECLINE: SAMBAR takes mutation data; its contract lists an expression matrix as incompatible). The
guard's typed data check asks Jev one question -- "Which kind of data does the user say the analysis should be built
from?" -- and the request names both the analysis's data (mutations) and the user's (expression): Jev read "several"
0.32 (data-first round) and expression_matrix 0.31 (carry-links), under the 0.7 threshold, so nothing rules SAMBAR out.
Today Q18 is refused only when the re-reading happens to lose the SAMBAR link (DECLINE full_gap, a wrong reason); that
is why carry-links failed K2.

## Change (a new typed field, not a reworded question)

- A second closed Jev question beside the guard's data question, frozen in `interpretation/data_has.py`: **"Which
  kind of data does the user say they have?"**, with the guard's own `DATA_CRITERIA` options (same kinds, same words).
- The guard's existing rule (`ruled_out`: a typed contract field -- incompatible_input_artifacts, a refused input, or
  a single kind outside the declared input_artifacts -- at confidence >= 0.7) is applied to this read too; a workflow
  is ruled out when either read rules it out. Nothing else changes: the guard still only asks its data confirm
  (`jev_condition`), never declines from the read alone.

## Measurement (offline, before any code in the app path; prompts only, real Jev, cached)

Every j1-j8 item with a gold call and workflows (opening prompts; ~330). For each: the guard's existing data read and
the new has-read; `ruled_out` for each gold workflow.

## Gates (declared before any Jev call)

- **D1 precision (hard)**: on gold DO / PARTIAL items, the number whose gold workflow the union (existing OR new) rules
  out is <= the number the existing read alone rules out (no new false confirm).
- **D2 recall**: j2 Q18 ruled out for SAMBAR by the new read; and on gold-DECLINE items of the data-type groups (T
  incompatible / not_accepted, N n_decline with a data reason) the union catches >= the existing read.
- Reported: every item where the two reads disagree. Cost cap US$0.10.

Pass -> build it in the guard (jev-guard session agreed first), replay + tests, then live. Fail -> stop.
No gate is changed after the run.

## Addendum after the offline measurement, before the code (jev-guard review)

- The confirm names the kind that ruled the workflow out: `check_typed_data` records `ruled_by` ("data" / "has") and
  the confirm question is built from that read's kind; the contract line is `ruled_out`'s, unchanged.
- **D3 chains (reported, then controls)**: count the 348 items whose gold is a registered chain or handoff (e.g.
  PANDA -> CONDOR from expression) and what the union does to them; if none, 2-3 such requests become declared live
  controls (hard: no chain control ends in a confirm-then-decline).
- **D4 stability (hard)**: the has-read 10x on j2 Q18 and on two gold-DO controls: Q18 >= 0.7 on expression in >= 8 of
  10; the controls never rule out their gold workflow.
- D3 count (no Jev call): 2 of the 348 are gold chains listing CONDOR beside PANDA -- j5 W17 (has expression 0.67, data
  0.69) and j8 Z14 (several); the union rules neither out. **D4 controls are these two** (W17 is the closest to the
  threshold): each must never rule out CONDOR in 10 has-reads.
