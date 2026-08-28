# OTTER integration contract

The agent registers aggregate OTTER as `run_otter`. It calls the verified
low-level netZooPy API after strict input validation; it does not route OTTER's
PPI or co-expression projection into PANDA's motif-prior role.

## Verified package surface

The Dockerfile pins netZooPy commit
`60bcaf5ac69ac8f002db5fc6b1b10cbc101ee822`. The image reports version `0.11.0`.
The executable API is:

```text
netZooPy.otter.otter.otter(W, P, C, lam=0.035, gamma=0.335,
                           Iter=60, eta=0.00001, bexp=1)
```

The official CLI registers both `netzoopy otter` and `netzoopy otterlioness`.
The former reads expression, motif, and PPI paths and writes an OTTER result;
the latter uses the official `LionessOtter` helper for sample-specific outputs.
Neither official CLI nor the low-level `otter(W, P, C, ...)` signature accepts a
precomputed co-expression path or sample metadata. The agent therefore provides
`coexpression_file` as an explicitly labeled adapter input and keeps the
registered `run_otter` artifact aggregate. It does not claim that aggregate
`run_otter` is LIONESS-OTTER.

## Input roles and validation

The adapter materializes the arrays the API expects:

| Role | Contract | Array |
|---|---|---|
| `motif_file` | OTTER TF-by-gene seed/prior edge list, with numeric weights | `W`: TF × gene |
| `ppi_file` | TF-TF edge list; exact TF ID set from `motif_file` | `P`: TF × TF |
| `expression_file` | gene-by-sample matrix; unique gene IDs and at least two samples | computes `C`: gene × gene |
| `coexpression_file` | labeled symmetric square gene-by-gene matrix | `C`: gene × gene |

All three layers must agree exactly. Gene order is preserved and is never
implicitly intersected or reordered. PPI IDs must equal the regulatory TF layer;
TF and gene partitions must be disjoint. NAs, non-finite values, duplicate IDs,
empty rows/columns, duplicate pairs, non-numeric values, and invalid shapes are
rejected before import/call. Expression and precomputed co-expression can both
be supplied for an explicit exact-order cross-check.

The official OTTER reader is more permissive: it symmetrizes/binarizes PPI and
uses simple reading/merging behavior. Its CLI warning specifically calls out
NAs and non-intersection W/P/C inputs. The agent makes those cases explicit and
fails closed.

## Parameters and output

`lam` is constrained to `[0, 1]` and weights co-expression versus PPI as
`(lam, 1-lam)`. `gamma` is non-negative regularization. `iterations`, `eta`, and
`bexp` are positive optimization controls. `computing=gpu` is rejected by the
current agent runtime because the installed execution path is CPU-only; this is
an agent runtime gate, not a claim that the official package has no GPU code.
The verified API has no independent sparsity penalty or threshold: `gamma` is an
L2-style regularizer, not a sparsity parameter. The adapter does not invent a
`sparsity` argument. The official CLI's `mode_process` is also not exposed as a
silent intersection/union switch; this adapter always requires exact identifiers
and order.

The output is either:

- a labeled TF-by-gene matrix (`tf` rows, gene columns), or
- a complete `source,target,weight` edge list.

The weight is the optimized OTTER W score. Both forms are aggregate TF-to-gene
regulatory artifacts, with disjoint regulator/target partitions. Only the
validated edge-list form can hand off to CONDOR; a matrix requires explicit
conversion and revalidation.

COBRA is a declared predecessor for batch/confounder correction. Its adjusted
co-expression artifact may be passed to OTTER only after this adapter confirms
the exact gene identifiers, order, shape, symmetry, and finite values. OTTER
does not automatically correct batch effects.

## Lifecycle and non-compositions

Planning displays the exact source choice, orientation, shapes, parameters, and
output contract. Dry-run does not import or execute netZooPy or write an output.
Execution remains behind the common `/execute` confirmation gate and validates
the artifact after writing it. The registry exposes OTTER → CONDOR only through
the validated bipartite edge-list contract. PANDA/PUMA/LIONESS/DRAGON inputs are
not mixed with OTTER inputs, and the agent does not invent a LIONESS-OTTER action.
