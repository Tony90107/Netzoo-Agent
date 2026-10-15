# Phase 1 gate (spec 2026-10-15, section 9) — declared before round p1

- Code: `a43841c` (phase 1: the check reads the request's goal; `decide_core` CLARIFY when the confirmed reading is
  `purpose_only` or names a result no requirement reads; `with_core` holds the turn; `clarify_goal` reply), run from
  `.worktrees/netzoo-core-p0-run` (`freeze-p1.json`). Tests: 3800 passed.
- Smoke (dev items, not bench): C01 answered CLARIFY with the result list and one question; C05 still planned its
  LIONESS-COEXPRESSION run. Two rendering fixes followed (`e.g.` split, the 10-line cap).
- Bench: the same 56 items, one run each, tag `p1`; scoring unchanged (`score_core.py`), reference `p0-replay`
  (do 8/14, dont 8/13, ask 3/15, vague 1/14; core 45.6).
- Gate (all must hold):
  - G1 vague: correct > 1/14 (the targeted class improves).
  - G2 do: at most 1 do item is CLARIFY (needless clarification).
  - G3 do, dont and ask: correct counts at most 1 below p0-replay (≥ 7, ≥ 7, ≥ 2).
  - G4 every CLARIFY reply (any class) checked by me: none names a workflow as fitting or available, none plans a run.
- Budget announced to the user: smoke 2 sessions + bench 56 sessions; about 60–180 nemotron calls, about US$0.11.
- A failed gate is fixed only within the phase-1 design (spec section 0); anything else goes to the spec's change log
  with the user's OK first.
