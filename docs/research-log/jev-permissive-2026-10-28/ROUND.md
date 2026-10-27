# Jev re-read of a permissive input_network (2026-10-28) — declared before code

User decision (2026-10-28): when a row is credited while its typed `input_network` is `none` or `not_stated`, Jev
re-reads the network kind on the same closed menu. Declare gates, then measure offline, then ask before anything live.
Branch `jev-permissive` (from main df806e15, worktree `.worktrees/netzoo-j4`); not merged.

## Problem (j4 RESULTS-J4.md, C1)

j4 S22: "a DRAGON partial-correlation network linking plasma metabolites and proteins … detect communities of
metabolites and proteins in it". gpt-4o-mini typed `input_network=none` and credited `condor.communities`. CONDOR
takes only a regulator-to-gene network, but `none` (and `not_stated`) never rule an entry out, so the row was
available and the call was DO (a false accept; arm F's reading of the same item typed the network and refused). The
forms read (jev-forms) only re-reads a typed value that refuses, so a misread in the permissive direction is never
read.

S10 is not in scope: the user has protein and metabolite measurements and no network, so `not_stated`/`none` is right
there; its blocker is the data kind, which the data-first step handles. It is in the population as a control.

## Change (only with `NETZOO_JEV_FORMS=on`; same flag, question, threshold and cache as the forms read)

In `jev_forms.forms_doubts`, on a credited row that fits (the branch that today returns unchanged):
- When the typed `input_network` is `none`, `not_stated` or missing, and some credited entry takes one network kind
  (today: the three CONDOR entries, `regulator_gene`), Jev reads the frozen `input_network` question once.
- The options under which the permissive value is what the user said are the kinds the credited entries take plus
  `none` and `not_stated`. Doubted when Jev puts at most THRESHOLD (0.3) on those, i.e. at least 0.7 on network kinds
  the credited entries do not take (`gene_gene`, `other`).
- A doubted row gets a wait on `input_network` (the existing needs_fact dimension: "Does your network link regulators
  (such as TFs) to their target genes, or genes to genes?"), unless it already waits on it. The answer binds as any
  form answer does (code, or the jev-answers read).
- Nothing else: the typed value is not changed, Jev makes no DO or DECLINE, picks no workflow and writes no reason.

## Population (`population.json`, from `scan.py`) and labels

Every recorded reading under docs/research-log with a result ask credited to a CONDOR entry and typed `input_network`
`none`, `not_stated` or missing: 54 readings, 18 items. One labeller (me), from each item's request:
- misread (4 readings, 2 items): j4 S22 (f, g); h5 Q18 (-1, -2), a DRAGON microbe-metabolite edge list.
- regulator_gene (6 readings, 4 items): Q06, Q13 (PANDA output), M45 (a TF-to-gene network), R10 (a TF-gene motif
  prior and TF-TF PPI, from which PANDA builds the network). The permissive read is right.
- no_network (24 readings, 7 items): C18, H27, J46, L48, Q41, R09 (CONDOR straight from expression), S10. Right.
- unsure (20 readings, 5 items): C21, H13, L22, M07, Q30, where the user says they do not know whether the file is
  TF-to-gene or gene-gene. `not_stated` is right; a network question there would be the item's own gold (ASK), so it
  is reported, not gated.

## Measurement

Each population reading's check is rebuilt from its recorded proposal (as `jev-forms-r2/measure.py`), both readers
on, current code vs changed code: each row's status, wait and the call's needs. Calls: the harness replay through
`jev-forms/adapter.py`, flags on, current code (`replay-before.json`) vs changed code.

## Gates

- P0, off = no change: flags off, harness replay 0 of 1388 changed vs `replay-frozen.json`; the test suite (clean
  environment) has no new failures beyond the known env-dependent one.
- P1, precision (hard): 0 of the 30 regulator_gene and no_network readings get the network wait.
- P2, recall: >= 3 of the 4 misread readings get the network wait, covering both items.
- P3, shape and scope: flags-on harness replay, changed vs current code: every changed call is a population reading,
  the change is to ASK `needs_fact` with the input_network question, no call becomes DO or DECLINE, and no reason text
  changes.
- Reported, not gated: the unsure readings; Jev's read on each item; for the misread items, Jev's read of the item's
  own natural description given as the answer (does it bind `gene_gene`?), since the end-to-end decline depends on it.

Stop rule: if P1 fails, the change is withdrawn as declared.
