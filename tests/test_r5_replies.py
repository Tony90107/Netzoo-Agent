"""Log 331: Test 4 and Test 8 replies from the r5 round (2026-10-03), rendered from the recorded decisions.

Test 4 titled its reading "RNA-seq", listed six workflows with every premise
and formula, and gave the single-cell advice after its question. Test 8's
"What you asked about" answered "how can we directly quantify this
differential modular structure between the two networks?" with CONDOR's core
scores. All display: the decisions are the recorded ones.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from test_reply_cards import respond_and_card  # noqa: E402

RECORDED = json.loads((ROOT / "docs" / "research-log" / "test10-2026-10-03" / "out" / "r5-decisions.json").read_text())


def _reply(key):
    item = RECORDED[key]
    return respond_and_card(item["prompt"], TaskDecision.model_validate(item["decision"]))


def test_a_reading_is_titled_by_its_result_quote_even_when_the_quote_ends_differently():
    text, _, card = _reply("test4")
    # The model quoted "... across these 6 states." where the request goes on after a comma.
    assert '**Reading 1 -- "compare how regulatory networks are rewired across these 6 states"**' in text
    assert card.choices.options[0].label.startswith("Reading 1: “compare how regulatory networks")


def test_many_workflows_for_one_reading_get_one_line_each():
    text, _, _ = _reply("test4")
    reading = text.split("**Reading 1", 1)[1].split("**Reading 2", 1)[0]
    assert "Mathematical interpretation" not in reading and "Registered purpose" not in reading
    assert "- TF-only regulatory network:\n  - **PANDA** —" in reading
    assert "Per-sample version: **LIONESS-PANDA**." in reading


def test_the_single_cell_note_comes_before_the_question():
    text, _, _ = _reply("test4")
    assert text.index("**Single-cell data.**") < text.index("Which reading should we start with")


def test_a_gap_reply_explains_the_outside_step_before_offering_the_alternative():
    text, _, _ = _reply("test7")
    assert text.index("**Building the prior from chromatin accessibility.**") < text.index("PANDA can instead")


def test_a_concern_about_comparing_two_networks_is_not_answered_with_core_scores():
    text, _, _ = _reply("test8")
    asked = text.split("What you asked about:", 1)[1].split("\n\n", 2)[1]
    assert "Core scores" not in asked
    assert asked.endswith("CONDOR finds modules in one network at a time; it does not compare two. "
                          "ALPACA, described below, does.")
    assert text.index("What you asked about:") < text.index("**Comparing module structure between two networks.**")
    assert "(TF, target gene, control weight, disease weight)" in text


def test_single_cell_data_is_not_offered_the_per_cell_networks_its_note_advises_against():
    # Log 334: r1-r3 offered "Only expression data -> LIONESS-COEXPRESSION or BONOBO".
    item = json.loads((ROOT / "docs" / "research-log" / "test10-2026-10-03" / "out"
                       / "r3-decisions.json").read_text())["test4"]
    text, _, card = respond_and_card(item["prompt"], TaskDecision.model_validate(item["decision"]))
    assert "per-cell LIONESS or BONOBO networks are not advised" in text
    assert "What your data allows" not in text and "LIONESS-COEXPRESSION" not in text
    assert card.choices.header != "Inputs"
    assert not any("BONOBO" in (option.description or "") for option in card.choices.options)
