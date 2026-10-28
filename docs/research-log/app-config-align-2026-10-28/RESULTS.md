# App config align -- results (2026-10-28, no model calls)

Change: `docker-compose.yml` passes `OPENROUTER_CAPABILITY_MODEL` (empty default) and defaults
`NETZOO_MAX_TASK_TOKENS` to 30000. Gates declared in ROUND.md (2a08727e) before the edit.

| gate | result |
|---|---|
| G1 compose resolves with the app `.env` | pass: `netzoo` and `netzoo-daemon` (via `extends`) both get `openai/gpt-4o-mini-2024-07-18` and 30000 |
| G2 unset -> empty -> treated as unset | pass: both services get `''`; every reader (`_check_model`, `check_output_reserve`, `_goal_model`, budget preflight) tests `own` for truthiness |
| G3 replay of 778 turns on aligned settings | pass: turns losing a call 108 -> 4 (<= runners' 78), check cuts 10 -> 0 (`replay-aligned.json`) |
| G4 clean-env tests | pass: 5105 passed, 2 failed = the two known (`explicit_panda` characterization, `history_says_which_sessions_can_be_resumed`) |

The 4 turns still hit: `selection_conditions` 3 and `hypothesis_bases` 2, the same kind the runners' own replay has.

Cost (replay, gpt-4o-mini prices): mean US$0.0057 -> 0.0058 per turn, about +700 tokens; a lower bound.

The aligned settings equal the ones the ck1 live round ran with (own check model, 30,000 turn + 30,000 allowance,
4,000 reserve), so the measurements since check-reserve-2026-10-28 now describe the app's check settings. The one
remaining difference from the runners is the Jev flags: the app `.env` has FORMS off, the runners ran all three on.
