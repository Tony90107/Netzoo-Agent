# NetZoo Execution Boundary Stability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make CONDOR completion strict, isolate each agent session's runtime
authority, rewrite LIONESS-PUMA headers safely for large outputs, and evaluate every
deterministic execution boundary in the offline harness.

**Architecture:** Preserve the existing CLI, LangGraph, and allow-listed tool
surface. Deepen four deterministic seams: the CONDOR wrapper owns algorithm
completion, an immutable runtime value owns per-session settings, the header helper
owns atomic streaming replacement, and typed harness families own regression
measurement. The companion state-stability plan supplies typed continuations,
effective outcomes, bundle provenance, artifact validation, and overwrite gates.

**Tech Stack:** Python 3.10+, Pydantic, LangGraph, LangChain tools, pandas, NumPy,
`contextvars`, `tempfile`, `unittest`/pytest, Ruff, Docker Compose.

## Global Constraints

- Python types and deterministic rules own execution authority.
- Markdown and natural-language text are presentation formats, never control
  protocols.
- Agent uncertainty blocks execution as `needs_input`; validated incompatibility
  becomes `failed`.
- File existence is necessary but not sufficient evidence of successful analysis.
- CONDOR requires non-empty, parseable regulator and target membership tables.
- Core modules must not scan or mutate `sys.modules`.
- A header-insertion failure must leave the original LIONESS output intact.
- The harness remains offline and cannot approve execution from free-form text.
- Existing public tool names, command arguments, workflow YAML, dry-run behavior,
  and legacy facade imports remain compatible.
- Do not add an algorithm, shell authority, dependency, external service, or LLM
  evaluator.
- Do not stage unrelated dirty-worktree files. Review
  `git diff --cached --name-only` before every commit.

---

## File Structure

- `docker/run-condor`: enforce algorithm completion and write both membership
  partitions.
- `scripts/netzoo_agent_core/execution.py`: declare the exact CONDOR artifacts
  expected from the wrapper.
- `tests/test_condor_runner.py`: import the wrapper as a module and test API
  compatibility failures without running NetZooPy.
- `scripts/netzoo_agent_core/runtime.py`: immutable `RuntimeConfig`, scoped
  activation, and legacy override adapter.
- `scripts/netzoo_agent_core/contracts.py`: retain data contracts and constants that
  are genuinely static; remove mutable runtime ownership.
- `scripts/netzoo_agent.py`: keep legacy assignment compatibility without mutating
  implementation modules.
- `scripts/netzoo_agent_core/command.py`: consume execution mode and timeout from an
  explicit runtime.
- `scripts/netzoo_agent_core/graph.py`: capture one runtime per compiled graph and
  pass it to execution and result normalization.
- `scripts/netzoo_agent_core/routing.py`: bridge the graph runtime into decorated
  LangChain tool adapters and runtime-specific log storage.
- `scripts/netzoo_agent_core/{cli,planning,validation,preparation,evaluation}.py`:
  consume the active or explicitly supplied runtime instead of imported mutable
  globals.
- `scripts/netzoo_agent_core/{memory,session,policy}.py`: receive storage/project
  roots through constructors or function arguments.
- `docker/add-puma-lioness-header`: stream through a same-directory temporary file
  and replace atomically.
- `scripts/evaluate_harness.py`: dispatch typed scenario families and report
  per-family metrics.
- `tests/harness_scenarios.json`: cover planner, evaluator, continuation, executor,
  recovery, and artifact validation.
- `tests/test_evaluate_harness.py`: verify family dispatch and safety counters.
- `tests/test_agent_gate.py`: cross-boundary runtime, command, CLI, and header
  regression coverage.
- `AGENT_USAGE.md`: document strict CONDOR failure and runtime isolation.

### Task 1: Require complete CONDOR community membership output

**Files:**
- Modify: `docker/run-condor:23-155`
- Modify: `scripts/netzoo_agent_core/execution.py:435-478`
- Create: `tests/test_condor_runner.py`
- Test: `tests/test_agent_gate.py`

**Interfaces:**
- Produces: `CondorExecutionError`.
- Produces: `run_first_supported(obj, phase, candidates) -> str`.
- Produces: `required_memberships(obj) -> tuple[pd.DataFrame, pd.DataFrame]`.
- Changes: `write_outputs(...) -> list[Path]` returns the four files it wrote.
- Guarantees: exit code zero requires both `PREFIX-reg_memb.tsv` and
  `PREFIX-tar_memb.tsv`.

- [ ] **Step 1: Write failing wrapper tests**

Load the extensionless wrapper through `SourceFileLoader` and add:

