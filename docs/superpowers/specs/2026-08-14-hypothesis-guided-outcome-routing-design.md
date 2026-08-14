# Hypothesis-Guided Outcome Routing Design

**Status:** Approved design; awaiting written-spec review

## Goal

Improve the NetZoo Agent's ability to infer likely workflows from incomplete or
informal scientific requests without encoding answers for particular sentences.

For an underspecified request, the Agent should preserve plausible interpretations,
compare them with registry-owned workflow capabilities, explain the best-supported
hypothesis, and ask the smallest useful confirmation question. Uncertainty must still
prevent execution.

The motivating requests are:

```text
if i want to get sample specific network data, what tools do i need?
```

```text
if i want to get sample specific mi-RNA network data, what tools do i need?
```

The second request should identify `PUMA → LIONESS-PUMA` as the uniquely compatible
registered composition under the hypothesis that "miRNA network data" means a
sample-specific miRNA regulatory network, then ask the user to confirm that
interpretation. The first request has no evidence that justifies ranking a TF/miRNA,
TF-only, or co-expression network first, so it must present the compatible network
families without an artificial priority and ask which relationship the user means.

## Observed Failure and Root Cause

The saved sessions show that the Router recognized the requests at a prose level but
returned an almost empty typed outcome.

For the generic request it returned:

```text
operation=unknown
artifact_type=unknown
entity_types=[]
regulator_types=[]
granularity=sample_specific
```

For the request that explicitly included `mi-RNA`, it returned:

```text
operation=unknown
artifact_type=unknown
entity_types=[]
regulator_types=[]
granularity=not_applicable
```

This exposes three separate defects:

1. **Semantic under-classification.** The Router discarded explicit scientific
   concepts such as miRNA and sample-specific granularity instead of representing
   them as evidence or hypotheses.
2. **All-or-nothing capability matching.** `match_requested_outcome()` immediately
   returns an ambiguous result when any relevant dimension is unknown. It does not
   compute compatible candidates from the dimensions that are known.
3. **Lossy response rendering.** `render_outcome_clarification()` ignores possible
   workflows and renders the same negative template for every ambiguous result. It
   therefore loses both the original context and the Router's prose-level insight.

The failure is not simply insufficient conversation history. It is a context
engineering problem at component boundaries: rich user language is compressed into
one brittle record, uncertainty erases usable evidence, and later components cannot
recover it.

## Design Principles

1. **Preserve evidence before deciding.** Extracted facts, inferred facts, and open
   assumptions must remain distinguishable.
2. **Hypotheses are not authority.** A likely interpretation can drive an explanation
   or confirmation question, but only a complete exact capability match can authorize
   planning or execution.
3. **Match registry semantics, not complete phrases.** Workflow recommendations must
   be derived from `OutputCapabilityDefinition` and `guidance_predecessors`, not from
   a lookup table of user sentences.
4. **Known dimensions remain useful.** An unknown field must not erase valid evidence
   from other fields.
5. **Detect implausibly empty classifications.** A scientific tool-selection request
   that becomes an all-unknown outcome is a classification failure, not a valid final
   interpretation.
6. **Clarify with a useful hypothesis.** The response should state what the Agent
   currently thinks the user means, why that maps to a workflow, and exactly what
   assumption needs confirmation.
7. **Keep execution fail-closed.** No change may weaken input validation, plan
   evaluation, mode authorization, or the exact-match execution gate.

## Scope

### In scope

- Extend the LLM-facing outcome representation to preserve bounded candidate
  hypotheses and evidence.
- Detect semantic under-classification and allow one bounded reclassification.
- Add partial capability matching for advisory candidates.
- Keep exact matches, advisory hypotheses, and unsupported alternatives separate.
- Render registry-grounded, hypothesis-led clarification responses.
- Update tracing so the classification, candidate ranking, and unresolved assumption
  can be audited.
- Add regression and paraphrase tests for regulatory, co-expression, and measurement
  requests.

### Out of scope

- Adding new NetZoo scientific workflows.
- Building an unrestricted biological ontology.
- Using embeddings or vector search for routing.
- Allowing partial matches or LLM suggestions to authorize execution.
- Changing input discovery, validation, Plan Evaluator rules, or `/test` and
  `/execute` authorization.
- Encoding the motivating English sentences as exact-match rules.

## Proposed Architecture

### 1. Evidence-bearing outcome hypotheses

