"""Round m3 fixes (2026-10-15): methods questions meet M1's method rules, and a verified setting is not judged twice.

Round m3 (`docs/research-log/m3-clarification-2026-10-15/RESULTS.md`): all 9 false accepts had no result row. "Can
LIONESS-PANDA run for exactly two expression samples ...?" and its kind were read as questions about the methods, and
the data size they state had no request-level field, so the sample minimums, SAMBAR's clustering limit and the
LIONESS-DRAGON cap never applied; "keep save_pvals=true but set sparsify=false" broke a rule the registry records but the
check never read. Among the false refusals, P08's "set cluster=false" -- already read as SAMBAR.cluster=false -- was
answered "violates" by the free-text condition check, and MX12's learning rate, which GIRAFFE cannot take, refused the
two results asked apart from it. Each test gives the check the reading recorded in round m3, plus the request-level
count the new contract asks for where the fix needs it (`docs/research-log/m3-method-fitting-2026-10-15`).
"""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from test_method_conditions import _ask  # noqa: E402

import workflow_registry  # noqa: E402
from netzoo_agent_core.contracts.capability_check import (  # noqa: E402
    conditions_model, proposal_model, unstated_conditions,
)
from netzoo_agent_core.data import bonobo, inspection, lioness_dragon  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import (  # noqa: E402
    build_capability_check, condition_pairs, request_sentences, stated_requirements, understanding_paragraph,
)
from netzoo_agent_core.interpretation.run_check import run_check_verdict  # noqa: E402
from netzoo_agent_core.workflow_conditions import StatedSetting, combination_issues, conditions_for  # noqa: E402


def _proposal(task, *asks, has=(), about=(), **conditions):
    """One reading: every ask in the sentence it quotes, `has` and `about` (methods questions) in theirs, and the
    request-level conditions given."""
    sentences = [task[start:end] for start, end in request_sentences(task)]
    readings = {f"s{index}": {"role": "background", "has": [], "about_methods": [], "asks": []}
                for index in range(1, len(sentences) + 1)}
    for ask in asks:
        index = next(i for i, text in enumerate(sentences, 1) if ask["quote"] in text)
        readings[f"s{index}"]["asks"].append(ask)
        readings[f"s{index}"]["role"] = "asks"
    for field, quotes, role in (("has", has, None), ("about_methods", about, "methods_question")):
        for quote in quotes:
            index = next(i for i, text in enumerate(sentences, 1) if quote in text)
            readings[f"s{index}"][field].append(quote)
            if role and readings[f"s{index}"]["role"] == "background":
                readings[f"s{index}"]["role"] = role
    readings["conditions"] = {**unstated_conditions(), **conditions}
    return proposal_model(len(sentences)).model_validate(readings)


def _check(task, *asks, **readings):
    check, rejected = build_capability_check(task, _proposal(task, *asks, **readings))
    assert not rejected, rejected
    return check


def _settings(*items):
    return [{"name": name, "quote": quote, "value_quote": value} for name, quote, value in items]


# --- 1. A methods question is held to the method rules -----------------------------------------------------------

N03 = "Can LIONESS-PANDA run for exactly two expression samples if collecting more samples is prohibited?"
N15 = "Can BONOBO run on exactly two total samples when no background samples can be supplied?"


@pytest.mark.parametrize("task, named, said, minimum", [
    (N03, "LIONESS-PANDA", "exactly two expression samples", inspection.LIONESS_MIN_SAMPLES),
    (N15, "BONOBO", "exactly two total samples", bonobo.BONOBO_MIN_SAMPLES),
])
def test_a_methods_question_with_too_few_samples_is_not_available(task, named, said, minimum):
    reading = dict(about=[task], has=[said], named_method=named, named_method_quote=named)
    # As recorded in round m3: the count had no request-level field, so nothing was judged and the card said it fits.
    assert not _check(task, **reading).results()
    check = _check(task, **reading, sample_count=2, sample_count_quote=said)
    [result] = check.results()
    assert (result.quote, result.status) == (said, "not_available")
    assert result.limits == [f"{named} needs at least {minimum} samples; the request has 2"]
    assert not result.defaults and check.full_gap  # no workflow takes two samples, with any setting
    assert f'"{said}" -- not available here as asked.' in understanding_paragraph(check)
    # Enough samples: nothing is added, the methods question stays one.
    enough = _check(task.replace("two", "eight"), about=[task.replace("two", "eight")], named_method=named,
                    named_method_quote=named, sample_count=8, sample_count_quote=said.replace("two", "eight"))
    assert not enough.results()


