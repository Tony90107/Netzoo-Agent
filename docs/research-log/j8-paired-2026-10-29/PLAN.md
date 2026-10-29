# j8: has the system improved since 10-28? A paired comparison on a fresh set (2026-10-29, user "來跑 看看最新的harness有沒有改善")

## Question

Is today's main better than main at the start of this work, on requests neither has seen?
- **old** = `7ad2367f` (2026-10-28 13:41: the handoff's fixes merged -- J01, enum limit, check reserve, J34 allowance);
  run from worktree `.worktrees/netzoo-old`.
- **new** = `8f60b653` (2026-10-29: every change since, from this session and the jev-guard session); run from
  `.worktrees/netzoo-j5` (branch j8-eval, code = 8f60b653).
- Settings: the app's `.env` for both (gpt-4o-mini, own check model, Jev GUARD / OVERLAP / FORMS on, 30k turn budget,
  code check allowance), plus `NETZOO_AGENT_ANSWERS=on` for new (the app has it on now; old has no such code).
  So the comparison is "the app then" vs "the app now".

## Set

Fresh j8: 48 items, ids Z01-Z48, j5's seventeen groups and counts (`j8/AUTHOR-BRIEF.md` = j5's brief, new paths and
ids). Blind author subagent (reads only `workflows/*.yaml` and `workflow_registry.py`), blind gold reviewer, sealed by
SHA-256 before either arm runs. I read only counts until both arms are done.

## Run

Both arms: up to 3 turns, the j4-j7 reply rule, 1 rep, the same item order. Cap US$0.50 per arm.

## Analysis (declared before any run)

- Right / FA / FR / MA per arm as j4-j7 (`kind_of`; PARTIAL counted as DO; final gold = `final_after_fact` /
  `final_after_result` when that reply was sent). Strict right (a DO final also on gold workflows) reported.
- **Primary**: paired right finals; the items right in one arm only (discordant). Two-sided exact sign test on them.
  "Significant improvement" = new has more discordant wins AND p < 0.05. Anything else is reported as such, never
  rounded up.
- Secondary: false accepts (FA) paired the same way; every discordant item listed with both finals.
- One rep per arm: per-item reading variance (~20% item flips seen in p4b/p4c) is part of the noise; stated, not
  corrected.
