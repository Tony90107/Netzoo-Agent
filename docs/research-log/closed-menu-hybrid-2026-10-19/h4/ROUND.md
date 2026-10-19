# Hybrid blind round h4 -- declared before running (2026-10-19)

Spec: `docs/superpowers/specs/2026-10-19-hybrid-contract-veto-design.md`, section 5 (H2).

## Items

- `items-author.json`: 48 blind English items (M01-M48; do, dont, ask, vague 12 each; named, goal, run 4 each per
  class), written by a fresh subagent that read only the 13 `workflows/*.yaml` and `scripts/workflow_registry.py` of
  the run worktree -- never h1-h3, the 56 bench items, the dev items or the hybrid / slim-reading design. English only
  (no CJK). Each item lists its interpretation-critical facts (`interpretation_facts`).
- `items.json`: the same after one independent gold review by another fresh subagent (same sources only), which also
  checked the interpretation-critical facts; `GOLD-REVIEW.md` lists the changes. Scoring uses `items.json`.
- Nothing is tuned on h4. No code changes between this file and the runs.

## Arms

| arm | what runs | code |
|---|---|---|
| main | the live netzoo-agent main path, one CLI session per item, once; call = trace `core.decision` | `.worktrees/netzoo-core-p0-run` at `54d08ce7` (`freeze-main.json`; = netzoo-agent/main `122936cc` code), tag `h4main` |
| hybrid | the same h4main sessions; where the call is DO, the contract veto layer applied offline: its reads (gpt-4o-mini) on the live call's own workflows, then `contract_veto` and `vetoed_core` | this branch at the commit recorded in `live/h4/veto.json` |

The hybrid arm reuses main's calls, so the two arms differ only by the veto layer (h2: two identical-code live arms
differed on 14-17 calls).

## Metrics (frozen now; `compare_h4.py`, `score_core.outcome` unchanged)

| metric | outcomes counted | adoption |
|---|---|---|
| false accepts | dont: `false_accept`, `partly_accept` | hybrid **<** main |
| false refusals | do: `false_refusal` | hybrid <= main |
| missed asks | ask, vague: `committed_without_asking`, `refused_without_asking` | hybrid <= main |
| strict score | `correct`, per class and total | hybrid >= main |

Adoption: all four. Otherwise not adopted, and RESULTS reports per item why.

Also reported:

- the deciding fact asked (ask items): one blind labeller on `fact-sheet.json`, arms hidden and shuffled;
- each veto's reason and quotes: one blind labeller on `veto-sheet.json` (right / wrong reading / wrong contract),
  item classes hidden;
- runnable but with a scientific meaning different from what the user asked: each arm's DO on an item with
  interpretation-critical facts, what will run and what the user is told before running, one blind labeller on
  `meaning-sheet.json` (same, or flagged for confirmation / different and not flagged), arms hidden;
- the core-data question (user decision 2026-10-19): how often it fires, by class; on a do item it is a needless
  question (the strict score already counts it so) unless the gold says the data was not established;
- disclosures shown and run confirmations listed; unverified violations (reported, never a veto).

## Smoke run (not scored)

About 5 sessions of h4 items through the live CLI with the veto wired in (`NETZOO_CONTRACT_VETO=1`, a clean run
worktree at this branch's head): the trace has `core.contract_veto` and the reply follows the veto's call.

## Rules

- One round; a round with many provider errors (or a free-model outage in main) is void and rerun once, declared as
  such. A veto read that fails leaves the live call (as on the live path) and is counted.
- Single run: differences of one or two items are within live and reading variance.

## Budget (announced before running)

- main: 48 CLI sessions; about 50-150 nemotron :free calls (quota 1000/day, checked before the run) and about US$0.10
  gpt-4o-mini.
- hybrid: the veto reads for the DO sessions, about US$0.02.
- smoke: about 5 sessions, about US$0.02.
- Labellers are subagents (no API cost).
