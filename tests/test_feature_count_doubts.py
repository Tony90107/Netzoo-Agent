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
