"""PORCUPINE asked for on an aggregate network with no expression, refused from the user's words (dev-bank D011).

"I downloaded one published PANDA network for human liver, a single TF-by-gene weight table for the tissue as a
whole. I don't have the underlying expression data. ... find the pathways with heterogeneous regulation." The reading
put "the underlying expression data" among what the user has and typed the network only as a regulatory network, so
PORCUPINE (and LIONESS-PANDA -> PORCUPINE from expression) was offered. PORCUPINE's contract refuses aggregate
networks, and the one way to sample-specific networks (LIONESS-PANDA) needs the expression the user says is missing.

Code reads both facts from the request's words; the decline quotes them and the two contract facts. Nothing else
changes: a request that also names sample-specific networks, LIONESS, SCORPION or single cells is left as it is.
"""

from __future__ import annotations

import re

from workflow_registry import ACTION_DEFINITIONS

__all__ = ["AGGREGATE_ONLY", "NO_EXPRESSION", "porcupine_on_aggregate_core"]

NO_EXPRESSION = re.compile(
    r"\b(?:do(?:n'?t| not)|does(?:n'?t| not)|never) (?:have|had|kept|received|got)\b[^.]{0,40}\bexpression[^.]*|"
    r"\bno (?:\w+ ){0,2}expression (?:data|matrix|values|table|profiles?)\b|\bwithout (?:the |any )?(?:underlying )?"
    r"expression (?:data|matrix|values|table)\b", re.IGNORECASE)
AGGREGATE_ONLY = re.compile(
    r"\b(?:one|a single|single|an aggregate|the aggregate|aggregate|one published|a published)\b[^.]{0,60}\bnetwork\b"
    r"[^.]*|[^.]*\bas a whole\b[^.]*", re.IGNORECASE)
_PER_SAMPLE = re.compile(r"sample[- ]specific|per[- ]sample|each (?:sample|patient|donor|tumou?r)|lioness|scorpion|"
                         r"single[- ]cell|sn ?rna|sc ?rna", re.IGNORECASE)
CONTRACT = "Aggregate or co-expression networks and expression matrices are not valid inputs."


def _sentence(task: str, found) -> str:
    """The whole sentence of the request that holds the match: a quote is always the user's own words."""
    start = max(task.rfind(".", 0, found.start()), task.rfind("?", 0, found.start()), task.rfind("!", 0, found.start()))
    ends = [i for i in (task.find(".", found.end() - 1), task.find("?", found.end() - 1)) if i != -1]
    return task[start + 1:(min(ends) if ends else len(task))].strip(" ,;")


def porcupine_on_aggregate_core(core, task: str):
    """(core, action): a DO crediting PORCUPINE on a request whose only network is aggregate and which says it has no
    expression -> DECLINE with both quotes and PORCUPINE's and LIONESS-PANDA's contract facts; else the core as it came."""
    from ..contracts.core_decision import CoreDecision, DeclinedPart

    if core.kind != "DO" or "PORCUPINE" not in (core.workflows or []) or _PER_SAMPLE.search(task or ""):
        return core, "not_aggregate_porcupine"
    no_expression, aggregate = NO_EXPRESSION.search(task or ""), AGGREGATE_ONLY.search(task or "")
    if not (no_expression and aggregate):
        return core, "not_aggregate_porcupine"
    assert "expression_file" in ACTION_DEFINITIONS["run_lioness_panda"].required_inputs
    said = [_sentence(task, aggregate), _sentence(task, no_expression)]
    line = (f'You wrote "{said[0].rstrip(".")}" and "{said[1].rstrip(".")}". PORCUPINE\'s contract: "{CONTRACT}" '
            "LIONESS-PANDA builds the sample-specific networks PORCUPINE needs, but it needs the expression matrix. "
            "So PORCUPINE cannot do this as you asked.")
    evidence = {**core.evidence, "stated_inputs": {"kind_before": core.kind, "basis_before": core.basis,
                                                   "quotes": said}}
    return CoreDecision(kind="DECLINE", basis="jev_stated", evidence=evidence,
                        declined=[DeclinedPart(quote=said[0], reasons=[line], line=line)]), "declined"
