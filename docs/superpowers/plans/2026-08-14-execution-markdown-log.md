# Execution Markdown Log Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Save an independent timestamped Markdown execution record beside every actual workflow output.

**Architecture:** Add a focused execution-log writer that receives a validated `TaskDecision`, action, structured result, and raw adapter output. `structure_tool_result` calls it only for non-dry-run execute steps after output validation, retaining the existing private raw `.log` separately.

**Tech Stack:** Python 3, pathlib, pytest.

## Global Constraints

- Dry runs create no Markdown execution log.
- Write `<workflow>-execution-YYYYMMDD-HHMMSS.md` inside the validated output directory using exclusive creation.
- Include timestamps, action, exact command, preparation/validation report, status, diagnostics, and artifacts.
- Persist logs for both successful and failed Execute-mode steps without overwriting inputs, outputs, or previous logs.

---

### Task 1: Create the Markdown execution-log writer

**Files:**
- Create: `scripts/netzoo_agent_core/execution_log.py`
- Test: `tests/test_execution_log.py`

**Interfaces:**
- Consumes: `TaskDecision`, action, raw output, `ToolExecutionResult` fields.
- Produces: `write_execution_markdown_log(...) -> str | None`, returning the created display path.

- [ ] **Step 1: Write failing writer tests**

Test timestamped filename, exclusive non-overwrite behavior, command fenced block, preparation report, failure diagnostics, and output paths using `tmp_path`.

- [ ] **Step 2: Run the writer test**

Run: `pytest tests/test_execution_log.py -v`

Expected: FAIL because the writer does not exist.

- [ ] **Step 3: Implement the writer**

Resolve the log directory from `decision.output_dir` or `Path(decision.output_file).parent`; parse the existing `Command: ...` raw-output line; render sections and atomically create a timestamped `.md` with an incrementing suffix on a timestamp collision.

- [ ] **Step 4: Run writer tests**

Run: `pytest tests/test_execution_log.py -v`

Expected: PASS.

### Task 2: Integrate logs at the structured execution boundary

**Files:**
- Modify: `scripts/netzoo_agent_core/routing/results.py`
- Modify: `tests/test_agent_gate.py`

**Interfaces:**
- Consumes: `structure_tool_result(action, decision, raw_output, persist_log=True)`.
- Produces: an execution-log path in `ToolExecutionResult.metrics["execution_markdown_log"]` for Execute-mode workflow actions.

- [ ] **Step 1: Write failing integration tests**

Assert Execute-mode successful and failed results create a Markdown log in the output directory, while a `Dry run only` result produces none.

- [ ] **Step 2: Run the focused integration tests**

Run: `pytest tests/test_agent_gate.py -k 'execution_markdown_log' -v`

Expected: FAIL because no public execution log is written.

- [ ] **Step 3: Integrate without changing executor authority**

After the structured result determines status and artifacts, call the writer only when `persist_log` is true and `status != "dry_run"`. Preserve the existing private raw-log behavior and convert writer I/O failure into a warning rather than hiding the workflow result.

- [ ] **Step 4: Run targeted regression and commit**

Run: `pytest tests/test_execution_log.py tests/test_agent_gate.py tests/test_cli_lifecycle.py -v`

Expected: PASS.

Commit writer, routing integration, and tests with message `feat: write execution markdown logs`.
