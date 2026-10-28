# Asked doubts -- offline results (2026-10-29): D1-D3 PASS

Change: (1) carried from layer-count-features: feature-sized `omics_layers` doubts (smallest candidate >= 10) are
`feature_count` candidates judged in code; (2) `jev_guard_call.asked_doubts` (was `agent_doubts`): the user words of
every question the task asked or the user answered, any source, so `agreed_fact_core` never revives them.

| gate | result |
|---|---|
| D1 unit tests | pass 11/11 (`test_r1_jev_agreement.py`: agent / count / dimension questions pending or answered stop a revival, an unrelated count does not; `test_feature_count_doubts.py` incl. the X22 shape) |
| D2 recorded turns rebuilt (`rebuild.py`, `REBUILD.txt`) | pass: lc1 X22 t2 -> `already_asked` (the code-judged DECLINE stays); j6 X02 t2, t3 and X22 t2, t3 -> `already_asked`; ra2 W40, J46 t1 -> still `ask` |
| D3 clean-env tests / flags-off replay | pass: 5154 passed, 2 failed = the two known; 0 of 1388 changed |

## After the amendment (source `goal` left out)

D1 pass (the goal-quote case added: a CLARIFY goal quote holding the sentence does not block a revival), D2 pass
(same 7 results), D3 pass (5154 passed, 2 known failures; 0 of 1388 changed).
