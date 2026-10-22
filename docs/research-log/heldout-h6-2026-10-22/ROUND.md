# Held-out set h6 -- declared before authoring (2026-10-22)

Plan: `collab/ROUND-26-PLAN.md` sections 1.1 and 4; the user approved phase 0 on 2026-10-22.

## Sealing

- h6 is written and gold-reviewed now, and used once, in the plan's final validation (section 4). Until then I do
  not open `items-author.json`, `items.json`, `GOLD-REVIEW.md` or `fields.json` here, and no development step reads
  them. The only code that touches them prints counts (`check_format.py`) or the text-only baseline's score and the ids
  it gets wrong (`baseline_audit.py`) -- never a prompt.
- The subagents' replies are asked for counts only, never items.

## Code for the final run

The frozen worktree `.worktrees/netzoo-h6-run`, detached at `77c339a3` (the code before any ROUND-26 change). Its
`workflows/*.yaml` are identical to the h5 run's (`diff -rq`).

## Items

- `items-author.json`: 48 English items R01-R48 by a fresh subagent that reads only the 13 `workflows/*.yaml` and
  `scripts/workflow_registry.py` of the h6 run worktree. The brief is h5's, word for word, except ids and paths.
  Classes do, dont, ask, vague, 12 each; forms named, goal, run, 4 each per class.
- `items.json` and `GOLD-REVIEW.md`: one independent gold review by another fresh subagent, h5's brief.
- `fields.json`: the same reviewer's field gold (settings, results, input slots), using the field-gold labellers'
  brief and `field-gold-2026-10-22/vocabulary.md`.

## Audit after sealing (declared now)

The text-only baseline (`text-baseline-2026-10-22/baseline.py`'s model), trained on all 300 earlier items, predicts
h6. Its accuracy and the ids it gets wrong (the hard subset) are recorded; the final validation reports scores on the
whole set and on the hard subset.

## Notes during authoring

- The author's reply went beyond the counts it was asked for: it also listed, for each `dont` item, the kind of
  condition the item fails (a lambda pair with one value fixed, BONOBO delta 0.4 with sparsify, per-sample OTTER, an
  unexposed PUMA setting, three DRAGON layers, signed per-sample TF activity, sample clustering from expression,
  CONDOR comparing networks, LIONESS co-expression on 2 samples, COBRA with fewer genes than samples, a LIONESS-DRAGON
  size above the cap, a COBRA matrix handed to LIONESS-PANDA).
  - I read that reply; I did not open the file. So h6 is not fully sealed from me at the level of `dont` condition
    kinds. Prompts, wording, golds of other classes and field labels remain unseen.
  - Most of these kinds already occur in the dev sets, as the census shows: lambda pairs, BONOBO delta with sparsify,
    sample minimums, unexposed settings and LIONESS-DRAGON size limits. I have not checked every kind.
  - ROUND-26 development will not use this list. Any change that targets one of these kinds must be motivated by a
    dev-set failure, cited in the change.
  - The final report states this partial exposure.
- As with h5, a hook added the run worktree's `AGENTS.md` to the author's context. The author says it did not use
  it, and `AGENTS.md` holds no test items.
- The author reports that ids were assigned after a fixed-seed shuffle, so the order of ids does not reveal class.

## Sealing check and audit (2026-10-22)

- `check_format.py`: `items.json` has 48 items, ids R01-R48, 4 per class x form, and no non-ASCII prompt.
  `fields.json` has 48 items whose ids match; its links are 40 results, 30 settings, 116 has, 3 lacks and 63
  source, and no quote is missing from its prompt.
- The reviewer changed the gold of one item (R06) and the class of none.
- `baseline_audit.py`: the text-only baseline gets **45/48** on h6 (do 12/12, dont 10/12, ask 11/12, vague 12/12).
  The hard subset is R07, R20 and R31.
- **Declared now, before any ROUND-26 development:** the final validation's primary measure is field-level linking
  on `fields.json`. The four-way score is reported only as a secondary measure, beside the 3-item hard subset,
  because the wording alone predicts the class of 45 of the 48 items.
