# NetZoo OCR Eight-Issue Remediation Design

Date: 2026-08-01

## Objective

Fix the eight P1/P2 defects identified in the Delegation Mode review of commit
`1716e33` while preserving the existing CLI, LangGraph topology, allow-listed tool
authority, public imports, and current dirty-worktree changes.

The implementation must prevent false scientific success, unintended input or
output overwrites, autonomous cross-dataset mixing, orphaned worker processes,
truncated path parsing, and compatibility regressions.

## Scope

This change includes exactly these behaviors:

1. CONDOR succeeds only after producing valid regulator and target memberships.
2. A CONDOR prefix cannot escape its output directory or collide with an input.
3. Distinct output roles cannot resolve to the same path.
4. Autonomous multi-file discovery selects one coherent validated dataset bundle.
5. A timed-out local command terminates its complete process group.
6. Local write actions pass workflow-specific structural artifact validation.
7. Quoted paths containing spaces, Unicode, commas, or punctuation round-trip
   unchanged.
8. The historical executable entry point and import surface remain compatible.

Existing uncommitted bundle and recovery work is preserved and completed rather
than replaced. Unrelated runtime-configuration, harness-expansion, header-streaming,
documentation, deployment, dependency, and model-provider work is out of scope.

## Safety and Authority Constraints

- Python types and deterministic code remain the only execution authority.
- No new shell command surface, algorithm, dependency, external service, or LLM
  approval path is introduced.
- Subprocesses continue to receive an argument vector; `shell=True` is forbidden.
- `.env*`, secret, credential, key, `data/**`, and `outputs/**` content is not read,
  copied, staged, or sent to OCR or an external provider during implementation.
- Tests that need input or output files create fixtures only in temporary
  directories.
- Existing dirty-worktree files are preserved; only files required by these eight
  fixes may be edited or staged.

## Design

### 1. Strict CONDOR completion

`docker/run-condor` retains compatibility probes but records each failed method with
its label, exception type, and message. A normal method return is only an algorithm
step, not proof of completion.

Before a zero exit, both `reg_memb` and `tar_memb` must be non-empty pandas data
frames and must be written as `PREFIX-reg_memb.tsv` and `PREFIX-tar_memb.tsv`.
Missing, empty, malformed, or unwritable memberships produce a non-zero exit.

`scripts/netzoo_agent_core/execution.py` declares the edge list, both membership
files, and summary as expected outputs. The later artifact validator independently
rechecks both membership tables.

### 2. Safe derived output paths

CONDOR `prefix` is a basename, not a path. It must be non-empty and match a narrow
portable character set containing letters, digits, dot, underscore, and hyphen;
path separators, absolute paths, `.` and `..` components are rejected.

A shared helper resolves every final output target and verifies that it remains
inside the selected output directory and does not equal any resolved input path.
This check runs during planning and immediately before execution.

The Plan Evaluator also requires pairwise uniqueness across every populated output
role. Thus `output_file == lioness_output` is rejected even when neither path equals
an input.

### 3. Coherent autonomous dataset bundles

The existing `scripts/netzoo_agent_core/bundles.py` work becomes the single
autonomous discovery seam for PANDA, PUMA, LIONESS-PANDA, and LIONESS-PUMA.

An explicitly provided input anchors discovery to its directory. Without an anchor,
exactly one complete compatible directory bundle may be selected. Incomplete,
ambiguous, or incompatible directories produce `needs_input`. Explicit compatible
cross-directory inputs remain permitted because they are user choices rather than
autonomous mixing.

Each autonomously discovered evidence item carries a shared `bundle_id`. The Plan
Evaluator rejects discovered multi-file evidence with missing or conflicting bundle
IDs.

### 4. Process-tree timeout handling

Local commands start in their own process session on POSIX. On timeout, the command
runner sends termination to the process group, waits for bounded graceful shutdown,
then sends a forced kill if any process remains. It always waits for the direct
child before returning.

Windows keeps equivalent behavior behind a platform-specific helper where
available. The public `_run_command` return format and dry-run behavior remain
unchanged.

Timeout regression tests spawn a worker process in a temporary test harness and
verify that no descendant remains alive after `_run_command` returns.

### 5. Structural artifact validation

A focused `scripts/netzoo_agent_core/artifact_validation.py` module owns
post-execution checks. It returns a typed result containing verified paths, errors,
warnings, and compact metrics.

Common checks require each expected artifact to be a readable, non-empty regular
file. Workflow checks require:

- formatted expression: identifiers plus numeric sample values;
- co-expression: a non-empty numeric matrix;
- PANDA/PUMA text: network identity fields and numeric values;
- LIONESS text: network identity fields plus sample-specific numeric values;
- LIONESS NumPy: loadable, non-empty, finite numeric data;
- CONDOR: non-empty parseable regulator and target membership tables.

Dry runs and read-only tools skip artifact validation. A process exit of zero cannot
override a failed artifact check. Invalid artifacts yield `ToolExecutionResult`
status `failed` and cannot create a completed reusable episode.

### 6. Exact quoted-path parsing

Path parsing recognizes quoted and unquoted named assignments such as
`field="My Study/file.tsv"`, `field='My Study/file.tsv'`, and
`field is "My Study/file.tsv"`.

Quoted values preserve every interior character. Unquoted parsing retains the
legacy delimiter behavior. Parsing never evaluates escapes as shell syntax and
never expands a value into multiple command arguments.

Tests cover spaces, Unicode, commas, punctuation, POSIX paths, Windows-style paths,
and legacy unquoted inputs.

### 7. Backward compatibility

The repository restores executable mode `100755` on `scripts/netzoo_agent.py`.
The facade provides compatibility aliases for the historical
`explain_panda_puma_io` tool and `TOOLS` collection while retaining the current
modular implementation for new behavior.

Regression tests exercise direct script execution through the Python interpreter,
verify executable metadata through `stat`, and import all historical public names.

## Error Semantics

- Unsafe or colliding planned paths: Plan Evaluator `rejected`; no subprocess.
- Ambiguous or incomplete autonomous bundle: plan `needs_input`; no subprocess.
- Invalid explicit biological inputs: tool result `failed`.
- Timeout: tool result `failed` after the process group is confirmed terminated.
- Zero exit with invalid output: artifact-validation `failed`.
- Missing either CONDOR membership partition: wrapper non-zero and structured
  result `failed`.

## Testing Strategy

Every fix starts with a focused failing regression test. Tests use deterministic
fake CONDOR objects, temporary directories, short-lived local subprocesses, and
small generated artifact fixtures; no live model request or external provider is
needed.

Verification includes:

- targeted tests for all eight issue families;
- existing agent gate, stability, module-boundary, workflow-registry, and artifact
  suites;
- offline harness execution where its existing scenarios remain applicable;
- Python compilation, Ruff checks, formatting checks, and `git diff --check`;
- Docker configuration or container smoke checks only if available without exposing
  credentials.

## Success Criteria

- CONDOR cannot report success without both usable membership partitions.
- No CONDOR-derived output can leave its output directory or overwrite an input.
- No two output roles can refer to the same resolved path.
- Autonomous discovery cannot combine files from different dataset bundles.
- No timed-out worker survives the command runner.
- No empty or structurally invalid expected artifact is reported as successful.
- Quoted paths round-trip exactly and reach subprocess argument vectors unchanged.
- Existing supported CLI usage and historical facade imports continue to work.
- All pre-existing dirty-worktree edits remain preserved.
