# Requested Outcome Capability Matching Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make workflow recommendation and execution depend on a typed match between the user's requested deliverable and registry-owned workflow output contracts, so related-but-incompatible requests stop with a capability explanation instead of a false recommendation.

**Architecture:** The Router extracts a bounded `RequestedOutcome`; it does not own scientific workflow selection. A pure deterministic matcher compares that outcome with `OutputCapabilityDefinition` metadata in the Python workflow registry, while versioned YAML mirrors and validates the same contracts. Exact matches may populate code-owned workflow guidance; ambiguous and unsupported matches go through deterministic clarification or capability-gap renderers, and alternatives never authorize planning or execution.

**Tech Stack:** Python 3.12, Pydantic v2, LangGraph-compatible structured routing, PyYAML, pytest/unittest, existing NetZoo workflow registry and CLI contracts.

## Global Constraints

- Match typed requested deliverables, not isolated words or workflow-specific phrase lists.
- Router output alone cannot recommend or authorize a local run workflow.
- Unknown or unresolved outcome dimensions cannot become an exact match.
- `matched_actions` contains exact end-to-end actions; `recommended_actions` is a code-owned explanation sequence; `alternative_actions` is explanatory only.
- Alternative actions must never reach planning, execution, or Plan Evaluator approval.
- Explicit named-workflow purpose/input questions must continue to work unless they also request a conflicting deliverable.
- Provider failure must narrow behavior and must not infer unnamed scientific goals from loose keyword combinations.
- Existing required-input gates, policy hashing, `/test` versus `/execute`, and Plan Evaluator rules remain unchanged.
- Policy contracts migrate from version 1 to version 2; version 1 must not be silently reinterpreted.
- Preserve all pre-existing user work in the dirty worktree and stage only files listed by the current task.

---

## File Structure

- Create `scripts/netzoo_agent_core/contracts/outcomes.py`: bounded requested-outcome and capability-match Pydantic models.
- Create `scripts/netzoo_agent_core/routing/outcome_matching.py`: pure deterministic matching, alternative ranking, and guidance expansion.
- Modify `scripts/workflow_registry.py`: code-owned output capability definitions for every run action.
- Modify `scripts/netzoo_agent_core/contracts/__init__.py`: stable exports for outcome contracts.
- Modify `scripts/netzoo_agent_core/contracts/decisions.py`: carry typed outcome and match fields in `RouterDecision` and `TaskDecision`.
- Modify `scripts/netzoo_agent_core/contracts/policy.py`: version 2 policy and YAML output-capability schema.
- Modify `scripts/netzoo_agent_core/policy.py`: fail-closed YAML/Python capability validation and Router catalog rendering.
- Modify `AGENTS.md` and `workflows/*.yaml`: version 2 workflow output contracts.
- Modify `scripts/netzoo_agent_core/llm.py`: ask the Router to extract outcome semantics without inventing a supported goal.
- Modify `scripts/netzoo_agent_core/interpretation/hydration.py`: copy the typed outcome but initialize match fields as code-owned empty state.
- Modify `scripts/netzoo_agent_core/interpretation/repair.py`: apply deterministic match results and remove semantic keyword promotion.
- Modify `scripts/netzoo_agent_core/interpretation/provider_fallback.py`: support only explicit named workflows when provider semantics are unavailable.
- Modify `scripts/netzoo_agent_core/routing/capability.py`: gate local runs against `matched_actions` and remove the broad advisory fallback.
- Modify `scripts/netzoo_agent_core/routing/__init__.py`: export the matcher interfaces while preserving intentional compatibility exports.
- Modify `scripts/netzoo_agent_core/graph/routing_planning.py`: persist and trace trusted outcome/match state instead of model-selected candidates.
- Modify `scripts/netzoo_agent_core/interpretation/semantic_goal.py`: render public summaries from typed match facts.
- Modify `scripts/netzoo_agent_core/interpretation/concept_answers.py`: render unsupported and ambiguous outcome responses deterministically.
- Modify `scripts/netzoo_agent_core/graph/response.py`: select the new renderers before generic LLM response generation.
- Modify `scripts/netzoo_agent_core/contracts/state.py` and `scripts/netzoo_agent_core/cli/follow_up.py`: distinguish clarification, alternative confirmation, and exact recommendation follow-ups.
- Modify `scripts/netzoo_agent_core/progress_summaries.py`: state capability gaps accurately in the timeline.
- Create `tests/test_outcome_matching.py`: table-driven matcher and registry guidance tests.
- Create `tests/test_outcome_routing.py`: Router/graph contract and language-variation regression coverage without modifying the user's existing dirty graph-tracing test file.
- Modify `tests/test_agent_gate.py`, `tests/test_progress_summaries.py`, `tests/test_concept_answers.py`, `tests/test_routing_package.py`, and `tests/test_interpretation_package.py`: routing, response, fallback, package-surface, and regression coverage.
- Modify `AGENT_USAGE.md` and `NETZOO_HARNESS_ARCHITECTURE.md`: document typed matching and mismatch behavior.

---

### Task 1: Add the Typed Outcome Domain and Pure Capability Matcher

**Files:**
- Create: `scripts/netzoo_agent_core/contracts/outcomes.py`
- Create: `scripts/netzoo_agent_core/routing/outcome_matching.py`
- Create: `tests/test_outcome_matching.py`
- Modify: `scripts/workflow_registry.py`
- Modify: `scripts/netzoo_agent_core/contracts/__init__.py`
- Modify: `scripts/netzoo_agent_core/routing/__init__.py`
- Modify: `tests/test_routing_package.py`

**Interfaces:**
- Produces: `RequestedOutcome`, `CapabilityMatch`, and `CapabilityMatchStatus` Pydantic contracts.
- Produces: `OutputCapabilityDefinition` and `OUTPUT_CAPABILITIES` in `workflow_registry.py`.
- Produces: `match_requested_outcome(outcome, capabilities=OUTPUT_CAPABILITIES) -> CapabilityMatch`.
- Produces: `guidance_actions_for(action: RecommendedAction) -> list[RecommendedAction]`.
- Consumes: existing `ActionName`, `RecommendedAction`, `RUN_ACTIONS`, and registry action ordering.

