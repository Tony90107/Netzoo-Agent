# Phase 5 round p5 (spec section 13.5) — declared before running

- Code: `54d08ce7` (5a a confirmed unclear goal is CLARIFY when routing failed closed; 5b count_alternatives judged in
  code, only credited results make several; 5c FactProposal about/alternatives and R7, accepted by the user with C2
  at 16/24), run from `.worktrees/netzoo-core-p0-run` (`freeze-p5.json`). Tests: 3872 passed.
- Offline evidence before the round: 5a replay only C10's 4 turns change, 0 view mismatches (RESULTS-5A); 5b reading
  B1-B4 pass, U12 trace and the credited-results fix (RESULTS-5B); 5c fact agent C1 0, C2 16/24, C3 0, same-day
  control matches phase 2 (RESULTS-5C).
- Smoke before the bench (dev prompts, not bench; session ids `cj-p5smoke-*` in the run worktree): m3 U12 (5b count
  path), C01 (vague dev item, CLARIFY), C05 (do dev item, a run still planned). Smoke results do not gate; a crash or
  a view mismatch stops the round.
- Bench: the same 56 items, one run each, tag `p5`; scoring unchanged (`score_core.py`), ASK facts checked against
  gold by me. Reference (same code twice): p4b 89.6, 46/56 (do 11, dont 11, ask 12, vague 12); p4c 79.0, 39/56
  (do 10, dont 11, ask 8, vague 10).
- Gate (all must hold):
  - G1 each class correct at least the worse of p4b/p4c minus 1: do ≥ 9, dont ≥ 10, ask ≥ 7, vague ≥ 9.
  - G2 do and ask items judged CLARIFY with basis result_open: ≤ 1.
  - G3 an item whose request gives no candidate count has no count_fact call and no by_code wait (the only bench
    item giving candidate numbers is C45).
  - G4 0 view mismatches.
  - G5 check decode failures ≤ 3/56; budget.blocked counted.
- Reported per item: C10 (5a), C45 (5b), C24 (5c). The core score is reported for reference only: the same code has
  scored 79.0 and 89.6, so one round never claims the final thresholds of section 8.
- A round with many provider (connection) errors is void and rerun once. Budget announced: smoke 3 sessions and the
  bench 56 sessions; nemotron about 60–180 calls (free quota, 62 used today), gpt-4o-mini about US$0.12.
