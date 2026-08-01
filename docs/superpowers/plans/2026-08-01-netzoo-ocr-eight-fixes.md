# NetZoo OCR Eight-Issue Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the eight evidence-backed P1/P2 defects from the Delegation Mode review without expanding NetZoo tool authority or overwriting existing worktree changes.

**Architecture:** Preserve the current planner/executor/evaluator topology. Complete the existing coherent-bundle seam, add one deterministic path-safety seam and one artifact-validation seam, make CONDOR and subprocess completion strict at their owning boundaries, and restore the historical facade surface. Every task begins with a failing regression test and ends with a focused commit containing only in-scope files.

**Tech Stack:** Python 3.10+, Pydantic, pandas, NumPy, LangChain tools, `unittest`, POSIX process groups, Bash wrappers, Git.

## Global Constraints

- Python types and deterministic code remain the only execution authority.
- Preserve the existing CLI, LangGraph topology, allow-listed actions, command arguments, workflow YAML, and dry-run behavior.
- Preserve and build on the current uncommitted bundle and recovery work; do not revert it.
- Do not read, copy, stage, or expose `.env*`, secrets, credentials, key files, `data/**`, or `outputs/**` content.
- Tests create all new fixtures under `tempfile.TemporaryDirectory()`.
- Keep subprocess argument-vector execution; never add `shell=True`.
- Do not stage unrelated documentation, deleted files, memory work, or generated artifacts.
- Before every commit run `git diff --cached --check` and `git diff --cached --name-only`.

---

## File Structure

- `scripts/netzoo_agent_core/bundles.py`: existing WIP for atomic multi-file dataset discovery.
- `scripts/netzoo_agent_core/contracts.py`: add backward-compatible bundle evidence and artifact-result contracts.
- `scripts/netzoo_agent_core/planning.py`: apply one discovered bundle instead of per-field guessing.
- `scripts/netzoo_agent_core/evaluation.py`: enforce bundle provenance and pairwise output uniqueness.
- `scripts/netzoo_agent_core/path_safety.py`: validate CONDOR prefixes and derived output containment/collisions.
- `scripts/netzoo_agent_core/routing.py`: exact quoted-value parsing and artifact-result integration.
- `scripts/netzoo_agent_core/command.py`: process-group lifecycle and unchanged-output precheck.
- `scripts/netzoo_agent_core/artifact_validation.py`: workflow-specific structural artifact validation.
- `scripts/netzoo_agent_core/execution.py`: pre-launch path checks and complete CONDOR artifact declaration.
- `docker/run-condor`: strict compatibility probes and required membership output.
- `scripts/netzoo_agent.py`: legacy aliases and executable entry point.
- `tests/test_dataset_bundles.py`: coherent discovery and evaluator provenance tests.
- `tests/test_path_and_output_safety.py`: quoted paths, output collisions, and prefix traversal tests.
- `tests/test_command_processes.py`: process-tree timeout tests.
- `tests/test_agent_artifacts.py`: structural artifact tests.
- `tests/test_condor_runner.py`: extensionless wrapper unit tests.
- `tests/test_legacy_facade.py`: executable-mode and import compatibility tests.

### Task 1: Complete coherent dataset bundle discovery

**Files:**
- Modify: `scripts/netzoo_agent_core/contracts.py:493-507`
- Modify: `scripts/netzoo_agent_core/planning.py:46-55,231-367`
- Modify: `scripts/netzoo_agent_core/evaluation.py:75-150`
- Preserve/complete: `scripts/netzoo_agent_core/bundles.py`
- Preserve: `scripts/netzoo_agent_core/__init__.py`
- Preserve: `scripts/netzoo_agent.py`
- Create: `tests/test_dataset_bundles.py`

**Interfaces:**
- Consumes: `discover_coherent_bundle(action, nearby, explicit_inputs) -> BundleDiscovery | None` from existing WIP.
- Produces: `InputEvidence.bundle_id: str | None = None`.
- Produces: `_bundle_provenance_failures(plan, decision) -> list[str]`.
- Guarantees: autonomous multi-file inputs are applied atomically from one validated directory.

- [ ] **Step 1: Write failing bundle integration tests**

