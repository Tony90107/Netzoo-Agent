"""ROUND-20: a reply says only the reasons code can verify; with none, it says the result matched no registered workflow.

Each rule is tested on a sentence ROUND-19 found false (said no more) and one it found right (still said).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.capability_check import CapabilityCheck, CheckedRequirement  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import (  # noqa: E402
    _status_line, _why_not, understanding_paragraph,
)
from netzoo_agent_core.interpretation.requirement_split import unmet  # noqa: E402
from netzoo_agent_core.interpretation.stated_reasons import _form_reasons, claim_sentences, stated  # noqa: E402
from netzoo_agent_core.workflow_conditions import UNCLEAR_CHOICE  # noqa: E402

NOT_MATCHED = "-- I couldn't match this to anything a registered NetZoo workflow produces or lets you set."  # harness repair P2: the layer-2 reason


def _row(quote="the network", **fields):
    return CheckedRequirement(quote=quote, kind="result", status="not_available", **fields)


def _no_setting(workflow, words, passed="lambda1 and lambda2"):
    return f'NetZoo\'s {workflow} has no setting for "{words}"; the settings it passes are {passed}'


def _no_settings(workflow, words):
    return (f'NetZoo runs {workflow} with its package defaults and passes no settings to it, so "{words}" cannot be '
            "applied")


def test_b_the_condition_checks_answer_is_never_said():
    # C52: a doable request; the model judged the data description unmet.
    judged = _row(violations=['BONOBO does not meet "The data are log2-transformed and centered per gene"'])
    own = _row(limits=[unmet("DRAGON", "complete continuous values with no NAs")])  # C32 p2, an own-sentence answer
    assert stated(judged) is None and stated(own) is None
    assert _status_line(judged).endswith(NOT_MATCHED) and _status_line(own).endswith(NOT_MATCHED)
    sized = _row(limits=["COBRA requires more genes than samples; the request has 150 genes and 400 samples"])
    assert _why_not(sized) == ["COBRA requires more genes than samples; the request has 150 genes and 400 samples."]


def test_c_words_naming_no_allowed_choice_are_not_a_reason():
    # C40 g4o1: genes_axis words the contract could not settle, said as if BONOBO could not run.
    unclear = (f"BONOBO's genes_axis requires one of auto, rows or columns; \"gene IDs in the first column, sample IDs "
               f"in the header\" {UNCLEAR_CHOICE}")
    assert stated(_row(limits=[unclear])) is None
    lam = "OTTER's lam must be between 0 and 1; \"1.5\" is not"
    assert stated(_row(limits=[unclear, lam])).limits == [lam]


C44 = ('You said "I have no expression file, only that co-expression file."; OTTER needs a TF motif prior and no '
       "registered workflow or tool provides it")
C18 = ('You said "just this expression table"; CONDOR needs a regulator-gene network; every registered route to one '
       '(OTTER, PANDA, PUMA) needs an input you do not have: you said "I don\'t have any motif or PPI files"; OTTER '
       "needs a TF motif prior and no registered workflow or tool provides it")


def test_d_an_input_only_an_only_statement_rules_out_is_not_said():
    # C44: the user named seed_W_mm.tsv; "only that co-expression file" ruled the motif prior out by inference.
    inferred = CapabilityCheck(only_inputs=["coexpression"], only_inputs_quote="only that co-expression file",
                               ruled_out={"expression": "I have no expression file"})
    assert stated(_row(limits=[C44]), inferred) is None
    # C18: the user's own words rule the motif prior out; the network on the way is not the route's end.
    said = CapabilityCheck(ruled_out={"motif_prior": "I don't have any motif or PPI files",
                                      "ppi": "I don't have any motif or PPI files"})
    assert stated(_row(limits=[C18]), said).limits == [C18]
    assert stated(_row(limits=[C18])) is None  # no check: nothing to verify the user's words against


def test_a_no_setting_for_words_that_are_no_setting_is_not_said():
    for words in ("Estimate the lambdas automatically", "write the all-sample matrix to agg_dragon.tsv",
                  "the per-sample table to per_sample_edges.tsv", "start it right away"):  # J20
        assert stated(_row(limits=[_no_setting("LIONESS-DRAGON", words)])) is None, words
    assert stated(_row(limits=[_no_settings("COBRA", "rows match the sample IDs exactly")])) is None  # C57
    assert stated(_row(limits=[_no_setting("OTTER", "header row, gene IDs in the first column")])) is None  # C51
    # C32 p5r: edge_list is an allowed output_format of DRAGON, so "no setting for" it is false either way.
    for words in ("edge list", "edge_list"):
        assert stated(_row(limits=[_no_setting("DRAGON", words, "output_format, lambda1 and lambda2")])) is None
    kept = [_no_settings("GIRAFFE", "learning rate 1e-4"), _no_settings("GIRAFFE", "5,000 iterations"),
            _no_setting("DRAGON", "lambda_inter of 0.2", "output_format, lambda1 and lambda2"),
            _no_setting("OTTER", "L1 (lasso) sparsity penalty", "lam, gamma and iterations"),
            _no_setting("BONOBO", ".parquet file", "bonobo_output_format")]
    for reason in kept:
        assert stated(_row(limits=[reason])).limits == [reason], reason


def test_a_row_with_no_reason_left_offers_no_alternative_either():
    held = _row(limits=[_no_setting("LIONESS-DRAGON", "start it right away")], defaults=["lioness_dragon.per_sample_networks"])
    assert _why_not(held) == [] and _status_line(held).endswith(NOT_MATCHED)
    asked = _row(limits=[_no_settings("GIRAFFE", "learning rate 1e-4")], defaults=["giraffe.signed_regulation"])
    assert any("itself can still run" in reason for reason in _why_not(asked))


def test_e_other_regulators_is_never_the_reason_and_named_classes_still_are():
    assert _form_reasons(_row(attrs={"regulator_kinds": ["tf", "other"]})) == []
    assert any("none models lncRNA regulators" in reason
               for reason in _form_reasons(_row(attrs={"regulator_kinds": ["tf", "lncrna"]})))


def test_e_a_registry_wide_reason_is_said_only_for_a_result_in_its_claims_sentence():
    task = ("Using matched DNA methylation and RNA-seq from 60 colon biopsies, I need a directed network showing whether "
            "each methylation site drives its gene's expression or the other way round, so we can claim causal "
            "regulation in the paper rather than mere correlation. Also cluster the samples.")
    sentences = claim_sentences(task, {"causal": "we can claim causal regulation in the paper rather than mere "
                                                 "correlation"})
    check = CapabilityCheck(claim_sentences=sentences)
    directed = _row("a directed network showing whether each methylation site drives its gene's expression",
                    not_by=["causal_proof"])
    assert _why_not(directed, check) == [
        "Every registered workflow estimates associations or model coefficients from observational data."]
    assert _why_not(_row("cluster the samples", not_by=["causal_proof"]), check) == []
    # C07: a claim the study-purpose reader never verified (a bare set of claims carries no words) is never said.
    assert _why_not(directed, CapabilityCheck(claim_sentences=claim_sentences(task, frozenset({"causal"})))) == []


def test_the_understanding_paragraph_reads_through_the_same_rules():
    check = CapabilityCheck(requirements=[_row("Run OTTER with seed_W_mm.tsv", limits=[C44])],
                            only_inputs=["coexpression"], only_inputs_quote="only that co-expression file")
    # P2 layer 2: the row's own words name OTTER, so what OTTER gives is said after the unmatched sentence
    assert f'"Run OTTER with seed_W_mm.tsv" {NOT_MATCHED} OTTER gives: one weighted TF-to-gene' \
        in understanding_paragraph(check)
