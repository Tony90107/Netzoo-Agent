# Jev-first typed fields, phase B -- results (2026-10-29): B1 pass, **B2 FAIL** (45 > 44) -> stop, as declared

367 asks read once each (one Jev call, five questions), US$0.017, 0 errors. Same 433 readings and check-level
rebuild as phase A. `SCORE.txt`, `shadow_b.json`.

| arm | gold-DO right (168) | vs H | gold-DECLINE check-level false accepts (126) |
|---|---|---|---|
| H (phase A) | 120 | -- | 42 |
| **HB** (H + five Jev fields) | **147** | +28 / -1 | **45** (4 new readings) |
| H + group_membership | 135 | +15 / -0 | 47 (5 new) |
| H + input_network | 126 | +6 / -0 | 41 |
| H + scale | 122 | +3 / -1 | 42 |
| H + needs_sign | 120 | 0 | 42 |
| H + regulator_kinds | 122 | +2 / -0 | 42 |

- **B1 pass:** 147 >= 125; wrong->right 28 >= 2 x 1.
- **B2 FAIL:** 45 > 42 + 2. By the stop rule no phase C is proposed from this round; the gate stays as declared.
- **B3:** group_membership is "harmful" (+5 false accepts alone); the other four are not.

What the new false accepts are (read, not used to excuse the gate):
- j2 Q13 x2 (gold DECLINE: kmax 12 > 10 tumours), j4 S32 x2 (SAMBAR given an expression matrix; it takes mutation
  data), and with group_membership alone j4 S22 (DRAGON network to CONDOR; HB's own input_network read refuses it).
- In H these were refused only because mini typed `several_groups` -- refusals for a reason the user never gave
  (the "overlapping memberships" reason). Jev's read removes the wrong reason, and the check-level code has no other
  rule that refuses them: the real reasons (SAMBAR's kmax vs samples when the settings are not read; expression vs
  mutation data, judged by the condition check model) are not in this pure-code replay.
- So the measurement cannot tell whether today's condition check would still refuse S32 and Q13; that is what the
  gate needed and did not get.

The one right -> wrong: j1 J21 (BONOBO with sparsify) credits nothing in HB.

Spend so far (phases A + B): US$0.041.