- [ ] **Step 1: Write failing model and matcher tests**

Create `tests/test_outcome_matching.py` with explicit exact, ambiguous, unsupported, alternative, and guidance expectations:

```python
from netzoo_agent_core.contracts import RequestedOutcome
from netzoo_agent_core.routing import (
    guidance_actions_for,
    match_requested_outcome,
)


def outcome(**updates):
    values = {
        "operation": "infer",
        "artifact_type": "regulatory_network",
        "entity_types": ["mirna", "gene"],
        "display_entities": ["miRNA", "gene"],
        "regulator_types": ["mirna"],
        "target_types": ["gene"],
        "granularity": "sample_specific",
        "unresolved_dimensions": [],
    }
    values.update(updates)
    return RequestedOutcome(**values)


def test_sample_specific_mirna_regulatory_network_matches_lioness_puma():
    result = match_requested_outcome(outcome())
    assert result.status == "exact"
    assert result.matched_actions == ["run_lioness_puma"]
    assert result.alternative_actions == []
    assert guidance_actions_for("run_lioness_puma") == [
        "run_puma",
        "run_lioness_puma",
    ]


def test_sample_specific_mirna_measurements_are_not_a_workflow_match():
    result = match_requested_outcome(
        outcome(
            operation="acquire",
            artifact_type="measurement_dataset",
            regulator_types=[],
            target_types=[],
        )
    )
    assert result.status == "unsupported"
    assert result.matched_actions == []
    assert result.alternative_actions[0] == "run_lioness_puma"
    assert "operation" in result.mismatch_dimensions
    assert "artifact_type" in result.mismatch_dimensions


def test_unknown_artifact_stays_ambiguous_instead_of_matching():
    result = match_requested_outcome(
        outcome(artifact_type="unknown", unresolved_dimensions=["requested artifact"])
    )
    assert result.status == "ambiguous"
    assert result.matched_actions == []
    assert result.clarification_question is not None


def test_multiple_end_to_end_matches_require_a_selection_dimension():
    result = match_requested_outcome(
        outcome(
            entity_types=["gene"],
            display_entities=["gene"],
            regulator_types=[],
        )
    )
    assert result.status == "ambiguous"
    assert result.matched_actions == []
    assert "regulator type" in result.clarification_question


def test_unrelated_entity_has_no_suggested_alternative():
    result = match_requested_outcome(
        outcome(
            operation="acquire",
            artifact_type="measurement_dataset",
            entity_types=["protein"],
            display_entities=["protein abundance"],
            regulator_types=[],
            target_types=[],
        )
    )
    assert result.status == "unsupported"
    assert result.alternative_actions == []
```

- [ ] **Step 2: Run the new tests and verify import failures**

Run:

```bash
python -m pytest tests/test_outcome_matching.py -q
```

Expected: collection fails because `RequestedOutcome`, `match_requested_outcome`, and `guidance_actions_for` do not exist.

- [ ] **Step 3: Add code-owned output capability definitions**

In `scripts/workflow_registry.py`, add the shared literals and immutable definition before `ActionDefinition`:

```python
Operation = Literal["acquire", "prepare", "validate", "infer", "analyze", "explain", "unknown"]
ArtifactType = Literal[
    "measurement_dataset",
    "expression_matrix",
    "regulatory_network",
    "coexpression_network",
    "community_assignment",
    "validation_report",
    "unknown",
]
EntityType = Literal["tf", "mirna", "gene", "protein", "sample", "unknown"]
Granularity = Literal["aggregate", "sample_specific", "not_applicable", "unknown"]


@dataclass(frozen=True, slots=True)
class OutputCapabilityDefinition:
    operation: Literal["infer", "analyze"]
    artifact_type: ArtifactType
    entity_types: frozenset[EntityType]
    granularities: frozenset[Granularity]
    regulator_types: frozenset[Literal["tf", "mirna"]] = frozenset()
    target_types: frozenset[Literal["gene"]] = frozenset()
    guidance_predecessors: tuple[RecommendedAction, ...] = ()
```

Add `output_capability: OutputCapabilityDefinition | None = None` to `ActionDefinition`, then populate all six run actions. Use these exact values:

```python
run_panda = OutputCapabilityDefinition(
    operation="infer",
    artifact_type="regulatory_network",
    entity_types=frozenset({"tf", "gene"}),
    regulator_types=frozenset({"tf"}),
    target_types=frozenset({"gene"}),
    granularities=frozenset({"aggregate"}),
)
run_puma = OutputCapabilityDefinition(
    operation="infer",
    artifact_type="regulatory_network",
    entity_types=frozenset({"tf", "mirna", "gene"}),
    regulator_types=frozenset({"tf", "mirna"}),
    target_types=frozenset({"gene"}),
    granularities=frozenset({"aggregate"}),
)
run_lioness_panda = OutputCapabilityDefinition(
    operation="infer",
    artifact_type="regulatory_network",
    entity_types=frozenset({"tf", "gene"}),
    regulator_types=frozenset({"tf"}),
    target_types=frozenset({"gene"}),
    granularities=frozenset({"aggregate", "sample_specific"}),
    guidance_predecessors=("run_panda",),
)
run_lioness_puma = OutputCapabilityDefinition(
    operation="infer",
    artifact_type="regulatory_network",
    entity_types=frozenset({"tf", "mirna", "gene"}),
    regulator_types=frozenset({"tf", "mirna"}),
    target_types=frozenset({"gene"}),
    granularities=frozenset({"aggregate", "sample_specific"}),
    guidance_predecessors=("run_puma",),
)
run_lioness_coexpression = OutputCapabilityDefinition(
    operation="infer",
    artifact_type="coexpression_network",
    entity_types=frozenset({"gene"}),
    granularities=frozenset({"aggregate", "sample_specific"}),
)
run_condor = OutputCapabilityDefinition(
    operation="analyze",
    artifact_type="community_assignment",
    entity_types=frozenset({"gene"}),
    granularities=frozenset({"not_applicable"}),
)
```

