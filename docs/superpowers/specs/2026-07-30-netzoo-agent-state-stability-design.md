# NetZoo Agent State Stability Design

Date: 2026-07-30

## Objective

Harden the NetZoo agent's planning, continuation, execution, recovery, and result
evaluation semantics without replacing the existing CLI or LangGraph workflow.

The agent must preserve user-selected inputs exactly, refuse to guess across
unrelated datasets, distinguish historical failures from the final recovered
outcome, and verify that produced artifacts are usable before reporting success.

## Scope

This change includes:

- attempt-aware recovery results and final-status rendering;
- coherent bundle-based autonomous input discovery;
- post-execution artifact validation for every local write action;
- typed clarification, preference, recommendation, and overwrite continuations;
- collision-safe default output names and explicit overwrite confirmation;
- backward-compatible defaults for newly persisted model fields;
- focused regression and integration tests for each behavior.

This change does not include:

- deployment, Docker packaging, dependency locking, or secret management;
- new NetZoo algorithms or new tool authority;
- an LLM-based execution approver;
- removal of the `scripts/netzoo_agent.py` compatibility facade;
- a complete rewrite of the LangGraph topology;
- biological quality thresholds that have not been approved as project policy.

## Design Principles

1. Python types and deterministic rules own execution authority.
2. Markdown and natural-language text are presentation formats, never control
   protocols.
3. Agent uncertainty blocks execution as `needs_input`; validated incompatibility
   becomes `failed`.
4. Historical attempts remain auditable but cannot override the terminal outcome of
   a successful recovery.
5. File existence is necessary but not sufficient evidence of successful analysis.

## Attempt-Aware Recovery

`ToolExecutionResult` gains backward-compatible attempt metadata:

- `attempt_id`, defaulting to `0`;
- `superseded`, defaulting to `false`;
- `superseded_reason`, defaulting to `null`.

The graph assigns the current recovery count as the attempt ID. Before executing a
recovery plan, the failed result that triggered the recovery is marked superseded
with an explicit reason. The original result and log remain in the audit trail.

All user-facing rendering, next-turn selection, episode status, validation status,
error signatures, and reusable-memory decisions operate on effective results:
non-superseded results plus the terminal `EvaluationResult`. A completed terminal
evaluation therefore renders `COMPLETED` even when an earlier attempt failed. A
failed terminal evaluation still renders `FAILED`.

## Coherent Dataset Bundle Discovery

Autonomous discovery selects input bundles, not individual files.

For PANDA, PUMA, and their LIONESS variants, a candidate bundle must place the
expression, prior, PPI, and optional miRNA list in one dataset directory and pass
the existing format and identifier compatibility checks. A LIONESS candidate must
also satisfy its sample-count requirement. CONDOR and co-expression retain their
single-primary-input semantics.

Discovery behavior is:

1. Explicitly provided inputs are always preserved.
2. If an explicit input anchors the task, autonomous discovery may fill missing
   fields only from that input's dataset directory.
3. Without an anchor, the agent may choose a bundle only when exactly one complete,
   validated candidate is unambiguous.
4. Multiple valid bundles, incomplete bundles, or incompatible bundles produce
   `needs_input`; no analysis tool executes.
5. Users may explicitly provide compatible files from different directories. Those
   files are validated normally and are not rejected merely because their parents
   differ.
6. Explicitly selected files that fail format or identifier validation produce a
   normal validation `failed` result.

`InputEvidence` records a `bundle_id` for autonomous bundle selections. Inputs
reused under the confirmed `reuse_last_inputs` preference use a distinct `reused`
evidence status rather than pretending to be workspace discovery. The Plan
Evaluator requires all autonomously discovered multi-file inputs to share one
bundle ID and rejects a manually mutated plan that mixes bundles.

## Artifact Validation

Local write actions receive deterministic post-execution validation after the
process exits and before `ToolExecutionResult(status="success")` is created.

The validator returns a typed result containing:

- overall pass or fail;
- verified artifact paths;
- errors and warnings;
- compact structural metrics.

Common checks require every expected artifact to be a readable regular file or the
expected output directory member, to be non-empty, and to contain at least one
usable data record.

Workflow checks are deliberately structural:

- formatted expression output must contain identifiers and numeric sample values;
- co-expression output must contain a non-empty numeric matrix;
- PANDA/PUMA text output must contain regulator/gene fields and numeric network
  values;
- NumPy output must load successfully, be non-empty, and contain finite numeric
  values;
- LIONESS text output must contain network identity columns and sample-specific
  numeric values consistent with the input sample count;
- CONDOR must produce non-empty edge and summary files for the selected prefix.