Create `tests/test_dataset_bundles.py` with temporary PANDA/PUMA fixtures built by a local helper. The central tests are:

```python
def test_anchored_expression_does_not_pull_missing_inputs_from_other_directories(self):
    expression = self.write_expression(self.root / "study-a")
    self.write_puma_priors(self.root / "study-b")
    plan = build_workflow_plan(
        self.puma_decision(str(expression)),
        f"run PUMA with expression_file={expression}",
    )
    self.assertEqual(plan.status, "needs_input")
    self.assertIn("motif_file", plan.missing_inputs)

def test_one_complete_directory_is_applied_with_one_bundle_id(self):
    study = self.write_complete_puma_bundle(self.root / "study-a")
    expression = study / "expression.tsv"
    plan = build_workflow_plan(
        self.puma_decision(str(expression)),
        f"run PUMA with expression_file={expression}",
    )
    discovered = [item for item in plan.evidence if item.status == "discovered"]
    self.assertEqual(plan.status, "ready")
    self.assertEqual(
        {item.bundle_id for item in discovered},
        {f"directory:{study.resolve()}"},
    )

def test_plan_evaluator_rejects_conflicting_discovered_bundle_ids(self):
    plan = self.ready_puma_plan()
    discovered = [item for item in plan.evidence if item.status == "discovered"]
    discovered[-1].bundle_id = "directory:/forged-study"
    result = evaluate_workflow_plan(plan, self.task)
    self.assertEqual(result.status, "rejected")
    self.assertIn(
        "dataset_bundle_provenance",
        {item.criterion for item in result.rubric if item.result == "fail"},
    )
```

- [ ] **Step 2: Run the tests and verify the planner still guesses per field**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_dataset_bundles -v
```

Expected: FAIL because `InputEvidence.bundle_id` is absent and `planning.py` still invokes `_find_candidate_files` independently for each missing field.

- [ ] **Step 3: Add backward-compatible bundle evidence**

Add to `InputEvidence`:

```python
bundle_id: str | None = None
```

Existing persisted sessions remain valid because the field defaults to `None`.

- [ ] **Step 4: Apply one bundle before the evidence loop**

Import `discover_coherent_bundle`. After `nearby` is known, call it once for supported multi-file actions:

```python
bundle = discover_coherent_bundle(action, nearby, explicit_input_values)
if bundle is not None:
    for field_name, value in bundle.values.items():
        if field_name in explicit_input_values:
            continue
        setattr(decision, field_name, value)
        autonomous_values[field_name] = value
        autonomous_reasons[field_name] = bundle.reason
        autonomous_sources[field_name] = "discovered"
        autonomous_bundle_ids[field_name] = bundle.bundle_id
```

For multi-file actions, remove the per-field `_find_candidate_files` fallback. If no complete bundle exists, retain candidate lists for clarification but leave each unresolved field `missing`.

When constructing evidence, assign:

```python
bundle_id=autonomous_bundle_ids.get(field_name)
```

- [ ] **Step 5: Reject forged mixed autonomous evidence**

Add an evaluator criterion that inspects only `status == "discovered"` items belonging to multi-file workflows:

```python
bundle_ids = {item.bundle_id for item in discovered}
bundle_ok = bool(discovered) and None not in bundle_ids and len(bundle_ids) == 1
```

Explicit `provided` or `selected` cross-directory inputs are not subject to this criterion.

- [ ] **Step 6: Run focused and existing stability tests**

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_dataset_bundles -v
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_agent_stability -v
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -p 'test_agent_gate.py' -k 'bundle or autonom' -v
```

Expected: all tests pass, including the pre-existing dirty-worktree bundle tests.

- [ ] **Step 7: Commit only bundle implementation files**

```bash
git add scripts/netzoo_agent_core/bundles.py scripts/netzoo_agent_core/contracts.py scripts/netzoo_agent_core/planning.py scripts/netzoo_agent_core/evaluation.py scripts/netzoo_agent_core/__init__.py scripts/netzoo_agent.py tests/test_dataset_bundles.py
git diff --cached --check
git diff --cached --name-only
git commit -m "fix: discover NetZoo datasets as coherent bundles"
```

