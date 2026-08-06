# Recovery Provenance Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the full test suite green by isolating clarification tests from workspace discovery and giving allow-listed recovery artifacts explicit, strictly validated provenance.

**Architecture:** Preserve coherent dataset autofill and the historical evaluation facade. Clarification tests will construct their own missing-input plan, while recovery will introduce a `derived` evidence status validated by a new private plan-aware rule and rendered with an explicit source label.

**Tech Stack:** Python 3.12, Pydantic, pytest/unittest, standard-library pathlib, and the existing NetZoo planning/evaluation packages.

## Global Constraints

- Work only in `/Users/chenzhonghan/Documents/LLM AGENT/network-zoo-panda-puma` on the existing `main` branch.
- Do not create a branch or modify, stage, or commit unrelated dirty-worktree files.
- Preserve coherent-bundle autofill for complete validated datasets.
- Preserve `_evidence_contract_failures(evidence, user_task)` and every existing public/legacy facade signature and export.
- Do not weaken recovery allowlists, recovery attempt bounds, step ordering, dataset bundle validation, or execution authority.
- A `derived` input is valid only for the allow-listed PUMA header-removal recovery and must match its decision and format-step output.
- Use TDD for product behavior and make one focused commit per task.
- Require `pytest -q` to finish with zero failures before invoking `finishing-a-development-branch`.

## File Map

| Path | Responsibility in this repair |
| --- | --- |
| `tests/test_agent_gate.py` | Stable clarification fixtures and recovery provenance behavior. |
| `scripts/netzoo_agent_core/contracts.py` | Add the explicit `derived` evidence vocabulary. |
| `scripts/netzoo_agent_core/evaluation/recovery.py` | Mark bounded recovery output as derived and clear stale provenance. |
| `scripts/netzoo_agent_core/evaluation/plan_rules.py` | Validate derived evidence shape and recovery context without changing the historical helper signature. |
| `scripts/netzoo_agent_core/evaluation/plan_review.py` | Combine historical evidence checks with the private derived-context check. |
| `scripts/netzoo_agent_core/evaluation/rendering.py` | Render derived inputs with a clear source label. |
| `tests/test_evaluation_package.py` | Characterize the derived rendering label. |

---

### Task 1: Isolate Clarification Tests from Workspace Discovery

**Files:**
- Modify: `tests/test_agent_gate.py`

**Interfaces:**
- Consumes: `TaskDecision`, `WorkflowPlan`, and `InputEvidence` through the legacy `netzoo_agent` facade.
- Produces: a test-only `_panda_clarification_plan()` fixture with exactly two missing fields and deterministic candidates.

- [ ] **Step 1: Re-run the three stale clarification tests as the red baseline**

Run:

```bash
pytest \
  tests/test_agent_gate.py::CapabilityGateTests::test_clarification_wizard_selects_each_missing_field_independently \
  tests/test_agent_gate.py::CapabilityGateTests::test_selected_input_keeps_selected_provenance_after_replanning \
  tests/test_agent_gate.py::CapabilityGateTests::test_clarification_marker_preserves_previous_action_against_reroute \
  -q
```

Expected: all three fail because `build_workflow_plan()` returns a ready plan after coherent-bundle autofill, leaving no missing evidence for clarification.

- [ ] **Step 2: Add the isolated clarification fixture**

Add this helper to `CapabilityGateTests` immediately before the clarification wizard tests:

