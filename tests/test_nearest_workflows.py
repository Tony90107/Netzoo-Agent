"""couldn't-match-2026-11-18: a refusal names the nearest of the six main workflows, built in code."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from netzoo_agent_core.contracts.capability_check import CapabilityCheck, CheckedRequirement  # noqa: E402
from netzoo_agent_core.interpretation import nearest_workflows as nw  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import full_gap_reply  # noqa: E402

ASKED = "I need a separate network of which transcription factors control which genes, and how strongly."


def check(linked):
    return CapabilityCheck(requirements=[CheckedRequirement(quote=ASKED, kind="result", status="not_available")],
                           full_gap=True, linked=linked)


def decision(linked=None, inputs=()):
    return SimpleNamespace(capability_check=check(linked or {}), guidance_input_artifacts=list(inputs),
                           outcome_hypotheses=[])


def test_the_reading_links_are_kept_per_sentence():
    proposal = {"s1": {"asks": [{"quote": ASKED, "delivered_by": ["lioness_panda.per_sample_networks"]},
                                {"quote": "other", "delivered_by": []}]}, "goal": "x"}
    assert nw.reading_links(proposal) == {ASKED: ["lioness_panda.per_sample_networks"]}


def test_a_linked_main_workflow_is_named_with_what_happened_and_what_it_produces():
    line = nw.nearest_line(decision({ASKED: ["lioness_panda.per_sample_networks"]}))
    assert line.startswith("Nearest of NetZoo's main workflows: **LIONESS-PANDA** (one TF-gene network per sample")
    assert "did not confirm" in line and "If that is what you meant" in line


def test_a_linked_workflow_outside_the_six_is_not_named():
    assert nw.nearest_line(decision({ASKED: ["dragon.two_layer_network"]})) == ""


def test_without_a_link_the_main_workflows_taking_the_stated_data_are_named():
    line = nw.nearest_line(decision(inputs=["expression_matrix"]))
    assert "by the kind of data you described" in line and "**PANDA**" in line
    assert all(nw.is_main(name) for name in ("PANDA", "LIONESS-PANDA", "SCORPION", "PORCUPINE"))
    assert not nw.is_main("DRAGON") and not nw.is_main("BONOBO")
    assert line.count("**") <= 2 * nw.MAX_NAMED


def test_nothing_found_says_nothing():
    assert nw.nearest_line(decision()) == "" and nw.nearest_line(None) == ""


def test_the_full_gap_reply_carries_the_line_before_its_closing():
    line = nw.nearest_line(decision({ASKED: ["lioness_panda.per_sample_networks"]}))
    reply = full_gap_reply(check({}), options=line)
    assert line in reply and reply.endswith("No files were inspected and no analysis ran.")


def test_a_workflow_linked_by_several_entries_is_named_once():
    line = nw.nearest_line(decision({ASKED: ["panda.tf_gene_network", "panda.targeting_scores",
                                             "lioness_panda.per_sample_networks"]}))
    assert line.count("**PANDA**") == 1 and line.count("**LIONESS-PANDA**") == 1


def test_a_near_miss_entry_names_no_nearest_workflow():
    assert nw.nearest_line(decision({ASKED: ["panda.no_sign"]})) == ""
