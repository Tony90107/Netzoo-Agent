# CLI, Memory, Data Direction, and Code Reading Design

**Date:** 2026-08-07

**Status:** Approved design pending written-spec review

## 1. Objective

Make `scripts/netzoo_agent_core` easier to enter, trace, and modify without removing
working behavior. This iteration focuses only on the three remaining navigation
hotspots:

1. the 469-line `cli.loop.run_cli` lifecycle;
2. the 842-line `memory.py` module;
3. the upward and framework-facing dependencies inside the nominally low-level
   `data` package.

The iteration also adds a maintained `CODE_READING_GUIDE.md` for a reader who knows
basic Python but does not yet know LangGraph or NetZoo.

## 2. Non-negotiable constraints

- Existing successful CLI commands, interactive behavior, resume behavior, stored
  data formats, tool outputs, and workflow decisions must remain unchanged.
- Historical imports through `scripts/netzoo_agent.py`, `netzoo_agent_core.memory`,
  `netzoo_agent_core.validation`, `netzoo_agent_core.preparation`, and existing data
  compatibility paths must remain usable.
- Existing exported object identity and function signatures remain stable wherever
  the current compatibility tests define them.
- The uncommitted UUID JSON-sanitization behavior currently present in
  `memory.py` must survive the package conversion.
- This work does not redesign Planner, Plan Evaluator, Executor behavior, episode
  ranking, retention rules, trace storage, or workflow policy.
- Compatibility facades are retained. New behavior belongs in owner modules, not
  in facades.
- Every structural step is protected by characterization tests and a complete
  regression run.

## 3. Considered approaches

### 3.1 Compatibility-first incremental extraction — selected

Add behavior-level tests first, move one responsibility cluster at a time, and keep
stable package facades at historical seams. This produces useful locality while
keeping the smallest rollback and review surface.

### 3.2 Rewrite the CLI around a new application class — rejected

A single stateful application object could look cleaner, but it would alter too
many session, trace, monkeypatch, and entrypoint assumptions at once. The current
goal is navigation with zero normal-feature loss, not a lifecycle redesign.

### 3.3 Documentation and import cleanup only — rejected

This would be low risk but would leave the two largest navigation hotspots intact.
It would improve appearance without creating stronger seams or locality.

## 4. Target architecture

### 4.1 CLI lifecycle

The stable interface remains:

```python
from netzoo_agent_core.cli import main, parse_args
from netzoo_agent_core.cli.loop import run_cli
```

The implementation becomes:

```text
cli/
├── __init__.py          # existing public facade
├── arguments.py         # argparse definitions
├── commands.py          # immediate web, trace, memory, and policy commands
├── bootstrap.py         # validation and runtime dependency construction
├── conversation.py      # one-shot, interactive, clarification, and resume lifecycle
├── clarification.py     # existing clarification behavior
├── follow_up.py         # existing follow-up behavior
├── trace_commands.py    # existing trace status/export behavior
├── loop.py              # short run_cli coordinator
└── main.py              # parse_args() -> run_cli(args)
```

`commands.py` hides the ordering and rendering of commands that terminate before a
Graph invocation. Its implementation may use private helpers, but its interface to
`loop.py` is limited to explicit handlers that return `int | None`, where `None`
means normal startup should continue.

`bootstrap.py` owns validation and construction of memory stores, project policy,
trace infrastructure, synchronization, resume state, and compiled graph. It returns
a typed internal runtime context instead of exposing a large tuple. It does not own
the interactive loop.

`conversation.py` owns the mutable per-session state currently held in local
variables inside `run_cli`: conversation messages, pending plan, clarification
selections, token usage, run id, pause status, next prompt, and one-shot mode. Its
external seam is one function that runs the conversation and returns the process
exit code.

`loop.run_cli(args) -> int` configures process-wide compatibility settings, calls
the immediate-command seam, builds the runtime context only when needed, and then
delegates to the conversation seam. It contains no detailed prompt, resume, trace,
or result-processing branches.

### 4.2 CLI error behavior

Existing successful behavior remains exact. Error exits are made explicit:

| Situation | Required result |
|---|---|
| Successful one-shot | `0` |
| Pending input in non-interactive mode | `2` |
| Keyboard interruption during Graph invocation | `130` |
| Ordinary Graph/provider/tool exception in one-shot mode | non-zero (`1`) |
| Ordinary exception in interactive mode | render the current failure prompt and continue |

The one-shot non-zero result is a correctness repair: current code catches an
exception, loops once, exits through the one-shot guard, and returns `0`.

### 4.3 Memory package

The stable interface remains:

```python
from netzoo_agent_core.memory import EpisodeStore, UserProfileStore
```

The implementation becomes:

```text
memory/
├── __init__.py          # exact historical exports and compatibility tuple
├── storage.py           # safe ids, JSON sanitization, permissions, locks, atomic writes
├── profiles.py          # UserProfileStore
├── normalization.py     # episode intent, metadata normalization, compact rendering
└── episodes.py          # cleanup report, EpisodeStore, retention/search/migration
```

`storage.py` is a local-substitutable filesystem module. It hides permissions,
locking, atomic replacement, invalid-Unicode handling, and UUID serialization.
Profile and episode implementations use this seam rather than duplicating storage
rules.

`profiles.py` owns confirmed preference validation and persistence only.

`normalization.py` is in-process computation. It turns typed plans and results into
bounded episode metadata and renders compact status payloads without performing
filesystem operations.

`episodes.py` owns the bounded profile-partitioned episode repository, including
layout migration, quarantine, pruning, recording, scoring, listing, and deletion.
The public `EpisodeStore` interface and on-disk JSON schema remain unchanged.

`memory/__init__.py` re-exports the exact current names so direct and legacy imports
continue to resolve to the actual owner objects.

### 4.4 Data dependency direction

The intended direction is:

```text
contracts/settings
        ↓
pure data rules and discovery
        ↓
tool adapters / execution
        ↓
planning, evaluation, graph, CLI
```

The current `data.bundles` import of private functions from `interpretation` is
removed. Candidate keyword generation, filename scoring inputs, and best-file
selection move to `data.discovery`, which both bundle discovery and interpretation
may consume.

Pure table and transformation implementations must not import:

- `cli`, `graph`, `planning`, `evaluation`, or `execution`;
- `interpretation` or `routing`;
- LangChain/LangGraph decorators;
- mutable process-wide execution flags.

To preserve existing decorated tool interfaces while achieving that direction:

```text
data/
├── discovery.py         # neutral candidate naming and selection
├── tables.py            # pure table parsing and validation implementation
├── transforms.py        # pure expression/co-expression transformation implementation
├── table_validation.py  # historical data-path compatibility facade
├── preparation.py       # historical data-path compatibility facade
└── ...                  # paths, inspection, bundles, artifacts

tool_adapters.py         # @tool wrappers and EXECUTE_TOOLS/dry-run policy
validation.py            # historical top-level facade
preparation.py           # historical top-level facade
```

`data.tables` and `data.transforms` accept explicit values needed to decide whether
to write. They return the same user-visible strings and create the same outputs as
the current implementations.

`tool_adapters.py` owns the external LangChain seam. It exports the decorated
`inspect_netzoo_inputs`, `format_expression_for_netzoo`, and
`convert_expression_to_coexpression` objects with their historical signatures.
Compatibility modules re-export those same objects. Existing callers using
`.invoke(...)` therefore keep working.

The historical `data.table_validation` and `data.preparation` paths remain thin
facades. New internal code imports pure owners or `tool_adapters` directly.

### 4.5 Internal imports

Files touched in this iteration stop importing unrelated settings, presentation
helpers, or framework types through the 67-name `contracts` facade. They import
from `contracts.decisions`, `contracts.planning`, `contracts.results`, `settings`,
`presentation`, or `framework_compat` as appropriate. This is limited to files
already changed by the three refactors; it is not a repository-wide import rewrite.

## 5. Code reading guide

Create `CODE_READING_GUIDE.md` for readers who know basic Python but do not yet know
LangGraph or NetZoo. It is a navigation document, not a second architecture spec.

Required sections:

1. **Before reading:** the minimum Python ideas and the five NetZoo terms needed.
2. **15-minute path:** entrypoint, CLI coordinator, Graph topology, planning seam,
   evaluation seam, execution adapter, and typed results.
