# Hypothesis-Guided Outcome Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a general, evidence-preserving routing path that proposes registry-compatible workflow hypotheses for incomplete scientific requests without encoding answers for specific sentences or allowing ambiguous hypotheses to execute.

**Architecture:** Replace the Router's single lossy outcome with a bounded set of evidence-bearing hypotheses, validate those hypotheses for semantic under-classification, and allow one repair call when the first classification is implausibly empty. Keep strict exact capability matching for execution, add a separate partial advisory matcher for compatible candidates, and render unique or tied hypotheses from registry metadata.

**Tech Stack:** Python 3.11, Pydantic v2, LangGraph-compatible graph nodes, pytest, existing NetZoo workflow registry and trace contracts.

## Global Constraints

- The motivating prompts are regression inputs, never production sentence-to-action rules.
- Workflow compatibility and predecessor composition come only from `OUTPUT_CAPABILITIES` and `guidance_predecessors`.
- `matched_actions` contains complete exact matches only; advisory hypotheses never authorize planning or execution.
- Equal semantic evidence remains tied. Registry order may stabilize display order but must not imply confidence, recommendation, or scientific priority.
- A semantic repair call is permitted at most once per user turn and must respect the existing task-token budget.
- Raw measurement-data requests must not be reinterpreted as regulatory-network inference.
- All user-visible Agent output remains English, as required by `AGENTS.md`.
- Preserve unrelated dirty-worktree changes and do not include them in task commits.

---

## File Structure

- `scripts/netzoo_agent_core/contracts/outcomes.py`: define evidence and hypothesis contracts and extend capability-match results.
- `scripts/netzoo_agent_core/contracts/decisions.py`: make Router hypotheses the transport contract and store validated hypotheses on `TaskDecision`.
- `scripts/netzoo_agent_core/contracts/state.py`: expose hypothesis state to the graph.
- `scripts/netzoo_agent_core/contracts/__init__.py`: export the new public contracts.
- `scripts/netzoo_agent_core/interpretation/outcome_consistency.py`: detect under-classification and select a unique evidence-leading hypothesis without choosing tied candidates.
- `scripts/netzoo_agent_core/interpretation/hydration.py`: hydrate Router hypotheses into `TaskDecision`.
- `scripts/netzoo_agent_core/interpretation/repair.py`: apply exact/advisory matches while preserving the existing execution gates.
- `scripts/netzoo_agent_core/interpretation/semantic_goal.py`: expose exact, hypothesized, and tied candidates to tracing and response rendering.
- `scripts/netzoo_agent_core/routing/outcome_matching.py`: implement pure strict and partial capability matching.
- `scripts/netzoo_agent_core/llm.py`: describe general hypothesis extraction and build the bounded repair prompt.
- `scripts/netzoo_agent_core/graph/routing_planning.py`: run at most one semantic repair call and record its telemetry.
- `scripts/netzoo_agent_core/interpretation/concept_answers.py`: render registry-grounded unique and tied hypothesis clarifications.
- `scripts/netzoo_agent_core/graph/response.py`: pass policy metadata into the clarification renderer.
- `scripts/netzoo_agent_core/progress_summaries.py`: describe hypothesis clarification without claiming ignorance.
- `scripts/netzoo_agent_core/cli/follow_up.py`: keep ambiguous hypotheses in the clarification interaction branch.
- `tests/test_outcome_routing.py`: verify contracts, consistency detection, hydration, and execution safety.
- `tests/test_outcome_matching.py`: verify general partial matching and neutral ties.
- `tests/test_concept_answers.py`: verify unique and tied hypothesis wording.
- `tests/test_graph_tracing.py`: verify the bounded repair call and audit events.
- `tests/test_agent_gate.py`: add cross-layer regression cases and ensure no phrase-specific production rule exists.
- `tests/test_progress_summaries.py`: verify user-visible progress text.
- `AGENT_USAGE.md`: document hypothesis guidance and the exact-versus-advisory boundary.
- `docs/NETZOO_CHAT_REASONING_AND_WORKFLOW_GUIDE.md`: document generalized examples across workflow families.

---

### Task 1: Add Evidence-Bearing Outcome Contracts

**Files:**
- Modify: `scripts/netzoo_agent_core/contracts/outcomes.py`
- Modify: `scripts/netzoo_agent_core/contracts/decisions.py`
- Modify: `scripts/netzoo_agent_core/contracts/state.py`
- Modify: `scripts/netzoo_agent_core/contracts/__init__.py`
- Test: `tests/test_outcome_routing.py`
- Test: `tests/test_contracts_package.py`

**Interfaces:**
- Produces: `OutcomeEvidence`, `OutcomeHypothesis`, `RouterDecision.outcome_hypotheses`, `TaskDecision.outcome_hypotheses`, `TaskDecision.hypothesis_actions`, and `CapabilityMatch.hypothesis_actions`.
- Preserves: `TaskDecision.requested_outcome` as an optional validated primary outcome for existing downstream code.

- [ ] **Step 1: Write failing contract tests**

Add imports for `OutcomeEvidence` and `OutcomeHypothesis` and add these tests to `tests/test_outcome_routing.py`:

