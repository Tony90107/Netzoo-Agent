"""ROUND-03 (collab/ROUND-03-PLAN.md): the request's counts and settings as one record the checks and the run cite.

Each test gives the capability check one reading and looks at the record: a value written in several places is one
fact read several times, different data objects stay apart, a total is code's own value with its parts, the result
cites what it was judged on, and the run's controls name the facts they came from. The result checks themselves are
unchanged (979 recorded readings rebuilt identically, `docs/research-log/request-facts-round03-2026-10-20`).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from test_method_conditions import _ask  # noqa: E402

from netzoo_agent_core.contracts.capability_check import proposal_model, unstated_conditions  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import (  # noqa: E402
    build_capability_check, request_sentences,
)
from netzoo_agent_core.interpretation.count_alternatives import verified_count_alternatives  # noqa: E402
from netzoo_agent_core.interpretation.request_facts import merge_facts, run_fact_bindings  # noqa: E402


def _proposal(task, *asks, **conditions):
    sentences = [task[start:end] for start, end in request_sentences(task)]
    readings = {f"s{index}": {"role": "background", "has": [], "about_methods": [], "asks": []}
                for index in range(1, len(sentences) + 1)}
    for ask in asks:
        index = next(i for i, text in enumerate(sentences, 1) if ask["quote"] in text)
        readings[f"s{index}"]["asks"].append(ask)
        readings[f"s{index}"]["role"] = "asks"
    readings["conditions"] = {**unstated_conditions(), **conditions}
    return proposal_model(len(sentences)).model_validate(readings)


def _check(task, *asks, **conditions):
    check, rejected = build_capability_check(task, _proposal(task, *asks, **conditions))
    assert not rejected, rejected
    return check


def _facts(check, prop):
    return [fact for fact in check.facts if fact.property == prop]


LIVER = "We have 40 liver samples. Build one PANDA network for the 40 liver samples."


def test_a_count_written_at_request_and_result_level_is_one_fact_read_twice():
    ask = _ask("Build one PANDA network for the 40 liver samples", ["panda.tf_gene_network"], scale="whole_cohort",
               regulator_kinds=["tf"], samples=40, samples_quote="the 40 liver samples")
    check = _check(LIVER, ask, sample_count=40, sample_count_quote="the 40 liver samples")
    [fact] = _facts(check, "sample_count")
    assert fact.value == "40" and fact.reads() == 2
    assert {e.reader for e in fact.evidence} == {"request", "result"}
    [result] = check.results()
    assert result.method["samples"] == 40 and result.fact_ids == [fact.id]


def test_overlapping_words_with_the_same_number_are_one_fact():
    task = "Build one PANDA network for the 40 liver samples."
    ask = _ask("Build one PANDA network for the 40 liver samples", ["panda.tf_gene_network"], scale="whole_cohort",
               regulator_kinds=["tf"], samples=40, samples_quote="the 40 liver samples")
    check = _check(task, ask, sample_count=40, sample_count_quote="40 liver samples")
    [fact] = _facts(check, "sample_count")
    assert fact.reads() == 2
    # the result keeps its own words, as before; words elsewhere that do not overlap would stay a fact of their own
    # (two places can count two things)
    assert check.results()[0].method["samples_quote"] == "the 40 liver samples"


def test_a_different_cohort_in_other_words_is_a_fact_of_its_own():
    task = "We have 400 lung adenocarcinoma patients. Build one PANDA network for 150 patients from another hospital."
    ask = _ask("Build one PANDA network for 150 patients from another hospital", ["panda.tf_gene_network"],
               scale="whole_cohort", regulator_kinds=["tf"], samples=150,
               samples_quote="150 patients from another hospital")
    check = _check(task, ask, sample_count=400, sample_count_quote="400 lung adenocarcinoma patients")
    facts = _facts(check, "sample_count")
    assert sorted(fact.value for fact in facts) == ["150", "400"]
    assert all(fact.belongs_to == "" for fact in facts)  # never filled from guesswork
    [result] = check.results()
    assert result.method["samples"] == 150
    [conflict] = check.fact_conflicts
    assert conflict.reason == "result_own_value" and conflict.property == "sample_count"
    assert [check_fact.value for check_fact in check.facts if check_fact.id in conflict.used] == ["150"]
    assert [check_fact.value for check_fact in check.facts if check_fact.id in conflict.set_aside] == ["400"]


def test_two_layers_with_the_same_number_stay_two_facts_and_their_total_is_derived():
    task = "Build one DRAGON network from 300 RNA genes and 300 CpG probes measured on 60 samples."
    ask = _ask(task.rstrip("."), ["dragon.two_layer_network"], omics_layers=2,
               features=[(300, "300 RNA genes"), (300, "300 CpG probes")])
    check = _check(task, ask)
    parts = [fact for fact in _facts(check, "feature_count") if fact.origin == "user_stated"]
    assert len(parts) == 2 and {fact.quote for fact in parts} == {"300 RNA genes", "300 CpG probes"}
    [total] = [fact for fact in check.facts if fact.origin == "derived"]
    assert total.value == "600" and total.formula == "300 + 300"
    assert sorted(total.derived_from) == sorted(fact.id for fact in parts)
    assert {e.role for e in total.evidence} == {"operand"}
    [result] = check.results()
    assert result.method["features"] == 600 and set(result.fact_ids) == {*total.derived_from, total.id}


C45 = ("I don't remember whether the proteomics we got back is the 200-protein targeted panel or the 2,000-protein "
       "discovery panel.")


def test_candidates_compile_back_as_before():
    proposal = _proposal(C45, count_alternatives=[{
        "of": "features", "quote": "the 200-protein targeted panel or the 2,000-protein discovery panel",
        "values": [200, 2000]}])
    check, _rejected = build_capability_check(C45, proposal)
    [fact] = _facts(check, "feature_count")
    assert fact.state == "unsure" and fact.values == ["200", "2000"]
    assert check.count_alternatives == [{k: v for k, v in item.items() if k != "span"}
                                        for item in verified_count_alternatives(C45, proposal)]


def test_an_unknown_count_with_the_same_candidates_is_the_same_doubt_read_again():
    task = "I am not sure whether we have 8 or 15 tumours in the final cohort."
    words = "whether we have 8 or 15 tumours"
    check = _check(task, count_alternatives=[{"of": "samples", "quote": words, "values": [8, 15]}],
                   unknown_facts=[{"quote": words, "about": "sample_count", "count_kind": "choices",
                                   "count_values": [8, 15], "applies_to": None}])
    [fact] = _facts(check, "sample_count")
    assert fact.state == "unsure" and fact.values == ["8", "15"]
    assert [e.reader for e in fact.evidence] == ["count_alternatives", "unknown_facts"]


def test_a_setting_restated_with_another_value_is_a_conflict_the_latest_wins():
    task = "Run OTTER with lam 0.1 on the expression table. Actually, set OTTER lam to 0.25."
    ask = _ask("Run OTTER with lam 0.1 on the expression table", ["otter.tf_gene_network"], named="OTTER",
               named_quote="OTTER", scale="whole_cohort", regulator_kinds=["tf"],
               settings=[("OTTER.lam", "lam 0.1", "0.1")])
    check = _check(task, ask, settings=[{"name": "OTTER.lam", "quote": "OTTER lam", "value_quote": "0.25"}])
    [result] = check.results()
    assert [item["value"] for item in result.method["settings"]] == ["0.25"]
    [conflict] = check.fact_conflicts
    assert conflict.reason == "latest_stated" and conflict.name == "OTTER.lam"
    values = {fact.id: fact.value for fact in check.facts}
    assert [values[i] for i in conflict.used] == ["0.25"] and [values[i] for i in conflict.set_aside] == ["0.1"]
    assert result.fact_ids == conflict.used


def test_each_run_setting_has_a_disposition_and_names_its_fact():
    task = "Run OTTER with precision set to single precision to build a TF-gene network."
    check = _check(task, _ask(task, ["otter.tf_gene_network"], named="OTTER", named_quote="OTTER",
                              scale="whole_cohort", regulator_kinds=["tf"],
                              settings=[("OTTER.precision", "precision", "single precision")]))
    [fact] = _facts(check, "setting")
    [binding] = run_fact_bindings(check, "run_otter")
    assert binding == {"fact": fact.id, "control": "precision", "quote": "precision", "value": "single",
                       "disposition": "applied", "from": "value"}
    assert run_fact_bindings(check, "run_otter", lambda name: name == "precision")[0]["disposition"] \
        == "set_by_request"
    assert run_fact_bindings(check, "run_otter", approved=False)[0]["disposition"] == "held"

    # A value the workflow cannot take leaves it uncredited: no run, so nothing to bind -- its place is the limit.
    vague = "Run OTTER with precision set to half to build a TF-gene network."
    check = _check(vague, _ask(vague, ["otter.tf_gene_network"], named="OTTER", named_quote="OTTER",
                               scale="whole_cohort", regulator_kinds=["tf"],
                               settings=[("OTTER.precision", "precision", "half")]))
    assert run_fact_bindings(check, "run_otter") == [] and check.results()[0].limits
    assert check.results()[0].fact_ids == [fact.id for fact in _facts(check, "setting")]


def test_a_reread_adds_its_result_reads_but_not_the_carried_request_reads_again():
    ask = _ask("Build one PANDA network for the 40 liver samples", ["panda.tf_gene_network"], scale="whole_cohort",
               regulator_kinds=["tf"], samples=40, samples_quote="the 40 liver samples")
    first = _check(LIVER, ask, sample_count=40, sample_count_quote="the 40 liver samples")
    again = _check(LIVER, ask, sample_count=40, sample_count_quote="the 40 liver samples")
    [fact] = merge_facts(first.facts, again.facts, set(again.results()[0].fact_ids))
    # the re-read carries the first reading's conditions (no new request read), and a result read identical to one
    # the record holds is not added twice; `merge_reread` keeps only results the first reading did not have
    assert [e.reader for e in fact.evidence] == ["request", "result"]


def test_recordings_from_before_round03_load_without_facts():
    from netzoo_agent_core.contracts.capability_check import CapabilityCheck, CheckedRequirement

    check = CapabilityCheck.model_validate({"requirements": [{"quote": "x", "kind": "result",
                                                              "status": "available"}]})
    assert check.facts == [] and check.fact_conflicts == []
    assert CheckedRequirement.model_validate({"quote": "x", "kind": "result", "status": "available"}).fact_ids == []


def test_the_response_model_is_not_given_the_record_again():
    import json

    from netzoo_agent_core.contracts import TaskDecision
    from netzoo_agent_core.graph.response_payload import _NOT_FOR_RESPONSE

    ask = _ask("Build one PANDA network for the 40 liver samples", ["panda.tf_gene_network"], scale="whole_cohort",
               regulator_kinds=["tf"], samples=40, samples_quote="the 40 liver samples")
    check = _check(LIVER, ask, sample_count=40, sample_count_quote="the 40 liver samples")
    base = dict(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="r")
    shown = json.loads(TaskDecision(**base, capability_check=check).model_dump_json(exclude=_NOT_FOR_RESPONSE))
    assert "facts" not in shown["capability_check"] and "fact_conflicts" not in shown["capability_check"]
    assert "fact_ids" not in shown["capability_check"]["requirements"][0]
    assert shown["capability_check"]["requirements"][0]["method"]["samples"] == 40
    assert "advisory_recommendation" not in json.loads(TaskDecision(**base).model_dump_json(exclude=_NOT_FOR_RESPONSE))


# --- ROUND-04: reading shape 2 -- counts and settings once, for the request, scoped to the results ---------------

_ASK_ONLY = ("settings", "sample_count", "sample_count_quote", "feature_counts")


def _ask2(*args, **kwargs):
    return {key: value for key, value in _ask(*args, **kwargs).items() if key not in _ASK_ONLY}


def _check2(task, *asks, **conditions):
    sentences = [task[start:end] for start, end in request_sentences(task)]
    readings = {f"s{index}": {"role": "background", "has": [], "about_methods": [], "asks": []}
                for index in range(1, len(sentences) + 1)}
    for ask in asks:
        index = next(i for i, text in enumerate(sentences, 1) if ask["quote"] in text)
        readings[f"s{index}"]["asks"].append(ask)
        readings[f"s{index}"]["role"] = "asks"
    readings["conditions"] = {**unstated_conditions(2), **conditions}
    check, rejected = build_capability_check(task, proposal_model(len(sentences), version=2).model_validate(readings))
    assert not rejected, rejected
    return check


def _samples(count, quote, applies_to=None):
    return {"count": count, "quote": quote, "applies_to": applies_to}


def _features(count, quote, belongs_to="", applies_to=None):
    return {"count": count, "quote": quote, "belongs_to": belongs_to, "applies_to": applies_to}


def _setting(name, quote, value, applies_to=None):
    return {"name": name, "quote": quote, "value_quote": value, "applies_to": applies_to}


TF = dict(scale="whole_cohort", regulator_kinds=["tf"])
GROUPS = "Build one PANDA network for the 12 hypoxia samples. Build another PANDA network for the 15 normoxia samples."
HYPOXIA = "Build one PANDA network for the 12 hypoxia samples"
NORMOXIA = "Build another PANDA network for the 15 normoxia samples"


def test_shape2_asks_carry_no_counts_or_settings_and_the_switch_selects_it(monkeypatch):
    from netzoo_agent_core.contracts.capability_check import reading_version, schema_version

    ask = proposal_model(1, version=2).model_json_schema()
    text = str(ask)
    assert "sample_counts" in text and "applies_to" in text and "sample_count_quote" not in text
    monkeypatch.delenv("NETZOO_CHECK_SCHEMA", raising=False)
    assert schema_version() == 1
    monkeypatch.setenv("NETZOO_CHECK_SCHEMA", "2")
    assert schema_version() == 2
    assert reading_version(_proposal(LIVER)) == 1


def test_each_group_count_goes_to_its_own_result():
    check = _check2(GROUPS, _ask2(HYPOXIA, ["panda.tf_gene_network"], **TF),
                    _ask2(NORMOXIA, ["panda.tf_gene_network"], **TF),
                    sample_counts=[_samples(12, "12 hypoxia samples", [HYPOXIA]),
                                   _samples(15, "15 normoxia samples", [NORMOXIA])])
    assert [item.method.get("samples") for item in check.results()] == [12, 15]
    assert not check.fact_conflicts
    assert all(len(item.fact_ids) == 1 for item in check.results())


def test_two_different_counts_for_one_result_decide_nothing():
    task = "We have 400 patients and a validation cohort of 150 patients. Build one PANDA network for them."
    check = _check2(task, _ask2("Build one PANDA network for them", ["panda.tf_gene_network"], **TF),
                    sample_counts=[_samples(400, "400 patients"), _samples(150, "150 patients")])
    [result] = check.results()
    assert "samples" not in result.method
    [conflict] = check.fact_conflicts
    assert conflict.reason == "several_values" and len(conflict.set_aside) == 2 and conflict.used == []


def test_a_count_for_every_result_applies_to_each_of_several():
    task = "We have 40 liver samples. Build a PANDA network. Then find communities with CONDOR."
    check = _check2(task, _ask2("Build a PANDA network", ["panda.tf_gene_network"], **TF),
                    _ask2("Then find communities with CONDOR", ["condor.communities"], scale="whole_cohort"),
                    sample_counts=[_samples(40, "40 liver samples")])
    assert [item.method.get("samples") for item in check.results()] == [40, 40]


def test_a_setting_scoped_to_one_result_stays_with_it():
    task = ("Run DRAGON on RNA-seq (2,000 genes) and protein data (220 antibodies). Also give me a PANDA network. "
            "Fix lambda1 at 0.3 for the DRAGON run.")
    dragon = "Run DRAGON on RNA-seq (2,000 genes) and protein data (220 antibodies)"
    check = _check2(task, _ask2(dragon, ["dragon.two_layer_network"], omics_layers=2),
                    _ask2("Also give me a PANDA network", ["panda.tf_gene_network"], **TF),
                    settings=[_setting("DRAGON.lambda1", "lambda1", "0.3", [dragon])],
                    feature_counts=[_features(2000, "2,000 genes", "RNA-seq", [dragon]),
                                    _features(220, "220 antibodies", "protein data", [dragon])])
    first, second = check.results()
    assert [item["value"] for item in first.method["settings"]] == ["0.3"] and "settings" not in second.method
    assert first.method["features"] == 2220 and "features" not in second.method
    owners = {fact.quote: fact.belongs_to for fact in check.facts if fact.property == "feature_count"
              and fact.origin == "user_stated"}
    assert owners == {"2,000 genes": "RNA-seq", "220 antibodies": "protein data"}


def test_an_unscoped_registered_setting_goes_only_to_its_workflows_results():
    task = "Build a PANDA network. Then run DRAGON on the two layers. Use lambda1 0.3."
    check = _check2(task, _ask2("Build a PANDA network", ["panda.tf_gene_network"], **TF),
                    _ask2("Then run DRAGON on the two layers", ["dragon.two_layer_network"], omics_layers=2),
                    settings=[_setting("DRAGON.lambda1", "lambda1", "0.3")])
    panda, dragon = check.results()
    assert "settings" not in panda.method and dragon.method["settings"][0]["value"] == "0.3"


def test_a_scope_whose_words_are_not_in_the_request_is_never_guessed_among_several():
    one = _check2(LIVER, _ask2("Build one PANDA network for the 40 liver samples", ["panda.tf_gene_network"], **TF),
                  sample_counts=[_samples(40, "40 liver samples", ["a network for the kidney"])])
    assert one.results()[0].method["samples"] == 40
    several = _check2(GROUPS, _ask2(HYPOXIA, ["panda.tf_gene_network"], **TF),
                      _ask2(NORMOXIA, ["panda.tf_gene_network"], **TF),
                      sample_counts=[_samples(12, "12 hypoxia samples", ["a network for the kidney"])])
    assert all("samples" not in item.method for item in several.results())
    assert [fact.scope_unverified for fact in several.facts] == [True]


def test_a_count_for_no_asked_result_applies_to_none():
    check = _check2(LIVER, _ask2("Build one PANDA network for the 40 liver samples", ["panda.tf_gene_network"], **TF),
                    sample_counts=[_samples(40, "40 liver samples", [])])
    assert "samples" not in check.results()[0].method


def test_a_belongs_to_not_in_the_request_is_left_empty():
    task = "Run DRAGON on 300 RNA genes and 300 CpG probes."
    check = _check2(task, _ask2(task.rstrip("."), ["dragon.two_layer_network"], omics_layers=2),
                    feature_counts=[_features(300, "300 RNA genes", "transcriptome table"),
                                    _features(300, "300 CpG probes", "CpG probes")])
    owners = sorted(fact.belongs_to for fact in check.facts if fact.property == "feature_count"
                    and fact.origin == "user_stated")
    assert owners == ["", "CpG probes"]
    assert check.results()[0].method["features"] == 600


def test_a_shape2_reread_carries_the_scoped_conditions():
    from netzoo_agent_core.contracts.capability_check import reread_as_proposal, reread_model

    conditions = proposal_model(1, version=2).model_validate({
        "s1": {"role": "asks", "has": [], "about_methods": [], "asks": []},
        "conditions": {**unstated_conditions(2), "sample_counts": [_samples(40, "40 liver samples")]}}).conditions
    reread = reread_model(1, version=2).model_validate({"s1": {"asks": [_ask2("a PANDA network", [], **TF)]}})
    proposal = reread_as_proposal(reread, conditions)
    assert proposal.conditions.sample_counts[0].count == 40 and "sample_count" not in proposal.s1.asks[0].model_dump()


def test_an_unscoped_unregistered_setting_holds_no_result_among_several_but_a_scoped_one_holds_its_own():
    task = "Build a PANDA network. Then run DRAGON on the two layers. Let it estimate both shrinkage values."
    asks = (_ask2("Build a PANDA network", ["panda.tf_gene_network"], **TF),
            _ask2("Then run DRAGON on the two layers", ["dragon.two_layer_network"], omics_layers=2))
    loose = _check2(task, *asks, settings=[_setting("unregistered", "estimate both shrinkage values", "")])
    assert all(item.status == "available" for item in loose.results())
    scoped = _check2(task, *asks, settings=[_setting("unregistered", "estimate both shrinkage values", "",
                                                     ["Then run DRAGON on the two layers"])])
    # held to it, DRAGON's result is read without it and the words become a not-available row of their own (round m3's
    # settings_apart: stated in a clause of their own); PANDA's result is untouched
    panda, dragon, apart = scoped.results()
    assert panda.status == "available" and "settings" not in panda.method and "settings" not in dragon.method
    assert apart.quote.startswith("estimate both shrinkage values") and apart.status == "not_available"


def test_one_run_takes_one_set_of_settings_whichever_result_they_were_scoped_to():
    task = "Time to rerun OTTER on expr.tsv. Set precision to single. Start it now."
    rerun, start = "Time to rerun OTTER on expr.tsv", "Start it now"
    check = _check2(task, _ask2(rerun, ["otter.tf_gene_network"], **TF), _ask2(start, ["otter.tf_gene_network"], **TF),
                    settings=[_setting("OTTER.precision", "precision", "single", [rerun])])
    assert [item.method["settings"][0]["value"] for item in check.results()] == ["single", "single"]
    nowhere = _check2(task, _ask2(rerun, ["otter.tf_gene_network"], **TF),
                      _ask2(start, ["otter.tf_gene_network"], **TF),
                      settings=[_setting("OTTER.precision", "precision", "single", [])])
    assert all("settings" not in item.method for item in nowhere.results())


# --- ROUND-05: reading shape 3 -- shape 1, with each setting's description sent once -------------------------------

def test_shape3_sends_the_settings_description_once_and_reads_as_shape1(monkeypatch):
    import json

    from langchain_core.utils.function_calling import convert_to_openai_tool

    from netzoo_agent_core.contracts.capability_check import reading_version, schema_version
    from netzoo_agent_core.method_names import setting_meanings

    described = " | ".join(setting_meanings())[:60]
    one = json.dumps(convert_to_openai_tool(proposal_model(3), strict=True))
    three = json.dumps(convert_to_openai_tool(proposal_model(3, version=3), strict=True))
    assert one.count(described) == 5 and three.count(described) == 1
    assert len(three) < 0.85 * len(one)
    reading = proposal_model(1, version=3).model_validate({
        "s1": {"role": "asks", "has": [], "about_methods": [], "asks": [_ask(
            "Build one PANDA network for the 40 liver samples", ["panda.tf_gene_network"], **TF)]},
        "conditions": unstated_conditions(3)})
    assert reading_version(reading) == 1
    assert proposal_model(1).model_validate(reading.model_dump()).model_dump() == reading.model_dump()
    monkeypatch.setenv("NETZOO_CHECK_SCHEMA", "3")
    assert schema_version() == 3
