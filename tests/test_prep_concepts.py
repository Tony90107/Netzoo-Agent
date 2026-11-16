"""A question about a preparation step -- SNAIL and the other normalizations, SPONGE -- is answered about that step
(2026-11-16).

Live: "What is the difference between SNAIL and quantile normalization?" got the fourteen network results; "What does
SPONGE do compared with just using a motif prior with PANDA?" got "I couldn't match what you asked for to a result
any registered NetZoo workflow produces", which reads as SPONGE not being supported.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.core_decision import ClarifyNeed, CoreDecision  # noqa: E402
from netzoo_agent_core.interpretation.core_views import ALLOWED, core_view  # noqa: E402
from netzoo_agent_core.interpretation.prep_concepts import PREP_CONCEPT_KIND, prep_concept_reply  # noqa: E402


def test_two_normalizations_are_compared_with_the_lines_the_run_path_uses():
    reply = prep_concept_reply("What is the difference between SNAIL and quantile normalization?")
    assert reply.startswith("How SNAIL (PySNAIL) and quantile (preprocessCore) differ:")
    assert "- SNAIL (PySNAIL): smooth quantile normalization within the sample groups you give" in reply
    assert "- quantile (preprocessCore): every sample takes the same value distribution" in reply
    assert "SNAIL is smooth quantile normalization adapted so that it does not create false co-expression" in reply
    assert "preparation step, not a network workflow" in reply and "PANDA" in reply
    assert "To pick one for your data: which does it need" in reply
    for absent in ("CONDOR", "SAMBAR", "I can't tell yet", "couldn't match"):
        assert absent not in reply


def test_one_normalization_is_described_then_planned():
    reply = prep_concept_reply("What is SNAIL?")
    assert reply.startswith("What SNAIL (PySNAIL) does:")
    assert "To plan it: give the path to your expression matrix and a sample-to-group file" in reply
    assert "To pick one" not in reply
    assert "sample-to-group" not in prep_concept_reply("What does TMM do?")


def test_sponge_is_described_as_the_step_that_builds_the_priors():
    reply = prep_concept_reply("What does SPONGE do compared with just using a motif prior with PANDA?")
    assert reply.startswith("What SPONGE does: it builds the two prior files")
    assert "hg38, 750 bp upstream to 250 bp downstream" in reply
    assert "SCORPION" in reply and "PANDA" in reply, "the workflows that read its priors, from the registry"
    assert "1,019 in JASPAR2026" in reply
    assert "SPONGE is only needed when you have none" in reply
    assert "couldn't match" not in reply


@pytest.mark.parametrize("task", [
    "Normalize /data/counts.tsv with SNAIL.",
    "Build the priors with SPONGE for FOXF2.",
    "What is the difference between PANDA and LIONESS?",
    "Run PANDA on data/study.",
    "Don't use SPONGE; what does PANDA need?",
])
def test_commands_and_other_questions_are_not_this_reply(task):
    assert prep_concept_reply(task) is None


def test_it_answers_a_call_that_is_not_do():
    task = "What is the difference between SNAIL and quantile normalization?"
    core = CoreDecision(kind="CLARIFY", basis="goal_unclear", clarify=ClarifyNeed(
        missing="both", candidates=["PANDA", "CONDOR"], question="Which of these results do you want?"))
    decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="read",
                            core=core)
    from netzoo_agent_core.contracts import HumanMessage

    state = {"decision": decision.model_dump(), "messages": [HumanMessage(content=task)]}
    result = core_view(None, state, lambda content, kind: {"content": content, "reply_kind": kind})
    assert result["reply_kind"] == PREP_CONCEPT_KIND and result["content"].startswith("How SNAIL")
    assert all(PREP_CONCEPT_KIND in ALLOWED[kind] for kind in ("CLARIFY", "ASK", "DECLINE", "UNCHECKED"))


@pytest.mark.parametrize("task", [
    "Can you run PANDA on my SNAIL-normalized counts?",
    "What does PANDA need? My counts were normalized with SNAIL.",
    "Which motif prior should I use for data/priors built with SPONGE?",
    "What is the difference between SNAIL and quantile normalization for /data/raw/counts.tsv?",
    "How do I run qsmooth on my counts?",
    "Lungs from 30 mice, RNA-seq. We want one regulatory network and to check whether TMM versus quantile "
    "normalisation changes it.",
])
def test_data_the_step_already_made_or_a_file_is_about_the_run(task):
    assert prep_concept_reply(task) is None
