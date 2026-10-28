"""feature-count-doubts (2026-10-28): a feature count the user gives as candidates, typed `feature_count` in
`unknown_facts`, is judged in code like `count_alternatives` (j2 Q42, j3 R35 shapes)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from test_count_alternatives import KEY, NETWORKS, PANELS, TASK, _networks  # noqa: E402
from test_request_facts import _check  # noqa: E402
from test_method_conditions import _ask  # noqa: E402


def _doubt(quote, values, about="feature_count", kind="choices"):
    return {"about": about, "quote": quote, "count_kind": kind, "count_values": list(values)}


def test_a_feature_doubt_typed_as_a_feature_count_is_judged_per_candidate():
    check = _check(TASK, _networks(features=[(300, "300 serum miRNAs")]), unknown_facts=[_doubt(PANELS, (200, 2000))])
    (row,) = check.results()
    assert (row.status, row.depends_on, row.by_code) == ("needs_fact", "feature_count", True)
    assert row.method["samples"] == 50  # the stated patients stay
    assert row.outcomes == {"200": [KEY], "2000": []}
    assert not check.unknowns  # never a fixed-dimension ask as well


def test_r35_shape_second_layer_candidates_against_the_value_cap():
    task = ("Build a LIONESS-DRAGON network for each of our 100 colon tissue samples, with layer one being 300 "
            "proteins. I'm not sure whether the metabolite layer will end up with 200 or 600 metabolites after QC.")
    doubt = "whether the metabolite layer will end up with 200 or 600 metabolites after QC"
    ask = _ask("Build a LIONESS-DRAGON network for each of our 100 colon tissue samples", [KEY], samples=100,
               samples_quote="100 colon tissue samples", omics_layers=2, scale="per_sample",
               features=[(300, "300 proteins")])
    (row,) = _check(task, ask, unknown_facts=[_doubt(doubt, (200, 600))]).results()
    # 500 features: 124,750 pairs x 100 = 12,475,000 values; 900: 404,550 x 100 = 40,455,000 > 20,000,000.
    assert (row.status, row.depends_on, row.by_code) == ("needs_fact", "feature_count", True)
    assert row.outcomes == {"200": [KEY], "600": []}


def test_q42_shape_gene_candidates_against_cobras_genes_and_samples():
    task = ("Run COBRA on our 150 adipose samples to get covariate components. I can't remember whether the "
            "filtered matrix kept 120 genes or 2,000 genes.")
    doubt = "whether the filtered matrix kept 120 genes or 2,000 genes"
    key = "cobra.covariate_components"
    ask = _ask("Run COBRA on our 150 adipose samples to get covariate components", [key], named="COBRA",
               named_quote="COBRA", samples=150, samples_quote="150 adipose samples")
    (row,) = _check(task, ask, unknown_facts=[_doubt(doubt, (120, 2000))]).results()
    assert (row.status, row.depends_on, row.by_code) == ("needs_fact", "feature_count", True)
    assert row.method["samples"] == 150
    assert row.outcomes == {"120": [], "2000": [key]}  # COBRA needs more genes than samples (cobra.py)


def test_candidates_not_in_the_quote_are_ignored():
    check = _check(TASK, _networks(features=[(300, "300 serum miRNAs")]), unknown_facts=[_doubt(PANELS, (200, 3000))])
    (row,) = check.results()
    assert row.status != "needs_fact" or row.depends_on != "feature_count"
    assert not any(f.property == "feature_count" and f.state == "unsure" for f in check.facts)


def test_a_feature_doubt_without_candidates_is_no_fixed_dimension():
    check = _check(TASK, _networks(features=[(300, "300 serum miRNAs")]),
                   unknown_facts=[_doubt(PANELS, (), kind="unspecified")])
    assert not check.unknowns
    assert not any(f.property == "feature_count" and f.state == "unsure" for f in check.facts)


def test_x22_shape_a_feature_sized_layer_count_is_judged_as_features():
    """layer-count-features-2026-10-29 (j6 X22): "150 or 400 metabolites" typed omics_layers is a feature count."""
    task = ("We have 100 breast tumors with 400 transcript features and a metabolite panel measured on the same tumors, "
            "and we want LIONESS-DRAGON networks for every tumor. I don't know yet whether the metabolomics core used "
            "their 150-metabolite panel or their 400-metabolite panel.")
    doubt = "whether the metabolomics core used their 150-metabolite panel or their 400-metabolite panel"
    ask = _ask("we want LIONESS-DRAGON networks for every tumor", [KEY], samples=100, samples_quote="100 breast tumors",
               omics_layers=2, scale="per_sample", features=[(400, "400 transcript features")])
    check = _check(task, ask, unknown_facts=[_doubt(doubt, (150, 400), about="omics_layers")])
    (row,) = check.results()
    # 550 features: 150,975 pairs x 100 = 15,097,500 values; 800: 319,600 x 100 = 31,960,000 > 20,000,000.
    assert (row.status, row.depends_on, row.by_code) == ("needs_fact", "feature_count", True)
    assert row.outcomes == {"150": [KEY], "400": []}
    assert not check.unknowns


def test_a_small_layer_count_doubt_is_unchanged():
    task = "We want one partial-correlation network. I'm not sure whether we have one or two omics layers."
    ask = _ask("We want one partial-correlation network", [KEY], samples=50, samples_quote="50", omics_layers=2)
    check = _check(task, ask, unknown_facts=[_doubt("whether we have one or two omics layers", (1, 2),
                                                    about="omics_layers")])
    assert not any(f.property == "feature_count" and f.state == "unsure" for f in check.facts)