```python
    @staticmethod
    def _panda_clarification_plan():
        decision = agent.TaskDecision(
            action="run_panda",
            in_scope=True,
            should_execute=False,
            confidence=0.95,
            reason="formal PANDA request",
            motif_file="data/lioness-toy/motif-panda.tsv",
            output_file="outputs/demo/panda.tsv",
        )
        return agent.WorkflowPlan(
            workflow="PANDA",
            objective=decision.reason,
            decision=decision.model_dump(),
            evidence=[
                agent.InputEvidence(
                    field="expression_file",
                    status="missing",
                    reason="Choose the expression input.",
                    candidates=[
                        "data/lioness-toy/expression.tsv",
                        "data/manual-tests/expression.tsv",
                    ],
                ),
                agent.InputEvidence(
                    field="motif_file",
                    status="provided",
                    value="data/lioness-toy/motif-panda.tsv",
                    reason="Explicitly provided by the user.",
                ),
                agent.InputEvidence(
                    field="ppi_file",
                    status="missing",
                    reason="Choose the PPI input.",
                    candidates=[
                        "data/lioness-toy/ppi.tsv",
                        "data/manual-tests/ppi.tsv",
                    ],
                ),
                agent.InputEvidence(
                    field="output_file",
                    status="defaulted",
                    value="outputs/demo/panda.tsv",
                    reason="The reversible project default was used.",
                ),
            ],
            missing_inputs=["expression_file", "ppi_file"],
            status="needs_input",
            question="Provide the next missing input.",
        )
```

- [ ] **Step 3: Replace discovery-dependent setup in exactly three tests**

In these tests only:

```text
test_clarification_wizard_selects_each_missing_field_independently
test_selected_input_keeps_selected_provenance_after_replanning
test_clarification_marker_preserves_previous_action_against_reroute
```

replace the repeated `TaskDecision(...)` plus `build_workflow_plan(...)` setup with:

```python
        plan = self._panda_clarification_plan()
```

Keep every existing assertion unchanged. Do not alter planner or coherent-bundle production code.

- [ ] **Step 4: Run clarification and bundle tests**

Run:

```bash
pytest \
  tests/test_agent_gate.py::CapabilityGateTests::test_clarification_wizard_selects_each_missing_field_independently \
  tests/test_agent_gate.py::CapabilityGateTests::test_selected_input_keeps_selected_provenance_after_replanning \
  tests/test_agent_gate.py::CapabilityGateTests::test_clarification_marker_preserves_previous_action_against_reroute \
  tests/test_dataset_bundles.py \
  -q
```

Expected: all selected tests pass, proving clarification behavior is isolated while coherent-bundle autofill remains enabled.

- [ ] **Step 5: Commit the stable fixtures**

```bash
git add tests/test_agent_gate.py
git commit -m "test: isolate clarification fixtures"
```

---

### Task 2: Add Strict Derived Recovery Provenance

**Files:**
- Modify: `tests/test_agent_gate.py`
- Modify: `scripts/netzoo_agent_core/contracts.py`
- Modify: `scripts/netzoo_agent_core/evaluation/recovery.py`
- Modify: `scripts/netzoo_agent_core/evaluation/plan_rules.py`
- Modify: `scripts/netzoo_agent_core/evaluation/plan_review.py`

**Interfaces:**
- Consumes: the existing `InputEvidence`, `WorkflowPlan`, `TaskDecision`, and `_evidence_contract_failures(evidence, user_task)` compatibility seam.
- Produces: private `_derived_evidence_contract_failures(plan: WorkflowPlan, decision: TaskDecision) -> list[str]`; the historical helper signature remains unchanged.

- [ ] **Step 1: Change the valid recovery assertion to require derived evidence**

In `test_recovered_plan_is_authorized_by_the_same_plan_evaluator`, change only:

```python
        self.assertEqual(expression_evidence.status, "derived")
        self.assertIsNone(expression_evidence.bundle_id)
        self.assertEqual(expression_evidence.candidates, [])
```

Keep the existing assertion that the recovered plan is approved and the evidence value matches `recovered.decision["expression_file"]`.

- [ ] **Step 2: Add tests rejecting fabricated and mismatched derived evidence**

Add these methods beside the existing recovery evaluator tests:

```python
    def test_initial_plan_cannot_claim_derived_input(self):
        task = "用 expression.tsv、motif.tsv、ppi.tsv、mirna.txt 跑 PUMA，輸出 out.tsv"
        decision = agent.TaskDecision(
            action="run_puma",
            in_scope=True,
            should_execute=True,
            intent_type="run_analysis",
            confidence=0.99,
            reason="run PUMA",
            expression_file="expression.tsv",
            motif_file="motif.tsv",
            ppi_file="ppi.tsv",
            mirna_file="mirna.txt",
            output_file="out.tsv",
        )
        plan = agent.build_workflow_plan(decision, task)
        expression_evidence = next(
            item for item in plan.evidence if item.field == "expression_file"
        )
        expression_evidence.status = "derived"
        expression_evidence.reason = "forged recovery provenance"

        evaluation = agent.evaluate_workflow_plan(plan, task)

        self.assertEqual(evaluation.status, "rejected")
        failed = {
            item.criterion for item in evaluation.rubric if item.result == "fail"
        }
        self.assertIn("evidence_provenance_contract", failed)

    def test_recovery_rejects_derived_output_mismatched_with_format_step(self):
        task = "用 expression.tsv、motif.tsv、ppi.tsv、mirna.txt 跑 PUMA，輸出 out.tsv"
        decision = agent.TaskDecision(
            action="run_puma",
            in_scope=True,
            should_execute=True,
            intent_type="run_analysis",
            confidence=0.99,
            reason="run PUMA",
            expression_file="expression.tsv",
            motif_file="motif.tsv",
            ppi_file="ppi.tsv",
            mirna_file="mirna.txt",
            output_file="out.tsv",
        )
        plan = agent.build_workflow_plan(decision, task)
        recovered, _ = agent.recover_workflow_plan(
            plan,
            1,
            agent.EvaluationResult(
                status="replan",
                reason="PUMA rejected an expression header.",
                recovery_action="format_expression_headerless",
            ),
        )
        recovered.steps[1].arguments["output_file"] = "outputs/forged.tsv"

        evaluation = agent.evaluate_workflow_plan(recovered, task)

        self.assertEqual(
            next(
                item for item in recovered.evidence
                if item.field == "expression_file"
            ).status,
            "derived",
        )
        self.assertEqual(evaluation.status, "rejected")
        failed = {
            item.criterion for item in evaluation.rubric if item.result == "fail"
        }
        self.assertIn("evidence_provenance_contract", failed)
```

- [ ] **Step 3: Run the recovery tests to verify the new contract is red**

Run:

```bash
pytest tests/test_agent_gate.py -k \
  'recovered_plan_is_authorized or initial_plan_cannot_claim_derived or recovery_rejects_derived_output' \
  -q
```

Expected: failures because `derived` is not yet an allowed evidence status, recovery still writes `discovered`, and there is no plan-aware derived validator.

- [ ] **Step 4: Add `derived` to the evidence model**

In `InputEvidence.status` in `scripts/netzoo_agent_core/contracts.py`, add the literal after `discovered`:

```python
        "discovered",
        "derived",
        "demo_bundle",
```

Do not change any other contract field or default.

- [ ] **Step 5: Mark recovery output as derived and clear stale provenance**

In both branches that create or update expression evidence in `recover_workflow_plan()`, use:

```python
                status="derived",
```

and for the existing evidence branch use:

```python
        expression_evidence.status = "derived"
        expression_evidence.value = derived
        expression_evidence.reason = recovery_reason
        expression_evidence.candidates = []
        expression_evidence.bundle_id = None
```

The new-evidence branch may rely on the model defaults for `candidates=[]` and `bundle_id=None`.

- [ ] **Step 6: Validate derived shape without changing the historical helper signature**

Add this branch to `_evidence_contract_failures()` in `plan_rules.py`, immediately after the `discovered` branch:

```python
        elif item.status == "derived":
            if (
                not item.value
                or not item.reason
                or item.bundle_id is not None
                or item.candidates
            ):
                failures.append(
                    f"{item.field} has malformed derived-input provenance"
                )
```

Keep its existing signature exactly:

