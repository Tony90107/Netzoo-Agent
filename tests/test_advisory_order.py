"""Log 218: the advisory stages' order and handoff, pinned where they are written down.

After intent, up to three stages add advice to a decision: the condition
recommender (quoted study facts), folder inspection (file contents) and input
preflight. Their order and the rules between them -- the first recommendation
stands, the folder sees the whole tie, one source per recommendation -- lived
only in the code; they are now stated at the call site in `router_invocation`
and these tests make any change to them deliberate.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from workflow_registry import SELECTION_AXES  # noqa: E402
import netzoo_agent_core.graph.router_invocation as router_invocation  # noqa: E402
from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    AdvisoryCondition,
    AdvisoryRecommendation,
    SelectionConditionClaims,
)
from netzoo_agent_core.graph.condition_recommender import condition_options, recommend_from_claims  # noqa: E402
from netzoo_agent_core.graph.input_inspection import INSPECTED_AXIS, advise_from_inspected_inputs  # noqa: E402
from test_ambiguous_guidance_is_scored import row  # noqa: E402
from test_input_inspection import PANDA_SET, _decision, _folder, _task  # noqa: E402

FACT = AdvisoryRecommendation(
    action="run_lioness_puma",
    conditions=[AdvisoryCondition(axis="per_sample_quantity", value="wiring", text_span="per-patient TF networks")],
)


def test_the_stages_run_in_the_documented_order(monkeypatch):
    calls = []
    for name, label in (("invoke_hypothesis_matcher", "hypotheses"),
                        ("invoke_condition_recommender", "conditions"),
                        ("invoke_input_inspection", "folder"),
                        ("apply_input_preflight_intent", "preflight")):
        original = getattr(router_invocation, name)

        def recorded(*args, _original=original, _label=label, **kwargs):
            calls.append(_label)
            return _original(*args, **kwargs)

        monkeypatch.setattr(router_invocation, name, recorded)

    result, _ = row()

    # Log 257: a goal review that finds one goal yields to the method stage.
    assert result["call_roles"][-1] == "selection_conditions"
    assert calls == ["hypotheses", "conditions", "folder", "preflight"]


def test_a_stated_fact_recommendation_is_not_replaced_by_the_folder(tmp_path):
    written = _folder(tmp_path, PANDA_SET)

    # The same folder alone recommends LIONESS-PANDA (no miRNA list) ...
    alone = advise_from_inspected_inputs(_task(written), _decision(), root=tmp_path)
    assert alone.advisory_recommendation.action == "run_lioness_panda"
    # ... but it does not override a recommendation from quoted facts.
    decision = _decision(advisory_recommendation=FACT)
    assert advise_from_inspected_inputs(_task(written), decision, root=tmp_path) is decision


def test_the_folder_sees_the_whole_tie(tmp_path):
    """Log 200's known limitation: facts that narrow a three-way tie to the two
    LIONESS variants are not passed on, so the folder, seeing GIRAFFE too,
    cannot compare inputs and recommends nothing."""
    written = _folder(tmp_path, PANDA_SET)
    decision = _decision(hypothesis_actions=["run_lioness_panda", "run_lioness_puma", "run_giraffe"])

    advised = advise_from_inspected_inputs(_task(written), decision, root=tmp_path)

    assert advised.advisory_recommendation is None
    assert advised.inspected_directories == [written]


def test_each_recommendation_comes_from_one_source(tmp_path):
    candidates = ["run_lioness_coexpression", "run_cobra"]
    task = "Adjust the co-expression network for the sequencing batch covariate."
    claims = SelectionConditionClaims.model_validate(
        {"claims": [{"condition": "covariates:yes", "text_span": "sequencing batch covariate"}]}
    )
    from_facts, _ = recommend_from_claims(task, claims, condition_options(candidates), candidates)
    written = _folder(tmp_path, PANDA_SET)
    from_folder = advise_from_inspected_inputs(_task(written), _decision(), root=tmp_path).advisory_recommendation

    assert from_facts.action == "run_cobra"
    assert {item.axis for item in from_facts.conditions} <= set(SELECTION_AXES)
    assert {item.axis for item in from_folder.conditions} == {INSPECTED_AXIS}
