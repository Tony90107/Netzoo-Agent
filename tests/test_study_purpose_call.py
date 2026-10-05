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


# -- b'' (Log 359) ------------------------------------------------------------------------

def test_a_quote_setting_out_to_show_a_cause_supports_no_other_conclusion():
    # Sixth held-out set, P2-b: proposed as a group difference three times.
    task = ("We have whole-blood microarrays from 64 ALS patients and 40 age- and sex-matched healthy controls, "
            "expression only. The grant aim is to show that immune co-expression changes drive motor neuron loss.")
    purpose, rejected = verify_proposal(task, _proposal(
        "groups", "64 ALS patients and 40 age- and sex-matched healthy controls",
        [("group_difference", "show that immune co-expression changes drive motor neuron loss")]))
    assert purpose.claims == () and rejected == [
        {"field": "claim", "value": "group_difference", "reason": "causal_wording"}]


def test_an_individual_change_needs_a_change_or_an_extreme():
    task = "For now I just want each subject's co-expression network built so the team can browse them."
    purpose, rejected = verify_proposal(task, _proposal(claims=[(
        "individual_change", "each subject's co-expression network built so the team can browse them")]))
    assert purpose.claims == () and rejected[0]["reason"] == "no_cue"


@pytest.mark.parametrize("quote", [
    "Who shows the most dramatic rewiring between the primary and the metastasis?",
    "Which donors' organoids show the strongest network response to IL-22?",
    "rank the runners by how strongly their own networks were perturbed",
])
def test_individuals_with_a_change_or_an_extreme_stay(quote):
    purpose, _ = verify_proposal(f"We have RNA-seq. {quote}", _proposal(claims=[("individual_change", quote)]))
    assert purpose.claim == "individual_change"


# -- Log 361: technical terms veto only what they pair or group ------------------------------

@pytest.mark.parametrize("design, quote", [
    ("groups", "12 Shank3-mutant mice and 12 wild-type littermates"),
    ("groups", "Our count matrix of sorted splenic Treg cells has columns WT_1 to WT_10 and Ezh2cKO_1 to Ezh2cKO_10"),
    ("groups", "four replicate pools at each of vehicle and three bisphenol S concentrations"),
    ("groups", "60 children with Kawasaki disease and 40 febrile children with other infections; we only have the "
               "expression matrix"),
])
def test_a_technical_word_beside_a_real_design_does_not_veto_it(design, quote):
    purpose, rejected = verify_proposal(f"{quote}. We want one network.", _proposal(design, quote))
    assert purpose.design == design and rejected == []


@pytest.mark.parametrize("design, quote", [
    ("paired", "2 x 150 bp paired-end RNA-seq, about 40 million read pairs per library"),
    ("paired", "paired RNA-seq and proteomics matrices from the same tumours"),
    ("paired", "I saved the count matrix both before and after normalization"),
    ("groups", "collected at two hospitals and over three years"),
    ("groups", "sequenced in four batches and two lanes"),
    ("groups", "TMM versus quantile normalisation"),
])
def test_a_technical_pairing_or_grouping_is_still_no_design(design, quote):
    purpose, rejected = verify_proposal(f"We have RNA-seq, {quote}. We want one network.", _proposal(design, quote))
    assert purpose.design is None and rejected[0]["reason"] in {"technical", "two_data_types"}


# -- Logs 365-368: workflows with one result for all the samples ------------------------------
# Recorded decisions from earlier live rounds (already read), so only the reply layer is under test.

LIVE = ROOT / "docs" / "research-log" / "purpose-contract-2026-10-04" / "live"
POOLED = ("With one sample per individual (per time point), that says nothing about a single individual; "
          "a result for one individual needs many samples from that individual.")


def _recorded(tag, key, purpose=None):
    from langchain_core.messages import HumanMessage
    from netzoo_agent_core.cli.follow_up import build_next_turn_prompt
    from netzoo_agent_core.contracts import WorkflowPlan
    from netzoo_agent_core.graph import response
    from netzoo_agent_core.reply_cards.builder import build_reply_card
    from test_reply_cards import POLICY
    import ast
    import json

    item = json.loads((LIVE / f"{tag}-decisions.json").read_text())[key]
    traced = item["study_purpose"]
    traced = purpose or (ast.literal_eval(traced) if isinstance(traced, str) else traced)
    decision = TaskDecision.model_validate(item["decision"])
    plan = WorkflowPlan(workflow="NO-TOOL", objective=item["prompt"][:200], decision=decision.model_dump(),
                        status="respond_only")
    state = {"decision": decision.model_dump(), "plan": plan.model_dump(), "tool_results": [], "evaluation": None,
             "messages": [HumanMessage(content=item["prompt"])], "study_purpose": traced}
    out = response.respond(SimpleNamespace(project_policy=POLICY), state)
    result = {**state, "messages": [*state["messages"], out["messages"][-1]], "reply_kind": out["reply_kind"]}
    card = build_reply_card(result, build_next_turn_prompt(result), POLICY, task=item["prompt"])
    return out["messages"][-1].content, card


