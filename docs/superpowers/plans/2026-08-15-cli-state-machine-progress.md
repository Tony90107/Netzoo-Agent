# CLI State-Machine Progress Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace independent progress messages with a compact, fact-grounded CLI state machine that retains completed stages and exposes only actual tool activity.

**Architecture:** Existing graph events remain unchanged. `presentation.py` owns a `ProgressState` with `understand`, `match`, and `next_step` stages. Recognized public events update the state; a TTY redraws one block and non-TTY streams receive permanent summaries. Existing tool events are rendered as permanent records below the block.

**Tech Stack:** Python 3.12, existing ANSI terminal output, pytest.

## Global Constraints

- Normal mode must never render raw prompts, chain-of-thought, memory/provider payloads, or unknown graph events.
- A tool record can only be rendered from an existing graph tool start/completion event.
- Keep `--verbose`, `--quiet`, `--timeline`, and non-TTY output compatible.
- Preserve unrelated dirty files and use `apply_patch` for edits.

---

### Task 1: Build the pure state model and renderer

**Files:** Modify `scripts/netzoo_agent_core/presentation.py:1-188`; test `tests/test_presentation_timeline.py`.

**Interfaces:** `ProgressStage(label, status, detail=None)`, `ProgressState.initial()`, `activate(name, detail=None)`, `complete(name)`, `attention(name, detail)`, `fail(name, detail)`, and `_render_progress_state(state) -> str`.

- [ ] Add failing tests for a state whose `match` stage is active and for an attention state on `next_step`.
- [ ] Run `python -m pytest -q tests/test_presentation_timeline.py -k progress_state`; expect failure because `ProgressState` is absent.
- [ ] Implement code-owned labels `Understand request`, `Match workflow capabilities`, and `Choose next step`; render status markers `✓`, `●`, `○`, `!`, and `✗`. `activate()` completes earlier steps and leaves exactly one active step.
- [ ] Re-run the focused test; expect pass.
- [ ] Commit with `git add scripts/netzoo_agent_core/presentation.py tests/test_presentation_timeline.py` then `git commit -m "feat: add CLI progress state model"`.

### Task 2: Restrict state transitions to public graph events

**Files:** Modify `scripts/netzoo_agent_core/presentation.py:70-165`; test `tests/test_presentation_timeline.py`.

**Interfaces:** `_apply_public_progress_event(state, stage, message, detail) -> bool`.

- [ ] Add a failing test that sends the three existing events: `Interpreting the request and capability boundaries`, `Checking registered workflow capabilities`, and `Choosing the next safe step`; assert the rendered history contains completed understand/match stages and active next-step stage.
- [ ] Run `python -m pytest -q tests/test_presentation_timeline.py -k public_trace_events_update`; expect failure.
- [ ] Map only `(intent, Interpreting the request and capability boundaries)` to `understand`, `(reasoning, Checking registered workflow capabilities)` to `match`, and `(reasoning, Choosing the next safe step)` to `next_step`. Use `_bounded_timeline_detail` only on the active stage; map planner input and capability ambiguity to `attention("next_step", ...)`; ignore all other normal-mode events.
- [ ] Re-run the focused test; expect pass.
- [ ] Commit with message `feat: map public graph events to CLI progress`.

### Task 3: Add TTY redraw, non-TTY fallback, and final retention

**Files:** Modify `scripts/netzoo_agent_core/presentation.py:165-280`; test `tests/test_presentation_timeline.py`.

**Interfaces:** `_render_or_update_progress_state(state) -> None` and `_finalize_progress_state() -> None`.

- [ ] Add failing tests asserting that TTY transitions include cursor-up/clear ANSI codes and non-TTY transitions contain no ANSI codes but do contain a permanent active state line.
- [ ] Run `python -m pytest -q tests/test_presentation_timeline.py -k 'redraws_on_tty or permanent_lines_on_non_tty'`; expect failure.
- [ ] Track the prior state-block line count. On a TTY, clear and redraw that many lines; on non-TTY, print only changed blocks. Finalize before final response output so the final block remains visible. Keep transient trace behavior unchanged outside `state_machine` mode.
- [ ] Re-run the focused tests; expect pass.
- [ ] Commit with message `feat: render CLI progress state in place`.

### Task 4: Render real tool activity as permanent records

**Files:** Modify `scripts/netzoo_agent_core/presentation.py:110-145,220-280`; test `tests/test_presentation_timeline.py`.

**Interfaces:** `_render_tool_activity(action, status, detail) -> str`.

- [ ] Add a failing test for `Executor [1/1]: run_lioness_puma` followed by `run_lioness_puma → success`; assert the permanent output contains `Tool: run_lioness_puma`, its supplied result detail, and `✓ Run LIONESS-PUMA`.
- [ ] Run `python -m pytest -q tests/test_presentation_timeline.py -k tool_activity_is_permanent`; expect failure.
- [ ] Reuse `_timeline_action_label`, `_timeline_result_label`, and `_bounded_timeline_detail`. Move past the live TTY block before printing each permanent tool record, then redraw it. Never manufacture command, input, or result text. A failed tool marks `next_step` failed.
- [ ] Re-run focused tool tests; expect pass.
- [ ] Commit with message `feat: show verified CLI tool activity`.

### Task 5: Make the state machine the default and verify modes

**Files:** Modify `scripts/netzoo_agent_core/cli/loop.py:13-36` and `scripts/netzoo_agent_core/cli/arguments.py:220-255`; test `tests/test_presentation_timeline.py`.

**Interfaces:** default `PRESENTATION_MODE="state_machine"` when no display flag is chosen.

- [ ] Add a failing `run_cli` test that captures `configure_runtime` and asserts its default mode is `state_machine`.
- [ ] Run `python -m pytest -q tests/test_presentation_timeline.py -k state_machine_by_default`; expect failure because default is `compact`.
- [ ] Select state-machine mode only without an explicit display flag. Preserve `--timeline` as legacy permanent blocks, `--verbose` as detailed technical events, and `--quiet` as silent. Update option help text.
- [ ] Run `python -m pytest -q && python -m compileall -q scripts && git diff --check`; expect all tests and compilation to pass.
- [ ] Manually run `./netzoo-chat` with `help me to find mi-RNA regulator network with the data i have currently.`; expect the three stages to update in one block and remain above the aggregate/sample-specific clarification, with no tool record.
- [ ] Commit with message `feat: use state-machine CLI progress by default`.

## Plan Self-Review

Tasks 1-3 cover all display-state requirements, Task 4 restricts activity records to executed tools, and Task 5 protects modes plus provides automated/manual acceptance. Interfaces are consistently named and no task relies on unspecified behavior.