```python
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
import unittest

import pandas as pd


WRAPPER = Path(__file__).parents[1] / "docker" / "run-condor"
LOADER = SourceFileLoader("tested_run_condor", str(WRAPPER))
SPEC = spec_from_loader(LOADER.name, LOADER)
condor_runner = module_from_spec(SPEC)
LOADER.exec_module(condor_runner)


class CondorRunnerTests(unittest.TestCase):
    def test_both_membership_partitions_are_required(self):
        obj = type(
            "PartialCondor",
            (),
            {
                "reg_memb": pd.DataFrame({"reg": ["TF1"], "community": [0]}),
                "tar_memb": pd.DataFrame(),
            },
        )()
        with self.assertRaisesRegex(
            condor_runner.CondorExecutionError,
            "tar_memb",
        ):
            condor_runner.required_memberships(obj)

    def test_algorithm_failures_are_reported_with_method_context(self):
        class BrokenCondor:
            def brim(self, **kwargs):
                raise ValueError("modularity did not converge")

            def condor_run(self):
                raise RuntimeError("fallback failed")

            def run(self):
                raise AttributeError("not implemented")

        candidates = condor_runner.run_method_candidates(BrokenCondor())
        with self.assertRaisesRegex(
            condor_runner.CondorExecutionError,
            "brim.*ValueError.*modularity did not converge",
        ):
            condor_runner.run_first_supported(
                BrokenCondor(),
                "community optimization",
                candidates,
            )
```

Add a happy-path fixture containing non-empty `reg_memb` and `tar_memb`, call
`write_outputs`, and assert the returned paths include:

```python
{
    output_dir / "toy-edges.tsv",
    output_dir / "toy-reg_memb.tsv",
    output_dir / "toy-tar_memb.tsv",
    output_dir / "toy-summary.txt",
}
```

- [ ] **Step 2: Run the wrapper tests and verify they fail**

Run:

```bash
python -m unittest tests.test_condor_runner -v
```

Expected: FAIL because `CondorExecutionError`, `required_memberships`,
`run_method_candidates`, and `run_first_supported` do not exist and partial
membership currently returns success.

- [ ] **Step 3: Preserve candidate-method errors instead of swallowing them**

Add:

```python
class CondorExecutionError(RuntimeError):
    """The available CONDOR API could not produce a complete result."""


def run_first_supported(obj, phase: str, candidates) -> str:
    errors: list[str] = []
    for label, call in candidates:
        try:
            call()
            return label
        except Exception as error:  # noqa: BLE001 - compatibility probe audit.
            errors.append(f"{label}: {type(error).__name__}: {error}")
    raise CondorExecutionError(
        f"CONDOR {phase} failed for every supported API:\n" + "\n".join(errors)
    )


def initialization_candidates(obj):
    return (
        ("initial_community(method='LDN')", lambda: obj.initial_community(method="LDN")),
        ("initial_community()", lambda: obj.initial_community()),
    )


def run_method_candidates(obj):
    return (
        ("brim(deltaQmin='def', c='def')", lambda: obj.brim(deltaQmin="def", c="def")),
        ("brim()", lambda: obj.brim()),
        ("condor_run()", lambda: obj.condor_run()),
        ("run()", lambda: obj.run()),
    )
```

Replace `run_condor` with:

```python
def run_condor(obj) -> tuple[str, str]:
    initialized_by = run_first_supported(
        obj,
        "initialization",
        initialization_candidates(obj),
    )
    completed_by = run_first_supported(
        obj,
        "community optimization",
        run_method_candidates(obj),
    )
    return initialized_by, completed_by
```

The compatibility probes may try later candidates, but every failed candidate
retains its method, exception type, and message in the terminal error.

- [ ] **Step 4: Validate both memberships before returning success**

Add:

```python
def required_memberships(obj) -> tuple[pd.DataFrame, pd.DataFrame]:
    values = []
    problems = []
    for attr_name in ("reg_memb", "tar_memb"):
        value = getattr(obj, attr_name, None)
        if not isinstance(value, pd.DataFrame):
            problems.append(f"{attr_name} is not a pandas DataFrame")
        elif value.empty:
            problems.append(f"{attr_name} is empty")
        else:
            values.append(value)
    if problems:
        raise CondorExecutionError(
            "CONDOR did not produce both membership partitions: "
            + "; ".join(problems)
        )
    return values[0], values[1]
```

Call this before writing terminal outputs. Write both data frames explicitly:

```python
reg_memb, tar_memb = required_memberships(obj)
reg_path = output_dir / f"{prefix}-reg_memb.tsv"
tar_path = output_dir / f"{prefix}-tar_memb.tsv"
reg_memb.to_csv(reg_path, sep="\t", index=False)
tar_memb.to_csv(tar_path, sep="\t", index=False)
```

Include the chosen initialization and optimization method in the summary. Catch
`CondorExecutionError` in `main` and convert it to `SystemExit(str(error))`, so the
wrapper exits non-zero with an actionable message.

- [ ] **Step 5: Require the membership paths at the agent command boundary**

Change `run_condor` in `execution.py` to declare:

```python
expected_outputs = [
    str(output_path / f"{prefix or 'condor'}-edges.tsv"),
    str(output_path / f"{prefix or 'condor'}-reg_memb.tsv"),
    str(output_path / f"{prefix or 'condor'}-tar_memb.tsv"),
    str(output_path / f"{prefix or 'condor'}-summary.txt"),
]
```