```python
def hypothesis(
    *,
    outcome: RequestedOutcome | None = None,
    confidence: float = 0.9,
    evidence: list[OutcomeEvidence] | None = None,
    assumptions: list[str] | None = None,
) -> OutcomeHypothesis:
    return OutcomeHypothesis(
        outcome=outcome or mirna_network_outcome(),
        confidence=confidence,
        evidence=evidence
        or [
            OutcomeEvidence(
                dimension="regulator_type",
                value="mirna",
                source="explicit",
                rationale="The request explicitly names miRNA.",
            )
        ],
        assumptions=assumptions or [],
    )


def test_router_schema_requires_bounded_outcome_hypotheses():
    schema = RouterDecision.model_json_schema()

    assert "outcome_hypotheses" in schema["required"]
    assert schema["properties"]["outcome_hypotheses"]["maxItems"] == 3


def test_task_decision_keeps_hypotheses_separate_from_exact_matches():
    item = hypothesis(assumptions=["network means regulatory network"])

    decision = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        confidence=0.9,
        reason="advisory hypothesis",
        outcome_hypotheses=[item],
        hypothesis_actions=["run_lioness_puma"],
    )

    assert decision.requested_outcome is None
    assert decision.matched_actions == []
    assert decision.hypothesis_actions == ["run_lioness_puma"]
```

Extend `tests/test_contracts_package.py` so all four new contracts are exported from the stable facade and the legacy facade.

- [ ] **Step 2: Run the contract tests and verify failure**

Run:

```bash
python -m pytest tests/test_outcome_routing.py tests/test_contracts_package.py -q
```

Expected: collection or assertion failures because the hypothesis contracts and fields do not exist.

- [ ] **Step 3: Implement the new contracts**

In `contracts/outcomes.py`, add:

```python
EvidenceDimension = Literal[
    "operation",
    "artifact_type",
    "entity_type",
    "regulator_type",
    "target_type",
    "granularity",
]


class OutcomeEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dimension: EvidenceDimension
    value: str = Field(min_length=1, max_length=80)
    source: Literal["explicit", "inferred"]
    rationale: str = Field(min_length=1, max_length=240)


class OutcomeHypothesis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outcome: RequestedOutcome
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[OutcomeEvidence] = Field(default_factory=list, max_length=12)
    assumptions: list[str] = Field(default_factory=list, max_length=4)

    @field_validator("assumptions")
    @classmethod
    def _bounded_assumptions(cls, values: list[str]) -> list[str]:
        if any(not item.strip() or len(item) > 160 for item in values):
            raise ValueError("assumptions must contain 1-160 characters")
        return values
```

Add `hypothesis_actions: list[RecommendedAction]` to `CapabilityMatch`. In `contracts/decisions.py`, replace the Router transport field with:

```python
outcome_hypotheses: list[OutcomeHypothesis] = Field(
    default_factory=list,
    min_length=1,
    max_length=3,
    description=(
        "Required bounded interpretations of the scientific result. Preserve "
        "competing interpretations instead of erasing known evidence."
    ),
)
```

Update the transport-schema hook so `outcome_hypotheses` is required. Add these fields to `TaskDecision`:

```python
outcome_hypotheses: list[OutcomeHypothesis] = Field(default_factory=list, max_length=3)
hypothesis_actions: list[RecommendedAction] = Field(default_factory=list, max_length=6)
```

Add `outcome_hypotheses: NotRequired[list[dict]]` to `AgentState` and export every new contract and type alias from `contracts/__init__.py`.

- [ ] **Step 4: Update existing Router fixtures to use the new transport contract**

For each of the five `RouterDecision(...)` fixtures found by `rg -n "RouterDecision\\(" tests`, pass one explicit `outcome_hypotheses` item. Named PANDA fixtures use an aggregate TF-to-gene regulatory-network hypothesis; miRNA fixtures use `hypothesis(outcome=...)`. Do not weaken the schema by silently manufacturing a scientific hypothesis in the transport model.

- [ ] **Step 5: Run the contract tests and verify success**

Run:

```bash
python -m pytest tests/test_outcome_routing.py tests/test_contracts_package.py -q
```

Expected: all tests pass.

- [ ] **Step 6: Commit the contract change**

```bash
git add scripts/netzoo_agent_core/contracts/outcomes.py scripts/netzoo_agent_core/contracts/decisions.py scripts/netzoo_agent_core/contracts/state.py scripts/netzoo_agent_core/contracts/__init__.py tests/test_outcome_routing.py tests/test_contracts_package.py tests/test_graph_tracing.py tests/test_agent_gate.py
git commit -m "feat: preserve outcome hypotheses in routing contracts"
```

---

### Task 2: Add Partial Advisory Capability Matching

**Files:**
- Modify: `scripts/netzoo_agent_core/routing/outcome_matching.py`
- Modify: `scripts/netzoo_agent_core/routing/__init__.py`
- Test: `tests/test_outcome_matching.py`

**Interfaces:**
- Consumes: `OutcomeHypothesis`, `OutputCapabilityDefinition`, and the existing strict `match_requested_outcome()`.
- Produces: `match_outcome_hypotheses(hypotheses, capabilities=OUTPUT_CAPABILITIES) -> CapabilityMatch`.
- Guarantees: `matched_actions` is strict; `hypothesis_actions` is advisory; tied top candidates remain present together.

- [ ] **Step 1: Write failing partial-match tests**

Add helpers and tests to `tests/test_outcome_matching.py`:

```python
def advisory_hypothesis(
    requested: RequestedOutcome,
    *evidence: OutcomeEvidence,
    assumptions: list[str] | None = None,
) -> OutcomeHypothesis:
    return OutcomeHypothesis(
        outcome=requested,
        confidence=0.9,
        evidence=list(evidence),
        assumptions=assumptions or ["One outcome dimension remains unconfirmed."],
    )


def test_partial_mirna_sample_network_uniquely_suggests_lioness_puma():
    result = match_outcome_hypotheses(
        [
            advisory_hypothesis(
                outcome(
                    operation="unknown",
                    artifact_type="regulatory_network",
                    entity_types=["mirna"],
                    regulator_types=["mirna"],
                    target_types=[],
                    granularity="sample_specific",
                    unresolved_dimensions=["operation", "target type"],
                ),
                OutcomeEvidence(
                    dimension="regulator_type",
                    value="mirna",
                    source="explicit",
                    rationale="The request explicitly names miRNA.",
                ),
                OutcomeEvidence(
                    dimension="granularity",
                    value="sample_specific",
                    source="explicit",
                    rationale="The request explicitly asks for one network per sample.",
                ),
            )
        ]
    )

    assert result.status == "ambiguous"
    assert result.matched_actions == []
    assert result.hypothesis_actions == ["run_lioness_puma"]


def test_generic_sample_network_keeps_all_lioness_families_tied():
    result = match_outcome_hypotheses(
        [
            advisory_hypothesis(
                outcome(
                    operation="infer",
                    artifact_type="unknown",
                    entity_types=[],
                    display_entities=[],
                    regulator_types=[],
                    target_types=[],
                    granularity="sample_specific",
                    unresolved_dimensions=["network type"],
                ),
                OutcomeEvidence(
                    dimension="granularity",
                    value="sample_specific",
                    source="explicit",
                    rationale="The request explicitly asks for a sample-specific result.",
                ),
            )
        ]
    )

    assert result.status == "ambiguous"
    assert set(result.hypothesis_actions) == {
        "run_lioness_panda",
        "run_lioness_puma",
        "run_lioness_coexpression",
    }


def test_measurement_artifact_conflicts_with_every_network_hypothesis():
    result = match_outcome_hypotheses(
        [
            advisory_hypothesis(
                outcome(
                    operation="acquire",
                    artifact_type="measurement_dataset",
                    regulator_types=[],
                    target_types=[],
                ),
                OutcomeEvidence(
                    dimension="artifact_type",
                    value="measurement_dataset",
                    source="explicit",
                    rationale="The request asks for measured miRNA values.",
                ),
            )
        ]
    )

    assert result.matched_actions == []
    assert result.hypothesis_actions == []
    assert result.status == "unsupported"
```

- [ ] **Step 2: Run the matching tests and verify failure**

Run:

```bash
python -m pytest tests/test_outcome_matching.py -q
```

Expected: failures because `match_outcome_hypotheses` and advisory results do not exist.

- [ ] **Step 3: Implement known-dimension compatibility**

In `routing/outcome_matching.py`, add pure helpers with these signatures:

```python
def _known_scalar_matches(requested: str, supported: str) -> bool:
    return requested == _UNKNOWN or requested == supported


def _known_set_matches(requested: Sequence[str], supported: frozenset[str]) -> bool:
    known = set(requested) - {_UNKNOWN}
    return known.issubset(supported)


def _partially_compatible(
    outcome: RequestedOutcome,
    capability: OutputCapabilityDefinition,
) -> bool:
    return (
        _known_scalar_matches(outcome.operation, capability.operation)
        and _known_scalar_matches(outcome.artifact_type, capability.artifact_type)
        and (
            outcome.granularity == _UNKNOWN
            or outcome.granularity in capability.granularities
        )
        and _known_set_matches(outcome.entity_types, capability.entity_types)
        and _known_set_matches(outcome.regulator_types, capability.regulator_types)
        and _known_set_matches(outcome.target_types, capability.target_types)
    )
```

Do not treat `unresolved_dimensions` as a conflict in partial mode; it is precisely why the result stays advisory.

- [ ] **Step 4: Implement evidence scoring and tie preservation**

Add:

```python
def _hypothesis_evidence_score(hypothesis: OutcomeHypothesis) -> int:
    return sum(2 if item.source == "explicit" else 1 for item in hypothesis.evidence)


def match_outcome_hypotheses(
    hypotheses: Sequence[OutcomeHypothesis],
    capabilities: Mapping[RecommendedAction, OutputCapabilityDefinition] = OUTPUT_CAPABILITIES,
) -> CapabilityMatch:
    exact = []
    advisory = []
    for hypothesis in hypotheses:
        strict = match_requested_outcome(hypothesis.outcome, capabilities)
        if not hypothesis.assumptions and strict.status == "exact":
            exact.extend(strict.matched_actions)
        score = _hypothesis_evidence_score(hypothesis)
        for index, (action, capability) in enumerate(capabilities.items()):
            if _partially_compatible(hypothesis.outcome, capability):
                advisory.append((score, index, action))
    if len(set(exact)) == 1:
        return CapabilityMatch(status="exact", matched_actions=list(dict.fromkeys(exact)))
    if advisory:
        top_score = max(item[0] for item in advisory)
        top_actions = [
            action
            for score, _, action in sorted(advisory, key=lambda item: item[1])
            if score == top_score
        ]
        return CapabilityMatch(
            status="ambiguous",
            hypothesis_actions=list(dict.fromkeys(top_actions)),
            clarification_question="Which compatible network result do you mean?",
        )
    first_outcome = hypotheses[0].outcome if hypotheses else None
    return (
        match_requested_outcome(first_outcome, capabilities)
        if first_outcome is not None
        else CapabilityMatch(status="ambiguous", clarification_question="What scientific result do you want?")
    )
```