Expose only run definitions through:

```python
OUTPUT_CAPABILITIES = {
    action: definition.output_capability
    for action, definition in ACTION_DEFINITIONS.items()
    if definition.run and definition.output_capability is not None
}
```

- [ ] **Step 4: Add strict Pydantic outcome contracts**

Create `scripts/netzoo_agent_core/contracts/outcomes.py` using `ConfigDict(extra="forbid")`. Define `RequestedOutcome` with all fields required except bounded lists, and define:

```python
CapabilityMatchStatus = Literal["exact", "ambiguous", "unsupported"]


class CapabilityMatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: CapabilityMatchStatus
    matched_actions: list[RecommendedAction] = Field(default_factory=list, max_length=6)
    alternative_actions: list[RecommendedAction] = Field(default_factory=list, max_length=2)
    mismatch_dimensions: list[str] = Field(default_factory=list, max_length=5)
    clarification_question: str | None = Field(default=None, max_length=300)
```

Export both models through `contracts/__init__.py` and include the module in `_CONTRACT_IMPLEMENTATION_MODULES` so compatibility patching sees the new contract owner.

- [ ] **Step 5: Implement the pure matcher**

Create `routing/outcome_matching.py`. Keep exact matching and alternative ranking separate. The exact predicate must reject unknowns and unresolved dimensions:

```python
def _matches(outcome: RequestedOutcome, capability: OutputCapabilityDefinition) -> bool:
    if outcome.unresolved_dimensions:
        return False
    if "unknown" in {
        outcome.operation,
        outcome.artifact_type,
        outcome.granularity,
    }:
        return False
    return (
        outcome.operation == capability.operation
        and outcome.artifact_type == capability.artifact_type
        and outcome.granularity in capability.granularities
        and set(outcome.entity_types).issubset(capability.entity_types)
        and set(outcome.regulator_types).issubset(capability.regulator_types)
        and set(outcome.target_types).issubset(capability.target_types)
    )
```

For alternatives, require non-empty overlap between known `entity_types` and the capability. Score two points for requested granularity support, two points per overlapping entity, one point per overlapping regulator type, and one point per overlapping target type. Sort by descending score then registry insertion order and return at most two actions.

Return `ambiguous` when a capability-relevant scalar or list contains `unknown`,
when `unresolved_dimensions` is non-empty, or when more than one end-to-end
action matches and registry metadata does not identify one as the selected
action's guidance predecessor. Do not expose those possible actions through
`matched_actions`; return one minimal selection question instead. Return
`unsupported` when every field is known but no exact action exists. Populate
`mismatch_dimensions` by comparing the request with all capabilities, not by
inspecting original words.

Implement guidance expansion as:

```python
def guidance_actions_for(action: RecommendedAction) -> list[RecommendedAction]:
    capability = OUTPUT_CAPABILITIES[action]
    return [*capability.guidance_predecessors, action]
```

- [ ] **Step 6: Update routing exports and package characterization**

Export `match_requested_outcome` and `guidance_actions_for` from `routing/__init__.py`. Add `outcome_matching` to the imported routing modules and append both names to `HISTORICAL_EXPORTS` in `tests/test_routing_package.py`; the legacy facade must expose the same objects.

- [ ] **Step 7: Run focused tests**

Run:

```bash
python -m pytest tests/test_outcome_matching.py tests/test_routing_package.py -q
```

Expected: all tests pass.

- [ ] **Step 8: Commit the domain core**

```bash
git add scripts/workflow_registry.py scripts/netzoo_agent_core/contracts/outcomes.py scripts/netzoo_agent_core/contracts/__init__.py scripts/netzoo_agent_core/routing/outcome_matching.py scripts/netzoo_agent_core/routing/__init__.py tests/test_outcome_matching.py tests/test_routing_package.py
git commit -m "feat: add typed workflow outcome matching"
```

---

### Task 2: Migrate Workflow Policy to Version 2 Output Contracts

**Files:**
- Modify: `scripts/netzoo_agent_core/contracts/policy.py`
- Modify: `scripts/netzoo_agent_core/policy.py`
- Modify: `AGENTS.md`
- Modify: `workflows/condor.yaml`
- Modify: `workflows/lioness-coexpression.yaml`
- Modify: `workflows/lioness-panda.yaml`
- Modify: `workflows/lioness-puma.yaml`
- Modify: `workflows/panda.yaml`
- Modify: `workflows/puma.yaml`
- Modify: `tests/test_agent_gate.py`

**Interfaces:**
- Consumes: `OutputCapabilityDefinition` and `ACTION_DEFINITIONS[action].output_capability` from Task 1.
- Produces: `WorkflowOutputCapabilitySpec` and version 2 `WorkflowPolicySpec`.
- Produces: fail-closed equality validation between YAML and Python capability definitions.

- [ ] **Step 1: Add failing policy-version and capability-consistency tests**

In the existing `ProjectPolicyTests` section of `tests/test_agent_gate.py`, change the loaded-policy assertion to `policy_version == 2` and add:

```python
def test_every_workflow_policy_matches_python_output_capability(self):
    policy = agent.ProjectPolicyLoader(PROJECT_ROOT).load()
    for action, spec in policy.workflows.items():
        definition = agent.ACTION_DEFINITIONS[action].output_capability
        assert definition is not None
        assert spec.output_capability.operation == definition.operation
        assert spec.output_capability.artifact_type == definition.artifact_type
        assert set(spec.output_capability.entity_types) == set(definition.entity_types)
        assert set(spec.output_capability.granularities) == set(definition.granularities)

def test_policy_rejects_version_one_after_capability_migration(self):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / ".git").mkdir()
        (root / "AGENTS.md").write_text(
            "---\npolicy_version: 1\nproject: old\nworkflow_spec_dir: workflows\n---\n",
            encoding="utf-8",
        )
        with self.assertRaises(agent.ProjectPolicyError):
            agent.ProjectPolicyLoader(root).load()
```

