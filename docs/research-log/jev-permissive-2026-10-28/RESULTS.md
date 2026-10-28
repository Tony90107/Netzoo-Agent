# Jev re-read of a permissive input_network — offline results (2026-10-28): P1 FAILS, WITHDRAWN

Code: `jev_forms.permissive_network` and the fitting branch of `forms_doubts` (commit on branch `jev-permissive`, then
reverted there; main untouched). Raw: `measure-after.json` / `.log` (`measure.py`, both readers on), Jev reads cached
in `jev-forms-cache.json` (new reads under US$0.001). `replay-before.json` is the flags-on harness baseline on
df806e15 (labelled 757, right 610).

| gate | result |
|---|---|
| P1 precision (hard) | **2 of 30 control readings got the network wait: j3 R10 (f and g)**. Jev read `other` 0.82 (regulator_gene 0.06). **FAIL** |
| P2 recall | 3 of 4 misread readings, both items: h5 Q18-1, Q18-2 (gene_gene 0.75, other 0.24), j4g S22 (gene_gene 0.89). j4f S22 got no read: its row is already refused and waiting on group_membership, so the fitting branch is not reached. PASS |
| P0, P3 | not run (stop rule) |

As declared, P1 failing withdraws the change.

## Reported

- unsure (20 readings): Jev read `not_stated` on all 20; no new wait. (C21's 3 network waits come from the current
  code, not this change.)
- regulator_gene and no_network: Q06, Q13 read regulator_gene 1.0; every no_network item read `none`; S10 got no
  read (its row is refused and waits on group_membership).
- The answer read (end-to-end) was not measured, since the change is withdrawn.

## Post hoc (labelled; not a gate, not adopted)

R10: "RNA-seq …, a TF-gene motif prior and a TF-TF PPI matrix with matching IDs. I'd love to find some interesting
modules or regulators in it." The user has no network: CONDOR is credited through PANDA, which builds the
regulator-gene network from those priors. The frozen menu's `other` option ("such as protein-protein interactions")
takes the PPI prior as the network. So the closed menu does not separate "the network you already have" from "the
priors a network would be built from".

Counting only `gene_gene` (not `other`) would have kept R10 out (0.04) and S22 (0.89) and Q18 (0.75, at the margin)
in. That rule was chosen after seeing these reads, and every item here is now seen. Using it would need a declared
round on a population no one has read.
