from __future__ import annotations

import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.interpretation import render_spec_backed_concept_answer  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402


def _decision() -> TaskDecision:
    return TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=1.0,
        reason="concept question",
    )


def test_purpose_question_uses_registered_workflow_description():
    policy = ProjectPolicyLoader(Path(__file__).parents[1]).load()

    answer = render_spec_backed_concept_answer(
        "what is the function of PANDA", _decision(), policy
    )

    assert answer is not None
    assert "Infer an aggregate TF-to-gene regulatory network" in answer
    assert "No files were inspected and no analysis ran." in answer


def test_non_purpose_question_keeps_response_model_path():
    policy = ProjectPolicyLoader(Path(__file__).parents[1]).load()

    assert render_spec_backed_concept_answer("compare PANDA and PUMA", _decision(), policy) is None