Extend the existing YAML/Python conflict fixture with an `output_capability` mismatch and assert the error contains `output_capability conflict`.

- [ ] **Step 2: Run policy tests and verify version/capability failures**

Run:

```bash
python -m pytest tests/test_agent_gate.py -k "policy" -q
```

Expected: failures show version 1 and missing `output_capability` are still accepted by the old schema.

- [ ] **Step 3: Add the version 2 policy schema**

In `contracts/policy.py`, define `WorkflowOutputCapabilitySpec` with list fields matching the registry definition and `extra="forbid"`. Change all three policy model versions from `Literal[1]` to `Literal[2]`, and add `output_capability: WorkflowOutputCapabilitySpec` to `WorkflowPolicySpec`.

Use these fields:

```python
class WorkflowOutputCapabilitySpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation: Literal["infer", "analyze"]
    artifact_type: ArtifactType
    entity_types: list[EntityType] = Field(max_length=8)
    granularities: list[Granularity] = Field(max_length=3)
    regulator_types: list[Literal["tf", "mirna"]] = Field(default_factory=list, max_length=2)
    target_types: list[Literal["gene"]] = Field(default_factory=list, max_length=1)
    guidance_predecessors: list[RecommendedAction] = Field(default_factory=list, max_length=2)
```

- [ ] **Step 4: Validate YAML capability equality against Python**

In `ProjectPolicyLoader._validate_against_code`, normalize the YAML lists to frozensets/tuple and compare the entire value with `definition.output_capability`. Reject absent code metadata and any mismatch with an action-specific message:

```python
yaml_capability = OutputCapabilityDefinition(
    operation=spec.output_capability.operation,
    artifact_type=spec.output_capability.artifact_type,
    entity_types=frozenset(spec.output_capability.entity_types),
    granularities=frozenset(spec.output_capability.granularities),
    regulator_types=frozenset(spec.output_capability.regulator_types),
    target_types=frozenset(spec.output_capability.target_types),
    guidance_predecessors=tuple(spec.output_capability.guidance_predecessors),
)
if yaml_capability != definition.output_capability:
    raise ProjectPolicyError(
        f"{action} output_capability conflict with Python: "
        f"yaml={yaml_capability}, code={definition.output_capability}."
    )
```

Extend `router_capability_summary()` to include operation, artifact, entities, regulator roles, target roles, and granularities from the validated spec. Do not derive the Router catalog from prose descriptions alone.

- [ ] **Step 5: Migrate AGENTS.md and all workflow YAML files**

Change `policy_version: 1` to `policy_version: 2` in `AGENTS.md` and all six YAML files. Add `output_capability` values exactly matching Task 1. For example, `workflows/lioness-puma.yaml` gains:

```yaml
output_capability:
  operation: infer
  artifact_type: regulatory_network
  entity_types: [tf, mirna, gene]
  granularities: [aggregate, sample_specific]
  regulator_types: [tf, mirna]
  target_types: [gene]
  guidance_predecessors: [run_puma]
```

Use empty YAML lists for role fields that do not apply. For CONDOR use `operation: analyze`, `artifact_type: community_assignment`, `entity_types: [gene]`, and `granularities: [not_applicable]`.

- [ ] **Step 6: Run policy and registry tests**

Run:

```bash
python -m pytest tests/test_agent_gate.py -k "policy or workflow_registry" -q
```

Expected: all selected tests pass and policy hash generation still succeeds.

- [ ] **Step 7: Commit policy version 2**

```bash
git add AGENTS.md workflows/condor.yaml workflows/lioness-coexpression.yaml workflows/lioness-panda.yaml workflows/lioness-puma.yaml workflows/panda.yaml workflows/puma.yaml scripts/netzoo_agent_core/contracts/policy.py scripts/netzoo_agent_core/policy.py tests/test_agent_gate.py
git commit -m "feat: validate workflow output capabilities"
```

---

### Task 3: Make Router Semantics Descriptive and Matcher Decisions Authoritative

**Files:**
- Modify: `scripts/netzoo_agent_core/contracts/decisions.py`
- Modify: `scripts/netzoo_agent_core/llm.py`
- Modify: `scripts/netzoo_agent_core/interpretation/hydration.py`
- Modify: `scripts/netzoo_agent_core/interpretation/repair.py`
- Modify: `scripts/netzoo_agent_core/interpretation/provider_fallback.py`
- Modify: `scripts/netzoo_agent_core/routing/capability.py`
- Modify: `scripts/netzoo_agent_core/graph/routing_planning.py`
- Modify: `scripts/netzoo_agent_core/contracts/state.py`
- Modify: `scripts/netzoo_agent_core/interpretation/semantic_goal.py`
- Modify: `tests/test_agent_gate.py`
- Create: `tests/test_outcome_routing.py`
- Modify: `tests/test_interpretation_package.py`

**Interfaces:**
- Consumes: `RequestedOutcome`, `CapabilityMatch`, `match_requested_outcome`, and `guidance_actions_for` from Task 1.
- Produces: Router-owned `requested_outcome` and code-owned `matched_actions`, `recommended_actions`, `alternative_actions`, and `capability_match_status`.
- Produces: `apply_outcome_match(decision: TaskDecision) -> TaskDecision` as the single deterministic decision-enrichment seam.
- Preserves: `repair_router_decision(raw_decision, task) -> TaskDecision` public signature.

- [ ] **Step 1: Replace the false-positive regression and add authority tests**

Replace `test_sample_specific_mirna_guidance_recommends_puma_and_lioness` in `tests/test_agent_gate.py` with:

