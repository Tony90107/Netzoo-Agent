"""Repair authority belongs to one failed hypothesis and one failed fact."""
from copy import deepcopy

from test_semantic_patch_repair import proposal_of, grounded_item
from netzoo_agent_core.contracts.outcomes import SemanticPatch
from netzoo_agent_core.contracts.repair_scope import Issue
from netzoo_agent_core.interpretation.semantic_patch import apply_semantic_patch
from netzoo_agent_core.interpretation.outcome_validation import validate_outcome_hypotheses


def test_other_hypothesis_issues_do_not_license_changes():
    base = proposal_of(grounded_item())
    base.outcome_hypotheses.append(base.outcome_hypotheses[0].model_copy(deep=True))
    patch = SemanticPatch.model_validate({'hypothesis_index': 0, 'outcome': {
        'granularity': 'sample_specific', 'input_artifacts': ['expression_matrix']}})
    merged, _ = apply_semantic_patch(base, patch, validation_issues=(
        Issue('hypothesis[0].conflicting_evidence:granularity=sample_specific', {'granularity'}),
        Issue('hypothesis[1].missing_current_input:expression_matrix', {'input_artifacts'}),
    ))
    assert merged.outcome_hypotheses[0].outcome.input_artifacts == ['mutation_matrix']
    assert merged.outcome_hypotheses[1] == base.outcome_hypotheses[1]
    assert merged.outcome_hypotheses[0].outcome.granularity == 'sample_specific'


def test_local_repair_cannot_rewrite_request_mode_or_goal():
    base = proposal_of(grounded_item())
    patch = SemanticPatch.model_validate({'request_mode': 'execute', 'semantic_goal': 'Another goal'})
    merged, _ = apply_semantic_patch(base, patch, permitted_fields=frozenset({'granularity'}))
    assert merged.request_mode == base.request_mode
    assert merged.semantic_goal == base.semantic_goal


def test_quote_only_repair_can_replace_failed_quote_without_rewriting_other_support():
    task = 'Which tool groups patients from somatic mutations?'
    item = grounded_item()
    bad = next(e for e in item['evidence'] if e['dimension'] == 'input_artifact')
    bad.update(source='explicit', text_span='not in the user request')
    base = proposal_of(item)
    issues = validate_outcome_hypotheses(task, base.outcome_hypotheses).issues
    assert any('ungrounded_evidence' in issue for issue in issues)
    replacement = {**bad, 'text_span': 'somatic mutations'}
    unrelated = deepcopy(next(e for e in item['evidence'] if e['dimension'] == 'artifact_type'))
    unrelated.update(source='explicit', text_span='invented unrelated quote')
    patch = SemanticPatch.model_validate({
        'outcome': {'artifact_type': 'unknown'},
        'evidence_removals': [{'dimension': 'input_artifact', 'value': 'mutation_matrix'}],
        'evidence_additions': [replacement, unrelated],
    })
    merged, audit = apply_semantic_patch(base, patch, validation_issues=issues, user_task=task)
    assert merged.outcome_hypotheses[0].outcome == base.outcome_hypotheses[0].outcome
    assert validate_outcome_hypotheses(task, merged.outcome_hypotheses).valid
    assert any(row.get('reason') == 'evidence_outside_repair_scope' for row in audit)
    assert bad['text_span'] == base.outcome_hypotheses[0].evidence[1].text_span


def test_failed_quote_repair_still_fails_validation():
    item = grounded_item()
    item['evidence'][1].update(source='explicit', text_span='invented')
    base = proposal_of(item)
    task = 'Which tool groups patients from somatic mutations?'
    issues = validate_outcome_hypotheses(task, base.outcome_hypotheses).issues
    patch = SemanticPatch.model_validate({'evidence_removals': [{'dimension': 'input_artifact', 'value': 'mutation_matrix'}]})
    merged, _ = apply_semantic_patch(base, patch, validation_issues=issues, user_task=task)
    result = validate_outcome_hypotheses(task, merged.outcome_hypotheses)
    assert not result.valid
    assert any('ungrounded_evidence' in issue for issue in result.issues)


def test_production_patch_repairs_quote_without_changing_the_goal():
    from test_semantic_claims import legacy_context, legacy_payload, run, TASK

    first = legacy_payload()
    evidence = first['outcome_hypotheses'][0]['evidence']
    bad = next(item for item in evidence if item['dimension'] == 'artifact_type')
    bad['text_span'] = 'invented quote'
    ctx = legacy_context(first, {
        'hypothesis_index': 0, 'request_mode': 'execute', 'semantic_goal': 'Unrelated goal',
        'evidence_removals': [{'dimension': 'artifact_type', 'value': 'regulatory_network'}],
        'evidence_additions': [{**bad, 'text_span': 'regulator network'}],
    })
    result, usage, _, error, _ = run(ctx)
    assert result is not None and error is None
    assert result.request_mode == 'guidance'
    assert result.semantic_goal == first['semantic_goal']
    assert validate_outcome_hypotheses(TASK, result.outcome_hypotheses).valid
    assert [c.role for c in usage.calls] == ['semantic_interpreter', 'semantic_reviewer']