Do not stage `scripts/netzoo_agent_core/memory.py` or `tests/test_agent_stability.py`; those existing WIP changes remain untouched.

### Task 2: Enforce safe paths and exact quoted values

**Files:**
- Create: `scripts/netzoo_agent_core/path_safety.py`
- Modify: `scripts/netzoo_agent_core/routing.py:437-446`
- Modify: `scripts/netzoo_agent_core/evaluation.py:403-429`
- Modify: `scripts/netzoo_agent_core/execution.py:435-478`
- Modify: `scripts/netzoo_agent_core/__init__.py`
- Modify: `scripts/netzoo_agent.py`
- Create: `tests/test_path_and_output_safety.py`

**Interfaces:**
- Produces: `validate_output_basename(value: str, label: str) -> str`.
- Produces: `condor_artifact_paths(output_dir: str | Path, prefix: str) -> dict[str, Path]`.
- Produces: `resolved_output_collisions(decision: TaskDecision) -> list[str]`.
- Retains: `_extract_named_path(task, names) -> str | None` with exact quoted-value support.

- [ ] **Step 1: Write failing path tests**

```python
def test_quoted_path_with_spaces_round_trips(self):
    task = 'run PANDA with expression_file="/tmp/My Study/表現 matrix.tsv"'
    self.assertEqual(
        _extract_named_path(task, ("expression_file",)),
        "/tmp/My Study/表現 matrix.tsv",
    )

def test_lioness_output_roles_must_be_distinct(self):
    plan, task = self.ready_lioness_plan(output="same.tsv", lioness="same.tsv")
    verdict = evaluate_workflow_plan(plan, task)
    self.assertEqual(verdict.status, "rejected")

def test_condor_prefix_cannot_escape_output_directory(self):
    with self.assertRaisesRegex(ValueError, "prefix"):
        condor_artifact_paths("/tmp/out", "../victim")

def test_condor_artifacts_remain_under_output_directory(self):
    paths = condor_artifact_paths("/tmp/out", "trial-1")
    root = Path("/tmp/out").resolve()
    self.assertTrue(all(path.is_relative_to(root) for path in paths.values()))
```

- [ ] **Step 2: Run tests and prove all three current failures**

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_path_and_output_safety -v
```

Expected: quoted paths truncate at the first space, equal LIONESS outputs are approved, and traversal prefixes are accepted.

- [ ] **Step 3: Implement quoted named-value parsing**

Use one regex with named quote/value groups and a legacy unquoted fallback:

```python
pattern = re.compile(
    rf"(?:{name_pattern})\s*(?:是|為|=|:|：|at|as|is|to)?\s*"
    r"(?:(?P<quote>['\"])(?P<quoted>.*?)(?P=quote)|(?P<plain>[^\s，,。；;]+))",
    flags=re.IGNORECASE,
)
value = match.group("quoted") if match.group("quote") else match.group("plain")
return value.strip().rstrip(".。") if not match.group("quote") else value
```

Do not call `shlex.split` on parsed paths.

- [ ] **Step 4: Add shared output-path safety**

`validate_output_basename` rejects empty values, `.`/`..`, `/`, `\\`, and values outside:

```python
SAFE_OUTPUT_BASENAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")
```

`condor_artifact_paths` resolves the output root and creates four targets:

```python
suffixes = ("edges.tsv", "reg_memb.tsv", "tar_memb.tsv", "summary.txt")
paths = {suffix: (root / f"{safe_prefix}-{suffix}").resolve() for suffix in suffixes}
if any(not path.is_relative_to(root) for path in paths.values()):
    raise ValueError("CONDOR output path escapes output_dir")
```

`resolved_output_collisions` groups every populated output role by `_resolve_user_path(value)` and returns a message for any group containing more than one role.

- [ ] **Step 5: Bind safety into evaluator and executor**

The evaluator adds required criteria for pairwise output uniqueness and valid CONDOR derived paths. `run_condor` calls `condor_artifact_paths` before constructing the command and rejects any target equal to the resolved `network_file` before `_run_command` creates directories.

- [ ] **Step 6: Run path, planner, and CONDOR dry-run tests**

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_path_and_output_safety -v
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -p 'test_agent_gate.py' -k 'path or overwrite or condor' -v
```

