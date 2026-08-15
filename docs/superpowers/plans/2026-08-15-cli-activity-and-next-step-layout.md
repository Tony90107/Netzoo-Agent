# CLI Activity and Next-Step Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement task-by-task.

**Goal:** Render Activity and Next step as separate CLI sections and suppress duplicate clarification prose.

**Architecture:** Update presentation rendering to add section spacing and expose a CLI-owned clarification marker to response generation. Preserve tool cards and normal answers.

**Tech Stack:** Python, pytest.

## Global Constraints

- Only public facts are rendered.
- A clarification appears once, in Next step.

### Task 1: Render sectioned CLI output

**Files:** Modify `scripts/netzoo_agent_core/presentation.py`; test `tests/test_presentation_timeline.py`.

- [ ] Write failing tests for `Activity`, `Next step`, one clarification, and tool-card preservation.
- [ ] Run `pytest tests/test_presentation_timeline.py -k 'activity or clarification' -v` and verify failure.
- [ ] Implement section headings, blank-line boundaries, and one compact reply hint.
- [ ] Run the focused test and verify pass.

### Task 2: Suppress duplicate answer content

**Files:** Modify CLI response/conversation code identified by existing clarification response tests; test its existing test module.

- [ ] Write a failing test showing a CLI-owned clarification is not repeated in the answer.
- [ ] Implement the response marker and suppression branch without changing ordinary responses.
- [ ] Run focused tests, then `pytest -q`.
- [ ] Commit: `git commit -m "feat: clarify CLI activity layout"`.