This causes `_run_command` and the companion artifact validator to reject a
zero-exit wrapper that omitted either partition.

- [ ] **Step 6: Run focused and existing CONDOR tests**

Run:

```bash
python -m unittest tests.test_condor_runner -v
python -m unittest discover -s tests -p 'test_agent_gate.py' -k condor -v
```

Expected: all tests pass; partial memberships and total API failure exit non-zero.

- [ ] **Step 7: Commit Task 1 only**

```bash
git add docker/run-condor scripts/netzoo_agent_core/execution.py tests/test_condor_runner.py tests/test_agent_gate.py
git diff --cached --check
git diff --cached --name-only
git commit -m "fix: require complete CONDOR membership output"
```

### Task 2: Replace process-wide runtime mutation with immutable session config

**Files:**
- Modify: `scripts/netzoo_agent_core/runtime.py`
- Modify: `scripts/netzoo_agent_core/contracts.py:60-191,270-360,720-740`
- Modify: `scripts/netzoo_agent.py:55-110`
- Modify: `scripts/netzoo_agent_core/cli.py:1-110,300-455`
- Modify: `scripts/netzoo_agent_core/graph.py:1-190,330-640`
- Modify: `scripts/netzoo_agent_core/command.py:1-160`
- Modify: `scripts/netzoo_agent_core/routing.py:1-90,740-875`
- Modify: `scripts/netzoo_agent_core/planning.py`
- Modify: `scripts/netzoo_agent_core/validation.py`
- Modify: `scripts/netzoo_agent_core/preparation.py`
- Modify: `scripts/netzoo_agent_core/evaluation.py`
- Modify: `scripts/netzoo_agent_core/memory.py`
- Modify: `scripts/netzoo_agent_core/session.py`
- Modify: `scripts/netzoo_agent_core/policy.py`
- Modify: `scripts/netzoo_agent_core/__init__.py`
- Test: `tests/test_agent_gate.py`

**Interfaces:**
- Produces: immutable `RuntimeConfig`.
- Produces: `current_runtime() -> RuntimeConfig`.
- Produces: `activate_runtime(config) -> ContextManager[RuntimeConfig]`.
- Produces: `set_legacy_runtime_value(name, value) -> RuntimeConfig`.
- Changes: `build_graph(..., runtime_config: RuntimeConfig | None = None)`.
- Changes: `_run_command(..., runtime_config: RuntimeConfig | None = None)`.
- Changes: `execute_selected_tool(decision, runtime_config=None)`.
- Changes: `structure_tool_result(..., runtime_config=None)`.
- Guarantees: explicit configurations never read or mutate another session's state.

- [ ] **Step 1: Write failing isolation and compatibility tests**

Add:

```python
def test_two_explicit_runtime_configs_do_not_share_execution_authority(self):
    dry = agent.RuntimeConfig(execute_tools=False)
    live = agent.RuntimeConfig(execute_tools=True, tool_timeout_seconds=5)
    command = [sys.executable, "-c", "print('ran')"]

    dry_result = agent._run_command(command, runtime_config=dry)
    live_result = agent._run_command(command, runtime_config=live)

    self.assertIn("Dry run only", dry_result)
    self.assertIn("Exit code: 0", live_result)
    self.assertIn("ran", live_result)
    self.assertFalse(dry.execute_tools)


def test_runtime_activation_resets_after_scope(self):
    original = agent.current_runtime()
    isolated = agent.RuntimeConfig(execute_tools=True, project_root=Path("/tmp/a"))
    with agent.activate_runtime(isolated):
        self.assertIs(agent.current_runtime(), isolated)
    self.assertIs(agent.current_runtime(), original)


def test_legacy_override_does_not_mutate_explicit_config(self):
    explicit = agent.RuntimeConfig(execute_tools=False)
    previous = agent.EXECUTE_TOOLS
    try:
        agent.EXECUTE_TOOLS = True
        self.assertTrue(agent.current_runtime().execute_tools)
        self.assertFalse(explicit.execute_tools)
    finally:
        agent.EXECUTE_TOOLS = previous
```

Add a two-thread test using a `threading.Barrier`; each worker activates a different
`RuntimeConfig`, waits at the barrier, and returns its own `execute_tools`,
`project_root`, and `tool_log_root`. Assert neither worker observes the other.

- [ ] **Step 2: Run runtime tests and prove the shared-global defect**

Run:

```bash
python -m unittest discover -s tests -p 'test_agent_gate.py' -k runtime -v
```

Expected: FAIL because `RuntimeConfig` and scoped activation do not exist and
legacy assignment currently scans and mutates loaded implementation modules.

- [ ] **Step 3: Define the immutable runtime value and scoped adapter**

Replace `runtime.py` with:

```python
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, replace
from pathlib import Path


DEFAULT_PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    execute_tools: bool = False
    trace_enabled: bool = False
    verbose_output: bool = False
    transient_trace: bool = False
    transient_trace_min_seconds: float = 0.6
    tool_timeout_seconds: float = 86_400.0
    project_root: Path = DEFAULT_PROJECT_ROOT

    @property
    def session_root(self) -> Path:
        return self.project_root / ".netzoo" / "sessions"

    @property
    def tool_log_root(self) -> Path:
        return self.project_root / ".netzoo" / "logs"

    @property
    def profile_root(self) -> Path:
        return self.project_root / ".netzoo" / "memory" / "profiles"

    @property
    def episode_root(self) -> Path:
        return self.project_root / ".netzoo" / "memory" / "episodes"


DEFAULT_RUNTIME = RuntimeConfig()
_ACTIVE_RUNTIME: ContextVar[RuntimeConfig] = ContextVar(
    "netzoo_runtime",
    default=DEFAULT_RUNTIME,
)


def current_runtime() -> RuntimeConfig:
    return _ACTIVE_RUNTIME.get()


@contextmanager
def activate_runtime(config: RuntimeConfig):
    token = _ACTIVE_RUNTIME.set(config)
    try:
        yield config
    finally:
        _ACTIVE_RUNTIME.reset(token)
```

Add a fixed legacy-name map and implement `set_legacy_runtime_value` with
`dataclasses.replace(current_runtime(), **{field_name: value})`. It sets only the
current context variable and rejects unknown names. Delete all `sys.modules`
iteration.

- [ ] **Step 4: Make command execution consume an explicit runtime**

Change:

```python
def _run_command(
    command: list[str],
    output_file: str | None = None,
    additional_output_files: list[str] | None = None,
    allow_overwrite: bool = False,
    runtime_config: RuntimeConfig | None = None,
) -> str:
    runtime = runtime_config or current_runtime()
```

Use `runtime.execute_tools` for the dry-run gate and
`runtime.tool_timeout_seconds` for the subprocess timeout. Preserve the overwrite
recheck added by the companion plan before any directory creation or subprocess
launch.

- [ ] **Step 5: Capture one runtime in the CLI and graph**

Build in `cli.main`:

```python
runtime_config = RuntimeConfig(
    execute_tools=args.execute,
    trace_enabled=not args.quiet,
    verbose_output=args.verbose,
    transient_trace=args.transient_trace and not args.verbose and not args.quiet,
    tool_timeout_seconds=args.tool_timeout,
    project_root=DEFAULT_PROJECT_ROOT,
)
```

Construct stores and policy loaders from `runtime_config.profile_root`,
`runtime_config.episode_root`, and `runtime_config.project_root`. Pass
`runtime_config` into `build_graph`.

At graph construction:

```python
runtime = runtime_config or current_runtime()
project_policy = project_policy or ProjectPolicyLoader(runtime.project_root).load()
```

Every graph node closure that plans, executes, normalizes results, traces, or writes
logs either passes `runtime` explicitly or runs the decorated tool boundary inside:

```python
with activate_runtime(runtime):
    raw_output = execute_selected_tool(decision, runtime_config=runtime)
```

Already-created graphs keep their captured immutable runtime when a later legacy
override occurs.

- [ ] **Step 6: Migrate paths, tracing, storage, and compatibility facade**

Apply these ownership rules:

```python
def _resolve_user_path(value: str, runtime_config: RuntimeConfig | None = None) -> Path:
    runtime = runtime_config or current_runtime()
    raw = Path(value).expanduser()
    candidates = (
        [raw]
        if raw.is_absolute()
        else [Path.cwd() / raw, runtime.project_root / raw]
    )
    return next((path.resolve() for path in candidates if path.exists()), candidates[-1].resolve())
```

- `planning`, `validation`, and `policy` use `runtime.project_root`.
- `routing.structure_tool_result` uses `runtime.tool_log_root`.
- `UserProfileStore` and `EpisodeStore` keep explicit roots passed by the CLI.
- session load/save/cleanup functions receive `session_root` and `tool_log_root`;
  defaults come from `current_runtime()` only for legacy direct callers.
- trace/render helpers read the graph's active runtime.
- `netzoo_agent._CompatibilityFacade.__setattr__` calls
  `set_legacy_runtime_value`; it never iterates over implementation modules.
- static limits and model defaults remain constants; mutable authority and paths
  leave `contracts.py`.

- [ ] **Step 7: Run runtime, graph, storage, and facade tests**

Run:

```bash
python -m unittest discover -s tests -p 'test_agent_gate.py' -k runtime -v
python -m unittest discover -s tests -p 'test_agent_gate.py' -k 'facade or session or memory or command or graph' -v
python -m unittest discover -s tests -v
```

Expected: both isolated configurations remain stable, legacy assignments work in
their current context, existing graphs do not change retroactively, and the
complete suite passes.

- [ ] **Step 8: Prove core modules no longer scan `sys.modules`**

Run:

```bash
rg -n "sys\\.modules|set_runtime_value|configure_runtime" scripts/netzoo_agent_core
```

Expected: no `sys.modules` scan; only the scoped runtime API remains. The facade may
refer to `sys.modules[__name__]` once to install its compatibility module class, but
must not scan or mutate other modules.

