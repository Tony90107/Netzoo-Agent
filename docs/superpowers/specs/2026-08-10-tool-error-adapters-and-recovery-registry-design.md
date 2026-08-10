# Tool Error Adapters and Recovery Registry Design

## Goal

Replace the PUMA-specific error substring and duplicated recovery authorization
with two stable seams:

1. tool error adapters translate tool-owned machine error codes into a common
   diagnosis contract;
2. a recovery registry owns recovery lookup, applicability, plan mutation, and
   recovery-plan validation.

This change does not add an LLM diagnostic call. Unknown errors stop safely and
remain visible to the user and trace system.

## Current Problem

`routing/results.py` currently combines three responsibilities:

- generic normalization of raw tool text, exit codes, diagnostics, and artifacts;
- recognition of a PUMA-specific English sentence;
- selection of the `format_expression_headerless` recovery.

Recovery authorization is also repeated across the `WorkflowPlan` literal,
plan-rule conditions, result normalization, and `recover_workflow_plan`. Adding a
new recovery therefore requires editing multiple shared modules. Human-readable
text changes can also prevent a known PUMA failure from being recognized.

The Result Evaluator itself remains suitably generic: it decides only whether a
structured result means continue, complete, fail, or replan. The refactor keeps
that deterministic state-machine role.

## Scope

### In scope

- Add stable machine-readable tool error codes.
- Add a tool error adapter interface and action-keyed adapter registry.
- Move PUMA header-error recognition out of generic result normalization.
- Add an optional `error_code` to `ToolExecutionResult`.
- Carry the triggering error code into recovery evaluation and plan provenance.
- Add a recovery strategy interface and registry.
- Move PUMA headerless plan mutation and validation behind its strategy.
- Preserve the existing recovery output path, evidence, step sequence, retry
  limit, trace ordering, and user-visible outcome.
- Preserve backward validation of saved results and plans that do not contain
  the new optional fields.

### Out of scope

- Calling an LLM to diagnose unknown errors.
- Adding new PANDA, LIONESS, or CONDOR automatic repairs.
- Allowing tools, policy Markdown, YAML, or LLM output to register executable
  Python recovery functions at runtime.
- Changing the graph topology or `/test` versus `/execute` authorization.
- Converting every existing tool executor from text output to a new return type.

## Architecture

### Tool error adapter seam

The generic result normalizer continues to parse universal signals:

- line-leading errors and warnings;
- process exit code;
- dry-run status;
- expected artifact validation;
- bounded raw output and log persistence.

Tool-specific interpretation moves behind this interface:

```python
class ToolErrorDiagnosis(BaseModel):
    error_code: str
    retryable: bool = False
    recovery_action: str | None = None
    evidence: list[str] = Field(default_factory=list)

class ToolErrorContext(BaseModel):
    action: str
    reported_error_codes: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    exit_code: int | None = None

class ToolErrorAdapter(Protocol):
    def adapt(self, context: ToolErrorContext) -> ToolErrorDiagnosis | None: ...

def adapt_tool_error(context: ToolErrorContext) -> ToolErrorDiagnosis | None: ...
```

The adapter registry is code-owned and keyed by action. It is not populated from
LLM output, project policy, retrieved content, or user data.

```python
TOOL_ERROR_ADAPTERS = {
    "run_puma": (PumaToolErrorAdapter(),),
}
```

The PUMA wrapper reports a stable code alongside its human-readable message:

```text
Error code: PUMA_EXPRESSION_HEADER_UNSUPPORTED
```

The PUMA adapter recognizes the code, not the English explanation. Therefore the
human-readable wording may change without breaking recovery.

The generic `structure_tool_result` interface remains unchanged. It extracts
machine codes, builds `ToolErrorContext`, calls `adapt_tool_error`, and copies a
recognized diagnosis into `ToolExecutionResult.error_code`, `retryable`, and
`recovery_hint`. An absent adapter or unknown error code produces no recovery
hint and therefore stops safely.

