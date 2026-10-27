# j2 two-arm run (PLAN-J2.md) — overall gates pass; S3 fails → step 3 withdrawn as declared (pending user decision)

Frozen code b0c1e85a; j2 sealed (items.json dc687d77…). Arm F (guard off) and arm G (guard on), gpt-4o-mini, up to 2
turns, 48 conversations each; spent US$0.54 together (cap 1.00). Raw: RESULTS-J2.txt, gates-j2.json.

| | final right | FA | FR | MA | extra q | UNCHECKED |
|---|---|---|---|---|---|---|
| F (guard off) | 25/48 | 7 | 7 | 5 | 3 | 1 |
| G (guard on)  | **30/48** | **5** | **6** | **0** | 4 | 3 |

By group F → G: T 4→5, TC 8→9, U 5→9, N 4→4, V 4→3.

| gate | result |
|---|---|
| O1 G >= F + 3 | 30 vs 25 **PASS** |
| O2 FA/FR/MA not up | 7→5, 7→6, 5→0 **PASS** |
| O3 no wrong Jev decline | none **PASS** |
| S0 J-ask false alarms on TC/N DO <= 2 | 0 **PASS** |
| S1 step 1″: T DO items confirmed >= 4, TC <= 1 | Q12 Q33 Q46 Q48 of 6; TC 0 **PASS** |
| S3 step 3: answer declines >= half of failing replies | Q05, Q33 of Q05 Q12 Q33 Q46 Q48 **fail** |
| S4 step 4: V links <= 1, N CLARIFY linked >= half | V 0; Q07 Q14 Q37 of 4 **PASS** |

As declared, a failed step is withdrawn: step 3 (the answer read), unless the user decides otherwise.

## Why S3 failed (post hoc)

- Q48 (wrong): the step-1″ confirm quoted the typed field as `LIONESS-PANDA input_checks refuses_input:
  coexpression_matrix`, the field key, not the check's own text ("An aggregate COBRA adjusted co-expression artifact
  is not a direct LIONESS handoff"). Jev read "Yes, the input would be the COBRA adjusted co-expression matrix" as
  `meets` (0.92). Final DO, a false accept. A defect of the 1″ wiring: the refuses_input quote should be the
  input_check's verbatim text.
- Q46: `meets` at 0.52 (< 0.7), so no action; the system then said DO.
- Q12: Jev read `fails` (0.97), but the system had already declined on turn 2 (the answer step acts only on a DO).
  The final was right; it does not count as caught.
- Q05, Q33: declined by the answer with both quotes, both right.

UNCHECKED 1 → 3 (Q10, Q26 check_unconfirmed) is the reading's variance. The guard cannot make UNCHECKED.

## User decision (2026-10-27): step 3 KEPT

The user kept step 3 despite S3, and asked to fix the refuses_input quote to the input_check's own text, add a test,
and check it offline on the recorded j2 replies (no new live run).

## Fix and offline re-judge (REJUDGE-J2.txt, Jev only, no agent run)

Fix: a refuses_input rule now quotes the input_check's own text (`ruled_out`); a test asserts it is verbatim YAML
and has no field key. Flag off: replay 0 of 1388 changed; 5055 tests pass.

Re-judging the 7 recorded answer turns of arm G with their lines (the fixed text for Q46, Q48):
- Q46 meets 0.52 → fails 0.69, and Q48 meets 0.92 → fails 0.59. The misread is gone, but both are under 0.7, so the
  call stays the system's (DO).
- Q33: same line, same reply; fails 0.88 → 0.40. Jev's confidence on answer reads varies run to run, more than on
  the kind question (30/30 identical).
- Q05: declined both times. Q21, Q27: meets both times. Wrong declines: 0.

Correction to the S3 note above: `meets` never changes a call, so Q48's final DO came from the system's own turn-2
reading. The step failed to catch it; it did not cause it. Step 3 adds no wrong declines, but its recall is fragile
(1-2 of 5 here).
