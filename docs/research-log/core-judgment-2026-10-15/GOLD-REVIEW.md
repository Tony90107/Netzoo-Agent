# Gold review (2026-10-15, before any live output)

Reviewer: Claude (main session), against the 13 `workflows/*.yaml` contracts only. One reviewer instead of an
independent subagent (token budget; the author was already blind). Author's original file kept as
`items-author.json`; `items.json` differs only by the fields below.

All 60 gold calls checked against the contracts; none changed. Checked in particular: sample minimums (LIONESS-*,
BONOBO ≥3; SAMBAR kmax ≤ samples), DRAGON's two layers and paired lambdas, BONOBO delta < 1/3 with sparsify, OTTER
lam ∈ [0, 1] and no sparsity penalty, GIRAFFE has no controls, COBRA needs more genes than samples, CONDOR takes a
regulator-gene edge list only, LIONESS-DRAGON's 20,000,000-value cap (C07 1.6 M ok; C45 6.2 M vs 132 M).

Additions (scoring rule fixed in `analyze.outcome` + `test_harness.py` before the round):

- C43, C44 `file_checkable: true`: run-form ask items whose deciding fact is checked by the workflow's own input
  check before anything runs (LIONESS sample count; OTTER co-expression matrix shape). A DOES answer that states the
  check settles it (`states_condition`) counts as correct. C20 and C42 are not file-checkable (PANDA does not tell
  expression from a binary mutation matrix; DRAGON does not reject 0/1 values), nor C45 (goal form, no file).
- Review notes: C09 (borderline vague — comparing and asking is right, a bare recommendation is a commit without
  asking); C17 (saying one lambda cannot be fixed while the other is estimated is DECLINES, even with the
  supply-both alternative).

Weakest items, kept: C06 (RBP vs TF regulators — the contracts type regulators as TFs/miRNAs, but a reader could
argue PANDA runs on any regulator prior), C36 and C11 (both branches are supported by different workflows: the
right call is still to ask which).
