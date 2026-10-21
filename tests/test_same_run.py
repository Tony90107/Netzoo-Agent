"""ROUND-17 (user decision, 2026-10-21): a result resting only on a workflow another row shows cannot run as asked is
held too, with the reason, so the turn is declined and says why rather than running what is left."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from test_m3_method_fitting import MX12, _check  # noqa: E402
from test_method_conditions import _ask  # noqa: E402

from netzoo_agent_core.contracts.capability_check import CheckedRequirement  # noqa: E402
from netzoo_agent_core.interpretation.same_run import blocked_workflows, same_run_holds  # noqa: E402

L21 = ("Please run GIRAFFE on our 44 psoriasis skin biopsies (expression, motif prior and PPI are ready), but change the "
       "optimizer: learning rate 0.0005, 5,000 iterations, and a heavier weight on the PPI term of the loss.")


def test_a_run_whose_own_settings_cannot_be_used_is_held_with_them():
    rate = [("unregistered", "learning rate 0.0005", "0.0005"), ("unregistered", "5,000 iterations", "5,000")]
    check = _check(L21, _ask("Please run GIRAFFE", ["giraffe.tf_activity"], named="GIRAFFE", named_quote="GIRAFFE",
                             settings=rate, scale="per_sample"))
    # the check alone sets the settings apart and leaves the run doable (round m3) ...
    assert [item.status for item in check.results()][0] == "available"
    held = same_run_holds(check)
    # ... held, the run is not available either, and says which settings stop it
    run = held.results()[0]
    assert run.status == "not_available" and run.blocks == ["GIRAFFE"]
    assert any('"learning rate 0.0005" cannot be applied' in reason for reason in run.limits)
    assert all(item.status == "not_available" for item in held.results())


def test_mx12_superseded_every_result_of_the_blocked_run_is_held():
    rate = [("unregistered", "exposed custom optimizer learning rate", "0.009")]
    check = _check(MX12, _ask("signed R", ["giraffe.signed_regulation"], named="GIRAFFE", named_quote="GIRAFFE",
                              settings=rate, needs_sign=True, scale="whole_cohort"),
                   _ask("sample-varying TFA", ["giraffe.tf_activity"], named="GIRAFFE", named_quote="GIRAFFE",
                        settings=rate, scale="per_sample"))
    assert [item.status for item in same_run_holds(check).results()] == ["not_available"] * 3


def test_a_result_another_workflow_gives_stays_doable():
    task = "Build a PANDA network. Then run DRAGON on the two layers. Let it estimate both shrinkage values."
    from test_request_facts import TF, _ask2, _check2, _setting
    asks = (_ask2("Build a PANDA network", ["panda.tf_gene_network"], **TF),
            _ask2("Then run DRAGON on the two layers", ["dragon.two_layer_network"], omics_layers=2))
    scoped = _check2(task, *asks, settings=[_setting("unregistered", "estimate both shrinkage values", "",
                                                     ["Then run DRAGON on the two layers"])])
    panda, dragon, _apart = same_run_holds(scoped).results()
    assert panda.status == "available" and dragon.status == "not_available"


def test_words_naming_no_allowed_choice_and_model_judged_violations_block_nothing():
    unclear = CheckedRequirement(quote="gene IDs in the first column", kind="result", status="not_available",
                                 limits=['BONOBO\'s genes_axis requires one of auto, rows and columns; "gene IDs in the '
                                         'first column" does not identify one allowed choice'], blocks=["BONOBO"])
    judged = CheckedRequirement(quote="complete continuous values with no NAs", kind="result", status="not_available",
                                limits=['DRAGON does not meet "complete continuous values with no NAs"'])
    assert blocked_workflows(unclear) == [] and blocked_workflows(judged) == []
