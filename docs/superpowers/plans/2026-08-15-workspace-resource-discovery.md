# Workspace Resource Discovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let NetZoo answer local-data availability questions by performing a bounded, read-only, registry-driven inventory of compatible resources inside the NetZoo workspace.

**Architecture:** The contextual resolver preserves the user's latest text and passes prior workflow facts as typed graph state. The Router may select one allow-listed read-only discovery action; deterministic planning injects the workspace root and registry-derived workflow candidates. A pure data-layer inventory engine returns typed validated bundles and partial candidates, and both conversational discovery and workflow planning consume that same service.

**Tech Stack:** Python 3.10+, Pydantic v2, LangChain structured output/tools, LangGraph typed state, pytest, Ruff.

## Global Constraints

- Search only the resolved NetZoo workspace; never scan the home directory, whole computer, mounted external drives, or paths outside the workspace.
- Discovery is read-only, does not follow symlinks, and never starts an analysis.
- Enforce maximum depth, visited files, candidate groups, returned paths, per-file parse limits, and execution time.
- Derive input roles, filename hints, validators, and scientific constraints from declarative registry specifications.
- Do not add phrase allow-lists for examples such as `useful data`, `this computer`, or translations.
- Do not add workflow-name branches to the resolver or discovery engine.
- Complete validated bundles sort before partial candidates; partial candidates state missing input roles.
- Prior assistant prose is never trusted context or tool authority.
- The response has one deterministic operational footer and one CLI-owned next-turn prompt.
- Preserve all unrelated dirty-worktree changes and stage only files named by each task.

---

## File structure

- `scripts/workflow_registry.py`: declarative `DiscoverySpec`, read-only action metadata, and discoverable workflow registrations.
- `scripts/netzoo_agent_core/contracts/resources.py`: typed discovery scope, bundle, partial candidate, and inventory result models.
- `scripts/netzoo_agent_core/data/resource_inventory.py`: pure bounded traversal, grouping, validation dispatch, and deterministic ranking.
- `scripts/netzoo_agent_core/data/resource_validators.py`: named validator adapters selected by `DiscoverySpec`; no workflow dispatch.
- `scripts/netzoo_agent_core/data/bundles.py`: compatibility wrapper that delegates coherent bundle selection to the inventory engine.
- `scripts/netzoo_agent_core/tool_adapters.py`: LangChain read-only discovery tool adapter.
- `scripts/netzoo_agent_core/cli/reply_resolution.py`: semantic follow-up classification and typed context preservation.
- `scripts/netzoo_agent_core/cli/conversation.py`: passes trusted interaction context into graph state separately from user text.
- `scripts/netzoo_agent_core/llm.py`: Router messages with a separate trusted context envelope and generic discovery semantics.
- `scripts/netzoo_agent_core/interpretation/extraction.py`: filesystem-shaped workspace subpath extraction with resolved containment.
- `scripts/netzoo_agent_core/interpretation/repair.py`: preserves the typed read-only discovery route without phrase matching.
- `scripts/netzoo_agent_core/planning/context.py`: injects code-owned scope and creates a ready one-step read-only plan.
- `scripts/netzoo_agent_core/evaluation/plan_review.py`: evaluates read-only actions without analysis-input evidence requirements.
- `scripts/netzoo_agent_core/routing/results.py`: retains typed JSON tool output as trusted structured result metadata.
- `scripts/netzoo_agent_core/graph/response.py`: supplies typed inventory to the response model and appends one canonical footer.
- `tests/test_workspace_resource_inventory.py`: synthetic registry, safety, completeness, and ordering coverage.
- Existing package, routing, planning, graph, resolver, and CLI lifecycle tests: integration and public-surface regression coverage.

---

### Task 1: Add typed resource contracts and declarative discovery registry

**Files:**
- Create: `scripts/netzoo_agent_core/contracts/resources.py`
- Modify: `scripts/workflow_registry.py:10-370`
- Modify: `scripts/netzoo_agent_core/contracts/decisions.py:15-75`
- Modify: `scripts/netzoo_agent_core/contracts/results.py:35-70`
- Modify: `scripts/netzoo_agent_core/contracts/state.py:10-40`
- Modify: `scripts/netzoo_agent_core/contracts/__init__.py:1-150`
- Test: `tests/test_contracts_package.py`
- Test: `tests/test_agent_gate.py`

**Interfaces:**
- Produces: `DiscoverySpec`, `READ_ONLY_ACTIONS`, `DISCOVERABLE_ACTIONS`, `WorkspaceDiscoveryScope`, `ValidatedResourceBundle`, `PartialResourceCandidate`, `WorkspaceResourceInventory`.
- Produces: `TaskDecision.workspace_root: str | None`, `TaskDecision.resource_subpath: str | None`, `TaskDecision.resource_actions: list[RecommendedAction]`, and `ToolExecutionResult.structured_output: dict[str, object]`.
- Consumes: existing `RecommendedAction`, `ActionDefinition`, `INPUT_ROLE_FIELDS`, and output-role conventions.

- [ ] **Step 1: Write failing registry and contract tests**

Add tests that prove the action and all scientific discovery differences are data:

