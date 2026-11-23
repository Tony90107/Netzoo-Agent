"""needs-sign-2026-11-18: a typed needs_sign counts only when some words of the request ask for the sign."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from netzoo_agent_core.interpretation.capability_check import build_capability_check  # noqa: E402
from netzoo_agent_core.interpretation.request_readings import SIGN_WORDS  # noqa: E402
from test_capability_check import _ask  # noqa: E402

ENTRIES = ("lioness_panda.per_sample_networks",)


@pytest.mark.parametrize("text", ["which transcription factors control which genes, and how strongly",
                                  "how active each TF is", "activity scores for every TF in every patient",
                                  "a significant network"])
def test_strength_or_activity_words_do_not_ask_for_the_sign(text):
    assert not SIGN_WORDS.search(text)


@pytest.mark.parametrize("text", ["whether each TF switches its target genes on or off",
                                  "whether each TF turns its targets up or down",
                                  "signed TF-to-gene effects, activating versus repressing",
                                  "the sign of each edge", "which TFs repress their targets", "and their signs"])
def test_sign_words_ask_for_the_sign(text):
    assert SIGN_WORDS.search(text)


def test_live_b3_keeps_lioness_panda():
    task = ("For each of our 85 ovarian cancer patients I need a separate network of which transcription factors "
            "control which genes, and how strongly. We have tumour expression, a TF motif prior and a PPI file.")
    quote = "I need a separate network of which transcription factors control which genes, and how strongly."
    check, _ = build_capability_check(task, _ask(task, quote, ENTRIES, scale="per_sample", sign=True))
    assert check.results()[0].status == "available" and not check.full_gap


@pytest.mark.parametrize("task,quote", [
    ("We want one network per sample saying whether each TF activates or represses each gene.",
     "one network per sample saying whether each TF activates or represses each gene"),
    ("We want one TF-to-gene network per sample. It must say whether each TF activates or represses its targets.",
     "one TF-to-gene network per sample")])
def test_a_sign_asked_in_the_same_or_another_sentence_still_rules_lioness_panda_out(task, quote):
    check, _ = build_capability_check(task, _ask(task, quote, ENTRIES, scale="per_sample", sign=True))
    assert check.results()[0].status == "not_available"