### Recovery registry seam

Recovery behavior moves behind a code-owned strategy interface:

```python
class RecoveryStrategy(Protocol):
    name: str
    applicable_actions: frozenset[str]
    accepted_error_codes: frozenset[str]

    def apply(
        self,
        plan: WorkflowPlan,
        step_index: int,
        evaluation: EvaluationResult,
    ) -> tuple[WorkflowPlan, int]: ...

    def validate(
        self,
        plan: WorkflowPlan,
        decision: TaskDecision,
        normal_steps: list[str],
    ) -> RecoveryValidation: ...
```

```python
RECOVERY_STRATEGIES = {
    "format_expression_headerless": PumaHeaderlessExpressionRecovery(),
}
```

Registry lookup and applicability checks are centralized. A strategy is rejected
unless all of the following are true:

- its name exists in the registry;
- the failed action is in `applicable_actions`;
- the triggering error code is in `accepted_error_codes`;
- the retry limit has not been exceeded;
- its generated plan satisfies its strategy validation and every general Plan
  Evaluator rule.

`WorkflowPlan.recovery_action` changes from a one-value `Literal` to optional
`str`. The plan also gains optional `recovery_error_code`. These fields describe
provenance; they do not grant authority. Authority comes only from a strategy
present in the code-owned registry.

## Exact Recovery Data Flow

Recovery does not call the Router LLM and does not rebuild a plan from the user's
prompt. It performs a bounded mutation of the already-approved typed plan.

Assume the initial PUMA plan is:

```python
WorkflowPlan(
    workflow="PUMA",
    decision={
        "action": "run_puma",
        "expression_file": "data/expression.tsv",
        "output_file": "outputs/puma.tsv",
        # remaining required inputs omitted here
    },
    steps=[
        WorkflowStep(action="inspect_inputs"),
        WorkflowStep(action="run_puma"),
    ],
    current_step=1,
)
```

The state transition is:

1. `run_puma` reports
   `PUMA_EXPRESSION_HEADER_UNSUPPORTED` while executing step index 1.
2. The PUMA error adapter returns a typed diagnosis with
   `recovery_action="format_expression_headerless"`.
3. `evaluate_step_result` returns `EvaluationResult(status="replan")` carrying
   both the recovery action and the triggering error code.
4. The graph routes to `recover`.
5. `recover_workflow_plan` retrieves the strategy from the recovery registry and
   verifies action, error code, and retry limits.
6. The strategy derives
   `outputs/expression.puma-expression.tsv`; it never overwrites the original
   expression input.
7. The strategy changes the copied `TaskDecision.expression_file` to the derived
   path.
8. The strategy replaces the expression evidence with explicit derived
   provenance:

   ```python
   InputEvidence(
       field="expression_file",
       status="derived",
       value="outputs/expression.puma-expression.tsv",
       derived_from="data/expression.tsv",
       reason="The prior PUMA attempt rejected the expression header...",
   )
   ```

9. It preserves already-completed steps before the failure and replaces the
   failed suffix. The plan changes from:

   ```text
   [inspect_inputs, run_puma]
   ```

   to:

   ```text
   [inspect_inputs, format_expression, inspect_inputs, run_puma]
   ```

10. `current_step` remains 1, so the already-completed first inspection is not
    repeated. Execution resumes at `format_expression`.
11. Recovery metadata is recorded on the plan:

    ```python
    recovery_action = "format_expression_headerless"
    recovery_error_code = "PUMA_EXPRESSION_HEADER_UNSUPPORTED"
    recovery_step_index = 1
    recovery_attempt = 1
    ```

12. The failed result is kept for audit but marked superseded by recovery attempt
    1.
13. Before any new tool runs, the graph sends the mutated plan through the Plan
    Evaluator again.