- [ ] **Step 7: Commit path safety**

```bash
git add scripts/netzoo_agent_core/path_safety.py scripts/netzoo_agent_core/routing.py scripts/netzoo_agent_core/evaluation.py scripts/netzoo_agent_core/execution.py scripts/netzoo_agent_core/__init__.py scripts/netzoo_agent.py tests/test_path_and_output_safety.py
git diff --cached --check
git diff --cached --name-only
git commit -m "fix: enforce NetZoo output path safety"
```

### Task 3: Require complete CONDOR membership output

**Files:**
- Modify: `docker/run-condor:33-149`
- Modify: `scripts/netzoo_agent_core/execution.py:435-478`
- Create: `tests/test_condor_runner.py`

**Interfaces:**
- Produces: `CondorExecutionError`.
- Produces: `run_first_supported(phase, candidates) -> str`.
- Produces: `required_memberships(obj) -> tuple[pd.DataFrame, pd.DataFrame]`.
- Changes: `write_outputs(...) -> list[Path]`.
- Guarantees: wrapper exit zero requires both membership files.

- [ ] **Step 1: Write failing extensionless-wrapper tests**

Load `docker/run-condor` with `SourceFileLoader`, then test:

```python
def test_missing_target_membership_is_terminal_failure(self):
    obj = SimpleNamespace(
        reg_memb=pd.DataFrame({"node": ["TF1"], "community": [0]}),
        tar_memb=pd.DataFrame(),
    )
    with self.assertRaisesRegex(condor.CondorExecutionError, "tar_memb"):
        condor.required_memberships(obj)

def test_method_errors_keep_context(self):
    candidates = (
        ("brim()", lambda: (_ for _ in ()).throw(ValueError("no convergence"))),
        ("run()", lambda: (_ for _ in ()).throw(RuntimeError("fallback failed"))),
    )
    with self.assertRaisesRegex(
        condor.CondorExecutionError,
        "brim.*ValueError.*no convergence",
    ):
        condor.run_first_supported("optimization", candidates)
```

The happy path writes both non-empty memberships and asserts the returned set contains all four derived paths.

- [ ] **Step 2: Run tests and confirm missing completion contracts**

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_condor_runner -v
```

- [ ] **Step 3: Implement audited API probes**

```python
class CondorExecutionError(RuntimeError):
    pass

def run_first_supported(phase, candidates):
    errors = []
    for label, call in candidates:
        try:
            call()
            return label
        except Exception as error:
            errors.append(f"{label}: {type(error).__name__}: {error}")
    raise CondorExecutionError(
        f"CONDOR {phase} failed for every supported API:\n" + "\n".join(errors)
    )
```

Use labeled initialization and optimization candidate tuples. Do not silently discard non-`AttributeError` exceptions.

- [ ] **Step 4: Require and write both memberships**

```python
def required_memberships(obj):
    memberships = []
    problems = []
    for name in ("reg_memb", "tar_memb"):
        value = getattr(obj, name, None)
        if not isinstance(value, pd.DataFrame):
            problems.append(f"{name} is not a pandas DataFrame")
        elif value.empty:
            problems.append(f"{name} is empty")
        else:
            memberships.append(value)
    if problems:
        raise CondorExecutionError("; ".join(problems))
    return memberships[0], memberships[1]
```

Write the frames to paths supplied by `condor_artifact_paths`, include chosen method labels in the summary, and convert `CondorExecutionError` to non-zero `SystemExit` in `main`.

- [ ] **Step 5: Run CONDOR regression tests**

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_condor_runner -v
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -p 'test_agent_gate.py' -k condor -v
```

- [ ] **Step 6: Commit strict CONDOR completion**

```bash
git add docker/run-condor scripts/netzoo_agent_core/execution.py tests/test_condor_runner.py
git diff --cached --check
git diff --cached --name-only
git commit -m "fix: require complete CONDOR membership output"
```

### Task 4: Terminate the full subprocess tree on timeout

