# Phase 0 baseline (spec 2026-10-15, section 9) — declared before round p0

- Code: `e317ba7` (branch `core-decision-phase0`; shadow `decide_core`, no behaviour change), run from the clean
  detached worktree `.worktrees/netzoo-core-p0-run` (`freeze-p0.json`, no modified files). Tests: 3790 passed.
- Bench: `items.json` minus DEV {C01, C02, C03, C05} = 56 items (do 14, dont 13, ask 15, vague 14), one run each,
  tag `p0`, 5 workers, 900 s per turn. Models as in `.env` (routing gpt-4o-mini, check nemotron :free).
- Scoring (`score_core.py`, frozen now): the core call in the trace (`core.decision`) against gold; ASK facts
  checked by me against the gold deciding fact (`facts-checked.json`); replies spot-checked for faithfulness —
  every session not scored correct or not DO, plus 10 seeded DO sessions (`faithful-checked.json`). No labellers.
- Offline check before the round: the shadow call matched m3's labelled takeaway in 115/150 sessions.
- Budget announced to the user: about 56–170 nemotron calls, about US$0.10 gpt-4o-mini.
- This is a baseline: no gate. It is the reference phases 1–3 are gated against.
