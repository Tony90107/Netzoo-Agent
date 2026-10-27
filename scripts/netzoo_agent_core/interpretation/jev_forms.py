"""Jev's second read of the other limiting result forms (docs/research-log/jev-forms-2026-10-27/ROUND.md): the pure part.

`jev_overlap` reads `group_membership`. The same misread clears right answers through three more typed attributes:
"time-course samples" typed `time_model=dynamic` (j3 R13), and a TF-to-gene edge list typed
`input_network=gene_gene`, which rules CONDOR out (j3 R39 and a recurring CONDOR family). Jev reads the user's words
once per attribute, on a closed menu. An attribute is doubted when Jev's probability on the options under which the
typed value is what the user said is at most THRESHOLD; a doubted limit becomes a question (or, on a row credited to
nothing, its form reason is not said). Jev never makes a DO or a DECLINE, never picks a workflow and writes no reason.

This module holds the frozen questions and the rules. The call (I/O, memo, offline cache, flag) is
`graph.jev_forms_call`, which passes `build_capability_check` a `forms_reader`; without one the builder reads nothing.
"""

from __future__ import annotations

__all__ = ["NEUTRAL", "QUESTIONS", "THRESHOLD", "doubted", "limiting_forms", "state_text"]

# Frozen with the stability check (jev-forms-2026-10-27/forms_q.py); never reworded after a run.
QUESTIONS = {
    "time_model": {
        "instructions": ("The user's samples may come from several time points or stages. Does the request say the "
                         "wanted result must model how the system changes from one time point to the next (time "
                         "lags, transitions, trajectories, a dynamic model)?"),
        "criteria": {
            "dynamic": "Yes: the result must model change from one time point to the next.",
            "separate": "No: the request wants results for samples or time points that are not linked into a model "
                        "of change (they may still be compared).",
            "not_stated": "The request does not say.",
        },
        "part": "The part that asks for the result",
    },
    "spatial": {
        "instructions": ("Does the request say the wanted result must use where samples sit in space, or which "
                         "samples are neighbours (spatial neighbourhoods, contiguous tissue regions)?"),
        "criteria": {
            "uses_neighbors": "Yes: the result must use positions in space or neighbouring samples.",
            "independent": "No: each sample is treated on its own.",
            "not_stated": "The request does not say.",
        },
        "part": "The part that asks for the result",
    },
    "input_network": {
        "instructions": ("The wanted result may be computed from a network the user already has. What kind of "
                         "network does the user say it is computed from?"),
        "criteria": {
            "regulator_gene": "Links from regulators such as transcription factors to target genes (for example a "
                              "PANDA or OTTER network, or a TF-to-gene edge list).",
            "gene_gene": "Links among genes or other features of one kind, such as a co-expression or "
                         "partial-correlation network (for example from DRAGON).",
            "other": "Another kind of network, such as protein-protein interactions.",
            "none": "The user has no such network, or the result is not computed from one.",
            "not_stated": "The request does not say.",
        },
        "part": "The part that asks for the result",
    },
}
THRESHOLD = 0.3
"""Doubted when the probability on the ruling-out options is at most this (stability: controls 1.0, misreads <= 0.03)."""
NEUTRAL = {"time_model": "not_dynamic", "spatial": "not_spatial", "input_network": "none"}
"""The value a doubted attribute is fitted with: one that rules no registered entry out."""
_NETWORKS = ("regulator_gene", "gene_gene", "other")


def state_text(attr: str, task: str, quote: str) -> str:
    return f"User request:\n{task}\n\n{QUESTIONS[attr]['part']}:\n{quote}"


def limiting_forms(attrs: dict, credited) -> list[tuple[str, tuple[str, ...]]]:
    """The typed attributes that rule the credited entries out, each with the options meaning the user said so.

    `credited`: the row's credited produces entries (sheet entries), or [] for a row credited to nothing (then only
    the form attributes, whose reason the reply would say)."""
    found = []
    if attrs.get("time_model") == "dynamic":
        found.append(("time_model", ("dynamic",)))
    if attrs.get("spatial") == "uses_neighbors":
        found.append(("spatial", ("uses_neighbors",)))
    typed = attrs.get("input_network")
    if credited and typed in _NETWORKS:
        excluded = [entry for entry in credited if entry.input_network is not None and entry.input_network != typed]
        if excluded:
            takes = {entry.input_network for entry in excluded}
            found.append(("input_network", tuple(kind for kind in _NETWORKS if kind not in takes)))
    return found


def doubted(read: dict, options: tuple[str, ...]) -> bool:
    """Whether a read (Jev's answer, or {"error": ...}) puts at most THRESHOLD on the ruling-out options."""
    if "error" in read or not read.get("probabilities"):
        return False
    return sum(read["probabilities"].get(option, 0) for option in options) <= THRESHOLD