```python
def _evidence_contract_failures(
    evidence: list[InputEvidence],
    user_task: str,
) -> list[str]:
```

- [ ] **Step 7: Add the private plan-aware derived validator**

Add below `_evidence_contract_failures()` in `plan_rules.py`:

```python
def _derived_evidence_contract_failures(
    plan: WorkflowPlan,
    decision: TaskDecision,
) -> list[str]:
    derived = [item for item in plan.evidence if item.status == "derived"]
    if not derived:
        return []

    failures: list[str] = []
    if len(derived) != 1:
        failures.append("a recovery plan must contain exactly one derived input")
    item = derived[0]
    index = plan.recovery_step_index
    format_step = (
        plan.steps[index]
        if index is not None and 0 <= index < len(plan.steps)
        else None
    )
    if (
        plan.recovery_action != "format_expression_headerless"
        or decision.action != "run_puma"
        or item.field != "expression_file"
    ):
        failures.append(
            "derived input is not authorized by PUMA header-removal recovery"
        )
    if item.value != decision.expression_file:
        failures.append("derived expression does not match the plan decision")
    if (
        format_step is None
        or format_step.action != "format_expression"
        or format_step.arguments.get("output_file") != item.value
    ):
        failures.append(
            "derived expression does not match the recovery format output"
        )
    return failures
```

Do not export this helper from `evaluation/__init__.py` or `scripts/netzoo_agent.py`.

- [ ] **Step 8: Combine derived failures under the existing provenance rubric**

Import the new helper in `plan_review.py`:

```python
    _derived_evidence_contract_failures,
```

Replace the local provenance calculation with:

```python
    provenance_failures = []
    if local_data_action:
        provenance_failures.extend(
            _evidence_contract_failures(plan.evidence, user_task)
        )
        provenance_failures.extend(
            _derived_evidence_contract_failures(plan, decision)
        )
```

Keep the rubric criterion name `evidence_provenance_contract` and all existing pass/fail text unchanged.

- [ ] **Step 9: Run focused recovery and compatibility tests**

Run:

```bash
python -m compileall -q scripts/netzoo_agent_core
pytest tests/test_agent_gate.py -k \
  'recovery or evidence_provenance or dataset_bundle_provenance' \
  -q
pytest tests/test_evaluation_package.py tests/test_dataset_bundles.py -q
```

Expected: all selected tests pass; `test_historical_evaluation_surface_is_preserved` confirms no public export changed.

- [ ] **Step 10: Commit the provenance contract**

```bash
git add \
  tests/test_agent_gate.py \
  scripts/netzoo_agent_core/contracts.py \
  scripts/netzoo_agent_core/evaluation/recovery.py \
  scripts/netzoo_agent_core/evaluation/plan_rules.py \
  scripts/netzoo_agent_core/evaluation/plan_review.py
git commit -m "fix: validate derived recovery provenance"
```

---

### Task 3: Render Derived Inputs Explicitly

**Files:**
- Modify: `tests/test_evaluation_package.py`
- Modify: `scripts/netzoo_agent_core/evaluation/rendering.py`

**Interfaces:**
- Consumes: `InputEvidence(status="derived")` and `render_compact_execution_response(plan, results, evaluation) -> str`.
- Produces: the stable user-visible source label `derived input`.

- [ ] **Step 1: Add a failing rendering test**

Append to `tests/test_evaluation_package.py`:

```python
def test_compact_response_labels_derived_input():
    decision = legacy_agent.TaskDecision(
        action="run_puma",
        in_scope=True,
        should_execute=True,
        confidence=1.0,
        reason="recovered PUMA",
        expression_file="outputs/expression.puma-expression.tsv",
    )
    plan = legacy_agent.WorkflowPlan(
        workflow="PUMA",
        objective=decision.reason,
        decision=decision.model_dump(),
        evidence=[
            legacy_agent.InputEvidence(
                field="expression_file",
                status="derived",
                value="outputs/expression.puma-expression.tsv",
                reason="Created by bounded header-removal recovery.",
            )
        ],
        steps=[
            legacy_agent.WorkflowStep(
                action="run_puma",
                purpose="Retry PUMA.",
            )
        ],
        status="ready",
    )

    response = evaluation.render_compact_execution_response(
        plan,
        [],
        legacy_agent.EvaluationResult(status="completed", reason="done"),
    )

    assert "[derived input]" in response
```

