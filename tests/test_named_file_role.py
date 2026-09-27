"""Log 238: a file the request names for one role but that is another by content.

Blind case 10 says "this expression matrix, data/blind-tests/case-1/expression.tsv";
by content that file is the TF-motif prior. Since b670faa a selected role is
never given another file, so discovery found nothing and the reply said the
gene-gene workflows "need only the input you named". The reply now says where
the named file belongs by content, and still offers no replacement for it.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from netzoo_agent_core.graph.input_inspection import advise_from_inspected_inputs  # noqa: E402
from netzoo_agent_core.interpretation.concept_answers import render_outcome_clarification  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402
from test_input_inspection import AUTHORITY, PANDA_SET, _decision, _folder  # noqa: E402

POLICY = ProjectPolicyLoader(Path(__file__).parents[1]).load()
AGGREGATE_TIE = ["run_panda", "run_otter", "run_giraffe"]
#: Case 10's folder: every name is another file's content.
MISNAMED = {"expression.tsv": "motif-panda.tsv", "motif.tsv": "ppi.tsv", "ppi.tsv": "expression.tsv"}


def _task(written: str) -> str:
    return f"All I have is this expression matrix, {written}expression.tsv. Build me a network and let's see."


def _advise(tmp_path, files):
    written = _folder(tmp_path, files)
    decision = _decision(hypothesis_actions=list(AGGREGATE_TIE))
    task = _task(written)
    return task, decision, advise_from_inspected_inputs(task, decision, root=tmp_path)


def test_a_named_file_that_is_another_role_is_reported_where_it_belongs(tmp_path):
    task, decision, advised = _advise(tmp_path, MISNAMED)

    assert advised.discovered_inputs == ["motif_file=data/study/expression.tsv"]
    assert not any(item.startswith("expression_file=") for item in advised.discovered_inputs)
    assert advised.advisory_recommendation is None
    for field in AUTHORITY:
        assert getattr(advised, field) == getattr(decision, field), field

    reply = render_outcome_clarification(advised, POLICY, task=task)

    assert ("By content, `data/study/expression.tsv`, which you named as the expression "
            "matrix, validates as the TF-motif prior, not as the expression matrix.") in reply
    assert "tell me which file holds your expression matrix" in reply
    assert "need only the input you named" not in reply
    assert "`ppi.tsv` as the expression matrix" not in reply


def test_a_named_file_that_is_what_the_user_said_is_reported_as_before(tmp_path):
    task, _, advised = _advise(tmp_path, PANDA_SET)

    assert "expression_file=data/study/expression.tsv" in advised.discovered_inputs

    reply = render_outcome_clarification(advised, POLICY, task=task)

    assert "By content, these files validate for an input role" in reply
    assert "which you named as" not in reply
