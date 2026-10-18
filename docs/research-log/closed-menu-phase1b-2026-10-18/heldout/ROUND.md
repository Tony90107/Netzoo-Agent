# Phase 1b step 6 held-out round `h1` -- declared before running (2026-10-18)

## Items

- `items-author.json`: 48 blind items (H01-H48; do, dont, ask, vague 12 each; named, goal, run 4 each per class), written
  by a subagent that read only the 13 `workflows/*.yaml` and `scripts/workflow_registry.py` -- never the 56 bench
  items, the gold readings or the closed-menu design.
- `items.json`: the same items after one independent gold review (another subagent, same sources only); changes and
  `file_checkable` flags are listed in `GOLD-REVIEW.md`. Scoring uses `items.json`.

## Arms (each item once)

| arm | what runs | code |
|---|---|---|
| live | the current netzoo-agent main path: one CLI session per item (`run_live.py`, 5 workers, 900 s), call = the trace's `core.decision` | `.worktrees/netzoo-core-p0-run` at `54d08ce7` (`freeze-live.json`; scripts and workflows identical to netzoo-agent/main `122936cc`) |
| first | closed-menu first read alone, `decide_menu` | this branch (commit recorded in `live/h1/menu.json`) |
| menu | first read + focused limit re-read + requirement check | same pass |
| probe | menu + the focused intent probe after the re-read (the user's variant, 2026-10-18) | same pass |

The three reader arms share one first read per item (`compare.py read-menu h1`).

## Scoring (frozen now)

- `score_core.outcome` (unchanged copy from core-judgment-2026-10-15) for every arm.
- An ASK is right only when a question targets the gold deciding fact: one blind labeller (subagent) judges
  `fact-sheet.json` -- the request, the gold fact and each answer's questions, arms hidden behind random codes.
- Reported side by side: correct per class and overall; wrong commitments (a DO or DECLINE that is not correct) per
  item; needless questions on do items; a secondary view where any ASK or CLARIFY on a vague item counts as right.
- For the probe arm also: how often it changed an intent, and in which direction (agree / unclear / adopted).
- One round, no rerun except a void round (many provider errors), declared as such.

## Budget (announced before running)

- live: 48 sessions; about 50-150 nemotron :free calls (quota 1000/day; 4 live sessions so far today) and about
  US$0.10 gpt-4o-mini. OpenRouter paid balance about US$4.68.
- reader arms: 48 first reads + up to 48 re-reads + intent probes + a few requirement checks, about US$0.10.
