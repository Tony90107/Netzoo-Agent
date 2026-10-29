# per-group-counts -- live R5 (2026-10-29, user "跑 live"): gates PASS, but the new reading did not do its job

Run pc1: code b8e8503f, app settings, gpt-4o-mini, turn 1, 1 rep, 8 started. Spent US$0.038.

| item | role | gold | sample_count_in read | count used | call |
|---|---|---|---|---|---|
| G1 | total only, enough ("48 ... samples in total") | DO OTTER | **each_group (wrong)** | samples 48 | DO OTTER |
| G2 | total below minimum ("only 2 ... samples in total") | DECLINE | **each_group (wrong)** | samples 2 | DECLINE "DRAGON needs at least 3 samples; the request has 2" |
| G3 | each group stated (2 per tissue) | DECLINE | each_group | samples 2 | DECLINE, same reason |
| G4 | per-sample control, groups named | DO LIONESS-PANDA | all_samples (per_sample row: no effect) | samples 60 | DO LIONESS-PANDA |
| X10 | kept | DO PANDA | all_samples ("30 pigs": each tissue from all 30) | samples_total 30, not judged | DO PANDA |
| W20 | kept | DO DRAGON | each_group | samples 15 | DO DRAGON |
| X30 | kept | DO OTTER | each_group | samples 12 | DO OTTER |
| W30 | kept | DO OTTER | each_group | samples 20 | DO OTTER |

- **Declared gates pass:** every call is the gold kind and workflow; no control or kept item changed; no reason
  quotes a total as a group's size (G2's reason says "the request has 2", which is true).
- **But the targets were not reached by the change:** both totals (G1, G2) were read `each_group`, so the
  `samples_total` path never ran on them; their calls are right only because 48 passes and 2 fails either way. The
  only live `samples_total` row is X10, where all_samples is a defensible read (30 pigs, every tissue from all of them)
  and the count was then left unjudged.
- Reading accuracy of the new field on its purpose: totals recognised 0 of 2. The change is no worse than before
  (an each_group read behaves exactly as the old code), but it has not been shown to fix the case it was built for.

## Decision (user "照建議合併", 2026-10-29): WITHDRAWN

Not merged. The gates passed, but the new reading never recognised a total (0 of 2), so the change has no shown
effect and adds a schema field. The code stays only on branch `per-group-counts` (b8e8503f); main keeps the docs.
The total-only case stays open.
