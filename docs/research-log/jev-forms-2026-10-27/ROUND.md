# Jev forms round (2026-10-27) — declared before any code

User decision (2026-10-27): generalize the overlap second read to `time_model`, `spatial` and `input_network`
(`group_membership` already done). Jev asks only about the user's words on a closed menu; when it disagrees, the
system asks a closed-option confirm question bound in code; it never lifts a limit. Declare gates, measure offline,
then ask the user. Branch `jev-link-gap` from main 4df817b6, worktree `.worktrees/netzoo-jev-link`.

## Problem

A typed attribute that alone rules the credited workflow out clears a right answer, the same way overlap did:
- j3 R13: "time-course samples", typed `time_model=dynamic`. The decline says no workflow models change from one
  time point to the next; gold DO (GIRAFFE).
- j3 R39 and a recurring CONDOR family: a TF-to-gene edge list typed `input_network=gene_gene`, which rules CONDOR
  out (it takes a regulator-gene network). Gold DO.

## Population (`population.json`) and labels

Every recorded reading (replay corpus 1388, j1/j2/j3 live, jo1) with a result ask whose typed value is a limit:
`time_model=dynamic`, `spatial=uses_neighbors`, or an `input_network` value that excludes a credited produces entry.
40 readings, 24 distinct requests. One labeller (me), on one textual property each: does the request say it?

- Controls (the user does say it; 9 requests): time_model HN2 NN7 QN8 RN1 SN5; spatial QN10 SN8; input_network Q18
  (a DRAGON microbe-metabolite edge list) and Q34 (a DRAGON matrix).
- Misreads (14 requests): time_model J01 (h2hyb), C23, R13 (t1, t2); input_network J16 (no network at all), Q06,
  R33, J40, L35, Q13 (nsbase), J17, J48 (t2), R47, R39, R20. (R20 is an overlap request: its refusal stays right
  through the overlap reason; only its network type is misread.)

All seen. A claim beyond them needs a fresh sealed set.

## Stability (done before this file; `forms_q.py` frozen, `stability.py`, `stability.json`)

30 repeats on 11 (attribute, request) pairs, 330 calls, US$0.0069. Ruling-out probability per pair:
time R13 0.00, C23 0.02-0.03, HN2 1.0, RN1 1.0; spatial QN10 1.0, SN8 1.0, R13 0.00; network (P(gene_gene or other))
R39 0.00, J40 0.00, Q18 1.0, Q34 1.0. C23's top choice varies (separate 24 / not_stated 6); the rule's probability
does not.

## Change (new flag `NETZOO_JEV_FORMS`, default off; `shadow` records, `on` applies; `NETZOO_JEV_OVERLAP` unchanged)

1. Rule: an attribute is doubted when Jev's probability on the options under which the typed value is what the user
   said is <= 0.3. Those options are: time `dynamic`; spatial `uses_neighbors`; network the typed value's kinds that
   exclude a credited entry (`gene_gene`, `other`, or `regulator_gene`, whichever the credits cannot take).
2. Credited row, refused: Jev reads each limiting attribute. If the credits fit with every doubted attribute set to
   its neutral value, the doubted attributes become waits (`needs_fact`). The question uses a `needed_facts`
   dimension, existing for input_network, new for time_model and spatial, with option labels sharing no word, and
   `bind_answers` binds it. The answer settles the wait next turn (`answered_check`).
3. Uncredited row: time_model and spatial get `doubted_forms` as overlap did, so their form reason is not said
   (layer 2 instead). input_network has no form reason; it is not read there.
4. Jev never makes a DO or a DECLINE, never picks a workflow, writes no reason; a failure leaves the row as it was.
   group_membership keeps its frozen question, cache and flag.

## Gates (offline, all must pass; then ask the user)

Measured by rebuilding each population reading's check from its recorded proposal (as `jev-overlap`'s
`measure_reasons.py`), plus the harness replay for calls.

- F0, off = no change: flags off, harness replay 0 of 1388 calls changed vs `replay-frozen.json`; with only
  `NETZOO_JEV_OVERLAP=on`, rows and lines identical to main's overlap behaviour on the population; the test suite has
  no new failures (clean environment).
- F1, precision (hard): 0 control readings get a form wait, or lose a form reason they print.
- F2, recall: >= 75% of misread readings are doubted. A credited reading counts when it turns into the
  attribute's question; an uncredited reading counts when it loses the wrong form reason.
- F3, scope: flags on (overlap + forms) over the harness replay: every changed call is a population reading, and no
  call changes to DO or to DECLINE (changes to ASK are listed).
- F4, reasons: every line that changes says only already-verified reasons, layer 2, or the dimension's wait line;
  no new reason text.

Stop rule: if F1 fails, the round is withdrawn as declared. The questions in `forms_q.py` are not reworded.

## Not measured offline

Turn 2 binding is covered by unit tests only. A live check (<= 16 sessions) is proposed only after the user sees
these results.