```python
def test_sample_specific_mirna_data_is_not_promoted_to_network_guidance(self):
    task = "if i want to get sample specific mi-RNA data, what tools do i need?"
    raw = agent.TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=0.99,
        reason="Guidance requested.",
        requested_outcome=agent.RequestedOutcome(
            operation="acquire",
            artifact_type="measurement_dataset",
            entity_types=["mirna"],
            display_entities=["miRNA"],
            regulator_types=[],
            target_types=[],
            granularity="sample_specific",
            unresolved_dimensions=[],
        ),
    )
    repaired = agent.repair_router_decision(raw, task)
    assert repaired.capability_match_status == "unsupported"
    assert repaired.matched_actions == []
    assert repaired.recommended_actions == []
    assert repaired.alternative_actions[0] == "run_lioness_puma"
    assert repaired.should_execute is False

def test_router_proposed_run_cannot_bypass_outcome_mismatch(self):
    decision = agent.TaskDecision(
        action="run_lioness_puma",
        in_scope=True,
        should_execute=True,
        intent_type="run_analysis",
        confidence=1.0,
        reason="model proposal",
        requested_outcome=measurement_outcome(),
        matched_actions=[],
        capability_match_status="unsupported",
    )
    gated = agent.enforce_capability_gate(decision, "download per-sample miRNA data")
    assert gated.action == "no_tool"
    assert "does not exactly match" in gated.reason
```

Add a direct goal-first test whose Router fixture returns a regulatory-network outcome and assert `matched_actions == ["run_lioness_puma"]`, `recommended_actions == ["run_puma", "run_lioness_puma"]`, and direct execution selects only `run_lioness_puma`.

- [ ] **Step 2: Run focused routing tests and verify old promotion remains**

Run:

```bash
python -m pytest tests/test_agent_gate.py -k "mirna_data or outcome_mismatch or goal_match" -q
```

Expected: the new mismatch and authority tests fail because decision contracts and repair do not contain typed match state.

- [ ] **Step 3: Change RouterDecision and TaskDecision contracts**

In `contracts/decisions.py`, remove Router-controlled `recommended_actions`, `candidate_actions`, and top-level `unresolved_dimensions`. Add:

```python
requested_outcome: RequestedOutcome | None = None
```

Keep `semantic_goal` only as a bounded human-readable summary during migration. Add these fields to `TaskDecision`:

```python
requested_outcome: RequestedOutcome | None = None
capability_match_status: CapabilityMatchStatus | None = None
matched_actions: list[RecommendedAction] = Field(default_factory=list)
alternative_actions: list[RecommendedAction] = Field(default_factory=list)
mismatch_dimensions: list[str] = Field(default_factory=list)
clarification_question: str | None = None
```

Keep the existing `recommended_actions` field but change its description to say
it is a code-owned guidance sequence. Update direct capability-gate fixtures,
including the shared PANDA `self.decision()` helper, so valid executable
decisions contain `matched_actions=[action]`; tests that intentionally model a
bad Router proposal must keep `matched_actions` empty.

Update Router fixtures in `tests/test_agent_gate.py` to supply
`requested_outcome` for goal-first requests and omit removed Router selection
fields. Put new graph-level fixtures in `tests/test_outcome_routing.py`; do not
edit the user's dirty `tests/test_graph_tracing.py`.

- [ ] **Step 4: Make the Router prompt extract requested outcomes**

In `llm.build_routing_prompt`, replace rule 5's direct workflow mapping with the typed vocabulary and these rules:

```text
Describe the scientific result the user requested in requested_outcome.
operation is the requested scientific operation, not whether the user phrased a question.
Use unknown and unresolved_dimensions when the artifact or granularity is not explicit.
Never reinterpret data acquisition as network inference merely because a related workflow exists.
The deterministic matcher selects workflows; do not select a local workflow from semantic similarity.
```

Update examples so the measurement-data question returns `no_tool` with `operation=acquire` and `artifact_type=measurement_dataset`, while the regulatory-network question returns `operation=infer` and `artifact_type=regulatory_network`.

- [ ] **Step 5: Hydrate descriptive fields without trusting recommendations**

In `hydrate_router_decision`, copy `route.requested_outcome` into `TaskDecision`, initialize all match/recommendation lists empty, and keep `should_execute` based on proposed action only until repair applies the match. Never copy an action list from Router output.

- [ ] **Step 6: Add the authoritative match application seam**

In `routing/outcome_matching.py`, add:

```python
def apply_outcome_match(decision: TaskDecision) -> TaskDecision:
    if decision.requested_outcome is None:
        return decision.model_copy(
            update={
                "matched_actions": [],
                "recommended_actions": [],
                "alternative_actions": [],
            }
        )
    match = match_requested_outcome(decision.requested_outcome)
    guidance = (
        guidance_actions_for(match.matched_actions[-1])
        if len(match.matched_actions) == 1
        else []
    )
    return decision.model_copy(
        update={
            "capability_match_status": match.status,
            "matched_actions": match.matched_actions,
            "recommended_actions": guidance,
            "alternative_actions": match.alternative_actions,
            "mismatch_dimensions": match.mismatch_dimensions,
            "clarification_question": match.clarification_question,
        }
    )
```

Export it from `routing/__init__.py` and update the package export characterization test.

- [ ] **Step 7: Replace keyword promotion in repair**

At the beginning of `repair_router_decision`, call `apply_outcome_match(raw_decision)`. Remove use of `infer_goal_capabilities()` and `infer_advisory_capabilities()` for unnamed goals. Apply these rules:

```python
if decision.capability_match_status in {"ambiguous", "unsupported"}:
    return decision.model_copy(update={"action": "no_tool", "should_execute": False})

if is_workflow_information_request(task):
    return decision.model_copy(
        update={"action": "no_tool", "intent_type": "answer_question", "should_execute": False}
    )

if (
    has_direct_execution_intent(task)
    and len(decision.matched_actions) == 1
):
    action = decision.matched_actions[0]
    repaired = decision.model_dump()
    repaired.update(
        {
            "action": action,
            "in_scope": True,
            "should_execute": True,
            "intent_type": "demo_run" if _is_demo_request(task) else "run_analysis",
            "confidence": max(decision.confidence, MIN_TOOL_CONFIDENCE),
            "reason": "The requested outcome exactly matches a registered workflow.",
        }
    )
    repaired["missing_inputs"] = [
        field_name
        for field_name in REQUIRED_INPUTS[action]
        if not repaired.get(field_name)
    ]
    return TaskDecision.model_validate(repaired)
```

