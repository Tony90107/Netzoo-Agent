"""ROUND-22 (R22-B): numbers a named workflow's result states that nothing read are read once against that workflow's
numeric settings; code keeps a setting only for those numbers, and the workflow's own rules judge it."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.capability_check import CapabilityCheck, CheckedRequirement  # noqa: E402
from netzoo_agent_core.contracts.request_facts import RequestFact  # noqa: E402
from netzoo_agent_core.interpretation.settings_read import (  # noqa: E402
    settings_read_model, settings_read_triggers, unread_numbers, with_settings_read,
)

M25 = ("Set SAMBAR going on mut_pilot.csv (6 tumours x 900 genes, non-negative counts), exon_sizes.csv and "
       "h.all.v2023.gmt, trying anywhere from 2 to 8 subtypes.")


def _check(task=M25, samples=6):
    row = CheckedRequirement(quote=task, kind="result", status="available", delivered_by=["sambar.subtypes"],
                             method={"named": "SAMBAR", "named_quote": "SAMBAR", "samples": samples})
    six = task.index("6 tumours")
    facts = [RequestFact(id="s", property="sample_count", value=str(samples), quote="6 tumours",
                         span=[six, six + len("6 tumours")])]
    return CapabilityCheck(requirements=[row], facts=facts)


def _read(**fields):
    blank = {"kmin_words": "", "kmin_value": "", "kmax_words": "", "kmax_value": ""}
    return settings_read_model("SAMBAR").model_validate({**blank, **fields})


def test_numbers_no_count_or_setting_read_trigger_the_read_and_file_names_do_not():
    check = _check()
    unread = [M25[s:e] for s, e in unread_numbers(check, check.results()[0], M25)]
    assert unread == ["900", "2", "8"]  # "6" is the sample count; v2023 sits in a file name
    assert settings_read_triggers(check, M25) == [(0, "SAMBAR")]
    assert settings_read_triggers(check.model_copy(update={"provisional": True}), M25) == []


def test_a_range_beyond_the_samples_is_judged_by_sambars_own_rule():
    words = "trying anywhere from 2 to 8 subtypes"
    held = with_settings_read(_check(), M25, 0, "SAMBAR",
                              _read(kmin_words=words, kmin_value="2", kmax_words=words, kmax_value="8"))
    row = held.results()[0]
    assert (row.status, row.delivered_by, row.defaults) == ("not_available", [], ["sambar.subtypes"])
    assert row.limits == ["SAMBAR: kmax cannot exceed the number of mutation samples when clustering is enabled"]
    assert [s["name"] for s in row.method["settings"]] == ["SAMBAR.kmin", "SAMBAR.kmax"]
    fits = with_settings_read(_check(samples=6), M25, 0, "SAMBAR", _read(kmin_words=words, kmin_value="2",
                                                                          kmax_words="from 2 to 6", kmax_value="6"))
    assert fits.results()[0].status == "available"  # words not in the request add nothing


def test_only_words_in_the_request_that_cover_an_unread_number_and_hold_its_value_count():
    check = _check()
    assert with_settings_read(check, M25, 0, "SAMBAR", _read(kmax_words="6 tumours", kmax_value="6")) == check
    assert with_settings_read(check, M25, 0, "SAMBAR", _read(kmax_words="2 to 8 subtypes", kmax_value="9")) == check
    assert with_settings_read(check, M25, 0, "SAMBAR", None) == check


def test_words_holding_a_stated_setting_are_not_a_fact_to_ask_but_a_valueless_one_is():
    # Live M25/C35: the fact agent made the typed subtype range an open result (CLARIFY); R4 now rejects it. h2 J21's
    # "lam should be 1.5, or maybe 0.15" named lam without a value: still asked.
    from netzoo_agent_core.interpretation.fact_check import holds_stated_setting

    words = "trying anywhere from 2 to 8 subtypes"
    at = M25.index("8 subtypes")
    check = _check()
    stated = RequestFact(id="k", property="setting", name="SAMBAR.kmax", value="8", quote="8", span=[at, at + 1])
    named = RequestFact(id="k", property="setting", name="SAMBAR.kmax", value="", quote="subtypes",
                        span=[at + 2, at + 10])
    assert holds_stated_setting(M25, check.model_copy(update={"facts": [*check.facts, stated]}), words)
    assert not holds_stated_setting(M25, check.model_copy(update={"facts": [*check.facts, named]}), words)
    assert not holds_stated_setting(M25, check, words)
    read = with_settings_read(check, M25, 0, "SAMBAR", _read(kmax_words=words, kmax_value="8"))
    assert holds_stated_setting(M25, read, words)  # a setting the settings read added counts too
