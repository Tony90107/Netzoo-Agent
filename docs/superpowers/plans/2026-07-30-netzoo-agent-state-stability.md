# NetZoo Agent State Stability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make NetZoo planning and execution preserve typed state, select only coherent autonomous datasets, validate output contents, and report recovered outcomes correctly.

**Architecture:** Extend the existing Pydantic contracts with backward-compatible state metadata, then add three focused deterministic seams: effective-result selection, coherent bundle discovery, and artifact validation. Keep the current LangGraph and CLI, but carry continuation data through `AgentState` instead of encoding control markers in natural-language strings.

**Tech Stack:** Python 3.10+, Pydantic, LangGraph, LangChain tools, pandas, NumPy, unittest/pytest, Ruff.

**Companion plan:** Strict CONDOR completion, runtime isolation, streaming header
insertion, and cross-boundary harness coverage are implemented by
`docs/superpowers/plans/2026-07-31-netzoo-execution-boundary-stability.md`.

## Global Constraints

- Python types and deterministic rules own execution authority.
- Markdown and natural-language text are presentation formats, never control protocols.
- Agent uncertainty blocks execution as `needs_input`; validated incompatibility becomes `failed`.
- Historical attempts remain auditable but cannot override the terminal outcome of a successful recovery.
- File existence is necessary but not sufficient evidence of successful analysis.
- Existing public tool names, command arguments, workflow YAML, dry-run behavior, and legacy facade imports remain compatible.
- New persisted model fields must have defaults so existing sessions and episodes remain readable.
- Do not add a new NetZoo algorithm, local executable, shell authority, or LLM execution approver.
- Do not stage unrelated dirty-worktree files. Review `git diff --cached --name-only` before every commit.

---

## File Structure

- `scripts/netzoo_agent_core/contracts.py`: persisted and graph-facing typed contracts.
- `scripts/netzoo_agent_core/outcomes.py`: effective-attempt and terminal-outcome helpers.
- `scripts/netzoo_agent_core/bundles.py`: coherent autonomous dataset bundle discovery.
- `scripts/netzoo_agent_core/artifact_validation.py`: post-execution structural output checks.
- `scripts/netzoo_agent_core/planning.py`: evidence construction, bundle application, output collision planning.
- `scripts/netzoo_agent_core/evaluation.py`: plan rules, effective-result rendering, recovery mutation.
- `scripts/netzoo_agent_core/routing.py`: tool-result normalization and artifact-validator integration.
- `scripts/netzoo_agent_core/interaction.py`: typed continuation creation and outcome-aware prompts.
- `scripts/netzoo_agent_core/graph.py`: continuation routing, attempt assignment, recovery supersession.
- `scripts/netzoo_agent_core/cli.py`: retain pending plans and submit typed continuations.
- `scripts/netzoo_agent_core/execution.py`: final overwrite gate passed into command execution.
- `scripts/netzoo_agent_core/command.py`: pre-launch collision rejection.
- `scripts/netzoo_agent_core/memory.py`: effective-result episode normalization.
- `scripts/workflow_registry.py`: optional overwrite executor argument mapping.
- `scripts/netzoo_agent.py`: compatibility re-exports for new public test seams.
- `tests/test_agent_gate.py`: unit and graph integration regression coverage.
- `tests/test_agent_artifacts.py`: focused artifact-structure validation.
- `AGENT_USAGE.md`: user-visible clarification, overwrite, and recovery semantics.

### Task 1: Add backward-compatible outcome and continuation contracts

**Files:**
- Modify: `scripts/netzoo_agent_core/contracts.py:493-618`
- Create: `scripts/netzoo_agent_core/outcomes.py`
- Modify: `scripts/netzoo_agent_core/__init__.py`
- Modify: `scripts/netzoo_agent.py:35-110`
- Test: `tests/test_agent_gate.py`

**Interfaces:**
- Produces: `ContinuationRequest`, `ToolExecutionResult.attempt_id`, `ToolExecutionResult.superseded`, `ToolExecutionResult.superseded_reason`.
- Produces: `effective_results(results) -> list[ToolExecutionResult]`.
- Produces: `terminal_failed(results, evaluation) -> bool`.
- Consumes: existing `WorkflowPlan`, `TaskDecision`, and `EvaluationResult`.

- [ ] **Step 1: Write failing backward-compatibility and effective-result tests**

```python
def test_legacy_tool_result_defaults_to_effective_attempt_zero(self):
    result = agent.ToolExecutionResult(
        action="run_puma",
        status="failed",
        summary="old payload",
    )
    self.assertEqual(result.attempt_id, 0)
    self.assertFalse(result.superseded)
    self.assertIsNone(result.superseded_reason)


def test_effective_results_excludes_superseded_failure(self):
    results = [
        agent.ToolExecutionResult(
            action="run_puma",
            status="failed",
            summary="header rejected",
            superseded=True,
            superseded_reason="recovered by attempt 1",
        ),
        agent.ToolExecutionResult(
            action="run_puma",
            status="success",
            summary="recovered",
            attempt_id=1,
        ),
    ]
    effective = agent.effective_results(results)
    self.assertEqual([item.status for item in effective], ["success"])
```

