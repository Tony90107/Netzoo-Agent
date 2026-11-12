"""A request to normalize expression -- SNAIL (PySNAIL), RLE (DESeq2), TMM (edgeR), quantile or FPKM -- read before
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

from .contracts import InputEvidence, RequestedOutcome, TaskDecision
from .contracts.normalization import NeedReading, NormalizationChoice
from .data.normalization import METHOD_LABELS, raw_count_signal
from .interpretation.extraction import _task_path
from workflow_registry import ACTION_DEFINITIONS

from .method_names import LIONESS_FAMILY, registered_workflows
from .routing.capability import has_explicit_advice_intent, is_workflow_information_request
from .routing.path_tokens import is_path_token
from .settings import INPUT_ROLE_FIELDS

if TYPE_CHECKING:
    from .contracts.outcomes import SemanticInterpretation

__all__ = [
    "CHAINABLE_ACTIONS", "NEED_METHODS", "build_normalization_decision", "chained_action", "decision_from_needs",
    "method_named", "methods_for_needs", "named_methods", "needs_normalization_reading", "normalization_decision",
    "named_normalization_decision", "normalization_requested", "verified_needs", "METHOD_OPTION_LINES", "method_choice_evidence",
    "normalize_first_request", "with_raw_count_note", "SMOOTH_QUANTILE_NOTE",
]

_METHOD_WORDS = {
    "snail": r"(?<![A-Za-z0-9])(?:py)?snail(?![A-Za-z0-9])|qsmooth|smooth[- _]?quantile",
    "rle": r"(?<![A-Za-z0-9])rle(?![A-Za-z0-9])|deseq2?|median[- _]of[- _]ratios?",
    "tmm": r"(?<![A-Za-z0-9])tmm(?![A-Za-z0-9])|edger",
    "quantile": r"(?<!smooth )(?<!smooth-)(?<!smooth_)quantile[- _]normali[sz]|preprocess[- _]?core|normalize\.quantiles",
    "fpkm": r"(?<![A-Za-z0-9])[fr]pkm(?![A-Za-z0-9])",
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
    r"(?:normali[sz]|snail|qsmooth|rle\b|tmm\b|[fr]pkm\b|deseq|edger|quantile)"
    r"|(?:不要|不用|不需要|別|勿).{0,6}(?:標準化|正規化|常態化|snail)",
    re.I,
)
_COMMAND = re.compile(
    r"(?:^|[.;!\n]\s*|\b(?:please|pls|can you|could you)\s+)"
    r"(?:normali[sz]e|run|apply|use|perform|do|compute|calculate|convert|make|correct|adjust|rescale|scale)\b"
    r"|請|幫我|做",
    re.I,
)
_SEQUENCE = re.compile(r"\b(?:then|after(?:wards)?|before|first|followed by)\b|之後|然後|再", re.I)
_TRAILING = ".,;:!?)]}\"'"  # sentence and bracket marks after a path, never part of it
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
    r"\bnormali[sz](?:e|ing)\b|\b(?:run|apply|use|with)\s+(?:the\s+)?(?:py)?(?:snail|qsmooth|smooth[- _]?quantile|rle|tmm|[fr]pkm|deseq2?|edger)\b"
    r"|(?:先|請|幫我).{0,10}(?:標準化|正規化|常態化)",
    re.I,
)

# A question about doing the one normalization it names ("which tool does smooth quantile normalization?", "how do I
# run qsmooth on my counts?", or the bare "smooth quantile normalization"): 4 of 6 went to workflow matching and got
# the list of network results, with no word of normalization (live 2026-11-12). Like a "which tool" question about
# a network, it is answered with the method's plan; nothing runs before the matrix is given and the plan confirmed.
_DOING = re.compile(r"normali[sz]|\b(?:run|apply|use|do|perform|get)\b|\b(?:tool|method|workflow)s?\b", re.I)
# ... but not a question about the method itself: what it is, how it works, or how it compares.
_ABOUT_METHOD = re.compile(
    r"^\s*what(?:'s|\s+is|\s+are|\s+does)\s+(?:an?\s+|the\s+)?(?:py)?(?:snail|qsmooth|smooth[- _]?quantile|quantile"
    r"|rle|tmm|[fr]pkm|deseq2?|edger)\b"
    r"|\bhow\s+does\b|\bwhy\b|\bexplain\b|\bdifferen(?:ce|t)\b|\bcompar|\bversus\b|\bvs\.?\s|\bbetter\b|\bmean(?:s|ing)?\b",
    re.I,
)


def _asks_named_method(task: str) -> bool:
    return len(named_methods(task)) == 1 and bool(_DOING.search(task)) and not _ABOUT_METHOD.search(task)


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


def chained_action(task: str, *, normalizing_read: bool = False) -> str | None:
    """The one workflow a "normalize, then run it" request names, when it reads a normalized expression matrix.

    The act of normalizing is in the words, or (`normalizing_read`) the need reader read the request as one.
    """
    named = _named_workflows(task)
    if len(named) != 1 or named[0] not in CHAINABLE_ACTIONS or not (normalizing_read or _NORMALIZE_ACT.search(task)):
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
    asked = _asks_named_method(task)
    if _NEGATED.search(task) or (not asked and (is_workflow_information_request(task) or has_explicit_advice_intent(task))):
        return False
    if _names_network_workflow(task) and chained_action(task) is None:
        return False
    commanded = interpretation is not None and interpretation.request_mode == "execute"
    return asked or commanded or bool(_COMMAND.search(task.strip()))


def _request_paths(task: str) -> dict[str, str]:
    """The request's own file roles: labelled groups and output, and the one remaining path as the matrix.

    "Normalize the counts in /data/counts.tsv" labels its matrix "counts", which is no expression alias for the
    other workflows; here, with the groups file and the output taken out, a single path left can only be the matrix.
    """
    paths: dict[str, str] = {}
    for field in ("groups_file", "gene_lengths_file", "output_file", "expression_file"):
        if value := _task_path(task, field):
            paths[field] = value.rstrip(_TRAILING)
    if "groups_file" not in paths and (
        found := re.search(r"\b(?:groups?|tissues?|conditions?)\b[^/~\n]{0,40}?\s((?:/|\./|\.\./|~)\S+|\S+\.(?:tsv|txt|csv|tab))", task, re.I)
    ) and is_path_token(found.group(1).rstrip(_TRAILING)):
        paths["groups_file"] = found.group(1).rstrip(_TRAILING)
    if "gene_lengths_file" not in paths and (
        found := re.search(r"\blengths?\b[^/~\n]{0,40}?\s((?:/|\./|\.\./|~)\S+|\S+\.(?:tsv|txt|csv|tab))", task, re.I)
    ) and is_path_token(found.group(1).rstrip(_TRAILING)):
        paths["gene_lengths_file"] = found.group(1).rstrip(_TRAILING)
    if "output_file" not in paths and (
        found := re.search(r"\b(?:write|save|store|output)\b[^/~.]{0,40}?\b(?:to|as|in|at|into)\s+(\S+)", task, re.I)
    ) and is_path_token(found.group(1)):
        paths["output_file"] = found.group(1).rstrip(_TRAILING)
    if "expression_file" not in paths:
        # Files labelled for the chained workflow's other roles ("motif /data/motif.tsv") are not the matrix.
        others = {value.rstrip(_TRAILING) for field in INPUT_ROLE_FIELDS - {"expression_file", "groups_file", "gene_lengths_file"}
                  if (value := _task_path(task, field))}
        taken = {*paths.values(), *others}
        rest = [chunk.rstrip(_TRAILING) for chunk in _PATH_CHUNK.findall(task)]
        rest = list(dict.fromkeys(chunk for chunk in rest if is_path_token(chunk) and chunk not in taken))
        if len(rest) == 1:
            paths["expression_file"] = rest[0]
    return paths


# Asked for as smooth quantile normalization (qsmooth): said to be SNAIL, and why (PySNAIL's README, 2026-11-12).
SMOOTH_QUANTILE_NOTE = (
    ". NetZoo runs smooth quantile normalization with SNAIL: it is smooth quantile normalization adapted so that it "
    "does not create false co-expression between lowly expressed genes, which matters for NetZoo's co-expression "
    "based networks"
)


# What each stated need is corrected by. Sequencing depth fits two methods, so it is asked, never picked.
NEED_METHODS = {
    "sequencing_depth": ("rle", "tmm"),
    "gene_length": ("fpkm",),
    "group_differences": ("snail",),
    "same_distribution": ("quantile",),
}


def verified_needs(task: str, readings) -> list[NeedReading]:
    """The model's need readings whose quote the request contains, one per need."""
    lowered = task.casefold()
    kept: dict[str, NeedReading] = {}
    for reading in readings:
        quote = reading.text_span.strip().strip("\"'")
        if len(quote) >= 3 and quote.casefold() in lowered and reading.need not in kept:
            kept[reading.need] = NeedReading(need=reading.need, text_span=quote)
    return list(kept.values())


