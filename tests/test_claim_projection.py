"""Projection parity is a harness invariant, not a model accuracy score."""
from copy import deepcopy
import pytest

from test_semantic_claims import TASK, claim, context, payload, run
from netzoo_agent_core.contracts.semantic_claims import SemanticClaims
from netzoo_agent_core.contracts.outcomes import SemanticInterpretation
from netzoo_agent_core.routing.outcome_matching import match_semantic_request


def test_checked_projection_preserves_values_sources_and_known_route():
    from netzoo_agent_core.interpretation.claim_projection import project_claims

    claims = SemanticClaims.model_validate(payload())
    before = claims.model_dump()
    projected = project_claims(TASK, claims)
    assert projected.validation.valid
    assert claims.model_dump() == before
    outcome = projected.interpretation.outcome_hypotheses[0].outcome
    assert outcome.granularity == 'sample_specific'
    assert outcome.regulator_types == ['mirna']
    match = match_semantic_request(TASK, projected.interpretation.outcome_hypotheses, request_mode='guidance')
    assert match.matched_actions == ['run_lioness_puma']
    rows = {row['field']: row for row in projected.facts}
    assert rows['operation']['support_status'] == 'inferred'
    assert rows['granularity']['support_status'] == 'quote_grounded'
    assert rows['granularity']['claim_path'] == 'outcome_hypotheses.0.outcome.granularity'


def test_fabricated_quote_is_not_a_verified_fact_or_an_accepted_projection():
    from netzoo_agent_core.interpretation.claim_projection import project_claims

    data = payload()
    data['outcome_hypotheses'][0]['outcome']['artifact_type'] = claim('regulatory_network', 'fabricated quote')
    result = project_claims(TASK, SemanticClaims.model_validate(data))
    assert not result.validation.valid
    assert any(d['category'] == 'invalid_reference' for d in result.validation.diagnostics)
    row = next(r for r in result.facts if r['field'] == 'artifact_type')
    assert row['support_status'] == 'quote_unverified'


def test_projection_list_order_and_duplicates_do_not_change_outcome_or_route():
    from netzoo_agent_core.interpretation.claim_projection import project_claims

    data = payload()
    data['outcome_hypotheses'][0]['outcome']['entity_types'] = [claim('mirna'), claim('gene'), claim('mirna')]
    reordered = deepcopy(data)
    items = reordered['outcome_hypotheses'][0]['outcome']['entity_types']
    reordered['outcome_hypotheses'][0]['outcome']['entity_types'] = items[1:] + items[:1]
    left = project_claims(TASK, SemanticClaims.model_validate(data))
    right = project_claims(TASK, SemanticClaims.model_validate(reordered))
    assert left.interpretation == right.interpretation
    assert left.interpretation.outcome_hypotheses[0].outcome.entity_types == ['gene', 'mirna']
    # Every original source remains traceable even when equal output values collapse.
    assert len([r for r in left.facts if r['field'] == 'entity_types']) == 3


def test_claim_runtime_records_projection_and_still_rejects_failed_repair():
    data = payload()
    data['outcome_hypotheses'][0]['outcome']['artifact_type'] = claim('regulatory_network', 'fabricated quote')
    ctx = context(data, {'hypothesis_index': 0, 'outcome': {'artifact_type': claim('regulatory_network', 'another fabrication')}})
    result, _, _, error, _ = run(ctx)
    assert result is None and error is not None
    events = [v for k, v in ctx.recorder.events if k == 'routing.semantic_claims_projected']
    assert len(events) == 2
    assert all(not event['valid'] for event in events)
    assert not any(k == 'routing.semantic_interpretation_accepted' for k, _ in ctx.recorder.events)


@pytest.mark.parametrize('granularity,quote,actions', [
    ('sample_specific', 'sample specific', ['run_lioness_puma']),
    ('aggregate', 'aggregate', ['run_puma']),
    ('sample_specific', 'fabricated quote', []),
])
def test_equivalent_legacy_and_claim_contract_have_same_validation_and_selection(granularity, quote, actions):
    from netzoo_agent_core.interpretation.claim_projection import project_claims
    from netzoo_agent_core.interpretation.outcome_validation import validate_outcome_hypotheses

    task = TASK.replace('sample specific', 'aggregate') if granularity == 'aggregate' else TASK
    legacy = SemanticInterpretation.model_validate({
        'request_mode': 'guidance', 'semantic_goal': 'Individual miRNA regulatory networks',
        'outcome_hypotheses': [{'confidence': 0.9, 'outcome': {
            'operation': 'infer', 'artifact_type': 'regulatory_network',
            'granularity': granularity, 'regulator_types': ['mirna']},
            'evidence': [
                {'dimension': dimension, 'value': value, 'source': 'explicit' if quote else 'inferred',
                 'text_span': quote, 'rationale': 'Fixture support.'}
                for dimension, value, quote in [
                    ('operation', 'infer', None),
                    ('artifact_type', 'regulatory_network', 'regulator network'),
                    ('granularity', granularity, quote),
                    ('regulator_type', 'mirna', 'mi-RNA')]
            ]}]
    })
    data = payload()
    data['outcome_hypotheses'][0]['outcome']['granularity'] = claim(granularity, quote)
    projected = project_claims(task, SemanticClaims.model_validate(data))
    assert validate_outcome_hypotheses(task, legacy.outcome_hypotheses).valid == projected.validation.valid == bool(actions)
    assert legacy.outcome_hypotheses[0].outcome == projected.interpretation.outcome_hypotheses[0].outcome
    if actions:
        for interpretation in (legacy, projected.interpretation):
            assert match_semantic_request(task, interpretation.outcome_hypotheses, request_mode='guidance').matched_actions == actions


def test_quote_alignment_does_not_override_negated_input_validation():
    from netzoo_agent_core.interpretation.claim_projection import project_claims

    data = payload()
    data['outcome_hypotheses'][0]['outcome']['input_artifacts'] = [claim('mutation_matrix', 'mutation matrix')]
    projected = project_claims(TASK + ' I do not have a mutation matrix.', SemanticClaims.model_validate(data))
    assert not projected.validation.valid
    assert any('noncurrent_input' in issue for issue in projected.validation.issues)
    assert next(r for r in projected.facts if r['field'] == 'input_artifacts')['support_status'] == 'quote_grounded'
