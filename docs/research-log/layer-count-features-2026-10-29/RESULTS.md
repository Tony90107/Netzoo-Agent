# Layer-count features -- offline results (2026-10-29): L1-L3 PASS

Change: `needed_facts.feature_sized_layers` (an `omics_layers` choices doubt whose smallest candidate is >= 10);
`FactRecord._read_unknown_count` reads it as a `feature_count` candidate fact (judged by `count_update`) and
`verified_unknowns` drops it from the fixed omics-layers dimension.

| gate | result |
|---|---|
| L1 harness replay flags off vs `replay-frozen.json` | pass: 0 of 1388 calls changed (no right -> wrong), right 609 -> 609 |
| L2 unit tests (`tests/test_feature_count_doubts.py`) | pass 7/7: X22 shape waits on the feature count (150 -> LIONESS-DRAGON, 400 -> none); a (1, 2) layer doubt unchanged; candidates not in the quote ignored |
| L3 clean-env tests | pass: 5154 passed, 2 failed = the two known |

Recorded X22 readings rebuilt (`rebuild_x22.py`): j6a and ao1 both now wait on `feature_count` with
{150: LIONESS-DRAGON, 400: none} (recorded: DO / fact-agent question, the doubt typed `omics_layers`).
