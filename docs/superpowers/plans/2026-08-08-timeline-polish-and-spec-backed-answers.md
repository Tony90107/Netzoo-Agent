# Timeline Polish and Spec-Backed Answers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove low-value timeline noise and answer basic registered-workflow purpose questions from validated policy metadata.

**Architecture:** Make the timeline formatter return `None` for setup, completion, and unknown events. Add a focused interpretation helper that maps basic purpose/function questions to `ProjectPolicySnapshot.workflows`, then let the response graph use its deterministic result before an LLM call.

**Tech Stack:** Python 3, Pydantic policy contracts, pytest.

## Global Constraints

- Do not expose private LLM chain-of-thought, raw event payloads, or unbounded model text.
- Preserve verbose trace visibility, quiet output, workflow/tool authority, and persisted trace schema.
- Use registered workflow description and required inputs; do not hardcode PANDA/PUMA/LIONESS/CONDOR prose in the renderer.
- Keep English-only agent-authored output and do not alter unrelated user changes.

---

### Task 1: Suppress setup and duplicate completion timeline noise

**Files:**

- Modify: `scripts/netzoo_agent_core/presentation.py`
- Modify: `tests/test_presentation_timeline.py`

**Interfaces:**

- Consumes: `_trace(stage: str, message: str, detail: str | None)`.
- Produces: `_render_timeline_block(...) -> str | None`; `_trace` prints only non-`None` blocks in timeline mode.

- [ ] **Step 1: Write failing suppression tests**

```python
def test_timeline_suppresses_setup_completion_and_unknown_events(monkeypatch, capsys):
    _enable_timeline(monkeypatch)
    for stage, message in (
        ("policy", "Project policy loaded: version=1, hash=abc"),
        ("memory", "Memory retrieval: profile=default, episodes=0"),
        ("done", "Session: abc123"),
        ("done", "LLM tokens: input=1, output=2, total=3, budget=10"),
        ("unknown", "private message"),
    ):
        presentation._trace(stage, message, "private detail")
    assert capsys.readouterr().out == ""
```

- [ ] **Step 2: Run focused tests to verify failure**

Run: `pytest tests/test_presentation_timeline.py -v`

Expected: FAIL because timeline currently emits generic activity/completion blocks.

- [ ] **Step 3: Implement suppression**

```python
def _render_timeline_block(...) -> str | None:
    # Return blocks only for recognized intent, plan, review, input, tool,
    # evaluate, and recovery messages; otherwise return None.

if PRESENTATION_MODE == "timeline":
    block = _render_timeline_block(stage, message, detail)
    if block:
        print(block, flush=True)
        print(flush=True)
    return
```

- [ ] **Step 4: Run focused tests to verify pass**

Run: `pytest tests/test_presentation_timeline.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/netzoo_agent_core/presentation.py tests/test_presentation_timeline.py
git commit -m "fix: suppress timeline setup noise"
```

### Task 2: Render basic concept answers from policy metadata

**Files:**

- Create: `scripts/netzoo_agent_core/interpretation/concept_answers.py`
- Modify: `scripts/netzoo_agent_core/interpretation/__init__.py`
- Modify: `scripts/netzoo_agent_core/graph/response.py`
- Create: `tests/test_concept_answers.py`

**Interfaces:**

- Consumes: `task: str`, `TaskDecision`, and `ProjectPolicySnapshot`.
- Produces: `render_spec_backed_concept_answer(task, decision, policy) -> str | None`.

- [ ] **Step 1: Write failing metadata-driven tests**

```python
def test_purpose_question_uses_registered_workflow_description(policy, decision):
    answer = render_spec_backed_concept_answer(
        "what is the function of PANDA", decision, policy
    )
    assert "Infer an aggregate TF-to-gene regulatory network" in answer
    assert "No files were inspected and no analysis ran." in answer


def test_registered_new_workflow_needs_no_hardcoded_renderer_branch(policy, decision):
    policy.workflows["run_condor"].workflow = "BIPARTITE"
    policy.workflows["run_condor"].description = "Discover communities in a bipartite network."
    answer = render_spec_backed_concept_answer("what is BIPARTITE for", decision, policy)
    assert "Discover communities in a bipartite network." in answer
```

- [ ] **Step 2: Run concept tests to verify failure**

Run: `pytest tests/test_concept_answers.py -v`

Expected: FAIL because the helper does not exist.

- [ ] **Step 3: Implement helper and response integration**

```python
def render_spec_backed_concept_answer(task, decision, policy) -> str | None:
    if not (decision.in_scope and decision.action == "no_tool" and decision.intent_type == "answer_question"):
        return None
    if not re.search(r"\b(function|purpose|what is|what does)\b", task, re.I):
        return None
    for spec in policy.workflows.values():
        if spec.workflow.casefold() in task.casefold():
            inputs = ", ".join(spec.required_inputs) or "no registered required inputs"
            return _ui_text(f"{spec.workflow} {spec.description}\n\nRegistered required inputs: {inputs}.\nNo files were inspected and no analysis ran.")
    return None
```

Call the helper in `respond()` after needs-input/rejection branches and before constructing response-model messages. When it returns text, return `AIMessage(content=text)` without invoking the response LLM.

- [ ] **Step 4: Run focused tests to verify pass**

Run: `pytest tests/test_concept_answers.py tests/test_graph_package.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/netzoo_agent_core/interpretation scripts/netzoo_agent_core/graph/response.py tests/test_concept_answers.py
git commit -m "feat: answer workflow concepts from policy specs"
```

### Task 3: Verify regression coverage

**Files:**

- Modify: no production files expected
- Test: `tests/`

- [ ] **Step 1: Run relevant regression tests**

Run: `pytest tests/test_presentation_timeline.py tests/test_concept_answers.py tests/test_agent_gate.py tests/test_graph_tracing.py -v`

Expected: PASS.

- [ ] **Step 2: Run the complete suite and inspect the diff**

Run: `pytest -q && git diff --check && git status --short`

Expected: full suite passes, no whitespace errors, and no unrelated feature files are staged.
