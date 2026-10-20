"""ROUND-07 (collab/ROUND-07-PLAN.md): a count the user left in doubt stays in doubt until the files or the user settle it.

G1: a count the reading wrote as one number whose words give another beside it ("two or ten samples") is kept as the
user's candidates, never as that number. G2: a stated count the doubt set aside is recorded as set aside. G3: the
expression file the request names answers a sample-count doubt -- only when its count is one of the candidates, and
only for a request asking one result.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from test_method_conditions import _ask  # noqa: E402
from test_request_facts import _facts, _proposal  # noqa: E402

from netzoo_agent_core.interpretation.capability_check import build_capability_check, understanding_paragraph  # noqa: E402
from netzoo_agent_core.interpretation.count_words import side_by_side_values  # noqa: E402
from netzoo_agent_core.interpretation.input_bindings import bound_expression_samples  # noqa: E402
from netzoo_agent_core.interpretation.veto_evidence import _side_by_side  # noqa: E402

KEY = "lioness_panda.per_sample_networks"
TASK = "Build a LIONESS-PANDA network for each sample in tumour_expression.tsv; it holds two or ten samples."
ASKED = "Build a LIONESS-PANDA network for each sample in tumour_expression.tsv"


def _networks(samples=2, quote="two or ten samples"):
    return _ask(ASKED, [KEY], scale="per_sample", regulator_kinds=["tf"], samples=samples, samples_quote=quote)


def _check(task, *asks, counted=None, **conditions):
    check, rejected = build_capability_check(task, _proposal(task, *asks, **conditions), counted_samples=counted)
    assert not rejected, rejected
    return check


# -- G1: side by side --------------------------------------------------------------------------------------------

def test_side_by_side_numbers_are_candidates_and_quantities_of_different_things_are_not():
    assert side_by_side_values("either 8 or 15 tumours", 8) == [8, 15]
    assert side_by_side_values("8-15 tumours", 15) == [8, 15]
    assert side_by_side_values("two or ten paired samples", 2) == [2, 10]
    assert side_by_side_values("88 donors: 44 AD, 44 controls", 88) == []
    assert side_by_side_values("88 donors: 44 AD, 44 controls", 44) == []
    assert side_by_side_values("6 tumours x 900 genes", 6) == []
    assert side_by_side_values("rna_85.csv holds 85 samples", 85) == []


def test_the_veto_layer_reads_the_same_rule():
    assert _side_by_side("either 8 or 15 tumours", 8.0)
    assert not _side_by_side("88 donors: 44 AD, 44 controls", 88.0)


def test_one_number_of_two_side_by_side_is_the_users_candidates_not_the_count():
    """Before ROUND-07 the 2 was stated and LIONESS-PANDA (at least 3 samples) was ruled out."""
    (row,) = _check(TASK, _networks()).results()
    assert (row.status, row.by_code, row.depends_on) == ("needs_fact", True, "sample_count")
    assert row.outcomes == {"2": [], "10": [KEY]}
    assert "samples" not in row.method


def test_the_candidates_are_one_fact_with_the_readings_own_candidates():
    check = _check(TASK, _networks(), count_alternatives=[{"of": "samples", "quote": "two or ten samples",
                                                           "values": [2, 10]}])
    [fact] = _facts(check, "sample_count")
    assert fact.state == "unsure" and fact.values == ["2", "10"]
    assert [e.reader for e in fact.evidence] == ["count_alternatives", "side_by_side"]
    assert check.results()[0].status == "needs_fact"


def test_quantities_of_different_things_stay_a_stated_count():
    task = "Build a LIONESS-PANDA network for each donor in alzheimer_expression.tsv (88 donors: 44 AD, 44 controls)."
    ask = _ask("Build a LIONESS-PANDA network for each donor in alzheimer_expression.tsv", [KEY], scale="per_sample",
               regulator_kinds=["tf"], samples=88, samples_quote="88 donors: 44 AD, 44 controls")
    (row,) = _check(task, ask).results()
    assert row.status == "available" and row.method["samples"] == 88


# -- G2: the doubt is recorded as winning ---------------------------------------------------------------------------

PANEL_TASK = ("We want a separate miRNA-protein partial-correlation network for each of our 50 patients, from 300 "
              "serum miRNAs and a plasma proteomics panel. I don't remember whether the proteomics is the 200-protein "
              "targeted panel or the 2,000-protein discovery panel.")
PANELS = "the 200-protein targeted panel or the 2,000-protein discovery panel"


def test_a_stated_count_inside_the_candidates_words_is_recorded_as_set_aside():
    ask = _ask("a separate miRNA-protein partial-correlation network for each of our 50 patients",
               ["lioness_dragon.per_sample_networks"], samples=50, samples_quote="50 patients", omics_layers=2,
               scale="per_sample", features=[(300, "300 serum miRNAs"), (2000, "2,000-protein")])
    check = _check(PANEL_TASK, ask, count_alternatives=[{"of": "features", "quote": PANELS, "values": [200, 2000]}])
    assert check.results()[0].status == "needs_fact"
    [conflict] = check.fact_conflicts
    assert conflict.reason == "unsure_candidates" and conflict.property == "feature_count"
    stated = next(fact for fact in check.facts if fact.id in conflict.set_aside)
    unsure = next(fact for fact in check.facts if fact.id in conflict.used)
    assert stated.value == "2000" and unsure.values == ["200", "2000"]


def test_a_stated_count_beside_a_count_the_user_does_not_know_is_recorded_as_set_aside():
    task = ("Build a LIONESS-PANDA network for each of the 12 samples in tumour_expression.tsv. I do not know how "
            "many samples will pass quality control.")
    ask = _ask("Build a LIONESS-PANDA network for each of the 12 samples in tumour_expression.tsv", [KEY],
               scale="per_sample", regulator_kinds=["tf"], samples=12, samples_quote="the 12 samples")
    check = _check(task, ask, unknown_facts=[{"quote": "I do not know how many samples will pass quality control",
                                              "about": "sample_count", "count_kind": "unspecified", "count_values": [],
                                              "applies_to": None}])
    assert "samples" not in check.results()[0].method
    [conflict] = check.fact_conflicts
    assert (conflict.reason, conflict.used) == ("unsure_candidates", [])
    [stated] = [fact for fact in check.facts if fact.id in conflict.set_aside]
    assert stated.value == "12" and stated.state == "stated"


# -- G3: the named file answers -------------------------------------------------------------------------------------

def _expression(folder: Path, samples: int, name="tumour_expression.tsv") -> Path:
    rows = ["gene\t" + "\t".join(f"S{i}" for i in range(1, samples + 1))]
    rows += [f"G{g}\t" + "\t".join(str((g * i) % 7 + 0.5) for i in range(1, samples + 1)) for g in range(1, 6)]
    path = folder / name
    path.write_text("\n".join(rows) + "\n")
    return path


def test_the_named_expression_file_is_counted_as_preflight_counts_it(tmp_path):
    _expression(tmp_path, 10)
    assert bound_expression_samples(TASK, tmp_path) == (10, "tumour_expression.tsv")
    assert bound_expression_samples(TASK.replace("tumour_expression.tsv", "missing_expression.tsv"), tmp_path) is None


def test_a_file_count_among_the_candidates_settles_the_doubt():
    check = _check(TASK, _networks(), counted=(10, "tumour_expression.tsv"))
    (row,) = check.results()
    assert row.status == "available" and row.delivered_by == [KEY]
    assert row.method["samples"] == 10 and row.method["samples_file"] == "tumour_expression.tsv"
    assert "sample_count@file:tumour_expression.tsv" in row.fact_ids
    [conflict] = check.fact_conflicts
    assert (conflict.reason, conflict.used) == ("settled_by_file", ["sample_count@file:tumour_expression.tsv"])
    file_fact = next(fact for fact in check.facts if fact.origin == "file")
    assert file_fact.value == "10" and file_fact.evidence[0].reader == "input_file"
    assert "tumour_expression.tsv has 10 samples (counted from the file)" in understanding_paragraph(check)


def test_a_file_count_the_user_did_not_give_settles_nothing():
    check = _check(TASK, _networks(), counted=(7, "tumour_expression.tsv"))
    (row,) = check.results()
    assert row.status == "needs_fact" and "samples_file" not in row.method
    [conflict] = check.fact_conflicts
    assert conflict.reason == "file_disagrees" and conflict.set_aside == ["sample_count@file:tumour_expression.tsv"]


def test_a_file_count_answers_a_count_the_user_does_not_know():
    task = "Build a LIONESS-PANDA network for each sample in tumour_expression.tsv. I do not know how many samples it has."
    ask = _ask(ASKED, [KEY], scale="per_sample", regulator_kinds=["tf"])
    unknown = [{"quote": "I do not know how many samples it has", "about": "sample_count", "count_kind": "unspecified",
                "count_values": [], "applies_to": None}]
    (row,) = _check(task, ask, counted=(2, "tumour_expression.tsv"), unknown_facts=unknown).results()
    assert row.status == "not_available" and row.method["samples"] == 2  # LIONESS needs at least 3
    assert any("at least 3 samples" in limit for limit in row.limits)


def test_a_file_count_outside_an_unknown_counts_candidates_settles_nothing():
    task = "Build a LIONESS-PANDA network for each sample in tumour_expression.tsv. I am not sure if it has 8 or 15 samples."
    ask = _ask(ASKED, [KEY], scale="per_sample", regulator_kinds=["tf"])
    unknown = [{"quote": "I am not sure if it has 8 or 15 samples", "about": "sample_count", "count_kind": "choices",
                "count_values": [8, 15], "applies_to": None}]
    settled = _check(task, ask, counted=(15, "tumour_expression.tsv"), unknown_facts=unknown).results()[0]
    assert settled.method.get("samples_file") == "tumour_expression.tsv" and settled.method["samples"] == 15
    other = _check(task, ask, counted=(20, "tumour_expression.tsv"), unknown_facts=unknown)
    assert "samples_file" not in other.results()[0].method
    assert [conflict.reason for conflict in other.fact_conflicts] == ["file_disagrees"]


def test_a_stated_count_is_never_replaced_by_the_file():
    task = "Build a LIONESS-PANDA network for each of the 12 samples in tumour_expression.tsv."
    ask = _ask("Build a LIONESS-PANDA network for each of the 12 samples in tumour_expression.tsv", [KEY],
               scale="per_sample", regulator_kinds=["tf"], samples=12, samples_quote="the 12 samples")
    check = _check(task, ask, counted=(2, "tumour_expression.tsv"))
    (row,) = check.results()
    assert row.method["samples"] == 12 and "samples_file" not in row.method
    assert not any(fact.origin == "file" for fact in check.facts)


def test_with_several_results_the_file_settles_nothing():
    task = ("Build a LIONESS-PANDA network for each sample in tumour_expression.tsv; it holds two or ten samples. "
            "Also build one OTTER network for the normal tissue.")
    other = _ask("Also build one OTTER network for the normal tissue", ["otter.tf_gene_network"],
                 scale="whole_cohort", regulator_kinds=["tf"])
    check = _check(task, _networks(), other, counted=(10, "tumour_expression.tsv"))
    lioness = next(row for row in check.results() if KEY in row.delivered_by or row.status == "needs_fact")
    assert lioness.status == "needs_fact" and "samples_file" not in lioness.method
    assert not any(fact.origin == "file" for fact in check.facts)