Keep explicit workflow-name routing as a separate deterministic path. Resolve the exact registered name and set `matched_actions=[action]` plus `recommended_actions=guidance_actions_for(action)`. Before applying that exception, reject a non-`None` requested outcome whose explicit artifact or operation conflicts with the named capability.

For continuation markers, populate `matched_actions=[action]` so the gate can verify the resumed workflow without broadening authorization.

- [ ] **Step 8: Narrow provider fallback**

In `deterministic_router_fallback`, delete the sample-specific/miRNA advisory inference. For a named workflow information question, set the exact named action's match/guidance fields and return `no_tool`. For a named run request, set `matched_actions=[action]`. For an unnamed goal-first request, return:

```python
TaskDecision(
    action="no_tool",
    in_scope=True,
    should_execute=False,
    intent_type="unknown",
    confidence=1.0,
    reason="The provider failed and the requested outcome could not be normalized safely.",
    clarification_question=(
        "What result do you want NetZoo to produce: a regulatory network, "
        "a co-expression network, or community assignments?"
    ),
)
```

- [ ] **Step 9: Enforce exact matched action membership**

In `enforce_capability_gate`, before missing-input checks, reject any local run action absent from `decision.matched_actions`. Preserve all new match fields when constructing the blocking `TaskDecision`:

```python
if (
    decision.action in LOCAL_WORKFLOW_ACTIONS
    and decision.action not in decision.matched_actions
):
    rejection_reasons.append(
        "The selected workflow does not exactly match the requested deliverable."
    )
```

Delete the `infer_goal_capabilities` mutation at the start of the gate. Keep the legacy inference functions exported temporarily for external compatibility, but no production routing, repair, fallback, or gate path may call them.

Change `validate_task_text` to accept the backward-compatible keyword-only
parameter `matched_actions: Sequence[RecommendedAction] = ()`. Replace its call
to `inferred_execution_action(task)` with
`has_direct_execution_intent(task) and action in matched_actions`, and pass
`decision.matched_actions` from the gate. Existing two-argument callers remain
valid, while unnamed execution is authorized only by typed matching.

- [ ] **Step 10: Persist typed match state and update public summaries**

Add `requested_outcome` and `capability_match` keys to `AgentState`. In `classify_task`, derive both from the repaired `TaskDecision`; stop rebuilding candidates from `infer_goal_capability_match` or Router action lists. Store:

```python
capability_match = {
    "status": decision.capability_match_status,
    "matched_actions": decision.matched_actions,
    "alternative_actions": decision.alternative_actions,
    "mismatch_dimensions": decision.mismatch_dimensions,
    "clarification_question": decision.clarification_question,
}
```

Update `semantic_goal.public_semantic_summary` to say exact, ambiguous, or unsupported based only on these validated fields. It must never describe alternatives as matching candidates.

- [ ] **Step 11: Run routing, graph, and package tests**

Run:

```bash
python -m pytest tests/test_agent_gate.py tests/test_outcome_routing.py tests/test_interpretation_package.py tests/test_routing_package.py -k "router or routing or capability or goal or mirna or fallback or graph" -q
```

Expected: all selected tests pass. Confirm with `rg` that production modules outside legacy compatibility definitions no longer call `infer_advisory_capabilities`.

- [ ] **Step 12: Commit authoritative routing**

```bash
git add scripts/netzoo_agent_core/contracts/decisions.py scripts/netzoo_agent_core/contracts/state.py scripts/netzoo_agent_core/llm.py scripts/netzoo_agent_core/interpretation/hydration.py scripts/netzoo_agent_core/interpretation/repair.py scripts/netzoo_agent_core/interpretation/provider_fallback.py scripts/netzoo_agent_core/interpretation/semantic_goal.py scripts/netzoo_agent_core/routing/capability.py scripts/netzoo_agent_core/routing/outcome_matching.py scripts/netzoo_agent_core/routing/__init__.py scripts/netzoo_agent_core/graph/routing_planning.py tests/test_agent_gate.py tests/test_outcome_routing.py tests/test_interpretation_package.py tests/test_routing_package.py
git commit -m "fix: require exact outcome matches for routing"
```

---

### Task 4: Render Capability Gaps and Confirm Alternatives Safely

**Files:**
- Modify: `scripts/netzoo_agent_core/interpretation/concept_answers.py`
- Modify: `scripts/netzoo_agent_core/graph/response.py`
- Modify: `scripts/netzoo_agent_core/contracts/state.py`
- Modify: `scripts/netzoo_agent_core/cli/follow_up.py`
- Modify: `scripts/netzoo_agent_core/progress_summaries.py`
- Modify: `tests/test_concept_answers.py`
- Modify: `tests/test_progress_summaries.py`
- Modify: `tests/test_agent_gate.py`

**Interfaces:**
- Consumes: typed outcome/match fields on `TaskDecision` and validated policy specs.
- Produces: `render_outcome_clarification(...) -> str | None`.
- Produces: `render_capability_gap(...) -> str | None`.
- Produces: `NextTurnPrompt.kind` values `clarify_outcome` and `alternative_outcome`.
- Produces: safe `CONFIRMED_OUTCOME_ACTION=<action>` continuation that recommends but does not execute and rebuilds a typed outcome from the confirmed capability.

- [ ] **Step 1: Write failing deterministic response tests**

Add to `tests/test_concept_answers.py`:

```python
def test_measurement_request_explains_gap_before_offering_network():
    policy = ProjectPolicyLoader(PROJECT_ROOT).load()
    decision = mismatch_decision(
        alternative_actions=["run_lioness_puma"],
        mismatch_dimensions=["operation", "artifact_type"],
    )
    answer = render_capability_gap(decision, policy)
    assert "do not acquire sample-specific miRNA measurement data" in answer
    assert "can instead infer" in answer
    assert "LIONESS-PUMA" in answer
    assert "Did you mean" in answer
    assert "No files were inspected and no analysis ran." in answer

def test_ambiguous_outcome_asks_only_the_validated_question():
    decision = ambiguous_decision(
        clarification_question="Do you want measurement data or a regulatory network?"
    )
    assert render_outcome_clarification(decision) == (
        "I cannot select a workflow until the requested result is clear. "
        "Do you want measurement data or a regulatory network?\n\n"
        "No files were inspected and no analysis ran."
    )
```

