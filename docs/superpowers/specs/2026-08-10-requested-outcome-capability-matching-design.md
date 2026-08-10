# Requested Outcome Capability Matching Design

**Status:** Approved for implementation planning

## Goal

Prevent the NetZoo Agent from presenting a related workflow as though it can
produce a user's requested deliverable when the workflow actually produces a
different artifact.

The solution must generalize across workflows, biological entities, languages,
and paraphrases. It must compare a normalized requested outcome with explicit,
registry-owned workflow output contracts instead of routing from isolated words
or workflow-specific regular expressions.

When the requested deliverable is unsupported, the Agent must explain the
capability gap and may ask whether the user wants the nearest supported outcome.
It must not describe that alternative as a match unless the user confirms the
changed objective.

## Current Problem and Root Cause

The request below reproduces the bug:

```text
if i want to get sample specific mi-RNA data, what tools do i need?
```

`infer_goal_capability_match()` correctly finds no supported goal because the
request does not ask for a regulatory network. However,
`infer_advisory_capabilities()` then applies a broader fallback that treats the
co-occurrence of sample-specific and miRNA concepts as sufficient evidence for
PUMA plus LIONESS-PUMA. `repair_router_decision()` uses that fallback for
information questions and replaces the Router's uncertainty with those
recommendations. The CLI response consequently explains workflow inputs even
though PUMA and LIONESS-PUMA infer regulatory networks; they do not acquire or
generate sample-specific miRNA measurement data.

An existing test, `test_sample_specific_mirna_guidance_recommends_puma_and_lioness`,
records this false-positive recommendation as expected behavior. The failure is
therefore not only prompt behavior. It is encoded in deterministic routing and
its tests.

The broader architectural issue is that the current decision model conflates
three different concepts:

1. what the user requested;
2. which workflow exactly satisfies that request;
3. which workflow is merely related and could be offered as an alternative.

`recommended_actions` cannot represent that distinction. A related workflow can
therefore be promoted into an apparent match.

## Design Principles

1. **Match deliverables, not words.** Natural-language expressions are evidence
   used to normalize a request, not direct workflow authorization.
2. **The Router describes; code decides.** The LLM extracts a bounded semantic
   outcome. It does not grant a workflow recommendation or execution authority.
3. **Workflow outputs are explicit contracts.** Each run workflow declares the
   operation and artifact it produces, including relevant biological roles and
   granularity.
4. **Exact matches and alternatives are separate.** A nearby capability never
   appears in `recommended_actions` until its outcome is confirmed.
5. **Uncertainty fails conversationally, not silently.** Ambiguous requests lead
   to one minimal clarification. Unsupported requests explain the mismatch and
   can offer a nearest supported outcome.
6. **Provider failure narrows behavior.** The deterministic fallback may use an
   explicit workflow name for stable information, but it must not infer an
   unnamed scientific deliverable from loose keyword combinations.
7. **Execution remains independently gated.** This design strengthens semantic
   alignment without weakening required-input checks, Plan Evaluator approval,
   or `/execute` authorization.

## Scope

### In scope

- Add a typed `RequestedOutcome` to Router output.
- Add typed output capability contracts for every registered run workflow.
- Validate YAML workflow output contracts against the Python registry.
- Add a deterministic outcome-to-capability matcher.
- Distinguish exact matches, ambiguous matches, and unsupported outcomes.
- Separate exact recommendations from suggested alternatives.
- Render deterministic clarification and capability-gap responses.
- Remove the loose advisory fallback that caused this false positive.
- Update Router prompts, trace summaries, CLI follow-ups, policy versioning,
  documentation, and tests to use the new semantics.
- Preserve explicit named-workflow questions such as "What inputs does PUMA
  require?" without requiring the user to restate PUMA's output artifact.

### Out of scope

- Acquiring miRNA, gene-expression, sequencing, or other external datasets.
- Adding a new Network Zoo analysis workflow.
- Using embeddings or another LLM call to judge capability compatibility.
- Building a general biological ontology.
- Inferring arbitrary conversions between artifact types.
- Changing file discovery, input validation, execution wrappers, Plan Evaluator
  rules, or `/test` and `/execute` authorization.

## Domain Model

### Requested outcome

The Router returns a normalized description of the user's requested result:

```python
Operation = Literal[
    "acquire",
    "prepare",
    "validate",
    "infer",
    "analyze",
    "explain",
    "unknown",
]

ArtifactType = Literal[
    "measurement_dataset",
    "expression_matrix",
    "regulatory_network",
    "coexpression_network",
    "community_assignment",
    "validation_report",
    "unknown",
]

EntityType = Literal[
    "tf",
    "mirna",
    "gene",
    "protein",
    "sample",
    "unknown",
]

Granularity = Literal[
    "aggregate",
    "sample_specific",
    "not_applicable",
    "unknown",
]

class RequestedOutcome(BaseModel):
    operation: Operation
    artifact_type: ArtifactType
    entity_types: list[EntityType] = Field(default_factory=list, max_length=8)
    display_entities: list[str] = Field(default_factory=list, max_length=8)
    regulator_types: list[Literal["tf", "mirna", "unknown"]] = Field(
        default_factory=list, max_length=3
    )
    target_types: list[Literal["gene", "unknown"]] = Field(
        default_factory=list, max_length=3
    )
    granularity: Granularity
    unresolved_dimensions: list[str] = Field(default_factory=list, max_length=4)
```

The bounded vocabularies describe capability-relevant distinctions, not every
possible biological concept. `entity_types` provides a small typed vocabulary
for generic matching and alternative ranking. `display_entities` preserves
normalized free text for explanations and future extension, but code does not
branch on individual names from that field. Exact compatibility uses typed
fields such as `artifact_type`, `entity_types`, `regulator_types`,
`target_types`, and `granularity`.

For the reproducing request, the expected normalized outcome is:

```python
RequestedOutcome(
    operation="acquire",
    artifact_type="measurement_dataset",
    entity_types=["mirna"],
    display_entities=["miRNA"],
    regulator_types=[],
    target_types=[],
    granularity="sample_specific",
    unresolved_dimensions=[],
)
```

If the phrase is genuinely ambiguous between a measurement dataset and a
regulatory network, the Router uses `artifact_type="unknown"` and records one
plain-language unresolved dimension. It must not choose the more convenient
supported interpretation.

### Workflow capability contract

Each run action declares what it produces independently of how users describe
it:

```python
class OutputCapability(BaseModel):
    operation: Literal["infer", "analyze"]
    artifact_type: ArtifactType
    entity_types: frozenset[EntityType]
    regulator_types: frozenset[Literal["tf", "mirna"]] = frozenset()
    target_types: frozenset[Literal["gene"]] = frozenset()
    granularities: frozenset[
        Literal["aggregate", "sample_specific", "not_applicable"]
    ]
    guidance_predecessors: tuple[RecommendedAction, ...] = ()
```

Examples:

```text
PANDA
  infer regulatory_network
  regulators: tf
  targets: gene
  granularities: aggregate

PUMA
  infer regulatory_network
  entities: tf, mirna, gene
  regulators: tf, mirna
  targets: gene
  granularities: aggregate

LIONESS-PUMA
  infer regulatory_network
  entities: tf, mirna, gene
  regulators: tf, mirna
  targets: gene
  granularities: aggregate, sample_specific
  guidance predecessor: PUMA

LIONESS-COEXPRESSION
  infer coexpression_network
  granularities: aggregate, sample_specific

CONDOR
  analyze community_assignment
  granularities: not_applicable
```

The Python `ActionDefinition` remains the authority for executable actions and
gains an `output_capability` field. Workflow YAML mirrors that contract for
validated policy and human inspection. `ProjectPolicyLoader` fails closed when
the YAML and Python contracts differ.

Because output capability becomes a required policy field and changes the
meaning of valid workflow policy, `AGENTS.md`, workflow YAML, and policy Pydantic
contracts move from `policy_version: 1` to `policy_version: 2`. Version 1 is not
silently reinterpreted.

## Matching Semantics

The matcher has a small, pure interface:

```python
class CapabilityMatch(BaseModel):
    status: Literal["exact", "ambiguous", "unsupported"]
    matched_actions: list[RecommendedAction] = Field(default_factory=list)
    alternative_actions: list[RecommendedAction] = Field(default_factory=list)
    mismatch_dimensions: list[str] = Field(default_factory=list)
    clarification_question: str | None = None

def match_requested_outcome(
    outcome: RequestedOutcome,
    capabilities: Mapping[RecommendedAction, OutputCapability],
) -> CapabilityMatch: ...
```

Matching proceeds by typed dimensions in this order:

1. operation;
2. artifact type;
3. granularity;
4. regulator role, when relevant to the artifact;
5. target role, when relevant to the artifact.

An action is an exact candidate only when every explicitly requested dimension
is supported. Unknown or unresolved dimensions cannot create an exact match.

The result rules are:

- **exact:** at least one capability satisfies every specified dimension and no
  required selection dimension is unresolved;
- **ambiguous:** more information could select among otherwise compatible
  capabilities, or a capability-relevant requested dimension is unknown;
- **unsupported:** at least one explicit requested dimension conflicts with all
  registered capabilities.

Multiple exact actions can have either an alternatives or composition
relationship. That relationship is registry metadata, not inferred from the
number or ordering of actions. The end-to-end exact action for a sample-specific
miRNA regulatory network is LIONESS-PUMA. Its capability contract declares PUMA
as a `guidance_predecessor`, allowing the Agent to explain the aggregate PUMA
stage followed by sample-specific LIONESS-PUMA without treating a separate PUMA
run as another authorized execution action.

Alternative ranking is deterministic and explanatory only. It counts matching
typed dimensions, requires overlap in `entity_types`, and
uses a stable registry order for ties. This permits a sample-specific miRNA
regulatory network to be offered as an alternative to unsupported
sample-specific miRNA measurements because the entity and granularity overlap,
while preventing an unrelated CONDOR community workflow from being suggested.
At most two alternatives are returned. Alternatives never authorize execution
and never populate exact-match fields.

## Router and Decision Contract Changes

`RouterDecision` gains `requested_outcome` and stops exposing
`recommended_actions`, `candidate_actions`, and top-level
`unresolved_dimensions` as model-controlled workflow selections. The Router
prompt lists the normalized outcome vocabulary and instructs the model to
preserve unknowns instead of completing a supported goal on the user's behalf.

`TaskDecision` gains:

```python
requested_outcome: RequestedOutcome | None = None
capability_match_status: Literal["exact", "ambiguous", "unsupported"] | None
matched_actions: list[RecommendedAction] = Field(default_factory=list)
alternative_actions: list[RecommendedAction] = Field(default_factory=list)
mismatch_dimensions: list[str] = Field(default_factory=list)
```

`matched_actions` contains only exact end-to-end capabilities and is the only
match field consulted by the capability gate. `recommended_actions` remains for
downstream compatibility but becomes a code-owned guidance sequence. It is
derived from the selected exact action's `guidance_predecessors` followed by the
exact action. For LIONESS-PUMA guidance this may be
`[run_puma, run_lioness_puma]`, while `matched_actions` contains only
`[run_lioness_puma]`. Hydration initializes both lists empty; deterministic
matching and registry metadata alone may populate them.

The Router may still return a proposed `action` because the existing structured
interface also routes documentation and input-preparation requests. A proposed
local run action is an untrusted hint. Repair and the capability gate replace or
reject it unless it belongs to the code-owned `matched_actions` result.

Named workflow requests are a separate, explicit route. When the user names a
registered workflow and asks about its purpose, inputs, or execution, the name
selects the workflow contract. This preserves stable questions such as "PUMA
需要哪些 input？". It does not permit a named workflow to satisfy a simultaneously
requested, conflicting deliverable. For example, "Can PUMA download raw miRNA
measurements?" produces a capability mismatch, not PUMA input guidance.

## End-to-End Data Flow

1. The Router reads only the latest user turn and returns intent plus a
   `RequestedOutcome`.
2. Pydantic rejects unknown enum values, excess fields, and oversized lists.
3. Hydration extracts paths and other deterministic inputs as it does today.
4. The capability matcher compares the requested outcome with code-owned output
   contracts.
5. Repair may correct an under-routed action only from an exact matcher result.
   It may not manufacture recommendations from loose keyword combinations.
6. The capability gate rechecks that any local run action belongs to
   `matched_actions`. A model-proposed action outside that set becomes
   `no_tool`.
7. The graph stores the normalized outcome and match result as trusted typed
   state and emits a public summary derived from those fields.
8. Response rendering follows the match status:
   - exact information request: explain the matching registered workflow;
   - exact execution request: continue through the existing planner and gates;
   - ambiguous: ask the single matcher-produced clarification;
   - unsupported: state the requested-versus-produced artifact mismatch and ask
     whether the user wants the nearest supported outcome.
9. Only a new user turn explicitly confirming the alternative creates a new
   requested outcome and can yield an exact match.

For the reproducing request, the response should be equivalent to:

```text
The registered NetZoo workflows do not acquire sample-specific miRNA
measurement data. LIONESS-PUMA can instead infer sample-specific miRNA/TF-to-gene
regulatory networks from an expression matrix and regulatory priors. Did you
mean that regulatory-network result?

No files were inspected and no analysis ran.
```

