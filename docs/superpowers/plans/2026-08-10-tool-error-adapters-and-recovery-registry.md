# Tool Error Adapters and Recovery Registry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace generic PUMA error-text special casing with machine-coded tool error adapters and move recovery authorization, mutation, and validation behind a code-owned recovery registry.

**Architecture:** `routing.results` retains generic output normalization and delegates tool-owned failures to an action-keyed adapter registry. `evaluation.recovery` retains its stable public interface and delegates to registered strategies that own applicability, plan mutation, and recovery-specific validation; the general Plan Evaluator remains the final authority.

**Tech Stack:** Python 3.11+, Pydantic v2, pytest/unittest, LangGraph state contracts.

## Global Constraints

- Do not add an LLM diagnostic call.
- Unknown errors stop safely and receive no automatic recovery authority.
- Preserve the public `structure_tool_result(...)` and `recover_workflow_plan(...)` interfaces.
- Preserve `/test` versus `/execute`, graph topology, trace ordering, retry limits, derived output naming, and original-input non-overwrite behavior.
- All new serialized contract fields are optional with backward-compatible defaults.
- Registries are immutable code-owned data; project policy, retrieved content, and LLM output cannot register Python behavior.
- A recovery plan must return through the deterministic Plan Evaluator before execution.

---

## File Structure

| File | Responsibility |
|---|---|
| `scripts/netzoo_agent_core/routing/error_adapters.py` | Tool error diagnosis contracts, adapter protocol, action registry, stable machine-code extraction, and PUMA adapter |
| `scripts/netzoo_agent_core/routing/results.py` | Generic text/exit/artifact normalization and delegation to the adapter seam |
| `scripts/netzoo_agent_core/execution.py` | Emit the stable PUMA header error code with human-readable validation output |
| `scripts/netzoo_agent_core/contracts/results.py` | Add optional result and evaluation error-code provenance |
| `scripts/netzoo_agent_core/contracts/planning.py` | Make recovery action extensible and add optional triggering error-code provenance |
| `scripts/netzoo_agent_core/evaluation/recovery_registry.py` | Recovery strategy protocol, immutable registry, and guarded strategy lookup |
| `scripts/netzoo_agent_core/evaluation/recovery_strategies/puma_headerless.py` | PUMA headerless plan mutation and recovery-specific validation |
| `scripts/netzoo_agent_core/evaluation/recovery.py` | Stable recovery orchestration delegating through the registry |
| `scripts/netzoo_agent_core/evaluation/plan_rules.py` | General plan rules delegating recovery validation to the selected strategy |
| `scripts/netzoo_agent_core/evaluation/step_results.py` | Propagate the structured triggering error code into `EvaluationResult` |
| `tests/test_tool_error_adapters.py` | Error-adapter interface behavior and PUMA wording independence |
| `tests/test_recovery_registry.py` | Registry authorization, deterministic plan mutation, and evaluator integration |
| `tests/test_contracts_package.py` | Updated intentional schema digests for optional contract fields |
| `tests/test_routing_package.py` | New child-module import coverage without changing historical exports |
| `tests/test_evaluation_package.py` | New child-module import coverage without changing historical exports |

---

### Task 1: Add machine-coded tool error adapters

**Files:**
- Create: `tests/test_tool_error_adapters.py`
- Create: `scripts/netzoo_agent_core/routing/error_adapters.py`
- Modify: `scripts/netzoo_agent_core/contracts/results.py`
- Modify: `scripts/netzoo_agent_core/execution.py`
- Modify: `scripts/netzoo_agent_core/routing/results.py`
- Modify: `tests/test_routing_package.py`

**Interfaces:**
- Consumes: existing `structure_tool_result(action, decision, raw_output, persist_log=False, attempt_id=0) -> ToolExecutionResult`.
- Produces: `ToolErrorDiagnosis`, `ToolErrorContext`, `ToolErrorAdapter`, `extract_reported_error_codes(raw_output) -> list[str]`, and `adapt_tool_error(context) -> ToolErrorDiagnosis | None`.
- Produces: optional `ToolExecutionResult.error_code: str | None`.

- [ ] **Step 1: Write failing adapter tests**

