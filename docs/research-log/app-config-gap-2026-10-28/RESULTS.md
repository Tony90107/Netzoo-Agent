# App check settings vs the test runners' — measured on recordings (2026-10-28, no model calls)

User decision (2026-10-28): measure the gap before changing any config. The jev-guard session noted that compose does
not pass `OPENROUTER_CAPABILITY_MODEL`; reading the code, that means the app's check runs on the router/semantic LLM:

| | app (docker compose) | test runners (all our live rounds since 10-20) |
|---|---|---|
| check model | `openai/gpt-4o-mini` = the router LLM (`factory.py`: semantic == router) | own model `openai/gpt-4o-mini-2024-07-18` |
| check output cap / reserve | 1,200 (`NETZOO_ROUTER_MAX_TOKENS`) | 16,000 (4,000 after check-reserve) |
| turn budget | 20,000 (+30,000 allowance for the check family) | 30,000 (+30,000) |

So the enum-limit and 16k-reserve bugs do not hit the app (its check is the backup path, which already compacted and
reserved 1,200). The app has other losses instead.

## Method (`simulate.py`, `simulate.json`)

778 recorded turns whose check ran on the own model (excluding today's ck1 runs, which ran the 4,000 reserve). Each
turn's recorded calls are replayed in order, refused calls put back where they were refused, under one set of budget
rules (`evaluate_budget_call`: refused when consumed + input + reserved output > budget - 1,500; the check family gets
the 30,000 allowance). Calibration with the runners' settings: 61 of 70 recorded refusals reproduced; 20 of 6,035
calls that ran are refused in the replay (0.3%; preflight estimates input from characters, the replay uses recorded
tokens). A refusal in the app would change what follows; the replay keeps the recorded sequence, so it counts first
losses only.

## Result: 108 of 778 turns (14%) would lose a call or a check in the app

| what the app loses | turns | what that call does |
|---|---|---|
| `selection_conditions` refused | 50 | the method-tie recommendation / separating question (condition_recommender returns the tie as it is) |
| `semantic_reviewer` refused | 46 | the repair pass after a first semantic reading fails validation, so the failed reading stands |
| capability check output over 1,200 (cut off) | 10 | the check itself (decode failure, then provisional) |
| `hypothesis_bases` | 6 | |
| `fact_check` | 5 | the contract-grounded fact questions |
| `semantic_discriminator`, `intent_router` | 3 each | routing calls |
| others (sibling repair 2, re-read 2, data_facts 1, study_purpose 1) | | |

And the app runs calls the runners refused (its check reserve is 1,200): 54 re-reads and 11 second opinions, which is
what check-reserve-2026-10-28 now also gives the runners.

The app's own traces (`netzoo_agent/.netzoo/traces`, 3,789 runs 08-04 to 10-25) have only 16 checks on the app's
setting (gpt-4o-mini, no own model); 4 of them (10-14) had `study_purpose` and `data_facts` refused. Too few to
measure, but consistent with the smaller turn budget.

## What it means

Every measurement since 10-20 (j2-j4, the Jev rounds, today's live check) was made on the runners' settings, which the
app does not use. The app's turn budget (20,000) refuses the routing-side calls that run after a long check, and its
1,200 cap cuts the largest checks. Aligning the app with the tested settings (passing `OPENROUTER_CAPABILITY_MODEL`
and `NETZOO_MAX_TASK_TOKENS=30000` through compose), or measuring on the app's settings, is a config decision for the
user.
