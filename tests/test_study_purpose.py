"""Log 342: the comparison design and conclusion a request states, and the replies they add to.

Log 341's minimal pairs fixed the data and changed only the purpose sentence;
the replies did not change with it. The decisions below are the recorded
ones from that round (`docs/research-log/minimal-pairs-2026-10-04`), so only
the reply layer is under test.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import get_args

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from langchain_core.messages import AIMessage  # noqa: E402
from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.graph import router_invocation  # noqa: E402
from netzoo_agent_core.interpretation.practical_notes import practical_notes  # noqa: E402
from netzoo_agent_core.interpretation.study_purpose_notes import with_study_purpose_reply  # noqa: E402
from netzoo_agent_core.routing.study_purpose import Claim, study_purpose, timepoint_count  # noqa: E402
from test_reply_cards import respond_and_card  # noqa: E402
from workflow_registry import CLAIM_SUPPORT, OUTPUT_CAPABILITIES, UNSUPPORTED_CLAIMS  # noqa: E402

MINIMAL_PAIRS = ROOT / "docs" / "research-log" / "minimal-pairs-2026-10-04"
PROMPTS = json.loads((MINIMAL_PAIRS / "prompts.json").read_text())
RECORDED = json.loads((MINIMAL_PAIRS / "out" / "s1-decisions.json").read_text())


def _reply(key):
    item = RECORDED[key]
    return respond_and_card(item["prompt"], TaskDecision.model_validate(item["decision"]))


# -- witnesses -----------------------------------------------------------------

@pytest.mark.parametrize("key, design, claim", [
    ("A0", "paired", None), ("A1", "paired", "group_difference"), ("A2", "paired", "individual_change"),
    ("A3", "paired", "regulator_change"), ("A4", "paired", "causal"), ("A5", "paired", None),
    ("B1", "groups", "group_difference"), ("B2", "groups", None), ("B3", "groups", "prediction"),
])
def test_the_log_340_prompts_get_their_pre_written_labels(key, design, claim):
    purpose = study_purpose(PROMPTS[key])
    assert (purpose.design, purpose.claim) == (design, claim)


def test_the_users_own_example_stays_open():
    # "Whether the patients' gene regulation changes" may mean the cohort, each
    # patient or the regulators; it is asked, never assumed.
    assert study_purpose(PROMPTS["A5"]).claims == ()


@pytest.mark.parametrize("task", [
    "This is not causal; we only want an association network.",
    "We are not trying to predict outcomes; we want one network for the cohort.",
    # A real session (Chinese negation before an English witness).
    "這是無向的統計關聯網路，不是 causal 或 TF-gene regulatory network。",
    "Our prior includes predicted targets of miRNAs from TargetScan. Build a network.",
    "Explain the difference between PANDA and PUMA.",
    "Which patients belong to which subtype?",
])
def test_negated_or_unrelated_words_are_no_witness(task):
    purpose = study_purpose(task)
    assert purpose.claims == () and purpose.design is None


def test_paired_omics_layers_are_not_a_paired_design():
    # A real session: mRNA and miRNA from the same tumors, not before and after.
    task = "We collected mRNA expression and miRNA expression data for 150 paired tumor samples."
    assert study_purpose(task).design is None


def test_time_points_alone_are_not_pairing():
    # Mice are often sacrificed per time point.
    assert study_purpose("We profiled 12 mice at three time points after infection.").design is None


def test_a_negation_only_covers_its_own_clause():
    task = ("We do not want to claim that the knockout causes anything, just describe which TFs "
            "differ between knockout and wild-type.")
    claims = [claim for claim, _ in study_purpose(task).claims]
    assert "causal" not in claims and claims[0] == "regulator_change"


def test_the_quote_is_the_requests_own_sentence():
    purpose = study_purpose(PROMPTS["A4"])
    assert purpose.claim_quote == "We want to show that the treatment itself causes changes in gene regulation."


def test_timepoints_are_read_from_words():
    assert timepoint_count(PROMPTS["A2"]) == 2
    assert timepoint_count("each sampled at three time points") == 3
    assert timepoint_count(PROMPTS["B1"]) is None


# -- registry --------------------------------------------------------------------

def test_every_declared_cell_names_a_workflow_a_claim_and_a_design():
    claims = set(get_args(Claim))
    for (action, claim, design), cell in CLAIM_SUPPORT.items():
        assert action in OUTPUT_CAPABILITIES, action
        assert claim in claims - set(UNSUPPORTED_CLAIMS), claim
        assert design in {"paired", "groups", "*"}, design
        assert cell.level in {"direct", "with_step"} and cell.text


def test_only_the_global_table_states_a_gap():
    assert set(UNSUPPORTED_CLAIMS) == {"causal", "prediction"}
    # v1 declares no multi-omic or community workflow (proposal, section 3.2).
    assert not any(action in {"run_dragon", "run_lioness_dragon", "run_condor", "run_sambar"}
                   for action, _, _ in CLAIM_SUPPORT)


# -- replies (recorded Log 341 decisions) ------------------------------------------

def test_a_cohort_change_question_gets_the_comparison_step_above_the_question():
    text, _, card = _reply("A1-1")
    block = text.split("For your question (", 1)[1]
    assert block.startswith('"We want to know whether the regulatory network changes after treatment across the cohort."')
    assert "- **PANDA**, **PUMA** — Build one network for each time point" in block
    assert "does not use the pairing" in block
    assert text.index("For your question") < text.index("These all fit; to choose")
    assert any(point.startswith("Your question: whether the groups or time points differ") for point in card.points)


def test_two_readings_get_no_purpose_paragraph():
    text, _, _ = _reply("A1-3")
    assert "For your question" not in text


def test_a_per_patient_change_gets_the_per_patient_step_and_the_paired_sample_count():
    text, _, _ = _reply("A2-1")
    assert "(for your 24 patients × 2 samples each = 48 samples, 49 PANDA runs)" in text
    assert "measures how much that individual changed" in text
    assert text.count("not statistically independent") == 1


def test_a_causal_claim_is_answered_first_and_the_tie_no_longer_says_all_fit():
    text, _, card = _reply("A4-1")
    first = text.split("\n\n", 1)[0]
    assert first.startswith('About "We want to show that the treatment itself causes changes in gene regulation.": ')
    assert "cannot separate the treatment's effect from time" in first
    assert "These all fit" not in text
    assert "These fit the result you described, but none can show that one thing causes another" in text
    assert any(row.label == "Show that one thing causes another" for row in card.unavailable)


def test_a_two_group_coexpression_question_names_cobras_group_component():
    text, _, _ = _reply("B1-1")
    assert "- **COBRA** — Put the group label in COBRA's design matrix" in text
    assert "Deciding which gene pairs differ beyond chance is a separate analysis." in text


def test_a_prediction_request_that_failed_validation_gets_the_gap_not_could_not_validate():
    text, kind, card = _reply("B3-1")
    assert kind == "unresolved"
    assert "could not validate" not in text.casefold()
    assert text.startswith('About "We want a model that predicts whether a new patient will respond.": '
                           "No registered workflow builds a model")
    assert text.endswith("No files were inspected and no analysis ran.")
    assert card.headline == "No registered workflow can do this: predict outcomes for new samples."


@pytest.mark.parametrize("key", ["A0-1", "A0-2", "A5-1", "B2-1"])
def test_requests_without_a_stated_conclusion_keep_their_reply(key, monkeypatch):
    text, _, _ = _reply(key)
    from netzoo_agent_core.graph import response
    monkeypatch.setattr(response, "with_study_purpose_reply", lambda result, state, reply: result)
    baseline, _, _ = _reply(key)
    assert text == baseline


def test_other_reply_kinds_are_untouched():
    result = {"messages": [AIMessage(content="Summary.")], "reply_kind": "response_model"}
    state = {"messages": [], "decision": {}}
    assert with_study_purpose_reply(result, state, None) is result


def test_the_paired_count_never_counts_individuals_as_samples_without_a_number_each():
    task = "We followed 15 patients longitudinally; build per-patient networks."
    note = practical_notes("run_lioness_panda", task)[0]
    assert "count samples, not patients: each of your 15 patients gives more than one sample" in note
    unpaired = practical_notes("run_lioness_panda", "We have 40 patients; one network each.")[0]
    assert "(for your 40 patients, 41 PANDA runs)" in unpaired


def test_the_trace_event_reads_the_request_only(monkeypatch):
    events = []
    monkeypatch.setattr(router_invocation, "record_event",
                        lambda context, state, name, node, payload: events.append((name, payload)))
    router_invocation._record_study_purpose(None, {}, PROMPTS["A4"])
    router_invocation._record_study_purpose(None, {}, PROMPTS["B2"].replace("30 from", "some from"))
    assert events[0][0] == "routing.study_purpose_detected"
    assert events[0][1]["design"] == "paired" and events[0][1]["claims"][0]["claim"] == "causal"
    assert len(events) == 2 and events[1][1]["claims"] == []
