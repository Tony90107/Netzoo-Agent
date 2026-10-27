# Jev forms round — offline results (2026-10-27): NOT PASSED (F2)

Code (rebased onto main 17dd2745): `interpretation/jev_forms.py` (frozen questions, `limiting_forms`, `doubted`,
`forms_doubts`), `graph/jev_forms_call.py` (flag `NETZOO_JEV_FORMS`, cache `NETZOO_JEV_FORMS_CACHE`, event
`core.jev_forms`), a `forms_reader` parameter in `build_capability_check`, `needed_facts.DIMENSIONS` time_model and
spatial, and router wiring; `tests/test_jev_forms.py` (10 tests). Jev reads cached in `jev-forms-cache.json` and
`jev-overlap-cache.json`, under US$0.002 beyond the US$0.0069 stability check.

Raw: `measure-overlap-only.json` / `measure-forms.json` (`measure_forms.py`, population-full.json, 53 readings),
`gates-measure.json`, `replay-off.json`, `replay-overlap.json` / `replay-forms.json` / `compare-overlap-forms.txt`
(harness via `adapter.py`, which injects the readers as the router does; without it the harness passes none and
sees no change).

| gate | result |
|---|---|
| F0 off = no change | flags off: replay 0 of 1388 changed vs replay-frozen.json; tests 5084 passed, 51 skipped, 0 failed (clean env) **PASS** |
| F1 controls untouched (hard) | 0 of 28 control readings changed (0/18 on the original population) **PASS** |
| F2 >= 75% of misreads doubted | 17 of 25 = 68% (14/22 = 64% original) **FAIL** |
| F3 scope | overlap+forms vs overlap only: 9 of 1388 calls changed, all to ASK/needs_fact (6 from DECLINE/full_gap, 3 from CLARIFY/goal_open), all population readings; no new DO or DECLINE; labelled right 609 -> 610 (C21, gold ASK) **PASS** |
| F4 reasons | 17 changed lines: each is the dimension's wait line ("the request does not say ..."), layer 2, or a subset of its old reasons; 0 new reason text **PASS** |

The F0 harness note: "0 of 1388" with only `NETZOO_JEV_OVERLAP=on` also holds without the adapter, because the
research scripts call the builder with no reader (the merge checks used `m2_adapter.py` for the same reason).

## The 8 missed readings (post hoc, not a gate)

| reading | why the hook did not act |
|---|---|
| R20 x2 (j3f, j3g) | A real overlap request: neutral network still leaves several_groups, and the overlap read confirms it. The refusal is right; the network misread changes nothing. |
| R13 x3 (j3f t1, j3g t1, t2) | time_model is doubted (P(dynamic) 0.00), but the credits (giraffe.tf_activity, activity_tests) also fail `needs_sign`: the signed entry was not credited. A second, separate credit miss. |
| J16 | The row is already available; the misread refused nothing. |
| J17 | Two readings of the same sentence disagree (regulator_gene and gene_gene); the builder fits the first, which fits, so the row is not "refused by its forms". |
| J01 | The wrong time reason is on a request-level condition row ("five time points"), not on an ask; the hook covers asks only. |

Over the 19 readings where the typed form alone refused the credits (excluding R20, R13, J16), 17 were handled (89%).
That figure is post hoc and is no gate.

## What changed in the calls (F3)

- DECLINE -> ASK on the network question: h5 Q06, nsbase/nsfields Q13, h6 R33, nsbase Q06, C21 (the user does not
  know which network; gold ASK).
- CLARIFY -> ASK: nsbase/nsfields J40 and nsbase L35 (CONDOR on a TF-gene edge list). The confirm question replaces a
  goal question for a request that names the run.
- j3 R39 and R47 also become the network question in the measurement; they are not in the harness corpus.

As declared, the round has not passed; nothing is proposed live without the user's decision.
