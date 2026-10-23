"""G6 (feasibility eval F23, F25): a result a typed attribute rules out says why, from the capability sheet."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.capability_check import CheckedRequirement  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import _line  # noqa: E402

PLAIN = {"scale": "unstated", "omics_layers": 0, "data_unit": "not_stated", "regulator_kinds": [], "needs_sign": False,
         "input_network": "none", "group_membership": "not_about_groups", "time_model": "not_dynamic",
         "spatial": "not_spatial"}


def _gap(quote="the result", **attrs):
    return CheckedRequirement(quote=quote, kind="result", status="not_available", attrs={**PLAIN, **attrs},
                              blank=True)


def test_each_ruled_out_form_says_why():
    cases = {
        "spatial": ({"spatial": "uses_neighbors"}, "uses where samples sit in space"),
        "overlap": ({"group_membership": "several_groups"}, "none returns overlapping memberships"),
        "dynamic": ({"time_model": "dynamic"}, "from one time point to the next"),
        "cells": ({"data_unit": "single_cells"}, "none models single cells"),
        "lncrna": ({"regulator_kinds": ["tf", "lncrna"]}, "none models lncRNA regulators"),
    }
    for name, (attrs, words) in cases.items():
        line = _line(_gap(**attrs))
        assert line.startswith('"the result" -- not available here: no registered workflow produces this. '), name
        assert words in line, name


def test_a_gap_no_attribute_explains_stays_unmatched():
    assert _line(_gap()) == ('"the result" -- I couldn\'t match this to anything a registered NetZoo workflow produces '
                             'or lets you set.')
    assert _line(_gap(omics_layers=3, regulator_kinds=["tf", "mirna"], data_unit="bulk_samples")) == _line(_gap())


def test_two_reasons_at_most_and_none_on_an_available_result():
    line = _line(_gap(spatial="uses_neighbors", time_model="dynamic", data_unit="single_cells"))
    assert "space" in line and "time point" in line and "single cells" not in line
    available = CheckedRequirement(quote="x", kind="result", status="available", attrs={**PLAIN, "spatial": "uses_neighbors"},
                                   delivered_by=["panda.tf_gene_network"])
    assert "space" not in _line(available)
