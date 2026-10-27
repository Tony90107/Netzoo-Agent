# Step 3 — answers to a Jev question (declared 2026-10-27, before any call)

User request (2026-10-27): the remaining problems in the order I proposed; first, the follow-up answer (J04 "the PPI
file was never made", J20 "it's the COBRA matrix" still got DO). Cause: a `jev_fact` question has no options, so the
code-only binder (P3) never binds the answer and nothing in the schema changes.

## Design

1. When the guard asks, a second Jev call picks the **contract line** the unsure sentence depends on: a closed menu of
   the call's workflows' handoff-contract sentences and input-check texts, verbatim from the YAML (`contract_lines`).
   The line is shown in the question (the existing ASK reply renders `contract_quote`) and kept on the pending question.
2. On the answer turn, Jev judges the user's answer against that line: `meets` / `fails` / `unclear`.
3. Code: `fails` at confidence >= 0.7 while the system's call is DO → DECLINE, basis `jev_answer`. The reason is two
   verbatim quotes, the user's answer and the contract line (never-wrong-reason). `meets` / `unclear` → the system's
   call as it came.

This is the guard's first DECLINE. It is allowed only on the user's own answer to a question about a contract line,
never on a first-turn reading (Jev alone: FA 47 / FR 35).

## Offline feasibility (`answers_offline.py`, Jev only, < US$0.01)

U items of j1 (12) and h10 (8), all seen. Workflows = the gold `workflows` (live: the call's).
- A1: wrong declines = 0: no `fails` >= 0.7 on a `reply_fact` whose gold final is DO, nor on any `reply_restate`.
- A2: declines caught >= half of the gold-DECLINE finals.

Both pass → build into the guard, unit tests, flag-off replay 0 changes, then live on the U items with guard on, turns
1-2 (<= 20 sessions, about US$0.15, gpt-4o-mini). Either fails → stop and report; no wording retries.

## Offline result (ANSWERS-OFFLINE.txt, US$0.004)

Sentence found 20/20; contract line picked 14/20. A1 pass: 0 wrong declines (no `fails` on a DO-final `reply_fact`,
none on any of 14 `reply_restate`). A2 pass: 6 of 10 DECLINE finals caught (J04, J09, J20, W01, W04, W28).

Built: `pick_contract` at ask time, the line kept on the pending question (`labels.contract`), `judge_answer` on
the answer turn, `answered_core` → DECLINE `jev_answer` whose reply is the user's answer + the contract line, and
nothing about other workflows (PANDA takes a COBRA matrix through coexpression_file, so "no registered workflow"
would be wrong). 29 guard tests; flag off: replay 0 of 1388 changed.

## Live check (declared before running)

The 20 U items, guard on, turns 1-2 (`run_j1.py answers`, tag j1u, <= 20 sessions, about US$0.15). The jev_answer
path fires only where the guard asked on turn 1 and picked a line. Per session the event keeps the call without it
(`kind_before`).
- L1: no `jev_answer` DECLINE where the gold final is DO.
- Reported: declines caught, and finals right with the step against the same sessions' `kind_before`.

## Live result (RESULTS-ANSWERS.txt, 20 sessions, US$0.149, code 0259b312)

- L1 pass: 0 wrong `jev_answer` declines.
- Caught: J04 ("PPI file never made"), J20 ("COBRA matrix"), W01 — all three DO without the step, DECLINE with it.
- Finals right 12/20 with the step vs 9/20 without (same sessions' `kind_before`).
- Turn-1 Jev asks 7, with a contract line only 3 (offline 14/20 lines on gold workflows; live the call's workflows);
  the other 4 asked as before and their answers went to the system.

Left (not this step): J09 — the system's own fact-agent question, answered "fails", still DO: the answer read covers
only Jev's questions, though fact-agent questions carry a contract quote too (candidate next). J48 — system DECLINE
full_gap after a "meets" answer (follow-up reading). J46, W13, W14, W21, W28 — turn-1 misses where Jev was not
confident (or agreed), as on arm S.