The exact wording may be polished, but it must retain the capability distinction
and non-execution statement.

## Provider Failure and Deterministic Fallback

When the Router provider fails, the fallback may safely handle:

- an explicitly named registered workflow;
- an explicit local execution action with the required method name;
- existing deterministic commands and continuation markers.

For unnamed goal-first requests, the fallback returns `no_tool` with an
unresolved outcome and asks the user to restate the desired artifact. It no
longer uses combinations such as sample-specific plus miRNA to infer a workflow.
This intentionally prefers a clarification over a false scientific claim.

## Response and Follow-Up Behavior

The response layer must not send an unsupported or ambiguous outcome through
the current generic prompt with a non-empty `recommended_actions` list. It uses
deterministic renderers for capability mismatch and minimal clarification.

CLI follow-up state distinguishes:

- `recommended_workflow`: exact and safe to continue;
- `clarify_outcome`: missing semantic dimension;
- `alternative_outcome`: unsupported request with a nearby supported result;
- `unsupported`: no meaningful registered alternative.

Answering yes to an alternative prompt is converted into a canonical
continuation that quotes the proposed supported outcome. It is not treated as
approval to execute. Existing `/execute` authorization and required-input
collection still apply afterward.

## Testing Strategy

### Matcher unit tests

Table-driven tests cover every registered capability and each typed dimension:

- exact artifact, operation, granularity, regulator, and target matches;
- a conflicting operation;
- a conflicting artifact;
- a conflicting granularity;
- an unknown or unresolved artifact;
- multiple alternatives;
- a registered composition;
- stable alternative ordering;
- no semantically nearby alternative.

These tests call the pure matcher without an LLM.

### Language-variation contract tests

Router fixture tests use varied wording without making individual phrases part
of production routing logic:

- synonyms and paraphrases;
- English and Chinese requests;
- spelling and punctuation variation;
- requests that mention input data versus output artifacts;
- negation, such as "I do not want a network";
- questions about whether a named tool can produce an unsupported artifact;
- mixed supported and unsupported deliverables.

The goal is not to prove that every phrase is understood. It is to prove that
uncertainty never becomes an exact capability match.

### Regression tests

Replace the existing false-positive test with assertions that:

- sample-specific miRNA measurement data has no exact recommendation;
- LIONESS-PUMA appears only as an alternative when appropriate;
- sample-specific miRNA regulatory-network inference exactly matches the
  PUMA/LIONESS-PUMA composition;
- provider failure does not restore the false-positive recommendation;
- the response states the capability gap and asks for confirmation;
- no plan or executor access is created before confirmation.

### Policy and safety tests

- every run action has one valid output capability;
- YAML and Python output contracts must match exactly;
- version 1 policy is rejected after the version 2 migration;
- Router-supplied actions cannot bypass matcher output;
- unknown outcome enum values fail validation;
- alternative actions never pass the capability or Plan Evaluator gates;
- existing workflow input validation and `/execute` tests continue to pass.

## Migration Sequence

1. Add outcome and capability contract models with unit tests.
2. Add output capability metadata to the Python registry.
3. Migrate `AGENTS.md`, all workflow YAML, and policy schemas to version 2;
   enforce YAML/Python equality.
4. Implement the pure capability matcher and table-driven tests.
5. Change Router output and prompt to produce `RequestedOutcome`.
6. Change hydration, repair, and capability gating so only matcher results can
   populate exact recommendations.
7. Remove the broad advisory fallback and replace its regression test.
8. Add deterministic ambiguous and unsupported response renderers plus CLI
   follow-up behavior.
9. Update traces and user documentation.
10. Run focused routing tests, the full test suite, and representative TEST-mode
    CLI conversations.

## Acceptance Criteria

- The reproducing miRNA-data question does not claim that PUMA or LIONESS-PUMA
  can obtain the requested data.
- The Agent explains the unsupported deliverable and asks whether the user means
  the nearest supported network result.
- A paraphrased sample-specific miRNA regulatory-network request still matches
  the PUMA/LIONESS-PUMA composition.
- The matching implementation branches on typed outcome dimensions, not on
  individual biological phrases.
- Router output alone cannot select or authorize a workflow.
- Ambiguous outcomes never become exact recommendations.
- Suggested alternatives cannot reach planning or execution.
- Explicit named-workflow input and purpose questions continue to work.
- Provider failure does not broaden semantic inference.
- Policy loading fails closed when output contracts are absent or disagree with
  the Python registry.
- All existing execution authorization, validation, and Plan Evaluator tests
  continue to pass.
