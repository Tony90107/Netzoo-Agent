"""ROUND-18: a result naming a registered workflow that nothing was credited to still says why that workflow cannot
run as asked, from its own contract (live 2026-10-21 H40, C08: "not matched to any registered workflow")."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from test_m3_method_fitting import _check  # noqa: E402
from test_method_conditions import _ask  # noqa: E402

from netzoo_agent_core.interpretation.method_conditions import named_limits  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import understanding_paragraph  # noqa: E402

H40 = ("I'd like GIRAFFE run on 75 AML samples with a custom learning rate of 0.001, 5,000 iterations and a heavier "
       "weight on the PPI term in the loss - with the defaults it seemed to stop before the TF activities stabilised.")


def test_the_named_workflows_own_contract_judges_settings_typed_for_another():
    method = {"named": "GIRAFFE", "named_quote": "GIRAFFE",
              "settings": [{"name": "OTTER.eta", "quote": "a custom learning rate of 0.001", "value": "0.001"}]}
    assert named_limits(method) == ['NetZoo runs GIRAFFE with its package defaults and passes no settings to it, so '
                                    '"a custom learning rate of 0.001" cannot be applied']
    assert named_limits({"named": "LIONESS-PANDA", "named_quote": "LIONESS-PANDA", "samples": 2})
    # a named workflow its contract does not stop, and an unregistered or absent name, add nothing
    assert named_limits({"named": "PANDA", "named_quote": "PANDA"}) == []
    assert named_limits({"named": "none"}) == [] and named_limits({}) == []


def test_an_uncredited_named_run_is_declined_with_its_reason_not_as_unmatched():
    settings = [("OTTER.eta", "a custom learning rate of 0.001", "0.001"), ("OTTER.iterations", "5,000 iterations",
                                                                           "5,000")]
    check = _check(H40, _ask("I'd like GIRAFFE run on 75 AML samples", [], named="GIRAFFE", named_quote="GIRAFFE",
                             settings=settings))
    [row] = check.results()
    assert row.status == "not_available" and row.blocks == ["GIRAFFE"] and row.delivered_by == []
    assert "passes no settings to it" in row.limits[0]
    paragraph = understanding_paragraph(check)
    assert "not matched to any registered workflow" not in paragraph and "passes no settings" in paragraph
