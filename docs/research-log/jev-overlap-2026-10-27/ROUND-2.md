# Jev overlap round 2: no overlap reason on an uncredited row (2026-10-27) — declared before code

User decision (2026-10-27): a grouping row credited to no workflow, for which Jev finds no overlap asked, must not
print the overlap reason. It says the two-layer reason's layer 2 ("what was checked") instead. Declare gates first,
then measure offline. Same flag `NETZOO_JEV_OVERLAP`, same Jev question and threshold (P(overlapping) <= 0.3), same
branch `jev-overlap`.

## Problem (RESULTS.md, RESULTS-LIVE.md)

When gpt-4o-mini credits a grouping ask to no workflow (`delivered_by: []`) and types it `several_groups`, round 1
does not act: the overlap form is not the only blocker. The reply still says "not available here: no registered
workflow produces this. Registered grouping puts each item in exactly one group (...); none returns overlapping
memberships." That reason is wrong whenever the user never asked for overlap: live jo1 Q01 and Q13, replay j2f/j2g
Q01, Q13 t2 and Q37 t2. On real overlap requests credited to nothing (live ON5 and SN1, Jev not consulted in round
1), the reason is right and must stay.

## Change

1. A result row typed `group_membership=several_groups`, whose reading credits no produces entry, is read by Jev once
   (same question and cache as round 1).
2. P(overlapping) <= 0.3: the row records `doubted_forms=["group_membership"]`. `_form_reasons` then leaves out the
   overlap reason, so the line falls to whatever else code can verify, else layer 2 (`reason_layers.unmatched`).
3. Nothing else changes: the row's typed attributes, status, credits, second-opinion candidates and the call stay
   as they were. Jev failing, P > 0.3, or the flag off or in shadow: no change.

## Measurement (offline, no model call except cached Jev reads)

Each reading of population.json (44) plus the live jo1 turns typed several_groups is rebuilt with
`build_capability_check(task, recorded proposal)`. Each result row's line is rendered with `_status_line` and
checked for "none returns overlapping memberships". Calls are measured with the round-1 replays (harness 1388 +
`replay_jsets.py`).

## Gates

- G0, off = no change: harness replay with the flag off changes 0 of 1388 calls vs `replay-frozen.json`; the test
  suite has no new failures.
- G1, precision (hard): every rendered line of an overlap request (JN8 ON5 QN5 SN1, all readings) that printed the
  overlap reason with the flag on in round 1 still prints it.
- G2, recall: of the not-overlap readings whose rendered lines print the overlap reason with the round-1 code (flag
  on), >= 75% no longer print it.
- G3, calls unchanged: the flag-on harness replay and `replay_jsets.py` give the same calls as round 1 flag on
  (`replay-on.json`, `jsets-on.json`).
- G4, layer 2 only: every line that loses the overlap reason says only reasons that are already code-verified, or
  layer 2 (`is_unmatched`); it gains no new reason text.

Stop rule: if G1 fails, round 2 is withdrawn as declared. The Jev question is not reworded.
