# per-group-counts -- offline results (2026-10-29)

| Gate | Result |
|---|---|
| R1 unit tests (`tests/test_per_group_counts.py`) | pass: per_group + all_samples / not_stated total 48 -> available on OTTER, no limit, `samples_total` 48; total 1 -> refused "OTTER needs at least 2 samples in each group; the request has 1 in all"; each_group 1 -> refused as before; whole_cohort judged on the stated count whatever the field says; COBRA's relation not judged on a per-group total (and still judged for a whole-cohort row). |
| R2 schema | `sample_count_in` on the ask only (one definition), not on the request conditions; enum-limit test passes. |
| R3 rebuild of pb1 X10, W20, X30, W30 | all `available` on the same entry (panda / dragon / otter / otter), no limits; the counts are now `samples_total` (field absent -> not_stated), i.e. no longer judged -- the disclosed behaviour change. The unread-count question (`unread_sample_conditions`) does not fire on any of them. |
| R4 flags-off replay | 1388 readings, right 609, byte-identical to main's replay: 0 changed calls. |
| R4 clean-env tests | 5176 passed; the 2 known unrelated failures only; module size passes (capability_check.py 1,000 lines). |

Offline all gates pass. R5 live not run yet.
