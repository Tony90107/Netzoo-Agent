# The data confirm's unbound reply (declared 2026-10-28, before code)

User decision (2026-10-28): "Fix both layers". Found by the jev-forms session on j4 S35 (jev-conditions branch). The
guard asked "is the data you will use a gene-by-gene co-expression matrix…? (yes or no)". The reply "I checked: it's
the COBRA batch-adjusted co-expression matrix." confirms it, but does not start with a yes word. `bind_answers`
binds on the first word only, so nothing was bound. On turn 3 the confirm was `already_asked`, and the call fell
back to DO (gold DECLINE). An unsettled data confirm released a DO.

Branch `jev-merge` (= main df806e15). Flag `NETZOO_JEV_GUARD` as before; no new flag.

## Layer 1: Jev reads a reply the code did not bind

On the answer turn, if a `jev:condition` question is still pending (not bound by `bind_answers`), Jev reads the
latest reply once, on a closed menu:
- `yes`: the reply says the data really is as the question describes;
- `no`: the reply says the data is not as described;
- `not_answer`: it hedges, says they don't know, or is about something else.

State: the confirm question, the user sentence it quoted (if any), the contract line, and the reply. Only a pick at
confidence >= 0.7 counts:
- `yes` → DECLINE `jev_answer`, through `answered_core` (the same two-part reason);
- `no` → the call as it came.

## Layer 2: an unsettled confirm never releases a DO (code)

Still pending, and the read is `not_answer`, below 0.7, or failed, while the call is DO → ASK `jev_condition` again,
the same question, opened with "I need a yes or no to go on:". The P3 two-round cap still applies: past it the
call is an exhausted ASK, "nothing runs", never DO. Non-DO calls are left as they came.

## Offline test (`confirm_offline.py`; Jev only for layer 1; seen j2/j3/j4 items)

Each reply is read as the answer to that item's own confirm question. T items use their typed fact. For non-T items,
one fixed question is used ("is the data you will use somatic mutation calls per sample…?"), which none of them is
about.

- **Positives:** every T item's `reply_confirm` (j2 10, j3 6, j4 5) with its leading yes word removed ("Yes, they
  are …" → "They are …"), plus S35's own reply.
- **Negatives:**
  - every item's `reply_restate`;
  - every U item's `reply_fact` other than S35's;
  - three unsure replies per T item ("No idea, sorry.", "I'm not sure yet.", "I'd have to check with my
    student.");
  - one denial per T item ("No, that's not what we have; it's a different kind of table."), written now, before
    any run.

Gates:
- **L1 (recall):** positives read `yes` >= 0.7 on >= 75%.
- **L2 (precision, hard):** negatives read `yes` >= 0.7: 0.
- **L3 (stability):** S35's reply and 3 negatives (a denial, "No idea, sorry.", a restate), 10 reads each: every
  read falls on the same side of the decision (yes >= 0.7, or not).
- **F1 (fail-safe, unit tests):** an unsettled confirm never gives DO; with the round cap reached it is an
  exhausted ASK; a non-DO call is left as it came; a code-bound yes/no still takes the code path.

Plus the full suite (clean env) with 0 failures, and the flag-off replay at 0 of 1388. A failed hard gate (L2, F1)
means layer 1 is not kept; layer 2 is code-only and is kept on F1. Reported either way.

## Result (CONFIRM-OFFLINE.txt, US$0.006) — layer 1 withdrawn, layer 2 kept

- **L1 fail:** 6 of 22 positives read `yes` >= 0.7. S35's own reply read yes at 0.64.
- **L2 fail (hard):** 2 of 250 negatives read `yes` >= 0.7: j2 Q02 "It's the somatic mutation table." (0.89) and
  j4 S42's restate (0.80). Unsure 0/63, denials 0/21.
- **L3 fail:** S35 read `yes` 10/10, but at 0.59-0.70, so it falls on both sides of the threshold.
- **F1 pass:** unit tests show an unsettled confirm never gives DO; at the round cap it is an exhausted ASK; non-DO
  calls are left as they came.

As declared, layer 1 is not kept: the live path never calls `judge_confirm` (a test asserts it), and every unbound
confirm on a DO is asked again. S35 now ends as a re-asked confirm, then an exhausted ASK, never a DO. The cost is
that a natural "it's the COBRA matrix" reply needs the yes/no it is asked for.

Post hoc (not a gate):
- The two L2 "errors" are my own construction errors, not Jev errors. The fixed negative question asks about
  mutation calls, and both replies do say mutation data.
- L1's recall was likely depressed by the T-item question I used, the generic placed confirm ("could you confirm
  this about your data?"). It never names the fact, so Jev had to infer it from the quoted prompt.

A fair retest would use each item's own typed-fact question (as `condition_question` builds it) and controls written
against that question, on a fresh set. It needs the user's go-ahead.
