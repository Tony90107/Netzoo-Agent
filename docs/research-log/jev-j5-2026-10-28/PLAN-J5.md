# Fresh sealed set j5: baseline of the app as configured (plan, 2026-10-28)

User decisions (2026-10-28): measure the whole system on a fresh sealed set, on the app's actual settings, before
any more per-item fixes ("開始出 j5"); FORMS on in the app `.env`. j1-j4 are all seen. Nothing runs before the user
sees the item counts and the cost.

## 0. Code and settings under test (no change)

- main **7ad2367f** (jev-conditions merged: J01, check enum limit, 4k check reserve, compose alignment, 45k check
  allowance). The runner refuses to start if `scripts`, `workflows`, `prompts` or `AGENTS.md` differ from 7ad2367f.
- One arm = the app's settings: app `.env` + compose defaults. `NETZOO_JEV_GUARD`, `NETZOO_JEV_OVERLAP`,
  `NETZOO_JEV_FORMS` on; `OPENROUTER_CAPABILITY_MODEL` = gpt-4o-mini-2024-07-18; `NETZOO_MAX_TASK_TOKENS` 30000;
  `OPENROUTER_CAPABILITY_EXTRA_TOKENS` NOT set (code default 45,000); no offline Jev cache variables.
- Worktree `.worktrees/netzoo-j5` (branch `j5-eval`); records under `docs/research-log/jev-j5-2026-10-28/`.

## 1. The set j5 (48 items, ids W01-W48, 17 groups; `j5/AUTHOR-BRIEF.md`)

Written blind by a subagent that reads only `workflows/*.yaml` and `workflow_registry.py`; a second blind subagent
reviews every gold (`j5/REVIEW-BRIEF.md`). Sealed with SHA256 before any run; I read only counts.

The j4 groups are kept at smaller counts (form traps/controls 15, data type 7, U 6, N 6, V 4), and groups are added
for the open reading-level failures of the handoff (none written from those items): MF several input files listed
(J46, Q18 "several"), SA one aggregate result per group incl. time points (S45 per-sample misread), SP per-sample
control, U count doubts 3 of 6 (R35, R14), N spread over 6 workflows with >= 2 of COBRA/OTTER/GIRAFFE/SAMBAR/BONOBO
(S43, R14 routing), V 4 (Q25), and P PARTIAL 2.

## 2. Run (gpt-4o-mini, one arm, up to 3 turns, 1 rep)

Reply rule unchanged from j4 (`run_j4.next_reply`): after an ASK -- `reply_fact` when the question names the fact,
`reply_form` for a form question, `reply_confirm`, else `reply_restate`; after a CLARIFY -- `reply_result`, else
`reply_restate`; anything else ends the conversation.

## 3. What is reported (a baseline; no change is tested, so no pass/fail gate)

- Right finals of 48 (PARTIAL counted as DO, as in j4), FA / FR / MA, by group; check health (enum 400s, check
  budget refusals, UNCHECKED finals); wrong form reasons said.
- Every wrong final traced to one cause class from the trace, declared now: routing (wrong or no workflow),
  data type / files, scale, counts, form, goal (vague vs concrete), linking (result words to workflow), check budget,
  binding of a reply, other. The class with most wrong finals is the candidate for the next round.
- The j4 arm G numbers (38/48) are on another set and other settings; they are cited, never subtracted.
- After scoring, j5 is seen.

## 4. Budget

- Authoring and review subagents: no API spend.
- j4 one arm (48 conversations, up to 3 turns) cost about US$0.30; ck1 / ca1 about US$0.01 per conversation.
- j5: about US$0.30-0.50. **Cap US$0.80**, enforced by the runner.