```python
def test_workspace_discovery_is_a_registered_read_only_action():
    definition = ACTION_DEFINITIONS["discover_workspace_resources"]
    assert definition.read_only is True
    assert definition.required_inputs == ("workspace_root",)
    assert definition.executor_fields == (
        "workspace_root", "resource_subpath", "resource_actions"
    )
    assert "discover_workspace_resources" in READ_ONLY_ACTIONS


def test_discoverable_workflows_declare_complete_specs():
    assert DISCOVERABLE_ACTIONS
    for action in DISCOVERABLE_ACTIONS:
        spec = ACTION_DEFINITIONS[action].discovery
        assert spec is not None
        assert spec.input_roles
        assert set(spec.input_roles) == set(spec.filename_hints)
        assert spec.validator_ids


def test_inventory_contract_orders_typed_result_groups():
    inventory = WorkspaceResourceInventory(
        scope_root=".",
        visited_file_count=2,
        validated_bundles=[],
        partial_candidates=[],
    )
    assert inventory.truncated is False
    assert inventory.rejected_summary == {}
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```bash
pytest -q tests/test_contracts_package.py tests/test_agent_gate.py -x
```

Expected: collection or assertion failure because `DiscoverySpec`, the resource contracts, and `discover_workspace_resources` do not exist.

- [ ] **Step 3: Add the minimal typed contracts**

Create `contracts/resources.py` with bounded Pydantic models:

```python
class WorkspaceDiscoveryScope(BaseModel):
    workspace_root: str = Field(min_length=1, max_length=4_000)
    resource_subpath: str | None = Field(default=None, max_length=4_000)
    resource_actions: list[RecommendedAction] = Field(default_factory=list)


class ValidatedResourceBundle(BaseModel):
    directory: str
    compatible_actions: list[RecommendedAction] = Field(min_length=1)
    inputs: dict[str, str] = Field(min_length=1)
    validation_reasons: list[str] = Field(min_length=1)


class PartialResourceCandidate(BaseModel):
    directory: str
    action: RecommendedAction
    matched_inputs: dict[str, str] = Field(default_factory=dict)
    missing_inputs: list[str] = Field(min_length=1)


class WorkspaceResourceInventory(BaseModel):
    schema: Literal["workspace_resource_inventory"] = "workspace_resource_inventory"
    scope_root: str
    visited_file_count: int = Field(ge=0)
    truncated: bool = False
    validated_bundles: list[ValidatedResourceBundle] = Field(default_factory=list)
    partial_candidates: list[PartialResourceCandidate] = Field(default_factory=list)
    rejected_summary: dict[str, int] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list, max_length=20)
```

Add `interaction_context: NotRequired[dict]` to `AgentState`, code-owned discovery fields to `TaskDecision`, and `structured_output` to `ToolExecutionResult`. Re-export resource contracts from `contracts/__init__.py` without widening unrelated legacy public surfaces.

- [ ] **Step 4: Add declarative action metadata**

Add these frozen registry types and derived sets:

```python
@dataclass(frozen=True, slots=True)
class DiscoverySpec:
    input_roles: tuple[str, ...]
    filename_hints: Mapping[str, tuple[str, ...]]
    allowed_extensions: frozenset[str] = frozenset({".tsv", ".tab", ".txt", ".csv"})
    validator_ids: tuple[str, ...] = ()
    min_samples: int | None = None
    ranking_hints: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ActionDefinition:
    read_only: bool = False
    discovery: DiscoverySpec | None = None


READ_ONLY_ACTIONS = frozenset(
    action for action, definition in ACTION_DEFINITIONS.items()
    if definition.read_only
)
DISCOVERABLE_ACTIONS = tuple(
    action for action, definition in ACTION_DEFINITIONS.items()
    if definition.discovery is not None
)
```

Add `read_only` and `discovery` after the existing `output_capability` field on `ActionDefinition`; do not alter the existing fields or defaults. Register `discover_workspace_resources` with `read_only=True`, `required_inputs=("workspace_root",)`, and executor fields `workspace_root`, `resource_subpath`, and `resource_actions`. Declare specs on supported run actions. Put variations such as miRNA input, CONDOR edge input, and minimum sample count in the specs rather than in discovery control flow.

- [ ] **Step 5: Update schema snapshots and run GREEN tests**

Run:

```bash
pytest -q tests/test_contracts_package.py tests/test_agent_gate.py
ruff check scripts/workflow_registry.py scripts/netzoo_agent_core/contracts tests/test_contracts_package.py tests/test_agent_gate.py
```

Expected: all focused tests pass and only intentionally changed schema digests require updates.

- [ ] **Step 6: Commit Task 1**

```bash
git add scripts/workflow_registry.py scripts/netzoo_agent_core/contracts/resources.py scripts/netzoo_agent_core/contracts/decisions.py scripts/netzoo_agent_core/contracts/results.py scripts/netzoo_agent_core/contracts/state.py scripts/netzoo_agent_core/contracts/__init__.py tests/test_contracts_package.py tests/test_agent_gate.py
git commit -m "feat: define workspace resource discovery contracts"
```

---

### Task 2: Build the generic bounded inventory engine

**Files:**
- Create: `scripts/netzoo_agent_core/data/resource_inventory.py`
- Create: `scripts/netzoo_agent_core/data/resource_validators.py`
- Modify: `scripts/netzoo_agent_core/data/__init__.py`
- Test: `tests/test_workspace_resource_inventory.py`
- Test: `tests/test_data_package.py`

**Interfaces:**
- Consumes: `DiscoverySpec`, `ActionDefinition`, `WorkspaceResourceInventory`, and injected `ValidatorMap`.
- Produces: `InventoryLimits` and `inventory_workspace_resources(root: Path, actions: Sequence[RecommendedAction], *, definitions: Mapping[str, ActionDefinition] = ACTION_DEFINITIONS, validators: Mapping[str, ResourceValidator] = RESOURCE_VALIDATORS, explicit_inputs: Mapping[str, str] | None = None, limits: InventoryLimits = InventoryLimits()) -> WorkspaceResourceInventory`.
- Produces: `ResourceValidator = Callable[[Mapping[str, str], DiscoverySpec], tuple[bool, str]]`.

- [ ] **Step 1: Write failing synthetic-engine tests**

Use neutral action, role, and filenames so the test cannot pass through workflow-name branching:

```python
def test_inventory_uses_only_synthetic_registry_data(tmp_path):
    study = tmp_path / "study-a"
    study.mkdir()
    (study / "alpha.tsv").write_text("id\ts1\nsignal\t1\n", encoding="utf-8")
    (study / "beta.tsv").write_text("source\ttarget\na\tb\n", encoding="utf-8")
    definitions = dict(ACTION_DEFINITIONS)
    definitions["format_expression"] = replace(
        ACTION_DEFINITIONS["format_expression"],
        discovery=DiscoverySpec(
            input_roles=("primary", "relation"),
            filename_hints={"primary": ("alpha",), "relation": ("beta",)},
            validator_ids=("always_valid",),
        ),
    )

    result = inventory_workspace_resources(
        tmp_path,
        ["format_expression"],
        definitions=definitions,
        validators={"always_valid": lambda values, spec: (True, "validated")},
    )

    assert result.validated_bundles[0].directory == "study-a"
    assert result.validated_bundles[0].inputs == {
        "primary": "study-a/alpha.tsv",
        "relation": "study-a/beta.tsv",
    }