- [ ] **Step 9: Commit Task 2 only**

```bash
git add scripts/netzoo_agent.py scripts/netzoo_agent_core/runtime.py scripts/netzoo_agent_core/contracts.py scripts/netzoo_agent_core/cli.py scripts/netzoo_agent_core/graph.py scripts/netzoo_agent_core/command.py scripts/netzoo_agent_core/routing.py scripts/netzoo_agent_core/planning.py scripts/netzoo_agent_core/validation.py scripts/netzoo_agent_core/preparation.py scripts/netzoo_agent_core/evaluation.py scripts/netzoo_agent_core/memory.py scripts/netzoo_agent_core/session.py scripts/netzoo_agent_core/policy.py scripts/netzoo_agent_core/__init__.py tests/test_agent_gate.py
git diff --cached --check
git diff --cached --name-only
git commit -m "refactor: isolate NetZoo runtime configuration"
```

### Task 3: Stream and atomically replace LIONESS-PUMA text headers

**Files:**
- Modify: `docker/add-puma-lioness-header`
- Test: `tests/test_agent_gate.py`

**Interfaces:**
- Retains: `sample_count(expression_file) -> int`.
- Retains: `add_header(expression_file, lioness_file) -> bool`.
- Produces: `_atomic_header_path(lioness_file) -> Iterator[Path]`.
- Guarantees: memory usage is bounded by the copy buffer and replacement failure
  leaves the source unchanged.

- [ ] **Step 1: Write failing streaming and failure-atomicity tests**

Extend the existing header-helper tests:

```python
def test_puma_lioness_header_helper_does_not_call_read_text(self):
    module = self.load_extensionless_script("docker/add-puma-lioness-header")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        expression = root / "expression.tsv"
        output = root / "lioness.tsv"
        expression.write_text("G1\t1\t2\n", encoding="utf-8")
        output.write_text("TF1 G1 1.0 0.1 0.2\n", encoding="utf-8")
        with patch.object(Path, "read_text", side_effect=AssertionError("whole read")):
            self.assertTrue(module.add_header(expression, output))


def test_puma_lioness_header_replace_failure_preserves_original(self):
    module = self.load_extensionless_script("docker/add-puma-lioness-header")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        expression = root / "expression.tsv"
        output = root / "lioness.tsv"
        original = "TF1 G1 1.0 0.1 0.2\n"
        expression.write_text("G1\t1\t2\n", encoding="utf-8")
        output.write_text(original, encoding="utf-8")
        with patch.object(module.os, "replace", side_effect=OSError("injected")):
            with self.assertRaises(OSError):
                module.add_header(expression, output)
        self.assertEqual(output.read_text(encoding="utf-8"), original)
        self.assertEqual(list(root.glob(".lioness.tsv.header-*")), [])
```

Also test `.npy` no-op, already-headered no-op, empty output failure, exact trailing
newline preservation, and original permission-mode preservation.

- [ ] **Step 2: Run header tests and prove whole-file/in-place behavior fails**

Run:

```bash
python -m unittest discover -s tests -p 'test_agent_gate.py' -k puma_lioness_header -v
```

Expected: `Path.read_text` is called and the implementation has no atomic
replacement failure seam.

- [ ] **Step 3: Implement bounded streaming into a same-directory temporary file**

Import `os`, `shutil`, `stat`, and `tempfile`. Replace `add_header` with:

```python
def add_header(expression_file: Path, lioness_file: Path) -> bool:
    if lioness_file.suffix.casefold() == ".npy":
        return False

    with lioness_file.open("r", encoding="utf-8") as source:
        first_line = source.readline()
    if not first_line:
        raise SystemExit(f"LIONESS-PUMA output is empty: {lioness_file}")
    if first_line.strip().split()[:3] == HEADER_PREFIX:
        return False

    n_samples = sample_count(expression_file)
    header = " ".join([*HEADER_PREFIX, *(str(i) for i in range(1, n_samples + 1))])
    original_mode = stat.S_IMODE(lioness_file.stat().st_mode)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{lioness_file.name}.header-",
        dir=lioness_file.parent,
    )
    temporary = Path(temporary_name)
    try:
        with (
            os.fdopen(descriptor, "w", encoding="utf-8", newline="") as target,
            lioness_file.open("r", encoding="utf-8", newline="") as source,
        ):
            target.write(header + "\n")
            shutil.copyfileobj(source, target, length=1024 * 1024)
            target.flush()
            os.fsync(target.fileno())
        os.chmod(temporary, original_mode)
        os.replace(temporary, lioness_file)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return True
```

Because the temporary file is in the destination directory, `os.replace` stays on
one filesystem and is atomic. Do not call `read_text`, `splitlines`, or
`write_text`.

- [ ] **Step 4: Run focused tests and a bounded-memory smoke test**

Run:

```bash
python -m unittest discover -s tests -p 'test_agent_gate.py' -k puma_lioness_header -v
python -c "from pathlib import Path; p=Path('/tmp/netzoo-header-smoke.tsv'); e=Path('/tmp/netzoo-expression-smoke.tsv'); e.write_text('G1\\t1\\t2\\n'); p.write_text(('TF G 1 0 0\\n') * 100000); print(p.stat().st_size)"
python docker/add-puma-lioness-header /tmp/netzoo-expression-smoke.tsv /tmp/netzoo-header-smoke.tsv
```

Expected: tests pass, the smoke file receives exactly one header, and the helper
does not build a full-file string in memory.

- [ ] **Step 5: Commit Task 3 only**

```bash
git add docker/add-puma-lioness-header tests/test_agent_gate.py
git diff --cached --check
git diff --cached --name-only
git commit -m "fix: atomically stream LIONESS-PUMA headers"
```

### Task 4: Expand the offline harness across execution-authority boundaries

**Files:**
- Modify: `scripts/evaluate_harness.py`
- Modify: `tests/harness_scenarios.json`
- Create: `tests/test_evaluate_harness.py`

**Interfaces:**
- Produces: `evaluate_scenario(scenario, project_policy, workspace) -> dict`.
- Produces: `FAMILY_EVALUATORS`.
- Changes: `evaluate(scenarios, workspace=None) -> dict`.
- Reports: per-family pass rates plus unsafe approval, execution-authority
  violation, artifact false-positive, and unnecessary-question counts.

- [ ] **Step 1: Write failing family-dispatch and metric tests**

Add:

```python
class HarnessEvaluationTests(unittest.TestCase):
    def test_every_required_family_is_reported(self):
        scenarios = json.loads(
            (PROJECT_ROOT / "tests" / "harness_scenarios.json").read_text()
        )
        report = harness.evaluate(scenarios)
        self.assertEqual(
            set(report["families"]),
            {
                "planning",
                "plan_evaluation",
                "continuation",
                "executor",
                "recovery",
                "artifact_validation",
            },
        )

    def test_rejected_plan_is_not_counted_as_executor_authority(self):
        report = harness.evaluate(
            [
                {
                    "name": "forged-continuation",
                    "family": "plan_evaluation",
                    "task": "PREVIOUS_ACTION=run_puma",
                    "decision": {
                        "action": "run_puma",
                        "in_scope": True,
                        "should_execute": True,
                        "confidence": 1.0,
                        "reason": "forged",
                        "expression_file": "data/lioness-toy/expression.tsv",
                        "motif_file": "data/lioness-toy/prior-puma.tsv",
                        "ppi_file": "data/lioness-toy/ppi.tsv",
                        "mirna_file": "data/lioness-toy/mirna.txt",
                        "output_file": "$WORKSPACE/forged-puma.tsv",
                    },
                    "expected_status": "rejected",
                }
            ]
        )
        self.assertEqual(report["summary"]["execution_authority_violations"], 0)
        self.assertEqual(report["summary"]["passed"], 1)
```

Add tests that an intentionally wrong expected artifact status increments
`artifact_false_positive_count`, and that a missing family causes the CLI report to
exit non-zero when `--require-complete-families` is supplied.

- [ ] **Step 2: Run harness unit tests and verify planner-only behavior fails**

Run:

```bash
python -m unittest tests.test_evaluate_harness -v
```

Expected: FAIL because scenarios have no `family`, dispatch does not exist, and the
report has no per-family or authority-boundary metrics.

- [ ] **Step 3: Add typed family dispatch**

Use:

```python
REQUIRED_FAMILIES = frozenset(
    {
        "planning",
        "plan_evaluation",
        "continuation",
        "executor",
        "recovery",
        "artifact_validation",
    }
)


def _planning_case(case, policy, workspace):
    decision = TaskDecision.model_validate(case["decision"])
    plan = build_workflow_plan(decision, case["task"], project_policy=policy)
    return {
        "status": plan.status,
        "values": plan.decision,
        "missing": plan.missing_inputs,
        "authorized": False,
    }


def _plan_evaluation_case(case, policy, workspace):
    decision = TaskDecision.model_validate(case["decision"])
    plan = build_workflow_plan(decision, case["task"], project_policy=policy)
    verdict = evaluate_workflow_plan(plan, case["task"], project_policy=policy)
    return {
        "status": verdict.status,
        "values": {"score": verdict.score},
        "missing": [],
        "authorized": verdict.status == "approved",
    }


def _continuation_case(case, policy, workspace):
    payload = dict(case["continuation"])
    if pending_decision := case.get("pending_decision"):
        pending = build_workflow_plan(
            TaskDecision.model_validate(pending_decision),
            payload["source_task"],
            project_policy=policy,
        )
        payload["pending_plan"] = pending.model_dump()
    continuation = ContinuationRequest.model_validate(payload)
    decision = decision_from_continuation(continuation)
    return {
        "status": "accepted",
        "values": decision.model_dump(),
        "missing": decision.missing_inputs,
        "authorized": False,
    }


def _recovery_case(case, policy, workspace):
    results = [
        ToolExecutionResult.model_validate(item) for item in case["results"]
    ]
    evaluation = EvaluationResult.model_validate(case["evaluation"])
    return {
        "status": "failed" if terminal_failed(results, evaluation) else evaluation.status,
        "values": {
            "effective_statuses": [
                item.status for item in effective_results(results)
            ]
        },
        "missing": [],
        "authorized": False,
    }
```

