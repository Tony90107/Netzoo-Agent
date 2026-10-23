"""The shape of setting words (ROUND-20 rule A, harness repair P2 b): what a reply may say about a setting the
reading typed. Shared by `stated_reasons` (what a reply says) and `method_conditions` (what is set apart from an ask)."""

from __future__ import annotations

import re

from ..contracts.capability_check import CheckedRequirement
from ..workflow_conditions import conditions_for

__all__: list[str] = []


_IDENTIFIER = re.compile(r"(?<![\w.])(?:[A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_]*[A-Za-z0-9]|[A-Za-z]+\d+[A-Za-z0-9]*)(?![\w.])")
"""A parameter-shaped word the user wrote: with an underscore (lambda_inter, save_pvals) or letters then digits
(lambda2, L1)."""


def _unbound(item: CheckedRequirement) -> list[str]:
    """The registered settings (WORKFLOW.control) the reading typed on words naming another parameter.

    Harness repair P2 (b), spec A21. Live 2026-10-23 H18 typed "a lambda_inter of 0.2" as DRAGON.lambda2, and the reply
    said "lambda1 and lambda2 must be supplied together"; DRAGON has no lambda_inter. Words that name no parameter are
    left to the reading (C17 "the transcript layer's shrinkage is fixed at 0.3" is lambda1, and the pair rule is its
    gold reason); words naming one must name this control or one of its allowed values.
    """
    found = []
    for setting in item.method.get("settings") or []:
        workflow, _, control = (setting.get("name") or "").partition(".")
        conditions = conditions_for(workflow) if control else None
        limit = conditions.settings.get(control) if conditions is not None else None
        if limit is None:
            continue
        own = {_plain(control), *(_plain(str(value)) for value in limit.allowed_values),
               *(_plain(str(name)) for name, _ in limit.value_names)}
        words = _PATH.sub(" ", f"{setting.get('quote') or ''} {setting.get('value') or ''}")
        said = {_plain(word) for word in _IDENTIFIER.findall(words)}
        if said and not said & own:
            found.append(setting["name"])
    return found


_PATH = re.compile(r"\S*/\S*|[\w.-]*[A-Za-z_][\w-]*\.[A-Za-z][A-Za-z0-9]{0,7}\b")
"""A path or a file name with its extension (agg_dragon.tsv, condor_brain/), never a number (0.001, 1e-4)."""
_SHAPED = re.compile(r"\d|_|(?<![\w.])\.[A-Za-z][A-Za-z0-9]{0,7}\b")
"""A number, an identifier (lambda_inter, L1) or a bare extension (.parquet)."""


def _settable(workflow: str, words: str) -> bool:
    """Whether "W has no setting for <words>" can be said, from the shape of the words and W's own contract.

    The words (with the value stated for them), without file names and paths, must hold a value something could be set
    to -- a number, an identifier or a bare extension -- and name none of W's controls or allowed values: DRAGON's
    output_format allows edge_list, so "no setting for edge list" is false. Words of neither shape ("start it right away", "header row, gene IDs in the
    first column", a design table's description) were read as a setting by the model and are none (ROUND-19 A: J20,
    C51, C57, C32 p5r); "learning rate 1e-4", "lambda_inter of 0.2", "L1 (lasso)" and ".parquet file" are said.
    """
    rest = _PATH.sub(" ", words)
    if not _SHAPED.search(rest):
        return False
    conditions = conditions_for(workflow)
    own = [] if conditions is None else [*conditions.settings, *(str(value) for limit in conditions.settings.values()
                                                                  for value in limit.allowed_values)]
    plain = _plain(rest)
    return not any(re.search(rf"(?<![\w.]){re.escape(_plain(name))}(?!\w)", plain) for name in own if _plain(name))


def _plain(text: str) -> str:
    return " ".join(text.replace("_", " ").casefold().split())
