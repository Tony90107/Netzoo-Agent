# Semantic routing controls: mini baseline and isolated experiments

The default model configuration is unchanged. The production graph keeps the
existing `SemanticInterpretation` / `SemanticPatch` / `SemanticReview` provider
schemas and selects `review_policy="when_needed"`.

## Default behavior

- Skip the second semantic call only after evidence validation, a single outcome,
  known request mode and scientific operation, no unresolved dimensions, and an exact capability match
  (or the canonical non-scientific outcome). Schema validity alone is insufficient.
- Continue to use bounded repair for invalid or incomplete interpretations. A
  schema-invalid first reply requires a complete review; a parsed proposal uses
  the existing field patch contract. Intent, Plan Evaluator and executor authority
  are unchanged.
- Failed semantics no longer produces a workflow recommendation from phrase
  counts. Registry selection tags are no longer inferred by token overlap with
  the request. A failed interpretation remains a visible failure with no ready
  workflow. This can reduce recommendation coverage; it is not a measured gain
  in semantic accuracy.
- An explicit registered method identifier can still disambiguate a compatible,
  complete typed goal. Incomplete interpretations cannot be promoted by that name.
  Input and terminal-goal guards remain validation boundaries, not tool selectors.
- The default per-task token ceiling is 30,000. A measured interpreter + review +
  intent path used about 15,800 conservatively estimated tokens when provider usage
  metadata was absent; the final response brought the same four-call path to about
  25,500. A 25,000 ceiling therefore blocked a valid response. This is bounded
  capacity for the existing route, not evidence that a larger context improves
  semantic accuracy.

## Experimental contract (off by default)

`build_graph(..., semantic_contract="claims")` uses one `{value, support}` claim
per scientific field or list item. Internal outcome and evidence are projections.
Atomic field repairs replace a value and its support together and preserve other
fields and hypotheses. It does not let the model name or authorize tools.

This changes the provider schema and prompt. Earlier controlled results for the
legacy schema do not establish this contract's effectiveness. In particular, the
absence of mini trials blocked solely by conflicting evidence is no evidence of
a direct benefit on that corpus. Do not enable it as the mini default without a
new controlled comparison. The internal 12-entry evidence limit still applies.

## Reproducible evaluation

`evaluate_routing.py` accepts `--review-policy always|when_needed` and
`--semantic-contract legacy|claims`. Default CLI values match production. The
`--live` flag remains necessary for paid calls. Historical fixture and reconstructed
repair replays retain their recorded contract and always-review behavior unless
explicitly overridden; reports label both controls and fingerprint the schemas.

Compare review policies first with `legacy`, the same model, fixed cases, and
interleaved/repeated runs. Only after that compare `claims` against `legacy` with
the same review policy. Changing fallback policy, model, corpus and contract in one
comparison cannot identify a schema effect. Both current review-policy arms share
the reduced fallback policy; neither reproduces older fallback-enabled results.

Track complete goal/tool correctness, recommendation coverage, explicit failure,
wrong recommendation, call count, latency, and repair regressions separately.
Do not equate fewer validator issues with improved tool selection. Case-folding
and scripted SDK tests establish deterministic boundary behavior, not LLM semantic
invariance. No paid model evaluation was run for this change.

`scripts/compare_semantic_contracts.py` is the offline promotion gate for two
saved live reports. It rejects different corpora, models, review settings,
repetition counts, and case/trial identities; it also rejects stale summary counts.
Claims must not reduce pass, route-pass, or semantic-pass counts, introduce a
wrong tool or unsafe execution, increase terminal-goal/evidence conflicts, or
increase provider/repair calls. Passing these routing guardrails still says
nothing about execution or biological outputs.

The comparator's `--interleaved` option is an explicit attestation, not a
scheduler. Use it only when the two arms were actually alternated under the same
run conditions. Without that attestation, or with fewer than three repetitions,
the command deliberately reports `promotion_ready=false` even if all numerical
guardrails pass:

```bash
python scripts/compare_semantic_contracts.py legacy.json claims.json
# Only for reports from a genuinely interleaved run:
python scripts/compare_semantic_contracts.py legacy.json claims.json --interleaved
```

## Benchmark limits and next execution milestone

Routing reports explicitly set `execution_evaluated=false` and
`biological_output_evaluated=false`. Expected routing fields are not actual output
validation. User-provided historical A/B counts are not measurements of this change.

`tests/routing_semantic_variants.json` adds eight wording/contrast cases for the
miRNA example: two biological goal families (per-sample versus cohort-wide), not
eight independent tasks. Corpus loading is verified; model accuracy is unmeasured.

Expand independently authored goals as well as paraphrases. Keep paraphrases of
one goal in the same statistical group; they are not independent biological tasks.
Report confidence intervals and paired outcomes without counting repeated wording
as new independent evidence.

An execution benchmark needs fixed input bundles, reference outputs produced by
pinned workflows, and separately recorded execution/biological checks. It should
verify identifiers, orientation, sample coverage and artifact roles, compare numeric
results with justified tolerances, and assert both required and forbidden outputs.
Begin with a small representative set (aggregate regulation, sample-specific
regulation, and mutation-to-clustering), preserve provenance, then broaden it.
Do not call mock outputs or file-existence checks biological validation. This
execution benchmark has not been implemented or run by this routing change.
