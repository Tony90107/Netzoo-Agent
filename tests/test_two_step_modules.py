"""Log 327: "patient-specific networks ... then the gene modules inside each patient's network".

The modules reading keeps the per-patient scale the request states, which the
ontology does not give communities. Log 294 kept such a reading only when it
was the only one; beside the network reading it was repaired into a network
and dropped, so the modules half vanished. Kept now when the request names it
apart, set aside from matching, and answered as the gap it is.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "docs" / "research-log" / "two-step-modules-2026-10-03"))

from netzoo_agent_core.contracts.outcomes import OutcomeHypothesis  # noqa: E402
from netzoo_agent_core.interpretation.outcome_validation import (  # noqa: E402
    separately_stated_gaps, validate_outcome_hypotheses,
)
from netzoo_agent_core.routing.reading_selection import matchable_readings  # noqa: E402

TASK = ("I want patient-specific networks for my 30 patients and then the gene modules inside each patient's "
        "network. Which tool finds those per-patient modules? Advice only.")


def _reading(artifact, quote, granularity="sample_specific", source="explicit"):
    evidence = [{"dimension": "artifact_type", "value": artifact, "source": source, "text_span": quote,
                 "rationale": "Stated."},
                {"dimension": "granularity", "value": granularity, "source": "explicit",
                 "text_span": "per-patient modules", "rationale": "Stated."},
                {"dimension": "operation", "value": "infer", "source": "explicit",
                 "text_span": "Which tool finds those per-patient modules?", "rationale": "Stated."},
                {"dimension": "target_type" if artifact == "regulatory_network" else "entity_type",
                 "value": "gene", "source": "explicit", "text_span": "gene modules", "rationale": "Stated."}]
    entities = ["gene", "sample"] if artifact == "regulatory_network" else ["gene"]
    return OutcomeHypothesis.model_validate({"outcome": {
        "operation": "infer", "artifact_type": artifact, "granularity": granularity, "entity_types": entities,
        "regulator_types": ["unknown"] if artifact == "regulatory_network" else [],
        "target_types": ["gene"] if artifact == "regulatory_network" else []},
        "confidence": 0.9, "evidence": evidence})


NETWORKS = _reading("regulatory_network", "patient-specific networks for my 30 patients")
MODULES = _reading("community_assignment", "the gene modules inside each patient's network")


def test_a_modules_reading_named_apart_is_a_stated_gap_not_an_error():
    assert separately_stated_gaps(TASK, [NETWORKS, MODULES]) == [1]
    issues = validate_outcome_hypotheses(TASK, [NETWORKS.model_copy(deep=True), MODULES.model_copy(deep=True)],
                                         "guidance").issues
    assert not any(issue.startswith("hypothesis[1].") for issue in issues)


def test_the_gap_is_set_aside_from_matching_only():
    assert matchable_readings(TASK, [NETWORKS, MODULES]) == [NETWORKS]


def test_a_reading_reusing_another_readings_quote_is_not_named_apart():
    reused = _reading("community_assignment", "patient-specific networks for my 30 patients")
    unquoted = _reading("community_assignment", None, source="inferred")
    for extra in (reused, unquoted):
        assert separately_stated_gaps(TASK, [NETWORKS, extra]) == []
        assert matchable_readings(TASK, [NETWORKS, extra]) == [NETWORKS, extra]


def test_recorded_pf_trials_keep_both_halves_and_answer_the_modules_gap():
    import replay_mg

    fixtures = json.loads((ROOT / "docs" / "research-log" / "two-step-modules-2026-10-03"
                           / "pf_recorded_calls.json").read_text())
    for number in (0, 2):  # trials 1 and 3 need no sibling call under MG
        decision = replay_mg.route(fixtures[number])
        assert [h.outcome.artifact_type for h in decision.outcome_hypotheses] == [
            "regulatory_network", "community_assignment"]
        assert decision.hypothesis_actions == ["run_lioness_panda", "run_lioness_puma"]
        kind, text, card = replay_mg.answer(fixtures[number]["prompt"], decision)
        assert kind == "hypothesis_routes"
        assert "LIONESS-PANDA" in text and "CONDOR finds them in one network at a time" in text
        assert "run it on each sample's network separately" in card.replace("\n      ", " ")
