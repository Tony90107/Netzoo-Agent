# A "No" to "at least N samples?" rules the workflows out (2026-10-31, user: "Yes, write it")

## Why

The user's app test (answer buttons on): "I want a separate gene co-expression network for each of our skin biopsies.
I'm not sure whether we'll end up with five usable biopsies or only two." One run asked the count question ("2 or
5?", judged in code). My check run (`.worktrees/netzoo-ab`, session `q3-click-no-user-check`, US$0.01) got the fact
agent's yes/no form instead -- "Will you have at least three usable biopsies?" -- and the user's **No** was bound
(`task.answers_bound`: no, with LIONESS-COEXPRESSION's "Require at least three samples ..."), yet the turn ended DO
recommending LIONESS-COEXPRESSION and BONOBO, both needing three samples.

Cause: the agent-answer step (`agent_answer_call`, agent-answer-anchor-2026-10-29) skips a quoted line that is a count
rule -- counts were meant to be judged in code through the count question -- so a yes/no question about a count has no
step that applies its answer. Recorded runs: 46 of 143 agent questions quote a count rule (35 `min_samples`, 9
features > samples, 2 kmax). Not caused by the buttons: a typed "No" is bound the same way.

## Change (code only after this file is committed)

Branch `count-answers` from main 12d8409e. Flag `NETZOO_COUNT_ANSWERS`: off (default) / shadow / on. New module
`graph/count_answer_call.py`; a hook of at most three lines in `graph/routing_planning.py` after
`apply_agent_answer`.

1. **Scope.** The answer turn of an agent yes/no question (bound in code this turn: a button, or a reply starting with
   yes/no) whose quoted line contains, verbatim, an input check of one of its workflows with `limit: min_samples`,
   and whose question names that workflow's minimum (`workflow_conditions.conditions_for(...).min_samples`) as a
   number, in digits or words. Anything else (features > samples, kmax, another number, an unbound reply) is left as
   today.
2. **"No"** means the user's count is below that minimum. Code judges each workflow of the call with today's count
   rule (`data_issue(conditions, minimum - 1, None)`): a workflow whose own minimum it fails is ruled out. If none is
   left, the call becomes DECLINE `count_answer` with one line built in code, in the agent-answer format: `You answered
   "No" to "<question>". <WORKFLOW>'s contract: "<input check text>". So <WORKFLOW> cannot do this as you asked.` If
   some workflow is left, the call keeps only those (recorded).
3. **"Yes"** changes nothing.
4. Only a DO (or PARTIAL) call is changed. Recorded as `core.count_answer`.

## Gates

### Offline (pure code; recorded current-system runs j1-j8, j9 r1-r3, j10 arm M r1-r3)

- **E1 (hard)**: on every recorded answer turn of an in-scope question, flag on vs off: a "yes" answer changes nothing
  (0 changes); every "no" answer's new call is listed with its gold, and none turns a gold-DO end into a refusal.
- **E2 (hard, build)**: unit tests (scope, no, yes, mixed minimums, number in words and digits, unbound reply, off,
  shadow); flags-off replay byte-identical to `sa-off.json`; clean-env suite no new failures; module sizes.

### Live (after E1-E2 and the user's go-ahead; at most 12 conversations, about US$0.06, cap US$0.12)

Four prompts whose sample count is in doubt around a three-sample minimum (the user's biopsy prompt and three like it,
written before the run), flag on, buttons on: each run twice clicking the answer that means "below the minimum" ("No",
or the smaller count when the count question is asked instead) and once clicking the one that meets it.
- **F1 (hard)**: no "meets the minimum" run ends worse than the same prompt with the flag off would allow (it must not
  be refused for the count).
- **F2 (target)**: >= 6 of the 8 "below" runs end DECLINE with the minimum-samples contract line (or, when the count
  question was asked, with today's count refusal).

**Stop rule.** E1, E2 or F1 fails -> withdrawn, code reverted. F2 fails with the rest passing -> no claim; the user
decides. Merging needs the user; the flag stays off by default.
