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

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.capability_check import RunVerdict, proposal_model, unstated_conditions  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import (  # noqa: E402
    apply_second_opinion, build_capability_check, full_gap_reply, method_fitting, redirect_pairs, request_sentences,
    second_opinion_pairs, understanding_paragraph, verified_method,
)
from netzoo_agent_core.interpretation.run_check import run_check_verdict  # noqa: E402
from netzoo_agent_core.interpretation.run_hold import held_run_reply  # noqa: E402

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


def _check(task, *asks, has=(), about=(), whole=None):
    """One proposal: every ask in the sentence it quotes, `has` and `about` (methods questions) in theirs; `whole` the
    request-level method fields."""
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
    for quote in about:
        index = next(i for i, text in enumerate(sentences, 1) if quote in text)
        readings[f"s{index}"]["about_methods"].append(quote)
        readings[f"s{index}"]["role"] = "methods_question"
    if whole is not None:
        named, said, settings = whole
        readings["conditions"] = {**unstated_conditions(), "named_method": named, "named_method_quote": said,
                                  "settings": [{"name": n, "quote": q, "value_quote": v} for n, q, v in settings]}
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
    verdict = run_check_verdict(check, "run_otter")
    assert verdict["verdict"] == "gap" and verdict["results"][0]["limited"] is True
    held = held_run_reply(TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=1.0,
                                       reason="held", recommended_actions=["run_otter"],
                                       run_verdict=RunVerdict(action="run_otter", verdict="gap", held=True,
                                                              results=verdict["results"])),
                          understanding_paragraph(check))
    assert "it cannot run as you asked (above)" in held and "Tell me to run OTTER anyway" in held
    line = understanding_paragraph(check)
    assert "not available here as asked" in line and "OTTER itself can still run" in line
    assert "no registered workflow produces this" not in line
    # A second opinion may credit OTTER only as itself, with its own settings -- never the result as asked (m1b MX05).
    gap = check.model_copy(update={"full_gap": True})
    pairs = second_opinion_pairs(gap, ["run_otter", "run_panda"])
    assert [action for _index, action, _keys in pairs] == ["run_otter"]
    credited = apply_second_opinion(gap, pairs, ["all"])
    assert _result(credited).status == "not_available" and not _result(credited).delivered_by
    assert _result(credited).defaults and not credited.full_gap


K06_TURN2 = "Please give it to me as an edge list, with fixed lambdas of 0.2 and 0.6."


def test_k06_settings_dragon_has_and_takes_stay_available():
    check = _check(K06_TURN2, _ask(
        "give it to me as an edge list, with fixed lambdas of 0.2 and 0.6", ["dragon.two_layer_network"],
        omics_layers=2, settings=[("DRAGON.output_format", "as an edge list", "an edge list"),
                                  ("DRAGON.lambda1", "fixed lambdas", "0.2"), ("DRAGON.lambda2", "fixed lambdas", "0.6")]))
    result = _result(check)
    assert result.status == "available" and result.delivered_by == ["dragon.two_layer_network"]
    assert not result.limits and run_check_verdict(check, "run_dragon")["verdict"] == "agrees"


def test_enum_settings_are_checked_and_bound_with_the_same_choices():
    from netzoo_agent_core.interpretation.method_conditions import unbound_settings, unresolved_settings, verified_controls

    for words, allowed, bound in (("half", False, None), ("single or double", True, None),
                                  ("single precision", True, "single"), ("double", True, "double")):
        task = f"Run OTTER with precision set to {words} to build a TF-gene network."
        check = _check(task, _ask(task, ["otter.tf_gene_network"], named="OTTER", named_quote="OTTER",
                                 scale="whole_cohort", regulator_kinds=["tf"],
                                 settings=[("OTTER.precision", "precision", words)]))
        assert (run_check_verdict(check, "run_otter")["verdict"] == "agrees") is allowed
        assert verified_controls(check, "run_otter").get("precision") == bound
        if words == "single or double":
            # Both choices are supported; the unresolved choice is held rather than claimed impossible.
            assert unresolved_settings(_result(check).method, ["otter.tf_gene_network"])
            assert unbound_settings(check, "run_otter") == ["precision"]


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
    # m1b: the ask's own words name OTTER LIONESS-style, a LIONESS version NetZoo does not have.
    assert result.limits[0] == 'NetZoo has no registered method or variant "one OTTER network per sample, LIONESS-style"'
    assert "LIONESS-PANDA gives this result with its own method instead" in understanding_paragraph(check)
    # m1b N12 as recorded: typed LIONESS with "LIONESS-style" and credited to LIONESS-PANDA.
    check = _check(N12, _ask("one OTTER network per sample, LIONESS-style", ["lioness_panda.per_sample_networks"],
                             named="LIONESS", named_quote="LIONESS-style", **N12_ASK))
    assert _result(check).status == "not_available" and _result(check).method["named"] == "unregistered"


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


