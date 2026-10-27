# Jev overlap second read — offline results (2026-10-27)

Code on branch `jev-overlap` (from 62bade52): `interpretation/jev_overlap.py` (flag `NETZOO_JEV_OVERLAP`), hooks in
`interpretation/capability_check.py`, `interpretation/needed_facts.py` (new dimension `group_membership`), and
`graph/router_invocation.py` (event `core.jev_overlap`); `tests/test_jev_overlap.py`. No model call except Jev:
16 cached reads (`jev-cache.json`, `jev-cache-jsets.json`), under US$0.001. Stability check: see ROUND.md.

Raw: `replay-off.json` / `replay-on.json` / `compare-off-on.txt` (harness, 1388 readings), `jsets-off.json` /
`jsets-on.json` (`replay_jsets.py`, the 23 j1/j2 readings in population.json).

| gate | result |
|---|---|
| G0 flag off = no change | replay 0 of 1388 changed vs replay-frozen.json; tests 5062 passed, 51 skipped, 0 failed **PASS** |
| G1 overlap requests keep the refusal | 0 of 8 readings (JN8 ON5 QN5 SN1, vqbase + vqnew) became questions **PASS** |
| G2 >= 75% of not-overlap readings become the question | 25 of 37 = 67.6% **FAIL** |
| G3 flag on, whole replay corpus | 12 of 1388 changed, all DECLINE/full_gap -> ASK/needs_fact (Q26 x5, J22 x3, M45 x4); no new DO, no new DECLINE; right 609 -> 609 (these sessions are unlabelled) **PASS** |
| G4 reasons | a changed call asks the group_membership question (understanding line: "the request does not say whether one item may belong to several groups at once: if one group each: SAMBAR; if several groups at once: no registered workflow gives this"); unchanged overlap refusals keep their reason **PASS** |

As declared, a failed gate means the round has not passed; no live run is proposed without the user's decision.

## Why G2 failed (post hoc; not a gate)

The 37 not-overlap readings include 10 that were not refusals: 6 CLARIFY (Q13 t1, Q37 t1, Q37 t2), 3 DO
(vqnew Q26, J01, Q18) and 1 ASK (vqnew J22). Over the 27 not-overlap readings refused with full_gap, 23 became the
question (85%). The other 4 refusals are Q01 (x2), Q37 t2 (j2f) and Q13 t2 (j2g). In each, gpt-4o-mini credited
the grouping ask to no workflow (`delivered_by: []`), so the overlap form is not the only blocker and the hook does
not act. Their declines still print the overlap reason, which is a wrong reason left in place (a linking miss).

## Side effects seen outside the gates

- j1 J01 (gold DO): DO -> ASK. The several_groups row is now asked about, where the system had answered DO from
  another row (results_given). This is a needless question: a cost, not an error ([[netzoo-ask-cost-scoring]]).
- j2f Q18 (gold DECLINE: an expression matrix given to SAMBAR): DO -> ASK. Still not the right call, but it no
  longer approves the run.
- Jev reads: on every not-overlap text it read (14 distinct), P(overlapping) was 0. On both real-overlap texts that
  reached the hook, P was 1.0. Two of the four overlap requests never reached Jev, because no workflow was credited.

## Not measured

Turn 2 (the reply binding and answered_check) is covered by a unit test only
(`test_a_reply_naming_an_option_binds_in_code_and_settles_the_row_next_turn`). A reply that does not name an
option ("each tumor in one subtype") does not bind in code.
