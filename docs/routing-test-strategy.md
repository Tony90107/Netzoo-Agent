# Routing test strategy (P2)

## What each layer proves

| Layer | Entry point | Evidence | Does not prove |
| --- | --- | --- | --- |
| Deterministic contracts | Matcher, evidence validator, registry-derived invariants | Known structured meanings respect input/output and authority contracts | Natural-language understanding |
| Offline routing integration | Production `invoke_router`, progress renderer, selected-guidance `respond`, Next step and continuation controls | Interpreter → review → validation → matching → intent → complete terminal guidance; bounded failures and diagnostics | Real provider/model accuracy |
| Provider wire contract | Real ChatOpenAI SDK with intercepted HTTP requests | Provider-bound function schema retains required fields and artifact constraints; invalid function arguments reach reviewer; complete/incomplete scripted repairs take correct paths | The provider's own schema processing or model accuracy |
| Interactive terminal acceptance | PTY subprocess + ANSI screen emulator | Next step and navigation remain readable at narrow widths and after resize; keyboard submission still works | Every terminal emulator or arbitrarily short windows |
| Live raw-prompt evaluation | Same production boundaries, real configured routing provider | Public prompts are interpreted and matched without injecting the answer key; selected final guidance satisfies corpus assertions | General free-prose answer quality, file validation or biological clustering quality |
| Graph and scientific integration | Existing LangGraph and container tests | Full state transitions, execution gates and package artifacts | Robustness across untested prompts or clinical validity |

Do not present typed-fixture success as natural-language accuracy, corpus validation
as a live run, or a skipped integration test as passed. New test infrastructure
does not run scientific algorithms or authorize analysis.

## Runtime consistency boundaries

- `contracts/artifact_semantics.py` defines output-type semantics, not per-tool
  routing rules. For example, cluster assignments concern samples and are one
  cohort-level result; pathway scores concern pathways/samples, not genes. Unknown
  dimensions remain unresolved. Regulatory roles cannot leak into unrelated outputs.
- `exact` is distinct from `fallback`. Feature lookup, partial-evidence recovery,
  and schema/evidence recovery preserve `match_basis`; an unconfirmed recommendation
  never becomes an executable decision. CLI fallback progress is a warning,
  not exact-workflow success and not automatically a clarification request.
- The provider schema constrains entities, granularity and role lists by artifact
  type using the same ontology as the strict post-generation validator. Providers
  may ignore schema constraints, so deterministic validation remains mandatory.
  A failed proposal is retained transiently for one reviewer call, including when
  the structured adapter rejects its nesting. Feedback includes actual fields,
  permitted fields and required evidence repairs. Invalid values are never accepted
  merely because the second call also failed.
  Every artifact branch repeats the required outcome fields with their types;
  root properties remain authoritative for optional fields. Missing-field feedback
  resolves the exact hypothesis index, maps it to the review's singular hypothesis,
  and supplies the required field list, enum/type and evidence repair instructions.
  This does not fill missing operations from workflow defaults or relax validation.
- Recovery leaves `requested_outcome` unset; candidate-compatible lexical inputs
  live in `guidance_input_artifacts`, explicitly not a validated current-input
  classification. Candidate outputs remain registry facts, not user requirements.
  Existing validated partial goals are not overwritten by feature-based matching.
- `guidance_interaction` owns fallback answer/progress/follow-up policy. Only a
  concrete missing-choice question triggers clarification. Parser/provider failure
  does not require the user to reformulate an already clear goal. A candidate alone
  exposes neither a ready plan nor a workflow continuation. Even an acceptance reply
  must return through semantic validation rather than adopt candidate defaults.
- `RejectedMethod` carries the action, rejected current input, accepted inputs,
  reason code and explanation. The response contract recomputes these assertions
  from registry facts. A historical method mention is not evidence that the previous
  analysis was wrong; every rejection is scoped to the current input contract.
- Selected capability recommendations use code-owned rendering of registered
  inputs, transformations and distinct artifact definitions. They do not ask a
  free-text model to rewrite rejection polarity or artifact meanings. Existing
  deterministic composition/script renderers remain for compatible exact paths;
  rejection/fallback handling takes precedence. General conceptual and retrieval
  answers still have a response-model path; this is not an arbitrary-prose validator.