def methods_for_needs(needs: list[NeedReading]) -> list[str]:
    """The methods that correct every stated need; one means it is used, several mean the user chooses."""
    kinds = {reading.need for reading in needs}
    if "gene_length" in kinds:
        # FPKM divides by gene length and by library size, so it also answers a stated depth difference.
        return ["fpkm"]
    return list(dict.fromkeys(method for need in NEED_METHODS if need in kinds for method in NEED_METHODS[need]))


def method_named(task: str) -> str | None:
    """The one method the request names, or an explicit normalization_method= assignment."""
    if explicit := re.search(r"\bnormalization_method\s*=\s*(snail|rle|tmm|quantile|fpkm)\b", task, re.I):
        return explicit.group(1).lower()
    named = named_methods(task)
    return named[0] if len(named) == 1 else None


def needs_normalization_reading(task: str, interpretation: SemanticInterpretation | None = None) -> bool:
    """A command, about an expression matrix, that no registered workflow answered and that may describe a
    normalization in its own words ("make /data/counts.tsv comparable across sequencing depths"): the need reader
    is asked. A question, a negation or another named workflow is never read as one."""
    if _NEGATED.search(task) or is_workflow_information_request(task) or has_explicit_advice_intent(task):
        return False
    if _names_network_workflow(task) and (
        chained_action(task, normalizing_read=True) is None or not _SEQUENCE.search(task)
    ):  # a named workflow is only a follower: "make ... comparable, then run PANDA"
        return False
    if "expression_file" not in _request_paths(task):
        return False
    commanded = interpretation is not None and interpretation.request_mode == "execute"
    return commanded or bool(_COMMAND.search(task.strip()))