```

Add separate tests for partial candidates, deterministic ordering, multiple compatible actions, unreadable files, traversal truncation, symlink exclusion, and a resolved outside-root path.

- [ ] **Step 2: Run the inventory tests and verify RED**

Run:

```bash
pytest -q tests/test_workspace_resource_inventory.py tests/test_data_package.py -x
```

Expected: collection failure because the inventory module and interfaces do not exist.

- [ ] **Step 3: Implement bounded traversal and containment**

Create the immutable limits and containment helpers:

```python
@dataclass(frozen=True, slots=True)
class InventoryLimits:
    max_depth: int = 4
    max_visited_files: int = 2_000
    max_candidate_groups: int = 100
    max_returned_paths: int = 200
    max_file_bytes: int = 10_000_000
    max_duration_seconds: float = 5.0


def _contained(path: Path, root: Path) -> bool:
    return path.resolve().is_relative_to(root.resolve())
```

Walk with `os.walk(..., followlinks=False)`, remove symlink directories before descent, count every visited filename, and compare `time.monotonic()` with a start timestamp on each directory and file iteration. Stop and set `truncated=True` when any depth, visited-file, candidate-group, returned-path, byte, or duration limit is reached. Never open a path that is a symlink, outside root, too large, or has an extension absent from the active specs. Render every returned path relative to the resolved search root.

- [ ] **Step 4: Implement specification-driven grouping and validation**

For every candidate directory and action spec:

```python
matched = {
    role: best_matching_path(files, spec.filename_hints[role], spec.allowed_extensions)
    for role in spec.input_roles
}
present = {role: path for role, path in matched.items() if path is not None}
missing = [role for role in spec.input_roles if role not in present]
```

Return `PartialResourceCandidate` when `missing` is non-empty. For a complete group, call each `validator_id` through the injected mapping. Aggregate identical role-to-path bundles across compatible actions, then sort validated bundles before partial candidates using deterministic completeness, context action order, and relative path order.

- [ ] **Step 5: Run focused tests and static checks**

Run:

```bash
pytest -q tests/test_workspace_resource_inventory.py tests/test_data_package.py
ruff check scripts/netzoo_agent_core/data/resource_inventory.py scripts/netzoo_agent_core/data/resource_validators.py tests/test_workspace_resource_inventory.py tests/test_data_package.py
```

Expected: all focused tests pass; the pure data owners import no CLI, graph, planning, routing, or execution modules.

- [ ] **Step 6: Commit Task 2**

```bash
git add scripts/netzoo_agent_core/data/resource_inventory.py scripts/netzoo_agent_core/data/resource_validators.py scripts/netzoo_agent_core/data/__init__.py tests/test_workspace_resource_inventory.py tests/test_data_package.py
git commit -m "feat: inventory workspace resources from registry data"
```

---

### Task 3: Make workflow planning reuse the inventory engine

**Files:**
- Modify: `scripts/netzoo_agent_core/data/resource_validators.py`
- Modify: `scripts/netzoo_agent_core/data/bundles.py:1-190`
- Modify: `scripts/netzoo_agent_core/interpretation/discovery.py:20-170`
- Test: `tests/test_dataset_bundles.py`
- Test: `tests/test_agent_stability.py`
- Test: `tests/test_agent_gate.py`

**Interfaces:**
- Consumes: `inventory_workspace_resources(root: Path, actions: Sequence[RecommendedAction], *, definitions: Mapping[str, ActionDefinition] = ACTION_DEFINITIONS, validators: Mapping[str, ResourceValidator] = RESOURCE_VALIDATORS, explicit_inputs: Mapping[str, str] | None = None, limits: InventoryLimits = InventoryLimits()) -> WorkspaceResourceInventory`, existing `_inspect_panda_inputs_impl`, `inspect_condor_inputs_impl`, and `expression_sample_count`.
- Preserves: `discover_coherent_bundle(action: str, nearby: Path, explicit_inputs: dict[str, str]) -> BundleDiscovery | None`.
- Produces: production `RESOURCE_VALIDATORS` keyed by validator identifier, never by workflow action.

- [ ] **Step 1: Add failing parity tests**

Add a test that creates one complete compatible directory and proves conversational inventory and planning choose the same role-to-path mapping:

```python
inventory = inventory_workspace_resources(root, ["run_puma"])
bundle = discover_coherent_bundle("run_puma", root, {})
assert bundle is not None
assert bundle.values == inventory.validated_bundles[0].inputs
```

Retain existing tests proving that two equally valid bundles return `None` for autonomous planning, because planning may not guess even though inventory may list both.

- [ ] **Step 2: Run parity tests and verify RED**

Run:

```bash
pytest -q tests/test_dataset_bundles.py tests/test_agent_stability.py tests/test_agent_gate.py -x
```

Expected: the new parity assertion fails because `discover_coherent_bundle` still uses its private traversal and grouping implementation.

- [ ] **Step 3: Add production validator adapters**

Implement named adapters with the common signature:

```python
def validate_regulatory_inputs(values, spec):
    _, ok, _ = _inspect_panda_inputs_impl(
        values["expression_file"],
        values["motif_file"],
        values["ppi_file"],
        values.get("mirna_file", ""),
    )
    return ok, "regulatory input identifiers are compatible" if ok else "identifier_mismatch"


