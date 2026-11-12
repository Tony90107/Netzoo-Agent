"""What a "which tool do I need" sentence asks for, and the results the user already confirmed.

2026-11-12 ("if i want to get sample specific mi-rna regulator network, what tools do i need?", 7 first turns):
the capability check's second opinion was shown the whole sentence. When the quote kept the tool question it answered
"part" -- no workflow produces "what tools do I need" -- and the agent asked "Did you mean LIONESS-PUMA's result?"
(3 of 7); when the quote was only the result it answered "all" and the agent recommended LIONESS-PUMA (2 of 7). The
tool question asks for a method recommendation, which is how a credited result is answered anyway, so the second
opinion is shown the result words alone. Code trims; no prompt changes.

A result the user confirmed ("Did you mean X's result?" -> Yes) is X's for the goal it was asked about: on the answer
turn a second "part" reading declined it with "couldn't match this to anything" (2 of 3 answer turns).
"""

from __future__ import annotations

import re

__all__ = ["confirmed_links", "result_words"]

_TOOL = r"(?:netzoo\s+)?(?:tools?|methods?|workflows?|approach(?:es)?|algorithms?|software|packages?|pipelines?|options?)"
_WE = r"(?:i|we)"
_GIVE = r"(?:give|gives|produce|produces|output|outputs|return|returns|build|builds|make|makes|create|creates|compute|computes|fit|fits|work|works|is\s+best|would\s+(?:fit|work|give))"
# A clause that only asks which tool to use: "what tools do I need", "which workflow is best", "what are my options".
_TOOL_QUESTION = re.compile(
    rf"^(?:so\s+|then\s+)?(?:what|which)\s+(?:{_TOOL}|one|can)\b[^,;]*$"
    rf"|^(?:what|which)\s+(?:do|should|can|could|would)\s+{_WE}\s+(?:need|use|run|do)\b[^,;]*$"
    rf"|^what\s+are\s+(?:my|our|the)\s+options\b[^,;]*$"
    rf"|^(?:do\s+you\s+have|is\s+there|are\s+there)\s+(?:an?\s+|any\s+)?{_TOOL}\b[^,;]*$",
    re.IGNORECASE)
# The same question in front of the result; each is removed and the rest kept ("... to build a network" -> "build ...").
_LEADS = tuple(re.compile(pattern, re.IGNORECASE) for pattern in (
    rf"^(?:what|which)\s+{_TOOL}\s+(?:do|should|can|could|would)\s+{_WE}\s+(?:need|use|run)\s+(?:to|for)\s+",
    rf"^(?:what|which)\s+(?:can|should|do|could)\s+{_WE}\s+(?:use|run)\s+(?:to|for)\s+",
    rf"^(?:what|which)\s+{_TOOL}\s+{_GIVE}\s+(?:me\s+|us\s+)?(?:(?:if|when)\s+{_WE}\s+(?:want|need)(?:\s+to)?\s+)?",
    rf"^(?:do\s+you\s+have|is\s+there|are\s+there)\s+(?:an?\s+|any\s+)?{_TOOL}\s+(?:for|to|that\s+\w+)\s+",
    rf"^(?:can|could)\s+(?:netzoo|you|{_WE})\s+(?=\w)",
    rf"^(?:please\s+)?recommend\s+(?:an?\s+|the\s+)?{_TOOL}\s+(?:for|to)\s+",
    rf"^(?:please\s+)?tell\s+me\s+(?:which|what)\s+{_TOOL}\s+{_GIVE}\s+(?:me\s+)?",
    r"^what(?:'s|\s+is)\s+the\s+best\s+way\s+to\s+",
    r"^is\s+it\s+possible\s+to\s+",
    rf"^(?:if\s+)?{_WE}(?:'d|\s+would)?\s+(?:want|wanted|like|need|wish)(?:\s+to)?\s+",
    rf"^how\s+(?:can|do|should|could)\s+{_WE}\s+",
    r"^to\s+(?=\w)",
))


def _lead_off(part: str) -> str:
    previous = None
    while previous != part:
        previous = part
        for lead in _LEADS:
            part = lead.sub("", part, count=1)
    return part


def result_words(quote: str) -> str:
    """*quote* without the words that only ask which tool to use; *quote* itself when nothing else is left."""
    kept = []
    for part in (piece.strip(" ?!.") for piece in re.split(r"\s*[,;]\s*", quote.strip())):
        led = _lead_off(part)
        if _TOOL_QUESTION.match(part) and (led == part or re.match(rf"^(?:{_WE}\b|$)", led, re.IGNORECASE)):
            continue  # only asks which tool: "what tools do I need", "which workflow is best"
        kept.append(led)
    text = ", ".join(item for item in kept if item).strip(" ?!.")
    return text or quote


def confirmed_links(task_state) -> dict[str, str]:
    """`{workflow: goal}` for each "Did you mean X's result?" the user answered yes in this task."""
    state = task_state or {}
    goal = str(state.get("goal") or "")
    found = {}
    for fact in state.get("facts") or []:
        what = str(fact.get("what") or "")
        if what.startswith("jev_link:") and str(fact.get("value") or "").casefold() == "yes":
            found[what.split(":", 1)[1]] = goal
    return found
