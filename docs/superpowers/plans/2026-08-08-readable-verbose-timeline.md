# Readable Verbose Timeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `netzoo-chat` retain concise, readable, tool-aware progress blocks before its final result while preserving quiet and full diagnostic modes.

**Architecture:** Add `PRESENTATION_MODE` with compact, timeline, and verbose values. Keep `presentation._trace` as the graph's only rendering seam, adding a deterministic timeline formatter. The CLI normalizes display flags, while the launcher selects timeline by default.

**Tech Stack:** Python 3, argparse, existing NetZoo runtime settings, unittest/pytest, Bash.

## Global Constraints

- Do not disclose private or verbatim LLM chain-of-thought; render only existing structured decisions, validated evidence, tool metadata, and bounded deterministic summaries.
- No terminal UI dependency; timeline blocks must work in TTY and redirected stdout without ANSI clearing or timing delays.
- Preserve `--quiet` as final-answer-only, `--verbose` as complete diagnostic/audit output, direct Python CLI's compact default, and all current policy/trace/redaction/tool-authority rules.
- Retain English-only agent-authored user-visible output and do not alter unrelated user changes.

---

### Task 1: Create the presentation-mode runtime contract

**Files:**

- Modify: `scripts/netzoo_agent_core/settings.py`
- Modify: `scripts/netzoo_agent_core/runtime.py`
- Modify: `scripts/netzoo_agent_core/cli/arguments.py`
- Modify: `scripts/netzoo_agent_core/cli/loop.py`
- Create: `tests/test_presentation_timeline.py`

**Interfaces:**

- Consumes: `TRACE_ENABLED`, `VERBOSE_OUTPUT`, and `TRANSIENT_TRACE`.
- Produces: mutable `PRESENTATION_MODE: str` (`"compact" | "timeline" | "verbose"`) and `args.timeline: bool`.

- [ ] **Step 1: Write failing runtime-mode tests**

```python
from types import SimpleNamespace

from netzoo_agent_core import runtime, settings
from netzoo_agent_core.cli.loop import run_cli


def test_presentation_mode_is_mutable(monkeypatch):
    monkeypatch.setattr(settings, "PRESENTATION_MODE", "compact")
    runtime.configure_runtime(PRESENTATION_MODE="timeline")
    assert settings.PRESENTATION_MODE == "timeline"


def test_run_cli_selects_timeline_without_transient_output(monkeypatch):
    captured = {}
    monkeypatch.setattr("netzoo_agent_core.cli.loop.configure_runtime", lambda **values: captured.update(values))
    monkeypatch.setattr("netzoo_agent_core.cli.loop.handle_preflight_command", lambda _args: 0)
    args = SimpleNamespace(execute=False, quiet=False, verbose=False, timeline=True, transient_trace=False, tool_timeout=30.0)

    assert run_cli(args) == 0
    assert captured["PRESENTATION_MODE"] == "timeline"
    assert captured["TRANSIENT_TRACE"] is False
```

- [ ] **Step 2: Run the tests and verify failure**

Run: `pytest tests/test_presentation_timeline.py -v`

Expected: FAIL because `PRESENTATION_MODE` is not accepted by `configure_runtime` and the new flag is absent.

- [ ] **Step 3: Implement the minimal runtime/CLI contract**

```python
# settings.py
PRESENTATION_MODE = "compact"

# runtime.py
MUTABLE_RUNTIME_NAMES = frozenset(
    {
        "EXECUTE_TOOLS", "TRACE_ENABLED", "VERBOSE_OUTPUT", "TRANSIENT_TRACE",
        "PRESENTATION_MODE", "TRANSIENT_TRACE_MIN_SECONDS", "TOOL_TIMEOUT_SECONDS",
        "PROJECT_ROOT", "SESSION_ROOT", "TOOL_LOG_ROOT", "TRACE_ROOT",
        "PROFILE_ROOT", "EPISODE_ROOT",
    }
)

# arguments.py, inside the existing mutually exclusive display_group
display_group.add_argument(
    "--timeline", action="store_true",
    help="Show concise permanent activity blocks before the final answer.",
)

# loop.py
presentation_mode = "verbose" if args.verbose else "timeline" if args.timeline else "compact"
configure_runtime(
    EXECUTE_TOOLS=args.execute,
    TRACE_ENABLED=not args.quiet,
    VERBOSE_OUTPUT=args.verbose,
    PRESENTATION_MODE=presentation_mode,
    TOOL_TIMEOUT_SECONDS=args.tool_timeout,
    TRANSIENT_TRACE=(args.transient_trace and presentation_mode == "compact" and not args.quiet),
)
```

