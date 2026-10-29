# per-group-base -- offline results (2026-10-29)

| Gate | Result |
|---|---|
| Q1 unit tests (`tests/test_per_group_base.py`, 6) | pass: per_group on each LIONESS network entry -> its base entry; whole_cohort, per_sample, unstated unchanged; association tests (no `aggregate_entry`) kept; a bad `aggregate_entry` is rejected at load. `test_capability_check.py` (Log 397 design test) passes. |
| Q2 rebuild of recorded pg1 t1 readings | X10: `available ['panda.tf_gene_network']`; W20: `available ['dragon.two_layer_network']`; no full gap (before: lioness_panda / lioness_dragon). |
| Q3 flags-off replay | 1388 readings, right 609, output byte-identical to main's replay: 0 changed calls. |
| Q3 clean-env tests | 5171 passed; the 2 known unrelated failures only; module size test passes (capability_check.py 1,000 lines). |

Disclosed: one assertion of the previous round's own test (`test_per_group_scale.py`) said per_group keeps
LIONESS-PANDA -- the exact behaviour this round changes on purpose (ROUND.md Q1). It now says per_group credits
panda.tf_gene_network; the whole_cohort assertion beside it is unchanged.

Offline all gates pass. Q4 live not run yet.

Open item (jev-guard, not this round's scope): a per_group run uses one group's samples, but nothing ties the
checked sample_count to the group. On the four live per_group rows (pg1/pg2) the counted number was already the
per-group one (X30 12, X10 30, W20 15, W30 20), so none was a false accept. A request stating only a total ("48
samples across 4 stages") would be checked against 48. Proposed later as its own round: a typed group size for the
count checks, or a reply line saying the limits apply per group.