The Router should return a bounded list of one to three hypotheses instead of being
forced to collapse uncertainty into one empty `RequestedOutcome`.

Each hypothesis contains:

```python
class OutcomeEvidence(BaseModel):
    dimension: Literal[
        "operation",
        "artifact_type",
        "entity_type",
        "regulator_type",
        "target_type",
        "granularity",
    ]
    value: str
    source: Literal["explicit", "inferred"]
    rationale: str


class OutcomeHypothesis(BaseModel):
    outcome: RequestedOutcome
    confidence: float
    evidence: list[OutcomeEvidence]
    assumptions: list[str]
```

The implementation uses the `OutcomeEvidence` and `OutcomeHypothesis` contracts shown
above. `RouterDecision` exposes `outcome_hypotheses` with one to three items instead of
requiring one lossy `requested_outcome`. `TaskDecision` retains `requested_outcome` for
compatibility only when one hypothesis has strictly stronger semantic evidence; it is
`None` when the best hypotheses remain tied. `TaskDecision` also stores the bounded
`outcome_hypotheses` list for advisory rendering and audit. Lists remain small and text
fields remain bounded to preserve predictable model output and trace size.

Examples of general semantic behavior:

- `miRNA`, `micro RNA`, or a translated equivalent is explicit regulator/entity
  evidence when the user connects it to a network.
- `sample-specific`, `per patient`, or an equivalent phrase is explicit granularity
  evidence.
- `network data`, `network result`, and `edge scores` identify a network artifact
  rather than a raw measurement dataset when the surrounding request asks what
  method produces that network.
- `miRNA measurements`, `expression values`, or `raw data` remain measurement
  artifacts and must not be promoted to regulatory-network inference.

These are semantic distinctions described to the Router, not exact sentence-to-action
mappings.

### 2. Semantic consistency gate and bounded retry

After the first Router response, code validates the classification structurally and
semantically.

A result is under-classified when all of the following are true:

- the request is a scientific result or tool-selection question;
- the Router returns no usable entity, artifact, operation, or granularity evidence;
- the Router supplies no meaningful assumption explaining why those dimensions are
  unknowable.

Under-classification triggers one retry with a repair prompt containing:

- the original request;
- the first structured result;
- the validated workflow capability catalog;
- an instruction to recover explicit evidence, return competing hypotheses when
  necessary, and avoid selecting an executable action.

The retry limit is exactly one. If it still fails, the Agent remains non-executable
and presents the registry-derived candidate families that can be supported from any
remaining known evidence. It must not loop or silently fabricate certainty.

### 3. Partial advisory matching

The capability matcher gains a second, non-authoritative matching mode.

Exact matching keeps the current strict semantics: every required outcome dimension
must be known and compatible. Only an exact match may populate `matched_actions` or
participate in execution authorization.

Advisory matching compares the known dimensions of each hypothesis with every
registry capability:

- an incompatible known dimension eliminates a capability;
- an unknown dimension contributes neither a match nor a mismatch;
- explicit evidence weighs more than inferred evidence;
- more supported known dimensions rank higher;
- unsupported artifact or operation changes remain alternatives, not hypotheses;
- equal evidence and conflict scores remain tied; registry order may stabilize display
  order but must never be described as scientific preference or greater confidence.

The result model distinguishes:

```text
matched_actions       complete exact matches only
hypothesis_actions    compatible candidates for an ambiguous interpretation
alternative_actions  nearby workflows that require changing the requested outcome
```

For a compatible LIONESS end-to-end action, explanation steps are expanded from its
registry-owned `guidance_predecessors`. Therefore `run_lioness_puma` becomes
`run_puma → run_lioness_puma` without embedding that sequence in response text or
task-specific rules.

### 4. Candidate selection behavior

For `sample-specific miRNA network data`, a well-formed hypothesis contains:

```text
artifact_type=regulatory_network
regulator_types=[mirna]
target_types=[gene] or target_types=[unknown]
granularity=sample_specific
```

The registered capability set makes `run_lioness_puma` the only compatible
sample-specific miRNA regulatory-network workflow. The UI explains the derived
`PUMA → LIONESS-PUMA` composition and asks the user to confirm the regulatory-network
interpretation. It does not execute.

For generic `sample-specific network data`, the evidence is insufficient to make one
scientific network type exact. The compatible candidates remain tied and are presented
without a claimed scientific ranking:

- `PUMA → LIONESS-PUMA` for TF/miRNA regulatory networks;
- `PANDA → LIONESS-PANDA` for TF-only regulatory networks;
- `LIONESS-COEXPRESSION` for sample-specific co-expression networks.

Display order is stable for readability only. The response must not label the first
item as more likely, recommended, or selected. It asks which network relationship the
user means, and none of the tied candidates receives execution authority.

### 5. Hypothesis-led clarification rendering

Replace the universal ambiguous template with a renderer that receives:

- normalized hypotheses and evidence;
- scored compatible-action groups, including unresolved ties;
- registry workflow names, descriptions, and predecessor relationships;
- the single unresolved assumption that most reduces ambiguity.

Compatible-action groups may contain a tied top group. The renderer must preserve that
tie and must not convert list order into a recommendation.

Expected response shape:

```text
It sounds like you want sample-specific miRNA regulatory networks.

The matching workflow composition is PUMA → LIONESS-PUMA: PUMA builds the
aggregate TF/miRNA-to-gene network, and LIONESS-PUMA estimates one network per
sample.

Is that the network result you mean?

No files were inspected and no analysis ran.
```

The exact wording may remain registry-driven, but the response must:

1. state the current interpretation;
2. distinguish an assumption from a confirmed fact;
3. show the derived workflow composition;
4. ask one focused confirmation question;
5. state that no analysis ran.

When multiple materially different candidates remain tied, the response names them
briefly and asks one discriminating question. It should not make the user restart the
problem description with an abstract question such as "What artifact should NetZoo
produce?"

## Data Flow

```text
user request
  → Router outcome hypotheses + evidence
  → semantic consistency gate
      → one bounded repair call when under-classified
  → strict exact matcher
  → partial advisory matcher
  → registry-derived predecessor expansion
  → exact answer, hypothesis-led clarification, or capability-gap response
```

Execution remains on the existing strict branch:

```text
exact outcome match
  + direct execution intent
  + required inputs
  + Plan Evaluator approval
  + current-session /execute authorization
  → Executor
```

## Error Handling and Observability

- Record whether a hypothesis came from the first Router call or the repair call.
- Record the under-classification reason without exposing hidden reasoning.
- Record candidate scores as bounded facts: matched dimensions, conflicting
  dimensions, and unresolved dimensions.
- Never record unrestricted chain-of-thought.
- If the repair call fails, retain the original safe decision and render the best
  registry-grounded clarification available.
- If no capability is compatible even partially, use the existing capability-gap
  response rather than inventing a workflow.

## Testing Strategy

### Unit tests

- An outcome with known miRNA and sample-specific dimensions but an unknown target
  produces `run_lioness_puma` only as an advisory hypothesis.
- Unknown dimensions do not erase compatible known evidence.
- Conflicting known dimensions eliminate a capability.
- `guidance_predecessors` expands LIONESS-PUMA guidance to PUMA followed by
  LIONESS-PUMA.
- Advisory hypotheses never appear in `matched_actions` and cannot pass the execution
  gate.
- An all-unknown scientific classification triggers exactly one repair attempt.

### Routing regression tests

- Preserve the two motivating requests verbatim.
- Add paraphrases in English and Chinese, including spelling and punctuation changes.
- Cover per-sample miRNA regulatory networks, TF regulatory networks, and
  co-expression networks.
- Verify that `sample-specific miRNA measurements`, `miRNA expression data`, and
  explicit requests for raw data do not become network inference.
- Verify that vague network requests preserve an unranked tie across materially
  different compatible network families.

### End-to-end response tests

- The miRNA-network request mentions `PUMA` and `LIONESS-PUMA`, explains their ordered
  relationship, and asks for confirmation.
- The response does not contain the generic `What artifact should NetZoo produce?`
  template for requests with usable network evidence.
- No files are inspected and no analysis executes during guidance.
- A confirmed supported outcome resumes through the existing continuation contract.

## Acceptance Criteria

1. Both motivating prompts receive useful, context-preserving workflow guidance.
2. The miRNA prompt derives `PUMA → LIONESS-PUMA` from semantic evidence and
   registry metadata rather than an exact sentence rule.
3. Generic sample-specific network wording preserves all equally supported network
   families without presenting one as the default or preferred tool.
4. Measurement-data requests remain protected from false network recommendations.
5. Partial or repaired interpretations cannot authorize execution.
6. Existing workflow, policy, planning, evaluation, CLI, and safety tests continue to
   pass.