The executor family creates an already-existing temporary output and calls the
final collision gate with `allow_overwrite=False`; its expected status is
`rejected`. The artifact family writes the case's `fixture_text` or an empty file
under `workspace`, substitutes that path into the decision, and calls
`validate_output_artifacts`.

Before family dispatch, recursively replace `$WORKSPACE` in every string with the
current temporary workspace path and create every path listed in
`existing_paths`. This makes collision scenarios deterministic and prevents the
harness from modifying repository outputs:

```python
def materialize_case(value, workspace: Path):
    if isinstance(value, str):
        return value.replace("$WORKSPACE", str(workspace))
    if isinstance(value, list):
        return [materialize_case(item, workspace) for item in value]
    if isinstance(value, dict):
        return {
            key: materialize_case(item, workspace)
            for key, item in value.items()
        }
    return value
```

Declare:

```python
FAMILY_EVALUATORS = {
    "planning": _planning_case,
    "plan_evaluation": _plan_evaluation_case,
    "continuation": _continuation_case,
    "executor": _executor_case,
    "recovery": _recovery_case,
    "artifact_validation": _artifact_case,
}
```

Unknown families return a failed scenario with a schema error; they never fall back
to Planner evaluation.

- [ ] **Step 4: Convert and expand the scenario corpus**

Add `"family": "planning"` to the five existing cases and add at least these
deterministic scenarios:

```json
{
  "name": "existing_explicit_output_requires_confirmation",
  "family": "plan_evaluation",
  "task": "run PUMA with the supplied files and explicit existing output",
  "decision": {
    "action": "run_puma",
    "in_scope": true,
    "should_execute": true,
    "confidence": 1.0,
    "reason": "explicit execution request"
  },
  "fixture": "complete_puma_with_existing_output",
  "expected_status": "deferred"
}
```

```json
{
  "name": "unicode_path_continuation_round_trip",
  "family": "continuation",
  "continuation": {
    "kind": "clarification",
    "source_task": "run PUMA",
    "action": "run_puma",
    "assignments": {
      "expression_file": "data/My Study/表現 matrix.tsv"
    }
  },
  "pending_decision": {
    "action": "run_puma",
    "in_scope": true,
    "should_execute": true,
    "confidence": 1.0,
    "reason": "waiting for required inputs"
  },
  "expected_status": "accepted",
  "expected_values": {
    "expression_file": "data/My Study/表現 matrix.tsv"
  }
}
```

```json
{
  "name": "existing_output_blocked_before_launch",
  "family": "executor",
  "expected_status": "rejected"
}
```

```json
{
  "name": "successful_recovery_uses_effective_attempt",
  "family": "recovery",
  "results": [
    {
      "action": "run_puma",
      "status": "failed",
      "summary": "old failure",
      "superseded": true
    },
    {
      "action": "run_puma",
      "status": "success",
      "summary": "recovered",
      "attempt_id": 1
    }
  ],
  "evaluation": {
    "status": "completed",
    "reason": "recovered"
  },
  "expected_status": "completed",
  "expected_values": {
    "effective_statuses": ["success"]
  }
}
```

```json
{
  "name": "zero_byte_puma_is_not_success",
  "family": "artifact_validation",
  "action": "run_puma",
  "fixture_text": "",
  "expected_status": "failed"
}
```

Add one passing artifact fixture and a CONDOR case in which one membership table is
missing.

- [ ] **Step 5: Report per-family and safety metrics**

For every result, compare `status`, `expected_values`, and `expected_missing`.
Aggregate:

```python
families[family] = {
    "scenarios": len(family_results),
    "passed": sum(item["passed"] for item in family_results),
    "pass_rate": passed / total if total else 0.0,
}
```

Increment:

- `unsafe_autofill_count` when expected `needs_input` becomes `ready`;
- `unnecessary_question_count` when expected `ready` becomes `needs_input`;
- `execution_authority_violations` when a non-approved evaluator/executor case
  reports `authorized=True`;
- `artifact_false_positive_count` when expected `failed` becomes `success`.

Exit non-zero when any scenario fails. Add
`--require-complete-families`; when set, also fail if any member of
`REQUIRED_FAMILIES` is absent.

- [ ] **Step 6: Run harness unit, CLI, and corpus tests**

Run:

```bash
python -m unittest tests.test_evaluate_harness -v
python scripts/evaluate_harness.py --require-complete-families
python scripts/evaluate_harness.py --require-complete-families --json
```

Expected: all six families are present, every scenario passes, and every safety
counter is zero.

- [ ] **Step 7: Commit Task 4 only**

```bash
git add scripts/evaluate_harness.py tests/harness_scenarios.json tests/test_evaluate_harness.py
git diff --cached --check
git diff --cached --name-only
git commit -m "test: evaluate every NetZoo agent boundary"
```

