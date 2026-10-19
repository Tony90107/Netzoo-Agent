# Slim reading blind round h3 -- declared before running (2026-10-19)

Spec: `docs/superpowers/specs/2026-10-19-slim-reading-fields-design.md`, sections 6.1 (S3) and 6.2.

## Items

- `items-author.json`: 48 blind items (L01-L48; do, dont, ask, vague 12 each; named, goal, run 4 each per class),
  written by a fresh subagent that read only the 13 `workflows/*.yaml` and `scripts/workflow_registry.py` of the run
  worktree -- never h1, h2, the 56 bench items, the dev items, the gold readings or the slim-reading design. Same
  writer brief as h2 except the ids.
- `items.json`: the same after one independent gold review by another fresh subagent (same sources only);
  `GOLD-REVIEW.md` lists the changes. Scoring uses `items.json`.
- Nothing is tuned on h3. No code changes between this file and the two runs.

## Arms (each item once)

| arm | what runs | code |
|---|---|---|
| main | the live netzoo-agent main path, one CLI session per item, call = trace `core.decision` | `.worktrees/netzoo-core-p0-run` at `54d08ce7` (`freeze-main.json`; = netzoo-agent/main `122936cc` code), tag `h3main` |
| slim | the slim reading: core read, step-2 B fields, focused read, requirement check, `decide_menu` (reading calls only) | this branch at the commit recorded in `live/h3/slim.json` |

## Metrics (frozen now; `compare_h3.py`)

Primary (the spec's three scientific goals), counted with `score_core.outcome` (unchanged from h1/h2):

| metric | outcomes counted |
|---|---|
| false accepts | dont item: `false_accept`, `partly_accept` (a DO, partial included) |
| false refusals | do item: `false_refusal` (a DECLINE or a partial DO) |
| missed asks | ask or vague item: `committed_without_asking`, `refused_without_asking` |

Also reported:

- strict score (`score_core.outcome == correct`, per class and total);
- the deciding fact asked (ask items): one blind labeller on `fact-sheet.json`, arms hidden and shuffled (as h2);
- values written per read (slim only: both payloads, every leaf);
- misfilled values (slim only): one blind labeller on the written values with their quotes, from the prompt alone
  (`supported`, `wrong_value`, `not_supported`; as S2).

## Adoption rule (frozen)

Slim is adopted for the next step (S4, the user's decision) only if **all three error counts are each <= main's**
and **slim's strict score >= main's**. Otherwise it is not adopted, and RESULTS reports, per item, why each arm went
wrong.

## Rules

- One round; a round with many provider errors (or a free-model outage in main) is void and rerun once, declared as
  such.
- Two reads of the same code differ (h2: main vs main+gates differed on 14 calls from run-to-run variance alone), so a
  difference of one or two items is not read as a difference.

## Budget (announced before running)

- main: 48 CLI sessions; about 50-150 nemotron :free calls (quota 1000/day, checked before the run) and about
  US$0.12 gpt-4o-mini.
- slim: 48 core reads + focused reads + requirement checks, about US$0.02.
- Labellers are subagents (no API cost).
