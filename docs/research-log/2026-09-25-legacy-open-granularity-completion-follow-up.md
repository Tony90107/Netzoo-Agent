# Legacy Open Granularity Completion Follow-up

## Finding

The saved `gran-mirna-unstated-control` Legacy trace reproduces a gap in the
Legacy semantic path. Its first interpretation proposes `aggregate` without
grounding evidence. The recorded repair changes that value to `unknown` and
adds inferred evidence that the user has not decided between one cohort network
and separate per-patient networks. The router then asks whether the user wants
aggregate or sample-specific output.

Claims already calls `complete_open_granularity_alternatives()` before evidence
validation. Legacy restored stated fields and went directly to validation. It
therefore accepted one `unknown` hypothesis without representing either literal
candidate, even though the request explicitly names both choices. This was a
cross-contract integration gap; the shared completion helper already existed.

## Change

The Legacy interpreter now calls the shared completion helper after stated
field restoration and before evidence validation. The helper only expands a
granularity choice when the request leaves it open, both alternatives have
literal text witnesses, and the existing hypotheses share the same non-
granularity outcome and assumptions. The expanded hypotheses are adopted only
after they pass the existing evidence validator; otherwise the original set is
kept and a rejection event is recorded.

Added a self-contained offline regression using minimal first-pass and patch
replies distilled from the saved Legacy trace. It exercises
`_invoke_semantic_interpreter()` and checks that the final hypotheses contain
both `aggregate` and `sample_specific`, the matcher remains ambiguous and asks
the expected question, and the assembled `requested_outcome.granularity`
remains `unknown`.

The routing evaluator also has regression coverage for both sides of this
consistency contract: it rejects a selected `requested_outcome.granularity`
while asking for clarification, and it rejects a clarification result whose
hypotheses omit either literal alternative.

## Verification

- Before the Legacy-path change, the saved-trace regression failed with the
  final hypotheses equal to `["unknown"]`.
- After the change, the saved-trace regression passed.
- Related outcome, semantic, and empty-reading tests: 117 passed, 1 skipped.
- Evaluator consistency regressions: 2 passed.
- Full offline suite: 2046 passed, 53 skipped, 0 failed; two pre-existing
  dependency deprecation warnings.
- `python scripts/evaluate_routing.py --json`: 39 cases validated in
  `corpus_validation_only` mode. This checks corpus validity, not prompt/model
  accuracy.
- Ruff, `compileall`, and `git diff --check` passed for the changed code.
- No live provider was called.

## Remaining Limits

This verifies one captured Legacy trace and deterministic offline behavior; it
does not establish live model accuracy. The broader saved Legacy A/B replay
previously matched the current call sequence in only 3 of 5 cases, so those
non-matching rows are not valid end-to-end replay evidence. Its captured policy
hash also differs from the current policy hash, which limits contract-to-
contract comparison. Do not treat these results as support for promoting the
Claims contract to production default. The separately handled `prompt_seq`
desktop communication issue remains outside this repair.