- [ ] **Step 2: Run the focused tests and verify missing fields/helpers fail**

Run:

```bash
python -m pytest tests/test_agent_gate.py -k "legacy_tool_result or effective_results" -q
```

Expected: FAIL because the attempt metadata and `effective_results` do not exist.

- [ ] **Step 3: Add typed fields and helpers**

Insert these fields into the existing models without changing the other declared
fields:

```python
attempt_id: int = Field(default=0, ge=0)
superseded: bool = False
superseded_reason: str | None = None


class ContinuationRequest(BaseModel):
    kind: Literal[
        "clarification",
        "preference_confirmation",
        "recommendation_acceptance",
        "overwrite_confirmation",
    ]
    source_task: str
    action: str
    pending_plan: dict | None = None
    assignments: dict[str, str] = Field(default_factory=dict)
    cleared_fields: list[str] = Field(default_factory=list)
    approved: bool | None = None
```

Add `continuation: NotRequired[dict]` to `AgentState`.

Create `outcomes.py`:

```python
def effective_results(
    results: list[ToolExecutionResult | dict],
) -> list[ToolExecutionResult]:
    models = [ToolExecutionResult.model_validate(item) for item in results]
    return [item for item in models if not item.superseded]


def terminal_failed(
    results: list[ToolExecutionResult | dict],
    evaluation: EvaluationResult | dict | None,
) -> bool:
    if evaluation is not None:
        terminal = EvaluationResult.model_validate(evaluation)
        if terminal.status == "completed":
            return False
        if terminal.status == "failed":
            return True
    return any(item.status == "failed" for item in effective_results(results))
```

Export the new contracts and helpers through `netzoo_agent_core.__init__` and the
legacy facade.

- [ ] **Step 4: Run the focused tests**

Run:

```bash
python -m pytest tests/test_agent_gate.py -k "legacy_tool_result or effective_results" -q
```

Expected: PASS.

- [ ] **Step 5: Commit only Task 1 files**

```bash
git add scripts/netzoo_agent_core/contracts.py scripts/netzoo_agent_core/outcomes.py scripts/netzoo_agent_core/__init__.py scripts/netzoo_agent.py tests/test_agent_gate.py
git diff --cached --check
git commit -m "feat: add typed agent outcome contracts"
```

### Task 2: Make recovery terminal status attempt-aware

**Files:**
- Modify: `scripts/netzoo_agent_core/graph.py:343-418`
- Modify: `scripts/netzoo_agent_core/evaluation.py:525-765`
- Modify: `scripts/netzoo_agent_core/interaction.py:363-465`
- Modify: `scripts/netzoo_agent_core/memory.py:305-383,650-714`
- Test: `tests/test_agent_gate.py`

**Interfaces:**
- Consumes: `effective_results()` and `terminal_failed()` from Task 1.
- Produces: `supersede_triggering_failure(results, next_attempt)`.
- Guarantees: a completed recovery renders and records completed even when audit history contains an earlier failed attempt.

- [ ] **Step 1: Write failing recovery-rendering, prompt, and memory tests**

```python
def test_successful_recovery_ignores_superseded_failure_in_terminal_status(self):
    results = [
        agent.ToolExecutionResult(
            action="run_puma",
            status="failed",
            summary="header rejected",
            superseded=True,
            superseded_reason="recovery attempt 1",
        ),
        agent.ToolExecutionResult(
            action="format_expression",
            status="success",
            summary="formatted",
            attempt_id=1,
        ),
        agent.ToolExecutionResult(
            action="run_puma",
            status="success",
            summary="completed",
            attempt_id=1,
            artifacts=["outputs/puma.tsv"],
        ),
    ]
    evaluation = agent.EvaluationResult(status="completed", reason="recovered")
    rendered = agent.render_compact_execution_response(self.ready_plan(), results, evaluation)
    self.assertIn("COMPLETED", rendered)
    self.assertNotIn("workflow stopped", rendered.casefold())


def test_successful_recovery_next_prompt_is_completed(self):
    state = self.completed_recovery_state()
    self.assertEqual(agent.build_next_turn_prompt(state).kind, "completed")
```

Add an episode test asserting `status == "completed"` and
`error_signature is None` for the same effective results.

- [ ] **Step 2: Run recovery tests and verify they fail**

Run:

```bash
python -m pytest tests/test_agent_gate.py -k "successful_recovery" -q
```

Expected: FAIL with `FAILED`, `failed` prompt, or retained error signature.

- [ ] **Step 3: Mark the triggering result superseded during recovery**

Add:

```python
def supersede_triggering_failure(
    results: list[ToolExecutionResult | dict],
    next_attempt: int,
) -> list[dict]:
    models = [ToolExecutionResult.model_validate(item) for item in results]
    for item in reversed(models):
        if item.status == "failed" and not item.superseded:
            item.superseded = True
            item.superseded_reason = f"superseded by recovery attempt {next_attempt}"
            break
    return [item.model_dump() for item in models]
```

