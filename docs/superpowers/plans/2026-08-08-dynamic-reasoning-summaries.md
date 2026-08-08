# Dynamic Reasoning Summaries Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace fixed timeline labels with natural, truthful Agent progress summaries.

**Architecture:** A presentation helper turns only sanitized Router, Plan, Tool, Evaluation, and policy facts into public summaries; normal typed state remains the verification source.

**Tech Stack:** Python 3 and pytest.

## Global Constraints

- Never show private chain-of-thought, raw prompt/model text, secrets, memory records, or raw command output.
- Public summaries cannot claim a tool, file, result, or authority that typed state does not support.
- Keep verbose audit output and quiet output behavior unchanged.

---

### Task 1: Add grounded summary generation

**Files:**

- Create: `scripts/netzoo_agent_core/progress_summaries.py`
- Create: `tests/test_progress_summaries.py`

- [ ] Write a failing test asserting a no-tool concept fact renders: "This only needs an explanation, so I do not need to inspect files or run tools."
- [ ] Run `pytest tests/test_progress_summaries.py -v` and observe failure.
- [ ] Implement `render_progress_summary(kind: str, facts: dict[str, str]) -> str | None` with bounded fact-only fallbacks for concept, planning, tool start/result, missing input, recovery, and evaluation.
- [ ] Run `pytest tests/test_progress_summaries.py -v` and commit `feat: add grounded progress summaries`.

### Task 2: Render summaries in timeline mode

**Files:**

- Modify: `scripts/netzoo_agent_core/presentation.py`
- Modify: `tests/test_presentation_timeline.py`

- [ ] Write a failing test that a no-tool intent does not display the literal string `no_tool`.
- [ ] Run `pytest tests/test_presentation_timeline.py -v` and observe failure.
- [ ] Route timeline intent, plan, tool, input, recovery, and evaluation facts through `render_progress_summary`; retain raw structured rendering for verbose mode.
- [ ] Run `pytest tests/test_progress_summaries.py tests/test_presentation_timeline.py tests/test_graph_tracing.py -v` and commit `feat: narrate agent progress`.

### Task 3: Verify compatibility

- [ ] Run `pytest -q`.
- [ ] Run `git diff --check` and confirm only feature files are staged.
