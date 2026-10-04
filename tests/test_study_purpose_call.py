"""Log 355: the study-purpose call -- a model proposes, deterministic rules verify.

The provider is a fake; the proposals are shaped like Log 354's recorded ones,
including the failure the verification exists for: a request's goal sentence
quoted for a conclusion it does not state.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from langchain_core.messages import AIMessage  # noqa: E402
from netzoo_agent_core.contracts import LLMUsage, TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.study_purpose import StudyPurposeProposal  # noqa: E402
from netzoo_agent_core.graph.study_purpose_call import invoke_study_purpose  # noqa: E402
from netzoo_agent_core.interpretation.study_purpose_notes import purpose_from_state  # noqa: E402
from netzoo_agent_core.routing.study_purpose_verify import verify_proposal  # noqa: E402
from test_reply_cards import respond_and_card  # noqa: E402

TASK = ("Twenty-two adults each did two weeks on a high-salt and two weeks on a low-salt diet, in random order, "
        "with whole-blood RNA-seq after each; expression only. We want to find the participants whose "
        "co-expression networks shift most between diets.")


def _proposal(design="none", design_span="", claims=()):
    return StudyPurposeProposal(design=design, design_span=design_span,
                                claims=[{"claim": c, "text_span": q} for c, q in claims])


class Adapter:
    def __init__(self, reply):
        self.reply = reply

    def invoke(self, _messages):
        if isinstance(self.reply, BaseException):
            raise self.reply
        return {"parsed": self.reply, "raw": AIMessage(content=""), "parsing_error": None}


class Provider:
    def __init__(self, reply):
        self.reply = reply
        self.options = []

    def with_structured_output(self, schema, **options):
        self.options.append((schema, options))
        return Adapter(self.reply)


def _context(reply):
    events = []
    context = SimpleNamespace(
        study_purpose_llm=Provider(reply), semantic_model_name="offline", router_max_tokens=2000,
        task_token_budget=100000, price_catalog=None,
        recorder=SimpleNamespace(append=lambda run, name, node, data: events.append((name, data))),
    )
    return context, events


# -- verification ----------------------------------------------------------------------

def test_a_design_stated_without_the_usual_words_is_kept_when_its_quote_supports_it():
    purpose, rejected = verify_proposal(TASK, _proposal(
        "paired", "each did two weeks on a high-salt and two weeks on a low-salt diet, in random order",
        [("individual_change", "find the participants whose co-expression networks shift most between diets")]))
    assert purpose.design == "paired" and purpose.claim == "individual_change" and rejected == []


@pytest.mark.parametrize("task, claim, quote, reason", [
    # Log 354: a goal sentence naming TFs was offered as a regulator change.
    ("We want a single combined TF and miRNA regulatory network for maternal blood.", "regulator_change",
     "We want a single combined TF and miRNA regulatory network for maternal blood.", "no_cue"),
    ("We want to predict the target genes of each transcription factor at every time point.", "prediction",
     "predict the target genes of each transcription factor", "negated_or_vetoed"),
    ("We don't want a diagnostic classifier; we just want to know whether the network differs.", "prediction",
     "We don't want a diagnostic classifier", "negated_or_vetoed"),
    ("A donor table gives age, sex and cause of death. We want gene modules.", "causal",
     "cause of death", "negated_or_vetoed"),
    ("We want gene modules.", "causal", "the treatment causes rewiring", "quote_not_in_request"),
])
def test_a_proposed_conclusion_stands_only_on_its_own_quote(task, claim, quote, reason):
    purpose, rejected = verify_proposal(task, _proposal(claims=[(claim, quote)]))
    assert purpose.claims == () and rejected == [{"field": "claim", "value": claim, "reason": reason}]


@pytest.mark.parametrize("design, quote, reason", [
    ("paired", "2 x 150 bp paired-end RNA-seq", "technical"),
    ("paired", "matched expression and 450K methylation arrays on 110 primary neuroblastomas", "two_data_types"),
    ("groups", "85 primary cardiac fibroblast lines, each derived from a different adult donor", "no_cue"),
])
def test_a_proposed_design_needs_a_quote_that_states_one(design, quote, reason):
    task = f"We have {quote}. We want one network."
    purpose, rejected = verify_proposal(task, _proposal(design, quote))
    assert purpose.design is None and rejected == [{"field": "design", "value": design, "reason": reason}]


def test_a_group_difference_needs_a_verified_design():
    task = "We have 30 tumors. We want to know whether co-expression differs between subtypes we find."
    purpose, rejected = verify_proposal(task, _proposal(claims=[(
        "group_difference", "whether co-expression differs between subtypes we find")]))
    assert purpose.claims == () and rejected[0]["reason"] == "needs_design"


# -- the call ---------------------------------------------------------------------------

def test_the_call_is_strict_and_its_verified_reading_is_state():
    reply = _proposal("paired", "each did two weeks on a high-salt and two weeks on a low-salt diet",
                      [("individual_change", "find the participants whose co-expression networks shift most"),
                       ("regulator_change", "We want to find the participants")])
    context, events = _context(reply)
    entry, usage, _ = invoke_study_purpose(context, {}, TASK, LLMUsage(), [])
    assert context.study_purpose_llm.options[0][1] == {
        "method": "function_calling", "include_raw": True, "strict": True}
    assert entry == {"source": "model", "design": "paired",
                     "design_quote": "each did two weeks on a high-salt and two weeks on a low-salt diet",
                     "claims": [["individual_change", "find the participants whose co-expression networks shift most"]]}
    assert [call.role for call in usage.calls] == ["study_purpose"]
    detected = dict(events)["routing.study_purpose_detected"]
    assert detected["rejected"] == [{"field": "claim", "value": "regulator_change", "reason": "no_cue"}]


def test_a_failed_call_falls_back_to_the_words():
    context, events = _context(RuntimeError("provider down"))
    entry, usage, _ = invoke_study_purpose(context, {}, "We want to show that the drug causes it.", LLMUsage(), [])
    assert entry["source"] == "witness" and entry["claims"][0][0] == "causal"
    assert [name for name, _ in events] == ["routing.study_purpose_failed", "routing.study_purpose_detected"]
    assert [(call.role, call.status) for call in usage.calls] == [("study_purpose", "failed")]


def test_a_verified_empty_reading_is_not_replaced_by_the_words():
    # The model is primary: when it states nothing, the words do not add a reading back.
    state = {"study_purpose": {"source": "model", "design": None, "design_quote": "", "claims": []}}
    assert purpose_from_state(state, "We want to show that the drug causes it.").claims == ()
    assert purpose_from_state({}, "We want to show that the drug causes it.").claim == "causal"


def test_the_reply_reads_the_states_purpose():
    from netzoo_agent_core.graph import response
    from netzoo_agent_core.contracts import WorkflowPlan
    from langchain_core.messages import HumanMessage

    task = "We have expression from 40 patients. We want to know which patients stand out the most."
    decision = TaskDecision(
        action="no_tool", in_scope=True, should_execute=False, intent_type="answer_question", confidence=.9,
        reason="Guidance", capability_match_status="exact", match_basis="registry_features",
        matched_actions=["run_lioness_coexpression"], recommended_actions=["run_lioness_coexpression"])
    plan = WorkflowPlan(workflow="NO-TOOL", objective=task, decision=decision.model_dump(), status="respond_only")
    base = {"decision": decision.model_dump(), "plan": plan.model_dump(), "messages": [HumanMessage(content=task)],
            "tool_results": [], "evaluation": None}
    from test_reply_cards import POLICY
    with_purpose = response.respond(SimpleNamespace(project_policy=POLICY), {**base, "study_purpose": {
        "source": "model", "design": None, "design_quote": "",
        "claims": [["prediction", "We want to know which patients stand out the most."]]}})
    without = response.respond(SimpleNamespace(project_policy=POLICY), {**base, "study_purpose": {
        "source": "model", "design": None, "design_quote": "", "claims": []}})
    assert "No registered workflow builds a model" in with_purpose["messages"][-1].content
    assert "No registered workflow builds a model" not in without["messages"][-1].content


# -- b' (Log 357) -------------------------------------------------------------------------

def test_two_data_types_from_the_same_samples_are_no_paired_design():
    # Fifth held-out set, T4: "same" alone is no time point or condition.
    task = "Paired RNA-seq and methylation arrays from the same 80 lung adenocarcinoma resections. We want one network."
    purpose, rejected = verify_proposal(task, _proposal(
        "paired", "Paired RNA-seq and methylation arrays from the same 80 lung adenocarcinoma resections."))
    assert purpose.design is None and rejected[0]["reason"] == "two_data_types"


def test_two_data_types_at_two_time_points_stay_paired():
    task = ("We have matched RNA-seq and DNA methylation arrays from colon biopsies of 20 patients, taken before "
            "therapy and after eight weeks. We want one network.")
    purpose, _ = verify_proposal(task, _proposal(
        "paired", "taken before therapy and after eight weeks"))
    assert purpose.design == "paired"


@pytest.mark.parametrize("quote", [
    "Colonic organoids from 10 donors were each split into an IL-22 well and a vehicle well for RNA-seq",
    "an IL-22 well and a vehicle well",
])
def test_the_same_individuals_split_between_conditions_are_no_groups(quote):
    # Fifth held-out set, M6: the sentence splits each donor's organoids, so the conditions are paired.
    task = ("Colonic organoids from 10 donors were each split into an IL-22 well and a vehicle well for RNA-seq; "
            "human motif and PPI priors are ready. Which donors respond most?")
    purpose, rejected = verify_proposal(task, _proposal("groups", quote))
    assert purpose.design is None and rejected[0]["reason"] == "same_individuals"


def test_groups_from_different_people_stay_groups():
    task = "Quadriceps biopsies from 15 myositis patients and 15 age- and sex-matched controls. Which TFs differ most?"
    purpose, _ = verify_proposal(task, _proposal("groups", "15 myositis patients and 15 age- and sex-matched controls"))
    assert purpose.design == "groups"