- [ ] **Step 2: Run the rendering test to verify it fails**

Run:

```bash
pytest tests/test_evaluation_package.py::test_compact_response_labels_derived_input -q
```

Expected: failure because the current fallback label is `[derived]`.

- [ ] **Step 3: Add the explicit rendering label**

In the evidence source mapping in `render_compact_execution_response()`, add:

```python
                "derived": "derived input",
```

Place it immediately after the `discovered` mapping.

- [ ] **Step 4: Run rendering and evaluation tests**

Run:

```bash
pytest tests/test_evaluation_package.py tests/test_agent_stability.py -q
```

Expected: all tests pass, including the user-owned stability additions already present in the working tree.

- [ ] **Step 5: Commit the rendering contract**

Stage only the two planned files; do not stage the existing unrelated changes in `tests/test_agent_stability.py`:

```bash
git add \
  tests/test_evaluation_package.py \
  scripts/netzoo_agent_core/evaluation/rendering.py
git commit -m "feat: label derived recovery inputs"
```

---

### Task 4: Full Verification and Finishing Workflow

**Files:**
- Verify: all repository tests
- Verify only: unrelated dirty-worktree files

**Interfaces:**
- Consumes: the completed clarification, provenance, and rendering commits.
- Produces: a zero-failure suite and evidence suitable for `finishing-a-development-branch`.

- [ ] **Step 1: Verify compilation, whitespace, and planned scope**

Run:

```bash
python -m compileall -q scripts/netzoo_agent_core scripts/netzoo_agent.py
git diff --check
git diff --cached --name-only
git status --short
```

Expected: compilation succeeds, no whitespace errors, staging is empty, and all unrelated dirty-worktree entries remain unstaged and unchanged.

- [ ] **Step 2: Run focused integration coverage**

Run:

```bash
pytest \
  tests/test_agent_gate.py \
  tests/test_evaluation_package.py \
  tests/test_dataset_bundles.py \
  tests/test_planning_package.py \
  tests/test_interpretation_package.py \
  tests/test_graph_package.py \
  tests/test_graph_tracing.py \
  tests/test_agent_stability.py \
  -q
```

Expected: zero failures.

- [ ] **Step 3: Run the complete suite**

Run:

```bash
pytest -q
```

Expected: zero failures. Skips and the existing `pytz` deprecation warning are acceptable; the four formerly documented failures must now pass.

- [ ] **Step 4: Verify the final commit range and repository hygiene**

Use the design commit as the range base:

```bash
git diff --check 823c363..HEAD
git diff --cached --name-only
git log --oneline 823c363..HEAD
git status --short
```

Expected: only the design correction, plan, and three implementation commits appear in the range; staging is empty; unrelated dirty entries are unchanged.

- [ ] **Step 5: Invoke `finishing-a-development-branch`**

Read and follow:

```text
/Users/chenzhonghan/.codex/skills/finishing-a-development-branch/SKILL.md
```

The skill will re-run the full suite. Expected: green, then it detects the repository environment and presents its exact integration menu. Stop and wait for the user's integration choice; do not merge, push, create a PR, or clean up without that choice.

- [ ] **Step 6: Report completion evidence**

Report:

- the root causes and chosen repair;
- focused and full test counts;
- public evaluation facade compatibility;
- coherent-bundle regression result;
- implementation commit hashes;
- unchanged unrelated dirty-worktree entries; and
- the pending or completed integration choice from the finishing skill.

Do not create a verification-only commit.
