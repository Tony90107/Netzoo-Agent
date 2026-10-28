# Candidates never mix digits and number words (2026-10-28, user: "先修 R35")

## Trace

R35 (fc1, after feature-count-doubts): the doubt "200 or 600 metabolites" is now typed `feature_count`, but
"layer one being 300 proteins" is read by the side-by-side reader as the candidates 1 or 300 (`count_words._beside`
takes any one word between two numbers: "one being 300"), so the stated 300 proteins never reach the method.

All side-by-side / context candidate runs in the recorded checks (19 distinct): the 4 whose numbers mix digits and
number words are all labels, not candidates ("Layer one is 60 metabolites", "layer two is 90 proteins", "layer one
being 300 proteins", "the full one has 1,500 transcripts"); the 15 written in one notation ("10 or 15", "two or
four", "2 to 4", "either 100 or 200") are the user's candidates or ranges. A user giving candidates for one count
writes them the same way.

## Change

`count_words`: a run of side-by-side numbers that mixes digits and number words is not a run of candidates
(`side_by_side_values`, `candidate_runs`). Form only, no word list. Nothing else changes; the doubt sentence read as
a result row of its own (R35's second blocker) is not touched in this round.

## Gates (declared before the code)

- **M0** harness replay flags off vs `replay-frozen.json`: every changed call listed beside its gold; **0 changes
  from right to wrong**; clean-env tests: no new failures.
- **M1** unit tests: the 4 mixed quotes give no candidates; the 15 one-notation quotes give the same values as before.
- **M2** R35 rebuilt from its recorded fc1 reading (no model call): the 300 proteins are in the LIONESS-DRAGON row's
  method and the "1 or 300" doubt is gone. Whether R35 then waits on 200 / 600 is reported, not gated (the second
  blocker may remain).

Stop rule: M0 or M1 fails -> withdraw; no gate is changed afterwards. Live only after the user agrees.

## Live addendum (declared 2026-10-28 before the run, user "跑 live")

`run_live.py` (tag mn1): R35, R22 (targets) and J40, W39 (one-notation controls), turn 1, 1 rep, cap US$0.10.
- **N1** no target reading keeps a digit/word candidate fact (before: R35 2/2, R22 2/2 recorded readings did).
- **N2** both controls keep their sample-count candidates (J40 25/30, W39 2/4) as unsure facts.
- Reported, not gated: whether R35 waits on 200 / 600 (depends on the reading typing the doubt `feature_count`).
