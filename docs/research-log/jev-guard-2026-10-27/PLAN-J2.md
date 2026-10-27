# Fresh sealed set j2 for steps 1″, 3 and 4 together (plan, 2026-10-27, awaiting approval)

User request (2026-10-27): one fresh blind set covering steps 1″ (typed data checks), 3 (answers) and 4 (result
confirm), with data-type traps, unsure facts, named results and controls. Plan and budget first; nothing runs before
approval.

## 0. Build before the run (offline only)

Step 1″ is not on the live path yet. Wire it into the guard, in the same hook and under the same flag:
- On a DO: `check_typed_data`, with the post-hoc accepted-input rule added (a single data kind outside every call
  workflow's `input_artifacts` rules it out) and `same_samples`.
- A flag plus a sentence → ASK `jev_condition`, a confirm quoting the user's sentence and the typed contract field. The
  pending question keeps the field as `labels.contract`, so step 3 judges the reply: a confident `fails` → DECLINE
  with both quotes.

Unit tests are added; with the flag off, the replay must show 0 of 1388 changed. The code is frozen at one commit
before j2 is authored. No change after sealing.

## 1. The set j2 (48 items, ids Q01-Q48)

Written blind by a subagent that reads only `workflows/*.yaml` and `workflow_registry.py`, as for j1. A second blind
subagent reviews every gold; everything is sealed with SHA256 before any run, and I read only counts.

| group | n | gold (turn 1) | what it tests | replies |
|---|---|---|---|---|
| T  data-type trap | 10 | DECLINE | the request asks for a result a workflow makes, but the stated data is the wrong kind for every workflow that makes it (incompatible, not an accepted input, refused handoff, DRAGON layers from different samples); no workflow named in 5 | `reply_confirm` (re-states the fact) → final DECLINE |
| TC data-type control | 10 | DO | same shapes, but the data is right, including tricky alternatives the contracts allow (OTTER or PANDA with a co-expression matrix, DRAGON on stated same samples); 4 with an irrelevant uncertain aside | `reply_restate` |
| U  one unsure fact | 10 | ASK | as j1 U (which file, data property, count, input exists) | `reply_fact` (5 → DO, 5 → DECLINE), `fact_keywords`, `reply_restate` |
| N  named in own words | 9 | DO 6, DECLINE 3 | the result is described in plain words with a purpose framing and no workflow name (the shape the system wrongly CLARIFYs) | `reply_restate` |
| V  no result named | 9 | CLARIFY | as j1 V; 4 use output-sounding words, 1 names a workflow only as heard-of | `reply_result` (7 → DO, 2 → DECLINE) |

DRAGON / LIONESS-DRAGON appears in at least 3 T and 3 TC items. Every gold must quote contract text.

## 2. Runs (gpt-4o-mini, same frozen code, two arms)

- Arm F: guard off (the frozen system). Arm G: guard on.
- Each conversation runs up to 2 turns, with the scripted reply rule of run_j1.py:
  - after an ASK: `reply_fact` if the question names the fact, else `reply_confirm` / `reply_restate`;
  - after a CLARIFY: `reply_result`;
  - after DO or DECLINE: the conversation ends.
- Scored: turn-1 kind, and the final call against the final gold.

## 3. Gates (declared now, not loosened)

Overall, arm G vs arm F on the 48 items:
- O1: final right G >= F + 3.
- O2: G has no more FA than F, no more FR, no more MA.
- O3: 0 Jev-made declines (`jev_answer`) whose final gold is DO (a wrong reason).

Per step (arm G):
- S1 (step 1″): `jev_condition` asks on >= 4 of the T items whose call was DO; on TC <= 1.
- S3 (step 3): every `jev_answer` decline is on a gold-DECLINE final; caught >= half of the guard's asked items whose
  reply fails.
- S4 (step 4): `jev_link` on V <= 1; on N items whose call was CLARIFY >= half (reported when fewer than 2 such).
- S0 (J-ask kept): guard false alarms on TC + N gold-DO items <= 2.

All gates pass → I propose the code review and merge decision to you. Any fail → that step is withdrawn as declared,
and the overall verdict says which. Post-hoc analysis is labelled.

## 4. Budget

- Authoring and review subagents: no API spend.
- Two arms × 48 conversations × about 1.6 turns ≈ 150 mini turns ≈ US$0.65, plus Jev under US$0.02.
- Cap US$1.00 for both arms, enforced by the runner. Arm F runs first.
- Also: about 20 minutes of build and offline checks, then about 40 minutes of runs.
