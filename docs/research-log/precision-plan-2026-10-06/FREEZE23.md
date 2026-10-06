# Log 384 freeze: the data-needs plan, re-declared for what it controls (precision and no regression)

This change was frozen before anyone on the implementing side had read the twenty-third held-out set
(`heldout23/`). An isolated subagent writes that set after this freeze.

## The frozen change

The candidate is unchanged from Log 383:
- `2f3f2cf`, whose diff is `data-plan-2026-10-06/dp_frozen.patch`, sha256 `02867cff064c`, 23 files against `161f33d`;
- it runs in the clean worktree `.worktrees/netzoo-dp-cand`.

No line of code differs from what Log 383 measured.

## Why it is declared again, with a narrower claim

Log 383 withdrew it because ask recall (A1, L2: 3/15 in both arms) and one needless-ask trap (T1) failed.

Logs 380, 381 and 383 together show:
- The candidate controls the reply layer exactly: Log 383's L3 12/12, L4 12/12, L5 0.
- The precision half held in every round:

  | Measure | Log 380 | Log 381 | Log 383 |
  |---|---|---|---|
  | Needless priors asks (base → cand) | 10 → 0 | 5 → 0 | 9 → 0 |
  | Ruled-out said | 17/17 | 9/9 | 10/10 |
  | Unusable tools offered (base → cand) | 8 → 1 | 7 → 0 | 7 → 0 |

- Ask recall is capped by inputs the candidate does not own: the study-purpose reading, the possession reading of borderline wording, and routing/operation authority.

So the claim is narrowed to what the candidate controls, plus a no-regression condition on recall:
- fewer needless data questions;
- ruled-out data said;
- no unusable tool offered;
- the reply shows the plan;
- **and** never fewer asks where they are needed than the current system.

This narrower claim is declared before heldout23 exists and is tested there. Logs 380-383 stay withdrawn as recorded. Nothing in them is re-judged.

## Known input limits (stated before heldout23, from Log 383)

- **Study-purpose reading:**
  - reads half of a two-part question (G4 in sets 21 and 22);
  - finds no claim in a statement-form purpose (s22 F1);
  - reads a third party's single-quoted note as the user's claim (s22 T1).
- **Possession reading:** "a reviewer insisted … must use", "not shared yet", "the database covers".
- **Routing:** "about to download JASPAR and STRING" is read as a download request.
- **The routing artifact `regulatory_network_and_tf_activity`** is not in the plan's TF artifact list. It matters only when no question is quoted.
