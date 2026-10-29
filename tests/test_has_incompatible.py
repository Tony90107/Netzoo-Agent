"""has-incompatible-2026-10-30 (j2 Q18): what the user says they have rules a workflow out only through its explicit
incompatible_input_artifacts; the confirm names that kind; off by default makes no extra call."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.graph import jev_guard_call as guard  # noqa: E402

Q18 = ("I'd like to subtype our 300 ovarian cancer samples by how strongly each biological pathway is hit by "
       "mutations. What we have is a bulk RNA-seq expression matrix.")


def _fake(data, has, calls):
    def decide(state, questions):
        calls.append(sorted(questions))
        if "sentence" in questions:
            return {"answers": {"sentence": {"choice": "none", "confidence": 0.9}}}
        if "has" in questions:
            return {"answers": {"has": {"choice": has[0], "confidence": has[1]}}}
        return {"answers": {"data": {"choice": data[0], "confidence": data[1]}}}
    return decide


def test_off_makes_no_extra_call(monkeypatch):
    calls = []
    monkeypatch.delenv("NETZOO_JEV_DATA_HAS", raising=False)
    monkeypatch.setattr(guard, "_decide", _fake(("several", 0.32), ("expression_matrix", 0.8), calls))
    result = guard.check_typed_data(Q18, ["SAMBAR"])
    assert calls == [["data"]] and not any(result["ruled_out"].values()) and "has" not in result


def test_on_rules_out_through_the_explicit_field_and_the_confirm_names_that_kind(monkeypatch):
    calls = []
    monkeypatch.setenv("NETZOO_JEV_DATA_HAS", "on")
    monkeypatch.setattr(guard, "_decide", _fake(("several", 0.32), ("expression_matrix", 0.8), calls))
    result = guard.check_typed_data(Q18, ["SAMBAR"])
    assert result["ruled_out"]["SAMBAR"] == "SAMBAR incompatible_input_artifacts: expression_matrix"
    assert result["ruled_by"] == {"SAMBAR": "has"} and result["ruled_kind"] == "expression_matrix"
    assert result["unplaced"] and "gene-by-sample expression table" in guard.condition_question(result,
                                                                                             result["unplaced"])


def test_on_never_uses_the_broad_branch(monkeypatch):
    """j5 W17: expression for CONDOR (no incompatible list) is never ruled out by the has-read, even at 0.95."""
    calls = []
    monkeypatch.setenv("NETZOO_JEV_DATA_HAS", "on")
    monkeypatch.setattr(guard, "_decide", _fake(("expression_matrix", 0.69), ("expression_matrix", 0.95), calls))
    result = guard.check_typed_data("Find communities of TFs and genes from our expression data.", ["CONDOR"])
    assert not result["ruled_out"]["CONDOR"] and result["ruled_by"] == {}