In `graph.execute_tool`, pass `attempt_id=state.get("replan_count", 0)` into result
structuring. In `graph.recover`, return the superseded `tool_results` together with
the recovered plan.

- [ ] **Step 4: Use effective results consistently**

Update compact rendering, verbose rendering, `build_next_turn_prompt`,
`normalize_episode_memory`, and `EpisodeStore.record` to:

```python
effective = effective_results(results)
has_failure = terminal_failed(effective, evaluation)
has_dry_run = any(item.status == "dry_run" for item in effective)
```

Only effective errors contribute to `error_signature`; audit logs and persisted
`tool_results` keep all attempts.

- [ ] **Step 5: Run focused and full tests**

Run:

```bash
python -m pytest tests/test_agent_gate.py -k "recovery or render or next_prompt or episode" -q
python -m pytest -q
```

Expected: all selected tests and the full suite pass.

- [ ] **Step 6: Commit Task 2**

```bash
git add scripts/netzoo_agent_core/graph.py scripts/netzoo_agent_core/evaluation.py scripts/netzoo_agent_core/interaction.py scripts/netzoo_agent_core/memory.py tests/test_agent_gate.py
git diff --cached --check
git commit -m "fix: report recovered workflows by terminal attempt"
```

### Task 3: Replace per-field guessing with coherent bundle discovery

**Files:**
- Create: `scripts/netzoo_agent_core/bundles.py`
- Modify: `scripts/netzoo_agent_core/contracts.py:493-512`
- Modify: `scripts/netzoo_agent_core/planning.py:193-369`
- Modify: `scripts/netzoo_agent_core/evaluation.py:60-142,265-330`
- Modify: `scripts/netzoo_agent_core/interpretation.py:915-958`
- Modify: `scripts/netzoo_agent_core/__init__.py`
- Modify: `scripts/netzoo_agent.py`
- Test: `tests/test_agent_gate.py`

**Interfaces:**
- Produces: `BundleDiscovery(values, bundle_id, reason, candidates_by_field)`.
- Produces: `discover_coherent_bundle(action, nearby, explicit_inputs) -> BundleDiscovery | None`.
- Produces: `candidate_dataset_directories(action, nearby) -> list[Path]`.
- Produces: `validate_directory_bundle(action, directory, explicit_inputs) -> BundleDiscovery | None`.
- Consumes: existing bounded file discovery and existing PANDA/PUMA/CONDOR validators.
- Guarantees: auto-discovered multi-file inputs have one validated `bundle_id`.

- [ ] **Step 1: Write failing cross-directory and coherent-bundle tests**

```python
def test_cross_directory_candidates_do_not_autofill_a_multifile_workflow(self):
    self.write_dataset_file("data/a/expression.tsv", EXPRESSION)
    self.write_dataset_file("data/b/motif.tsv", MOTIF)
    self.write_dataset_file("data/c/ppi.tsv", PPI)
    self.write_dataset_file("data/d/mirna.txt", MIRNA)
    plan = agent.build_workflow_plan(self.puma_decision(), "run PUMA analysis")
    self.assertEqual(plan.status, "needs_input")
    self.assertTrue(plan.missing_inputs)


def test_one_complete_validated_directory_is_selected_as_one_bundle(self):
    self.write_complete_puma_bundle("data/study-a")
    plan = agent.build_workflow_plan(self.puma_decision(), "run PUMA analysis")
    self.assertEqual(plan.status, "ready")
    bundle_ids = {
        item.bundle_id
        for item in plan.evidence
        if item.status == "discovered"
    }
    self.assertEqual(len(bundle_ids), 1)
    self.assertNotIn(None, bundle_ids)


def test_explicit_compatible_cross_directory_inputs_are_allowed(self):
    decision, task = self.explicit_cross_directory_puma_request()
    plan = agent.build_workflow_plan(decision, task)
    self.assertEqual(plan.status, "ready")
```

Add a Plan Evaluator tampering test with two different discovered `bundle_id`
values and assert `status == "rejected"`.

- [ ] **Step 2: Run the bundle tests and verify the old planner fails them**

Run:

```bash
python -m pytest tests/test_agent_gate.py -k "bundle or cross_directory" -q
```

Expected: cross-directory auto-discovery incorrectly returns `ready`, or
`bundle_id` is missing.

- [ ] **Step 3: Add bundle evidence contracts**

Extend `InputEvidence.status` with `"reused"` and add:

```python
bundle_id: str | None = None
```

Update episode reuse to emit `status="reused"` and a source reason naming the
successful episode.

- [ ] **Step 4: Implement atomic bundle discovery**

Create:

```python
@dataclass(frozen=True, slots=True)
class BundleDiscovery:
    values: dict[str, str]
    bundle_id: str
    reason: str
    candidates_by_field: dict[str, list[str]]


def candidate_dataset_directories(action: str, nearby: Path) -> list[Path]:
    directories: set[Path] = set()
    for field_name in REQUIRED_INPUTS[action]:
        if field_name in OUTPUT_ROLE_FIELDS:
            continue
        keywords = _candidate_keywords(action, field_name)
        for candidate in _find_candidate_files(keywords, nearby):
            directories.add(_resolve_user_path(candidate).parent)
    return sorted(directories, key=str)


def validate_directory_bundle(
    action: str,
    directory: Path,
    explicit_inputs: dict[str, str],
) -> BundleDiscovery | None:
    values = resolve_required_files_in_one_directory(
        action,
        directory,
        explicit_inputs,
    )
    if values is None or not bundle_inputs_validate(action, values):
        return None
    return BundleDiscovery(
        values=values,
        bundle_id=f"directory:{directory.resolve()}",
        reason=f"Selected one complete validated dataset bundle from {directory}.",
        candidates_by_field={
            field_name: [value] for field_name, value in values.items()
        },
    )


def discover_coherent_bundle(
    action: str,
    nearby: Path,
    explicit_inputs: dict[str, str],
) -> BundleDiscovery | None:
    anchor_parents = {
        _resolve_user_path(value).parent for value in explicit_inputs.values()
    }
    if len(anchor_parents) > 1:
        return None
    roots = list(anchor_parents) or candidate_dataset_directories(action, nearby)
    valid = [
        bundle
        for directory in roots
        if (bundle := validate_directory_bundle(action, directory, explicit_inputs))
    ]
    return valid[0] if len(valid) == 1 else None
```

`validate_directory_bundle` must use exact required fields, choose files only
inside one directory, and run the existing compatibility validator before
returning a bundle.

Implement `resolve_required_files_in_one_directory` by mapping every required input
field through `_candidate_keywords` and `_best_named_file`, while preserving any
explicit value. Implement `bundle_inputs_validate` by dispatching PANDA/PUMA
families to `_inspect_panda_inputs_impl`, CONDOR to
`_inspect_condor_inputs_impl`, and LIONESS sample-count checks to
`_expression_sample_count`. Both helpers remain private to `bundles.py`.

- [ ] **Step 5: Apply one bundle in the Planner**

Call `discover_coherent_bundle` once before the evidence loop. Apply all returned
values atomically with identical `bundle_id`. Remove per-field autonomous calls to
`_find_candidate_files` for multi-file run actions. If no bundle is returned, keep
candidate lists for the wizard but mark unresolved fields `missing`.

Single-input CONDOR and co-expression discovery may retain bounded individual
selection.

- [ ] **Step 6: Enforce bundle provenance in the Plan Evaluator**

Add a required rubric item:

```python
discovered = [
    item for item in plan.evidence
    if item.status in {"discovered", "demo_bundle"}
    and item.field in INPUT_ROLE_FIELDS
]
bundle_ids = {item.bundle_id for item in discovered}
bundle_ok = not discovered or (
    None not in bundle_ids and len(bundle_ids) == 1
)
```

Apply this constraint only to autonomous multi-file selection. `provided`,
`selected`, and `reused` evidence may legitimately reference different
directories.

- [ ] **Step 7: Run targeted and full tests**

Run:

```bash
python -m pytest tests/test_agent_gate.py -k "bundle or discovery or evidence" -q
python -m pytest -q
```

Expected: all tests pass and the separate-directory probe produces
`status="needs_input"`.

- [ ] **Step 8: Commit Task 3**

```bash
git add scripts/netzoo_agent_core/bundles.py scripts/netzoo_agent_core/contracts.py scripts/netzoo_agent_core/planning.py scripts/netzoo_agent_core/evaluation.py scripts/netzoo_agent_core/interpretation.py scripts/netzoo_agent_core/__init__.py scripts/netzoo_agent.py tests/test_agent_gate.py
git diff --cached --check
git commit -m "fix: discover NetZoo inputs as coherent bundles"
```

### Task 4: Validate artifact contents before reporting success

**Files:**
- Create: `scripts/netzoo_agent_core/artifact_validation.py`
- Modify: `scripts/netzoo_agent_core/routing.py:789-872`
- Modify: `scripts/netzoo_agent_core/__init__.py`
- Modify: `scripts/netzoo_agent.py`
- Create: `tests/test_agent_artifacts.py`
- Test: `tests/test_agent_gate.py`

**Interfaces:**
- Produces: `ArtifactValidationResult`.
- Produces: `validate_output_artifacts(action, decision) -> ArtifactValidationResult`.
- Consumes: `TaskDecision`, `_resolve_user_path`, expression sample-count logic.
- Guarantees: executed local write actions cannot be `success` with empty or structurally invalid expected artifacts.

- [ ] **Step 1: Write failing empty and malformed artifact tests**

```python
def test_zero_byte_panda_output_fails_artifact_validation(tmp_path):
    output = tmp_path / "panda.tsv"
    output.touch()
    result = validate_output_artifacts(
        "run_panda",
        panda_decision(output_file=str(output)),
    )
    assert not result.ok
    assert any("empty" in message.casefold() for message in result.errors)


def test_malformed_puma_text_output_fails(tmp_path):
    output = tmp_path / "puma.tsv"
    output.write_text("not-a-network\n", encoding="utf-8")
    result = validate_output_artifacts(
        "run_puma",
        puma_decision(output_file=str(output)),
    )
    assert not result.ok


def test_valid_panda_fixture_passes(tmp_path):
    output = tmp_path / "panda.tsv"
    output.write_text("TF1\\tG1\\t0.25\\n", encoding="utf-8")
    result = validate_output_artifacts(
        "run_panda",
        panda_decision(output_file=str(output)),
    )
    assert result.ok
    assert result.metrics["verified_artifacts"] == 1
```