```python
from netzoo_agent_core.contracts import TaskDecision
from netzoo_agent_core.routing.error_adapters import (
    PUMA_EXPRESSION_HEADER_UNSUPPORTED,
    ToolErrorContext,
    adapt_tool_error,
    extract_reported_error_codes,
)
from netzoo_agent_core.routing.results import structure_tool_result


def _puma_decision() -> TaskDecision:
    return TaskDecision(
        action="run_puma",
        in_scope=True,
        should_execute=True,
        confidence=1.0,
        reason="test",
    )


def test_machine_error_code_is_extracted_independently_of_message():
    raw = "Error code: PUMA_EXPRESSION_HEADER_UNSUPPORTED\nerror: wording changed"
    assert extract_reported_error_codes(raw) == [
        PUMA_EXPRESSION_HEADER_UNSUPPORTED
    ]


def test_puma_adapter_maps_stable_code_to_recovery():
    diagnosis = adapt_tool_error(
        ToolErrorContext(
            action="run_puma",
            reported_error_codes=[PUMA_EXPRESSION_HEADER_UNSUPPORTED],
            errors=["arbitrary human wording"],
        )
    )
    assert diagnosis is not None
    assert diagnosis.error_code == PUMA_EXPRESSION_HEADER_UNSUPPORTED
    assert diagnosis.retryable is True
    assert diagnosis.recovery_action == "format_expression_headerless"


def test_human_phrase_without_machine_code_does_not_grant_recovery():
    result = structure_tool_result(
        "run_puma",
        _puma_decision(),
        "error: legacy netZooPy PUMA does not accept an expression header",
    )
    assert result.status == "failed"
    assert result.error_code is None
    assert result.retryable is False
    assert result.recovery_hint is None


def test_unknown_machine_code_stops_without_recovery():
    result = structure_tool_result(
        "run_puma",
        _puma_decision(),
        "Error code: PUMA_UNKNOWN_FAILURE\nerror: unknown",
    )
    assert result.status == "failed"
    assert result.error_code is None
    assert result.retryable is False
    assert result.recovery_hint is None
```

- [ ] **Step 2: Run the adapter tests and verify red**

Run:

```bash
pytest tests/test_tool_error_adapters.py -q
```

Expected: collection fails because `routing.error_adapters` and `ToolExecutionResult.error_code` do not exist.

- [ ] **Step 3: Add the tool error adapter module**

Implement immutable Pydantic context/diagnosis models, a `Protocol`, one PUMA adapter, and a mapping protected by `MappingProxyType`:

```python
PUMA_EXPRESSION_HEADER_UNSUPPORTED = "PUMA_EXPRESSION_HEADER_UNSUPPORTED"

class ToolErrorDiagnosis(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    error_code: str
    retryable: bool = False
    recovery_action: str | None = None
    evidence: list[str] = Field(default_factory=list)

class ToolErrorContext(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    action: str
    reported_error_codes: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    exit_code: int | None = None

class PumaToolErrorAdapter:
    def adapt(self, context: ToolErrorContext) -> ToolErrorDiagnosis | None:
        if PUMA_EXPRESSION_HEADER_UNSUPPORTED not in context.reported_error_codes:
            return None
        return ToolErrorDiagnosis(
            error_code=PUMA_EXPRESSION_HEADER_UNSUPPORTED,
            retryable=True,
            recovery_action="format_expression_headerless",
            evidence=list(context.errors),
        )
```

`adapt_tool_error` iterates only adapters registered under `context.action` and returns the first diagnosis. Unknown actions and codes return `None`.

- [ ] **Step 4: Emit and consume the stable machine code**

Add this separate line to the PUMA header validation output in `execution.py`:

```python
f"Error code: {PUMA_EXPRESSION_HEADER_UNSUPPORTED}\n"
```

In `routing/results.py`, delete the action/English-substring special case. Extract reported error codes, construct `ToolErrorContext`, call `adapt_tool_error`, and populate:

```python
error_code=diagnosis.error_code if diagnosis else None,
retryable=diagnosis.retryable if diagnosis else False,
recovery_hint=diagnosis.recovery_action if diagnosis else None,
```

- [ ] **Step 5: Preserve package surfaces and run focused tests**

Add `error_adapters` to the child-module import list in `tests/test_routing_package.py`; do not add new names to the historical `routing.__all__` list.

Run:

```bash
pytest tests/test_tool_error_adapters.py tests/test_routing_package.py -q
pytest tests/test_agent_gate.py -k 'structure_tool_result or puma_header' -q
```

Expected: all selected tests pass except legacy tests that intentionally expect the old phrase-only recovery; update those fixtures to include the stable error-code line without weakening their assertions.

- [ ] **Step 6: Commit Task 1**

