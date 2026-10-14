"""M1 steps 2-3 (2026-10-14): the method, settings and data size an ask states decide which workflow can give it.

Final acceptance a24b: each negative below was read as asking for a result some workflow gives, and was credited to
it, although the workflow cannot run the way the request asks. Each test gives the check the reading recorded in a24b
(`.worktrees/netzoo-final-live`) plus the typed method fields M1 adds, with its paired positive, which must stay
available. N35 (PUMA driven by miRNA expression) moved to M2 by the user's decision.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.capability_check import proposal_model  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import (  # noqa: E402
    build_capability_check, full_gap_reply, method_fitting, redirect_pairs, request_sentences,
    second_opinion_pairs, understanding_paragraph, verified_method,
)
from netzoo_agent_core.interpretation.run_check import run_check_verdict  # noqa: E402

PLAIN = {"scale": "unstated", "omics_layers": 0, "data_unit": "bulk_samples", "regulator_kinds": [],
         "needs_sign": False, "input_network": "none", "group_membership": "not_about_groups",
         "time_model": "not_dynamic", "spatial": "not_spatial", "asked_as": "request"}


def _ask(quote, delivered=(), not_by=(), *, named="none", named_quote="", settings=(), samples=None,
         samples_quote="", features=(), **attrs):
    return {**PLAIN, **attrs, "quote": quote, "delivered_by": list(delivered), "not_by": list(not_by),
            "named_method": named, "named_method_quote": named_quote,
            "settings": [{"name": name, "quote": quote_, "value_quote": value} for name, quote_, value in settings],
            "sample_count": samples, "sample_count_quote": samples_quote,
            "feature_counts": [{"count": count, "quote": words} for count, words in features]}


def _check(task, *asks, has=()):
    """One proposal: every ask in the sentence it quotes, `has` quotes as context in theirs."""
    sentences = [task[start:end] for start, end in request_sentences(task)]
    readings = {f"s{index}": {"role": "background", "has": [], "about_methods": [], "asks": []}
                for index in range(1, len(sentences) + 1)}
    for ask in asks:
        index = next(i for i, text in enumerate(sentences, 1) if ask["quote"] in text)
        readings[f"s{index}"]["asks"].append(ask)
        readings[f"s{index}"]["role"] = "asks"
    for quote in has:
        index = next(i for i, text in enumerate(sentences, 1) if quote in text)
        readings[f"s{index}"]["has"].append(quote)
        if readings[f"s{index}"]["role"] == "asks":
            readings[f"s{index}"]["role"] = "mixed"
    check, rejected = build_capability_check(task, proposal_model(len(sentences)).model_validate(readings))
    assert not rejected, rejected
    return check


def _result(check):
    [result] = check.results()
    return result


# --- N11 / K06: a setting the workflow does not have, and settings it has -----------------------------------------

N11 = ("Run OTTER with an L1 sparsity penalty of 0.1 so that most TF-gene edges are exactly zero; motif, PPI and "
       "expression for 64 samples are attached.")


def test_n11_a_penalty_otter_does_not_have_is_not_given_and_the_run_is_held():
    check = _check(N11, _ask(
        "Run OTTER with an L1 sparsity penalty of 0.1 so that most TF-gene edges are exactly zero",
        ["otter.tf_gene_network"], named="OTTER", named_quote="OTTER", scale="whole_cohort", regulator_kinds=["tf"],
        settings=[("unregistered", "an L1 sparsity penalty of 0.1", "0.1")], samples=64, samples_quote="64 samples"),
        has=["motif, PPI and expression for 64 samples are attached."])
    result = _result(check)
    assert result.status == "not_available" and not result.delivered_by
    assert 'has no setting for "an L1 sparsity penalty of 0.1"' in result.limits[0]
    assert result.defaults == ["otter.tf_gene_network"]
    # OTTER itself is offered, as what it is: the run is held for the user, never planned as asked.
    assert not check.full_gap
    assert run_check_verdict(check, "run_otter")["verdict"] == "gap"
    line = understanding_paragraph(check)
    assert "not available here as asked" in line and "OTTER itself can still run" in line
    assert "no registered workflow produces this" not in line
    # A second opinion is never asked to credit OTTER back with the penalty.
    assert second_opinion_pairs(check.model_copy(update={"full_gap": True}), ["run_otter", "run_panda"]) == []


K06_TURN2 = "Please give it to me as an edge list, with fixed lambdas of 0.2 and 0.6."


def test_k06_settings_dragon_has_and_takes_stay_available():
    check = _check(K06_TURN2, _ask(
        "give it to me as an edge list, with fixed lambdas of 0.2 and 0.6", ["dragon.two_layer_network"],
        omics_layers=2, settings=[("DRAGON.output_format", "as an edge list", "an edge list"),
                                  ("DRAGON.lambda1", "fixed lambdas", "0.2"), ("DRAGON.lambda2", "fixed lambdas", "0.6")]))
    result = _result(check)
    assert result.status == "available" and result.delivered_by == ["dragon.two_layer_network"]
    assert not result.limits and run_check_verdict(check, "run_dragon")["verdict"] == "agrees"


def test_a_value_outside_the_controls_range_is_not_given():
    check = _check("Run DRAGON with lambda1 1.5 on our two layers.", _ask(
        "Run DRAGON with lambda1 1.5 on our two layers", ["dragon.two_layer_network"], omics_layers=2,
        named="DRAGON", named_quote="DRAGON", settings=[("DRAGON.lambda1", "lambda1", "1.5")]))
    assert _result(check).status == "not_available"
    assert "lambda1 must be between 0 and 1" in _result(check).limits[0]


def test_gpu_is_a_value_this_runtime_does_not_take():
    task = "Run OTTER on our GPU for the 64 samples."
    check = _check(task, _ask("Run OTTER on our GPU for the 64 samples", ["otter.tf_gene_network"],
                              named="OTTER", named_quote="OTTER", settings=[("OTTER.computing", "on our GPU", "GPU")]))
    assert _result(check).status == "not_available" and "computing=gpu is not enabled" in _result(check).limits[0]


# --- MX05: a workflow that takes no settings at all ---------------------------------------------------------------

MX05 = ("Please fit GIRAFFE to our 45 pancreatic islet samples with the motif prior and PPI we sent, but set its "
        "regularisation lambda to 0.5 instead of the default.")


def test_mx05_giraffe_takes_no_settings_but_is_still_offered():
    check = _check(MX05, _ask(MX05.rstrip("."), ["giraffe.signed_regulation", "giraffe.tf_activity"],
                              named="GIRAFFE", named_quote="GIRAFFE", scale="whole_cohort", regulator_kinds=["tf"],
                              needs_sign=True, input_network="regulator_gene",
                              settings=[("OTTER.lam", "its regularisation lambda", "0.5")]))
    result = _result(check)
    assert result.status == "not_available" and "passes no settings" in result.limits[0]
    assert result.defaults == ["giraffe.signed_regulation"]  # the sign the reading asks for leaves only it
    assert not check.full_gap  # GIRAFFE's guidance stays: fitting it is what R1 asks, and it is given
    assert "GIRAFFE itself can still run" in understanding_paragraph(check)


# --- N36 / its pair: a named model that is not registered ---------------------------------------------------------

N36 = "Can you infer TF activities for our 70 samples with the TIGER Bayesian model specifically?"


def test_n36_an_unregistered_model_is_not_given_and_giraffe_is_only_an_alternative():
    check = _check(N36, _ask("infer TF activities", ["giraffe.tf_activity"], named="unregistered",
                             named_quote="the TIGER Bayesian model", asked_as="question", scale="per_sample",
                             regulator_kinds=["tf"], samples=70, samples_quote="70 samples"))
    result = _result(check)
    assert result.status == "not_available" and result.instead == ["giraffe.tf_activity"]
    assert 'no registered method or variant "the TIGER Bayesian model"' in result.limits[0]
    assert check.full_gap
    reply = full_gap_reply(check)
    assert 'GIRAFFE gives this result with its own method instead -- an alternative, not "the TIGER' in reply
    assert "can give this as you asked it" in reply
    assert second_opinion_pairs(check, ["run_giraffe"]) == []


def test_n36_pair_naming_giraffe_is_available():
    task = "Can you infer TF activities for our 70 samples with GIRAFFE specifically?"
    check = _check(task, _ask("infer TF activities", ["giraffe.tf_activity"], named="GIRAFFE", named_quote="GIRAFFE",
                              asked_as="question", scale="per_sample", regulator_kinds=["tf"]))
    assert _result(check).status == "available" and not _result(check).limits


# --- N12 / MX18 / P09: a LIONESS version that is not registered ---------------------------------------------------

N12 = "Can we get one OTTER network per sample, LIONESS-style, for our 50 kidney biopsies?"
N12_ASK = dict(asked_as="question", scale="per_sample", regulator_kinds=["tf"], input_network="gene_gene")


def test_n12_lioness_otter_is_never_credited_to_lioness_panda():
    for named, said in (("unregistered", "OTTER network per sample, LIONESS-style"), ("OTTER", "OTTER")):
        # As recorded: OTTER's near miss cited and nothing credited -- the second opinion then credited LIONESS-PANDA.
        check = _check(N12, _ask("one OTTER network per sample, LIONESS-style", (), ["otter.no_per_sample"],
                                 named=named, named_quote=said, **N12_ASK), has=["50 kidney biopsies"])
        assert check.full_gap and _result(check).status == "not_available"
        assert second_opinion_pairs(check, ["run_lioness_panda", "run_otter"]) == []
    # Had the check credited LIONESS-PANDA itself, it is kept apart as an alternative, not the result.
    check = _check(N12, _ask("one OTTER network per sample, LIONESS-style", ["lioness_panda.per_sample_networks"],
                             named="OTTER", named_quote="OTTER", **N12_ASK))
    result = _result(check)
    assert result.status == "not_available" and result.instead == ["lioness_panda.per_sample_networks"]
    assert result.limits[0] == "NetZoo's OTTER does not give this result"
    assert "LIONESS-PANDA gives this result with its own method instead" in understanding_paragraph(check)


def test_mx18_r1_otters_aggregate_network_and_p09_lioness_puma_stay_available():
    task = ("Can you give us OTTER's aggregate network for the 64 endometriosis samples (motif, PPI and expression "
            "supplied) and the per-sample LIONESS-OTTER networks too?")
    check = _check(task,
                   _ask("OTTER's aggregate network for the 64 endometriosis samples", ["otter.tf_gene_network"],
                        named="OTTER", named_quote="OTTER's", scale="whole_cohort", regulator_kinds=["tf"]),
                   _ask("the per-sample LIONESS-OTTER networks", ["lioness_panda.per_sample_networks"],
                        named="unregistered", named_quote="LIONESS-OTTER", scale="per_sample", regulator_kinds=["tf"]))
    first, second = check.results()
    assert first.status == "available" and second.status == "not_available" and not check.full_gap
    p09 = ("How do we get a separate TF-and-miRNA-to-gene network for each of 75 ovarian cancer patients? Expression, "
           "the motif prior with miRNA edges, PPI and the miRNA list are all ready.")
    check = _check(p09, _ask("a separate TF-and-miRNA-to-gene network for each of 75 ovarian cancer patients",
                             ["lioness_puma.per_sample_networks"], asked_as="question", scale="per_sample",
                             regulator_kinds=["tf", "mirna"], samples=75, samples_quote="75 ovarian cancer patients"))
    assert _result(check).status == "available"
    named = _ask("a LIONESS-PUMA network for each patient", ["lioness_puma.per_sample_networks"], named="LIONESS",
                 named_quote="LIONESS-PUMA", scale="per_sample", regulator_kinds=["tf", "mirna"])
    assert _result(_check("We want a LIONESS-PUMA network for each patient.", named)).status == "available"


# --- N13 / P20: too few samples -----------------------------------------------------------------------------------

N13 = ("We have exactly two RNA-seq samples, one per patient, and want a sample-specific co-expression network for "
       "each of the two.")
PER_SAMPLE_COEXPRESSION = ["lioness_coexpression.per_sample_networks", "bonobo.per_sample_networks"]


def test_n13_two_samples_are_too_few_for_any_per_sample_network():
    check = _check(N13, _ask("a sample-specific co-expression network for each of the two.", PER_SAMPLE_COEXPRESSION,
                             scale="per_sample", samples=2, samples_quote="exactly two RNA-seq samples"),
                   has=["We have exactly two RNA-seq samples, one per patient"])
    result = _result(check)
    assert result.status == "not_available" and check.full_gap and not result.defaults
    assert any("BONOBO needs at least 3 samples; the request has 2" == limit for limit in result.limits)
    assert any(limit.startswith("LIONESS-COEXPRESSION needs at least 3") for limit in result.limits)
    assert second_opinion_pairs(check, ["run_bonobo", "run_lioness_coexpression", "run_lioness_panda"]) == []


def test_p20_nine_samples_are_enough():
    task = ("We have only 9 log-transformed, centred RNA-seq profiles from rare paediatric tumours and want a "
            "co-expression network for each one, with a p-value per edge so we can keep only confident edges.")
    check = _check(task, _ask("a co-expression network for each one", PER_SAMPLE_COEXPRESSION, scale="per_sample",
                              samples=9, samples_quote="only 9 log-transformed, centred RNA-seq profiles"))
    assert _result(check).status == "available" and set(_result(check).delivered_by) == set(PER_SAMPLE_COEXPRESSION)


# --- N22 / P19: the LIONESS-DRAGON cap ----------------------------------------------------------------------------

N22 = "Run LIONESS-DRAGON on all 20,000 genes and 800 proteins for our 300 patients and keep every per-patient network."


def test_n22_the_per_sample_table_would_exceed_the_cap():
    check = _check(N22, _ask(
        "LIONESS-DRAGON on all 20,000 genes and 800 proteins for our 300 patients",
        ["lioness_dragon.per_sample_networks"], named="LIONESS-DRAGON", named_quote="LIONESS-DRAGON",
        scale="per_sample", omics_layers=2, samples=300, samples_quote="our 300 patients",
        features=[(20000, "all 20,000 genes"), (800, "800 proteins")]))
    result = _result(check)
    assert result.status == "not_available" and check.full_gap
    assert "20,000,000 values" in result.limits[0] and "64,892,880,000" in result.limits[0]
    assert run_check_verdict(check, "run_lioness_dragon")["verdict"] == "gap"


def test_p19_within_the_cap_and_with_lambdas_in_range():
    task = ("Run it now: LIONESS-DRAGON on the paired miRNA (300 features) and mRNA (600 features) tables from 30 "
            "endometrial tumours, with lambda1 0.3 and lambda2 0.4.")
    check = _check(task, _ask(
        "LIONESS-DRAGON on the paired miRNA (300 features) and mRNA (600 features) tables",
        ["lioness_dragon.per_sample_networks"], named="LIONESS-DRAGON", named_quote="LIONESS-DRAGON",
        scale="per_sample", omics_layers=2, samples=30, samples_quote="30 endometrial tumours",
        features=[(300, "300 features"), (600, "600 features")],
        settings=[("LIONESS-DRAGON.lambda1", "lambda1", "0.3"), ("LIONESS-DRAGON.lambda2", "lambda2", "0.4")]))
    assert _result(check).status == "available"
    assert run_check_verdict(check, "run_lioness_dragon")["verdict"] == "agrees"


# --- what the code keeps of a reading ---------------------------------------------------------------------------

def test_only_words_in_the_request_are_kept():
    ask = proposal_model(1).model_validate({"s1": {"role": "asks", "has": [], "about_methods": [], "asks": [_ask(
        "infer TF activities", ["giraffe.tf_activity"], named="GIRAFFE", named_quote="infer TF activities",
        settings=[("OTTER.lam", "a lambda of 0.9", "0.9")], samples=3, samples_quote="70 samples",
        features=[(5000, "5,000 genes")])]}}).s1.asks[0]
    # A registered method the words do not name, a count the words do not state, quotes not in the request: none kept.
    assert verified_method(N36, ask) == {}
    unregistered = ask.model_copy(update={"named_method": "unregistered", "named_method_quote": "TIGER Bayesian model",
                                          "sample_count": 70})
    assert verified_method(N36, unregistered) == {
        "named": "unregistered", "named_quote": "TIGER Bayesian model", "samples": 70, "samples_quote": "70 samples"}


def test_a_reading_from_before_m1_is_unchanged():
    old = {key: value for key, value in _ask(
        "a sample-specific co-expression network for each of the two.", PER_SAMPLE_COEXPRESSION,
        scale="per_sample").items()
        if key not in ("named_method", "named_method_quote", "settings", "sample_count", "sample_count_quote",
                       "feature_counts")}
    check = _check(N13, old)
    assert _result(check).status == "available" and not _result(check).method and not _result(check).limits
    assert method_fitting({}, ["bonobo.per_sample_networks"]) == (["bonobo.per_sample_networks"], [], [], [])


def test_a_redirect_never_offers_a_workflow_outside_the_named_method():
    check = _check(N12, _ask("one OTTER network per sample, LIONESS-style", (), ["otter.no_per_sample"],
                             named="OTTER", named_quote="OTTER", **N12_ASK))
    removed = check.model_copy(update={"requirements": [check.requirements[0].model_copy(update={
        "violations": ['OTTER does not meet "LIONESS-style"']})]})
    assert redirect_pairs(removed, ["run_lioness_panda", "run_lioness_coexpression"]) == []
