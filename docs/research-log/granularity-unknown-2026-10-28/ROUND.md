# One contradicted granularity no longer discards the whole reading (2026-10-28, user: "A 保留讀取")

## Trace

j5 W01 ("I want one regulatory network for the tumours, built from all tumour samples together, and one for the
normals, rather than any per-sample networks."): the reading said `aggregate` with its own evidence; the code witness
`granularity_mentions` found only "per-sample networks" (its negation list has not/without/no, not "rather than"), so
`request_integrity_issues` raised `granularity_contradicts_request:aggregate` on both attempts, the interpreter
failed (ValueError), and the turn ended UNCHECKED ("Semantic routing unavailable").

Recorded turns that failed the interpreter with this issue: 8 (j5 W01; m3 P29; p3live J19 x2; h2 J45 x2, "kept
separate from the aggregate one" read as sample-specific; j1smoke S02 with other issues too; one Chinese local run).

## Change

On the last attempt only: when every remaining issue of a hypothesis is `granularity_contradicts_request`, that
hypothesis keeps its reading with `granularity` set to `unknown` (no scale claimed either way) and is validated
again; the turn records `routing.granularity_left_unknown`. Any other issue, or a contradiction on an earlier
attempt, is handled as before (the retry still sees the issue). No word list changes.

## Gates (declared before the code)

Offline, the recorded rejected readings re-validated with each turn's recorded user message (`session.json`):
- **U0** calibration: the code before the change reproduces each recorded issue list (cases that do not reproduce are
  reported and left out).
- **U1** every reproduced case whose only issues are granularity contradictions validates with the change, with
  granularity `unknown` on the flagged hypotheses and every other outcome field unchanged.
- **U2** a case with any other issue (j1smoke S02) still fails.
- **U3** unit tests: contradiction + another issue -> fails; contradiction on attempt 1 -> retried as before.
- **U4** clean-env tests: no new failures; flags-off harness replay 0 of 1388 (it replays the check, not the
  interpreter, so it guards only against side effects).
- Reported: the Chinese case (English-first: not gated).

Live only after the user agrees (turn 1 of W01, P29, J45; about US$0.03).
Stop rule: a failed gate -> withdraw; no gate is changed afterwards.

## Live addendum (declared 2026-10-28 after the offline pass, before any run)

`run_live.py` (tag gu1): W01, P29, J45, turn 1, 1 rep, cap US$0.10.
- **V1** none of the three ends with the interpreter failure ("Semantic routing unavailable" / routing_failed).
- Reported: each call; W01's gold is DO (PANDA / OTTER / GIRAFFE run once per group).