N28 = "Can SAMBAR run with kmin=2 and kmax=9 on exactly six mutation samples while preserving kmax=9?"


def test_n28_a_kmax_above_the_samples_is_not_available_with_the_words_of_both():
    reading = dict(about=[N28], has=["exactly six mutation samples"], named_method="SAMBAR", named_method_quote="SAMBAR",
                   settings=_settings(("SAMBAR.kmin", "kmin=2", "2"), ("SAMBAR.kmax", "kmax=9", "9")))
    assert not _check(N28, **reading).results()  # as recorded: no count, so kmax=9 alone is legal
    check = _check(N28, **reading, sample_count=6, sample_count_quote="exactly six mutation samples")
    [result] = check.results()
    assert (result.quote, result.status) == ("kmin=2 and kmax=9 on exactly six mutation samples", "not_available")
    assert "kmax cannot exceed the number of mutation samples" in result.limits[0]
    assert result.defaults  # SAMBAR runs with its own kmax, offered as an alternative only
    assert run_check_verdict(check, "run_sambar")["verdict"] == "gap"
    twelve = N28.replace("six", "twelve")
    assert not _check(twelve, **{**reading, "about": [twelve], "has": ["exactly twelve mutation samples"]},
                      sample_count=12, sample_count_quote="exactly twelve mutation samples").results()


K05 = ("Previous NetZoo goal: Set BONOBO sparsify=true and save_pvals=true for valid expression inputs.\n"
       "User follow-up: Revision: keep save_pvals=true but set sparsify=false. Preserve that exact combination.")


def test_k05_a_combination_the_registry_marks_invalid_is_not_available():
    # As recorded: every sentence background, the request-level settings read; each is legal alone.
    reading = dict(named_method="BONOBO", named_method_quote="BONOBO",
                   settings=_settings(("BONOBO.sparsify", "set sparsify=false", "false"),
                                      ("BONOBO.save_pvals", "keep save_pvals=true", "true")))
    check = _check(K05, **reading)
    [result] = check.results()
    # "true" first appears in the previous goal; the words are the follow-up's own.
    assert (result.quote, result.status) == ("keep save_pvals=true but set sparsify=false", "not_available")
    assert result.limits == ["BONOBO: save_pvals requires sparsify"]
    both = K05.replace("set sparsify=false", "set sparsify=true")
    assert not _check(both, **{**reading, "settings": _settings(("BONOBO.sparsify", "set sparsify=true", "true"),
                                                              ("BONOBO.save_pvals", "keep save_pvals=true",
                                                               "true"))}).results()


def test_m3f_k05_no_method_named_the_settings_name_the_workflow():
    # Live m3f K05: the method typed "none" and each setting quoted by its name alone, which first stands in the
    # previous goal ("sparsify=true and save_pvals=true", a valid combination the row must not quote).
    check = _check(K05, settings=_settings(("BONOBO.sparsify", "sparsify", "false"),
                                           ("BONOBO.save_pvals", "save_pvals", "true")))
    [result] = check.results()
    assert (result.quote, result.status) == ("save_pvals=true but set sparsify=false", "not_available")
    assert result.limits == ["BONOBO: save_pvals requires sparsify"]
    # Settings naming two workflows name no one method: nothing is judged.
    assert not _check(K05, settings=_settings(("BONOBO.sparsify", "sparsify", "false"),
                                              ("SAMBAR.cluster", "save_pvals", "true"))).results()


def test_the_invalid_combination_rule_is_the_registrys(monkeypatch):
    conditions = conditions_for("BONOBO")
    stated = [StatedSetting("BONOBO.save_pvals", "save_pvals=true", "true")]  # sparsify keeps its default, false
    assert combination_issues(conditions, stated) == ["BONOBO: save_pvals requires sparsify"]
    # Words that settle no value are never judged.
    assert not combination_issues(conditions, [StatedSetting("BONOBO.save_pvals", "save p-values", "maybe")])
    definitions = dict(workflow_registry.ACTION_DEFINITIONS)
    definition = definitions["run_bonobo"]
    rules = tuple(replace(rule, valid=True) for rule in definition.output_capability.conditional_outputs)
    definitions["run_bonobo"] = replace(definition, output_capability=replace(
        definition.output_capability, conditional_outputs=rules))
    monkeypatch.setattr("netzoo_agent_core.workflow_conditions.ACTION_DEFINITIONS", definitions)
    assert not combination_issues(conditions, stated)


