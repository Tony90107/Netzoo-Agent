# Input selection priority

Routing, input-role mapping, parameter echoes and the Planner share
`interpretation.input_bindings.request_input_bindings`. It covers every
registered file input role, including optional co-expression inputs, COBRA's
design matrix and DRAGON's two omics layers.

- Explicit role-to-file bindings outrank filename hints. Parenthesized role
  descriptions also bind neutral filenames, such as `prior regulatory table
  (data/study/a.tsv)`.
- A selected file cannot establish another input role from its filename.
  Output locations cannot establish input roles or input discovery directories.
- Content mapping fills open roles. Workspace discovery and remembered inputs
  cannot replace request-selected files, even when they are missing or invalid.
  Existing preflight reports those errors; a validated rearrangement of the same
  files can still be offered explicitly for confirmation.
- Any selected input can anchor discovery. Bare filenames under an explicit
  same-folder instruction resolve against one input directory. Multiple possible
  directories require clarification. Inferred locations remain discovered
  evidence and require confirmation under the existing execution gate.
- Folder-only requests retain their ambiguity when multiple priors are present.
  A selected mixed TF/miRNA prior is not made ambiguous by an unused TF-only
  prior beside it. Its validated contents support the matching PUMA or
  LIONESS-PUMA recommendation without granting execution authority.

`tests/test_request_input_binding_priority.py` derives its workflow/role cases
from the registry. `tests/test_input_inspection.py` covers mixed priors, unrelated
priors, missing and invalid selected priors, and aggregate/sample-specific
recommendations. These are deterministic regression checks, not a guarantee of
LLM accuracy for arbitrary scientific requests.

## Verification

- Focused input/routing/planning checks: 521 passed.
- Final suite: 2495 passed, 36 skipped, 2 deselected.
- The two deselections were independently reproduced on an isolated copy of
  the original committed code: descendant-process timeout cleanup and
  `test_explicit_panda_run_survives_semantic_validation_failure`'s call count.
- The original prompt was replayed offline at the input-inspection boundary:
  it recommended `run_puma` with `prior-puma.tsv` and `mirna.txt`, preserving
  the existing execution gate. No live LLM calls or scientific analysis ran.
- A full persistent graph refresh was attempted, but the CBM worker refused
  to start because another pre-coordination or unverified generation is active.
  Source checks and executable regressions were used instead of the stale graph.
