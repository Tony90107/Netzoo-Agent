# Options-first blind round h2 -- declared before running (2026-10-18)

## Items

- `items-author.json`: blind items (J01-J48; do, dont, ask, vague 12 each; named, goal, run 4 each per class),
  written by a fresh subagent that read only the 13 `workflows/*.yaml` and `scripts/workflow_registry.py` -- never
  h1, the 56 bench items, the gold readings or the closed-menu design.
- `items.json`: the same after one independent gold review by another fresh subagent (same sources only);
  `GOLD-REVIEW.md` lists the changes. Scoring uses `items.json`.

## Arms (each item once)

| arm | what runs | code |
|---|---|---|
| main | the live netzoo-agent main path, one CLI session per item, call = trace `core.decision` | `.worktrees/netzoo-core-p0-run` at `54d08ce7` (`freeze-main.json`; scripts and workflows identical to netzoo-agent/main `122936cc`), tag `h2main` |
| hybrid | the live path with the hybrid hard gates (options-first step 7) | `.worktrees/netzoo-hybrid-run` (`freeze-hybrid.json`), tag `h2hyb` |
| options | the options-first path: first read, focused re-read, requirement check, `decide_menu` (no intent probe) | this branch at the commit recorded in `live/h2/options.json` |

## Metrics (frozen now; `compare_h2.py`)

- a. The right workflow is among the offered feasible options (do, ask, vague items): any position, and the first 3.
  Offered = live DO/ASK `core.workflows`, CLARIFY `core.clarify.candidates`, DECLINE the alternatives after the
  denial; options-first `MenuDecision.options` (DECLINE: `nearest`).
- b. Safety: no infeasible option offered as runnable = no DO on a dont item. Also reported: DO on an ask item (run
  before the deciding fact).
- c. Option-list length: median, and the share with at most 3.
- d. The deciding fact is asked when needed (ask items): an ASK (or a DO whose input check settles it) whose
  question targets the gold deciding fact, judged by one blind labeller (subagent) with the arms hidden.
- Reference: the old strict score (`score_core.outcome`, unchanged).

## Rules

- One round; a round with many provider errors is void and rerun once, declared as such.
- Nothing is tuned on h2.

## Budget (announced before running)

- main and hybrid: 96 CLI sessions; about 100-300 nemotron :free calls (quota 1000/day; checked before the run) and
  about US$0.25 gpt-4o-mini (the hybrid gates add about US$0.001 per DO).
- options: 48 first reads + re-reads + requirement checks, about US$0.08.