Add a graph response test proving the generic response LLM is not called when
either deterministic renderer returns content. Use a response model that fails
if invoked:

```python
class FailingResponseLLM:
    def invoke(self, _messages):
        raise AssertionError("capability gaps must use deterministic rendering")


def test_capability_gap_bypasses_generic_response_model(monkeypatch, tmp_path):
    app = build_graph_with_router_outcome(
        tmp_path,
        requested_outcome=measurement_outcome(),
        response_llm=FailingResponseLLM(),
    )
    result = app.invoke({"messages": [HumanMessage(content="per-sample miRNA data")]})
    assert "do not acquire" in result["messages"][-1].content
    assert result["decision"]["recommended_actions"] == []
```

Define `build_graph_with_router_outcome` in the same new
`tests/test_outcome_routing.py` file using the existing fake-model pattern from
`LangGraphHarnessIntegrationTests`: the fake Router returns a `RouterDecision`
with the supplied `requested_outcome`, while the fake response model is the
passed object.

- [ ] **Step 2: Write failing CLI follow-up tests**

In `tests/test_progress_summaries.py`, add one unsupported alternative state and one ambiguous state. Assert:

```python
assert alternative_prompt.kind == "alternative_outcome"
assert alternative_prompt.continuation_action is None
assert alternative_prompt.alternative_action == "run_lioness_puma"

assert clarify_prompt.kind == "clarify_outcome"
assert clarify_prompt.continuation_action is None

continuation = resolve_next_turn_input(alternative_prompt, "yes")
assert continuation.startswith("CONFIRMED_OUTCOME_ACTION=run_lioness_puma")
assert "PREVIOUS_ACTION" not in continuation
```

- [ ] **Step 3: Run response/follow-up tests and verify missing behavior**

Run:

```bash
python -m pytest tests/test_concept_answers.py tests/test_progress_summaries.py -q
```

Expected: failures show missing renderers, prompt kinds, and alternative confirmation fields.

- [ ] **Step 4: Add deterministic outcome labels and renderers**

In `concept_answers.py`, define bounded labels for operations, artifacts, and granularities. Render from typed fields, not the original user sentence. Implement:

```python
def render_outcome_clarification(decision: TaskDecision) -> str | None:
    if decision.capability_match_status != "ambiguous" or not decision.clarification_question:
        return None
    return _ui_text(
        "I cannot select a workflow until the requested result is clear. "
        f"{decision.clarification_question}\n\n"
        "No files were inspected and no analysis ran."
    )
```

`render_capability_gap` must require `status="unsupported"`, describe the requested operation/artifact/granularity/entities, look up only the first validated `alternative_action`, describe that workflow's output capability, ask whether the alternative is intended, and end with the non-execution statement. When no alternative exists, state the supported artifact families without inventing a candidate.

- [ ] **Step 5: Route mismatch responses before generic generation**

In `graph/response.py`, call the clarification renderer and then the capability-gap renderer after plan rejection handling but before purpose/composition/generic response paths. Return immediately on either result. Do not add unsupported alternatives to `relevant_specs` as though they matched.

- [ ] **Step 6: Add safe CLI prompt states**

Extend `NextTurnPrompt.kind` with `clarify_outcome` and `alternative_outcome`, and add:

```python
alternative_action: RecommendedAction | None = None
alternative_granularity: Granularity | None = None
```

In `build_next_turn_prompt`:

```python
if decision.capability_match_status == "ambiguous":
    return NextTurnPrompt(
        kind="clarify_outcome",
        question=_ui_text("Reply with the clarification above, or describe another NetZoo goal."),
    )

if decision.capability_match_status == "unsupported" and decision.alternative_actions:
    return NextTurnPrompt(
        kind="alternative_outcome",
        question=_ui_text("Reply yes if you want the supported alternative above, or describe another goal."),
        alternative_action=decision.alternative_actions[0],
        alternative_granularity=(
            decision.requested_outcome.granularity
            if decision.requested_outcome
            and decision.requested_outcome.granularity
            in OUTPUT_CAPABILITIES[decision.alternative_actions[0]].granularities
            else None
        ),
    )
```

In `resolve_next_turn_input`, handle an affirmative alternative before the existing `continuation_action` path:

```python
if prompt.alternative_action and affirmative:
    granularity = (
        f" CONFIRMED_GRANULARITY={prompt.alternative_granularity}."
        if prompt.alternative_granularity
        else ""
    )
    return (
        f"CONFIRMED_OUTCOME_ACTION={prompt.alternative_action}.{granularity} "
        "Explain the confirmed supported outcome and recommend its workflow. "
        "Do not execute it yet."
    )
```

In `repair_router_decision`, recognize only allow-listed
`CONFIRMED_OUTCOME_ACTION` markers. Return `no_tool`, `answer_question`, exact
`matched_actions`, and registry-derived `recommended_actions`; never set
`should_execute=True` for this marker. Rebuild `requested_outcome` from the
confirmed capability's operation, artifact, entity, regulator, and target
fields. Use `CONFIRMED_GRANULARITY` only when it belongs to that capability;
otherwise use the capability's sole granularity or leave it unresolved.

- [ ] **Step 7: Correct timeline summaries**

Pass `capability_match_status` into `render_progress_summary("next_step", ...)`. Add explicit summaries for ambiguous and unsupported outcomes so the timeline does not say "stable guidance" when a capability gap was found.

- [ ] **Step 8: Run response and CLI tests**

Run:

```bash
python -m pytest tests/test_concept_answers.py tests/test_progress_summaries.py tests/test_agent_gate.py -k "capability_gap or outcome or follow_up or continuation or response" -q
```

Expected: all selected tests pass.

- [ ] **Step 9: Commit mismatch interaction**

