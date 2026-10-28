# The check's own model takes the compact schema over the 1,000-enum limit — offline results (2026-10-28): ALL GATES PASS

Code: `graph/capability_check_call._enum_limited`, used by the check and the re-read. Tests:
`tests/test_check_enum_limit.py` (3; the two over-limit tests fail under the old rule with 1,066 and 1,240 values).

| gate | result |
|---|---|
| K0 off-path unchanged | 4 sentences (907 values) and a model not on OpenAI (nemotron) keep the full schema (unit test). Harness replay 0 of 1388 changed vs `replay-frozen.json` (609 -> 609). Tests: 5103 passed, 51 skipped, 2 failed, both known (the env-dependent supervisor test; `test_planning_model_dump_is_characterized[explicit_panda]`, failing on main df806e15 too) **PASS** |
| K1 scope | Over every recorded turn text (sentences: 1: 408, 2: 1,232, 3: 489, 4: 153, 5+: 17), only the 17 of 5+ sentences are over the limit. The 6 read by gpt-4o-mini all failed with the enum 400; the 11 others ran on nemotron (not routed to OpenAI, so not compacted). No call that worked changes **PASS** |
| K2 the failure is gone | the own model `openai/gpt-4o-mini-2024-07-18` sees 313 values for a 5-sentence check and <= 1,000 for an 8-passage re-read (unit tests) **PASS** |

Live effect not measured: the 6 failed third turns (j1a J20, J48; j3g R21; j4g S05, S35; jo1 Q02) need re-running.
