# Phase 3 gate (spec 2026-10-15, section 9) — declared before round p3

- Code: `89d471df3a9fe8298083f9d7f7ea29b409dd2054` (phase 3: core_view dispatch for CLARIFY/ASK/DECLINE/UNCHECKED, text boundaries as DECLINE
  evidence, unconfirmed guidance turns UNCHECKED, run gates read core.run_allowed, mismatch recorded), run from
  `.worktrees/netzoo-core-p0-run` (`freeze-p3.json`). Tests: 3825 passed.
- Offline: p2 replayed with this code (`replay_p3.py` -> `live/p2-replay3`): 0 view mismatches (recorded p1 8,
  p2 4); the one kind change (C19) is a replay artefact (the recorded decision was already held by with_core).
- Implementation note (spec change log, awaiting the user's confirmation): the classify-stage rewrite points
  (INVENTORY-P3.md) are held at the two exits, not each rewritten to write evidence only.
- Bench: the same 56 items, one run each, tag `p3`; scoring unchanged. Reference p2: do 10/14, dont 7/13, ask 7/15,
  vague 9/14, core 72.5.
- Gate (all must hold):
  - G1 convergence: 0 of 56 replies whose renderer is not one of their call's (`core.view` mismatch).
  - G2 faithfulness: every non-DO reply and 10 seeded DO replies checked by me: 0 contradictions.
  - G3 no class more than 1 below p2: do ≥ 9, dont ≥ 6, ask ≥ 6, vague ≥ 8.
- Reported, not gated here: the spec's final thresholds (section 8). The user deferred the three open items that
  hold most of the gap (ASK outcome verification, nemotron decode failures, the dont false accepts).
- Budget announced: 56 sessions; nemotron about 60–170 calls (quota reset 08:00), gpt-4o-mini about US$0.12.

## Round p3 result and the G2 rerun (declared before p3b)

- p3: G1 0 mismatches (pass); G3 do 11, dont 6, ask 10, vague 9 (pass); core 75.3.
- **G2 failed** on C42 and C43 (UNCHECKED held runs): each was headed "Workflow -- X" over an unmarked
  "available from X" line from the backup reading.
- Fixed within the phase-3 design (`9cd49e94c5d09d0773a23d8f59223aaa215b3372`): UNCHECKED names no workflow in the progress line, and a backup
  reading's available result reads "(not confirmed)". Offline replay of p3 (`live/p3-replay`): 0 mismatches, and the
  C42/C43 lines are marked; the one kind change (C56) is the replay artefact seen before.
- Rerun p3b: the 5 items whose p3 call was UNCHECKED (C10 C37 C42 C43 C47), one run each, `freeze-p3b.json`,
  about US$0.01, announced. G2 is judged on every non-DO reply of p3b; p3's counts stand for G1 and G3.
