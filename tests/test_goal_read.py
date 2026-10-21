"""ROUND-21 (R21-A): a full gap no reason can be given for is read once more; when the request names no result, the
turn is CLARIFY instead of DECLINE. Any other answer, or none, leaves the DECLINE."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.capability_check import (  # noqa: E402
    CapabilityCheck, CheckedRequirement, GoalRead,
)
from netzoo_agent_core.contracts.fact_check import FactCheck  # noqa: E402
from netzoo_agent_core.graph.goal_read_call import invoke_goal_read  # noqa: E402
from netzoo_agent_core.interpretation.core_decision import decide_core, with_core  # noqa: E402
from netzoo_agent_core.interpretation.goal_read import needs_goal_read, with_goal_read  # noqa: E402

C24 = ("Reviewers asked for 'a network analysis' of our placenta study. We have mRNA-seq and small-RNA-seq from 45 "
       "preeclampsia and control placentas. Honestly I don't know what kind of network they expect.")
C22 = "Call somatic SNVs and indels from tumour_07.bam against its matched normal_07.bam and give me a filtered VCF."


def _gap(quote, **row):
    return CapabilityCheck(requirements=[CheckedRequirement(quote=quote, kind="result", status="not_available", **row)],
                           full_gap=True)


def _decision(check, **extra):
    return TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="r",
                        capability_check=check, **extra)


def test_only_a_confirmed_full_gap_with_no_reason_to_say_is_read_again():
    blank = _gap("'a network analysis' of our placenta study")
    assert needs_goal_read(blank, _decision(blank), C24)
    sized = _gap("a network", limits=["COBRA requires more genes than samples; the request has 48 genes and 600 "
                                      "samples"])
    assert not needs_goal_read(sized, _decision(sized), C24)  # it says why: the DECLINE stands
    assert not needs_goal_read(blank.model_copy(update={"full_gap": False}), None, C24)
    assert not needs_goal_read(blank.model_copy(update={"provisional": True}), None, C24)
    asked = _decision(blank, fact_check=FactCheck(status="checked", open_results=["what kind of network"]))
    assert not needs_goal_read(blank, asked, C24)  # the fact agent's CLARIFY comes first


def test_a_read_naming_no_result_with_its_words_in_the_request_opens_the_goal():
    blank = _gap("'a network analysis' of our placenta study")
    opened = with_goal_read(blank, C24, GoalRead(asked_words="a network analysis", result="names_no_result"))
    assert opened.open_goal_quote == "a network analysis"
    assert with_goal_read(blank, C24, GoalRead(asked_words="a network analysis", result="names_a_result")) == blank
    assert with_goal_read(blank, C24, GoalRead(asked_words="a pathway map", result="names_no_result")) == blank
    assert with_goal_read(blank, C24, None) == blank


def test_words_naming_one_registered_workflow_keep_their_goal():
    # As in goal_unclear: a question about one named method has a goal (unlabelled ve-m3 N21).
    task = ("Can PUMA convert its signed edge weights into experimentally proven activation and repression labels as a "
            "guaranteed native output?")
    gap = _gap(task)
    assert with_goal_read(gap, task, GoalRead(asked_words=task, result="names_no_result")) == gap


def test_an_open_goal_is_clarify_and_a_named_result_stays_declined():
    blank = _gap("'a network analysis' of our placenta study")
    opened = with_goal_read(blank, C24, GoalRead(asked_words="a network analysis", result="names_no_result"))
    core = decide_core(_decision(opened), C24)
    assert (core.kind, core.basis, core.clarify.goal_quote) == ("CLARIFY", "goal_open", "a network analysis")
    assert with_core(_decision(opened), core).clarification_question == core.clarify.question
    vcf = _gap("give me a filtered VCF")
    named = with_goal_read(vcf, C22, GoalRead(asked_words="give me a filtered VCF", result="names_a_result"))
    assert (decide_core(_decision(named), C22).kind, decide_core(_decision(named), C22).basis) == (
        "DECLINE", "full_gap")


class _Adapter:
    def __init__(self, answer):
        self.answer = answer

    def invoke(self, messages):
        assert "GoalRead" in messages[0].content and C24 in messages[1].content
        if isinstance(self.answer, Exception):
            raise self.answer
        return {"parsed": self.answer, "raw": None}


class _LLM:
    def __init__(self, answer):
        self.answer = answer

    def with_structured_output(self, schema, **kwargs):
        assert schema is GoalRead and kwargs["strict"]
        return _Adapter(self.answer)


def test_the_call_returns_the_read_or_its_error():
    read, _raw, _in, out, error = invoke_goal_read(
        _LLM(GoalRead(asked_words="a network analysis", result="names_no_result")), C24)
    assert error is None and read.result == "names_no_result" and "names_no_result" in out
    read, *_rest, error = invoke_goal_read(_LLM(ValueError("undecodable")), C24)
    assert read is None and isinstance(error, ValueError)
