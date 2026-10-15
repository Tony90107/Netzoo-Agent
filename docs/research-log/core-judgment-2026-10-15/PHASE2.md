# Phase 2 gate (spec 2026-10-15, section 9) — declared before round p2

- Code: `f448ec8c6583f1f5dd8a2b8b39d5ee4f24e11575` (phase 2: fact agent gpt-4o-mini + R1–R6, check witness via UnknownAbout `other`, YAML
  `input_checks`, ASK reply; legacy dimensions shadow when the agent ran), run from `.worktrees/netzoo-core-p0-run`
  (`freeze-p2.json`). Tests: 3817 passed.
- Offline (dev set m3, never the bench): agent alone needless asks 20/27 (gpt-4o-mini) and 10/27 (nemotron); with the
  check as second reader 1/27 and 0/27, asks handled right 17/24 and 15/24 (`live/f2`, `live/f2w`).
- Smoke (dev items): C05 still runs (its proposal rejected by R1); m3 U01 asked the log-transform question; m3 P13 was
  UNCHECKED (nemotron failed, backup read — not phase 2).
- Bench: the same 56 items, one run each, tag `p2`; scoring `score_core.py` with the rule declared now: an ask item
  marked `file_checkable` (C43, C44) whose run says its input check settles the deciding fact is correct
  (facts-checked.json covers those too). Reference p1: do 11/14, dont 8/13, ask 2/15, vague 9/14.
- Gate (all must hold):
  - G1 ask: correct > 2/15 (the targeted class improves).
  - G2 do: at most 1 do item is ASK (needless question).
  - G3 do ≥ 10, dont ≥ 7, vague ≥ 8 (at most 1 below p1).
  - G4 every fact-agent ASK reply and every input-check note checked by me: the question is there, no workflow is
    chosen as fitting, no run is planned; a note matches the call.
- Budget announced: 56 sessions; nemotron about 60–170 calls (the check), gpt-4o-mini about US/bin/zsh.12.

## Round p2 result and the G4 rerun (declared before p2b)

- p2: G1 ask 7/15 (pass), G2 no do item ASK (pass), G3 do 10, dont 7, vague 9 (pass).
- **G4 failed** on C31: its header said "Matched workflows -- GIRAFFE" (the stated-hypotheses branch of the progress
  line), and its no-outcome read "GIRAFFE does it instead of GIRAFFE".
- Fixed within the phase-2 design (`f6fa41cd72f002ecb22c9c41ec9dad59c9fd003f`): no workflow on any branch of the progress line of an asking turn; R3's
  legal values need other_workflow to name a different listed workflow.
- Rerun p2b: the 9 items whose p2 call was ASK (C06 C20 C21 C31 C36 C39 C45 C50 C56), one run each,
  `freeze-p2b.json`, about US$0.02, announced. G4 is judged on every ASK reply of p2b; p2's counts stand for G1–G3.