During implementation, keep the stable index only for deterministic list presentation. Do not add it to the scientific score.

- [ ] **Step 5: Run matcher tests and all existing outcome tests**

Run:

```bash
python -m pytest tests/test_outcome_matching.py tests/test_outcome_routing.py -q
```

Expected: all tests pass, including existing measurement-versus-network protections.

- [ ] **Step 6: Commit the matcher**

```bash
git add scripts/netzoo_agent_core/routing/outcome_matching.py scripts/netzoo_agent_core/routing/__init__.py tests/test_outcome_matching.py
git commit -m "feat: match partial outcome hypotheses safely"
```

---

### Task 3: Detect Semantic Under-Classification and Build One Repair Prompt

**Files:**
- Create: `scripts/netzoo_agent_core/interpretation/outcome_consistency.py`
- Modify: `scripts/netzoo_agent_core/interpretation/__init__.py`
- Modify: `scripts/netzoo_agent_core/llm.py`
- Test: `tests/test_outcome_routing.py`

**Interfaces:**
- Produces: `needs_outcome_repair(task: str, hypotheses: Sequence[OutcomeHypothesis]) -> bool`.
- Produces: `select_primary_hypothesis(hypotheses: Sequence[OutcomeHypothesis]) -> OutcomeHypothesis | None`.
- Produces: `build_router_repair_messages(routing_prompt: str, user_task: str, first_decision: RouterDecision) -> list`.

- [ ] **Step 1: Write failing consistency tests**

Add these tests to `tests/test_outcome_routing.py`:

```python
def unknown_hypothesis() -> OutcomeHypothesis:
    return OutcomeHypothesis(
        outcome=RequestedOutcome(
            operation="unknown",
            artifact_type="unknown",
            granularity="not_applicable",
            unresolved_dimensions=[],
        ),
        confidence=0.9,
        evidence=[],
        assumptions=[],
    )


@pytest.mark.parametrize(
    "task",
    [
        "What tools can produce a sample-specific network?",
        "哪個方法可以建立每個病人的調控網路？",
        "How should I infer individualized co-expression edges?",
        "Build a sample-specific regulator network for this cohort.",
    ],
)
def test_scientific_tool_questions_repair_empty_classifications(task):
    assert needs_outcome_repair(task, [unknown_hypothesis()]) is True


def test_non_scientific_cli_question_does_not_trigger_semantic_repair():
    assert needs_outcome_repair("How do I exit this CLI?", [unknown_hypothesis()]) is False


def test_tied_hypotheses_have_no_primary_outcome():
    first = hypothesis(confidence=0.9)
    second = hypothesis(confidence=0.9, assumptions=["co-expression interpretation"])

    assert select_primary_hypothesis([first, second]) is None
```

Also test that `build_router_repair_messages()` contains the original request, the first structured result, and the phrase `Return one to three evidence-bearing hypotheses`, without containing either motivating prompt as a hard-coded example.

- [ ] **Step 2: Run the consistency tests and verify failure**

Run:

```bash
python -m pytest tests/test_outcome_routing.py -q
```

Expected: import or assertion failures because the consistency and repair helpers do not exist.

- [ ] **Step 3: Implement general under-classification detection**

Create `interpretation/outcome_consistency.py` with:

```python
from collections.abc import Sequence

from ..contracts import OutcomeHypothesis
from ..routing import has_direct_execution_intent, is_workflow_information_request


def _has_usable_evidence(hypothesis: OutcomeHypothesis) -> bool:
    outcome = hypothesis.outcome
    return bool(
        hypothesis.evidence
        or outcome.operation != "unknown"
        or outcome.artifact_type != "unknown"
        or outcome.granularity not in {"unknown", "not_applicable"}
        or set(outcome.entity_types) - {"unknown"}
        or set(outcome.regulator_types) - {"unknown"}
        or set(outcome.target_types) - {"unknown"}
    )


def needs_outcome_repair(
    task: str,
    hypotheses: Sequence[OutcomeHypothesis],
) -> bool:
    scientific_intent = (
        is_workflow_information_request(task)
        or has_direct_execution_intent(task)
    )
    return scientific_intent and not any(
        _has_usable_evidence(item) for item in hypotheses
    )


def select_primary_hypothesis(
    hypotheses: Sequence[OutcomeHypothesis],
) -> OutcomeHypothesis | None:
    scored = sorted(
        (
            sum(2 if item.source == "explicit" else 1 for item in hypothesis.evidence),
            hypothesis.confidence,
            index,
            hypothesis,
        )
        for index, hypothesis in enumerate(hypotheses)
    )
    if not scored:
        return None
    best = scored[-1]
    if len(scored) > 1 and best[:2] == scored[-2][:2]:
        return None
    return best[3]
```

The function uses a general request-intent signal and structured evidence emptiness. It does not inspect `miRNA`, `sample-specific`, or either motivating sentence.

- [ ] **Step 4: Update the primary Router prompt for semantic hypotheses**

In `build_routing_prompt()` replace the single-outcome instructions with general rules that say:

```text
- Return one to three outcome_hypotheses for scientific result and tool-selection requests.
- Preserve explicit entities, biological roles, network type, and granularity as evidence even when another dimension is unknown.
- Treat words such as data, result, values, scores, or output according to the scientific object they modify; they do not by themselves make the artifact a measurement dataset.
- A network artifact and a raw measurement dataset are different outcomes.
- When multiple registered scientific interpretations remain plausible, return competing hypotheses with assumptions instead of clearing known fields.
- Hypotheses describe meaning only. They never authorize workflow execution.
```

Keep examples distributed across TF regulatory networks, miRNA regulatory networks, co-expression networks, measurement datasets, and CONDOR communities. Do not include either motivating sentence verbatim.

- [ ] **Step 5: Implement the repair-message builder**

Add to `llm.py`:

```python
def build_router_repair_messages(
    routing_prompt: str,
    user_task: str,
    first_decision: RouterDecision,
) -> list:
    return [
        SystemMessage(content=routing_prompt),
        HumanMessage(content=user_task[-ROUTER_CONTEXT_MAX_CHARS:]),
        HumanMessage(
            content=(
                "The first classification below erased the scientific request into "
                "an empty outcome. Reclassify the same request once. Return one to "
                "three evidence-bearing hypotheses, preserve explicit facts, state "
                "assumptions, and do not grant tool authority.\n\n"
                f"<first_classification>\n{first_decision.model_dump_json()}\n"
                "</first_classification>"
            )
        ),
    ]
```

Export the consistency helpers from `interpretation/__init__.py` and the prompt builder from `llm.py`.

- [ ] **Step 6: Run tests and verify the prompt contains no motivating sentence**

Run:

```bash
python -m pytest tests/test_outcome_routing.py -q
! rg -n -i "if i want to get sample specific network data" scripts
```

Expected: tests pass and `rg` finds no production match.

- [ ] **Step 7: Commit consistency and prompt behavior**

```bash
git add scripts/netzoo_agent_core/interpretation/outcome_consistency.py scripts/netzoo_agent_core/interpretation/__init__.py scripts/netzoo_agent_core/llm.py tests/test_outcome_routing.py
git commit -m "feat: repair under-classified scientific outcomes"
```

---

### Task 4: Wire Hypotheses and the Bounded Repair Call Through the Graph

**Files:**
- Modify: `scripts/netzoo_agent_core/interpretation/hydration.py`
- Modify: `scripts/netzoo_agent_core/interpretation/repair.py`
- Modify: `scripts/netzoo_agent_core/interpretation/semantic_goal.py`
- Modify: `scripts/netzoo_agent_core/graph/routing_planning.py`
- Test: `tests/test_outcome_routing.py`
- Test: `tests/test_graph_tracing.py`

**Interfaces:**
- Consumes: `needs_outcome_repair`, `select_primary_hypothesis`, `build_router_repair_messages`, and `match_outcome_hypotheses`.
- Produces: graph state keys `outcome_hypotheses` and capability-match `hypothesis_actions`.
- Records: one `routing.underclassified` event and one `router_repair` LLM usage entry only when repair occurs.

- [ ] **Step 1: Write failing hydration and execution-safety tests**

Add to `tests/test_outcome_routing.py`:

```python
def test_hydration_preserves_tied_hypotheses_without_primary_outcome():
    route = RouterDecision(
        action="no_tool",
        in_scope=True,
        intent_type="answer_question",
        confidence=0.9,
        reason="network type is ambiguous",
        outcome_hypotheses=[
            hypothesis(outcome=mirna_network_outcome(), confidence=0.8),
            hypothesis(
                outcome=mirna_network_outcome().model_copy(
                    update={
                        "artifact_type": "coexpression_network",
                        "entity_types": ["gene"],
                        "regulator_types": [],
                        "target_types": [],
                    }
                ),
                confidence=0.8,
            ),
        ],
    )

    decision = hydrate_router_decision(route, "Which sample network should I infer?")

    assert decision.requested_outcome is None
    assert len(decision.outcome_hypotheses) == 2


def test_advisory_hypothesis_cannot_authorize_execution():
    raw = TaskDecision(
        action="run_lioness_puma",
        in_scope=True,
        should_execute=True,
        intent_type="run_analysis",
        confidence=0.99,
        reason="provider proposed execution",
        outcome_hypotheses=[
            hypothesis(assumptions=["network means regulatory network"])
        ],
    )

    repaired = repair_router_decision(raw, "Build my sample-specific miRNA network")

    assert repaired.action == "no_tool"
    assert repaired.should_execute is False
    assert repaired.matched_actions == []
    assert repaired.hypothesis_actions == ["run_lioness_puma"]
```

- [ ] **Step 2: Write a failing bounded-repair graph test**

In `tests/test_graph_tracing.py`, add a `SequencedHypothesisRouter` whose first `invoke()` returns one empty hypothesis and whose second returns a sample-specific miRNA regulatory-network hypothesis with the assumption `network data means a regulatory-network result`. Invoke the graph with a guidance question and assert:

```python
assert router.calls == 2
assert result["decision"]["action"] == "no_tool"
assert result["decision"]["matched_actions"] == []
assert result["decision"]["hypothesis_actions"] == ["run_lioness_puma"]
assert [call["role"] for call in result["token_usage"]["calls"]] == [
    "router",
    "router_repair",
]
assert sum(event.event_type == "routing.underclassified" for event in events) == 1
```