RESOURCE_VALIDATORS = {
    "regulatory_inputs": validate_regulatory_inputs,
    "condor_edges": validate_condor_edges,
    "expression_samples": validate_expression_samples,
}
```

The engine calls these identifiers from `DiscoverySpec`; it never tests an action name.

- [ ] **Step 4: Replace private bundle traversal with the shared engine**

Implement the compatibility wrapper:

```python
inventory = inventory_workspace_resources(
    nearby,
    [action],
    explicit_inputs=explicit_inputs,
)
compatible = [
    bundle for bundle in inventory.validated_bundles
    if action in bundle.compatible_actions
]
if len(compatible) != 1:
    return None
selected = compatible[0]
values = {
    role: _display_path((nearby.resolve() / relative_path).resolve())
    for role, relative_path in selected.inputs.items()
}
return BundleDiscovery(
    values=values,
    bundle_id=f"directory:{(nearby.resolve() / selected.directory).resolve()}",
    reason=selected.validation_reasons[0],
    candidates_by_field={key: [value] for key, value in values.items()},
)
```

Remove duplicate directory-walking and workflow-name discovery branches only after parity is green. Keep the public compatibility signature and existing safety semantics.

- [ ] **Step 5: Run planning and bundle regression tests**

Run:

```bash
pytest -q tests/test_workspace_resource_inventory.py tests/test_dataset_bundles.py tests/test_agent_stability.py tests/test_agent_gate.py
```

Expected: inventory may list several bundles; autonomous planning selects only exactly one validated bundle and otherwise declines to guess.

- [ ] **Step 6: Commit Task 3**

```bash
git add scripts/netzoo_agent_core/data/resource_validators.py scripts/netzoo_agent_core/data/bundles.py scripts/netzoo_agent_core/interpretation/discovery.py tests/test_dataset_bundles.py tests/test_agent_stability.py tests/test_agent_gate.py
git commit -m "refactor: share workspace bundle discovery"
```

---

### Task 4: Expose a typed read-only discovery tool

**Files:**
- Modify: `scripts/netzoo_agent_core/tool_adapters.py`
- Modify: `scripts/netzoo_agent_core/execution.py:1-440`
- Modify: `scripts/netzoo_agent_core/routing/dispatch.py:1-35`
- Modify: `scripts/netzoo_agent_core/routing/results.py:1-180`
- Test: `tests/test_agent_gate.py`
- Test: `tests/test_routing_package.py`

**Interfaces:**
- Consumes: `inventory_workspace_resources(Path(workspace_root), resource_actions)`.
- Produces: LangChain tool `discover_workspace_resources(workspace_root: str, resource_subpath: str | None, resource_actions: list[str]) -> str` returning `WorkspaceResourceInventory.model_dump_json()`.
- Produces: generic JSON-schema extraction into `ToolExecutionResult.structured_output` when raw tool output contains a recognized typed `schema` discriminator.

- [ ] **Step 1: Write failing adapter and structured-result tests**

```python
def test_discovery_tool_returns_typed_read_only_inventory(tmp_path, monkeypatch):
    monkeypatch.setattr(tool_adapters, "PROJECT_ROOT", tmp_path)
    raw = discover_workspace_resources.invoke(
        {
            "workspace_root": str(tmp_path),
            "resource_subpath": None,
            "resource_actions": [],
        }
    )
    inventory = WorkspaceResourceInventory.model_validate_json(raw)
    assert inventory.scope_root == "."


def test_structured_result_preserves_inventory_payload():
    raw = WorkspaceResourceInventory(
        scope_root=".", visited_file_count=0
    ).model_dump_json()
    result = structure_tool_result("discover_workspace_resources", decision, raw)
    assert result.status == "success"
    assert result.structured_output["schema"] == "workspace_resource_inventory"
