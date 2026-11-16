"""A question about a preparation step -- a normalization method (SNAIL, RLE, TMM, quantile, FPKM) or SPONGE -- answered
from what NetZoo itself says about that step (2026-11-16).

The preparation steps are no menu workflows: the semantic interpreter reads results the registry's workflows produce,
so "What is the difference between SNAIL and quantile normalization?" was answered with the fourteen network results,
and "What does SPONGE do compared with just using a motif prior with PANDA?" with "I couldn't match what you asked for
to a result any registered NetZoo workflow produces" -- read as SPONGE not being supported (live 2026-11-16). A command
to run the step is taken before the interpreter (`normalization_request`, `prior_request`); a question about it is
answered here, with the lines the run paths already use (`METHOD_OPTION_LINES`, `SMOOTH_QUANTILE_NOTE`, the SPONGE
module's own account and defaults), then the one question that picks or places the step. Nothing runs.
"""

from __future__ import annotations

import re

from workflow_registry import ACTION_DEFINITIONS

__all__ = ["PREP_CONCEPT_KIND", "prep_concept_reply", "prep_concept_result"]

PREP_CONCEPT_KIND = "prep_concept"
_CLOSING = "Nothing was selected and nothing runs before you answer.\n\nNo files were inspected and no analysis ran."
# A question about the step itself: what it is or does, how it works, how it compares, which to use.
_ABOUT = re.compile(
    r"\bwhat(?:'s|\s+is|\s+are|\s+does|\s+do)\b|\bhow\s+(?:does|do|is|are)\b|\bwhy\b|\bexplain|\bdifferen(?:ce|t)\b"
    r"|\bcompar|\bversus\b|\bvs\.?\s|\bbetter\b|\bwhich\b.{0,40}?\b(?:use|pick|choose|run)\b",
    re.I | re.S,
)
# ... not data the step already made, nor a request with a file: "PANDA on my SNAIL-normalized counts in data/x.tsv"
# asks about the run, and its own call answers it.
_NOT_ABOUT = re.compile(
    r"(?:snail|qsmooth|quantile|tmm|rle|fpkm|deseq2?|edger|sponge)[- ](?:normali[sz]ed|built|made|derived|generated)"
    r"|normali[sz]ed\s+(?:with|by|using|in)\b|(?:built|made|generated)\s+(?:with|by)\s+sponge"
    r"|(?:^|[\s=\"'(])[\w~.-]*/[\w./-]+|\b[\w-]+\.(?:tsv|csv|txt|gmt|h5ad|rds|parquet)\b",
    re.I,
)
# ... nor a study the request describes and wants analysed ("Lungs from 30 mice ... We want one regulatory network and
# to check whether TMM versus quantile normalisation changes it", a saved request): its own call answers it.
_STUDY = re.compile(r"\b(?:we|i)\s+(?:want|need|would like|'d like|plan)\b"
                    r"|\b\d+\s+(?:samples?|mice|patients?|donors?|cells?|biopsies|tumou?rs?|subjects?)\b", re.I)


def _workflow_list(actions) -> str:
    names = [ACTION_DEFINITIONS[action].workflow for action in sorted(actions)]
    return ", ".join(names[:-1]) + " and " + names[-1] if len(names) > 1 else "".join(names)


def _normalization_part(methods: list[str]) -> list[str]:
    from ..normalization_request import _NEED_WORDS, CHAINABLE_ACTIONS, METHOD_OPTION_LINES, SMOOTH_QUANTILE_NOTE
    from ..data.normalization import METHOD_LABELS

    labels = [METHOD_LABELS[method] for method in methods]
    head = (f"What {labels[0]} does:" if len(methods) == 1 else
            f"How {' and '.join(labels) if len(labels) == 2 else ', '.join(labels[:-1]) + ' and ' + labels[-1]} differ:")
    parts = [head + "\n" + "\n".join(f"- {METHOD_OPTION_LINES[method]}" for method in methods)]
    if "snail" in methods:
        parts.append("SNAIL" + SMOOTH_QUANTILE_NOTE.split("with SNAIL: it", 1)[1].rstrip(".") + ".")
    parts.append("Where it fits: normalization is a preparation step, not a network workflow. It writes a normalized "
                 f"expression matrix that {_workflow_list(CHAINABLE_ACTIONS)} can then read.")
    if len(methods) > 1:
        verbs = {"sequencing_depth": "correcting ", "group_differences": "keeping "}
        needs = [verbs.get(need, "") + words for need, words in _NEED_WORDS.items()]
        parts.append(f"To pick one for your data: which does it need -- {', '.join(needs[:-1])}, or {needs[-1]}?")
    else:
        parts.append("To plan it: give the path to your expression matrix"
                     + (" and a sample-to-group file (tissue or condition)." if methods == ["snail"] else "."))
    return parts


def _sponge_part(task: str) -> list[str]:
    from ..prior_request import PRIOR_CONSUMERS, SPONGE_DEFAULTS, sponge_cost_note

    parts = [
        "What SPONGE does: it builds the two prior files a regulatory network starts from, for human genes -- a TF "
        "motif prior, by scanning JASPAR binding sites in gene promoters (by default "
        f"{SPONGE_DEFAULTS['genome_assembly']}, {SPONGE_DEFAULTS['promoter_upstream']} bp upstream to "
        f"{SPONGE_DEFAULTS['promoter_downstream']} bp downstream), and a TF PPI prior, from the STRING interactions "
        "between the selected TFs.",
        "Where it fits: SPONGE is a preparation step, not a network workflow. Its motif and PPI priors are inputs "
        f"that {_workflow_list(PRIOR_CONSUMERS)} read.",
        sponge_cost_note(None),
    ]
    if re.search(r"\bmotif\b|\bprior\b|\bPPI\b", task.replace("SPONGE", ""), re.I):
        parts.append("Using a motif prior you already have instead: those workflows read any motif prior and PPI "
                     "file you give, so SPONGE is only needed when you have none for your genes.")
    parts.append("To plan it: do you already have a motif prior and a PPI network, or should SPONGE build them?")
    return parts


def prep_concept_reply(task: str) -> str | None:
    """The whole reply to a question about a preparation step; None when the words ask no such question.

    A command to run the step ("Normalize /data/counts.tsv with SNAIL", "Build the priors with SPONGE") is no
    question here: those are planned before the interpreter and never reach this reply.
    """
    from ..normalization_request import _asks_named_method, named_methods
    from ..prior_request import _NEGATED as _NOT_SPONGE, _SPONGE

    task = (task or "").rsplit("User follow-up:", 1)[-1].strip()
    if not task or not _ABOUT.search(task) or _NOT_ABOUT.search(task) or _STUDY.search(task):
        return None
    if _asks_named_method(task):  # "How do I run qsmooth on my counts?" -- answered with the method's plan
        return None
    methods = named_methods(task)
    sponge = bool(_SPONGE.search(task)) and not _NOT_SPONGE.search(task)
    if not methods and not sponge:
        return None
    parts: list[str] = []
    if methods:
        parts.extend(_normalization_part(methods))
    if sponge:
        parts.extend(_sponge_part(task))
    return "\n\n".join([*parts, _CLOSING])


def prep_concept_result(task: str, reply) -> dict | None:
    """The whole reply when the turn is a question about a preparation step, else None."""
    if (content := prep_concept_reply(task)) is None:
        return None
    return reply(content, PREP_CONCEPT_KIND)
