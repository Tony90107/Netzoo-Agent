"""reread-tail-fragments-2026-10-31: with NETZOO_REREAD_TAILS=on, a re-read ask in the tail of a sentence that credits
no workflow and carries no reason is not added (it would be refused as "couldn't match"); whole sentences, credited
asks and asks with a reason are added as before; off by default."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from netzoo_agent_core.contracts.capability_check import CapabilityCheck  # noqa: E402
from netzoo_agent_core.interpretation.reread import merge_reread, tails_mode  # noqa: E402
from test_reread import _req, _reread_check  # noqa: E402

# j4 S20-shaped: the result is quoted; the re-read was given the purpose clause after it.
TASK = ("Please build one TF-to-gene PANDA network for each developmental stage from our expression, motif and PPI "
        "files, so we can see which TFs are high at each stage.")
RESULT = "one TF-to-gene PANDA network for each developmental stage"
TAIL = "so we can see which TFs are high at each stage"


def _found():
    return CapabilityCheck(requirements=[_req(RESULT, "result", "available", ["panda.tf_gene_network"])])


def test_off_by_default_the_tail_is_added_as_before(monkeypatch):
    monkeypatch.delenv("NETZOO_REREAD_TAILS", raising=False)
    assert tails_mode() == "off"
    merged = merge_reread(TASK, _found(), _reread_check(TASK, TAIL), [TAIL])
    assert [(item.quote, item.status) for item in merged.results()][-1] == (TAIL, "not_available")


def test_on_a_tail_that_matches_nothing_is_not_added(monkeypatch):
    monkeypatch.setenv("NETZOO_REREAD_TAILS", "on")
    merged = merge_reread(TASK, _found(), _reread_check(TASK, TAIL), [TAIL])
    assert [item.quote for item in merged.results()] == [RESULT]
    assert not merged.full_gap


def test_on_a_credited_tail_is_still_added(monkeypatch):
    monkeypatch.setenv("NETZOO_REREAD_TAILS", "on")
    merged = merge_reread(TASK, _found(), _reread_check(TASK, TAIL, ["panda.targeting_scores"]), [TAIL])
    assert [item.quote for item in merged.results()] == [RESULT, TAIL]


def test_on_a_delivery_tail_keeps_its_reason_only_with_a_verified_claim(monkeypatch):
    """heldout14 P1 (test_reread EMAILED): the unsupported tail the re-read exists for. Typed `delivery` with the claim
    verified for the turn, it keeps its registry-wide reason and stays a refused part; unverified, it is dropped --
    the known risk of this rule, measured live (T4 delivery controls)."""
    from test_reread import EMAILED, _decision  # noqa: F401
    from netzoo_agent_core.interpretation.reread import reread_passages

    monkeypatch.setenv("NETZOO_REREAD_TAILS", "on")
    found = CapabilityCheck(requirements=[_req("each patient's TF-gene network", "result", "available",
                                               ["lioness_panda.per_sample_networks"]),
                                          _req("expression, motifs and PPI of 50 patients", "context")])
    passages = reread_passages(EMAILED, _decision(found))
    tail = "emailed to each patient's doctor automatically"
    # As the router builds it: the turn's verified claims (study purpose) keep the registry-wide reason.
    from netzoo_agent_core.contracts.capability_check import reread_as_proposal, reread_model
    from netzoo_agent_core.interpretation.capability_check import build_capability_check
    from test_reread import PLAIN

    reread = reread_model(1).model_validate({"s1": {"asks": [{**PLAIN, "quote": tail, "delivered_by": [],
                                                              "not_by": ["delivery"]}]}})
    built = build_capability_check(EMAILED, reread_as_proposal(reread), {"delivery": tail})[0]
    merged = merge_reread(EMAILED, found, built, passages)
    assert [(item.quote, item.status) for item in merged.results()][-1] == (tail, "not_available")
    # Without a verified claim the same tail has no reason and is dropped: the live controls of RESULTS.md (T4)
    # check how often that happens.
    unverified = merge_reread(EMAILED, found, _reread_check(EMAILED, tail, not_by=["delivery"]), passages)
    assert [item.quote for item in unverified.results()] == ["each patient's TF-gene network"]


def test_on_a_whole_sentence_given_to_the_reread_is_still_added(monkeypatch):
    monkeypatch.setenv("NETZOO_REREAD_TAILS", "on")
    task = "We have expression for 24 samples. We want a figure for the grant."
    sentence = "We want a figure for the grant."
    empty = CapabilityCheck(requirements=[_req("We have expression for 24 samples.", "context")],
                            unchecked=[sentence])
    merged = merge_reread(task, empty, _reread_check(task, sentence), [sentence])
    assert [(item.quote, item.status) for item in merged.results()] == [(sentence, "not_available")]