```

- [ ] **Step 2: Run adapter tests and verify RED**

Run:

```bash
pytest -q tests/test_agent_gate.py tests/test_routing_package.py -x
```

Expected: import or executor lookup failure for `discover_workspace_resources`.

- [ ] **Step 3: Implement the tool and register its executor**

The adapter resolves the supplied root, then resolves `resource_subpath` beneath it. Reject the request unless both resolved paths remain within `PROJECT_ROOT`. Call the inventory engine with the contained search root and serialize the typed result. Register it in `LOCAL_TOOL_EXECUTORS`; let `executor_arguments()` obtain the three code-owned fields from `TaskDecision`.

Do not consult global execution mode for this action: it is read-only in both Planning and Execute modes.

- [ ] **Step 4: Parse typed JSON generically**

In `structure_tool_result`, attempt bounded JSON-object parsing for successful raw output. When a `schema` discriminator is present, retain the object in `structured_output`; leave existing text-only tool results unchanged. Do not branch on a workflow name.

- [ ] **Step 5: Run focused tests and Ruff**

Run:

```bash
pytest -q tests/test_agent_gate.py tests/test_routing_package.py tests/test_workspace_resource_inventory.py
ruff check scripts/netzoo_agent_core/tool_adapters.py scripts/netzoo_agent_core/execution.py scripts/netzoo_agent_core/routing/dispatch.py scripts/netzoo_agent_core/routing/results.py
```

Expected: discovery executes read-only in either runtime mode and produces typed structured output.

- [ ] **Step 6: Commit Task 4**

```bash
git add scripts/netzoo_agent_core/tool_adapters.py scripts/netzoo_agent_core/execution.py scripts/netzoo_agent_core/routing/dispatch.py scripts/netzoo_agent_core/routing/results.py tests/test_agent_gate.py tests/test_routing_package.py
git commit -m "feat: expose read-only workspace discovery"
```

---

### Task 5: Preserve user text and pass trusted interaction context separately

**Files:**
- Modify: `scripts/netzoo_agent_core/contracts/interaction.py:1-80`
- Modify: `scripts/netzoo_agent_core/cli/reply_resolution.py:10-115`
- Modify: `scripts/netzoo_agent_core/cli/conversation.py:80-330`
- Modify: `scripts/netzoo_agent_core/llm.py:110-155`
- Modify: `scripts/netzoo_agent_core/graph/router_invocation.py:145-245`
- Test: `tests/test_reply_resolution.py`
- Test: `tests/test_cli_lifecycle.py`
- Test: `tests/test_outcome_routing.py`

**Interfaces:**
- Produces: `ContextualReplyResolution.interaction_context: FollowUpContext | None`.
- Changes: a `follow_up` resolution sets `resolved_task` to the exact latest reply rather than a prose wrapper.
- Changes: `build_router_messages(routing_prompt: str, messages: list, interaction_context: FollowUpContext | dict | None = None) -> list`.
- Changes: `build_router_repair_messages(routing_prompt: str, user_task: str, first_decision: RouterDecision, interaction_context: FollowUpContext | dict | None = None) -> list`.

- [ ] **Step 1: Write failing semantic and data-boundary tests**

```python
def test_resource_availability_question_is_a_substantive_follow_up():
    model = Mock()
    model.invoke.return_value = ReplyIntentDecision(
        kind="follow_up", confidence=0.91, reason="Requests local resource discovery."
    )
    reply = "Could you check whether this workspace already has compatible inputs?"
    result = ContextualReplyResolver.for_test(model).resolve(
        _context(), reply, None, "run-1"
    )
    assert result.resolution.resolved_task == reply
    assert result.resolution.interaction_context.candidate_actions


def test_cli_passes_context_outside_the_user_message():
    conversation = importlib.import_module("netzoo_agent_core.cli.conversation")
    goal = "Which tools produce sample-specific miRNA networks?"
    resource_question = "Could you inspect whether the workspace has compatible inputs?"
    runtime = _fake_cli_runtime(
        invoke_error=[_guidance_result(goal), _guidance_result(resource_question)],
        interactive_answers=[goal, resource_question, "exit"],
        reply_resolver=_resolved_reply("follow_up"),
    )
    assert conversation.run_conversation(
        SimpleNamespace(task=None, keep_session=False), runtime
    ) == 0
    invocation = runtime.invoke_graph_turn_func.call_args_list[1].args[1]
    assert invocation["messages"][-1].content == resource_question
    assert invocation["interaction_context"]["candidate_actions"] == [
        "run_puma", "run_lioness_puma"
    ]