**Files:**
- Modify: `scripts/netzoo_agent_core/command.py:1-150`
- Create: `tests/test_command_processes.py`

**Interfaces:**
- Produces: `_terminate_process_tree(process: subprocess.Popen, grace_seconds: float = 1.0) -> None`.
- Retains: `_run_command(...) -> str` public behavior.

- [ ] **Step 1: Write a failing descendant-lifecycle test**

The test launches a parent Python process that starts a long-running child and prints the child PID. The PID is held only in memory; no repository file is created:

```python
def test_timeout_terminates_descendant_process(self):
    runtime_timeout = 0.2
    command = [
        sys.executable,
        "-c",
        (
            "import subprocess,sys,time; "
            "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); "
            "print(p.pid, flush=True); time.sleep(30)"
        ),
    ]
    output = self.run_live(command, timeout=runtime_timeout)
    child_pid = int(re.search(r"STDOUT before timeout:\\n(\\d+)", output).group(1))
    self.assertFalse(process_exists(child_pid))
```

`process_exists` uses `os.kill(pid, 0)` on POSIX and treats `ProcessLookupError` as terminated. Cleanup force-kills the PID in `addCleanup` so a failing test cannot leak it.

- [ ] **Step 2: Run the test and prove the orphan survives**

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_command_processes -v
```

Expected: FAIL because the direct child times out but its spawned process remains alive.

- [ ] **Step 3: Replace `subprocess.run` with controlled `Popen`**

On POSIX:

```python
process = subprocess.Popen(
    command,
    stdout=stdout_handle,
    stderr=stderr_handle,
    start_new_session=True,
)
try:
    returncode = process.wait(timeout=timeout)
except subprocess.TimeoutExpired:
    _terminate_process_tree(process)
    timed_out = True
```

Termination helper:

```python
def _terminate_process_tree(process, grace_seconds=1.0):
    if os.name == "posix":
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=grace_seconds)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
    else:
        process.terminate()
        try:
            process.wait(timeout=grace_seconds)
        except subprocess.TimeoutExpired:
            process.kill()
    process.wait()
```

Handle races with `ProcessLookupError`. Preserve bounded stdout/stderr capture and existing launch-error messages.

- [ ] **Step 4: Run command and timeout tests**

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_command_processes -v
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -p 'test_agent_gate.py' -k 'local_command or timeout' -v
```

- [ ] **Step 5: Commit process isolation**

```bash
git add scripts/netzoo_agent_core/command.py tests/test_command_processes.py
git diff --cached --check
git diff --cached --name-only
git commit -m "fix: terminate timed-out NetZoo process groups"
```

### Task 5: Validate produced artifacts structurally

**Files:**
- Create: `scripts/netzoo_agent_core/artifact_validation.py`
- Modify: `scripts/netzoo_agent_core/contracts.py`
- Modify: `scripts/netzoo_agent_core/routing.py:789-875`
- Modify: `scripts/netzoo_agent_core/__init__.py`
- Modify: `scripts/netzoo_agent.py`
- Create: `tests/test_agent_artifacts.py`

**Interfaces:**
- Produces: `ArtifactValidationResult` with `ok`, `artifacts`, `errors`, `warnings`, and `metrics`.
- Produces: `validate_output_artifacts(action, decision) -> ArtifactValidationResult`.
- Produces: `ARTIFACT_WRITE_ACTIONS`, the exact set of local actions that create validated outputs.
- Guarantees: status `success` requires a zero exit and valid workflow artifacts.

- [ ] **Step 1: Write failing artifact tests**

Create small temporary fixtures for each action. Required defect tests:

```python
def test_zero_byte_puma_output_fails(self):
    output = self.touch("puma.tsv")
    decision = self.puma_decision(output_file=str(output))
    result = validate_output_artifacts("run_puma", decision)
    self.assertFalse(result.ok)

def test_malformed_lioness_text_fails(self):
    aggregate = self.write("aggregate.tsv", "TF1\tGene1\t1.0\n")
    lioness = self.write("lioness.tsv", "not-a-network\n")
    result = validate_output_artifacts(
        "run_lioness_panda",
        self.lioness_decision(aggregate, lioness),
    )
    self.assertFalse(result.ok)

def test_condor_requires_both_memberships(self):
    self.write_condor_supporting_files(prefix="trial")
    self.write("trial-reg_memb.tsv", "node\tcommunity\nTF1\t0\n")
    result = validate_output_artifacts("run_condor", self.condor_decision())
    self.assertFalse(result.ok)
    self.assertIn("tar_memb", " ".join(result.errors))
```

