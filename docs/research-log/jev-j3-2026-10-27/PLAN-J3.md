# Fresh sealed set j3: jev-guard + jev-overlap together (plan, 2026-10-27, awaiting approval)

User request (2026-10-27): one fresh sealed set testing both Jev branches together, with overlap controls and
grouping traps; two arms; gates declared. Plan and budget first; nothing runs before approval.

## 0. Code under test (no merge, no change)

- jev-overlap's tip **00c14271** already contains jev-guard's tip 62bade52 (checked: ancestor). It is frozen as is.
- The run uses its own worktree `.worktrees/netzoo-jev-combined` (branch `jev-combined` at 00c14271), so neither
  session's worktree is written. The records live there under `docs/research-log/jev-j3-2026-10-27/`.
- Arm F: `NETZOO_JEV_GUARD=off`, `NETZOO_JEV_OVERLAP=off` (the frozen system).
  Arm G: both `on`.
- Before the run: flag-off replay 0 of 1388 changed, and the test suite (clean env) as recorded. The runner refuses
  to start if the code differs from 00c14271.
- The open architecture points (the Jev call inside `build_capability_check`, two copies of the transport) are not
  touched before this test. Changing code now would test something else.

## 1. The set j3 (48 items, ids R01-R48)

Written blind by a subagent reading only `workflows/*.yaml` and `workflow_registry.py`, then a second blind subagent
reviews every gold. Both work in the j3 folder only and leave no helper script outside it. Everything is sealed with
SHA256 before any run, and I read only counts.

| group | n | gold (turn 1) | tests | replies |
|---|---|---|---|---|
| GT grouping, no overlap asked | 8 | DO | subtypes / clusters / communities in plain words (k ranges, "groups of samples", "modules of genes"); the shape mini misreads as several_groups. 4 name a workflow, 4 don't | `reply_membership`: natural words saying each item is in one group (not forced to the option label); `reply_restate` |
| GO overlap asked (controls, hard) | 6 | DECLINE | the user asks that one item may belong to several groups at once, or for a membership strength per group; written plainly, in varied words | `reply_restate` |
| GL grouping with a real limit | 4 | DECLINE | grouping asked, no overlap, but a stated contract limit fails (e.g. a k range above the sample count, a wrong input type for the grouping workflow) | `reply_restate` |
| T data-type trap | 6 | DECLINE | as j2 T (2 DRAGON different samples) | `reply_confirm` |
| TC data-type control | 6 | DO | as j2 TC (2 DRAGON same samples; 2 with an irrelevant uncertain aside) | `reply_restate` |
| U one unsure fact | 8 | ASK | as j2 U (4 → DO, 4 → DECLINE after the fact) | `reply_fact`, `fact_keywords`, `reply_restate` |
| N result in plain words | 5 | DO 4 / DECLINE 1 | as j2 N | `reply_restate` |
| V no result named | 5 | CLARIFY | as j2 V | `reply_result` (4 → DO, 1 → DECLINE) |

Every gold quotes contract text. GL golds must also say the true refusal reason, so reasons can be checked.

## 2. Runs (gpt-4o-mini, two arms, up to 3 turns)

Reply rule (run_j2.py, extended):
- After an ASK, use the first that applies:
  - `reply_fact`, when the question names the fact (a Jev question: also its quoted sentence);
  - `reply_membership`, when the question is the group-membership one;
  - `reply_confirm`;
  - `reply_restate`.
- After a CLARIFY: `reply_result`, else `reply_restate`.
- After anything else, the conversation ends.

Scored: the final call's kind against the final gold, and every DECLINE's reply text, for the overlap reason.

## 3. Gates (declared now, not loosened)

Overall, arm G vs arm F on the 48:
- **O1:** final right G >= F + 4.
- **O2:** FA, FR and MA each not higher in G.
- **O3:** 0 Jev-made declines (`jev_answer`) whose final gold is DO.
- **O4 (reasons):** finals that say "none returns overlapping memberships" on a non-GO item: G <= 1, and G <= F.

Per step (arm G):
- **OV1 (hard):** all 6 GO items end DECLINE and keep the overlap reason. None of them is asked the
  group-membership question.
- **OV2:** of the GT items arm F refused with the overlap reason, >= 2/3 end DO in G, or are still waiting on a
  question at turn 3 (reported apart).
- **S0:** J-ask false alarms on gold-DO items (GT, TC, N DO) <= 2.
- **S1:** step 1″ confirms >= half of the T items whose call was DO; on TC <= 1.
- **S3:** (with O3) answer declines reported, including recall.
- **S4:** `jev_link` on V <= 1.

A failed overall gate means the combination is not adopted. A failed step gate withdraws that step (the user may keep it
by decision). Post-hoc analysis is labelled as such.

## 4. Budget

- Authoring and review subagents: no API spend.
- Two arms × 48 conversations × about 1.8 turns ≈ 175 mini turns ≈ US$0.85, plus Jev under US$0.03.
- **Cap US$1.30** for both arms, enforced by the runner; arm F first.
- Time: about 15 minutes of setup (worktree, flag-off checks, runner and scorer), about 15 minutes of authoring and
  review, and about 30 minutes of runs.
