# per-group-scale -- offline results (2026-10-29)

| Gate | Result |
|---|---|
| P1 unit tests (`tests/test_per_group_scale.py`, 4) | pass. per_group credits aggregate entries exactly as whole_cohort does (LIONESS-PANDA also writes the cohort network, so it carries both scales -- unchanged design); per_sample still rules OTTER out; per_group counts as a stated scale for the scale question; jev-guard's opposite direction: a bound "several groups at once" is left out of the condition check AND still refuses CONDOR through `answered_check`. |
| P2 enum limit | pass (`test_contract_limits.py`); one value added to `scale`. |
| Rebuild of recorded j6 X30 t1 | recorded reading (scale per_sample): `not_available`, full gap. Same reading with scale per_group: `available ['otter.tf_gene_network']`, no full gap. |
| P3 flags-off replay | 1388 readings, right 609 -- output byte-identical to main's replay (`check-reserve-2026-10-28/sa-off.json`): 0 right -> wrong, 0 changes (no recorded reading says per_group). |
| P3 clean-env tests | 5166 passed; 2 known unrelated failures (explicit_panda characterization, history_says_which_sessions_can_be_resumed). |

Offline all gates pass. Whether gpt-4o-mini picks per_group for X30-like wording -- and keeps per_sample on the
controls -- is P4 live, not run yet.

Correction (not a gate), withdrawn: an earlier note here said P4 would cost about US$1.4, read from the j5/j6
`spent_usd` fields. Those fields are cumulative over each run, not per session (sa1-sa3 cost US$0.0035 a session).
ROUND.md's "about US$0.05" was right; P4 spent US$0.032. The seven prompts were checked: X10, W20, W30 ask one result
per tissue/visit; X14, W13, W35 one per patient.