These checks do not claim biological validity. Species, cohort, identifier
namespace, and acceptable coverage thresholds remain domain-policy concerns.

An empty, unreadable, malformed, or incomplete artifact converts the result to
`failed`, prevents a completed episode from being recorded, and produces an
actionable error. Dry runs do not perform artifact validation.

## Typed Continuations

The agent no longer encodes control state into user-looking strings such as
`PREVIOUS_ACTION=...` or `SELECTED_FIELD=...`.

A backward-compatible `ContinuationRequest` carries:

- continuation kind: clarification, preference confirmation, recommendation
  acceptance, or overwrite confirmation;
- the original authorized user task;
- the pending workflow plan or recommended action;
- exact field assignments;
- confirmation decisions.

`AgentState` accepts this typed payload. When present, classification deterministically
resumes the authorized action without calling the Router. Planning applies trusted
assignments directly and preserves the original decision fields. Plan evaluation
uses typed authorization metadata rather than searching user text for hidden
markers.

The user's visible reply remains in conversation history for audit, but is not
reparsed as a command protocol. Paths containing spaces, commas, Unicode, or shell
metacharacters remain plain path values and must round-trip unchanged.

Preference confirmation resumes the existing task with all original inputs after
the preference is accepted or declined. Recommendation acceptance creates a typed
continuation for the recommended workflow and then asks only for genuinely missing
inputs.

Older persisted sessions that contain the legacy text markers remain readable, but
new CLI interactions do not generate them.

## Output Collision Handling

Default output paths are reversible:

- if a generated default path does not exist, it is used;
- if it exists, the Planner selects the first available numbered sibling;
- paired LIONESS outputs use a shared run suffix so they remain associated.

Explicit output paths are never silently renamed. If an explicit output already
exists, the plan enters `needs_confirmation` with confirmation kind `overwrite`.
Approval is stored in typed continuation state and checked by the Plan Evaluator.
Declining returns the output field to `needs_input`.

The Executor performs a final collision check immediately before launch. An
unapproved existing explicit output fails closed even if the file appeared after
planning.

## Error and User-Interaction Semantics

- Autonomous uncertainty: `needs_input`.
- Explicit incompatible inputs: validation `failed`.
- Invalid or empty output: artifact-validation `failed`.
- Recoverable first attempt followed by successful repair: terminal `completed`,
  with the first failure retained as superseded audit history.
- Rejected overwrite: `needs_input` for a replacement output.
- Invalid continuation payload: Plan Evaluator rejection; no tool execution.
- Router or response-model failure: deterministic capability and required-input
  guidance is rendered from the workflow registry when recommendations exist.

## Compatibility

Existing public tool names, command arguments, workflow YAML, dry-run behavior, and
legacy facade imports remain unchanged. New persisted fields have defaults so
existing sessions and episodes validate without migration.

The Plan Evaluator remains deterministic Python. An optional future critic model may
explain biological risks, but it cannot approve execution or mutate the plan.

## Testing

Tests must prove:

1. a successful recovered attempt renders `COMPLETED`, selects a completed next
   prompt, and records completed memory while retaining superseded history;
2. a terminally failed recovery still renders and records `FAILED`;
3. independently discoverable files in different directories do not form a ready
   plan;
4. one complete validated bundle may be selected atomically;
5. explicitly supplied compatible cross-directory inputs remain allowed;
6. a plan with conflicting autonomous bundle IDs is rejected;
7. zero-byte, unreadable, malformed, or incomplete outputs become failed results;
8. valid PANDA, PUMA, LIONESS, formatting, co-expression, and CONDOR fixtures pass
   artifact validation;
9. preference confirmation preserves every original input;
10. clarification paths containing spaces and Unicode round-trip unchanged;
11. recommendation acceptance no longer depends on text markers;
12. existing default outputs receive collision-free names;
13. explicit existing outputs require typed approval and a final pre-launch check;
14. response-model failure still returns deterministic tool and input guidance;
15. legacy persisted models and compatibility-facade behavior continue to work.

Verification consists of targeted red-green tests, the complete Python test suite,
Ruff, formatting checks, Python compilation, and container CLI smoke tests that do
not require a live OpenRouter request.

## Success Criteria

- No superseded failure can make a successfully recovered workflow appear failed.
- No multi-file workflow can autonomously combine files from different dataset
  bundles.
- No empty or structurally invalid expected output can be reported as successful.
- No new continuation depends on parsing hidden markers from natural-language text.
- No existing output is overwritten without deterministic renaming or explicit
  typed approval.
- Every ready initial or continued plan passes the same code-enforced Plan Evaluator
  before Executor access.
- Existing supported CLI workflows and legacy imports remain functional.
