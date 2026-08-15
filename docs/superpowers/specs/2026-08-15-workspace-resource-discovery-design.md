# Workspace Resource Discovery Design

## Problem

After NetZoo recommends a workflow, a substantive follow-up such as asking whether
the current computer contains useful data is incorrectly reduced to `needs_detail`.
The live structured resolver classified the request as `needs_detail` with confidence
0.75 because its prompt recognizes questions about entities, inputs, outputs, and
workflows, but not questions about the availability or discovery of local resources.

Changing only that prompt would not complete the behavior. When the same request is
forced through to the scientific Router, it becomes `no_tool/ambiguous`: the action
registry has no read-only workspace-resource discovery capability. Existing bounded
file and coherent-bundle discovery is available only inside workflow planning, after
an analysis action has already been selected. A conversational resource question
therefore cannot inspect the workspace or provide an evidence-backed answer.

## Goals

- Recognize local resource availability, inventory, discovery, and suitability
  questions as substantive goals or follow-ups without matching fixed phrases.
- Inspect only the NetZoo workspace through an explicit, read-only, allow-listed
  capability.
- Derive relevant input roles, filename hints, validators, and constraints from a
  declarative workflow registry rather than workflow-specific branches.
- Report complete validated bundles before incomplete candidates and state what each
  incomplete candidate lacks.
- Preserve the existing separation between LLM semantic interpretation and
  deterministic scope, validation, and execution authority.
- Support a resource-discovery question with or without prior workflow context.

## Non-goals

- Searching the user's home directory, the whole computer, mounted external drives,
  or any path outside the NetZoo workspace.
- Downloading datasets from the internet.
- Automatically selecting a discovered bundle and starting an analysis.
- Treating filename similarity alone as proof that a bundle is valid.
- Adding phrase lists for examples such as `useful data`, `this computer`, or their
  translations.
- Encoding workflow behavior through `if workflow == ...` discovery branches.

## Selected approach

Add an allow-listed `discover_workspace_resources` action. The LLM may select this
action when it semantically interprets a request to find, list, inspect, or assess
locally available resources. Deterministic code fixes the scope to the NetZoo
workspace and derives discovery behavior from trusted workflow specifications.

Prompt-only handling is rejected because it cannot truthfully claim what exists on
disk. Dispatching discovery directly from the CLI resolver is also rejected because
it would combine conversational classification, tool authority, and filesystem work
in one module.

## Architecture

### Conversational resolution

The contextual reply resolver continues to classify conversational relationship:
`follow_up`, `new_goal`, `accept_workflow`, `needs_detail`, or `navigation`. Its
semantic instructions explicitly treat questions about available resources, local
files, example datasets, reusable inputs, and suitability for a trusted workflow as
substantive. These are semantic categories, not keyword triggers.

A bare acknowledgement remains `needs_detail`. A resource question is not downgraded
merely because it omits paths: discovering paths is the requested operation.

Trusted prior-turn workflow facts remain separate from assistant prose. The graph
receives a structured interaction context containing the candidate actions and their
registered input roles. The user's latest text remains unmodified. Code-generated
context labels must not be fed back as ordinary user text where they can trigger
lexical routing rules.

### Router and capability boundary

`discover_workspace_resources` is a first-class read-only action in the action
registry and Router schema. The Router selects it based on structured semantic intent,
not a production phrase matcher. It does not choose arbitrary roots, paths, workflow
requirements, or validators.

The deterministic gate authorizes the action only with a scope object created by the
harness:

- root: the resolved NetZoo project root;
- candidate actions: trusted prior-turn workflow candidates, when present;
- mode: read-only inventory;
- configured traversal and output limits.

If prior workflow candidates exist, discovery is restricted to their registered
discovery specifications. Without prior workflow context, the engine inventories all
local workflow actions that declare a discovery specification. A user-supplied path
may narrow the search only when path resolution proves it remains under the workspace
root.

### Declarative discovery specifications

Each discoverable workflow action declares a `DiscoverySpec` in the registry. It
contains data such as:

- input roles required for a complete bundle;
- filename hints or aliases for each role;
- allowed file extensions;
- validation pipeline identifiers;
- workflow constraints such as minimum sample count;
- optional ranking hints for example or toy data.

The discovery engine iterates over these specifications. It does not branch on a
workflow name. Workflow-specific scientific differences exist only as registry data
or as reusable named validator implementations already selected by the specification.
Adding another workflow must require a new registry entry and tests, not edits to the
resolver or discovery control flow.

Existing candidate scoring, traversal bounds, input inspection, and coherent bundle
validation should be reused or factored behind this specification-driven interface.
The current planning path should consume the same discovery service so conversation
and execution planning cannot disagree about which files form a valid bundle.