def test_a_lioness_version_the_registry_lacks_names_no_registered_method():
    # m1a MX18: "LIONESS-OTTER" typed LIONESS, which stands for every LIONESS-X.
    task = "Can you give us the per-sample LIONESS-OTTER networks too?"
    check = _check(task, _ask("the per-sample LIONESS-OTTER networks", ["lioness_panda.per_sample_networks"],
                              named="LIONESS", named_quote="LIONESS-OTTER", scale="per_sample", regulator_kinds=["tf"]))
    result = _result(check)
    assert result.method["named"] == "unregistered" and result.status == "not_available"
    assert result.instead == ["lioness_panda.per_sample_networks"]
    # A registered LIONESS version, or LIONESS alone, still stands for itself.
    for said in ("LIONESS-PANDA", "LIONESS"):
        task = f"We want a {said} network for each patient."
        check = _check(task, _ask(f"a {said} network for each patient", ["lioness_panda.per_sample_networks"],
                                  named="LIONESS", named_quote=said, scale="per_sample", regulator_kinds=["tf"]))
        assert _result(check).status == "available", said


def test_an_unmapped_request_offers_the_workflow_that_runs_with_its_own_settings():
    # m1a MX04: "run OTTER ... on the GPU" read as artifact unknown; the reply said no workflow is offered.
    from evaluate_routing import ProjectPolicyLoader
    from netzoo_agent_core.contracts import TaskDecision
    from netzoo_agent_core.interpretation.unmapped_routes import unmapped_reply

    task = "Go ahead and run OTTER on the 110 lung samples on the GPU so it finishes faster."

    def reply_for(check):
        decision = TaskDecision.model_validate({
            "action": "no_tool", "in_scope": True, "should_execute": False, "confidence": 1.0, "reason": "unmapped",
            "match_basis": "semantic", "capability_check": check.model_dump(),
            "requested_outcome": {"operation": "unknown", "input_artifacts": ["expression_matrix"],
                                  "artifact_type": "unknown", "entity_types": [], "regulator_types": [],
                                  "target_types": [], "granularity": "unknown"}})
        return unmapped_reply(decision, ProjectPolicyLoader(Path(__file__).parents[1]).load())

    # The GPU joined to the ask's words: the result is asked so, and OTTER is offered with its own settings.
    check = _check(task, _ask("run OTTER", ["otter.tf_gene_network"], named="OTTER", named_quote="OTTER",
                              settings=[("OTTER.computing", "on the GPU", "GPU")]))
    reply = reply_for(check)
    assert "**OTTER**" in reply and "with its own settings instead" in reply
    assert "no workflow is offered" not in reply
    # Round m3: a24b's own wording sets the GPU apart by a clause boundary, and its gold judged it apart ("run OTTER on
    # the 110 lung samples" supported, "on the GPU so it finishes faster" not); OTTER is offered for the network, and
    # the GPU line says why it is not available.
    task = ("Go ahead and run OTTER on the 110 lung samples (motif, PPI and expression attached) on the GPU so it "
            "finishes faster.")
    check = _check(task, _ask("run OTTER", ["otter.tf_gene_network"], named="OTTER", named_quote="OTTER",
                              settings=[("OTTER.computing", "on the GPU", "GPU")]))
    network, gpu = check.results()
    assert (network.status, gpu.quote, gpu.status) == ("available", "on the GPU", "not_available")
    assert "computing=gpu is not enabled" in gpu.limits[0]
    assert '**OTTER** — for "run OTTER"' in reply_for(check)
    assert '"on the GPU" -- not available here as asked.' in understanding_paragraph(check)


# --- live m1a: the request's own method and settings, and what each setting means ----------------------------------

F1 = ("Can you run PANDA with its alpha update rate set to 0.25 on our 60 lung samples? Expression, motif prior and "
      "PPI are ready.")


def test_f1_a_setting_given_in_a_methods_question_holds_the_run():
    # As recorded: the whole question filed as a methods question, no ask; the request names PANDA and the alpha.
    check = _check(F1, about=["Can you run PANDA with its alpha update rate set to 0.25 on our 60 lung samples?"],
                   has=["Expression, motif prior and PPI are ready."],
                   whole=("PANDA", "PANDA", [("unregistered", "its alpha update rate", "0.25")]))
    result = _result(check)
    assert result.status == "not_available" and result.quote == "its alpha update rate"
    assert "has no setting" in result.limits[0] and result.defaults == ["panda.tf_gene_network"]
    assert not check.full_gap and run_check_verdict(check, "run_panda")["verdict"] == "gap"
    # Without a failing setting nothing is added: "nothing asked beyond running it" stays as it was.
    plain = _check("Can you run PANDA on our 60 lung samples?",
                   about=["Can you run PANDA on our 60 lung samples?"], whole=("PANDA", "PANDA", []))
    assert not plain.results() and run_check_verdict(plain, "run_panda")["verdict"] == "no_result"