Also add valid fixtures for formatted expression, co-expression, PANDA/PUMA, LIONESS text, LIONESS `.npy`, and full CONDOR output.

- [ ] **Step 2: Run tests and verify the validator is absent**

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_agent_artifacts -v
```

- [ ] **Step 3: Define the typed validation contract**

```python
class ArtifactValidationResult(BaseModel):
    ok: bool
    artifacts: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metrics: dict[str, int | float | str | bool] = Field(default_factory=dict)
```

Declare the closed action set in the validator module:

```python
ARTIFACT_WRITE_ACTIONS = frozenset(
    {
        "format_expression",
        "convert_expression",
        "run_panda",
        "run_puma",
        "run_lioness_panda",
        "run_lioness_puma",
        "run_lioness_coexpression",
        "run_condor",
    }
)
```

- [ ] **Step 4: Implement common and workflow validators**

Common helper:

```python
def _readable_nonempty_file(path: Path, label: str, errors: list[str]) -> bool:
    if not path.is_file():
        errors.append(f"{label} is missing or not a regular file: {path}")
        return False
    if path.stat().st_size == 0:
        errors.append(f"{label} is empty: {path}")
        return False
    try:
        with path.open("rb") as handle:
            handle.read(1)
    except OSError as error:
        errors.append(f"{label} is not readable: {error}")
        return False
    return True
```

Use `netzoo_table_io.read_table` for text tables, `numpy.load(..., allow_pickle=False)` for `.npy`, numeric coercion for value columns, and `condor_artifact_paths` for membership locations. Validators check structure only and do not introduce biological thresholds.

- [ ] **Step 5: Integrate validation into structured results**

In `structure_tool_result`, after text/exit-code failure detection and before assigning success:

```python
artifact_check = None
if not failed and not dry_run and action in ARTIFACT_WRITE_ACTIONS:
    artifact_check = validate_output_artifacts(action, decision)
    metrics.update(artifact_check.metrics)
    warning_lines.extend(artifact_check.warnings)
    if not artifact_check.ok:
        failed = True
        error_lines.extend(artifact_check.errors)
```

Use `artifact_check.artifacts` as the verified artifact list. Do not count `path.exists()` as verification.

- [ ] **Step 6: Run artifact, routing, recovery, and memory tests**

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_agent_artifacts -v
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -p 'test_agent_gate.py' -k 'structured or artifact or command' -v
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_agent_stability -v
```

- [ ] **Step 7: Commit artifact validation**

```bash
git add scripts/netzoo_agent_core/artifact_validation.py scripts/netzoo_agent_core/contracts.py scripts/netzoo_agent_core/routing.py scripts/netzoo_agent_core/__init__.py scripts/netzoo_agent.py tests/test_agent_artifacts.py
git diff --cached --check
git diff --cached --name-only
git commit -m "fix: validate NetZoo output artifacts"
```

### Task 6: Restore the historical CLI/import facade

**Files:**
- Modify mode and contents: `scripts/netzoo_agent.py`
- Create: `tests/test_legacy_facade.py`

**Interfaces:**
- Restores: executable mode `100755`.
- Restores: `explain_panda_puma_io` LangChain-compatible tool.
- Restores: `TOOLS` containing the historical four tools.

- [ ] **Step 1: Write failing compatibility tests**

```python
def test_entrypoint_is_executable(self):
    mode = stat.S_IMODE(ENTRYPOINT.stat().st_mode)
    self.assertTrue(mode & stat.S_IXUSR)

def test_historical_tool_imports_remain_available(self):
    self.assertTrue(hasattr(agent, "explain_panda_puma_io"))
    self.assertTrue(hasattr(agent, "TOOLS"))
    names = {tool.name for tool in agent.TOOLS}
    self.assertEqual(
        names,
        {"explain_panda_puma_io", "inspect_netzoo_inputs", "run_panda", "run_puma"},
    )
```

