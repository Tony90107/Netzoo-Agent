# Confirmation round p4c (2026-10-16) — declared before running

- Purpose (user's request): rerun the same 56 items with the same code as p4b, to see whether p4b's scores are stable.
  No code change between p4b and p4c.
- Code: the same `freeze-p4b.json` (base `71433f1`), the same run worktree. Scoring unchanged (`score_core.py`),
  ASK facts checked against gold by me.
- No new gate. Report: each class and the core score for p4b and p4c side by side; per item, whether the call
  agrees between the two rounds; whether the spec's final thresholds (section 8) hold in both.
- Budget announced: 56 sessions; nemotron about 60–170 calls, gpt-4o-mini about US$0.11.