def build_normalization_decision(
    task: str, method: str | None, choice: NormalizationChoice,
) -> TaskDecision:
    then_action = chained_action(task, normalizing_read=choice.source == "need")
    """normalize_expression for this request; `method` None leaves the choice among `choice.candidates` asked."""
    label = METHOD_LABELS[method] if method else " or ".join(METHOD_LABELS[c] for c in choice.candidates)
    if method == "snail" and not re.search(r"(?<![A-Za-z0-9])(?:py)?snail(?![A-Za-z0-9])", task, re.I) and _METHODS["snail"].search(task):
        label += SMOOTH_QUANTILE_NOTE
    return TaskDecision(
        **_request_paths(task),
        action="normalize_expression", in_scope=True, should_execute=True,
        intent_type="prepare_input", confidence=1.0,
        reason=f"Normalize the expression matrix with {label}.",
        requested_outcome=RequestedOutcome(
            operation="prepare", artifact_type="expression_matrix", granularity="not_applicable",
        ),
        capability_match_status="exact", match_basis="semantic",
        matched_actions=["normalize_expression"],
        then_action=then_action,
        normalization_method=method,
        normalization_choice=choice,
    )


def decision_from_needs(task: str, needs: list[NeedReading]) -> TaskDecision:
    """The decision for a request whose method is read from its stated needs (or the default when none)."""
    if not needs:
        return build_normalization_decision(task, "snail", NormalizationChoice(source="default"))
    candidates = methods_for_needs(needs)
    method = candidates[0] if len(candidates) == 1 else None
    return build_normalization_decision(
        task, method, NormalizationChoice(source="need", needs=needs, candidates=candidates),
    )