Add valid/invalid tests for formatted expression, co-expression, LIONESS text,
LIONESS `.npy`, and both CONDOR membership tables.

- [ ] **Step 2: Run artifact tests and verify the module is missing**

Run:

```bash
python -m pytest tests/test_agent_artifacts.py -q
```

Expected: FAIL because `artifact_validation` does not exist.

- [ ] **Step 3: Implement bounded structural validators**

Define:

```python
class ArtifactValidationResult(BaseModel):
    ok: bool
    artifacts: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metrics: dict[str, int | float | str | bool] = Field(default_factory=dict)
```

Implement helpers that:

- reject missing, non-file, unreadable, and zero-byte outputs;
- read only the header and a bounded number of text records;
- parse required numeric cells with `pandas.to_numeric`;
- load NumPy output with `allow_pickle=False`;
- reject empty arrays and non-finite numeric arrays;
- validate both `PREFIX-reg_memb.tsv` and `PREFIX-tar_memb.tsv` for CONDOR,
  requiring a header and at least one usable membership record in each;
- compare LIONESS sample columns with `_expression_sample_count`.

Dispatch only these write actions:

```python
WRITE_ACTIONS = {
    "format_expression",
    "convert_expression",
    "run_panda",
    "run_puma",
    "run_lioness_panda",
    "run_lioness_puma",
    "run_lioness_coexpression",
    "run_condor",
}
```

- [ ] **Step 4: Integrate validation into structured tool results**

After preliminary text/exit-code classification and before returning success:

```python
if status == "success" and action in WRITE_ACTIONS:
    artifact_check = validate_output_artifacts(action, decision)
    artifacts = artifact_check.artifacts
    warning_lines.extend(artifact_check.warnings)
    metrics.update(artifact_check.metrics)
    if not artifact_check.ok:
        status = "failed"
        error_lines.extend(artifact_check.errors)
```

Do not validate artifacts for dry runs or read-only inspection/retrieval actions.

- [ ] **Step 5: Run artifact, result-structuring, and full tests**

Run:

```bash
python -m pytest tests/test_agent_artifacts.py -q
python -m pytest tests/test_agent_gate.py -k "structured or artifact or command" -q
python -m pytest -q
```

Expected: zero-byte/malformed outputs fail, valid fixtures pass, full suite passes.

- [ ] **Step 6: Commit Task 4**

```bash
git add scripts/netzoo_agent_core/artifact_validation.py scripts/netzoo_agent_core/routing.py scripts/netzoo_agent_core/__init__.py scripts/netzoo_agent.py tests/test_agent_artifacts.py tests/test_agent_gate.py
git diff --cached --check
git commit -m "feat: validate NetZoo output artifacts"
```

### Task 5: Replace text control markers with typed continuations

**Files:**
- Modify: `scripts/netzoo_agent_core/contracts.py:516-533,393-406`
- Modify: `scripts/netzoo_agent_core/interaction.py:75-244,343-353,507-540`
- Modify: `scripts/netzoo_agent_core/planning.py:63-125,203-295`
- Modify: `scripts/netzoo_agent_core/evaluation.py:50-142,233-263`
- Modify: `scripts/netzoo_agent_core/graph.py:200-332`
- Modify: `scripts/netzoo_agent_core/cli.py:470-604`
- Modify: `scripts/netzoo_agent_core/session.py:157-210`
- Test: `tests/test_agent_gate.py`

**Interfaces:**
- Consumes: `ContinuationRequest` from Task 1.
- Produces: `clarification_continuation(...) -> ContinuationRequest`.
- Produces: `preference_continuation(...) -> ContinuationRequest`.
- Produces: `recommendation_continuation(...) -> ContinuationRequest`.
- Produces: `decision_from_continuation(continuation) -> TaskDecision`.
- Extends: `build_workflow_plan(..., trusted_assignments, cleared_fields, execution_authorization)`.

- [ ] **Step 1: Write failing state-preservation tests**

```python
def test_clarification_continuation_preserves_space_and_unicode_path(self):
    selected = {"expression_file": "data/My Study/表現 matrix.tsv"}
    continuation = agent.clarification_continuation(
        self.pending_plan(),
        selected,
    )
    self.assertEqual(continuation.assignments, selected)
    self.assertNotIn("PREVIOUS_ACTION", continuation.model_dump_json())


def test_preference_continuation_preserves_original_decision_inputs(self):
    plan = self.preference_plan_with_all_puma_inputs()
    continuation = agent.preference_continuation(plan, approved=True)
    resumed = agent.decision_from_continuation(continuation)
    self.assertEqual(
        resumed.expression_file,
        plan.decision["expression_file"],
    )
    self.assertEqual(resumed.mirna_file, plan.decision["mirna_file"])


def test_recommendation_acceptance_is_typed(self):
    prompt = agent.NextTurnPrompt(
        kind="recommended_workflow",
        question="continue?",
        continuation_action="run_lioness_puma",
    )
    continuation = agent.resolve_next_turn_input(prompt, "yes", source_task="how?")
    self.assertIsInstance(continuation, agent.ContinuationRequest)
```

