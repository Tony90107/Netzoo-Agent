# Mixed notation -- offline results (2026-10-28): M0-M2 PASS

| gate | result |
|---|---|
| M0 harness replay flags off vs `replay-frozen.json` | pass: 0 of 1388 calls changed (no recorded reading in the corpus holds a mixed run), right 609 -> 609 |
| M0 clean-env tests | pass: 5136 passed, 2 failed = the two known ones |
| M1 unit tests (`tests/test_mixed_notation.py`) | pass 13/13: the 4 mixed runs give no candidates; the 9 one-notation runs give the same values as the code before the change (checked on a checkout of 026b0f06) |
| M2 R35 rebuilt from its fc1 reading (`rebuild_r35.py`) | pass: the LIONESS-DRAGON row's method now holds the 300 proteins, the "1 or 300" doubt is gone, and the row **waits on the feature count: 200 -> LIONESS-DRAGON, 600 -> none** |

R35's second reading issue remains (the doubt sentence is also a result row of its own, not available); with the
main row waiting it no longer runs. The j3 recordings of R35 (before `feature_count`) only gain the 300 proteins.

Live not run: needs the user's go.
