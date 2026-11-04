"""A request to normalize expression -- SNAIL (PySNAIL), RLE (DESeq2), TMM (edgeR) or quantile -- read before
workflow matching. One method runs per step; a request naming two methods is left to routing.

The semantic interpreter reads results the registry's workflows produce; normalization produces none, so a plain
"Normalize my counts with SNAIL" reads as "no registered result" and the goal is asked (live 2026-11-04). Like the
STRING download, this preparation step is taken from the request's own words: the method or the act named, and a
command rather than a question.

"Normalize ... and then run PANDA" names one workflow that reads an expression matrix: the normalization is planned
now and the workflow is recorded as `then_action`, planned on a later turn with the normalized matrix (no step runs
unconfirmed, and the two are never run as one). Any other workflow named alongside is left to routing.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from .contracts import RequestedOutcome, TaskDecision
from .data.normalization import METHOD_LABELS
from .interpretation.extraction import _task_path
from workflow_registry import ACTION_DEFINITIONS

from .method_names import LIONESS_FAMILY, registered_workflows
from .routing.capability import has_explicit_advice_intent, is_workflow_information_request
from .routing.path_tokens import is_path_token
from .settings import INPUT_ROLE_FIELDS

if TYPE_CHECKING:
    from .contracts.outcomes import SemanticInterpretation

__all__ = ["CHAINABLE_ACTIONS", "chained_action", "named_methods", "normalization_decision", "normalization_requested"]

_METHOD_WORDS = {
    "snail": r"(?<![A-Za-z0-9])(?:py)?snail(?![A-Za-z0-9])|qsmooth|smooth[- _]?quantile",
    "rle": r"(?<![A-Za-z0-9])rle(?![A-Za-z0-9])|deseq2?|median[- _]of[- _]ratios?",
    "tmm": r"(?<![A-Za-z0-9])tmm(?![A-Za-z0-9])|edger",
    "quantile": r"(?<!smooth )(?<!smooth-)(?<!smooth_)quantile[- _]normali[sz]|preprocess[- _]?core|normalize\.quantiles",
}
_METHODS = {method: re.compile(words, re.I) for method, words in _METHOD_WORDS.items()}
_SNAIL = re.compile("|".join(f"(?:{words})" for words in _METHOD_WORDS.values()), re.I)  # any method named
_NORMALIZE_EXPRESSION = re.compile(
    r"normali[sz]\w*\b.{0,80}?\b(?:counts?|expression|matrix|rna-?seq)\b"
    r"|\b(?:counts?|expression|matrix|rna-?seq)\b.{0,40}?normali[sz]"
    r"|(?:標準化|正規化|常態化)",
    re.I | re.S,
)
_NEGATED = re.compile(
    r"\b(?:do\s*n[o']t|don't|never|without|no|skip|not)\s+(?:\w+\s+){0,2}"
    r"(?:normali[sz]|snail|qsmooth|rle\b|tmm\b|deseq|edger|quantile)"
    r"|(?:不要|不用|不需要|別|勿).{0,6}(?:標準化|正規化|常態化|snail)",
    re.I,
)
_COMMAND = re.compile(
    r"(?:^|[.;!\n]\s*|\b(?:please|pls|can you|could you)\s+)"
    r"(?:normali[sz]e|run|apply|use|perform|do)\b"
    r"|請|幫我|做",
    re.I,
)
_PATH_CHUNK = re.compile(r"[^\s\"'`()\[\]{}<>，。；：、「」（）]+")


# Workflows that read the expression matrix a normalization writes. BONOBO is left out: it needs log-transformed,
# centered values, and every method here writes count-scale (or CPM) values.
CHAINABLE_ACTIONS = frozenset(
    action for action in registered_workflows().values()
    if action != "run_bonobo" and "expression_file" in {
        *ACTION_DEFINITIONS[action].required_inputs, *ACTION_DEFINITIONS[action].optional_inputs,
        *(field for group in ACTION_DEFINITIONS[action].required_input_groups for field in group),
    }
)
# The act of normalizing, not a description of data already normalized ("my SNAIL-normalized counts").
_NORMALIZE_ACT = re.compile(
    r"\bnormali[sz](?:e|ing)\b|\b(?:run|apply|use|with)\s+(?:the\s+)?(?:py)?(?:snail|qsmooth|rle|tmm|deseq2?|edger)\b"
    r"|(?:先|請|幫我).{0,10}(?:標準化|正規化|常態化)",
    re.I,
)


def _named_workflows(task: str) -> list[str]:
    """The workflows the request names, longest name first ("LIONESS-PANDA" is not also "PANDA")."""
    workflows = registered_workflows()
    spans: list[tuple[int, int, str]] = []
    for name in sorted([*workflows, LIONESS_FAMILY], key=len, reverse=True):
        for found in re.finditer(rf"(?<![A-Za-z0-9]){re.escape(name)}(?![A-Za-z0-9])", task, re.I):
            if not any(start <= found.start() and found.end() <= end for start, end, _ in spans):
                spans.append((found.start(), found.end(), name))
    return list(dict.fromkeys(workflows.get(name, name) for _, _, name in spans))


def _names_network_workflow(task: str) -> bool:
    return bool(_named_workflows(task))


def chained_action(task: str) -> str | None:
    """The one workflow a "normalize, then run it" request names, when it reads a normalized expression matrix."""
    named = _named_workflows(task)
    if len(named) != 1 or named[0] not in CHAINABLE_ACTIONS or not _NORMALIZE_ACT.search(task):
        return None
    return named[0]


def named_methods(task: str) -> list[str]:
    """The normalization methods the request names (SNAIL when it names none)."""
    return [method for method, words in _METHODS.items() if words.search(task)]


def normalization_requested(task: str, interpretation: SemanticInterpretation | None = None) -> bool:
    """The request asks, now, for one normalization of an expression matrix (and at most a workflow after it)."""
    if not (_SNAIL.search(task) or _NORMALIZE_EXPRESSION.search(task)):
        return False
    if len(named_methods(task)) > 1:  # one method per step; "compare RLE and TMM" is not read as one of them
        return False
    if _NEGATED.search(task) or is_workflow_information_request(task) or has_explicit_advice_intent(task):
        return False
    if _names_network_workflow(task) and chained_action(task) is None:
        return False
    commanded = interpretation is not None and interpretation.request_mode == "execute"
    return commanded or bool(_COMMAND.search(task.strip()))


def _request_paths(task: str) -> dict[str, str]:
    """The request's own file roles: labelled groups and output, and the one remaining path as the matrix.

    "Normalize the counts in /data/counts.tsv" labels its matrix "counts", which is no expression alias for the
    other workflows; here, with the groups file and the output taken out, a single path left can only be the matrix.
    """
    paths: dict[str, str] = {}
    for field in ("groups_file", "output_file", "expression_file"):
        if value := _task_path(task, field):
            paths[field] = value.rstrip(".,;")
    if "groups_file" not in paths and (
        found := re.search(r"\b(?:groups?|tissues?|conditions?)\b[^/~\n]{0,40}?\s((?:/|\./|\.\./|~)\S+|\S+\.(?:tsv|txt|csv|tab))", task, re.I)
    ) and is_path_token(found.group(1).rstrip(".,;")):
        paths["groups_file"] = found.group(1).rstrip(".,;")
    if "output_file" not in paths and (
        found := re.search(r"\b(?:write|save|store|output)\b[^/~.]{0,40}?\b(?:to|as|in|at|into)\s+(\S+)", task, re.I)
    ) and is_path_token(found.group(1)):
        paths["output_file"] = found.group(1).rstrip(".,;")
    if "expression_file" not in paths:
        # Files labelled for the chained workflow's other roles ("motif /data/motif.tsv") are not the matrix.
        others = {value.rstrip(".,;") for field in INPUT_ROLE_FIELDS - {"expression_file", "groups_file"}
                  if (value := _task_path(task, field))}
        taken = {*paths.values(), *others}
        rest = [chunk.rstrip(".,;:!?") for chunk in _PATH_CHUNK.findall(task)]
        rest = list(dict.fromkeys(chunk for chunk in rest if is_path_token(chunk) and chunk not in taken))
        if len(rest) == 1:
            paths["expression_file"] = rest[0]
    return paths


def normalization_decision(task: str, interpretation: SemanticInterpretation | None = None) -> TaskDecision | None:
    if not normalization_requested(task, interpretation):
        return None
    method = next(iter(named_methods(task)), "snail")
    if (explicit := re.search(r"\bnormalization_method\s*=\s*(snail|rle|tmm|quantile)\b", task, re.I)):
        method = explicit.group(1).lower()
    return TaskDecision(
        **_request_paths(task),
        action="normalize_expression", in_scope=True, should_execute=True,
        intent_type="prepare_input", confidence=1.0,
        reason=f"Normalize the expression matrix with {METHOD_LABELS[method]}.",
        requested_outcome=RequestedOutcome(
            operation="prepare", artifact_type="expression_matrix", granularity="not_applicable",
        ),
        capability_match_status="exact", match_basis="semantic",
        matched_actions=["normalize_expression"],
        then_action=chained_action(task),
        normalization_method=method,
    )