```bash
git add scripts/netzoo_agent_core/routing/error_adapters.py scripts/netzoo_agent_core/routing/results.py scripts/netzoo_agent_core/contracts/results.py scripts/netzoo_agent_core/execution.py tests/test_tool_error_adapters.py tests/test_routing_package.py tests/test_agent_gate.py
git commit -m "refactor: adapt machine-coded tool errors"
```

---

### Task 2: Add the recovery registry and PUMA strategy

**Files:**
- Create: `tests/test_recovery_registry.py`
- Create: `scripts/netzoo_agent_core/evaluation/recovery_registry.py`
- Create: `scripts/netzoo_agent_core/evaluation/recovery_strategies/__init__.py`
- Create: `scripts/netzoo_agent_core/evaluation/recovery_strategies/puma_headerless.py`
- Modify: `scripts/netzoo_agent_core/contracts/results.py`
- Modify: `scripts/netzoo_agent_core/contracts/planning.py`
- Modify: `scripts/netzoo_agent_core/evaluation/recovery.py`
- Modify: `scripts/netzoo_agent_core/evaluation/step_results.py`
- Modify: `scripts/netzoo_agent_core/evaluation/plan_rules.py`
- Modify: `tests/test_evaluation_package.py`

**Interfaces:**
- Consumes: `ToolExecutionResult.error_code` and adapter-provided `recovery_hint` from Task 1.
- Produces: `RecoveryValidation`, `RecoveryStrategy`, `get_recovery_strategy(name)`, and immutable `RECOVERY_STRATEGIES`.
- Produces: optional `EvaluationResult.recovery_error_code` and `WorkflowPlan.recovery_error_code`; extensible `WorkflowPlan.recovery_action: str | None`.
- Preserves: `recover_workflow_plan(plan, step_index, evaluation) -> tuple[WorkflowPlan, int]`.

- [ ] **Step 1: Write failing registry and plan-mutation tests**

Create helpers for a ready PUMA plan and assert:

```python
def test_unknown_recovery_name_is_not_registered():
    assert get_recovery_strategy("delete_inputs_and_retry") is None


def test_puma_strategy_rejects_wrong_error_code():
    strategy = get_recovery_strategy("format_expression_headerless")
    assert strategy is not None
    assert strategy.accepts(
        action="run_puma",
        error_code="PUMA_UNKNOWN_FAILURE",
    ) is False


def test_registered_strategy_builds_bounded_plan():
    recovered, next_step = recover_workflow_plan(
        ready_puma_plan(),
        1,
        EvaluationResult(
            status="replan",
            reason="header rejected",
            recovery_action="format_expression_headerless",
            recovery_error_code="PUMA_EXPRESSION_HEADER_UNSUPPORTED",
        ),
    )
    assert next_step == 1
    assert [step.action for step in recovered.steps] == [
        "inspect_inputs",
        "format_expression",
        "inspect_inputs",
        "run_puma",
    ]
    assert recovered.recovery_error_code == "PUMA_EXPRESSION_HEADER_UNSUPPORTED"
    expression = next(
        item for item in recovered.evidence if item.field == "expression_file"
    )
    assert expression.status == "derived"
    assert expression.derived_from == "data/expression.tsv"
```

Also test wrong action, missing error code, second attempt, malformed derived evidence, and modified format arguments.

- [ ] **Step 2: Run registry tests and verify red**

Run:

```bash
pytest tests/test_recovery_registry.py -q
```

Expected: collection fails because recovery registry and strategy modules do not exist.

- [ ] **Step 3: Generalize serialized contracts and evaluator propagation**

Add:

```python
class EvaluationResult(BaseModel):
    # existing fields
    recovery_error_code: str | None = None

class WorkflowPlan(BaseModel):
    # existing fields
    recovery_action: str | None = None
    recovery_error_code: str | None = None
```

Change `evaluate_step_result` to copy `structured.error_code` into `recovery_error_code` whenever it returns `status="replan"`.

- [ ] **Step 4: Implement the registry and strategy**

Define `RecoveryValidation` as an immutable model containing `ok`, `detail`, `failures`, and `expected_steps`. Define a strategy protocol with `accepts`, `apply`, and `validate`. Store the PUMA strategy in a `MappingProxyType` registry.

Move all PUMA-specific mutation from `evaluation/recovery.py` into `PumaHeaderlessExpressionRecovery.apply`. Move the recovery-specific checks currently in `_derived_evidence_contract_failures` and `_expected_plan_steps` into `PumaHeaderlessExpressionRecovery.validate`.