Add a third-answer trap to the fake Router so the test fails if the graph calls it more than twice.

- [ ] **Step 3: Run the focused tests and verify failure**

Run:

```bash
python -m pytest tests/test_outcome_routing.py tests/test_graph_tracing.py -q
```

Expected: failures because hydration, repair, graph retry, and trace state still use one requested outcome.

- [ ] **Step 4: Hydrate and match hypotheses**

In `hydrate_router_decision()`, copy `route.outcome_hypotheses` into `TaskDecision`, call `select_primary_hypothesis()`, and set `requested_outcome` only when it returns one hypothesis.

In `repair_router_decision()`, replace the unconditional single `apply_outcome_match(raw_decision)` call with:

```python
match = match_outcome_hypotheses(raw_decision.outcome_hypotheses)
primary = select_primary_hypothesis(raw_decision.outcome_hypotheses)
decision = raw_decision.model_copy(
    update={
        "requested_outcome": primary.outcome if primary else None,
        "capability_match_status": match.status,
        "matched_actions": match.matched_actions,
        "hypothesis_actions": match.hypothesis_actions,
        "recommended_actions": (
            guidance_actions_for(match.matched_actions[0])
            if len(match.matched_actions) == 1
            else []
        ),
        "alternative_actions": match.alternative_actions,
        "mismatch_dimensions": match.mismatch_dimensions,
        "clarification_question": match.clarification_question,
    }
)
```

Keep the existing branch that forces ambiguous and unsupported outcomes to `action="no_tool"` and `should_execute=False`.

- [ ] **Step 5: Add one bounded repair call to `classify_task()`**

After parsing the first `RouterDecision`, call `needs_outcome_repair()`. When true:

1. record `routing.underclassified` with bounded facts (`hypothesis_count`, `usable_evidence=false`);
2. build repair messages;
3. perform a second `preflight_budget()` with role `router_repair`;
4. if allowed, invoke the same structured Router once and append usage with role `router_repair`;
5. if blocked or failed, retain the first safe Router decision;
6. never enter another retry branch.

Refactor the existing Router invocation into a private `_invoke_router_once(...)` helper only if doing so removes duplicated parsing and usage code; keep it in `routing_planning.py` because it depends on graph context, budgets, and events.

- [ ] **Step 6: Expose hypothesis state and trace summaries**

Update `outcome_routing_state()` to return:

```python
{
    "outcome_hypotheses": [item.model_dump() for item in decision.outcome_hypotheses],
    "capability_match": {
        "status": decision.capability_match_status,
        "matched_actions": decision.matched_actions,
        "hypothesis_actions": decision.hypothesis_actions,
        "alternative_actions": decision.alternative_actions,
        "mismatch_dimensions": decision.mismatch_dimensions,
        "clarification_question": decision.clarification_question,
    },
}
```

For semantic summaries, use exact `recommended_actions` when present and otherwise use `hypothesis_actions`. Mark relationships as `composition` only after registry predecessor expansion; keep tied candidate families as `alternatives`.

- [ ] **Step 7: Run focused graph and routing tests**

Run:

```bash
python -m pytest tests/test_outcome_routing.py tests/test_graph_tracing.py tests/test_agent_gate.py -q
```

Expected: all tests pass and the bounded-repair fixture reports exactly two Router calls.

- [ ] **Step 8: Commit graph integration**

```bash
git add scripts/netzoo_agent_core/interpretation/hydration.py scripts/netzoo_agent_core/interpretation/repair.py scripts/netzoo_agent_core/interpretation/semantic_goal.py scripts/netzoo_agent_core/graph/routing_planning.py tests/test_outcome_routing.py tests/test_graph_tracing.py tests/test_agent_gate.py
git commit -m "feat: route through bounded outcome repair"
```

---

### Task 5: Render Useful Unique and Tied Hypothesis Clarifications

**Files:**
- Modify: `scripts/netzoo_agent_core/interpretation/concept_answers.py`
- Modify: `scripts/netzoo_agent_core/graph/response.py`
- Modify: `scripts/netzoo_agent_core/progress_summaries.py`
- Modify: `scripts/netzoo_agent_core/cli/follow_up.py`
- Test: `tests/test_concept_answers.py`
- Test: `tests/test_progress_summaries.py`

**Interfaces:**
- Consumes: `TaskDecision.hypothesis_actions`, `TaskDecision.outcome_hypotheses`, and `ProjectPolicySnapshot`.
- Produces: `render_outcome_clarification(decision, policy) -> str | None` with a unique-hypothesis form and an unranked-tie form.

- [ ] **Step 1: Write failing unique-hypothesis response test**

Add to `tests/test_concept_answers.py`:

```python
def test_unique_mirna_hypothesis_explains_registry_composition_and_confirms():
    policy = ProjectPolicyLoader(Path(__file__).parents[1]).load()
    decision = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=0.9,
        reason="advisory hypothesis",
        capability_match_status="ambiguous",
        outcome_hypotheses=[
            OutcomeHypothesis(
                outcome=RequestedOutcome(
                    operation="infer",
                    artifact_type="regulatory_network",
                    entity_types=["mirna", "gene"],
                    display_entities=["miRNA", "gene"],
                    regulator_types=["mirna"],
                    target_types=["gene"],
                    granularity="sample_specific",
                    unresolved_dimensions=["confirm network interpretation"],
                ),
                confidence=0.9,
                evidence=[],
                assumptions=["network data means a regulatory-network result"],
            )
        ],
        hypothesis_actions=["run_lioness_puma"],
        clarification_question="Is that the network result you mean?",
    )

    answer = render_outcome_clarification(decision, policy)

    assert "It sounds like" in answer
    assert "PUMA" in answer
    assert "LIONESS-PUMA" in answer
    assert answer.index("PUMA") < answer.index("LIONESS-PUMA")
    assert "Is that the network result you mean?" in answer
    assert "I cannot select a workflow" not in answer
```

