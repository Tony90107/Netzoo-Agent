# Phase 4b gate (spec section 12.4) — declared before round p4b

- Code: `71433f12ee60314ba5f074f7b3037c2fe4fc4de9` (4a COBRA relation + scope/limit; 4b ruled_out_inputs and only_inputs with verified words,
  route_available shared by the check's credits and the two-step routes; the 16k check cap; ASK replies without
  outcomes), run from `.worktrees/netzoo-core-p0-run` (`freeze-p4b.json`). Tests: 3845 passed.
- Smoke (dev prompts, not bench): S1 "I only have expr_liver.tsv; no motif prior and no PPI" -> DECLINE with the user's
  words (after two fixes: a network absent when stated inputs hold none; "only these inputs"); S2 "no PPI" -> PANDA
  still DO (STRING provides PPI); C05 still runs. Two earlier smokes failed on provider connection errors.
- Bench: the same 56 items, one run each, tag `p4b`; scoring unchanged. Reference p3: do 11/14 (1 false refusal),
  dont 6/13 (3 false accepts + 1 partly), ask 10/15, vague 9/14, core 75.3, 6/56 check decode failures.
- Gate (all must hold):
  - G1 dont: false accepts incl. partly fewer than p3's 4.
  - G2 do: false refusals not above p3's 1, and no do item loses a credit to ruled_out/only inputs.
  - G3 other classes at most 1 below p3: do ≥ 10, ask ≥ 9, vague ≥ 8.
  - G4 0 view mismatches.
  - G5 check decode failures ≤ 6/56; budget.blocked counted.
- A round with many provider (connection) errors is void and rerun once; announced: 56 sessions, nemotron about 60–170
  calls, gpt-4o-mini about US$0.12 (balance about US$3.20).
