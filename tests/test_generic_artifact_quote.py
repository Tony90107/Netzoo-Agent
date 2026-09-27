"""Log 193: a quote that says nothing about what is connected states no network kind.

Log 189 saw "build me a network" cited as explicit evidence for
`regulatory_network` in 3 of 4 Case 10 replies. The quote grounds, so routing is
unchanged, but it does not say the network is regulatory, and the reply's
assumption note -- which keyed on "any artifact quote" -- was suppressed.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

from netzoo_agent_core.contracts.outcomes import OutcomeEvidence  # noqa: E402
from test_reply_notes import _answer, _decision  # noqa: E402


def _quoted(span: str):
    decision = _decision(artifact_source="explicit")
    hypothesis = decision.outcome_hypotheses[0]
    evidence = [OutcomeEvidence(
        dimension="artifact_type", value="regulatory_network", source="explicit",
        text_span=span, rationale="t",
    )]
    return decision.model_copy(update={
        "outcome_hypotheses": [hypothesis.model_copy(update={"evidence": evidence})],
    })


@pytest.mark.parametrize("span", ["build me a network", "Build me a network and let's see.", "幫我建一個網路"])
def test_a_generic_network_quote_still_gets_the_assumption_note(span):
    answer = _answer(_quoted(span))

    assert "Your request does not say what the network should connect" in answer
    assert "**BONOBO** and **LIONESS-COEXPRESSION** need only the input you named." in answer


@pytest.mark.parametrize("span", [
    "regulatory network", "which TFs regulate genes", "a network of genes",
    "each patient's regulatory wiring is different", "我想知道調控因子",
])
def test_a_quote_naming_what_is_connected_adds_no_note(span):
    assert "does not say what the network should connect" not in _answer(_quoted(span))
