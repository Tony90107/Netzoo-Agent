# A "layer count" doubt whose candidates are feature-sized is a feature-count doubt (2026-10-29, "下一階段的修復")

## Trace (j6 X22, gold DECLINE after "400"; ends DO, a false accept)

"I don't know yet whether the metabolomics core used their 150-metabolite panel or their 400-metabolite panel." The
reading typed the doubt `omics_layers` with choices [150, 400] (j6a and ao1 alike), so the feature-count path
(feature-count-doubts-2026-10-28: 150 -> 550 features fit LIONESS-DRAGON's 20,000,000 values, 400 -> 800 do not) never
ran; the fact agent asked instead, and its answer is not applied in code (W16 / R01).

Recorded readings with an `omics_layers` doubt and candidate values: every one whose smallest candidate is >= 96 is a
feature count (17 distinct requests: "150 or 400 metabolites", "250-gene or 2,000-gene panel", "96-gene panel or the
full 18,000-gene matrix", C45, R35, S15, Q14, ...); the genuine layer-count doubts have candidates 0-3.

## Change

An `omics_layers` unknown with `count_kind` choices whose smallest candidate is >= 10 (no request has ten or more omics
data types) is read as a `feature_count` candidate fact, with the same verification as a typed one (every candidate
stated in its quote), and judged in code by `count_update`; it is not also a fixed omics-layers dimension. Smaller
candidates are unchanged.

## Gates (declared before the code)

- **L1** harness replay flags off vs `replay-frozen.json`: every changed call listed beside its gold; **0 right ->
  wrong**.
- **L2** unit tests: X22 shape (100 tumours, 400 transcripts, "150 or 400 metabolites" as omics_layers) waits with
  150 -> LIONESS-DRAGON, 400 -> none; a (1, 2) layer doubt is unchanged; numbers not in the quote are ignored.
- **L3** clean-env tests no new failures.
- **L4 live** (after the user agrees): X22 up to 3 turns (the count question is code-judged; "400" binds and declines)
  plus W40 turn 1 unchanged; about US$0.03.

Stop rule: a failed gate -> withdraw; no gate is changed afterwards.

## Live addendum L4 (declared after the offline pass, before any run)

`run_live.py` (tag lc1): X22 up to 3 turns; `run_live_w40.py` (tag lc2): W40 turn 1. Cap US$0.07 in all.
- **L4a:** X22's turn 1 asks the code-judged feature count (150 or 400); after "400" the final is DECLINE (gold).
- **L4b:** W40 turn 1 still shows the somatic question.
