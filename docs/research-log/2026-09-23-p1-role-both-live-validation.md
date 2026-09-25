# P1 coordinated regulator live validation

Run date: 2026-09-23

## Pre-run criteria

This targeted round covers only `role-both-agg-en` and `role-both-ss-en` from
`tests/routing_semantic_families.json`, using the recorded prompts unchanged.
Run both semantic contracts (`legacy`, `claims`) at repeat=3 with the existing
gpt-4o-mini trace harness and `review_policy=when_needed`.

Expected routes:

- `role-both-agg-en`: exact `run_puma` / PUMA.
- `role-both-ss-en`: exact `run_lioness_puma` / LIONESS-PUMA.

Pass criteria, evaluated separately for each case and contract:

1. At least 2 of 3 trials have `route_passed=true`, `semantic_passed=true`, and
   the expected exact action above.
2. The combined round has zero wrong exact or fallback recommendations and
   zero unsafe executions. Advice-only trials must not execute a workflow.
3. Record each trial's outcome artifact and regulator roles, plus whether a
   reviewer call occurred and whether its patch validated, so routing success
   can be distinguished from a silent fallback.

No code changes are planned between recording these criteria and running the
round. Trace files are written beside this record for offline inspection.

## Follow-up round criteria after evidence-grounding fix

Run date: 2026-09-23

This is a new, bounded round after the offline evidence-restoration regression
fix. It uses the same two unchanged cases (`role-both-agg-en` and
`role-both-ss-en`), both contracts (`legacy`, `claims`), repeat=3,
gpt-4o-mini, and `review_policy=when_needed`. No other prompt IDs or models are
in scope. Results will be written to
`live-semantic-trace-2026-09-23-p1-evidence-fix-legacy.json` and
`live-semantic-trace-2026-09-23-p1-evidence-fix-claims.json`.

Pass criteria remain per case and contract: at least 2/3 trials must have
`route_passed=true`, `semantic_passed=true`, and the expected exact action
(`run_puma` for aggregate; `run_lioness_puma` for sample-specific). Across the
round there must be zero wrong exact or fallback recommendations and zero
unsafe executions. In any reviewer-corrected trial, inspect that the corrected
artifact has supporting artifact-type evidence and both regulator-role claims
have grounded evidence spans. Record reviewer invocation, patch validation,
outcome artifact, and roles for every trial.

The implementation and criteria are fixed before starting these four targeted
live batches; no code changes will be made between recording this section and
the API calls.

## Evidence-grounding follow-up results

The follow-up evidence-grounding round completed with the original criteria,
but did not pass the per-case threshold:

- `legacy`: aggregate 1/3, sample-specific 2/3 (3/6 total; 0 wrong exact,
  0 wrong fallback, 0 unsafe executions).
- `claims`: aggregate 3/3, sample-specific 0/3 (3/6 total; 0 wrong exact,
  0 wrong fallback, 0 unsafe executions; 9 unmatched evidence entries).

Inspection identified two residual defects. In legacy aggregate failures, a
review patch sometimes treated the requested output `regulatory_network` as a
provided input artifact, or retained entity evidence conflicting with the
corrected role set. In claims sample-specific failures, the corrected role
evidence was grounded, but the model's unmatched explicit `entity_type=tf`
quote (`TF regulation`) remained attached and failed validation.

## Bounded follow-up criteria after input and entity evidence fix

Run date: 2026-09-23

Run only `role-both-agg-en` and `role-both-ss-en`, both contracts (`legacy`,
`claims`), repeat=3, gpt-4o-mini, and `review_policy=when_needed`. Outputs will
be written to `live-semantic-trace-2026-09-23-p1-restoration-fix-legacy.json`
and `live-semantic-trace-2026-09-23-p1-restoration-fix-claims.json`.

Pass criteria remain per case and contract: at least 2/3 trials must have
`route_passed=true`, `semantic_passed=true`, and the exact expected action
(`run_puma` for aggregate; `run_lioness_puma` for sample-specific). Across the
round, require zero wrong exact or fallback recommendations and zero unsafe
executions. For both cases, inspect that no unwitnessed artifact is retained in
`input_artifacts`; for claims sample-specific trials, confirm any unmatched
role-derived `entity_type` quote is removed while the explicit regulator and
target claims remain grounded. Record trial outcomes and review/patch status.

The implementation and criteria are fixed before these four targeted live
batches; no code changes will be made between this section and the API calls.

