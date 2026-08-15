# LLM-Owned Guidance Response Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Route NetZoo guidance and ambiguity answers through the response LLM while preserving deterministic workflow validation and preventing ordinary phrases such as `network data` from becoming file paths.

**Architecture:** The Router and registry matcher continue producing typed, non-authoritative capability facts. The response graph passes those facts, including exact, advisory, and alternative actions, to the response LLM instead of returning deterministic conversation templates. The path parser separately requires explicit assignment or path-like evidence before hydrating file fields.

**Tech Stack:** Python 3.12, Pydantic contracts, LangGraph, pytest/unittest, registry-backed YAML workflow policy.

## Global Constraints

- All user-visible Agent output remains English.
- Only an exact registered outcome plus the existing execution gates can authorize a workflow run.
- Ambiguous and advisory workflow candidates remain `no_tool` and cannot reach the Executor.
- The response LLM may phrase guidance but may use only validated workflow facts supplied in trusted context.
- Deterministic missing-input, preference-confirmation, plan-rejection, execution-result, and provider-failure safety paths remain intact.
- Tests assert semantic behavior and model invocation, not an exact generated paragraph.
- Existing user changes in the dirty worktree must not be modified or committed.

---

### Task 1: Send validated guidance through the response LLM

**Files:**
- Modify: `tests/test_agent_gate.py`
- Modify: `tests/test_graph_tracing.py`
- Modify: `tests/test_graph_package.py`
- Modify: `scripts/netzoo_agent_core/graph/response.py`
- Modify: `scripts/netzoo_agent_core/graph/prompts.py`

**Interfaces:**
- Consumes: `TaskDecision.recommended_actions`, `matched_actions`, `hypothesis_actions`, and `alternative_actions`; `ProjectPolicySnapshot.workflows`; `latest_user_task(messages)`.
- Produces: the existing `respond(context: _GraphContext, state: AgentState) -> dict` behavior, with validated guidance reaching `context.response_llm.invoke()` and all candidate workflow specifications included in trusted context.

- [ ] **Step 1: Write the failing end-to-end guidance test**

Add a LangGraph integration test in `LangGraphHarnessIntegrationTests` that provides a Router result with two otherwise identical miRNA regulatory-network hypotheses: sample-specific confidence `0.9` and aggregate confidence `0.8`. The response fixture records its messages and returns a direct `PUMA → LIONESS-PUMA` answer.

