"""Log 320: what a request needs beyond the registry, and what to expect before a run.

TEST_PROMPTS (2026-10-03) Tests 4, 7, 8 and 9 asked for single-cell networks,
a chromatin-filtered prior, a comparison of two networks' modules and a
convex guarantee; the replies answered with registered workflows alone.
Tests 2, 3 and 10 were not told what CONDOR's input needs or what LIONESS
costs. These pin the notes, their triggers and where they appear.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.interpretation.advisory_answers import _without_global_optimum_claims  # noqa: E402
from netzoo_agent_core.interpretation.outside_steps import outside_steps, with_outside_steps  # noqa: E402
from netzoo_agent_core.interpretation.practical_notes import practical_notes  # noqa: E402
from test_reply_cards import POLICY, decision, reading, respond_and_card  # noqa: E402

PROMPTS = json.loads((ROOT / "docs" / "research-log" / "test10-2026-10-03" / "prompts.json").read_text())
TIE = ["run_panda", "run_lioness_panda", "run_otter", "run_giraffe"]


def _tie(actions=TIE, **fields):
    return decision([reading("regulatory_network", ["expression_matrix"], ["tf"], granularity="unknown")],
                    capability_match_status="ambiguous", hypothesis_actions=list(actions), **fields)


def _keys(made: TaskDecision, task: str) -> list[str]:
    return [step.key for step in outside_steps(made, task)]


def test_each_outside_step_fires_on_its_own_test_prompt_only():
    condor = decision([reading("community_assignment", ["regulatory_network"], entities=["tf", "gene"])],
                      capability_match_status="exact", matched_actions=["run_condor"])
    expected = {"test4": ["single_cell"], "test7": ["chromatin_prior"], "test9": ["convex_guarantee"]}
    for key, prompt in PROMPTS.items():
        made = condor if key in {"test3", "test8"} else _tie()
        assert _keys(made, prompt) == (["differential_modules"] if key == "test8" else expected.get(key, [])), key


def test_a_step_tied_to_workflows_needs_one_of_them_in_the_reply():
    assert _keys(_tie(), PROMPTS["test8"]) == []
    assert _keys(_tie(["run_lioness_coexpression", "run_bonobo"]), PROMPTS["test9"]) == []


def test_chromatin_alone_does_not_bring_the_prior_note():
    assert _keys(_tie(), "We have ATAC-seq and RNA-seq from the same tumours; which multi-omic network fits?") == []


def test_the_note_goes_above_the_closing_line():
    text = "Some guidance.\n\nNo files were inspected and no analysis ran."
    updated = with_outside_steps(text, _tie(), PROMPTS["test4"])
    assert updated.index("**Single-cell data.**") < updated.index("No files were inspected")
    assert "SCORPION" in updated and "pseudo-bulk" in updated


def test_the_card_lists_an_outside_step_as_not_available_here():
    made = _tie(clarification_question="Which modeling assumption best matches your experiment?")
    text, _, card = respond_and_card(PROMPTS["test9"], made)
    assert "**On a convex, globally optimal guarantee.**" in text
    row = next(item for item in card.unavailable if item.key == "outside-convex_guarantee")
    assert not row.available and "non-convex" in row.reason


def test_lioness_cost_quotes_the_users_own_count():
    note = practical_notes("run_lioness_panda", PROMPTS["test10"])[0]
    assert "N samples take N+1 PANDA runs" in note and "(for your 90 patients, 91 PANDA runs)" in note
    assert "{runs}" not in practical_notes("run_lioness_puma", "Each patient's network, please.")[0]
    assert practical_notes("run_lioness_panda", PROMPTS["test10"], short=True) == [
        "Cost: N samples take N+1 PANDA runs (for your 90 patients, 91 PANDA runs)."]


def test_condor_is_told_to_threshold_a_panda_network_first():
    made = decision([reading("community_assignment", ["regulatory_network"], entities=["tf", "gene"])],
                    capability_match_status="exact", matched_actions=["run_condor"],
                    recommended_actions=["run_condor"])
    text, _, card = respond_and_card(PROMPTS["test3"], made)
    assert "pandaToCondorObject" in text and "core score" in text
    assert any(point.startswith("Before running: threshold a PANDA or LIONESS network") for point in card.points)
    assert len(card.points) <= 6


def test_a_prepared_input_gap_does_not_say_no_workflow_builds_the_network():
    # The decision Test 7 got live (r1), with operation "prepare".
    recorded = json.loads((ROOT / "docs" / "research-log" / "test10-2026-10-03" / "r1-decisions.json").read_text())
    made = TaskDecision.model_validate(recorded["test7"]["decision"])
    assert made.requested_outcome.operation == "prepare"
    text, _, card = respond_and_card(PROMPTS["test7"], made)
    assert "do not prepare" not in text and "as an input step" in text
    assert card.headline.startswith("No registered workflow prepares") and "cannot produce" not in card.headline
    assert "**Building the prior from chromatin accessibility.**" in text


def test_a_shared_mechanism_sentence_reads_as_one_sentence():
    made = decision([reading("regulatory_network", ["expression_matrix"], granularity="sample_specific")],
                    capability_match_status="ambiguous", hypothesis_actions=["run_lioness_panda", "run_lioness_puma"])
    from netzoo_agent_core.interpretation.tie_guidance import render_tie_guidance

    text = render_tie_guidance(made, POLICY, family_label=lambda spec: spec.workflow)
    assert "; the participating layers depend" not in text
    assert ("All of them derive each sample network from all-sample and leave-one-out networks, and "
            "iteratively exchange information across biological evidence networks.") in text


def test_a_rationale_never_claims_a_global_optimum():
    rationale = ("OTTER uses an explicit objective. This method guarantees a globally optimal solution, "
                 "which fits a non-heuristic preference. It balances the priors.")
    assert _without_global_optimum_claims(rationale) == "OTTER uses an explicit objective. It balances the priors."