def normalization_decision(task: str, interpretation: SemanticInterpretation | None = None) -> TaskDecision | None:
    """The request read without the need reader: the named method, or SNAIL by default."""
    if not normalization_requested(task, interpretation):
        return None
    if method := method_named(task):
        # The continuation of an asked choice carries the answer as an assignment: it was chosen, not named.
        source = "answered" if re.search(r"\bPREVIOUS_ACTION=normalize_expression\b", task) else "named"
        return build_normalization_decision(task, method, NormalizationChoice(source=source, candidates=[method]))
    return build_normalization_decision(task, "snail", NormalizationChoice(source="default"))


def named_normalization_decision(task: str) -> TaskDecision | None:
    """A commanded normalization whose method the request names, read from its words alone (2026-11-10).

    Like SPONGE, it is decided before the semantic interpreter: a named method needs no reading, and an interpreter
    whose output fails validation dropped "Normalize counts.tsv with SNAIL, using the tissue groups in groups.tsv"
    to "no registered workflow" (live 2026-11-09, 1 of 2). A request naming no method still goes to the need reader.
    """
    return normalization_decision(task) if method_named(task) else None


# One line per method for the choice: what you get · how it differs · when to use it.
METHOD_OPTION_LINES = {
    "snail": "SNAIL (PySNAIL): smooth quantile normalization within the sample groups you give · keeps real "
             "differences between groups · use with a sample-groups file (tissues, conditions)",
    "rle": "RLE (DESeq2): counts divided by a per-sample size factor, the median ratio to a pseudo-reference sample · "
           "assumes most genes do not change · use for depth differences between comparable samples",
    "tmm": "TMM (edgeR): counts per million on library sizes scaled by a trimmed mean of M-values · also adjusts "
           "when a few very abundant genes take up the reads · use for depth plus composition differences",
    "quantile": "quantile (preprocessCore): every sample takes the same value distribution · the strongest "
                "equalizing, which also removes real global differences · use when samples should be alike overall",
    "fpkm": "FPKM (edgeR rpkm): counts per kilobase of gene length per million reads · compares genes of different "
            "length within a sample · needs a gene-lengths file",
}
_NEED_WORDS = {
    "sequencing_depth": "a sequencing-depth difference",
    "gene_length": "a gene-length correction",
    "group_differences": "differences between sample groups",
    "same_distribution": "the same distribution in every sample",
}


def method_choice_evidence(decision: TaskDecision) -> list[InputEvidence]:
    """The method to ask for when the stated needs fit more than one: a missing input with the candidates."""
    choice = decision.normalization_choice
    if decision.action != "normalize_expression" or decision.normalization_method or choice is None:
        return []
    if len(choice.candidates) < 2:
        return []
    stated = "; ".join(f'{_NEED_WORDS[need.need]} ("{need.text_span}")' for need in choice.needs)
    question = (
        f"Your request states {stated}, which {len(choice.candidates)} methods correct. Which should run?\n"
        + "\n".join(f"- {METHOD_OPTION_LINES[method]}" for method in choice.candidates)
    )
    return [InputEvidence(
        field="normalization_method", status="missing", reason=question, candidates=list(choice.candidates),
    )]


def normalize_first_request(plan) -> str | None:
    """The request "Normalize first" submits for a workflow plan whose matrix looks like raw counts (2026-11-05).

    It names the matrix and the workflow's other input files as role=path, so the normalization binds the matrix
    and, once it has run, the workflow is planned on the normalized matrix with those same files. The plan's
    output paths are left out: they are the workflow's, not the normalization's.
    """
    signal = getattr(plan, "raw_counts", None)
    action = (plan.decision or {}).get("action")
    if signal is None or action not in CHAINABLE_ACTIONS:
        return None
    others = [
        f"{item.field}={item.value}" for item in plan.evidence
        if item.value and item.field in INPUT_ROLE_FIELDS and item.field != "expression_file"
    ]
    request = f"Normalize the expression matrix expression_file={signal.expression_file} first, then run {plan.workflow}"
    return request + (" with " + " ".join(others) if others else "") + "."


def with_raw_count_note(plan, action: str):
    """The plan with `raw_counts` set when its workflow reads a matrix that looks like raw counts (2026-11-05)."""
    expression = next((item.value for item in plan.evidence if item.field == "expression_file" and item.value), None)
    if action not in CHAINABLE_ACTIONS or not expression or plan.status == "respond_only":
        return plan
    return plan.model_copy(update={"raw_counts": raw_count_signal(expression)})