The strategy must:

- accept only `run_puma` plus `PUMA_EXPRESSION_HEADER_UNSUPPORTED`;
- derive `<output-parent>/<expression-stem>.puma-expression.tsv`;
- replace or append exactly one derived `expression_file` evidence item;
- insert `format_expression`, `inspect_inputs`, and `run_puma` at the failed step;
- set action, error code, step index, and incremented attempt metadata;
- return the failed step index as the resume position.

- [ ] **Step 5: Delegate recovery orchestration and plan validation**

`recover_workflow_plan` must return the unchanged plan/index for missing or unregistered strategy, failed applicability, or exhausted attempts. Otherwise it calls `strategy.apply`.

Replace direct PUMA/action string comparisons in `plan_rules.py` with:

```python
strategy = get_recovery_strategy(plan.recovery_action)
validation = strategy.validate(plan, decision, normal_steps) if strategy else ...
```

Initial plans with no recovery metadata continue to expect `normal_steps`. Any recovery metadata with no registered strategy fails authorization.

- [ ] **Step 6: Run registry, evaluator, and forged-plan tests**

Run:

```bash
pytest tests/test_recovery_registry.py tests/test_evaluation_package.py -q
pytest tests/test_agent_gate.py -k 'recovery or header_failure or unapproved_sequence' -q
pytest tests/test_agent_module_boundaries.py -k recovery -q
```

Expected: all selected tests pass; recovery still routes through `evaluate_plan`.

- [ ] **Step 7: Commit Task 2**

```bash
git add scripts/netzoo_agent_core/contracts/results.py scripts/netzoo_agent_core/contracts/planning.py scripts/netzoo_agent_core/evaluation/recovery_registry.py scripts/netzoo_agent_core/evaluation/recovery_strategies scripts/netzoo_agent_core/evaluation/recovery.py scripts/netzoo_agent_core/evaluation/step_results.py scripts/netzoo_agent_core/evaluation/plan_rules.py tests/test_recovery_registry.py tests/test_evaluation_package.py tests/test_agent_gate.py
git commit -m "refactor: register bounded recovery strategies"
```

---

### Task 3: Verify compatibility, schemas, and full behavior

**Files:**
- Modify: `tests/test_contracts_package.py`
- Modify: `docs/superpowers/plans/2026-08-10-tool-error-adapters-and-recovery-registry.md`
- Test: `tests/test_planning_package.py`
- Test: `tests/test_graph_tracing.py`

**Interfaces:**
- Consumes: final contracts and registries from Tasks 1 and 2.
- Produces: intentional schema digests, verified package compatibility, and recorded verification results.

- [ ] **Step 1: Confirm only intended schemas changed**

Run:

```bash
pytest tests/test_contracts_package.py -q
```

Expected: only `WorkflowPlan` and `ToolExecutionResult` schema digest assertions fail. `EvaluationResult` is not currently digest-pinned. Calculate the two new SHA-256 values using the exact canonical JSON logic already in the test and update only those digest constants.

- [ ] **Step 2: Run focused package and integration suites**

```bash
pytest \
  tests/test_tool_error_adapters.py \
  tests/test_recovery_registry.py \
  tests/test_routing_package.py \
  tests/test_evaluation_package.py \
  tests/test_contracts_package.py \
  tests/test_planning_package.py \
  tests/test_agent_gate.py \
  tests/test_graph_tracing.py \
  -q
```

Expected: all tests pass. Fix compatibility failures at the owning interface without restoring generic PUMA string matching.

- [ ] **Step 3: Enforce architectural absence checks**

Run:

```bash
rg -n 'does not accept an expression header|action == "run_puma"' \
  scripts/netzoo_agent_core/routing/results.py
rg -n 'format_expression_headerless|run_puma' \
  scripts/netzoo_agent_core/evaluation/plan_rules.py
```

Expected: both commands return no matches. PUMA-specific behavior exists only in the PUMA adapter and registered strategy.

- [ ] **Step 4: Run the full suite**

```bash
pytest -q
```

Expected: all tests pass with no new warnings attributable to this refactor.

- [ ] **Step 5: Record verification and commit**

Append exact focused/full-suite test counts and architectural absence-check results to this plan under `## Verification Results`, then run:

```bash
git add tests/test_contracts_package.py tests/test_planning_package.py tests/test_graph_tracing.py docs/superpowers/plans/2026-08-10-tool-error-adapters-and-recovery-registry.md
git commit -m "test: verify recovery registry refactor"
```
