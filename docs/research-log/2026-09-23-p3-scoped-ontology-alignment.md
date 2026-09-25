# P3 scoped ontology-alignment follow-up

Date: 2026-09-23

## Finding

The saved claims traces show the reviewer sometimes changed a patient-clustering
request to `sample_cluster_assignment` but left granularity `unknown`. The
ontology permits `unknown`, so validation accepted an outcome too incomplete
for an exact SAMBAR match. In round 4, trials 1 and 3 for
`hist-expression-then-mutation-en` took this path.

`sample_cluster_assignment` has only one legal granularity: `aggregate`. The
request-integrity rule already deterministically identifies an explicit
patient-clustering goal and requires that artifact. The claims path, however,
did not apply the artifact's single-value constraint.

## Change

Added an artifact allowlist to `restore_stated_fields` and used it in the
claims path only when `patient_clustering_goal` is true. The allowlist contains
only `sample_cluster_assignment`. When that artifact is selected, its ontology
sets granularity to `aggregate` and retires any conflicting granularity
evidence.
Other artifacts are not aligned by this rule; in particular, this does not
enable global claims artifact alignment.

## Saved-response replay

Replayed the saved round-4 claims interpreter and repair responses for
`hist-expression-then-mutation-en` trials 1 and 3 through current restoration
and deterministic registry matching. Both now end with
`sample_cluster_assignment` / `aggregate`, pass outcome validation, and match
exactly to `run_sambar`.

As a P2 guard, replayed the saved `role-tf-ss-en` initial claims response. The
terminal-goal allowlist remains empty; the explicit witness restores
`sample_specific`, leaving `regulatory_network_and_tf_activity` invalid because
its ontology requires aggregate output. Validation rejects it and matching
returns `unsupported` with no action; it is not silently aligned to an
aggregate TF-activity result.

Python compilation, Ruff on the edited modules, and `git diff --check` passed.
This was an offline replay through restoration, outcome validation, and
deterministic workflow matching, not a full CLI or live model round. The live
provider key was unavailable during the earlier validation attempt.