```

Assert the resolver system prompt describes availability, inventory, local resources,
example datasets, reuse, and suitability as semantic categories. Do not assert or add a phrase allow-list.

- [ ] **Step 2: Run resolver and CLI tests and verify RED**

Run:

```bash
pytest -q tests/test_reply_resolution.py tests/test_cli_lifecycle.py tests/test_outcome_routing.py -x
```

Expected: current follow-ups embed `Previous NetZoo goal` and `Registered workflow context` into the user task and expose no separate `interaction_context`.

- [ ] **Step 3: Extend resolution without adding tool authority**

Add the optional typed context to `ContextualReplyResolution`. For `follow_up`, return:

```python
ContextualReplyResolution(
    kind="follow_up",
    resolved_task=reply,
    interaction_context=context,
    reason=decision.reason,
)
```

Update the resolver prompt with general resource-discovery semantics. Keep the 0.80 fail-safe and the rule that only an offered continuation can become `accept_workflow`.

- [ ] **Step 4: Pass typed context through CLI and Router messages**

When conversation submits the resolved follow-up, add:

```python
invocation["interaction_context"] = resolution.interaction_context.model_dump()
```

Build Router messages as system policy, a bounded system-level trusted-context envelope, and the unchanged latest human request. Update the repair call to receive the same envelope. Never add code-generated labels to the human message.

- [ ] **Step 5: Run focused tests and verify no context contamination**

Run:

```bash
pytest -q tests/test_reply_resolution.py tests/test_cli_lifecycle.py tests/test_outcome_routing.py
```

Expected: a resource question reaches the graph unchanged, candidate workflows are available in typed state, a bare acknowledgement still short-circuits, and lexical documentation detection cannot be triggered by context labels.

- [ ] **Step 6: Commit Task 5**

```bash
git add scripts/netzoo_agent_core/contracts/interaction.py scripts/netzoo_agent_core/cli/reply_resolution.py scripts/netzoo_agent_core/cli/conversation.py scripts/netzoo_agent_core/llm.py scripts/netzoo_agent_core/graph/router_invocation.py tests/test_reply_resolution.py tests/test_cli_lifecycle.py tests/test_outcome_routing.py
git commit -m "refactor: separate trusted follow-up context"
```

---

### Task 6: Route and plan generic read-only resource discovery

**Files:**
- Modify: `scripts/netzoo_agent_core/llm.py:35-110`
- Modify: `scripts/netzoo_agent_core/interpretation/repair.py:100-310`
- Modify: `scripts/netzoo_agent_core/interpretation/extraction.py:1-190`
- Modify: `scripts/netzoo_agent_core/graph/routing_planning.py:20-100`
- Modify: `scripts/netzoo_agent_core/planning/builder.py:15-45`
- Modify: `scripts/netzoo_agent_core/planning/context.py:30-180`
- Modify: `scripts/netzoo_agent_core/evaluation/plan_review.py:20-230`
- Modify: `scripts/netzoo_agent_core/evaluation/plan_rules.py`
- Test: `tests/test_outcome_routing.py`
- Test: `tests/test_planning_package.py`
- Test: `tests/test_agent_gate.py`

**Interfaces:**
- Consumes: `AgentState.interaction_context`, `READ_ONLY_ACTIONS`, `DISCOVERABLE_ACTIONS`, and `PROJECT_ROOT`.
- Produces: `extract_workspace_subpath(task: str, workspace_root: Path = PROJECT_ROOT) -> str | None`, which recognizes filesystem-shaped tokens only and returns a contained workspace-relative directory.
- Changes: `build_workflow_plan(raw_decision: TaskDecision, task: str, profile: UserProfile | dict | None = None, retrieved_episodes: list[Episode | dict] | None = None, project_policy: ProjectPolicySnapshot | dict | None = None, interaction_context: FollowUpContext | dict | None = None) -> WorkflowPlan`.
- Produces: a ready one-step plan whose decision contains code-owned `workspace_root` and `resource_actions`.

- [ ] **Step 1: Write failing Router/planner/gate tests**

```python
def test_resource_discovery_plan_uses_code_owned_scope_and_context_actions():
    user_task = "Can you inspect what compatible data is available?"
    decision = TaskDecision(
        action="discover_workspace_resources",
        in_scope=True,
        should_execute=True,
        intent_type="inspect_input",
        confidence=0.93,
        reason="Inspect locally available resources.",
    )
    plan = build_workflow_plan(
        decision,
        user_task,
        interaction_context=FollowUpContext(
            prior_user_goal="Which tools produce sample-specific miRNA networks?",
            prompt_kind="completed",
            prompt_question="Enter a follow-up question.",
            candidate_actions=["run_puma", "run_lioness_puma"],
        ),
    )
    planned = TaskDecision.model_validate(plan.decision)
    assert planned.workspace_root == str(PROJECT_ROOT)
    assert planned.resource_actions == ["run_puma", "run_lioness_puma"]
    assert [step.action for step in plan.steps] == ["discover_workspace_resources"]
    assert plan.status == "ready"


def test_discovery_plan_evaluation_is_read_only_not_analysis_execution():
    evaluation = evaluate_workflow_plan(plan, user_task)
    assert evaluation.status == "approved"
    evidence_item = next(
        item for item in evaluation.rubric
        if item.criterion == "required_input_evidence"
    )
    assert evidence_item.result == "not_applicable"