- [ ] **Step 2: Run continuation tests and verify text-marker behavior fails**

Run:

```bash
python -m pytest tests/test_agent_gate.py -k "continuation and (space or preference or recommendation)" -q
```

Expected: FAIL because continuation helpers return strings or lose fields.

- [ ] **Step 3: Add plan authorization metadata**

Extend `WorkflowPlan` with:

```python
source_task: str = ""
execution_authorization: Literal[
    "direct_request",
    "clarification_continuation",
    "preference_continuation",
    "recommendation_acceptance",
    "overwrite_confirmation",
    "none",
] = "none"
```

Set `source_task=task` on initial planning. Extend `build_workflow_plan`:

```python
def build_workflow_plan(
    raw_decision: TaskDecision,
    task: str,
    ...,
    trusted_assignments: dict[str, str] | None = None,
    cleared_fields: set[str] | None = None,
    execution_authorization: str = "direct_request",
) -> WorkflowPlan:
```

Trusted assignments are applied directly and produce `selected` evidence without
requiring `SELECTED_FIELD` text. Cleared fields suppress extraction from the
original task for that planning turn.

- [ ] **Step 4: Return typed continuations from interaction helpers**

Replace generated marker strings with:

```python
return ContinuationRequest(
    kind="clarification",
    source_task=plan.source_task,
    action=decision.action,
    pending_plan=plan.model_dump(),
    assignments=assignments,
)
```

Preference continuation carries the full pending plan and approval. Recommendation
acceptance carries the recommended action and the original advisory task.

Keep a private legacy marker parser only for loading/resuming older sessions; new
CLI paths must not call it.

- [ ] **Step 5: Bypass Router for typed continuations**

In `graph.classify_task`, when `state["continuation"]` exists:

```python
continuation = ContinuationRequest.model_validate(state["continuation"])
decision = decision_from_continuation(continuation)
return {
    "decision": decision.model_dump(),
    "continuation": continuation.model_dump(),
}
```

`decision_from_continuation` validates the pending plan, copies its existing
`TaskDecision`, applies only allow-listed assignment fields, clears only declared
fields, and sets execution intent from the continuation kind. Recommendation
acceptance constructs a fresh decision for the allow-listed recommended action.

In `plan_task`, pass assignments, cleared fields, source task, and typed
authorization to `build_workflow_plan`. Do not call the response Router for the
continuation.

- [ ] **Step 6: Replace evaluator marker trust**

Remove new-flow dependence on:

```python
PREVIOUS_ACTION=
SELECTED_FIELD=
```

`intent_and_capability_alignment` and evidence provenance must accept only the
typed `WorkflowPlan.execution_authorization` values. Legacy resumed plans may be
normalized once into typed metadata before evaluation.

- [ ] **Step 7: Update CLI and session flow**

The CLI keeps the original visible reply in `messages` and passes:

```python
invocation = {
    "messages": [*conversation, HumanMessage(content=answer)],
    "continuation": continuation.model_dump(),
    "session_id": session_id,
}
```

Persist pending plan `source_task` and typed continuation state in session JSON.
Paths are never reconstructed by splitting a generated sentence.

- [ ] **Step 8: Run focused wizard, graph, and full tests**

Run:

```bash
python -m pytest tests/test_agent_gate.py -k "clarification or continuation or preference or recommended_workflow or resume" -q
python -m pytest -q
```

Expected: all typed continuation tests pass and existing session fixtures remain
readable.

- [ ] **Step 9: Commit Task 5**

```bash
git add scripts/netzoo_agent_core/contracts.py scripts/netzoo_agent_core/interaction.py scripts/netzoo_agent_core/planning.py scripts/netzoo_agent_core/evaluation.py scripts/netzoo_agent_core/graph.py scripts/netzoo_agent_core/cli.py scripts/netzoo_agent_core/session.py tests/test_agent_gate.py
git diff --cached --check
git commit -m "refactor: carry workflow continuations as typed state"
```

### Task 6: Prevent silent output overwrites

**Files:**
- Modify: `scripts/netzoo_agent_core/contracts.py:436-479,516-533`
- Modify: `scripts/netzoo_agent_core/routing.py:533-553`
- Modify: `scripts/netzoo_agent_core/planning.py:268-343`
- Modify: `scripts/netzoo_agent_core/evaluation.py:402-446`
- Modify: `scripts/netzoo_agent_core/interaction.py:335-465`
- Modify: `scripts/netzoo_agent_core/cli.py:489-574`
- Modify: `scripts/netzoo_agent_core/execution.py:52-135,206-360,435-478`
- Modify: `scripts/netzoo_agent_core/preparation.py:35-180,184-270`
- Modify: `scripts/netzoo_agent_core/command.py:49-90`
- Modify: `scripts/workflow_registry.py:91-217`
- Test: `tests/test_agent_gate.py`

