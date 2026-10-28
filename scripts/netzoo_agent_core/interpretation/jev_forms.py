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

from types import SimpleNamespace

__all__ = ["ANSWER_VALUES", "BIND", "FORM_DIMENSIONS", "NEUTRAL", "QUESTIONS", "THRESHOLD", "answer_question",
           "answer_state", "answer_value", "bind_form_answers", "condition_doubts", "doubted", "forms_doubts",
           "limiting_forms", "state_text"]

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


def forms_doubts(task, result, attrs, read, credited, applicable, doubted_forms, reader, overlap_reader, fitting):
    """ROUND.md: the waits and unsaid form reasons Jev's reads add to one result row, as (applicable, doubted_forms).

    A credited row refused by its typed attributes: each limiting one Jev doubts (with group_membership when the overlap
    read doubts it too) is fitted at its neutral value; when the credits then fit, each doubted one becomes a wait.
    Round 2: when something else still blocks them (another typed attribute, the method checks), a doubted form is only
    not said as the reason. A row credited to nothing: a doubted time_model or spatial is only not said. Nothing else
    changes. `read`: the credits left after the method checks; `fitting`: the check's `_fitting`."""
    from ..capability_sheet import sheet_entries

    if not credited:
        found = [attr for attr, options in limiting_forms(attrs, []) if reader(task, result, attr, options)]
        return applicable, [*doubted_forms, *found]
    if read and fitting(read, SimpleNamespace(**attrs)):
        return applicable, doubted_forms  # not refused by its forms
    known = sheet_entries()
    found = [attr for attr, options in limiting_forms(attrs, [known[k] for k in read] if read else credited)
             if reader(task, result, attr, options)]
    waits = [about for about, quote, _domain in applicable if quote == result]
    if (attrs.get("group_membership") == "several_groups" and "group_membership" not in waits
            and overlap_reader is not None and overlap_reader(task, result)):
        found.append("group_membership")
    if not found:
        return applicable, doubted_forms
    neutral = {**attrs, **{attr: NEUTRAL.get(attr, "not_stated") for attr in [*found, *waits]}}
    if read and fitting(read, SimpleNamespace(**neutral)):
        added = [(attr, result, None) for attr in found if attr not in waits]
        return [*applicable, *added], [*doubted_forms, *(attr for attr in found if attr != "group_membership")]
    return applicable, [*doubted_forms, *(attr for attr in found if attr in _FORM_REASON_ATTRS)]


def condition_doubts(task, rows, reader, overlap_reader):
    """jev-conditions-2026-10-28 (J01): a form condition stated apart from every ask has a row of its own, credited to
    nothing (`requirement_split.condition_requirements`). A form Jev doubts there is only not said, as on an ask's row
    credited to nothing; status, credits and waits do not change."""
    out = []
    for row in rows:
        found = [attr for attr, options in limiting_forms(row.attrs, [])
                 if reader is not None and reader(task, row.quote, attr, options)]
        if (row.attrs.get("group_membership") == "several_groups" and overlap_reader is not None
                and overlap_reader(task, row.quote)):
            found.append("group_membership")
        out.append(row.model_copy(update={"doubted_forms": [*row.doubted_forms, *found]}) if found else row)
    return out


_FORM_REASON_ATTRS = ("time_model", "spatial", "group_membership")
"""The forms whose reason `stated_reasons._form_reasons` says; input_network has none."""


# jev-answers-2026-10-27 (ROUND.md): a natural answer to a form question, read on the same closed menu, bound in code.
FORM_DIMENSIONS = ("group_membership", "time_model", "spatial", "input_network")
BIND = 0.7
"""Bound when Jev's probability on the options meaning one value is at least this (offline: 8/8 right, 0 wrong)."""
ANSWER_VALUES = {
    "group_membership": {"overlapping": "several_groups", "one_each": "one_group"},
    "time_model": {"dynamic": "dynamic", "separate": "not_dynamic"},
    "spatial": {"uses_neighbors": "uses_neighbors", "independent": "not_spatial"},
    "input_network": {"regulator_gene": "regulator_gene", "gene_gene": "gene_gene"},
}
"""Jev option -> the dimension value it means; the other options (not_stated, other, none) bind nothing."""


def answer_question(dim: str) -> tuple[str, dict[str, str]]:
    """The frozen instructions and criteria of a dimension's question (group_membership: the overlap read's)."""
    if dim == "group_membership":
        from .jev_overlap import CRITERIA, INSTRUCTIONS

        return INSTRUCTIONS, CRITERIA
    return QUESTIONS[dim]["instructions"], QUESTIONS[dim]["criteria"]


def answer_state(question: str, answer: str) -> str:
    return f"The assistant asked the user:\n{question}\n\nThe user's answer:\n{answer}"


def answer_value(dim: str, read: dict) -> str | None:
    """The value a read binds, or None (an error, nothing at BIND, or only options that bind nothing)."""
    if "error" in read or not read.get("probabilities"):
        return None
    totals: dict[str, float] = {}
    for option, value in ANSWER_VALUES[dim].items():
        totals[value] = totals.get(value, 0) + read["probabilities"].get(option, 0)
    return next((value for value, total in totals.items() if total >= BIND), None)


def bind_form_answers(state, reply: str, reader):
    """The task with the asked form questions a natural reply answers bound, and the facts bound (ROUND.md).

    Only questions still open after the code binding are read; `reader(dim, question, reply)` gives the value or None.
    A value binds only when it is one of the question's own options."""
    from ..contracts.task_state import TaskFact

    if state is None or state.status == "closed":
        return state, []
    asked = [q for q in state.pending if q.status == "asked" and q.source == "dimension" and q.what in FORM_DIMENSIONS]
    bound = []
    for question in asked:
        value = reader(question.what, question.question, reply)
        if value is not None and value in question.options:
            bound.append(TaskFact(question_id=question.question_id, source=question.source, what=question.what,
                                  question=question.question, user_quote=question.user_quote,
                                  options=question.options, labels=question.labels, value=value,
                                  answer_quote=reply.strip(), turn=state.turns))
    if not bound:
        return state, []
    done = {fact.question_id for fact in bound}
    return state.model_copy(update={"pending": [q for q in state.pending if q.question_id not in done],
                                    "facts": [*state.facts, *bound], "revision": state.revision + 1}), bound
