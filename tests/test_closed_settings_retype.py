"""Class 4 (docs/research-log/excluded-entries-2026-11-01/ROUND-C4.md): a setting typed onto a control the user does
not set is set apart (j11 C34), never when the value binds or the words may be a control the workflow takes."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_m3_method_fitting import _check, _settings  # noqa: E402
from test_method_conditions import _ask  # noqa: E402

from netzoo_agent_core.interpretation.closed_settings_retype import retyped  # noqa: E402

C34 = ("Please run PANDA on our 120 breast tumour RNA-seq samples with the human motif prior and PPI file to get the "
       "aggregate TF-gene network. I'd also like the update step alpha set to 0.25 instead of the default.")
ALPHA = "the update step alpha set to 0.25 instead of the default"
S1 = ("Please run PANDA on our 120 breast tumour RNA-seq samples with the human motif prior and PPI file to get the "
      "aggregate TF-gene network.")
S2 = "I'd also like the update step alpha set to 0.25 instead of the default."


def _c34(value="0.25"):
    setting = ("PANDA.with_header", ALPHA, value)
    ask = _ask("to get the aggregate TF-gene network", ["panda.tf_gene_network"], named="PANDA", named_quote="run PANDA",
               scale="whole_cohort", data_unit="bulk_samples", input_network="regulator_gene", settings=[setting])
    return _check(C34, ask, named_method="PANDA", named_method_quote="run PANDA", settings=_settings(setting))


def _read(with_header="not_stated", other="set", **set_controls):
    answers = {"with_header": {"choice": with_header, "confidence": 0.9},
               "other": {"choice": other, "confidence": 0.9}}
    picks = {"other": {"choice": "s2", "confidence": 0.9}}
    for name in set_controls:
        answers[name] = {"choice": "set", "confidence": 0.9}
        picks[name] = {"choice": "s2", "confidence": 0.9}
    return {"answers": answers, "picks": picks, "sentences": {"s1": S1, "s2": S2}}


def test_c34_alpha_typed_as_with_header_is_set_apart():
    check = _c34()
    after, changes = retyped(check, C34, _read())
    assert [c["setting"] for c in changes] == ["PANDA.with_header"]
    run = next(row for row in after.results() if row.delivered_by)
    assert run.status == "available" and not run.method.get("settings")
    assert run.method["settings_apart"] == [ALPHA]
    assert not any(fid.startswith("setting:PANDA.with_header@") for fid in run.fact_ids)
    [apart] = [row for row in after.results() if row.quote == ALPHA]
    assert apart.status == "not_available" and apart.blocks == ["PANDA"] and apart.defaults == ["panda.tf_gene_network"]
    assert apart.limits[0].startswith('NetZoo\'s PANDA has no setting for "the update step alpha')


def test_no_change_when_the_value_binds_or_jev_disagrees():
    assert retyped(_c34("true"), C34, _read())[1] == []  # a value the control takes: never removed
    assert retyped(_c34(), C34, _read(with_header="set"))[1] == []
    assert retyped(_c34(), C34, _read(other="not_stated"))[1] == []


def test_no_change_when_a_control_the_workflow_takes_is_read_in_that_sentence():
    # with_header is PANDA's only wired control; a set read of it in that sentence keeps the setting
    read = _read()
    read["answers"]["with_header"] = {"choice": "set", "confidence": 0.9}
    read["picks"]["with_header"] = {"choice": "s2", "confidence": 0.9}
    assert retyped(_c34(), C34, read)[1] == []


def test_a_reasonless_row_holding_the_words_takes_the_line():
    # j11 C34 m2: the alpha sentence is also an uncredited ask (layer-2 line); it takes the line, no second row
    setting = ("PANDA.with_header", ALPHA, "0.25")
    ask = _ask("to get the aggregate TF-gene network", ["panda.tf_gene_network"], named="PANDA", named_quote="run PANDA",
               scale="whole_cohort", data_unit="bulk_samples", input_network="regulator_gene", settings=[setting])
    alone = _ask(S2, [], settings=[setting])
    check = _check(C34, ask, alone, named_method="PANDA", named_method_quote="run PANDA", settings=_settings(setting))
    assert [row.status for row in check.results()] == ["available", "not_available"]
    after, changes = retyped(check, C34, _read())
    assert len(changes) == 1 and len(after.results()) == 2
    run, words = after.results()
    assert not run.method.get("settings") and words.quote == S2
    assert words.limits[0].startswith("NetZoo's PANDA has no setting for") and words.blocks == ["PANDA"]
