# data-has -- offline measurement (2026-10-29): D1, D2 PASS

348 j1-j8 gold items, opening prompts; the guard's existing data read and the new has-read (`HAS_INSTRUCTIONS`, the
guard's `DATA_CRITERIA` options), each one Jev call; US$0.016, 0 errors. `SCORE.txt`, `measure.json`.

| Gate | Result |
|---|---|
| D1 precision (hard) | gold DO / PARTIAL items (158) with a gold workflow ruled out: existing 0, new 0, **union 0** -- PASS |
| D2 recall | j2 Q18: existing `expression_matrix` 0.32 (below 0.7), has-read `expression_matrix` **0.80** -> SAMBAR ruled out by its `incompatible_input_artifacts`. Data-type gold-DECLINE items (27): existing 17, union **18** -- PASS |

Small and precise: the has-read adds Q18 and nothing else (its reads track the existing ones, mostly a little less
confident; it never ruled out a gold-DO workflow). The 9 data-type items neither read catches are N n_decline items
whose refusal is not a data kind (or "several").

Next by the ROUND: build it in the guard's `check_typed_data` (jev-guard session first), replay + tests, then live.

## D4 stability (10 has-reads each, US$0.0007, `STABILITY.txt`): **FAIL** -> withdrawn, no app code written

| item | rule-out of | result |
|---|---|---|
| j2 Q18 | SAMBAR | 10/10 expression_matrix 0.73-0.81 -> ruled out every time (stable) |
| j8 Z14 (chain control) | CONDOR | 0/10 ("several" 0.51-0.57) |
| **j5 W17 (chain control)** | CONDOR | **1/10** (expression_matrix 0.70 once; 0.63-0.67 the other nine) |

D4 required W17 never to rule out CONDOR; once in ten did. Stop rule: withdrawn. Only `interpretation/data_has.py`
(the frozen question, used by the measurement) was committed; no guard code was written.

What the miss is (read, not used to change the gate): W17 is ruled out through the guard's broadest rule -- "a single
kind outside the workflow's declared input_artifacts" (CONDOR declares a regulatory network; expression is not listed
as incompatible) -- while Q18 is ruled out through SAMBAR's explicit `incompatible_input_artifacts: expression_matrix`.
The existing data read sits at the same edge for W17 (0.69), so the risk is not new, but this round would have added
a second chance to cross it. A has-read that applied only the explicit incompatible field would keep Q18 and never
touch W17; that would be a new round with its own gates.