**Interfaces:**
- Produces: `next_available_output(path, reserved=()) -> Path`.
- Adds: `TaskDecision.allow_overwrite: bool = False`.
- Adds: `WorkflowPlan.confirmation_kind`, `WorkflowPlan.confirmation_paths`.
- Adds optional `allow_overwrite: bool = False` to local write tool adapters.
- Consumes: typed overwrite continuation from Task 5.

- [ ] **Step 1: Write failing default-collision and explicit-confirmation tests**

```python
def test_existing_default_output_gets_numbered_sibling(tmp_path):
    existing = tmp_path / "study-puma.tsv"
    existing.write_text("old", encoding="utf-8")
    selected = agent.next_available_output(existing)
    self.assertEqual(selected, tmp_path / "study-puma-2.tsv")


def test_existing_explicit_output_requires_confirmation(self):
    decision, task = self.explicit_puma_request_with_existing_output()
    plan = agent.build_workflow_plan(decision, task)
    self.assertEqual(plan.status, "needs_confirmation")
    self.assertEqual(plan.confirmation_kind, "overwrite")
    self.assertEqual(plan.confirmation_paths, [decision.output_file])


def test_command_rejects_unapproved_existing_output(tmp_path):
    output = tmp_path / "existing.tsv"
    output.write_text("old", encoding="utf-8")
    raw = agent._run_command(
        ["run-panda", "--version"],
        output_file=str(output),
        allow_overwrite=False,
    )
    self.assertIn("overwrite approval", raw.casefold())
```

Add a LIONESS test proving both default outputs use the same `-2` run suffix and an
approved overwrite test proving the command may launch.

- [ ] **Step 2: Run collision tests and verify they fail**

Run:

```bash
python -m pytest tests/test_agent_gate.py -k "overwrite or numbered_sibling or output_collision" -q
```

Expected: existing defaults are reused and explicit outputs do not request
confirmation.

- [ ] **Step 3: Add collision-safe default helpers**

Implement:

```python
def next_available_output(path: Path, reserved: Collection[Path] = ()) -> Path:
    unavailable = {item.resolve() for item in reserved}
    if not path.exists() and path.resolve() not in unavailable:
        return path
    index = 2
    while True:
        candidate = path.with_name(f"{path.stem}-{index}{path.suffix}")
        if not candidate.exists() and candidate.resolve() not in unavailable:
            return candidate
        index += 1
```

For LIONESS, choose one available run index and apply it to both aggregate and
sample-specific paths.

- [ ] **Step 4: Add overwrite confirmation state**

Extend:

```python
class TaskDecision(BaseModel):
    allow_overwrite: bool = False


class WorkflowPlan(BaseModel):
    confirmation_kind: Literal["preference", "overwrite"] | None = None
    confirmation_paths: list[str] = Field(default_factory=list)
```

When a `provided` or `selected` output exists and `allow_overwrite` is false, return a
`needs_confirmation` plan with `confirmation_kind="overwrite"`. An approved typed
continuation rebuilds the plan with `allow_overwrite=True`. A declined
continuation clears the affected output fields so the wizard asks for replacements.

- [ ] **Step 5: Add final pre-launch collision gate**

Extend `_run_command`:

```python
def _run_command(
    command: list[str],
    output_file: str | None = None,
    additional_output_files: list[str] | None = None,
    allow_overwrite: bool = False,
) -> str:
    existing = [path for path in expected_outputs if Path(path).exists()]
    if EXECUTE_TOOLS and existing and not allow_overwrite:
        return (
            "- error: expected output already exists and has no overwrite approval: "
            + ", ".join(existing)
        )
```

Pass `allow_overwrite` through every write adapter and add it to the registry
executor fields with default `False`. This closes the plan-to-launch race.

- [ ] **Step 6: Run collision, dry-run, command, and full tests**

Run:

```bash
python -m pytest tests/test_agent_gate.py -k "overwrite or output or dry_run or command" -q
python -m pytest -q
```

Expected: defaults are versioned, explicit overwrites require approval, dry-run
previews still work, and full suite passes.

- [ ] **Step 7: Commit Task 6**

```bash
git add scripts/netzoo_agent_core/contracts.py scripts/netzoo_agent_core/routing.py scripts/netzoo_agent_core/planning.py scripts/netzoo_agent_core/evaluation.py scripts/netzoo_agent_core/interaction.py scripts/netzoo_agent_core/cli.py scripts/netzoo_agent_core/execution.py scripts/netzoo_agent_core/preparation.py scripts/netzoo_agent_core/command.py scripts/workflow_registry.py tests/test_agent_gate.py
git diff --cached --check
git commit -m "feat: require explicit output overwrite approval"
```

### Task 7: Add deterministic guidance fallback and complete verification

**Files:**
- Modify: `scripts/netzoo_agent_core/evaluation.py:768-793`
- Modify: `scripts/netzoo_agent_core/graph.py:490-602`
- Modify: `AGENT_USAGE.md`
- Test: `tests/test_agent_gate.py`