def _without_one_result(monkeypatch):
    from netzoo_agent_core.interpretation import study_purpose_notes
    from workflow_registry import CLAIM_SUPPORT

    monkeypatch.setattr(study_purpose_notes, "CLAIM_SUPPORT", {
        key: cell for key, cell in CLAIM_SUPPORT.items()
        if cell.level != "one_result" and key[0] not in {"run_dragon", "run_lioness_dragon"}})


def test_when_no_listed_workflow_answers_the_condition_comes_first_and_the_card_adds_per_sample_planning():
    # s9 S3-c: "Which patients show the biggest tumour-versus-normal shift ..." got PUMA as a fallback.
    text, card = _recorded("s9", "cand-S3-c-1")
    assert text.startswith('For your question ("Which patients show the biggest')
    assert (f"- **PUMA** — gives one network from all the samples it is given. {POOLED} Per-sample workflow for "
            "the same data: **LIONESS-PUMA**.") in text
    assert "does not answer" not in text and "cannot show" not in text
    assert "Fallback recommendation: **PUMA**" in text  # the decision and the rest of the reply are unchanged
    planned = [step.action for step in card.next_steps if step.resolution == "plan_workflow"]
    assert "run_lioness_puma" in planned
    assert any(point.startswith("PUMA gives one result for all the samples: with one sample per individual that "
                                "cannot show which individuals") for point in card.points)


def test_the_card_never_drops_a_step_it_had(monkeypatch):
    # s10 T2-3: three people sampled weekly for a year, DRAGON as a fallback -- DRAGON run per person
    # answers there (Log 366), so it must stay plannable wherever the card offered it.
    with_text, with_card = _recorded("s10", "cand-T2-3")
    _without_one_result(monkeypatch)
    _, without_card = _recorded("s10", "cand-T2-3")
    before = [step.key for step in without_card.next_steps]
    after = [step.key for step in with_card.next_steps]
    assert after[:len(before)] == before
    assert "plan-run_lioness_dragon" in after
    assert "- **DRAGON** — gives one two-layer network from all the samples it is given." in with_text


def test_a_tie_lists_the_workflows_that_answer_before_the_one_result_ones_and_names_them_in_its_lead():
    # s7 T1: "we just want to see whose marrow networks stand out most", tie with PANDA, PUMA, OTTER.
    text, card = _recorded("s7", "cand-T1-1")
    block = text.split("For your question (", 1)[1]
    assert block.index("- **LIONESS-PANDA**, **LIONESS-PUMA** — Each sample") < block.index(
        "- **PANDA**, **PUMA**, **OTTER** — each gives one network from all the samples it is given.")
    assert "Per-sample workflows for the same data: **LIONESS-PANDA**, **LIONESS-PUMA**." in block
    assert ("These fit the result you described; **PANDA**, **PUMA** and **OTTER** give one result for all the "
            "samples they are given. To choose, tell me: (1)") in text
    assert "These all fit" not in text
    # Others answer the question, so the card adds no planning step of its own.
    assert not any(step.key == "plan-run_lioness_panda" for step in card.next_steps)


def test_cobra_says_what_it_gives_but_stays_silent_where_no_cell_is_declared():
    text, _ = _recorded("s9", "cand-S1-a-1")
    assert "- **COBRA** — gives the co-expression associated with each covariate across all the samples" in text
    assert "Per-sample workflows for the same data: **LIONESS-COEXPRESSION**, **BONOBO**." in text
    # s9 S1-b asks whether the diet changes co-expression across the cohort (paired): COBRA has no
    # declared cell for a paired group difference, and an undeclared cell says nothing (CC1).
    text, _ = _recorded("s9", "cand-S1-b-1")
    assert "all the samples it is given" not in text and "one result for all the samples" not in text


def test_a_cohort_question_keeps_the_one_result_workflows_silent():
    text, card = _recorded("s7", "cand-T1-1", purpose={
        "source": "model", "design": "groups", "design_quote": "x",
        "claims": [["group_difference", "we just want to see whose marrow networks stand out most."]]})
    assert POOLED not in text and "one result for all the samples" not in text
    assert not any("one result for all the samples" in point for point in card.points)


def test_a_causal_claim_keeps_its_gap_lead_and_the_one_result_line_stays_in_the_paragraph():
    # The reply layer takes the state's reading as given (verifying it is the call's job).
    text, _ = _recorded("s7", "cand-T1-1", purpose={
        "source": "model", "design": None, "design_quote": "",
        "claims": [["causal", "Predicting progression or proving causality is off the table"],
                   ["individual_change", "we just want to see whose marrow networks stand out most."]]})
    assert text.startswith('About "Predicting progression or proving causality is off the table": None of the')
    assert "but none can show that one thing causes another; to choose among them, tell me:" in text
    assert "- **PANDA**, **PUMA**, **OTTER** — each gives one network" in text


def test_an_aggregate_named_only_because_its_per_sample_version_produces_it_says_nothing():
    # s10 T2-1: LIONESS-DRAGON matched; DRAGON appears only as "also produces the aggregate" (Log 366).
    text, _ = _recorded("s10", "cand-T2-1")
    assert "- **LIONESS-DRAGON** — Each sample gets its own two-layer network" in text
    assert "- **DRAGON** —" not in text