- New workflows using existing artifact types inherit these constraints. A new
  artifact type needs an explicit semantic definition; the ontology coverage test
  fails until one is supplied. No SAMBAR-specific branch is added to these rules.
- Explanations are gated by declared transformations and the concerns in the
  question, never workflow-name branches. The original prompts separately explain
  normalization, sparse pathway aggregation and input/method boundaries. Artifact
  definitions and rejection polarity remain code-owned. The mutation explanations
  follow [the primary methods paper](https://www.nature.com/articles/s41416-018-0109-7);
  clustering quality is not guaranteed and relative burden normalization is not a
  clinical TMB estimate.

## Offline regression

From the repository root, in the existing project Python environment:

```bash
python -m pytest -q tests/test_guidance_consistency.py tests/test_routing_evaluation.py tests/test_routing_registry_invariants.py tests/test_test_strategy.py tests/test_harness_evaluation.py --fail-on-skip
python -m pytest -q tests/test_semantic_repair_interaction.py --fail-on-skip
python -m pytest -q -rs
python -m ruff check scripts tests
python scripts/evaluate_harness.py --json
python scripts/evaluate_routing.py --json
```

The last command **only validates the corpus** and prints its IDs. It never builds
a provider or prints an accuracy score. Ordinary pytest does not make live API
calls. The offline provider responses are independently scripted; the evaluator
does not synthesize them from expected answers.

Registry invariants enumerate all registered workflows and their declared input
contracts. New workflows join those checks automatically. They are necessary but
not sufficient: a new scientific capability also needs human-authored raw prompts
and negative controls in `tests/routing_scenarios.json`.

Fault cases cover provider timeout, provider ValueError, malformed schema, repaired
schema, ungrounded evidence on both attempts, intent failure, mistaken execute
intent, joint semantic/intent misclassification, and budget exhaustion. The tests
also validate the evaluator's own scoring and exit statuses. A wrong typed output
must fail semantic scoring even when the selected action happens to be right.

The legacy Planner corpus is now covered by pytest as well. Its demo/discovered
input cases must stop at `needs_confirmation`, with no executable steps, instead
of assuming discovery authorizes execution. The unsupported variant-calling
case now supplies the upstream `no_tool` decision for a typed acquisition goal;
a separate assertion verifies that the matcher rejects that goal. The Planner
does not own semantic classification. An explicit-role PUMA case preserves a
positive `ready` control. Planner scoring checks expected steps and
counts a bypass of input confirmation as unsafe autofill; an empty corpus fails.

## Live evaluation (explicit opt-in)

Use an environment containing the project's existing `langchain-openai` dependency.
Provide `OPENROUTER_API_KEY` securely in that environment; the evaluator does not
load `.env` automatically or print credentials. It reuses `build_llm`, the router
model allowlist, temperature 0, timeout and structured-output conventions. No new
provider SDK or endpoint is introduced.

These commands make billable provider requests and send the selected prompts to
the configured provider. The bundled prompts are public, synthetic scenarios;
do not add patient data, secrets or private paths to the corpus.

Start with the three original reproduction prompts (at most 9 logical calls):

```bash
python scripts/evaluate_routing.py --live --case original-q1 --case original-q2 --case original-q3 --max-calls 9 --json
```

Run all 14 cases three times for a repeatability check (at most 126 logical calls):

```bash
python scripts/evaluate_routing.py --live --repeat 3 --max-calls 126 --json
```

The default call cap is 12. Oversized runs are rejected before provider creation.
`--timeout` is per call, defaults to 30 seconds, and is bounded to 60 seconds.
Each trial starts with fresh routing usage/state and retains the production task
token budget. The production provider has retries disabled. The cap is a call
bound, not a currency-spend guarantee.

The evaluator invokes routing and, when a workflow is selected or rejected, the
production final guidance node with a read-only `respond_only` plan. It never calls
the Planner, executor, memory stores, content mapper or a response model. Thus the
three-provider-call bound is unchanged. Even if a model incorrectly classifies a
guidance prompt as execution, the evaluator reports a safety failure without
performing the action. Reports contain structured routing results, final guidance and
sanitized diagnostic categories, not raw provider error messages. It captures the
actual public progress renderer, shares routing-progress publication with the CLI,
and renders the actual Next step prompt (including navigation). The scorer rejects
false clarification, exact-success signals on fallback, and unvalidated continuation
controls independently of answer correctness.

### Reviewer repair replay

The September failure traces retained issue codes, not complete rejected proposals.
`scripts/routing_repair_replay.py` therefore contains explicit **reconstructions**:
distance granularity/roles, cluster granularity/missing operation evidence, and
misplaced root assumptions/multi-omic roles. They are not raw captured model output.
The failed proposal is supplied to the real production reviewer; expected answers
remain outside model messages. A normal raw-prompt trial is still needed to evaluate
the first-pass interpreter.

Validate replay selection without any provider call:

```bash
python scripts/evaluate_routing.py --repair-replay --json
```

Explicitly opt into at most six logical provider calls (three reviewers, plus
up to three intent calls):

```bash
python scripts/evaluate_routing.py --live --repair-replay --max-calls 6 --json
```

`review_repair_validation_rate` measures accepted repairs; `review_repair_rate`
also requires gold semantic dimensions and the correct route. The denominator is
first-pass validation failures, not every routine review; an empty denominator is
`null`. Failed repairs remain fallback failures. `first_pass_source` labels injected
reconstructions; `provider_calls` excludes injections, while `total_tokens` retains
the conservative production budget estimate, including the injected first pass.
Offline scripted-reviewer results exercise the scorer only, never model repair rate.

### Latest missing-required-field batch

The newer three traces all omitted `outcome.operation`; Q2 also omitted
`granularity`, and Q3 omitted `operation` in both hypotheses. The reviewer again
omitted `operation` in all three. This is **not** the old missing-operation-evidence
case. Preserve the old replay and select this batch explicitly:

```bash
python scripts/evaluate_routing.py --repair-replay --repair-replay-suite missing-required --json
# Paid model calls only with this explicit opt-in:
python scripts/evaluate_routing.py --live --repair-replay --repair-replay-suite missing-required --max-calls 6 --json
```

Both suites remain reconstructions of error locations, not raw captured proposals.
Reports record `repair_replay_suite`. Also run the three raw prompts without replay
to measure first-pass performance; neither corpus validation nor scripted repair
success changes the last observed live exact-match/complete-repair result of 0/3.

### Offline wire and PTY gate

Install the acceptance dependencies in an isolated environment based on the project
environment, then require these tests to run with **zero skips**:

```bash
python -m pip install -r requirements-acceptance.txt
python -m pytest -q tests/test_semantic_provider_wire.py tests/test_missing_required_repair.py tests/test_terminal_pty.py tests/test_terminal_input.py tests/test_semantic_repair_interaction.py --fail-on-skip
```

The wire tests use the actual SDK function-calling adapter and `httpx.MockTransport`,
with an invalid endpoint and dummy key. They inspect the serialized HTTP body, not
just Pydantic's schema or a fixture adapter. No paid API calls are made. The pinned
acceptance SDKs are not production dependency pins and do not establish which
versions ran in a user's Docker image. In the tested SDK, root `required` already
survived conversion before the fix; the logs do not prove the SDK dropped fields.
The old artifact branches contained only partial refinements, so required fields
are now repeated explicitly there. Live effectiveness still requires measurement.

The PTY test drives production routing guidance into the actual prompt-toolkit
input application. It inspects the emulated screen at 40, 60 and 90 columns,
resizes the active prompt to 32 columns, then submits `exit`. It fails on clipped
`inputs.`, missing safety/navigation text, or broken key dispatch. This reproduced
the original truncation before `Window.wrap_lines=True` was added to the display
question, separately from the already-wrapping editable input. Existing string
surface tests cannot detect this renderer defect.

Validation recorded for this change (2026-09-04): the focused gate above passed
51 tests with zero skips. In the same LangGraph-enabled acceptance environment,
the full suite excluding the opt-in Docker test passed 842 tests and failed 16;
the unmodified `933f4ea` baseline passed 825 and failed the **same 16 test IDs**.
Those existing failures concern graph/response expectations and BONOBO tests;
they were not skipped, weakened or fixed as part of this bounded change. This is
not an all-green release gate. No live model or scientific Docker run was made.

User-supplied CLI/session observations after this change (2026-09-04, 17:15-17:16):

- Q1 and Q2 report `exact`; Q3 remains `fallback` with `registry_features`.
- All three final outcomes pass the internal validator, and no missing-required
  schema error is recorded. Q2's initial role/evidence errors were repaired.
  This is one observed validation repair, not three successful complete repairs.
- All three final `input_artifacts` lists are empty despite explicit mutation
  inputs. Q1 records `sample_distance_matrix` rather than the terminal cluster
  assignment; Q3 records `multi_omic_network` / `sample_specific` and loses the
  PANDA/LIONESS input rejections. Against the existing corpus's complete semantic
  labels, none of these three stored outcomes satisfies every required dimension.
- Next step text is fully visible across wrapped lines in all three transcripts.

Thus runtime exact labels improved from 0/3 to 2/3, but full semantic acceptance
must not be reported as 2/3. Follow-up priorities are explicit-current-input
completeness, distinguishing proposed means from terminal goals, and preserving
method compatibility assessment when semantic extraction omits inputs. These
remaining issues are not fixed by this schema/terminal checkpoint.

## Corpus and scoring

The initial corpus covers the three original mutation prompts, English and
Chinese paraphrases, a low-keyword variant, distance versus cluster outputs,
reverse historical context, sparse expression as a negative control, miRNA
networks, covariate coexpression, bipartite communities, multi-omic networks,
genuine missing granularity and unsupported measurement acquisition.

All current cases request **guidance only**. Do not add execution prompts without
extending the expectation model and safety scorer deliberately. `expected` fields
are test labels, never additions to the model prompt. Tool-specific names belong
in corpus expectations and registry contracts, not evaluator branches.

A case passes only if:

1. The final review passes the production schema/evidence validator.
2. Current input, output, entities and granularity match every specified gold dimension.
3. Match status and actions match the label, with no forbidden recommendation.
4. A real ambiguity receives a clarification; an exact result does not get an
   unnecessary clarification.
5. Guidance does not authorize execution and the three-call route bound holds.
6. The pipeline completes normally, rather than using semantic or intent fallback.
7. Where applicable, the actual final answer satisfies `answer_required` and
   `answer_forbidden` assertions. Unselected/general prose cases are explicitly
   `answer_evaluated=false`, not reported as passed final-answer tests. If such a
   case requires final-answer assertions, unevaluated means failure.
8. The complete guidance surface passes progress/answer/Next step consistency
   checks. Mutating only progress or continuation controls must fail the evaluator,
   even when the selected workflow and answer are otherwise correct.

`route_pass_rate`, `semantic_pass_rate` and final-answer results are separate.
Recommending the expected action through fallback does not pass an `exact`
expectation. `fallback_count` and `registry_recovery_count` expose recovery instead
of counting it as normal success. `answer_evaluated_count` and
`answer_failure_count` report final-guidance coverage separately. Reports include
schema/evidence/provider/intent/budget diagnostics, per-language and per-category
breakdowns, every trial result, unstable case IDs, model name, policy hash and
prompt/schema/corpus fingerprints. Fixture reports say `source=fixture`; they are
not model-performance measurements. A repaired first-pass schema can still pass,
but remains visible in diagnostics.

Exit codes: `0` = selected live trials all passed (or corpus-only validation
succeeded); `1` = a live trial failed; `2` = configuration/dependency/corpus error.
Never compare the exit code alone without checking the report mode/source.

## Acceptance and remaining boundaries

For a release, require the offline suite to pass and review live results for all
original prompts and negative controls. Require zero unsafe authorizations and
zero forbidden recommendations. Investigate any fallback, per-language failure
or instability rather than hiding it in an average. Three repetitions are a
small regression sample, not a statistical guarantee of model reliability.

In the LangGraph-enabled project environment, run the suite without silently
accepting missing graph coverage:

```bash
python -m pytest -q --fail-on-skip --ignore=tests/test_sambar_container.py
```

The Docker scientific regression is a separate opt-in gate on a Docker-enabled
host, using the existing project image/setup:

```bash
NETZOO_RUN_DOCKER_TESTS=1 python -m pytest -q tests/test_sambar_container.py --fail-on-skip
```

Without the required dependencies these gates must fail, not look green. Normal
local runs may omit `--fail-on-skip` for convenience, but must report skip counts.

The original three prompts now assert final guidance as well as semantic fields.
Regression tests also inject adversarial final text to prove that correct routing
cannot hide an answer failure, and verify that an unconstrained response provider
cannot overwrite a selected recommendation. These assertions protect the bounded
recommendation path, not all possible scientific discourse. Live-provider results
still need review; passing these tests says nothing about biological subtype
quality, which needs scientific fixtures and appropriate downstream validation.