**Interfaces:**
- Produces: `render_capability_guidance(decision, project_policy) -> str`.
- Consumes: validated workflow specifications and `recommended_actions`.
- Guarantees: response-model failure or token exhaustion still names the recommended NetZoo workflow and required inputs.

- [ ] **Step 1: Write failing deterministic guidance tests**

```python
def test_capability_guidance_names_tools_and_required_inputs(self):
    decision = agent.TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=1.0,
        reason="workflow guidance",
        recommended_actions=["run_puma", "run_lioness_puma"],
    )
    text = agent.render_capability_guidance(decision, self.project_policy())
    self.assertIn("PUMA", text)
    self.assertIn("LIONESS-PUMA", text)
    self.assertIn("expression_file", text)
    self.assertIn("mirna_file", text)
```

Add graph tests for response-model exception and token-budget exhaustion.

- [ ] **Step 2: Run fallback tests and verify current generic fallback fails**

Run:

```bash
python -m pytest tests/test_agent_gate.py -k "capability_guidance or response_model" -q
```

Expected: fallback contains only Router decision/reason and omits actionable inputs.

- [ ] **Step 3: Implement registry-backed deterministic guidance**

Render only validated policy data:

```python
def render_capability_guidance(
    decision: TaskDecision,
    project_policy: ProjectPolicySnapshot,
) -> str:
    lines = ["Recommended NetZoo capabilities:"]
    for action in decision.recommended_actions:
        spec = project_policy.workflows.get(action)
        if spec is None:
            continue
        lines.append(f"- {spec.workflow}: {spec.description}")
        lines.append("  Required inputs: " + ", ".join(spec.required_inputs))
    if len(lines) == 1:
        lines.append(f"- No local workflow was selected. Reason: {decision.reason}")
    return "\n".join(lines)
```

Use it for no-tool response fallback and token-budget exhaustion. Local execution
fallback continues to use deterministic execution rendering.

- [ ] **Step 4: Document the final interaction semantics**

Update `AGENT_USAGE.md` with:

- uncertainty means input selection, not failure;
- explicit incompatible data means validation failure;
- recovery history may contain a superseded attempt;
- existing explicit outputs require confirmation;
- default outputs are versioned rather than overwritten.

- [ ] **Step 5: Run all verification**

Run:

```bash
python -m pytest -q
python -m ruff check scripts tests
python -m ruff format --check scripts tests
python -m compileall -q scripts tests
git diff --check
docker compose config --quiet
docker compose run --rm -T netzoo python scripts/netzoo_agent.py --help
```

Expected:

- complete Python suite passes;
- Ruff check and format pass;
- compilation passes;
- no whitespace errors;
- Compose configuration is valid;
- container CLI help exits successfully without a live API request.

- [ ] **Step 6: Review the final diff against the written spec**

Run:

```bash
git diff --stat
git diff -- scripts/netzoo_agent_core scripts/workflow_registry.py scripts/netzoo_agent.py tests AGENT_USAGE.md
```

Confirm the requirements assigned to this plan in
`docs/superpowers/specs/2026-07-30-netzoo-agent-state-stability-design.md`
have a passing test. Confirm the companion plan owns strict CONDOR command
semantics, runtime isolation, streaming header insertion, and expanded harness
coverage.

- [ ] **Step 7: Commit Task 7**

```bash
git add scripts/netzoo_agent_core/evaluation.py scripts/netzoo_agent_core/graph.py AGENT_USAGE.md tests/test_agent_gate.py
git diff --cached --check
git commit -m "docs: finalize agent stability behavior"
```

## Final Acceptance Checklist

- [ ] Successful recovery renders `COMPLETED` and completed next-turn guidance.
- [ ] Superseded failures remain visible only in audit history.
- [ ] Generic autonomous discovery cannot mix multi-file datasets.
- [ ] Explicit compatible cross-directory inputs still run.
- [ ] Empty or malformed outputs cannot become successful results.
- [ ] New continuations contain no natural-language control markers.
- [ ] Paths with spaces and Unicode survive clarification and preference flows.
- [ ] Default outputs are collision-free.
- [ ] Explicit overwrites require typed approval and a final launch-time check.
- [ ] Response fallback remains capability-aware without an LLM.
- [ ] Existing sessions, episodes, CLI tools, dry runs, and compatibility imports pass.

## Spec Coverage Matrix

| Written-spec requirement | Implemented and tested by |
|---|---|
| Attempt-Aware Recovery | Tasks 1 and 2 |
| Coherent Dataset Bundle Discovery | Task 3 |
| Artifact Validation | Task 4 |
| Typed Continuations | Task 5 |
| Output Collision Handling | Task 6 |
| Deterministic capability guidance | Task 7 |
| Backward compatibility and complete verification | Tasks 1, 5, and 7 |
| Strict CONDOR Completion | Companion execution-boundary plan, Task 1 |
| Instance-Scoped Runtime Configuration | Companion execution-boundary plan, Task 2 |
| Streaming and Atomic LIONESS-PUMA Header Insertion | Companion execution-boundary plan, Task 3 |
| Deterministic Evaluation Harness | Companion execution-boundary plan, Task 4 |
