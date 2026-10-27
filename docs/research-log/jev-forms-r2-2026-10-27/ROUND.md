# Jev forms round 2: no doubted form reason on a credited row with another blocker (2026-10-27) — declared before code

User decision (2026-10-27): when a row credited to a workflow is refused, and something besides the typed form also
blocks it, a form attribute Jev doubts must not be said as the reason. Declare gates, then measure offline. Same flags
(`NETZOO_JEV_FORMS`, `NETZOO_JEV_OVERLAP`), questions, cache and threshold; branch `jev-forms`.

## Problem (jev-forms RESULTS-LIVE.md)

jf1 R13 t2: "time-course samples" typed `time_model=dynamic` and credited GIRAFFE's tf_activity only. Jev doubts the
time form (P(dynamic) 0.00), but the credits also fail `needs_sign` (the signed entry was not credited). So
`forms_doubts` does nothing, and the decline says "No registered workflow models how the system changes from one time
point to the next", a reason the user never gave. The overlap form has the same gap: on a credited row, the overlap
read is consulted only when overlap is the only blocker.

## Change

In `jev_forms.forms_doubts`, credited and refused row: as now, doubted forms whose neutral values make the credits fit
become waits. Otherwise (another blocker remains), each doubted form with a form reason (`time_model`, `spatial`, and
`group_membership` when the overlap read doubts it) is added to `doubted_forms`, so `_form_reasons` leaves it out. The
line then says the remaining verified reasons, or layer 2. Status, credits, waits and calls do not change.
`input_network` has no form reason, so it is unaffected. Only with `NETZOO_JEV_FORMS` on.

## Population (`population.json`) and labels

Every recorded reading (replay corpus, j1/j2/j3, jo1, jf) with a credited result ask typed `time_model=dynamic`,
`spatial=uses_neighbors` or `group_membership=several_groups`: 69 readings, 29 requests. One labeller (me): does the
request ask for that form?
- Controls (it does; 9 requests): JN8, QN5 (overlapping communities); SN5 (a dynamic model); j3 R16, R19, R20, R45,
  R46, R48 (overlapping or soft memberships).
- Misreads (20 requests): h5 Q26, J22, M45, j1 J01, W13, j2 Q02 (t1 and t2 texts), Q08, Q18, Q29, Q36, Q38, j3 R12,
  R13 (t1 and t2 texts), R18 (t1 and t2 texts), R31, R34, R39.

## Measurement

Each reading's check is rebuilt from its recorded proposal (as `jev-forms/measure_forms.py`). Both readers are on;
the current code is compared with the changed code. Each result row's line is rendered, and a form reason is the
sentence of `_FORM_REASONS` for time_model, spatial or group_membership. Calls: harness replay through
`jev-forms/adapter.py`, flags on.

## Gates

- G0, off = no change: flags off, harness replay 0 of 1388 changed vs `replay-frozen.json`; the test suite (clean
  environment) has no new failures.
- G1, precision (hard): 0 control readings lose a form reason they print with the current code.
- G2, recall: of the misread readings that print a form reason with the current code (both flags on), >= 75% no
  longer print it.
- G3, calls unchanged: flags-on harness replay changes 0 calls vs the current code; no row's status, credits or wait
  changes on the population.
- G4, reasons: every changed line only loses form-reason sentences (the rest is a subset of the old line) or falls to
  layer 2; no new reason text.

Stop rule: if G1 fails, the round is withdrawn as declared.