- [ ] **Step 2: Write failing neutral-tie response test**

Add a decision with `hypothesis_actions` containing all three LIONESS families and assert:

```python
assert "TF-only regulatory" in answer
assert "TF/miRNA regulatory" in answer
assert "co-expression" in answer
assert "Which network relationship" in answer
for biased_word in ("best", "preferred", "recommended", "most likely"):
    assert biased_word not in answer.casefold()
```

- [ ] **Step 3: Update progress-summary tests**

Add to `tests/test_progress_summaries.py`:

```python
def test_ambiguous_hypotheses_progress_preserves_candidate_context():
    text = render_progress_summary(
        "next_step",
        {
            "action": "no_tool",
            "in_scope": "true",
            "should_execute": "false",
            "capability_match_status": "ambiguous",
            "hypothesis_count": "3",
        },
    )

    assert "compatible workflow" in text
    assert "clarification" in text
    assert "requested result is ambiguous" not in text
```

- [ ] **Step 4: Run renderer tests and verify failure**

Run:

```bash
python -m pytest tests/test_concept_answers.py tests/test_progress_summaries.py -q
```

Expected: failures because the current renderer accepts no policy and always emits the generic negative template.

- [ ] **Step 5: Implement registry-grounded clarification rendering**

Change the signature to:

```python
def render_outcome_clarification(
    decision: TaskDecision,
    policy: ProjectPolicySnapshot,
) -> str | None:
```

For one `hypothesis_action`, use `guidance_actions_for(action)` to obtain the ordered composition and `policy.workflows[action]` for every user-visible workflow name and description. Render the primary outcome through the existing capability/outcome label helpers and clearly introduce it as an interpretation, not a fact.

For multiple `hypothesis_actions`, group by output capability and render neutral labels:

```text
I can map this to more than one registered sample-specific network family:
- TF-only regulatory network: PANDA → LIONESS-PANDA
- TF/miRNA regulatory network: PUMA → LIONESS-PUMA
- Gene co-expression network: LIONESS-COEXPRESSION

Which network relationship do you mean?

No files were inspected and no analysis ran.
```

Sort the displayed groups by the neutral network-family label, not match score. Do not use `recommended`, `best`, or `most likely` for a tied group.

- [ ] **Step 6: Wire renderer, progress, and CLI follow-up behavior**

Pass `context.project_policy` from `graph/response.py`. Extend the progress-summary facts with `hypothesis_count`. Keep `build_next_turn_prompt()` on `kind="clarify_outcome"` whenever `capability_match_status == "ambiguous"`; do not attach `continuation_action` for hypothesis-only results.

- [ ] **Step 7: Run renderer and CLI tests**

Run:

```bash
python -m pytest tests/test_concept_answers.py tests/test_progress_summaries.py tests/test_cli_package.py tests/test_cli_lifecycle.py -q
```

Expected: all tests pass; ambiguous guidance has one CLI-owned follow-up and no execution continuation.

- [ ] **Step 8: Commit the user-facing behavior**

```bash
git add scripts/netzoo_agent_core/interpretation/concept_answers.py scripts/netzoo_agent_core/graph/response.py scripts/netzoo_agent_core/progress_summaries.py scripts/netzoo_agent_core/cli/follow_up.py tests/test_concept_answers.py tests/test_progress_summaries.py
git commit -m "feat: explain workflow hypotheses before clarification"
```

---

### Task 6: Add Generalized Regression Coverage and Documentation

**Files:**
- Modify: `tests/test_agent_gate.py`
- Modify: `tests/test_graph_tracing.py`
- Modify: `AGENT_USAGE.md`
- Modify: `docs/NETZOO_CHAT_REASONING_AND_WORKFLOW_GUIDE.md`

**Interfaces:**
- Verifies: semantic behavior across paraphrases and workflow families.
- Verifies: the motivating sentences appear only in tests and documentation, not production branching code.

- [ ] **Step 1: Add a cross-family semantic regression matrix**

Add one table-driven `unittest` method to `tests/test_agent_gate.py` with structured hypotheses rather than a production phrase table:

```python
def test_partial_semantic_hypotheses_generalize_across_network_families(self):
    cases = [
        (
            "Which tools estimate one miRNA network for every patient?",
            agent.RequestedOutcome(
                operation="infer",
                artifact_type="regulatory_network",
                entity_types=["mirna", "gene"],
                display_entities=["miRNA", "gene"],
                regulator_types=["mirna"],
                target_types=["gene"],
                granularity="sample_specific",
                unresolved_dimensions=["confirmation"],
            ),
            ["run_lioness_puma"],
        ),
        (
            "如何建立每個樣本的轉錄因子調控網路？",
            agent.RequestedOutcome(
                operation="infer",
                artifact_type="regulatory_network",
                entity_types=["tf", "gene"],
                display_entities=["TF", "gene"],
                regulator_types=["tf"],
                target_types=["gene"],
                granularity="sample_specific",
                unresolved_dimensions=["confirmation"],
            ),
            ["run_lioness_panda"],
        ),
        (
            "What method gives individualized gene coexpression edges?",
            agent.RequestedOutcome(
                operation="infer",
                artifact_type="coexpression_network",
                entity_types=["gene"],
                display_entities=["gene"],
                regulator_types=[],
                target_types=[],
                granularity="sample_specific",
                unresolved_dimensions=["confirmation"],
            ),
            ["run_lioness_coexpression"],
        ),
    ]

    for task, outcome, expected in cases:
        with self.subTest(task=task):
            decision = agent.repair_router_decision(
                agent.TaskDecision(
                    action="no_tool",
                    in_scope=True,
                    should_execute=False,
                    intent_type="answer_question",
                    confidence=0.9,
                    reason="advisory hypothesis",
                    outcome_hypotheses=[
                        agent.OutcomeHypothesis(
                            outcome=outcome,
                            confidence=0.9,
                            evidence=[],
                            assumptions=[
                                "Confirm the inferred network interpretation."
                            ],
                        )
                    ],
                ),
                task,
            )

            self.assertEqual(decision.hypothesis_actions, expected)
            self.assertEqual(decision.matched_actions, [])
            self.assertFalse(decision.should_execute)
```

- [ ] **Step 2: Add motivating end-to-end repair cases**

Use the sequential fake Router from Task 4 for both motivating requests. The first repaired response returns three tied hypotheses; the second returns one miRNA regulatory-network hypothesis. Assert the final responses, not internal prompt strings:

```python
assert "Which network relationship do you mean?" in generic_response
assert "PUMA" in mirna_response
assert "LIONESS-PUMA" in mirna_response
assert "Is that the network result you mean?" in mirna_response
assert "What artifact should NetZoo produce?" not in generic_response + mirna_response
```

- [ ] **Step 3: Add measurement and execution-negation regressions**

Cover these requests with measurement-dataset hypotheses:

```text
I need sample-specific miRNA expression measurements, not a network.
取得每個樣本的 miRNA 原始數值，不要推論網路。
Which tool downloads per-patient microRNA abundance data?
```

Assert `hypothesis_actions == []`, `matched_actions == []`, `action == "no_tool"`, and no executor mock was called.

- [ ] **Step 4: Add a production-source anti-hardcoding test**

Add:

```python
def test_motivating_sentences_are_not_production_routing_rules():
    root = Path(__file__).parents[1] / "scripts"
    production = "\n".join(
        path.read_text(encoding="utf-8")
        for path in root.rglob("*.py")
    ).casefold()

    assert "if i want to get sample specific network data" not in production
    assert "if i want to get sample specific mi-rna network data" not in production
```

- [ ] **Step 5: Run all routing, response, and graph regressions**

Run:

```bash
python -m pytest tests/test_outcome_matching.py tests/test_outcome_routing.py tests/test_concept_answers.py tests/test_progress_summaries.py tests/test_graph_tracing.py tests/test_agent_gate.py -q
```

Expected: all tests pass.

- [ ] **Step 6: Update the user and reasoning documentation**

In `AGENT_USAGE.md`, add one section that distinguishes:

```text
exact outcome -> recommended_actions -> execution may proceed through normal gates
partial hypothesis -> hypothesis_actions -> explanation and clarification only
unsupported outcome -> alternative_actions -> changing the goal requires confirmation
```

In `docs/NETZOO_CHAT_REASONING_AND_WORKFLOW_GUIDE.md`, document one example for each of TF, miRNA, co-expression, generic network ambiguity, and measurement-data rejection. State explicitly that the examples test a general capability-contract mechanism and are not production phrase mappings.

- [ ] **Step 7: Run formatting, targeted tests, and the complete test suite**

Run:

```bash
python -m ruff format --check scripts tests
python -m ruff check scripts tests
python -m pytest -q
```

Expected: formatting checks pass, lint passes, and the complete suite passes.

- [ ] **Step 8: Inspect the final diff for accidental user-change inclusion**

Run:

```bash
git status --short
git diff --check
git diff --stat HEAD~5..HEAD
```

Expected: only the routing implementation, its tests, and the two approved documentation files are part of these implementation commits; the pre-existing unrelated dirty files remain unstaged.

- [ ] **Step 9: Commit generalized regressions and documentation**

```bash
git add tests/test_agent_gate.py tests/test_graph_tracing.py AGENT_USAGE.md docs/NETZOO_CHAT_REASONING_AND_WORKFLOW_GUIDE.md
git commit -m "test: prove generalized outcome hypothesis routing"
```

---

## Final Verification

- [ ] The exact motivating phrases exist only in regression tests or documentation.
- [ ] miRNA evidence selects only the LIONESS-PUMA advisory hypothesis and registry metadata expands it to `PUMA → LIONESS-PUMA`.
- [ ] TF evidence selects only LIONESS-PANDA and co-expression evidence selects only LIONESS-COEXPRESSION.
- [ ] A generic sample-specific network request keeps all compatible network families tied and asks one discriminating question.
- [ ] Measurement requests remain unsupported and are never promoted into network inference.
- [ ] The under-classification repair happens at most once and is represented in usage and trace data.
- [ ] Advisory hypotheses never populate `matched_actions`, never set `should_execute=True`, and never reach an Executor.
- [ ] The full test suite and formatting checks pass.