Call the explanation tool through `.invoke({"topic": "overview"})` and assert it returns the legacy PANDA/PUMA input summary without any LLM call.

- [ ] **Step 2: Run tests and prove mode/import regressions**

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_legacy_facade -v
```

- [ ] **Step 3: Restore compatibility aliases**

Define the deterministic explanation tool in the facade or a small core compatibility module using the historical signature:

```python
@tool
def explain_panda_puma_io(topic: str = "overview") -> str:
    """Explain PANDA/PUMA input and output formats without executing a workflow."""
    return _legacy_io_summary(topic)

TOOLS = [explain_panda_puma_io, inspect_netzoo_inputs, run_panda, run_puma]
```

Do not add it to the executor allowlist; it exists only for legacy direct callers.

- [ ] **Step 4: Restore executable mode and run facade tests**

```bash
chmod +x scripts/netzoo_agent.py
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_legacy_facade -v
PYTHONDONTWRITEBYTECODE=1 python scripts/netzoo_agent.py --help
```

- [ ] **Step 5: Commit compatibility restoration**

```bash
git add scripts/netzoo_agent.py tests/test_legacy_facade.py
git diff --cached --check
git diff --cached --name-only
git commit -m "fix: restore the legacy NetZoo agent facade"
```

### Task 7: Complete regression verification and scope audit

**Files:**
- Test: all files changed by Tasks 1-6.
- Preserve: unrelated dirty-worktree files.

**Interfaces:**
- Guarantees: all eight OCR issue families have named passing regression tests.

- [ ] **Step 1: Run all targeted regressions**

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_dataset_bundles -v
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_path_and_output_safety -v
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_condor_runner -v
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_command_processes -v
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_agent_artifacts -v
PYTHONDONTWRITEBYTECODE=1 python -m unittest tests.test_legacy_facade -v
```

- [ ] **Step 2: Run the complete host-side suite without bytecode writes**

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
PYTHONDONTWRITEBYTECODE=1 python scripts/evaluate_harness.py
python -m ruff check scripts tests docker/run-condor
python -m ruff format --check scripts tests docker/run-condor
PYTHONDONTWRITEBYTECODE=1 python -c 'from pathlib import Path; [compile(path.read_text(), str(path), "exec") for path in Path("scripts").rglob("*.py")]'
git diff --check
```

If Ruff is unavailable, record that as an environmental limitation and still run compilation and the complete unit suite.

- [ ] **Step 3: Run safe container/config smoke checks when available**

```bash
docker compose config --quiet
docker compose run --rm -T netzoo python scripts/netzoo_agent.py --help
```

Do not build, pull, or invoke a live provider unless separately authorized. Do not print composed environment values.

- [ ] **Step 4: Audit worktree and staged scope**

```bash
git status --short --branch
git diff --stat
git diff --cached --name-only
git log --oneline --decorate -12
```

Confirm that no excluded path, generated file, unrelated deletion, or unrelated documentation change was staged or committed.

- [ ] **Step 5: Final acceptance check**

Confirm all eight statements:

1. CONDOR requires both membership partitions.
2. CONDOR prefix traversal and input collisions are rejected before launch.
3. Output roles are pairwise unique.
4. Autonomous inputs share one bundle ID.
5. Timeout leaves no descendant process alive.
6. Empty and malformed artifacts fail structurally.
7. Quoted paths round-trip exactly.
8. Executable mode and historical imports are restored.

## Self-Review Mapping

| Approved requirement | Plan task |
|---|---|
| Strict CONDOR completion | Task 3 |
| Safe CONDOR prefix and derived paths | Task 2 |
| Pairwise output-role uniqueness | Task 2 |
| Coherent autonomous bundles | Task 1 |
| Process-tree termination | Task 4 |
| Structural artifact validation | Task 5 |
| Quoted paths with spaces and Unicode | Task 2 |
| Executable/import backward compatibility | Task 6 |
| Full non-secret verification | Task 7 |