3. **One PANDA request:** trace a concrete task from `HumanMessage` through routing,
   hydration, planning, plan approval, execution, result evaluation, and response.
4. **State map:** explain only the `AgentState` fields needed to follow that trace.
5. **Problem-to-owner map:** where to start for CLI, routing, missing inputs,
   validation, execution, memory, tracing, and response problems.
6. **Change recipes:** adding a workflow input, changing a validation rule, changing
   a CLI flag, changing a response, and diagnosing a recovery loop.
7. **What to skip initially:** legacy facades, compatibility tuples, detailed trace
   persistence, and archived design plans.
8. **Reading techniques:** use `rg`, begin at interfaces, follow return values, and
   run focused tests before reading implementation details.
9. **Glossary:** module, interface, seam, adapter, Router, Planner, Plan Evaluator,
   Executor, Result Evaluator, Graph state, and episode memory.

The guide links to exact maintained files and focused test commands. `README.md` and
`NETZOO_HARNESS_ARCHITECTURE.md` link back to the guide.

## 6. Testing and migration strategy

### 6.1 Baseline and characterization

Before moving code:

- run the complete test suite;
- record current public exports, representative signatures, and legacy object
  identity;
- add CLI lifecycle tests for one-shot success, pending input, interruption,
  one-shot ordinary error, and interactive ordinary error;
- add memory tests for JSON round-trip, UUID sanitization, profile confirmation,
  episode retention/search, migration, quarantine, and facade identity;
- add data tests for decorated adapter identity, pure function behavior, and the
  forbidden dependency set.

### 6.2 Incremental implementation

Each cluster is independently reviewable and committed:

1. CLI characterization and lifecycle extraction.
2. Memory characterization and package conversion.
3. Data discovery/pure-owner/tool-adapter migration.
4. Reading guide, architecture documentation, and strengthened dependency tests.

After each cluster, run its focused tests, `compileall`, and the complete suite.

### 6.3 Architecture assertions

The existing recursive cycle test remains. Add explicit assertions that:

- `run_cli` is a short coordinator rather than the lifecycle implementation;
- `memory` is a package and its facade exports point to owner modules;
- pure data owners do not import orchestration, interpretation, routing,
  framework decorators, or mutable runtime settings;
- compatibility facades contain no business decisions;
- no Python file exceeds the existing 1,000-line emergency threshold.

These are targeted seam assertions, not universal line-count rules.

## 7. Documentation and discoverability

The maintained navigation chain becomes:

```text
README.md
  ├── CODE_READING_GUIDE.md        # how to enter and trace code
  ├── NETZOO_HARNESS_ARCHITECTURE.md # complete runtime architecture
  ├── AGENT_USAGE.md               # how to operate the CLI
  └── AGENTS.md                    # enforced project policy
```

The duplicate architecture row currently present in the README document table is
removed while adding the reading-guide entry.

## 8. Acceptance criteria

- The complete suite passes with at least the current baseline of 316 passed and 12
  skipped tests; new tests increase the passed count.
- `python -m compileall` succeeds for `scripts/netzoo_agent.py` and
  `scripts/netzoo_agent_core`.
- Historical CLI commands and imports remain valid.
- Profile and episode JSON written before the refactor still load after it.
- The existing UUID JSON-sanitization behavior remains present and tested.
- One-shot ordinary failures return `1`; interactive ordinary failures remain
  recoverable; interruption remains `130`; pending non-interactive input remains `2`.
- `cli.loop.run_cli` is a short coordinator and no longer owns the conversation
  state machine.
- `memory` is a package with storage, profile, normalization, and episode owners.
- Pure data owners have no upward orchestration or framework dependencies.
- The static internal module dependency graph remains acyclic.
- `CODE_READING_GUIDE.md` supports both a 15-minute orientation and a complete PANDA
  request trace, and is linked from the README and architecture guide.

## 9. Out of scope

- Changing workflow definitions or adding NetZoo actions.
- Redesigning Graph topology, Planner evidence rules, Plan Evaluator rubrics, tool
  command construction, memory ranking, or trace cryptographic integrity.
- Removing legacy compatibility imports.
- Repository-wide cleanup of every import through `contracts` or `routing`.
- Splitting long but cohesive validation, evaluation, execution, or trace modules
  solely to reduce line counts.
