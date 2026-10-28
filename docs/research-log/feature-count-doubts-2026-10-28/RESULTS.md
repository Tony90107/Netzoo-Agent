# Feature-count doubts -- offline results (2026-10-28): F0-F2 PASS

| gate | result |
|---|---|
| F0 harness replay flags off vs `replay-frozen.json` | pass: 0 of 1388 calls changed, right 609 -> 609 |
| F0 clean-env tests | pass: 5123 passed, 2 failed = the two known ones |
| F1 unit tests (`tests/test_feature_count_doubts.py`) | pass 5/5: C45 shape (200 -> LIONESS-DRAGON, 2,000 -> none, the 50 patients kept), R35 shape (200 -> runs, 600 -> 40,455,000 values, not), Q42 shape (120 genes <= 150 samples -> not COBRA, 2,000 -> COBRA), candidates not in the quote ignored, a doubt without candidates makes no fixed-dimension ask; sample-count choice tests unchanged |
| F2 enum count | pass: one more enum value per sentence block; compact schema 146 / 230 / 314 / 440 at 1 / 3 / 5 / 8 sentences (limit 1,000), the full schema compacts at 5+ sentences as before |

My first Q42 test expectation had COBRA's rule backwards ("COBRA requires more genes than samples", `data/cobra.py`); the
code's outcome was right and the test now states the rule.

Live (L1-L3) not run yet: needs the user's go.
