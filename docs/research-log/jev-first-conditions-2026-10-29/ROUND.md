# Jev-first, phase B': the same arms with the condition check run (2026-10-29, user "開新一輪")

## Why

Phase B (`jev-first-fields-2026-10-29`) passed B1 (gold-DO right H 120 -> HB 147) and failed B2 (gold-DECLINE
check-level false accepts 42 -> 45 > 44); stopped as declared. The new false accepts (j2 Q13, j4 S32) had been
refused in H only through mini's `several_groups` misread -- a reason the user never gave. Their real reasons (SAMBAR
given an expression matrix; kmax above the tumour count) are judged in the app by the condition check (gpt-4o-mini,
Log 414), which the pure-code replay leaves out. This round asks what phase B could not: with the condition check
run as the router runs it, how many false accepts does each arm really have? Phase B's verdict stands; this is a new
measurement with its own gates.

## Design

- Population, Jev reads (both caches reused, no new Jev calls), arms and scoring as phases A/B: 433 first-turn
  readings of j1-j6; arms **M** (mini), **H** (Jev link >= 0.7), **HB** (H + five Jev fields >= 0.7), and
  **H+group_membership** (phase B's "harmful" field alone).
- Added after `build_capability_check`, as `router_invocation._with_capability_check` does at turn 1:
  `stated_requirements` (request and own-sentence), `condition_pairs`, `_condition_shown`; `code_answer` first; the
  rest to the app's condition-check model (`_own_llm` with OPENROUTER_CAPABILITY_MODEL = gpt-4o-mini-2024-07-18,
  temperature 0, the app's `_CONDITION_CHECK` prompt and `condition_check_model` schema); then
  `apply_condition_answers` / `apply_own_sentence_answers`. A failed call leaves the rows unchecked, as the router.
- Model answers are cached by the exact pair list sent, so arms that send the same pairs get the same answers.
- Not run (same for every arm): the redirect check, second opinion, re-read, fact agent, Jev guard.

## Gates (declared before any model call)

- **C1**: HB gold-DO right >= H's + 5, AND vs H wrong->right >= 2 x right->wrong (all with the condition check).
- **C2**: HB gold-DECLINE false accepts <= H's + 2 (with the condition check).
- **C3**: HB gold-DECLINE false accepts <= M's (no worse than today's reading).
- Cost cap US$1.00 (gpt-4o-mini, pre-approved).

All pass -> propose phase C (build behind a flag, fresh-set live test). Otherwise report and stop.
No gate is changed after the run.
