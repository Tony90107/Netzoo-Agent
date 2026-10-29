# Jev-first, phase B' -- results (2026-10-29): C1 pass, **C2 and C3 FAIL** -> stop, as declared

The condition check (app prompt and schema, gpt-4o-mini-2024-07-18, temperature 0) ran on every arm's pairs: only 8
distinct pair lists needed the model (US$0.0005, 0 errors); code answered the rest. It changed no arm's score.

| arm (with the condition check) | gold-DO right (168) | vs H | gold-DECLINE false accepts (126) |
|---|---|---|---|
| M (mini) | 101 | +1 / -20 | 40 |
| H | 120 | -- | 42 |
| **HB** | **147** | +28 / -1 | **45** |
| H+group_membership | 135 | +15 / -0 | 47 |

- **C1 pass** (147 >= 125; 28 >= 2 x 1). **C2 fail** (45 > 44). **C3 fail** (45 > M's 40). Stop rule applied.
- So phase B's guess was wrong: the condition check does NOT refuse HB's new false accepts (j2 Q13 x2, j4 S32 x2);
  no stated requirement reaches it for those asks.

Reported only, not a gate (2 Jev calls, US$0.00007): the live Jev guard's typed data check (`check_typed_data`, not in
any replay here) on the two prompts --
- S32: `violated: "SAMBAR incompatible_input_artifacts: expression_matrix"` (data expression_matrix, 1.0) -- the app
  would refuse it there, for the right reason.
- Q13: not ruled out (data mutation_matrix 0.91). Its real reason (kmax 12 above 10 tumours) is a setting/count rule
  (`combination_issues`) that fires only when the reading carries the kmax setting.

What this leaves: of HB's extra false accepts, S32 is probably caught later in the live app and Q13 is a real gap --
today it is refused only by mini's `several_groups` misread, i.e. for a wrong reason. Neither changes this round's
verdict. Total spend on phases A, B, B': US$0.042.