def test_an_unregistered_method_asked_to_run_is_not_given():
    task = "Can you run GENIE3 on our 80 colon samples?"
    check = _check(task, about=[task], whole=("unregistered", "GENIE3", []))
    assert _result(check).status == "not_available" and check.full_gap
    assert 'no registered method or variant "GENIE3"' in _result(check).limits[0]


def test_the_request_method_applies_to_its_one_result_but_not_across_two():
    task = "Run OTTER with an L1 sparsity penalty of 0.1 on our 64 samples."
    whole = ("OTTER", "OTTER", [("unregistered", "an L1 sparsity penalty of 0.1", "0.1")])
    one = _check(task, _ask("Run OTTER", ["otter.tf_gene_network"], scale="whole_cohort", regulator_kinds=["tf"]),
                 whole=whole)
    assert _result(one).status == "not_available" and _result(one).defaults == ["otter.tf_gene_network"]
    # Round m3: stated in a clause of its own, the penalty is a requirement of its own and the run is still held.
    task = "Run OTTER on our 64 samples, and use an L1 sparsity penalty of 0.1."
    apart = _check(task, _ask("Run OTTER", ["otter.tf_gene_network"], scale="whole_cohort", regulator_kinds=["tf"]),
                   whole=whole)
    assert [(item.quote, item.status) for item in apart.results()] == [
        ("Run OTTER", "available"), ("an L1 sparsity penalty of 0.1", "not_available")]
    assert run_check_verdict(apart, "run_otter")["verdict"] == "partial_gap"
    task = "Build a PANDA network with its alpha at 0.25, then find communities in it."
    two = _check(task, _ask("Build a PANDA network", ["panda.tf_gene_network"], scale="whole_cohort",
                            regulator_kinds=["tf"]),
                 _ask("find communities in it", ["condor.communities"], input_network="regulator_gene"),
                 whole=("PANDA", "PANDA", [("unregistered", "its alpha", "0.25")]))
    assert [item.status for item in two.results()] == ["available", "available"]


def test_the_schema_says_what_each_setting_does():
    import json
    schema = json.dumps(proposal_model(1).model_json_schema())
    assert "OTTER.lam: Weight of gene co-expression versus the TF-TF PPI network" in schema
    assert "OTTER.gamma: L2-style regularization" in schema and "not a sparsity penalty" in schema


def test_k09_the_setting_stated_last_wins():
    # m1b K09 turn 2: the ask typed computing=GPU from "Never mind the GPU"; the request also typed CPU after it.
    task = "Never mind the GPU - CPU is fine, just use single precision."
    check = _check(task, _ask("CPU is fine", ["otter.tf_gene_network"], named="none",
                              settings=[("OTTER.computing", "GPU", "GPU")]),
                   whole=("OTTER", "OTTER", [("OTTER.computing", "GPU", "GPU"), ("OTTER.computing", "CPU is fine", "CPU"),
                                             ("OTTER.precision", "single precision", "single")]))
    result = _result(check)
    assert result.status == "available"
    assert {item["name"]: item["value"] for item in result.method["settings"]} == {
        "OTTER.computing": "CPU", "OTTER.precision": "single"}


def test_lioness_with_a_per_sample_method_is_not_a_lioness_version():
    task = "Should we use LIONESS or BONOBO for one co-expression network per sample?"
    check = _check(task, _ask("one co-expression network per sample", ["lioness_coexpression.per_sample_networks"],
                              named="LIONESS", named_quote="LIONESS", scale="per_sample", asked_as="question"))
    assert _result(check).status == "available"


def test_boolean_words_the_user_writes_are_read():
    from netzoo_agent_core.workflow_conditions import boolean_value

    for words, quote, expected in (("false", "", False), ("without", "without sparsification", False),
                                   ("don't", "don't sparsify", False), ("turned off", "sparsify", False),
                                   ("no thanks", "sparsify", False), ("with no", "with no sparsification", False),
                                   ("yes", "", True), ("turned on", "", True), ("", "sparsify the networks", True),
                                   ("", "without sparsification", False), ("", "do not save p-values", False),
                                   ("yes, turn it off", "", None), ("sparse-ish", "", None), ("", "", None)):
        assert boolean_value(words, quote) is expected, (words, quote)


def test_a_negated_boolean_without_a_value_does_not_apply_its_combination_rule():
    from netzoo_agent_core.workflow_conditions import StatedSetting, combination_issues, conditions_for

    conditions = conditions_for("BONOBO")
    for quote, issues in (("without sparsification", 0), ("sparsify", 1)):
        assert len(combination_issues(conditions, [StatedSetting("BONOBO.sparsify", quote, ""),
                                                   StatedSetting("BONOBO.delta", "delta", "0.5")])) == issues
