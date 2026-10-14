"""Items 1-2 (2026-10-14): a decision the capability verdict approves for one request, for tests that build plans by
hand. The Plan Evaluator and the executor gate refuse an analysis run without one (`interpretation.run_check`)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.capability_check import RunVerdict  # noqa: E402
from netzoo_agent_core.interpretation.run_check import request_sha256  # noqa: E402


def approved(decision, message: str, verdict: str = "agrees"):
    """`decision` with an approving verdict for its own action, bound to `message`."""
    return decision.model_copy(update={"run_verdict": RunVerdict(
        action=decision.action, verdict=verdict, request_sha256=request_sha256(message))})


def check_reply(schema, quote: str, delivered: list[str]):
    """A capability-check reply whose first sentence asks for `quote`, credited to `delivered`; the rest background."""
    ask = {"quote": quote, "delivered_by": delivered, "not_by": [], "scale": "unstated", "omics_layers": 0,
           "data_unit": "not_stated", "regulator_kinds": [], "needs_sign": False, "input_network": "none",
           "group_membership": "not_about_groups", "time_model": "not_dynamic", "spatial": "not_spatial",
           "asked_as": "request"}
    names = [name for name in schema.model_fields if name != "conditions"]
    return schema.model_validate({name: {"role": "asks" if index == 0 else "background", "has": [],
                                         "about_methods": [], "asks": [ask] if index == 0 else []}
                                  for index, name in enumerate(names)})


class CheckingLLM:
    """Wraps a fake provider so the capability check answers with `check_reply`; every other schema is the fake's."""

    def __init__(self, inner, quote: str, delivered: list[str]):
        self.inner, self.quote, self.delivered = inner, quote, delivered

    def with_structured_output(self, schema, **kwargs):
        if schema.__name__ == "CapabilityCheckProposal":
            reply = check_reply(schema, self.quote, self.delivered)
            return type("CheckAdapter", (), {"invoke": lambda _self, _messages: reply})()
        return self.inner.with_structured_output(schema, **kwargs)

    def invoke(self, messages):
        return self.inner.invoke(messages)