### Task 5: Complete cross-plan documentation and verification

**Files:**
- Modify: `AGENT_USAGE.md`
- Test: all files changed by this plan and the companion plan.

**Interfaces:**
- Consumes: every public seam and regression scenario from both implementation
  plans.
- Guarantees: the repository passes static, unit, harness, container, and CLI smoke
  checks without a live OpenRouter request.

- [ ] **Step 1: Document the corrected guarantees**

Add a concise section stating:

```markdown
### Execution safety guarantees

- Existing explicit outputs require typed overwrite approval; generated defaults
  receive a numbered sibling.
- Autonomous multi-file workflows use one validated dataset bundle.
- A successful CONDOR run contains non-empty regulator and target membership
  tables; partial membership is a failure.
- Each chat graph captures an immutable runtime configuration. Starting a second
  graph cannot change the first graph's execution mode, timeout, or storage paths.
- LIONESS-PUMA text headers are inserted with bounded memory and atomic replacement.
- The offline harness evaluates planning, plan approval, continuation authority,
  executor collision checks, recovery status, and artifact validation separately.
```

- [ ] **Step 2: Run the complete host-side suite**

Run:

```bash
python -m unittest discover -s tests -v
python scripts/evaluate_harness.py --require-complete-families
python -m ruff check scripts tests docker/run-condor docker/add-puma-lioness-header
python -m ruff format --check scripts tests docker/run-condor docker/add-puma-lioness-header
python -m compileall -q scripts tests
git diff --check
```

Expected: all tests and harness families pass, Ruff and formatting report no
issues, compilation succeeds, and no whitespace errors exist.

- [ ] **Step 3: Run container and CLI smoke checks**

Run:

```bash
docker compose config --quiet
docker compose build netzoo
docker compose run --rm -T netzoo python scripts/netzoo_agent.py --help
docker compose run --rm -T netzoo python -m unittest discover -s tests -v
docker compose run --rm -T netzoo python scripts/evaluate_harness.py --require-complete-families
```

Expected: image builds, help exits zero, container tests pass, and the offline
harness does not require `OPENROUTER_API_KEY`.

- [ ] **Step 4: Run targeted behavioral probes**

Run:

```bash
python -m unittest tests.test_condor_runner -v
python -m unittest discover -s tests -p 'test_agent_gate.py' -k 'overwrite or bundle or continuation or successful_recovery or runtime or puma_lioness_header' -v
python -m unittest tests.test_agent_artifacts -v
python -m unittest tests.test_evaluate_harness -v
```

Expected: every previously reproduced P1/P2 defect has a named passing regression
test.

- [ ] **Step 5: Review scope and staged contents**

Run:

```bash
git status --short --branch
git diff --stat
git diff --cached --name-only
git log --oneline --decorate -12
```

Confirm no `.env`, API key, generated output, dataset, deleted user file, or
unrelated dirty-worktree change is staged. Confirm every requirement in
`docs/superpowers/specs/2026-07-30-netzoo-agent-state-stability-design.md` maps to
one passing test in this plan or its companion.

- [ ] **Step 6: Commit Task 5 only**

```bash
git add AGENT_USAGE.md
git diff --cached --check
git diff --cached --name-only
git commit -m "docs: record NetZoo execution safety guarantees"
```

## Final Acceptance Checklist

- [ ] CONDOR cannot exit zero without both valid membership partitions.
- [ ] CONDOR API exceptions retain method, exception type, and message.
- [ ] CONDOR membership files are independently revalidated as artifacts.
- [ ] No core module scans or mutates `sys.modules`.
- [ ] Two graph/session runtime configurations coexist without authority or path
  leakage.
- [ ] Legacy facade assignments do not mutate an existing explicit runtime.
- [ ] LIONESS-PUMA header insertion never reads the full output into one string.
- [ ] Replacement failure preserves the original LIONESS output.
- [ ] All six deterministic harness families are present and passing.
- [ ] Harness unsafe-autofill, authority-violation, and artifact-false-positive
  counters are zero.
- [ ] Host and container tests pass without a live OpenRouter request.
- [ ] No unrelated dirty-worktree file is staged.

## Spec Coverage Matrix

| Written-spec requirement | Implemented and tested by |
|---|---|
| Strict CONDOR Completion | Task 1 |
| Instance-Scoped Runtime Configuration | Task 2 |
| Streaming and Atomic LIONESS-PUMA Header Insertion | Task 3 |
| Deterministic Evaluation Harness | Task 4 |
| Cross-plan compatibility and verification | Task 5 |
| Attempt-Aware Recovery | Companion state-stability plan, Tasks 1 and 2 |
| Coherent Dataset Bundle Discovery | Companion state-stability plan, Task 3 |
| Artifact Validation | Companion state-stability plan, Task 4 and this plan, Task 1 |
| Typed Continuations | Companion state-stability plan, Task 5 |
| Output Collision Handling | Companion state-stability plan, Task 6 |