Export `PRESENTATION_MODE` from `settings.__all__`. The display group makes timeline, verbose, and quiet incompatible; transient mode remains accepted only alongside compact output.

- [ ] **Step 4: Run the tests and verify pass**

Run: `pytest tests/test_presentation_timeline.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/netzoo_agent_core/settings.py scripts/netzoo_agent_core/runtime.py scripts/netzoo_agent_core/cli/arguments.py scripts/netzoo_agent_core/cli/loop.py tests/test_presentation_timeline.py
git commit -m "feat: add timeline presentation mode"
```

### Task 2: Render permanent safe timeline blocks

**Files:**

- Modify: `scripts/netzoo_agent_core/presentation.py`
- Modify: `tests/test_presentation_timeline.py`

**Interfaces:**

- Consumes: `PRESENTATION_MODE`, `TRACE_ENABLED`, and controlled `_trace(stage, message, detail)` calls.
- Produces: `_render_timeline_block(stage: str, message: str, detail: str | None) -> str | None` and timeline handling in `_trace`.

- [ ] **Step 1: Write failing renderer tests**

```python
import netzoo_agent_core.presentation as presentation


def test_timeline_renders_permanent_tool_start(monkeypatch, capsys):
    monkeypatch.setattr(presentation, "TRACE_ENABLED", True)
    monkeypatch.setattr(presentation, "PRESENTATION_MODE", "timeline")

    presentation._trace("tool", "Executor [1/2]: inspect_inputs", "Check supplied files")

    output = capsys.readouterr().out
    assert "[Tool] Validating inputs" in output
    assert "Tool: inspect_inputs" in output
    assert "Purpose: Check supplied files" in output
    assert "\033[2K" not in output


def test_timeline_renders_safe_unknown_stage(monkeypatch, capsys):
    monkeypatch.setattr(presentation, "TRACE_ENABLED", True)
    monkeypatch.setattr(presentation, "PRESENTATION_MODE", "timeline")

    presentation._trace("unknown", "State dump: secret", "raw private payload")

    output = capsys.readouterr().out
    assert "[Agent activity]" in output
    assert "raw private payload" not in output
```

Add cases for tool completion, `intent`, `plan`, `review`, `input`, `evaluate`, and `recover`. Assert tool blocks explicitly include the tool action and that missing detail renders a fixed neutral sentence.

- [ ] **Step 2: Run the renderer tests and verify failure**

Run: `pytest tests/test_presentation_timeline.py -v`

Expected: FAIL because the timeline renderer and dispatch do not exist.

- [ ] **Step 3: Implement deterministic formatting**

```python
def _render_timeline_block(stage: str, message: str, detail: str | None = None) -> str:
    if stage == "tool":
        started = re.fullmatch(r"Executor \[\d+/\d+\]: (\w+)", message)
        if started:
            action = started.group(1)
            return _ui_text(
                f"[Tool] {_timeline_action_label(action)}\n"
                f"  Tool: {action}\n"
                f"  Purpose: {_bounded_timeline_detail(detail)}"
            )
    return _ui_text("[Agent activity]\n  Status: Activity update recorded.")


def _trace(stage: str, message: str, detail: str | None = None) -> None:
    if not TRACE_ENABLED:
        return
    if PRESENTATION_MODE == "timeline":
        print(_render_timeline_block(stage, message, detail), flush=True)
        print(flush=True)
        return
    # Preserve the existing verbose, transient, and compact branches below.
```