14. The general Plan Evaluator checks allowlists, evidence, output safety, policy
    binding, and planner state. The registered strategy checks the exact recovery
    metadata, derived path provenance, and expected step sequence.
15. Only an approved recovery plan executes:

    ```text
    format_expression
    -> Result Evaluator: continue
    -> inspect_inputs
    -> Result Evaluator: continue
    -> run_puma
    -> Result Evaluator: completed or failed
    ```

This is called `replan` because the typed plan changes, but it is not free-form
planning. It is a deterministic, registered plan transformation.

## Contract Changes

All new fields are optional to preserve old serialized state.

```python
class ToolExecutionResult(BaseModel):
    # existing fields
    error_code: str | None = None

class EvaluationResult(BaseModel):
    # existing fields
    recovery_action: str | None = None
    recovery_error_code: str | None = None

class WorkflowPlan(BaseModel):
    # existing fields
    recovery_action: str | None = None
    recovery_error_code: str | None = None
```

`recovery_hint` remains temporarily available on `ToolExecutionResult` to avoid
breaking existing imports, traces, and tests. Its value is now supplied by an
adapter rather than generic PUMA-specific code.

## Unknown and Invalid Conditions

- A tool error with no machine code remains a normal failed result.
- A machine code with no matching tool adapter remains a normal failed result.
- An adapter diagnosis without a recovery action remains a classified but
  non-recoverable failure.
- An unregistered recovery action is rejected and cannot mutate a plan.
- A registered strategy applied to the wrong action or error code is rejected.
- Malformed recovery metadata causes Plan Evaluator rejection.
- A recovery-generated output collision causes Plan Evaluator rejection.
- A second PUMA header failure reaches the existing maximum attempt limit and
  terminates as failed.

## File Responsibilities

- `execution.py`: tool-owned PUMA machine error code emission; no recovery
  selection.
- `routing/error_adapters.py`: diagnosis contracts, adapter registry, registry
  lookup, and PUMA adapter.
- `routing/results.py`: generic normalization and delegation to the adapter seam.
- `contracts/results.py`: optional structured error and recovery provenance.
- `contracts/planning.py`: extensible recovery metadata without an action literal.
- `evaluation/recovery_registry.py`: strategy interface, immutable registry, and
  guarded lookup.
- `evaluation/recovery_strategies/puma_headerless.py`: PUMA-specific plan mutation
  and recovery-plan validation.
- `evaluation/recovery.py`: stable orchestration interface delegating to the
  registry.
- `evaluation/plan_rules.py`: general rules plus delegation to registered strategy
  validation; no PUMA recovery string comparisons.

## Testing

Tests exercise the external seams rather than internal helper structure:

1. `structure_tool_result` recognizes the stable PUMA machine code and produces
   a retryable typed result.
2. Changing the human-readable PUMA error wording does not change diagnosis.
3. The old English phrase without the machine code no longer grants recovery.
4. Unknown codes and unregistered actions remain failed and non-retryable.
5. Recovery registry rejects unknown names, wrong actions, wrong error codes, and
   attempts beyond the configured maximum.
6. Registered PUMA recovery produces the exact derived evidence, decision path,
   metadata, step sequence, and resume index.
7. Forged or modified recovery plans remain rejected by the Plan Evaluator.
8. Existing graph ordering confirms `recover -> evaluate_plan -> execute_tool`.
9. Existing artifact, trace, memory, response, package-interface, and full test
   suites remain green.

## Success Criteria

- Generic result normalization contains no PUMA action or PUMA error-text special
  case.
- General plan rules contain no direct
  `format_expression_headerless` or `run_puma` recovery comparisons.
- Adding another tool error adapter does not require editing generic result
  normalization.
- Adding another recovery strategy does not require editing recovery orchestration
  or the `WorkflowPlan` type.
- Known PUMA header recovery remains bounded, auditable, non-overwriting, and
  gated by deterministic plan evaluation.
- Unknown errors never gain automatic execution authority.
