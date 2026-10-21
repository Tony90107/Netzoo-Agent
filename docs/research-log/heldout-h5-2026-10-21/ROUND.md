# Held-out round h5 -- declared before authoring and running (2026-10-21)

Plan: `collab/ROUND-24-PLAN.md`; approved by the user on 2026-10-21 (48 items x 2 reps, ~96 sessions, estimated
US$0.43, hard cap US$1.00, actual-cost guard).

## Code

The frozen run worktree `.worktrees/netzoo-h5-run`, detached at `ab2a0f61` (`e2fb5a63` plus research-log docs only).
No code changes from now until scoring ends. The runner verifies the worktree's HEAD and that it has no tracked or
untracked change before and after every session (`freeze.json`).

## Items

- `items-author.json`: 48 English items Q01-Q48, written by a fresh subagent that reads only the 13
  `workflows/*.yaml` and `scripts/workflow_registry.py` of the run worktree -- never h1-h4, the 56 core items, any
  dev items, `docs/research-log`, `collab`, `tests`, the capability sheet or any decision code. Classes do, dont, ask,
  vague, 12 each; forms named, goal, run, 4 each per class. Its brief describes the classes and forms only.
- `items.json`: the same after one independent gold review by another fresh subagent with the same sources;
  `GOLD-REVIEW.md` lists every change. Scoring uses `items.json`. My check is format and language only.

## Runs

- Smoke `h5smoke`: one item per class, one session each; not scored.
- Main `h5main`: every item twice (reps 1 and 2), two sessions in parallel, gpt-4o-mini for every role.
- A round with many provider errors is void and rerun once, declared as such.
- Cost guard: provider-reported cost summed after every session; no session starts once the round total reaches
  US$1.00.

## Metrics (frozen now; `score.py`)

1. Strict outcome per session by `score.outcome`, which is h4's `score_core.outcome` without the credit for a run
   whose input check settles the deciding fact (user decision 2026-10-21: such a fact is asked first). Per class and
   total: rep 1, rep 2, their mean, and pass^2 (both reps correct).
2. Error categories: false accept / partly accept (dont), false refusal (do), committed or refused without asking
   (ask, vague), needless question (do), unchecked, wrong question kind, wrong fact.
3. Wrong information: every DECLINE or partial-DO reply's stated reasons, judged by ROUND-19's frozen `judge.py`
   (reason-accuracy-2026-10-21); every judge-"wrong" reviewed by me; reported as wrong / misleading / right /
   true-not-main / no reason.
4. Ask items: whether the question asked the deciding fact -- one blind labeller (a subagent) on a sheet of the
   questions with item ids and reps shuffled.
5. Paired with the code before ROUND-17 (`425df6fa`): rep 1's recorded readings replayed offline by B2
   (`replay_full`, `--scripts`), fixes and breaks per item. An approximation: unrecorded calls are handled as live
   handles an unanswered one.

Reading of the result (declared): mean strict >= 85% -- the gains broadly generalize; 79-85% -- partly; < 79% -- mostly
item-specific. Reference: h1-h4 scored 79-89% live when fresh and 87-100% when replayed with today's code.

## Budget

Smoke 4 sessions about US$0.02; main 96 sessions about US$0.40; reason judge about US$0.005; hard cap US$1.00.
Authoring, review and labelling by subagents (no API cost).

## Notes during authoring

- The item author reports that, when it read the registry, a tool hook added the run worktree's `AGENTS.md` (the
  repository's instructions to coding agents) to its context automatically; it did not open the file and used none of
  it for any gold. `AGENTS.md` holds no test items.