Use only whitelisted regexes for existing event messages. Add `_bounded_timeline_detail` to collapse whitespace, cap known-safe summary text at 240 characters, and return `"No additional details."` when absent. Unknown or unmatched events must use the generic block and never echo raw message/detail. Timeline branches must not call `_trace_line`, `_clear_transient_trace`, or `time.sleep`.

- [ ] **Step 4: Run the renderer tests and verify pass**

Run: `pytest tests/test_presentation_timeline.py -v`

Expected: PASS, including output permanence and safe fallback coverage.

- [ ] **Step 5: Commit**

```bash
git add scripts/netzoo_agent_core/presentation.py tests/test_presentation_timeline.py
git commit -m "feat: render readable agent timeline"
```

### Task 3: Enable timeline mode from `netzoo-chat` and document it

**Files:**

- Modify: `netzoo-chat`
- Modify: `README.md`
- Modify: `AGENT_USAGE.md`
- Modify: `tests/test_netzoo_chat_launcher.py`
- Modify: `tests/test_cli_package.py`

**Interfaces:**

- Consumes: CLI `--timeline`, `--verbose`, and `--quiet` flags.
- Produces: launcher default timeline mode; documented display-mode behavior.

- [ ] **Step 1: Write failing integration tests**

```python
def test_launcher_selects_timeline_mode_by_default():
    source = LAUNCHER.read_text()
    assert 'scripts/netzoo_agent.py --timeline "$@"' in source
    assert "--transient-trace" not in source


def test_timeline_is_mutually_exclusive_with_quiet(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["netzoo_agent.py", "--timeline", "--quiet"])
    with pytest.raises(SystemExit) as error:
        parse_args()
    assert error.value.code == 2
```

Keep the existing launcher observer-secret test intact. Add the parser test in `tests/test_cli_package.py` through its established CLI imports.

- [ ] **Step 2: Run the integration tests and verify failure**

Run: `pytest tests/test_netzoo_chat_launcher.py tests/test_cli_package.py -v`

Expected: FAIL because the launcher still supplies `--transient-trace`.

- [ ] **Step 3: Implement launcher and docs changes**

```bash
docker compose run --rm -it netzoo python scripts/netzoo_agent.py --timeline "$@"
```

Replace the launcher command with the above. In `README.md` and `AGENT_USAGE.md`, document that `netzoo-chat` now prints concise permanent blocks for planning, tools, results, and evaluation; `--verbose` is the full audit view; `--quiet` hides progress; and these are auditable summaries, not private chain-of-thought. Keep direct `python scripts/netzoo_agent.py` documented as compact unless `--timeline` is supplied.

- [ ] **Step 4: Run focused regression tests**

Run: `pytest tests/test_presentation_timeline.py tests/test_netzoo_chat_launcher.py tests/test_cli_package.py tests/test_graph_tracing.py tests/test_trace_redaction.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add netzoo-chat README.md AGENT_USAGE.md tests/test_netzoo_chat_launcher.py tests/test_cli_package.py
git commit -m "feat: enable timeline in netzoo chat"
```

### Task 4: Verify complete regression and observable CLI modes

**Files:**

- Modify: no production files expected
- Test: `tests/`

**Interfaces:**

- Consumes: completed timeline mode and the existing CLI modes.
- Produces: final evidence that existing behavior remains compatible.

- [ ] **Step 1: Run the full unit suite**

Run: `pytest -q`

Expected: PASS with no regression in policy gates, graph tracing, CLI compatibility, or launcher behavior.

- [ ] **Step 2: Perform command-line display checks**

```bash
python scripts/netzoo_agent.py --timeline --task "Run a PANDA demo"
python scripts/netzoo_agent.py --quiet --task "Explain PANDA inputs"
python scripts/netzoo_agent.py --verbose --task "Explain PANDA inputs"
```

Expected: timeline blocks then final answer; quiet has no progress; verbose has full existing detail. If a model provider key is unavailable, verify parsing/runtime initialization and rely on unit tests instead of treating the provider configuration as a code failure.

- [ ] **Step 3: Inspect final changes and commit only required test corrections**

Run: `git diff --check && git status --short`

Expected: no whitespace errors and no unrelated staged files. If a correction is required, stage only feature files and commit with `test: stabilize timeline presentation coverage`.