```

Add a no-prior-context test asserting that `resource_actions` becomes the ordered `DISCOVERABLE_ACTIONS` list. Add a test that a Router-proposed external workspace root is overwritten by `PROJECT_ROOT`. Add containment tests showing an explicit workspace-relative subpath narrows the search while `../` and absolute outside-workspace paths are rejected before tool execution.

- [ ] **Step 2: Run routing/planning tests and verify RED**

Run:

```bash
pytest -q tests/test_outcome_routing.py tests/test_planning_package.py tests/test_agent_gate.py -x
```

Expected: action schema, plan construction, or plan evaluation rejects the new action.

- [ ] **Step 3: Teach the Router the semantic action**

Add a routing rule that selects `discover_workspace_resources` for explicit requests to find, inventory, inspect availability, reuse, or assess suitability of local workspace resources. State that omitted paths are expected for discovery and that this action never authorizes analysis. Do not add regex or phrase matching in production.

Preserve the Router decision in `repair_router_decision` when it selects an allow-listed read-only action with sufficient confidence and `intent_type=inspect_input`; deterministic code supplies all scope fields.

- [ ] **Step 4: Build a generic read-only plan**

In planning, branch on registry metadata (`action in READ_ONLY_ACTIONS`), not on workflow names. For the resource action:

```python
trusted = FollowUpContext.model_validate(interaction_context) if interaction_context else None
decision.workspace_root = str(PROJECT_ROOT)
decision.resource_subpath = extract_workspace_subpath(task)
decision.resource_actions = [
    action for action in (trusted.candidate_actions if trusted else DISCOVERABLE_ACTIONS)
    if action in DISCOVERABLE_ACTIONS
]
```

`extract_workspace_subpath(task)` accepts only explicit filesystem-shaped tokens, normalizes them relative to `PROJECT_ROOT`, and returns a relative path only after resolved containment succeeds. It does not participate in intent classification.

Create one ready `WorkflowStep` using the action's registered executor fields. Do not build dataset evidence or analysis outputs.

- [ ] **Step 5: Generalize plan evaluation for read-only actions**

Treat `READ_ONLY_ACTIONS` as execution-authorized when they are allow-listed, in scope, sufficiently confident, and semantically classified as inspection/retrieval. Mark required analysis input evidence, output collision, and execution-output rubrics not applicable. Still require exact workflow/action alignment, step allow-list, project binding, and read-only step order.

- [ ] **Step 6: Run focused routing and plan tests**

Run:

```bash
pytest -q tests/test_outcome_routing.py tests/test_planning_package.py tests/test_agent_gate.py tests/test_graph_package.py
ruff check scripts/netzoo_agent_core/llm.py scripts/netzoo_agent_core/interpretation/repair.py scripts/netzoo_agent_core/planning scripts/netzoo_agent_core/evaluation/plan_review.py
```

Expected: discovery is a ready read-only plan, external scope suggestions are ignored, and existing analysis authorization remains unchanged.

- [ ] **Step 7: Commit Task 6**

```bash
git add scripts/netzoo_agent_core/llm.py scripts/netzoo_agent_core/interpretation/repair.py scripts/netzoo_agent_core/interpretation/extraction.py scripts/netzoo_agent_core/graph/routing_planning.py scripts/netzoo_agent_core/planning/builder.py scripts/netzoo_agent_core/planning/context.py scripts/netzoo_agent_core/evaluation/plan_review.py scripts/netzoo_agent_core/evaluation/plan_rules.py tests/test_outcome_routing.py tests/test_planning_package.py tests/test_agent_gate.py tests/test_graph_package.py
git commit -m "feat: plan bounded workspace discovery"
```

---

### Task 7: Render evidence-backed inventory responses and prove the transcript

**Files:**
- Modify: `scripts/netzoo_agent_core/graph/prompts.py:20-100`
- Modify: `scripts/netzoo_agent_core/graph/response.py:20-180`
- Modify: `scripts/netzoo_agent_core/graph/response_context.py:1-80`
- Modify: `scripts/netzoo_agent_core/cli/follow_up.py:30-200`
- Modify: `scripts/netzoo_agent_core/presentation.py`
- Test: `tests/test_graph_package.py`
- Test: `tests/test_agent_gate.py`
- Test: `tests/test_cli_lifecycle.py`
- Test: `tests/test_progress_summaries.py`

**Interfaces:**
- Consumes: `ToolExecutionResult.structured_output` containing `WorkspaceResourceInventory`.
- Produces: response-model context with typed inventory as authoritative tool evidence.
- Produces: deterministic footer `Workspace files were inspected read-only; no analysis ran.` for workspace inventory results.

- [ ] **Step 1: Write failing response and transcript tests**

```python
def test_inventory_response_uses_typed_evidence_and_one_footer():
    inventory = WorkspaceResourceInventory(
        scope_root=".",
        visited_file_count=8,
        validated_bundles=[
            ValidatedResourceBundle(
                directory="data/study-a",
                compatible_actions=["run_lioness_puma"],
                inputs={
                    "expression_file": "data/study-a/expression.tsv",
                    "motif_file": "data/study-a/prior.tsv",
                    "ppi_file": "data/study-a/ppi.tsv",
                    "mirna_file": "data/study-a/mirna.txt",
                },
                validation_reasons=["all declared validators passed"],
            )
        ],
        partial_candidates=[
            PartialResourceCandidate(
                directory="data/study-b",
                action="run_lioness_puma",
                matched_inputs={
                    "expression_file": "data/study-b/expression.tsv"
                },
                missing_inputs=["motif_file", "ppi_file", "mirna_file"],
            )
        ],
    )
    decision = TaskDecision(
        action="discover_workspace_resources",
        in_scope=True,
        should_execute=True,
        intent_type="inspect_input",
        confidence=0.95,
        reason="Inspect workspace resources.",
    )
    plan = WorkflowPlan(
        workflow="WORKSPACE-RESOURCES",
        objective=decision.reason,
        decision=decision.model_dump(),
        steps=[WorkflowStep(
            action="discover_workspace_resources",
            purpose="Inventory compatible workspace resources read-only.",
        )],
        status="ready",
    )
    tool_result = ToolExecutionResult(
        action="discover_workspace_resources",
        status="success",
        summary="Workspace inventory completed.",
        structured_output=inventory.model_dump(),
    )
    captured = []

    class DiscoveryResponse:
        def invoke(self, messages):
            captured.extend(messages)
            return AIMessage(content=(
                "Validated bundle: data/study-a. "
                "Partial candidate data/study-b is missing mirna_file."
            ))

    context = SimpleNamespace(
        project_policy=ProjectPolicyLoader(PROJECT_ROOT).load(),
        response_llm=DiscoveryResponse(),
        response_prompt="Use only typed inventory evidence.",
        response_model_name="fake",
        response_max_tokens=800,
        task_token_budget=20_000,
        price_catalog=PriceCatalog.from_environment(),
        recorder=NullTraceRecorder(),
    )
    result = respond(context, {
        "messages": [HumanMessage(content="Inspect available workspace resources")],
        "decision": decision.model_dump(),
        "plan": plan.model_dump(),
        "tool_results": [tool_result.model_dump()],
        "evaluation": EvaluationResult(
            status="completed", reason="Discovery completed."
        ).model_dump(),
    })
    text = result["messages"][0].content
    assert captured
    assert "validated" in text.casefold()
    assert "mirna_file" in text
    assert text.count("Workspace files were inspected read-only") == 1
    assert "No files were inspected" not in text


def test_local_resource_follow_up_runs_discovery_not_needs_detail(capsys):
    conversation = importlib.import_module("netzoo_agent_core.cli.conversation")
    goal = "Which workflow gives one miRNA network per sample?"
    follow_up = "Could you inspect whether the workspace already has usable inputs?"
    discovery = _discovery_result(follow_up)
    runtime = _fake_cli_runtime(
        invoke_error=[_guidance_result(goal), discovery],
        interactive_answers=[goal, follow_up, "exit"],
        reply_resolver=_resolved_reply("follow_up"),
    )
    assert conversation.run_conversation(
        SimpleNamespace(task=None, keep_session=False), runtime
    ) == 0
    output = capsys.readouterr().out
    assert "Please enter a concrete follow-up question" not in output
    assert "Workspace files were inspected read-only" in output
    second_invocation = runtime.invoke_graph_turn_func.call_args_list[1].args[1]
    assert second_invocation["messages"][-1].content == follow_up
    assert second_invocation["interaction_context"]["candidate_actions"]