N26 = "Run LIONESS-DRAGON with 100 samples and 1000 total features, keeping every pair for every sample in one run."


def test_n26_the_requests_feature_count_reaches_its_one_result():
    ask = _ask("Run LIONESS-DRAGON", ["lioness_dragon.per_sample_networks"], named="LIONESS-DRAGON",
               named_quote="LIONESS-DRAGON", samples=100, samples_quote="100 samples", omics_layers=2)
    reading = dict(named_method="LIONESS-DRAGON", named_method_quote="LIONESS-DRAGON")
    assert [item.status for item in _check(N26, ask, **reading).results()] == ["available"]  # as recorded
    check = _check(N26, ask, **reading, feature_counts=[{"count": 1000, "quote": "1000 total features"}])
    [result] = check.results()
    size = lioness_dragon.lioness_dragon_size(100, 1000)
    assert result.status == "not_available" and f"give {size:,}" in result.limits[0]
    assert check.full_gap and run_check_verdict(check, "run_lioness_dragon")["verdict"] == "gap"


def test_the_requests_count_is_not_given_to_one_of_two_results_or_against_an_unknown_count():
    task = "Build an aggregate PANDA network from our 2 samples, then find communities in it."
    check = _check(task, _ask("Build an aggregate PANDA network", ["panda.tf_gene_network"], scale="whole_cohort",
                              regulator_kinds=["tf"]),
                   _ask("find communities in it", ["condor.communities"], input_network="regulator_gene"),
                   sample_count=2, sample_count_quote="2 samples")
    assert all("samples" not in item.method for item in check.results())
    # The user says the count is not known: a count the request-level reading typed anyway is not used either.
    task = "Run LIONESS-PANDA for our panel. It has two or five samples; I do not know which yet."
    ask = _ask("Run LIONESS-PANDA for our panel", ["lioness_panda.per_sample_networks"], named="LIONESS-PANDA",
               named_quote="LIONESS-PANDA", scale="per_sample", regulator_kinds=["tf"])
    unknown = [{"quote": "It has two or five samples; I do not know which yet", "about": "sample_count",
                "count_kind": "choices", "count_values": [2, 5], "applies_to": None}]
    check = _check(task, ask, unknown_facts=unknown, sample_count=2, sample_count_quote="two")
    [result] = check.results()
    assert "samples" not in result.method and result.status != "not_available"


def test_recordings_without_the_count_fields_still_read():
    fields = conditions_model().model_fields
    assert {"sample_count", "sample_count_quote", "feature_counts"} <= set(fields)
    recorded = {key: value for key, value in unstated_conditions().items()
                if key not in ("sample_count", "sample_count_quote", "feature_counts")}
    read = conditions_model().model_validate(recorded)
    assert read.sample_count is None and read.feature_counts == []
    assert conditions_model(compact=True).model_validate(recorded).sample_count is None


# --- 2. A verified typed setting is not judged again by the free-text condition check ------------------------------

P08 = ("Can SAMBAR return pathway mutation scores without assigning tumor clusters? Our sarcoma mutation CSV, positive "
       "exon lengths, single-line cancer gene list and GMT have overlapping genes; set cluster=false.")
P08_ASK = "Can SAMBAR return pathway mutation scores without assigning tumor clusters?"


def _p08(requirement="set cluster=false", value="false", task=P08):
    ask = _ask(P08_ASK, ["sambar.subtypes"], named="SAMBAR", named_quote="SAMBAR", asked_as="question",
               settings=[("SAMBAR.cluster", f"cluster={value}", value)])
    proposal = _proposal(task, ask, named_method="SAMBAR", named_method_quote="SAMBAR",
                         settings=_settings(("SAMBAR.cluster", f"cluster={value}", value)),
                         other_requirements=[{"about": "how_computed", "quote": requirement}])
    check, _rejected = build_capability_check(task, proposal)
    return proposal, check


