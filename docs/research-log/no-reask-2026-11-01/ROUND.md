# The fact agent does not ask an answered doubt again (2026-11-01, user: "Start with step 1")

## Why

count-answers live (`count-answers-2026-10-31/RESULTS-LIVE.md`): P4 r3 asked "Will you have at least three matched
samples?" -> Yes -> the same question again; P3 r2 answered the count question "2 or 4?" with 2 and was then asked
"Do you have at least three tumour samples?". In both, turn 2's fact agent proposed the doubt again on the same user
words. The task state holds the answer, but the fact agent's questions are never compared with it (the Jev path has
`asked_doubts`; this path has nothing), and the fact key -- the words' position in the request -- shifts when the
follow-up wraps the request (P4 r3: 117-178 -> 139-200).

Recorded runs (j1-j10 current system, the answer-buttons and count-answers live runs): of 108 questions asked after
turn 1, 12 ask a doubt the task had answered. By source: Jev fact 6, Jev agent 3, fact agent 2 (P3 r2, P4 r3), count
question 1, form question 1 (j6 X06 -- a different question on the same sentence). This round takes only the fact
agent's two: the Jev paths are the jev-guard session's module; the count question comes from the check's waits.

## Change (code only after this file is committed)

Branch `no-reask` from main 0269b806. Flag `NETZOO_NO_REASK`: off (default) / shadow / on. In
`graph/fact_check_call.apply_fact_check` (a few lines, through a new pure helper in `interpretation/answered_doubts.py`):
a fact-agent question (accepted or queued) whose user words overlap -- folded, one inside the other -- the user words of
a fact this task already holds as **known** from an **agent** or **count** question is moved to `rejected` with rule
"R9 answered" and is not asked. A known form/dimension answer never blocks a question (X06). Pending, unanswered
questions are left to today's rules. With nothing left to ask, the turn is decided as today without that question
(the answered count then applies through `answered_check`).

## Gates

### Offline (pure code)

- **N1 (hard, precision)**: on every recorded later turn, the helper (flag on) blocks only questions whose answered
  doubt is the same thing asked -- listed one by one: the two known cases (P3 r2, P4 r3) blocked; X06 (form answer)
  not blocked; nothing else blocked that asks something the answer did not settle.
- **N2 (hard, build)**: unit tests (blocked after agent yes/no, after a count; not after a form answer; not on a
  pending question; off; shadow); flags-off replay byte-identical to `sa-off.json`; clean-env suite no new failures.

### Live (after N1-N2 and the user's go-ahead; at most 8 conversations, about US$0.04, cap US$0.08)

count-answers' P3 and P4 prompts, 4 runs each with the flag on (buttons and count answers on), clicking as in
count-answers (2 below, 2 meets).
- **M1 (hard)**: no conversation asks a question about a doubt it already answered (fact-agent path).
- **M2 (hard)**: no run ends worse than the count-answers live runs of the same prompt and click.

**Stop rule.** Any hard gate fails -> withdrawn, code reverted. Merging needs the user; the flag stays off by default.