### Discovery result contract

The tool returns a typed `WorkspaceResourceInventory` with:

- `scope_root`: the displayed workspace-relative root;
- `visited_file_count` and `truncated`: bounded traversal evidence;
- `validated_bundles`: complete bundles that passed all declared validators;
- `partial_candidates`: candidate directories or groups with matched roles, missing
  roles, and bounded candidate paths;
- `rejected_summary`: counts and safe reason categories for invalid or unreadable
  candidates;
- `errors`: non-fatal bounded discovery errors.

Each validated bundle includes compatible registered actions, role-to-path mappings,
validation status, and a short evidence reason. Results are sorted by completeness,
validation, registry relevance to the prior context, and deterministic path order.
Discovery never chooses one bundle for execution.

## Interaction behavior

For a contextual local-data question, the expected flow is:

1. The reply resolver emits `follow_up`.
2. The Router emits `discover_workspace_resources`.
3. The deterministic gate injects the workspace-only scope and trusted candidate
   workflow specifications.
4. The read-only discovery tool inventories and validates bounded candidates.
5. The response model summarizes the typed result without inventing files or formats.
6. The CLI appends one canonical status footer and one next-turn prompt.

The response lists validated bundles first. Partial candidates follow with their
missing input roles. It explicitly states that no analysis was executed. If nothing
compatible is found, it says that no compatible data was found in the inspected
workspace; it does not claim that the question was insufficiently concrete.

## Safety and bounded execution

- The root is code-owned and resolves to the NetZoo workspace.
- Traversal does not follow symlinks and rejects resolved paths outside the root.
- Maximum depth, visited files, candidate groups, returned paths, and execution time
  are configured and enforced.
- Only allow-listed tabular extensions from the discovery specification are opened.
- Per-file read and parse limits prevent unbounded validation work.
- Permission and parse failures are recorded per candidate and do not fail the whole
  inventory.
- Discovery performs no writes and cannot transition into an analysis action.
- A discovered path is evidence, not execution authorization. Existing input,
  confirmation, plan-evaluation, and execution-mode gates remain required before a
  later run.

## Error handling

- No matching files: return an empty successful inventory with the inspected scope.
- Partial data only: return missing roles for each bounded candidate group.
- Multiple valid bundles: return all results up to the result limit; do not select one.
- Unreadable files: retain a safe unreadable count or bounded path summary.
- Invalid formats or incompatible identifiers: retain validator reason categories.
- Traversal limit reached: set `truncated=true` and state that the result is partial.
- Router or resolver uncertainty: ask a targeted scope or objective question only
  when semantic intent truly remains ambiguous. Do not use the generic concrete-
  follow-up message for an explicit local resource question.

## Testing strategy

### Resolver semantics

Use structured fake-model decisions and real-model smoke coverage to establish that
paraphrases and languages expressing local availability, inventory, reuse, or
suitability are substantive. Acknowledgements and fragments remain `needs_detail`.
Production code must not contain an allow-list of the test phrases.

### Registry-driven discovery

Create a synthetic workflow and `DiscoverySpec` with neutral names in a temporary
workspace. Without modifying the engine, tests must prove that it:

- finds and validates a complete bundle;
- reports a partial group and its missing roles;
- applies declared validation and minimum-sample constraints;
- returns deterministic bounded ordering;
- supports an additional registered workflow through data alone.

### Safety

Tests cover path containment, symlink exclusion, depth and visited-file limits,
result limits, parse limits, read-only behavior, timeout handling, and the rule that
discovery cannot authorize or execute an analysis.

### Conversation regression

An end-to-end injected conversation and a live Docker smoke test cover:

1. a workflow-guidance question that establishes trusted candidates;
2. a local resource availability follow-up;
3. resolver continuation into the graph;
4. Router selection of read-only discovery;
5. evidence-backed complete and partial results;
6. one operational footer and one CLI next-turn prompt.

The regression must prove that prior assistant prose is not used as authority and
that the generic `Please enter a concrete follow-up question` response is absent.

## Success criteria

- A clear request to discover useful local data is never rejected solely for lacking
  a path.
- The answer is based on an actual bounded inspection of the NetZoo workspace.
- Complete validated bundles appear before partial candidates, with missing roles
  clearly reported.
- No filesystem location outside the workspace is inspected.
- No analysis runs and no discovered bundle is silently selected.
- The resolver, Router, and discovery engine contain no workflow- or phrase-specific
  control-flow branches for this behavior.
- Adding a discoverable workflow is registry-only from the discovery engine's point
  of view.
- Existing routing, planning, validation, execution, and full-suite tests remain
  green.