def test_p08_a_verified_setting_is_not_sent_to_the_condition_check():
    proposal, check = _p08()
    assert stated_requirements(P08, proposal, check) == ["set cluster=false"]
    assert condition_pairs(check, ["set cluster=false"]) == []
    # More than the setting is still checked; so are the words of a setting that is not usable as stated.
    longer = "set cluster=false and keep only TP53-mutant samples"
    assert [quote for *_rest, quote in condition_pairs(check, [longer])] == [longer]
    task = P08.replace("cluster=false", "cluster=maybe")
    _proposal_, unresolved = _p08("set cluster=maybe", "maybe", task)
    assert [(item.quote, item.status) for item in unresolved.results()] == [
        (P08_ASK, "available")]  # "maybe" is unresolved, not a known setting violation.
    from netzoo_agent_core.interpretation.method_conditions import unresolved_settings
    assert unresolved_settings(unresolved.results()[0].method, ["sambar.subtypes"])
    assert [quote for *_rest, quote in condition_pairs(unresolved, ["set cluster=maybe"])] == ["set cluster=maybe"]


def test_p08_the_router_never_asks_and_the_supported_scores_stand(monkeypatch):
    from netzoo_agent_core.contracts import TaskDecision
    from netzoo_agent_core.graph import router_invocation

    proposal, _check_ = _p08()
    asked = []
    monkeypatch.setattr(router_invocation, "record_event", lambda *args, **kwargs: None)
    monkeypatch.setattr(router_invocation, "request_condition_check",
                        lambda context, state, shown, usage, warnings, **kwargs: (
                            asked.append(shown) or ["violates"] * len(shown), usage, warnings))
    decision = TaskDecision.model_validate({"action": "no_tool", "in_scope": True, "should_execute": False,
                                            "confidence": 0.9, "reason": "r", "capability_match_status": "exact",
                                            "matched_actions": ["run_sambar"]})
    invocation = router_invocation._RouterInvocation(decision=decision, routing_state={}, usage=None,
                                                     budget_warnings=[], reason_code=None)
    result = router_invocation._with_capability_check(SimpleNamespace(project_policy=None), {}, P08, invocation,
                                                      proposal)
    check = result.decision.capability_check
    assert asked == [] and not check.full_gap
    assert [(item.quote, item.status) for item in check.results()] == [(P08_ASK, "available")]


# --- 2b. A setting no credited workflow can use, stated in a clause of its own, limits only itself ------------------

MX12 = ("Run GIRAFFE with all validated priors to produce signed R and sample-varying TFA, and use an exposed custom "
        "optimizer learning rate of 0.009.")


def test_mx12_an_unusable_setting_in_its_own_clause_is_a_requirement_of_its_own():
    rate = [("unregistered", "exposed custom optimizer learning rate", "0.009")]
    check = _check(MX12, _ask("signed R", ["giraffe.signed_regulation"], named="GIRAFFE", named_quote="GIRAFFE",
                              settings=rate, needs_sign=True, scale="whole_cohort"),
                   _ask("sample-varying TFA", ["giraffe.tf_activity"], named="GIRAFFE", named_quote="GIRAFFE",
                        settings=rate, scale="per_sample"))
    assert [(item.quote, item.status) for item in check.results()] == [
        ("signed R", "available"), ("sample-varying TFA", "available"),
        ("exposed custom optimizer learning rate of 0.009", "not_available")]
    assert "passes no settings to it" in check.results()[2].limits[0]
    assert all("settings" not in item.method for item in check.results()[:2])
    # The run is still held: the user asked for the learning rate too.
    assert run_check_verdict(check, "run_giraffe")["verdict"] == "partial_gap"
    assert ('"exposed custom optimizer learning rate of 0.009" -- not available here as asked.'
            in understanding_paragraph(check))


F6 = ("Please build LIONESS-PANDA networks for our 40 liver samples with an edge sparsity threshold of 0.3 applied "
      "inside the method; motif and PPI files are ready.")


def test_m1b_f6_a_setting_joined_to_the_ask_still_limits_it():
    # m1b F6's gold judges the networks and the threshold as one requirement, not supported; no clause boundary
    # separates the threshold from "LIONESS-PANDA networks".
    check = _check(F6, _ask("LIONESS-PANDA networks", ["lioness_panda.per_sample_networks"], named="LIONESS-PANDA",
                            named_quote="LIONESS-PANDA", scale="per_sample", regulator_kinds=["tf"],
                            settings=[("unregistered", "edge sparsity threshold of 0.3", "0.3")]))
    [result] = check.results()
    assert result.status == "not_available" and result.defaults == ["lioness_panda.per_sample_networks"]
