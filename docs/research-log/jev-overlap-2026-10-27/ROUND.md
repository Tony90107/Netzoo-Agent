# Jev overlap second read (2026-10-27) — declared before any code

User decision (2026-10-27): Jev re-reads `group_membership`; when it disagrees, the system asks a closed-option
confirm question and the answer is bound in code. Run a 30x stability check first, then this file, and ask the user
before any live run. Branch `jev-overlap` from jev-guard 62bade52, worktree `.worktrees/netzoo-jev-overlap`.

## Problem

The capability check types a grouping request as `group_membership=several_groups` (each item may belong to several
groups at once). That value is a result-form limit (`CONDITIONS`, Log 402), so the row becomes `not_available` and
the reply says "Registered grouping puts each item in exactly one group (CONDOR ...; SAMBAR ...); none returns
overlapping memberships." When the user never asked for overlap, that is a wrong reason
([[never-wrong-reason]]), and it clears an exact registry match.

- j2 arm G: the reason is in the decline of Q01, Q02 (t2), Q13, Q18, Q29, Q36 (t2), Q38 (t2).
- `population.json`: every recorded reading (replay corpus + j1/j2 live) with a result row typed several_groups,
  44 readings and 21 distinct requests. All 44 rows are `not_available`.
- The quote-required fix 81912052 was reverted (4c18bdef): gpt-4o-mini never quotes real overlap requests, which
  then gave 4 false accepts.

## Labels (one labeller, me; one textual property)

Overlap = the request says that one gene, regulator or sample may belong to more than one group at once, or asks
for a membership strength or degree in each group.

- Overlap (4 distinct requests): JN8, ON5, QN5, SN1 (all vqbase, replay corpus).
- Not overlap (17): h5 Q26, J22, M45 ("separate TF-side and gene-side memberships" = one community per node,
  CONDOR), j1 J01, j1u W13, j2 Q01 Q02 Q08 Q13 Q18 Q29 Q36 Q37 Q38 (with the t2 combined texts of Q02, Q13, Q37).

These requests are all seen. A claim beyond them needs a fresh sealed set (not part of this round).

## Stability check (done before this file; `stability.py`, `stability.json`)

Jev question frozen in `overlap_q.py` (asks about the user's words, closed menu overlapping / one_each /
not_stated). 30 repeats each on Q26, Q01, Q29 (not overlap) and ON5, QN5, SN1 (overlap): 180 calls, US$0.0038.
Choices 30/30 identical on all six. Overlap controls: overlapping at confidence 1.0. Not-overlap items: not_stated,
confidence Q26 0.27-0.45, Q01 0.80-0.91, Q29 0.94-0.97; P(overlapping) 0, 0.05, 0 (Q26 splits one_each 0.44 /
not_stated 0.56). Hence the rule is stated on P(overlapping), not on the top choice's confidence.

## Change (flag `NETZOO_JEV_OVERLAP`, default off; `shadow` records, `on` applies)

1. A result row whose typed `group_membership` is `several_groups`, which that form alone rules out (the credited
   entries fit when `group_membership` is not stated), is read by Jev once (request + the row's quote).
2. P(overlapping) <= 0.3: the row waits on a new dimension `group_membership` (status `needs_fact`) with outcomes
   `one_group` -> the fitting entries, `several_groups` -> none. The existing needs_fact path asks
   "... one group each, or several groups at once?" and the existing `bind_answers` binds a reply naming an option
   (labels "one group each" / "several groups at once", no shared word). `answered_check` settles the row next turn.
3. Otherwise (P(overlapping) > 0.3, Jev error or timeout, flag off): the row is unchanged.

Jev never makes a DO or a DECLINE, never picks a workflow and writes no reason. Code lives in a new module
`graph/jev_overlap_call.py` plus small hooks; `jev_guard_call.py` is not touched.

## Gates (offline, all must pass; then ask the user about a live run)

- G0, off = no change: harness replay with the flag off changes 0 of 1388 calls vs `replay-frozen.json`; the test
  suite has no new failures (known env-dependent failure: `test_history_says_which_sessions_can_be_resumed`).
- G1, precision (hard): every reading of JN8, ON5, QN5, SN1 keeps its refusal; 0 of them become questions.
- G2, recall: of the not-overlap readings that replay, >= 75% turn into the group_membership question (per reading;
  also reported per distinct request).
- G3, scope: with the flag on over the whole replay corpus, every changed call is in the population and changes
  DECLINE -> ASK on `group_membership`; no new DO, no new DECLINE.
- G4, reasons: no changed call carries the overlap reason any more; refusals of the 4 overlap requests keep it.

Stop rule: if G1 fails, the change is withdrawn as declared. No rewording of the Jev question after a run
([[netzoo-no-prompt-wording-fixes]]).

## Not measured offline

Turn 2 needs replies, so the binding and the follow-up turn are checked only live. Proposed (needs user approval;
lean testing): <= 16 sessions, flag on, 1 rep: the 7 j2 items above, h5 Q26, j1 J01 with a reply naming an option,
and JN8 ON5 QN5 SN1 as controls; gpt-4o-mini + Jev, about US$0.05.
