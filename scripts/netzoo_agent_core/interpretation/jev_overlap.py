"""Jev's second read of overlapping group membership (docs/research-log/jev-overlap-2026-10-27/ROUND.md): the pure part.

The capability check rules a grouping result out when its reading types `group_membership=several_groups` (each item
in several groups at once; no registered workflow gives that). gpt-4o-mini types plain subtyping and community requests
that way ("2 to 5 subtypes", "groups of factors and the genes they share"), and the refusal then says no workflow
returns overlapping memberships -- a reason the user never gave. Jev reads the user's words once, on a closed menu;
when it confidently finds no overlap asked for, the result waits on a `group_membership` question with the two
options instead of being refused. Jev never makes a DO or a DECLINE, never picks a workflow and writes no reason.

This module holds the frozen question and the rule from a read to "doubted". The call itself (I/O, memo, offline
cache, flag) is `graph.jev_overlap_call`, which passes `build_capability_check` an `overlap_reader`; without one the
builder makes no read at all (merge plan 2026-10-27).
"""

from __future__ import annotations

__all__ = ["CRITERIA", "INSTRUCTIONS", "THRESHOLD", "doubted", "state_text"]

# Frozen with the stability check (jev-overlap-2026-10-27/overlap_q.py); never reworded after a run.
INSTRUCTIONS = ("The user asks for groups (communities, modules, subtypes or clusters). Does the request say that one "
                "item (a gene, regulator or sample) may belong to more than one group at the same time?")
CRITERIA = {
    "overlapping": "Yes: the request says an item may belong to several groups at once, or asks for a membership "
                   "strength or degree in each group.",
    "one_each": "No: the request says each item belongs to exactly one group.",
    "not_stated": "The request does not say whether an item can belong to more than one group.",
}
THRESHOLD = 0.3
"""Doubted when P(overlapping) is at most this (stability: controls 1.0; misreads 0 to 0.05)."""


def state_text(task: str, quote: str) -> str:
    return f"User request:\n{task}\n\nThe part that asks for groups:\n{quote}"


def doubted(read: dict) -> bool:
    """Whether a read (Jev's answer, or {"error": ...}) finds no overlap asked for, at P(overlapping) <= THRESHOLD."""
    p_overlap = (read.get("probabilities") or {}).get("overlapping")
    if p_overlap is None and "choice" in read:
        p_overlap = read["confidence"] if read["choice"] == "overlapping" else 1 - read["confidence"]
    return "error" not in read and p_overlap is not None and p_overlap <= THRESHOLD