```bash
git add scripts/netzoo_agent_core/interpretation/concept_answers.py scripts/netzoo_agent_core/interpretation/repair.py scripts/netzoo_agent_core/graph/response.py scripts/netzoo_agent_core/contracts/state.py scripts/netzoo_agent_core/cli/follow_up.py scripts/netzoo_agent_core/progress_summaries.py tests/test_concept_answers.py tests/test_progress_summaries.py tests/test_agent_gate.py
git commit -m "feat: explain unsupported requested outcomes"
```

---

### Task 5: Add Generalization Gauntlet, Documentation, and End-to-End Verification

**Files:**
- Modify: `tests/test_agent_gate.py`
- Modify: `tests/test_outcome_routing.py`
- Modify: `tests/test_progress_summaries.py`
- Modify: `AGENT_USAGE.md`
- Modify: `NETZOO_HARNESS_ARCHITECTURE.md`

**Interfaces:**
- Consumes: completed outcome contracts, policy metadata, matcher, routing gate, and renderers.
- Produces: regression evidence that wording variation cannot broaden capability matches.
- Produces: user and maintainer documentation for exact, ambiguous, unsupported, and alternative states.

- [ ] **Step 1: Add table-driven semantic generalization fixtures**

Add Router-fixture graph tests for these outcome classes; vary text without adding production regexes:

```python
UNSUPPORTED_MEASUREMENT_REQUESTS = [
    "How can I obtain one miRNA dataset per patient?",
    "我想取得每個樣本的 miRNA 原始資料，需要什麼工具？",
    "I need individual-level micro RNA measurements, not a network.",
]

SUPPORTED_NETWORK_REQUESTS = [
    "How do I infer per-sample miRNA-to-gene regulatory networks?",
    "請建立每個樣本的微小 RNA 基因調控網路",
    "Which workflow estimates individualized microRNA regulator–target edges?",
]
```

For the first table, the Router fixture returns `acquire/measurement_dataset`; assert no exact recommendation and no plan/executor access. For the second, it returns `infer/regulatory_network`; assert exact `run_lioness_puma` matching and PUMA-to-LIONESS-PUMA guidance. Add a negation case where a Router fixture incorrectly proposes `run_lioness_puma` but the typed measurement outcome still blocks it.

- [ ] **Step 2: Add provider-failure safety tests**

Call `deterministic_router_fallback` with each unnamed request above and `TimeoutError()`. Assert all are `no_tool`, have no `matched_actions` or `recommended_actions`, and ask for outcome clarification. Then test explicit `"What inputs does PUMA require?"` and assert named guidance remains available without execution.

- [ ] **Step 3: Run the new gauntlet**

Run:

```bash
python -m pytest tests/test_agent_gate.py tests/test_outcome_routing.py -k "generalization or provider_failure or measurement or regulatory_network" -q
```

Expected: all new cases pass.

- [ ] **Step 4: Update user and architecture documentation**

In `AGENT_USAGE.md`, replace the old sample-specific miRNA example that accepts underspecified miRNA data. Show both outcomes:

```text
sample-specific miRNA measurement data -> unsupported acquisition request;
ask whether a sample-specific miRNA-to-gene regulatory network was intended.

sample-specific miRNA regulatory network -> exact LIONESS-PUMA capability;
explain the aggregate PUMA stage and sample-specific LIONESS-PUMA stage.
```

In `NETZOO_HARNESS_ARCHITECTURE.md`, document the authority flow:

```text
Router RequestedOutcome
-> Pydantic validation
-> Python OutputCapabilityDefinition matcher
-> exact / ambiguous / unsupported
-> repair and capability gate
-> planner only for exact matched actions
```

State explicitly that YAML mirrors the Python registry, alternatives do not grant authority, and provider fallback handles unnamed semantic goals conservatively.

- [ ] **Step 5: Run static and focused verification**

Run:

```bash
python -m compileall -q scripts
python -m pytest tests/test_outcome_matching.py tests/test_routing_package.py tests/test_interpretation_package.py tests/test_concept_answers.py tests/test_progress_summaries.py -q
python -m pytest tests/test_agent_gate.py tests/test_outcome_routing.py -q
```

Expected: compile succeeds and all selected tests pass.

- [ ] **Step 6: Run the complete test suite**

Run:

```bash
python -m pytest -q
```

Expected: all tests pass. If an unrelated pre-existing dirty-worktree test fails, record the exact failing test and verify it also fails without the implementation commits before classifying it as pre-existing.

- [ ] **Step 7: Run TEST-mode CLI acceptance conversations**

Use the existing graph test harness or `./netzoo-chat` in TEST mode without `/execute`. Verify these two requests:

```text
if i want to get sample specific mi-RNA data, what tools do i need?
if i want to get sample specific mi-RNA regulator network, what tools do i need?
```

Expected first outcome: no workflow is claimed to obtain the data; the Agent explains the acquisition-versus-inference gap, offers LIONESS-PUMA only as an alternative, and states that nothing ran.

Expected second outcome: the Agent explains PUMA and LIONESS-PUMA as the registered guidance sequence, identifies LIONESS-PUMA as the end-to-end exact action, and states that nothing ran.

- [ ] **Step 8: Inspect the final diff and capability-call graph**

Run:

```bash
git diff --check
rg -n "infer_advisory_capabilities|infer_goal_capabilities" scripts/netzoo_agent_core
git status --short
git diff --stat HEAD~4..HEAD
```

Expected: no whitespace errors; legacy inference helpers have no production callers in repair, fallback, gate, or graph routing; unrelated user files remain unstaged and unchanged by these commits.

- [ ] **Step 9: Commit tests and documentation**

```bash
git add tests/test_agent_gate.py tests/test_outcome_routing.py tests/test_progress_summaries.py AGENT_USAGE.md NETZOO_HARNESS_ARCHITECTURE.md
git commit -m "test: verify generalized outcome capability gating"
```

- [ ] **Step 10: Record final evidence**

Capture the final commit IDs, focused/full test counts, both CLI acceptance outputs, and `git status --short`. Report any remaining dirty files as pre-existing user work and do not stage them.
