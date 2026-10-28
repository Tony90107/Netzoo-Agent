# Feature-count doubts typed and judged in code (2026-10-28, user: "修數量疑點")

## What the traces show (no code yet)

Recorded checks where the user gives a count as candidates ("X or Y") and the doubt is not judged in code:

- **Feature counts have no typed home in `unknown_facts`.** `UnknownAbout` lists `sample_count` but no
  `feature_count`, and the dedicated `count_alternatives` field is mostly left empty. So a feature doubt is either
  typed as a sample count (j2 Q42, 3 of 3 readings: "120 genes or 2,000 genes" -> `sample_count` beside a stated
  150 samples; COBRA's genes-vs-samples condition was then never weighed with the gene candidates) or dropped from
  the typed path (j3 R35, 2 of 2: "200 or 600 metabolites" kept as a choices domain but no unknown; the stated 600
  became a row of its own and LIONESS-DRAGON ran). The C45 note in `reconcile_unknown_counts` records the same
  limit ("The unknown schema cannot name feature_count").
- Sample-count doubts typed `sample_count` with choices are already judged (`needed_facts` outcomes over the
  candidates; j5 W39 asked "2 or 4?").
- Not in scope (first-read misses, no typed field to fix): j5 W26 (the stated 500 transcripts and 300 metabolites
  were never read, so the 20M cap could not be judged for 60 vs 70 samples) and j3 R14 (the gene-count doubt was not
  read at all).

## Change (contract shape + code)

1. `UnknownAbout` gains `feature_count` ("how many genes, proteins, metabolites or other features of one data type
   there are"); the count fields' descriptions name feature counts too.
2. An unknown `feature_count` with `count_kind` choices whose every value is stated in its quote is recorded as a
   feature-count candidate fact (reader `unknown_facts`) and compiled into the count alternatives (`of`=features),
   so `count_update` judges each candidate against the credited workflows' conditions (as phase 5b does for
   `count_alternatives`). Without verified choices it is not a fixed dimension: it stays an uncertainty quote for the
   fact agent, like `other`.
3. Sample-count unknowns are unchanged.

## Gates (declared before the code)

Offline:
- **F0** recorded readings never type `feature_count`: harness replay flags off 0 of 1388 calls changed vs
  `replay-frozen.json`; clean-env tests: no new failures beyond the known ones.
- **F1** unit tests on readings built like the traced ones: (a) Q42 shape (COBRA, 150 samples stated, "120 or 2,000
  genes" as `feature_count` choices) waits on the feature count with outcomes that differ by candidate; (b) R35 shape
  (LIONESS-DRAGON, 100 samples, 300 proteins stated, "200 or 600 metabolites") waits with 200 -> runs, 600 -> not;
  (c) choices whose numbers are not in the quote are ignored; (d) a `feature_count` without choices creates no fixed
  dimension ask and no crash; (e) a `sample_count` choices unknown gives the same result as before.
- **F2** OpenAI enum count of the check schema stays under the limit or compacts as today (check-enum-limit).

Live (only after the user agrees, gpt-4o-mini, 1 rep, cost listed first):
- Targets: seen items with a feature-count doubt (j2 Q42, j3 R35, p-set C45 and the p5 M01-D shape if recorded).
  **L1:** >= half of targets type the doubt `feature_count` and wait on it in code (before: 0).
- Controls: seen items with a sample-count doubt (j1 J08, J29, J40; j5 W26, W39; p5 S12) and DO items with stated
  counts and no doubt. **L2:** <= 1 sample-count doubt typed as `feature_count`; **L3:** 0 new asks on the no-doubt
  items.

Stop rule: a failed hard gate (F0, F1, L2, L3) -> withdraw; L1 below half -> withdraw; no gate is changed afterwards.
