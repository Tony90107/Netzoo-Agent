# A doubt the task already asked or the user answered is never revived by jev_agent (2026-10-29, user: "先修退步")

## Trace (j6, regression of r1-jev-agreement, merged 1f788661)

- X02 (U, gold DO after "yes"): t1 `jev_agent` asks "Do you have the table ... coded as numbers?"; t2 the user's
  "Yes, we still have the table ..." binds (`task.answers_bound` agent yes), yet `agreed_fact_core` revives the same
  doubt sentence and asks again; t3 again; the final is the exhausted ASK.
- X22 (U, gold DECLINE after "400"): t1 the fact agent asks about the panel; after the answer, `jev_agent` revives
  another R1-rejected proposal on the same sentence ("Do you have at least three samples?", a wrong line), twice.

`agreed_fact_core` only skips sentences in `asked_sentences`, which holds `jev:` questions; agent questions (the
fact agent's and its own revived ones) are `source: agent` in the task state and were not seen. The r1-jev-agreement
ROUND called this a known limit bounded by the P3 cap; j6 shows it costs the user's answer.

## Change

`agreed_fact_core` also skips when the Jev sentence overlaps the user words of any agent question the task already
asked (pending) or the user answered (facts). Nothing else changes; turn 1 (no task state) is unchanged.

## Gates (declared before the code)

- **O1** recorded j6 X02 t2/t3 and X22 t2/t3, rebuilt: the rule no longer asks (`already_asked`); recorded W40 / J46
  turn 1 (ra2) still ask.
- **O2** unit tests: a pending or answered agent question on the sentence -> no revival; none -> unchanged.
- **O3** clean-env tests no new failures; flags-off replay 0 of 1388.
- **O4 live** (after the user agrees): X02 and X22, up to 3 turns, plus W40 turn 1; about US$0.04. X02 must end DO;
  X22 is reported (the answer to a fact-agent question is still not applied in code -- the W16 / R01 open item -- so
  its final may be DO, a false accept, rather than the gold DECLINE; this round does not claim it).

Stop rule: a failed gate -> withdraw; no gate is changed afterwards.

## Live addendum O4 (declared after the offline pass, before any run)

`run_live.py` (tag ao1): X02, X22 up to 3 turns; `run_live_w40.py` (tag ao2): W40 turn 1. Cap US$0.07 in all.
- **O4a (hard):** X02 ends DO, with no second `jev_agent` ask after the "yes".
- **O4b:** X22 asks no second `jev_agent` question after the answer; its final is reported (the fact answer is not
  applied in code -- W16 / R01 -- so DO, a false accept, is possible and is not claimed fixed).
- **O4c:** W40 turn 1 still shows the somatic question (reply text).