```

Define this injected CLI boundary fixture beside `_guidance_result`; Task 6 tests the real Router and Planner action selection:

```python
def _discovery_result(goal: str) -> dict:
    decision = TaskDecision(
        action="discover_workspace_resources",
        in_scope=True,
        should_execute=True,
        intent_type="inspect_input",
        confidence=0.95,
        reason="Inspect workspace resources.",
    )
    plan = WorkflowPlan(
        workflow="WORKSPACE-RESOURCES",
        objective=decision.reason,
        decision=decision.model_dump(),
        steps=[WorkflowStep(
            action="discover_workspace_resources",
            purpose="Inventory compatible workspace resources read-only.",
        )],
        status="ready",
    )
    inventory = WorkspaceResourceInventory(
        scope_root=".", visited_file_count=1
    )
    tool_result = ToolExecutionResult(
        action="discover_workspace_resources",
        status="success",
        summary="Workspace inventory completed.",
        structured_output=inventory.model_dump(),
    )
    evaluation = EvaluationResult(
        status="completed", reason="Discovery completed."
    )
    return {
        "messages": [HumanMessage(content=goal), AIMessage(content=(
            "No compatible bundle was found.\n\n"
            "Workspace files were inspected read-only; no analysis ran."
        ))],
        "decision": decision.model_dump(),
        "plan": plan.model_dump(),
        "tool_results": [tool_result.model_dump()],
        "evaluation": evaluation.model_dump(),
    }
```

Add assertions for zero results, several valid bundles, partial-only results, truncation, one CLI prompt, and no automatic run action after discovery.

- [ ] **Step 2: Run response and lifecycle tests and verify RED**

Run:

```bash
pytest -q tests/test_graph_package.py tests/test_agent_gate.py tests/test_cli_lifecycle.py tests/test_progress_summaries.py -x
```

Expected: generic response ownership cannot yet distinguish read-only workspace inspection from no-file guidance.

- [ ] **Step 3: Add typed inventory response context**

Validate `structured_output` with `WorkspaceResourceInventory` before supplying it to the response model. The prompt instructs the model to list validated bundles first, partial candidates second with missing roles, state truncation, avoid claiming compatibility absent from the typed inventory, and never offer to execute a bundle.

Keep raw filesystem text out of capability authority; use the typed, bounded paths and reason categories.

- [ ] **Step 4: Add deterministic operational footer and next-turn behavior**

Add a result-type renderer that returns:

```python
"Workspace files were inspected read-only; no analysis ran."
```

when a successful typed workspace inventory is present. Strip any model-authored duplicate status or call to action before appending it. The CLI next prompt remains imperative and allows another question, a narrowed in-workspace path, or a new goal.

- [ ] **Step 5: Run all focused tests**

Run:

```bash
pytest -q tests/test_workspace_resource_inventory.py tests/test_reply_resolution.py tests/test_outcome_routing.py tests/test_planning_package.py tests/test_graph_package.py tests/test_cli_lifecycle.py tests/test_agent_gate.py tests/test_progress_summaries.py
```

Expected: complete and partial inventory answers are evidence-backed, have one status footer, and never execute an analysis.

- [ ] **Step 6: Run the full verification suite**

Run:

```bash
pytest -q
ruff check scripts/workflow_registry.py scripts/netzoo_agent_core tests/test_workspace_resource_inventory.py tests/test_reply_resolution.py tests/test_outcome_routing.py tests/test_planning_package.py tests/test_graph_package.py tests/test_cli_lifecycle.py tests/test_agent_gate.py tests/test_progress_summaries.py
python -m compileall -q scripts tests
git diff --check
```

Expected: the full suite passes, Ruff and compileall are clean, and no whitespace errors are reported.

- [ ] **Step 7: Run live Docker conversation QA**

Run `./netzoo-chat` and enter, in order:

```text
if i want to get sample specific mi-RNA network data,what tools do i need?
are there any useful data that i can use in this computer?
exit
```

Verify from the visible transcript and trace:

- first turn recommends the validated composition;
- second turn is classified as a substantive follow-up;
- Router selects the read-only discovery action;
- only workspace-relative complete and partial candidates are shown;
- no analysis action runs;
- one read-only inspection footer and one next-turn prompt are rendered.

The exact QA sentence is evidence only; production code must not contain it.

- [ ] **Step 8: Commit Task 7**

```bash
git add scripts/netzoo_agent_core/graph/prompts.py scripts/netzoo_agent_core/graph/response.py scripts/netzoo_agent_core/graph/response_context.py scripts/netzoo_agent_core/cli/follow_up.py scripts/netzoo_agent_core/presentation.py tests/test_graph_package.py tests/test_agent_gate.py tests/test_cli_lifecycle.py tests/test_progress_summaries.py
git commit -m "test: prove contextual workspace discovery"
```

---

## Final review checklist

- [ ] Confirm `git status --short` shows only pre-existing unrelated user changes after all scoped commits.
- [ ] Inspect `git diff <design-commit>..HEAD` for phrase matching or workflow-name branching in resolver/discovery control flow.
- [ ] Confirm every discoverable action obtains behavior from `DiscoverySpec`.
- [ ] Confirm the unchanged user reply and typed interaction context remain separate at the graph boundary.
- [ ] Confirm discovery paths are workspace-relative in user output and resolved containment is workspace-only.
- [ ] Confirm both conversational discovery and workflow planning call `inventory_workspace_resources`.
- [ ] Confirm full tests, Ruff, compileall, diff check, and live Docker QA are green.
