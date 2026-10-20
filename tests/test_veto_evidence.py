"""ROUND-02 (collab/ROUND-02-PLAN.md): the evidence the contract veto leans on (no model calls).

A: each count and data fact keeps its own words, the data it counts, and the corrections code verified.
B: a count its words do not back is never judged; the toolkit's name is no method; a question keeps only what its words
   support. C: the ledger lists every cell, read or not. D: an input the contract does not take is refused only when
   the user asks to give it to that workflow. Synthetic English requests only; the h1-h4 items stay in the research log.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contract_text import file_checkable  # noqa: E402
from netzoo_agent_core.contracts.slim_reading import Evidence, SlimReading, Stated  # noqa: E402
from netzoo_agent_core.interpretation.contract_veto import (  # noqa: E402
    VetoQuestion, _question, contract_veto, vetoed_core,
)
from netzoo_agent_core.interpretation.menu_requirements import _policy  # noqa: E402
from netzoo_agent_core.interpretation.menu_reader import request_layout  # noqa: E402
from netzoo_agent_core.interpretation.slim_reader import Needs, from_core, merge_focus  # noqa: E402
from netzoo_agent_core.interpretation.veto_evidence import backed_questions, count_backing, veto_ledger  # noqa: E402
from netzoo_agent_core.method_names import PROJECT_IDENTITIES, is_project_identity  # noqa: E402

ROOT = Path(__file__).parents[1]


def count(what, quote, value=None, values=(), layer="", belongs_to="", corrects=None) -> dict:
    return {"what": what, "layer": layer, "value": value, "values": list(values), "quote": quote,
            "belongs_to": belongs_to, "corrects": corrects}


def merged(task: str, counts: list[dict], names=("sample_count", "feature_count")) -> SlimReading:
    needs = Needs(candidates=("LIONESS-DRAGON",), counts=names)
    slim, _report = merge_focus(SlimReading(), {"settings": [], "counts": counts}, task, needs)
    return slim


def stated(slim: SlimReading, name: str) -> Stated:
    return next(f for f in slim.stated if f.name == name)


def setting(control: str, value: str, quote: str, workflow: str) -> Stated:
    return Stated(field="B5", name=control, value=value, quote=quote, workflow=workflow)


def do(*workflows: str):
    from netzoo_agent_core.contracts.core_decision import CoreDecision
    return CoreDecision(kind="DO", basis="results_given", workflows=list(workflows), run_allowed=True)


# --- A1: counts keep their words and what they count ------------------------------------------------------------------

TWO_LAYERS = ("Run LIONESS-DRAGON on rna.csv (40 samples x 250 genes) and atac.csv for the same 40 samples. I don't "
              "know if atac.csv is the 250-peak subset or the 4,000-peak export.")


def test_a_doubt_in_one_layer_stays_that_layers_options_and_the_total_is_codes():
    slim = merged(TWO_LAYERS, [
        count("samples", "40 samples", 40),
        count("features", "250 genes", 250, layer="rna", belongs_to="rna.csv"),
        count("features", "the 250-peak subset or the 4,000-peak export", values=(250, 4000), layer="atac",
              belongs_to="atac.csv")])
    total = stated(slim, "feature_count")
    assert total.values == ["500", "4250"] and total.derived == "250 + 250 or 4,000"
    assert total.quote == "the 250-peak subset or the 4,000-peak export"  # the words of the doubt, not "250 genes"
    roles = {(e.belongs_to, e.role) for e in total.evidence}
    assert roles == {("rna.csv", "operand"), ("atac.csv", "alternative")}


def test_versions_of_one_layer_are_never_added_and_a_restated_count_is_counted_once():
    task = "expr.tsv has 300 genes; yes, 300 genes, all of them in expr.tsv."
    slim = merged(task, [count("features", "300 genes", 300, layer="expression", belongs_to="expr.tsv"),
                         count("features", "300 genes, all of them", 300, layer="expression")])
    assert stated(slim, "feature_count").value == "300" and stated(slim, "single_feature_count").value == "300"


def test_a_verified_correction_retires_the_earlier_count_and_keeps_it_for_the_audit():
    task = "We have 48 tumour samples. Sorry, after QC it is 46 samples."
    slim = merged(task, [count("samples", "48 tumour samples", 48), count("samples", "it is 46 samples", 46, corrects=1)])
    fact = stated(slim, "sample_count")
    assert fact.value == "46"
    [old] = [e for e in fact.evidence if e.role == "corrected"]
    assert old.quote == "48 tumour samples" and old.corrected_by == "it is 46 samples"


def test_a_correction_code_cannot_verify_keeps_the_conflict():
    task = "It is 46 samples. Earlier I said 48 samples."
    # "46" claims to correct "48", whose words come later in the request: not a correction code can verify.
    slim = merged(task, [count("samples", "48 samples", 48), count("samples", "46 samples", 46, corrects=1)])
    assert stated(slim, "sample_count").values == ["46", "48"]


# --- A2: data -----------------------------------------------------------------------------------------------------

def core(task: str, data: list[dict]) -> SlimReading:
    payload = {"items": [], "data": data, "only_these": "", "run": "ask", "run_quote": "", "facts": [],
               "unregistered_methods": []}
    slim, _report = from_core(payload, task, request_layout(task))
    return slim


def datum(kind, status, quote, input_for="", corrects=None) -> dict:
    return {"kind": kind, "status": status, "quote": quote, "input_for": input_for, "corrects": corrects}


def test_not_knowing_whether_a_file_holds_expression_is_never_lacking_it():
    slim = core("I'm not sure counts.tsv is expression at all.", [datum("expression", "unsure", "counts.tsv")])
    assert [(d.name, d.value) for d in slim.data] == [("expression", "unsure")]
    verdict = contract_veto(slim, ["PANDA"])
    assert verdict.violations == {} and any(q.dimension.startswith("data:") for q in verdict.questions)


def test_have_and_lack_both_stated_without_a_verified_correction_is_a_conflict_kept_as_unsure():
    task = "We have no motif prior. We do have motif_hs.txt."
    slim = core(task, [datum("motif_prior", "lacks", "We have no motif prior"),
                       datum("motif_prior", "has", "motif_hs.txt")])
    assert slim.data[0].value == "unsure" and len(slim.data[0].evidence) == 2
    corrected = core(task, [datum("motif_prior", "lacks", "We have no motif prior"),
                            datum("motif_prior", "has", "motif_hs.txt", corrects=1)])
    assert corrected.data[0].value == "has"
    assert [e.role for e in corrected.data[0].evidence] == ["corrected", "value"]


def test_input_for_must_be_a_registered_name_in_the_request():
    task = "Feed adjusted.tsv into LIONESS-PANDA."
    slim = core(task, [datum("coexpression_matrix", "has", "adjusted.tsv", input_for="TIGER")])
    assert slim.data[0].workflow == ""
    slim = core(task, [datum("coexpression_matrix", "has", "adjusted.tsv", input_for="LIONESS-PANDA")])
    assert slim.data[0].workflow == "LIONESS-PANDA"


# --- B1: a count its words do not back is never judged ------------------------------------------------------------

def sambar(sample_quote: str, samples: str) -> SlimReading:
    return SlimReading(stated=[setting("kmin", "2", "trying 2 to 10 subtypes", "SAMBAR"),
                               setting("kmax", "10", "trying 2 to 10 subtypes", "SAMBAR"),
                               Stated(field="B6", name="sample_count", value=samples, quote=sample_quote)])


def test_a_count_given_two_ways_and_read_as_one_never_vetoes_even_through_a_setting_rule():
    verdict = contract_veto(sambar("the matrix has either 8 or 15 tumours", "8"), ["SAMBAR"])
    assert verdict.violations == {}
    assert verdict.set_aside and "another number beside it" in verdict.set_aside[0]
    assert vetoed_core(do("SAMBAR"), verdict).kind != "DECLINE"


def test_a_count_with_other_quantities_in_its_words_still_vetoes():
    verdict = contract_veto(sambar("(6 tumours x 900 genes, non-negative counts)", "6"), ["SAMBAR"])
    [violation] = verdict.violations["SAMBAR"]
    assert "kmax" in violation.reason and verdict.set_aside == []


@pytest.mark.parametrize("quote, value, backed", [
    ("8-15 tumours", "8", False),
    ("8, 15 tumours", "8", False),
    ("rna_85.csv (85 samples x 300 genes)", "85", True),  # the 85 in the file name is no number of the request's
    ("120 samples", "200", False),  # not in its own words
])
def test_count_backing(quote, value, backed):
    fact = Stated(field="B6", name="sample_count", value=value, quote=quote)
    assert (count_backing(fact) == "") is backed


def test_a_derived_total_must_be_the_sum_of_parts_each_in_its_own_words():
    good = [Evidence(quote="2,000 transcripts", values=["2000"], role="operand"),
            Evidence(quote="500 proteins", values=["500"], role="operand")]
    assert count_backing(Stated(field="B6", name="feature_count", value="2500", derived="2,000 + 500",
                                evidence=good)) == ""
    assert count_backing(Stated(field="B6", name="feature_count", value="3000", derived="2,000 + 500",
                                evidence=good)) != ""


# --- B2: the toolkit's own name -----------------------------------------------------------------------------------

def test_the_toolkits_own_name_is_no_unregistered_method_but_a_method_beside_it_is():
    assert contract_veto(SlimReading(unregistered_methods=["NetZoo"]), ["PUMA"]).violations == {}
    [violation] = contract_veto(SlimReading(unregistered_methods=["NetZoo-TIGER"]), ["PUMA"]).violations["PUMA"]
    assert violation.kind == "C5"
    assert not is_project_identity("the standard NetZoo analysis")


def test_project_identities_are_the_package_the_dockerfile_installs():
    clone = re.search(r"git clone https://github.com/([^/\s]+)/([^/\s.]+)", (ROOT / "Dockerfile").read_text()).groups()
    assert set(PROJECT_IDENTITIES) == set(clone)


# --- B3: a question keeps only what its words support --------------------------------------------------------------

def test_a_category_doubt_on_a_counts_doubt_words_is_set_aside_and_the_count_question_asks_the_part():
    doubt = "the 250-peak subset or the 4,000-peak export"
    total = Stated(field="B6", name="feature_count", values=["500", "4250"], quote=doubt, derived="250 + 250 or 4,000",
                   evidence=[Evidence(quote="250 genes", values=["250"], belongs_to="rna.csv", role="operand"),
                             Evidence(quote=doubt, values=["250", "4000"], belongs_to="atac.csv", role="alternative")])
    slim = SlimReading(stated=[total])
    questions = [VetoQuestion("LIONESS-DRAGON", "value_type", ("continuous", "binary"), doubt, ("binary",)),
                 VetoQuestion("LIONESS-DRAGON", "feature_count", ("500", "4250"), doubt, ("4250",))]
    kept, notes = backed_questions(questions, slim)
    assert [q.dimension for q in kept] == ["feature_count"] and "doubt of feature_count" in notes[0]
    text = _question(kept[0])
    assert text.startswith("How many features are in atac.csv: 250 or 4000?") and "500 or 4250" in text


def test_legacy_questions_are_kept_but_marked_and_questions_without_user_words_are_kept():
    slim = SlimReading(stated=[Stated(field="B6", name="feature_count", values=["600", "5300"], quote="300 genes")])
    questions = [VetoQuestion("LIONESS-DRAGON", "feature_count", ("600", "5300"), "300 genes", ("5300",)),
                 VetoQuestion("BONOBO", "setting:BONOBO.log_transformed", ("true", "false"), "", ("false",))]
    kept, notes = backed_questions(questions, slim)
    assert [q.evidence for q in kept] == ["legacy_unverified", ""] and notes == []


# --- C: the ledger ------------------------------------------------------------------------------------------------

def test_the_ledger_lists_every_cell_read_or_not_and_never_passes_a_veto_that_did_not_run():
    slim = SlimReading(stated=[setting("lambda1", "0.3", "fix lambda1 at 0.3", "DRAGON")])
    verdict = contract_veto(slim, ["DRAGON"], "Run DRAGON; fix lambda1 at 0.3")
    ledger = veto_ledger(["DRAGON"], "checked", slim, (), verdict)
    rows = {row["cell"]: row for row in ledger["cells"]}
    assert rows["setting:DRAGON.lambda1"]["read"] == "read" and rows["setting:DRAGON.lambda1"]["judged"] == "violate"
    assert rows["setting:DRAGON.lambda2"]["read"] == "not_mentioned"  # judged with lambda1: the pair rule names it
    assert rows["setting:DRAGON.output_format"]["read"] == "not_mentioned"
    assert rows["setting:DRAGON.output_format"]["judged"] == "not_evaluated"
    assert rows["setting:DRAGON.lambda1"]["legacy"] is True  # a hand-made fact without evidence
    failed = veto_ledger(["DRAGON"], "read_failed")
    assert failed["status"] == "read_failed" and {r["read"] for r in failed["cells"]} == {"not_run"}


# --- D: an input the contract does not take -------------------------------------------------------------------------

def test_an_aggregate_coexpression_matrix_given_to_lioness_panda_is_refused_with_the_contracts_words():
    task = "Feed adjusted_coexpression.tsv into LIONESS-PANDA as its co-expression input."
    slim = core(task, [datum("coexpression_matrix", "has", "adjusted_coexpression.tsv", input_for="LIONESS-PANDA")])
    [violation] = contract_veto(slim, ["LIONESS-PANDA"]).violations["LIONESS-PANDA"]
    assert violation.kind == "C8" and violation.user_quote == "adjusted_coexpression.tsv"
    assert violation.contract_quote == "An aggregate COBRA adjusted co-expression artifact is not a direct LIONESS handoff"


def test_raw_expression_for_lioness_panda_and_a_mentioned_cobra_result_are_not_refused():
    task = "COBRA gave us adjusted.tsv earlier. Run LIONESS-PANDA on expr.tsv with motif.txt and ppi.txt."
    slim = core(task, [datum("coexpression_matrix", "has", "adjusted.tsv"),
                       datum("expression", "has", "expr.tsv", input_for="LIONESS-PANDA")])
    assert contract_veto(slim, ["LIONESS-PANDA"]).violations == {}


def test_a_refused_input_is_a_request_level_check_no_file_inspection_settles():
    checks = _policy().workflows["run_lioness_panda"].input_checks
    refused = [c for c in checks if getattr(c, "limit", "").startswith("refuses_input:")]
    assert refused and not any(file_checkable(c) for c in refused)
    assert all(file_checkable(c) for c in checks if c not in refused)