## Role and input restoration follow-up results

The role/entity-evidence fix cleared the claims-mode failures: aggregate 3/3
and sample-specific 3/3, with zero wrong exact/fallback recommendations and
zero unsafe executions. Legacy reached sample-specific 3/3 but aggregate only
1/3. Its remaining rejected trials retained reviewer evidence for values that
the field-scoped patch did not put into the merged outcome, raising
`conflicting_evidence`.

## Final targeted criteria after evidence-patch filtering

Run date: 2026-09-23

Run only the same two cases (`role-both-agg-en`, `role-both-ss-en`), both
contracts (`legacy`, `claims`), repeat=3, gpt-4o-mini, and
`review_policy=when_needed`. Outputs will be written to
`live-semantic-trace-2026-09-23-p1-patch-filter-legacy.json` and
`live-semantic-trace-2026-09-23-p1-patch-filter-claims.json`.

Use the original per-case pass threshold: at least 2/3 trials per case and
contract must have `route_passed=true`, `semantic_passed=true`, and the exact
expected action (`run_puma` for aggregate, `run_lioness_puma` for
sample-specific). Require zero wrong exact or fallback recommendations and
zero unsafe executions. Inspect `evidence_additions_dropped` to confirm every
dropped patch claim names a value absent from the merged outcome, and record
review invocation/validation and all final inputs, roles, and granularity.

No code changes will be made between this criteria section and the four live
batches.

## Patch-filter round results

Claims again passed both cases 3/3 (6/6 total), with no wrong exact or fallback
recommendations and no unsafe executions. Legacy aggregate passed 3/3, but its
sample-specific case passed 0/3: all three accepted outcomes carried a stray
`unknown` entity alongside the explicitly witnessed TF, miRNA, and gene roles,
which kept matching at fallback or ambiguity. The new deterministic rule
removes that placeholder only when the witnessed roles and all known entities
are exactly the same set.

## Final targeted criteria after role-entity normalization

Run date: 2026-09-23

Run only `role-both-agg-en` and `role-both-ss-en`, both contracts (`legacy`,
`claims`), repeat=3, gpt-4o-mini, and `review_policy=when_needed`. Outputs will
be written to `live-semantic-trace-2026-09-23-p1-role-normalization-legacy.json`
and `live-semantic-trace-2026-09-23-p1-role-normalization-claims.json`.

Pass criteria are unchanged: at least 2/3 per case and contract must have a
semantic pass, an exact route, and the expected action (`run_puma` for
aggregate; `run_lioness_puma` for sample-specific). Require zero wrong exact or
fallback recommendations and zero unsafe executions. Inspect any removed
`unknown` entity against the complete explicit role witness, and record final
outcome fields and reviewer/patch status.

No code changes will be made between this section and the four live batches.

## Follow-up fixes and saved-trace replay

After the bounded live round, the remaining legacy failures were reproduced
from the saved provider responses. The common cause was that role restoration
applied a coordinated TF/miRNA-to-gene statement one regulator at a time. Each
partial update violated the outcome contract because the other declared role
was not yet present in `entity_types`; this also prevented stale TF evidence
from being replaced with the exact coordinated quote. Restoration now applies
all roles from the witnessed statement atomically and repairs evidence from the
same quote.

The schema failure came from a patch that marked `regulatory_network` as
explicit but supplied no quote. When current explicit regulator-to-target
roles support that artifact under the ontology, the patch evidence is now
downgraded to inferred with an audit note. Strict outcome validation still
checks the complete result; no quote is synthesized.

Replaying the six saved legacy responses through the current patch/restoration,
validation, and deterministic registry-matching stages now yields the expected
exact route in all six cases: PUMA for aggregate and LIONESS-PUMA for
sample-specific. The six saved claims responses also replay to their expected
exact routes. These are offline replays of fixed provider outputs, not a full
CLI rerun or a new live-model stability round. The original prompts were
advice-only, and no workflow executed.

Static checks passed: Ruff, Python compilation for the edited modules, and
`git diff --check`.

## Post-fix bounded live verification criteria

Run date: 2026-09-23

