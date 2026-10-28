# j6 results -- the app after the 2026-10-28 fixes, fresh sealed set (2026-10-29)

Run j6a: code 1f788661 unchanged throughout, app settings (GUARD, OVERLAP, FORMS on; own check model; 30k turn budget;
45k check allowance), gpt-4o-mini, 30 conversations, up to 3 turns, 1 rep. Spent **US$0.195** (cap 0.40).
Scores: `RESULTS-J6.txt`, `score-j6.json`. j6 is now seen.

## Headline

| | j6 (this run) |
|---|---|
| right finals | **25 / 30 (83%)** |
| FA / FR / MA | **0** / 2 / **0** |
| extra questions / wrong question kind / UNCHECKED | 3 / 0 / 0 |
| enum 400s, check-family refusals, provisional checks | 0, 0, 0 |
| form reasons said on a DECLINE the item did not ask for | 0 |

j5 was 36/48 (75%) on another set; cited, not compared. No false accept and no missed question on j6.

## The 5 wrong finals, by cause (read from the traces)

| item | gold | what happened | cause |
|---|---|---|---|
| X02 (U, design table exists?) | DO after "yes" | t1 asks via `jev_agent`; t2 the "yes" binds (`task.answers_bound` agent yes) but `jev_agent` revives the same doubt sentence and asks again; t3 again -> exhausted | **regression of r1-jev-agreement**: an answered agent question is revived (the `asked_sentences` limit noted in that ROUND) |
| X22 (U, 150 or 400 metabolites) | DECLINE after "400" | t1 fact agent asks; t2 after the answer, `jev_agent` revives an R1-rejected proposal on the same sentence ("Do you have at least three samples?", a wrong line), t3 again | **same regression** (plus the feature count not typed in code this time) |
| X07 (TC, 80 patients, LIONESS-DRAGON) | DO | the count reader took "80 type 2 diabetes patients" as candidates "2 or 80"; asked 3 rounds | count words: "type 2" is a label beside a count, both digits (the mixed-notation rule does not cover it) |
| X06 (GT, CONDOR on a TF->gene edge list) | DO | t1 group_membership asked, answer bound; t2 input_network asked though the prompt says "TFs as sources and genes as targets"; the reply did not answer it; t3 DECLINE full_gap | form question on a stated network, then the full gap after it |
| X30 (SA, OTTER one network per stage) | DO | t1 DECLINE full_gap: "one TF-to-gene network per stage, each built from all 12 samples" not matched | per-group aggregate result not linked (OTTER named) |

## Reading

- 2 of the 5 misses are a regression from the round merged yesterday (r1-jev-agreement): after the user answers, the
  rule asks again. It must be fixed first.
- The rest are one each: a count-word label ("type 2"), a needless form question on a stated network, and a
  per-group result not linked.
