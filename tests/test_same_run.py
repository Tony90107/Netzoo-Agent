"""ROUND-17 (user decision, 2026-10-21): a result resting only on a workflow another row shows cannot run as asked is
held too, with the reason, so the turn is declined and says why rather than running what is left.

Harness repair P2 (user decision, 2026-10-23): a setting the workflow cannot take while it can still run with its own
settings blocks nothing -- DO + partial, the run held for the user; a run limit (data size, sample count) still holds."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from test_m3_method_fitting import MX12, _check  # noqa: E402
from test_method_conditions import _ask  # noqa: E402

from netzoo_agent_core.contracts.capability_check import CheckedRequirement  # noqa: E402
from netzoo_agent_core.interpretation.same_run import blocked_workflows, same_run_holds  # noqa: E402

L21 = ("Please run GIRAFFE on our 44 psoriasis skin biopsies (expression, motif prior and PPI are ready), but change the "
       "optimizer: learning rate 0.0005, 5,000 iterations, and a heavier weight on the PPI term of the loss.")


def test_a_run_whose_own_settings_cannot_be_used_stays_doable_and_its_run_is_held():
    """L21: GIRAFFE takes no settings but runs with its own, so the turn is DO + partial and approves no run."""
    from netzoo_agent_core.contracts import TaskDecision
    from netzoo_agent_core.interpretation.core_decision import decide_core
    from netzoo_agent_core.interpretation.run_check import run_check_verdict

    rate = [("unregistered", "learning rate 0.0005", "0.0005"), ("unregistered", "5,000 iterations", "5,000")]
    check = _check(L21, _ask("Please run GIRAFFE", ["giraffe.tf_activity"], named="GIRAFFE", named_quote="GIRAFFE",
                             settings=rate, scale="per_sample"))
    assert same_run_holds(check) is check  # the setting rows name GIRAFFE among their defaults
    run, *settings = check.results()
    assert run.status == "available" and settings and all(item.status == "not_available" for item in settings)
    assert any('"learning rate 0.0005" cannot be applied' in reason for item in settings for reason in item.limits)
    assert run_check_verdict(check, "run_giraffe")["verdict"] == "partial_gap"  # not an approving verdict
    core = decide_core(TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="r",
                                    capability_check=check), L21)
    assert (core.kind, core.partial, core.run_allowed, core.workflows) == ("DO", True, False, ["GIRAFFE"])


def test_a_setting_whose_only_doable_row_names_no_workflow_still_holds_it():
    """C08/H18: the doable row is an attached purpose or question read as a result; listing it as available is false."""
    task = ("Can GIRAFFE be run with my own optimizer settings? I want a learning rate of 1e-4 and 2,000 iterations. "
            "I'd like to see whether these settings change that.")
    rate = [("unregistered", "learning rate of 1e-4", "1e-4"), ("unregistered", "2,000 iterations", "2,000")]
    check = _check(task, _ask("I'd like to see whether these settings change that", ["giraffe.tf_activity"],
                              settings=rate, scale="per_sample"))
    assert [item.status for item in same_run_holds(check).results()] == ["not_available"] * len(check.results())


def test_mx12_results_whose_words_name_no_workflow_are_still_held():
    """P2's known limit: "signed R" and "sample-varying TFA" do not name GIRAFFE in their own words, so code cannot tell
    them from an attached purpose (C08) and holds them as ROUND-17 did, though the a24b gold judged them doable."""
    rate = [("unregistered", "exposed custom optimizer learning rate", "0.009")]
    check = _check(MX12, _ask("signed R", ["giraffe.signed_regulation"], named="GIRAFFE", named_quote="GIRAFFE",
                              settings=rate, needs_sign=True, scale="whole_cohort"),
                   _ask("sample-varying TFA", ["giraffe.tf_activity"], named="GIRAFFE", named_quote="GIRAFFE",
                        settings=rate, scale="per_sample"))
    assert [item.status for item in same_run_holds(check).results()] == ["not_available"] * 3


def test_a_run_past_its_data_size_still_holds_every_row_of_it():
    """L13: LIONESS-DRAGON past its size cap cannot run at all, so its output sentence is not doable either."""
    task = ("Build LIONESS-DRAGON networks for each of our 200 patients from 3,000 RNA genes and 2,000 proteins. "
            "Write the per-sample edges to lioness_dragon/edges.tsv.")
    check = _check(task, _ask("Build LIONESS-DRAGON networks for each of our 200 patients",
                              ["lioness_dragon.per_sample_networks"], named="LIONESS-DRAGON",
                              named_quote="LIONESS-DRAGON", samples=200, samples_quote="200 patients",
                              features=[(3000, "3,000 RNA genes"), (2000, "2,000 proteins")], omics_layers=2,
                              scale="per_sample"),
                   _ask("Write the per-sample edges to lioness_dragon/edges.tsv",
                        ["lioness_dragon.per_sample_networks"], omics_layers=2, scale="per_sample"))
    assert [item.status for item in check.results()] == ["not_available", "available"]
    assert [item.status for item in same_run_holds(check).results()] == ["not_available", "not_available"]


def test_a_result_another_workflow_gives_stays_doable():
    task = "Build a PANDA network. Then run DRAGON on the two layers. Let it estimate both shrinkage values."
    from test_request_facts import TF, _ask2, _check2, _setting
    asks = (_ask2("Build a PANDA network", ["panda.tf_gene_network"], **TF),
            _ask2("Then run DRAGON on the two layers", ["dragon.two_layer_network"], omics_layers=2))
    scoped = _check2(task, *asks, settings=[_setting("unregistered", "estimate both shrinkage values", "",
                                                     ["Then run DRAGON on the two layers"])])
    panda, dragon, apart = same_run_holds(scoped).results()
    # P2: DRAGON runs with its own settings, so only the setting's own row is not available
    assert (panda.status, dragon.status, apart.status) == ("available", "available", "not_available")
    assert apart.defaults == ["dragon.two_layer_network"]


def test_words_naming_no_allowed_choice_and_model_judged_violations_block_nothing():
    unclear = CheckedRequirement(quote="gene IDs in the first column", kind="result", status="not_available",
                                 limits=['BONOBO\'s genes_axis requires one of auto, rows and columns; "gene IDs in the '
                                         'first column" does not identify one allowed choice'], blocks=["BONOBO"])
    judged = CheckedRequirement(quote="complete continuous values with no NAs", kind="result", status="not_available",
                                limits=['DRAGON does not meet "complete continuous values with no NAs"'])
    assert blocked_workflows(unclear) == [] and blocked_workflows(judged) == []
