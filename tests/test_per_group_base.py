"""per-group-base-2026-10-29 (live pg1 X10, W20): a result asked once per group is credited to the base entry whose
aggregate network a LIONESS entry also writes; whole_cohort stays as Log 397 set it."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from test_not_stated_fields import _ask  # noqa: E402

from netzoo_agent_core.capability_sheet import SHEET_PATH, load_sheet  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import _fitting  # noqa: E402

BASES = {"lioness_panda.per_sample_networks": "panda.tf_gene_network",
         "lioness_puma.per_sample_networks": "puma.regulator_gene_network",
         "lioness_dragon.per_sample_networks": "dragon.two_layer_network"}


@pytest.mark.parametrize("extension,base", BASES.items())
def test_a_result_per_group_goes_to_the_base_entry(extension, base):
    asked = _ask(scale="per_group", regulator_kinds=[], omics_layers=0)
    assert _fitting([extension], asked) == [base]
    assert _fitting([base, extension], asked) == [base]


def test_other_scales_and_entries_without_a_base_are_unchanged():
    keys = ["lioness_panda.per_sample_networks"]
    assert _fitting(keys, _ask(scale="whole_cohort")) == keys  # Log 397
    assert _fitting(keys, _ask(scale="per_sample")) == keys
    assert _fitting(keys, _ask(scale="unstated")) == keys
    assert _fitting(["lioness_panda.association_tests"], _ask(scale="per_group")) == ["lioness_panda.association_tests"]


def test_the_sheet_rejects_an_aggregate_entry_that_is_not_an_aggregate_result(tmp_path):
    bad = tmp_path / "sheet.yaml"
    bad.write_text(SHEET_PATH.read_text().replace(
        "aggregate_entry: panda.tf_gene_network", "aggregate_entry: lioness_panda.per_sample_targeting", 1))
    with pytest.raises(ValueError, match="bad aggregate_entry"):
        load_sheet(bad)
    assert {k: v.aggregate_entry for k, v in load_sheet().items() if v.aggregate_entry} == BASES