Repeat only `role-both-agg-en` and `role-both-ss-en`, both semantic contracts
(`legacy`, `claims`), repeat=3, `openai/gpt-4o-mini`,
`review_policy=when_needed`.
Expected actions are PUMA for aggregate and LIONESS-PUMA for sample-specific.
Pass requires at least 2/3 semantically valid exact routes per prompt and
contract, with zero wrong exact/fallback recommendations and zero unsafe
executions. Both prompts are advice-only. Save the two contract traces as
`live-semantic-trace-2026-09-23-p1-postfix-legacy.json` and
`live-semantic-trace-2026-09-23-p1-postfix-claims.json`.

The scope and criteria are fixed before these provider calls; no source changes
will be made during the bounded verification.

The live rerun could not start because `OPENROUTER_API_KEY` is not present in
the current shell. The evaluator exits during configuration, before creating a
provider or making a request; no new live traces or live results were produced.
The saved-response replays above remain the available post-fix evidence. A
fresh live gate requires running the same bounded command in an environment
where that credential is configured.

## Final bounded-round result

The latest live round passes the claims contract: both prompts were exact and
semantically valid in 3/3 trials each (6/6 total), with zero wrong exact or
fallback recommendations and zero unsafe executions.

The legacy contract remains below the preregistered per-case threshold:

- Aggregate: 1/3 exact and semantically valid. One review failed schema
  validation because an explicit evidence addition omitted `text_span`; one
  validated review remained ambiguous with `entity_types=[]`; one trial routed
  exactly to PUMA.
- Sample-specific: 2/3 exact and semantically valid; the remaining trial was a
  fallback after the reviewer repeated an ungrounded TF quote.
- Across legacy trials: 0 wrong exact recommendations, 0 wrong fallback
  recommendations, 0 unsafe executions.

All prompts were advice-only; the trace metadata has
`execution_evaluated=false`. The overall cross-contract live gate therefore
does not pass, even though claims is 6/6. The trace files preserve every trial
and reviewer patch for a focused legacy follow-up.

## Unknown-match round results

Claims again passed both cases 3/3. Legacy aggregate passed 2/3 and
sample-specific passed 1/3. The sample trial with a `partial_evidence` fallback
had fully grounded roles and only the extra `unknown` entity; inspection showed
`_has_unknown` had been corrected, but `_matches` still compared that literal
against supported entities. The next correction applies the same strict role
coverage condition to that subset comparison.

## Final targeted criteria after entity-set comparison fix

Run date: 2026-09-23

Run only `role-both-agg-en` and `role-both-ss-en`, both contracts (`legacy`,
`claims`), repeat=3, gpt-4o-mini, and `review_policy=when_needed`. Outputs will
be written to `live-semantic-trace-2026-09-23-p1-unknown-entity-legacy.json`
and `live-semantic-trace-2026-09-23-p1-unknown-entity-claims.json`.

Pass criteria remain: at least 2/3 semantically valid exact routes per case and
contract with the expected action (`run_puma` aggregate;
`run_lioness_puma` sample-specific), zero wrong exact/fallback recommendations,
and zero unsafe executions. Verify the matcher drops `unknown` from entity
comparison only when the outcome is `regulatory_network` and its known entity
set equals its non-unknown regulator/target role union.

No code changes will be made between this section and the four live batches.

## Role-normalization round results

Claims passed both cases 3/3 again (6/6 total, no wrong or unsafe routes).
Legacy passed aggregate 3/3 but sample-specific 0/3. The returned sample
outcomes still carried `entity_types=["gene", "tf", "unknown", "mirna"]`,
despite supported roles exactly enumerating TF, miRNA, and gene. The attempted
interpretation-level normalization did not appear in the live restoration
records, so the next bounded change treats that exact role-complete placeholder
as non-constraining inside capability compatibility.

## Final targeted criteria after matcher placeholder handling

Run date: 2026-09-23

Run only `role-both-agg-en` and `role-both-ss-en`, both contracts (`legacy`,
`claims`), repeat=3, gpt-4o-mini, and `review_policy=when_needed`. Outputs will
be written to `live-semantic-trace-2026-09-23-p1-unknown-match-legacy.json` and
`live-semantic-trace-2026-09-23-p1-unknown-match-claims.json`.

Pass criteria remain at least 2/3 exact, semantically valid trials per case and
contract with the expected action (`run_puma` aggregate; `run_lioness_puma`
sample-specific), zero wrong exact/fallback recommendations, and zero unsafe
executions. Verify that matcher handling is limited to regulatory outcomes
whose known entity set exactly equals the non-unknown regulator/target role
union; preserve the raw outcome and review status in the trace.

No code changes will be made between this section and the four live batches.
