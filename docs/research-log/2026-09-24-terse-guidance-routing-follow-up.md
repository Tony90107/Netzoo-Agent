# Terse workflow-selection routing follow-up

## Remaining failure

The saved claims traces for `per-sample miRNA-gene networks, which tool?` still
showed `request_mode=unknown`, `artifact_type=unknown`, and, in one trial, two
duplicate outcome hypotheses. That prevented the semantic matcher from
promoting the sole LIONESS-PUMA candidate to guidance and could trigger an
unneeded claims-repair call. This was a remaining narrow routing defect; it did
not establish that all semantic-routing issues were fixed.

## Changes made

- Explicit `which/what tool`, `workflow`, `method`, or `pipeline` questions now
  reconcile an otherwise unknown request mode to `guidance`. Explicit execution
  and direct-retrieval requests retain precedence.
- Claims interpretation applies the same request-mode reconciliation before its
  first match and completeness decision.
- When explicit regulator-to-target roles have exactly one artifact in the
  output ontology, restoration now applies the roles and artifact together as
  one consistency-checked change. It can replace an unsupported model-inferred
  artifact and retires its conflicting evidence. A grounded explicit artifact
  claim blocks that correction. Role combinations with several possible
  artifacts remain unresolved.
- Guidance promotion now accepts multiple hypotheses only when each is fully
  compatible with the same single workflow. An explicit operation that
  contradicts that workflow cannot be overwritten as if it were omitted.

## Offline replay

A replay of the three saved Round-6 claims proposals for the terse miRNA request
produced the expected exact route in all three trials:

- request mode: `guidance`
- inferred artifact and roles: `regulatory_network`, `mirna → gene`
- evidence validation: passed
- semantic match: exact `run_lioness_puma`
- execution: not authorized by this guidance mode

A generated boundary grid also kept the fail-closed cases intact: TF-to-gene
roles alone still leave the artifact unknown and the match ambiguous, while a
grounded explicit `multi-omic network` claim is not rewritten and fails semantic
validation against the incompatible roles. A contradictory inferred artifact
for the miRNA-to-gene request is corrected to `regulatory_network`.

`py_compile`, Ruff, and `git diff --check` passed. No live-model evaluation or
full test suite was run in this follow-up. The saved-response replay and
generated boundary grid do not measure corpus-wide routing performance.