```python
@patch("netzoo_agent.build_llm")
@unittest.skipIf(agent.StateGraph is None, "LangGraph runtime is available in Docker")
def test_explicit_sample_specific_guidance_reaches_response_llm(self, build_llm):
    motivating_request = (
        "if i want to get sample specific mi-RNA network data,what tools do i need?"
    )
    captured = []

    def hypothesis(granularity, confidence, assumption):
        return agent.OutcomeHypothesis(
            outcome=agent.RequestedOutcome(
                operation="infer",
                artifact_type="regulatory_network",
                entity_types=["tf", "mirna", "gene"],
                display_entities=["TF", "miRNA", "gene"],
                regulator_types=["mirna"],
                target_types=["gene"],
                granularity=granularity,
                unresolved_dimensions=[],
            ),
            confidence=confidence,
            evidence=[
                agent.OutcomeEvidence(
                    dimension="operation",
                    value="infer",
                    source="explicit",
                    rationale="The user asks which tools produce the network.",
                ),
                agent.OutcomeEvidence(
                    dimension="artifact_type",
                    value="regulatory_network",
                    source="explicit",
                    rationale="The requested object is a miRNA network.",
                ),
                agent.OutcomeEvidence(
                    dimension="granularity",
                    value=granularity,
                    source="explicit",
                    rationale="The Router supplied this granularity.",
                ),
            ],
            assumptions=[assumption],
        )

    class AmbiguousRouter:
        def invoke(self, _messages):
            return agent.RouterDecision(
                action="no_tool",
                in_scope=True,
                intent_type="answer_question",
                confidence=0.9,
                reason="Two typed hypotheses were returned.",
                outcome_hypotheses=[
                    hypothesis(
                        "sample_specific",
                        0.9,
                        "The user has not supplied input files yet.",
                    ),
                    hypothesis(
                        "aggregate",
                        0.8,
                        "Aggregate output may also be useful.",
                    ),
                ],
            )

    class RouterProvider:
        def with_structured_output(self, *_args, **_kwargs):
            return AmbiguousRouter()

    class GuidanceResponse:
        def invoke(self, messages):
            captured.extend(messages)
            return agent.AIMessage(
                content=(
                    "Use PUMA to build the aggregate regulatory network, then "
                    "LIONESS-PUMA to estimate one network per sample.\n\n"
                    "No files were inspected and no analysis ran."
                )
            )

    build_llm.side_effect = [RouterProvider(), GuidanceResponse()]
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        app = agent.build_graph(
            "fake",
            0.0,
            profile_store=agent.UserProfileStore(root / "profiles"),
            episode_store=agent.EpisodeStore(root / "episodes"),
        )
        result = app.invoke(
            {"messages": [agent.HumanMessage(content=motivating_request)]}
        )

    self.assertEqual(result["decision"]["capability_match_status"], "ambiguous")
    self.assertEqual(result["decision"]["action"], "no_tool")
    self.assertEqual(result["tool_results"], [])
    self.assertIn("PUMA", result["messages"][-1].content)
    self.assertNotIn(
        "aggregate or sample-specific",
        result["messages"][-1].content,
    )
    self.assertEqual(
        [call["role"] for call in result["token_usage"]["calls"]],
        ["router", "response"],
    )
    trusted_input = "\n".join(str(message.content) for message in captured)
    self.assertIn(motivating_request, trusted_input)
    self.assertIn('"action": "run_puma"', trusted_input)
    self.assertIn('"action": "run_lioness_puma"', trusted_input)
```

The two hypotheses intentionally carry the same evidence score and assumptions so the existing matcher reproduces the advisory ambiguity without granting execution authority.

- [ ] **Step 2: Run the new test and verify the deterministic early return fails it**

Run:

```bash
pytest -q tests/test_agent_gate.py::LangGraphHarnessIntegrationTests::test_explicit_sample_specific_guidance_reaches_response_llm
```

Expected: FAIL because `GuidanceResponse.invoke()` is not called, the output contains the fixed aggregate/sample-specific question, and token usage contains only the Router call.

- [ ] **Step 3: Remove conversational early returns and include every validated candidate action**

In `scripts/netzoo_agent_core/graph/response.py`:

1. Remove imports and early-return calls for `render_outcome_clarification`, `render_spec_backed_concept_answer`, `render_ambiguous_workflow_guidance`, and `render_workflow_composition_guidance`.
2. Keep deterministic branches for `needs_input`, `needs_confirmation`, rejected plans, capability gaps, and completed execution results.
3. Build relevant workflow specs from the stable de-duplicated union below, ignoring unknown action identifiers:

```python
relevant_actions = list(
    dict.fromkeys(
        [
            *decision.matched_actions,
            *decision.hypothesis_actions,
            *decision.recommended_actions,
            *decision.alternative_actions,
        ]
    )
)
relevant_specs = []
for action in relevant_actions:
    spec = context.project_policy.workflows.get(action)
    if spec is None:
        continue
    relevant_specs.append(
        {
            "action": action,
            "workflow": spec.workflow,
            "description": spec.description,
            "required_inputs": spec.required_inputs,
            "optional_inputs": spec.optional_inputs,
            "output_capability": spec.output_capability.model_dump(),
        }
    )
```

This changes only response context. It must not copy candidates into `matched_actions`, change `decision.action`, or alter the execution topology.

- [ ] **Step 4: Strengthen the response prompt around explicit constraints and trusted capabilities**

