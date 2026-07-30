# NetZoo Agent Correctness Hardening Design

Date: 2026-07-30

## Objective

Correct the execution-safety defects found in `netzoo_agent_core` without breaking
the existing CLI, LangChain tool, dry-run, workflow-policy, or legacy import
interfaces.

The change must preserve normal PANDA, PUMA, LIONESS, and CONDOR behaviour while
ensuring that validation failures cannot be reported as successful steps and that
every mutated recovery plan is evaluated before Executor access.

## Scope

This change includes:

- reliable normalization of human-readable tool diagnostics;
- re-evaluation of allow-listed recovery plans;
- bounded workspace file discovery;
- typed handling of local command-launch failures and configurable tool timeout;
- deletion of the accidental `netzoo_agent_core/Untitled` scratch file;
- regression tests for each changed behaviour.

This change does not include:

- removal of the `netzoo_agent.py` compatibility facade;
- redesign of all graph-state dictionaries;
- migration of every workflow tool from text output to a new public return type;
- changes to workflow inputs, biological algorithms, or command syntax.

## Design

### Diagnostic normalization

The existing LangChain tool interface continues to return text so external callers
and the CLI remain compatible. A private diagnostic-normalization function becomes
the seam between human-readable reports and `ToolExecutionResult`.

It recognizes error and warning labels with optional indentation, bullet markers,
and letter case. `structure_tool_result` uses only this normalized result instead of
depending on one exact Markdown spelling.

The parser remains intentionally narrow: only line-leading `error:` and `warning:`
labels are interpreted. Arbitrary mentions of those words inside explanatory text
do not change tool status.

### Recovery plan authorization

`WorkflowPlan` gains optional recovery metadata containing the allow-listed recovery
action and the step being repaired. `recover_workflow_plan` remains deterministic
and can only produce the existing `format_expression_headerless` repair.

When the recovery replaces the expression input, it also updates the expression
evidence entry to the derived path and records why it was derived. The Plan
Evaluator recognizes only the exact code-defined recovery sequence and rejects
unknown actions, inconsistent evidence, or repeated/unbounded recovery.

The graph changes from:

```text
recover -> execute_tool
```

to:

```text
recover -> evaluate_plan -> execute_tool
```

The normal initial-plan evaluator and recovered-plan evaluator therefore share one
authorization seam.

### Local command execution

The command adapter keeps its current string-returning interface. It catches command
launch, permission, and timeout failures and renders them as explicit local-tool
errors that `structure_tool_result` can classify.

Tool timeout is configurable independently from the LLM timeout. The default is
large enough for analysis workloads, and a non-positive value disables it
explicitly. Process output remains available for audit but is bounded before being
held by the agent; full diagnostics may be written to the existing private log
storage.

CLI error handling distinguishes local workflow failure from LLM provider failure.
Expected tool failures should normally remain typed graph results rather than escape
to the CLI loop.

### Bounded file discovery

Autonomous discovery may search the explicitly selected nearby directory and the
project `data/` directory. It stops at code-defined depth, visited-entry, and result
limits. Symlinked directories are not traversed.

When the scan budget is exhausted without an unambiguous match, the Planner asks for
the missing input instead of guessing.

### Compatibility

Existing public tool names, CLI prompts, command previews, workflow YAML schema, and
legacy facade exports remain unchanged. New fields added to persisted Pydantic
models have defaults so older session and episode files remain readable.

## Error Handling

- Invalid validation reports produce `ToolExecutionResult(status="failed")`.
- Missing executables, permission failures, and timeouts produce local-tool failure
  results with actionable error text.
- A recovery plan that fails evaluation is rendered as a Plan Evaluator rejection;
  no recovery tool runs.
- Discovery-limit exhaustion produces missing-input evidence rather than an
  exception.
- KeyboardInterrupt, SystemExit, and GeneratorExit retain their current fatal
  handling.

## Testing

Add tests proving that:

1. indented validation errors and warnings are normalized correctly;
2. missing PANDA/PUMA and CONDOR inputs cannot be reported as successful inspection;
3. a recovered plan passes the evaluator only with the exact allow-listed repair
   sequence and updated evidence;
4. the graph sends recovery through plan evaluation before execution;
5. missing executables and command timeouts become local-tool failures;
6. file discovery stops at its configured budget and preserves normal toy-data
   discovery;
7. existing command previews and interactive follow-up behaviour remain unchanged.

Verification consists of Python compilation, Ruff, the complete unittest suite, and
targeted probes for invalid input and recovery execution.

## Success Criteria

- Every ready initial or recovered plan must receive an approved
  `PlanEvaluationResult` before Executor access.
- A validation report containing an error can never become a successful structured
  result.
- Existing supported dry-run workflows and tests continue to pass.
- No new local action or shell authority is introduced.
- The compatibility facade remains functional.
