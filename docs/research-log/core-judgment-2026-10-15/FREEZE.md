# Core-judgment round freeze (2026-10-15)

The user asked (2026-10-15, after M3 and its fix branch): how well does the agent now judge the core of a request —
do it, decline it, ask the deciding fact, or clarify a request too vague to choose anything. The earlier rounds
(Log 408 94.7 B, Log 411 90.9 C, a24b 83.8 D, m3 77.1 D) scored requirement labels with asks as a side metric;
this round scores the four-way decision directly. Frozen before any live output exists.

## Code

- Under test: `fb9f50a` (branch `evidence-contract-grounding`: M3 + the m3 fix branch 919817c, 6327c8f, fb9f50a),
  clean detached worktree `.worktrees/netzoo-core-score`, no modified files (`freeze-code.json`). Other sessions'
  uncommitted edits in the main tree (`desktop/`, `graph/execution.py`) are not under test.
- Models: routing/semantic gpt-4o-mini; capability check nemotron-3-super-120b:free (as in `.env`).
- Smoke test before the round: one non-set question (`cj-smoke-1`), exit 0, 37 s.

## Items

- `items.json`: 60 English single-turn items, 15 per class (`do`, `dont`, `ask`, `vague`), forms `named` / `goal` /
  `run`, written by one blind author subagent that read only `workflows/*.yaml` and `scripts/workflow_registry.py`
  (no code, tests, research logs or earlier test sets). Gold review: GOLD-REVIEW.md (filled before the round).
- English only (Chinese stays out of gates, user decision 2026-10-14). One run per item (lean testing, 2026-10-13).

## Labelling and scoring (LABELING.md, analyze.py)

- One blind labeller per packet of 20 sessions (3 packets) plus my primary review (memory rule 2026-10-11).
- Blind decision per session: DOES / OPTIONS / ASKS / DECLINES / PARTLY / UNCONFIRMED / OTHER, plus the workflows
  presented as fitting and the question asked.
- Primary review adds `core_question` (ask: the question targets the deciding fact; vague: it clarifies the missing
  core) and `states_condition` (ask items answered without a question but naming the deciding condition).
- Per-class cost (0 = right call): do — DOES/OPTIONS within gold 0, needless ask/choice 1, wrong workflow or
  refusal 2; dont — DECLINES 0, undecided 1, PARTLY 2, DOES/OPTIONS 3; ask/vague — right question 0, wrong
  question / undecided / commit-or-refuse stating the condition (ask only) 1, commit or refuse without asking 2.
- **Core score** = mean over the 4 classes of `100 × (1 − cost / (max cost × n))`. Also: strict accuracy, 4×7
  decision matrix, accuracy by class × form, and the legacy do/dont weighted score with FAR/FRR grade for continuity.
- Review set: every non-correct outcome, every ask/vague question, every contradiction, every DOES/OPTIONS without a
  named workflow, every session with a provider exception, plus a seeded 10% of the rest.

## Budget (announced to the user)

60 sessions × 1 turn, 5 workers, 900 s per turn. About 60–180 nemotron calls (free quota) and about US$0.10–0.20
of gpt-4o-mini (paid balance US$3.76 before the round).

## Frozen inputs

- `items.json` sha256 `16ca2466…301180` (author original `items-author.json` `1c9dc530…b714`; differences in
  GOLD-REVIEW.md). `freeze-code.json` base `fb9f50a5cc1c`, no modified files. Harness tests: 4/4 pass.
- Started 2026-10-15 16:03 Asia/Taipei, tag `cj1`.

## Stopped (16:10)

The user stopped the round after 4 complete sessions ("think about the direction first, otherwise it burns
tokens"). No relaunch. Complete: C01 (vague: menu plus "available from PANDA"), C02 (dont: declined, correct),
C03 (dont: three omics layers, answered "DRAGON fits" — false accept), C05 (do: run planned, correct). Partial job
folders are kept as evidence. The other 56 items are unused by any code change and can serve as a code-scored bench.