Add these semantic requirements to the `action == no_tool` section of `scripts/netzoo_agent_core/graph/prompts.py`:

```text
- Answer the latest user's actual question directly from the validated workflow facts.
- Treat explicit constraints in the latest user request as settled unless they conflict internally. Never ask the user to choose a value already supplied.
- matched_actions are exact matches; hypothesis_actions are advisory candidates; alternative_actions require changing the requested outcome. None of these fields independently authorizes execution.
- Distinguish an aggregate predecessor workflow from the requested final result. For a sample-specific miRNA regulatory network, explain the validated PUMA followed by LIONESS-PUMA composition without asking aggregate versus sample-specific again.
- When uncertainty remains, ask only the smallest unresolved scientific question and do not invent additional workflow capabilities.
```

Replace the byte-level response-prompt hash assertion in `tests/test_graph_package.py` with semantic assertions for the explicit-constraint, candidate-authority, and minimal-clarification instructions. This keeps the test stable when prose is edited without changing policy.

- [ ] **Step 5: Update the existing Router-repair graph test to supply a response model**

In `tests/test_graph_tracing.py`, keep `SequencedHypothesisRouter` responsible for exactly two structured Router calls and add:

```python
class GuidanceResponseLLM:
    def __init__(self):
        self.calls = 0

    def invoke(self, _messages):
        self.calls += 1
        return legacy_agent.AIMessage(
            content=(
                "Use PUMA followed by LIONESS-PUMA for sample-specific miRNA "
                "regulatory networks. No files were inspected and no analysis ran."
            )
        )
```

Patch `build_llm` with a two-item iterator, Router provider first and response model second:

```python
response_llm = GuidanceResponseLLM()
models = iter([router, response_llm])
monkeypatch.setattr(
    graph_module,
    "build_llm",
    lambda *_args, **_kwargs: next(models),
)
```

Assert Router calls remain `2`, response calls equal `1`, the workflow stays `no_tool`, and usage roles become:

```python
["router", "router_repair", "response"]
```

- [ ] **Step 6: Run focused response tests**

Run:

```bash
pytest -q tests/test_agent_gate.py::LangGraphHarnessIntegrationTests::test_explicit_sample_specific_guidance_reaches_response_llm tests/test_agent_gate.py::LangGraphHarnessIntegrationTests::test_guidance_response_does_not_duplicate_cli_follow_up_question tests/test_graph_tracing.py::test_graph_repairs_an_underclassified_outcome_once tests/test_graph_package.py
```

Expected: PASS. The two safety-characterization tests that keep execution responses and preference confirmation deterministic must also remain unchanged.

- [ ] **Step 7: Commit the response slice**

```bash
git add tests/test_agent_gate.py tests/test_graph_package.py scripts/netzoo_agent_core/graph/response.py scripts/netzoo_agent_core/graph/prompts.py
git add -p tests/test_graph_tracing.py
git commit -m "fix: let response model resolve guidance ambiguity"
```

For `git add -p`, stage only the Router-repair response-model hunk from this task.
Leave the pre-existing UUID serialization test and its imports unstaged.

---

### Task 2: Require path evidence before hydrating file fields

**Files:**
- Modify: `tests/test_path_and_output_safety.py`
- Modify: `scripts/netzoo_agent_core/interpretation/extraction.py`

**Interfaces:**
- Consumes: `_extract_named_path(task: str, names: tuple[str, ...]) -> str | None` inside the file-role-aware `_task_path(task: str, field_name: str) -> str | None` hydration seam.
- Produces: the same public signatures, with ordinary noun phrases rejected for file fields and explicit assignments, quoted values, path-like tokens, and reverse `PATH as ALIAS` wording accepted. Generic named values such as `prefix demo` retain their existing behavior.

- [ ] **Step 1: Write failing hydration tests for natural language and explicit paths**

Add tests through `hydrate_router_decision`, not against parser internals:

```python
def test_natural_language_data_phrases_do_not_become_file_paths(self):
    tasks = [
        "if i want to get sample specific mi-RNA network data, what tools do i need?",
        "Which workflow produces network results for each patient?",
        "Explain the expression data requirements for PUMA.",
    ]
    for task in tasks:
        with self.subTest(task=task):
            decision = agent.hydrate_router_decision(
                agent.TaskDecision(
                    action="no_tool",
                    in_scope=True,
                    should_execute=False,
                    intent_type="answer_question",
                    confidence=0.9,
                    reason="guidance",
                ),
                task,
            )
            self.assertIsNone(decision.network_file)
            self.assertIsNone(decision.expression_file)


def test_explicit_network_paths_survive_hydration(self):
    cases = [
        ("network_file=data/network.tsv", "data/network.tsv"),
        ("network: data/network.tsv", "data/network.tsv"),
        ("use data/network.tsv as the network", "data/network.tsv"),
    ]
    for task, expected in cases:
        with self.subTest(task=task):
            decision = agent.hydrate_router_decision(
                agent.TaskDecision(
                    action="no_tool",
                    in_scope=True,
                    should_execute=False,
                    intent_type="answer_question",
                    confidence=0.9,
                    reason="guidance",
                ),
                task,
            )
            self.assertEqual(decision.network_file, expected)
```

- [ ] **Step 2: Run the path tests and verify the motivating request fails**

Run:

```bash
pytest -q tests/test_path_and_output_safety.py
```

Expected: FAIL because the motivating request currently produces `network_file="data"`, and the reverse path wording is not recognized.

- [ ] **Step 3: Add file-role-aware path evidence checks without changing public signatures**

In `scripts/netzoo_agent_core/interpretation/extraction.py`, keep `_task_path(task, field_name)` unchanged externally and add private helpers:

```python
_PATHLIKE_SUFFIXES = frozenset({".tsv", ".tab", ".txt", ".csv", ".npy"})


def _looks_like_path(value: str) -> bool:
    token = value.strip().rstrip(".。").casefold()
    return bool(
        "/" in token
        or "\\" in token
        or token.startswith((".", "~"))
        or any(token.endswith(suffix) for suffix in _PATHLIKE_SUFFIXES)
    )


def _alias_pattern(aliases: tuple[str, ...]) -> str:
    return "|".join(
        re.escape(alias) for alias in sorted(aliases, key=len, reverse=True)
    )


def _has_explicit_file_binding(task: str, aliases: tuple[str, ...]) -> bool:
    names = _alias_pattern(aliases)
    return bool(
        re.search(
            rf"(?:{names})\s*(?:(?:是|為|=|:|：)|\b(?:at|as|is|to)\b|['\"])",
            task,
            flags=re.IGNORECASE,
        )
    )


def _reverse_named_path(task: str, aliases: tuple[str, ...]) -> str | None:
    names = _alias_pattern(aliases)
    match = re.search(
        rf"(?:(?P<quote>['\"])(?P<quoted>.*?)(?P=quote)|"
        rf"(?P<plain>[^\s，,。；;]+))\s+(?:as|for)\s+(?:the\s+)?(?:{names})",
        task,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    value = match.group("quoted") or match.group("plain")
    cleaned = value.strip().rstrip(".。")
    return cleaned if match.group("quote") or _looks_like_path(cleaned) else None
```

Then keep the alias table inside `_task_path()` and replace its unconditional return with:

```python
aliases_by_field = {
    "expression_file": ("expression_file", "expression", "表現矩陣", "表現資料"),
    "motif_file": ("motif_file", "motif", "prior", "先驗", "調控先驗"),
    "ppi_file": ("ppi_file", "ppi", "PPI"),
    "mirna_file": ("mirna_file", "miRNA list", "mirna list", "miRNA", "mirna"),
    "network_file": ("network_file", "network", "bipartite", "二分網路", "網路"),
    "output_file": (
        "output_file",
        "aggregate output",
        "PANDA 輸出",
        "PUMA 輸出",
        "output",
        "輸出",
    ),
    "lioness_output": (
        "lioness_output",
        "lioness output",
        "LIONESS 輸出",
        "sample-specific output",
        "個體網路輸出",
    ),
    "output_dir": (
        "output_dir",
        "output dir",
        "output directory",
        "輸出資料夾",
        "輸出目錄",
    ),
}
aliases = aliases_by_field.get(field_name, (field_name,))
parsed = _extract_named_path(task, aliases)
if parsed and (
    _looks_like_path(parsed) or _has_explicit_file_binding(task, aliases)
):
    return parsed
return _reverse_named_path(task, aliases)
```

Do not inspect the filesystem. `_extract_named_path()` remains generic for non-file values such as `prefix`; `_task_path()` is the file-role boundary that requires textual path evidence. Existence and safety checks remain in planning and validation.

- [ ] **Step 4: Run the path and extraction regression tests**

Run:

```bash
pytest -q tests/test_path_and_output_safety.py tests/test_interpretation_package.py tests/test_routing_package.py tests/test_planning_package.py tests/test_agent_gate.py -k "path or hydration or named_path or planner_discards"
```

Expected: PASS, including quoted paths with spaces and sentence-final punctuation.

- [ ] **Step 5: Commit the path slice**

```bash
git add tests/test_path_and_output_safety.py scripts/netzoo_agent_core/interpretation/extraction.py
git commit -m "fix: require evidence before extracting task paths"
```

---

### Task 3: Verify the complete behavior and safety boundary

**Files:**
- Verify only; modify a file only if a failing test demonstrates a regression caused by Tasks 1 or 2.

**Interfaces:**
- Consumes: the complete graph response and path-extraction behavior from Tasks 1 and 2.
- Produces: test evidence that guidance uses the response LLM while execution authorization remains fail-closed.

- [ ] **Step 1: Run focused outcome and response suites**

```bash
pytest -q tests/test_outcome_routing.py tests/test_outcome_matching.py tests/test_concept_answers.py tests/test_graph_tracing.py tests/test_graph_package.py tests/test_progress_summaries.py tests/test_presentation_timeline.py
```

Expected: PASS. Direct unit tests for legacy deterministic render helpers may remain because those helpers are still valid fallback utilities; the graph must no longer select them for ordinary guidance.

- [ ] **Step 2: Run CLI and safety suites**

```bash
pytest -q tests/test_cli_lifecycle.py tests/test_cli_package.py tests/test_path_and_output_safety.py tests/test_agent_gate.py
```

Expected: PASS. In particular, local execution summaries, plan rejection, preference confirmation, and input clarification remain deterministic.

- [ ] **Step 3: Run the complete test suite**

```bash
pytest -q
```

Expected: PASS with no new warnings introduced by this change.

- [ ] **Step 4: Run static and diff checks**

```bash
python -m compileall -q scripts tests
git diff --check HEAD~2..HEAD
git status --short
```

Expected: compilation succeeds, no whitespace errors are reported, and pre-existing unrelated dirty-worktree entries remain untouched.

- [ ] **Step 5: Manually exercise the motivating CLI request when provider credentials are available**

```bash
./netzoo-chat
```

Enter:

```text
if i want to get sample specific mi-RNA network data, what tools do i need?
```

Expected semantic result:

- names `PUMA` and `LIONESS-PUMA` in their validated order;
- explains that PUMA is the aggregate predecessor and LIONESS-PUMA produces per-sample networks;
- does not ask aggregate versus sample-specific;
- reports that no files were inspected and no analysis ran;
- leaves `tool_results` empty.

If a provider call cannot run in the available environment, report the skipped manual check explicitly; do not treat it as a passing test.

- [ ] **Step 6: Record final evidence**

Summarize the focused and full test counts, any skipped provider-dependent check, the commits created, and the exact files changed. Do not include unrelated user-owned worktree changes.
