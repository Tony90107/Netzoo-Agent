"""The ASK card's buttons (answer-buttons-2026-10-31): the core's one question as `ReplyChoices`, built from the same
pending question the binder reads (`engine.answer_buttons.buttons`), with the row for the user's own answer."""
from __future__ import annotations

from ..engine.answer_buttons import buttons, buttons_mode
from .contracts import MAX_OPTIONS, ReplyChoices, ReplyOption

__all__ = ["ask_choices", "family_choices"]


def ask_choices(core) -> ReplyChoices | None:
    """The buttons of an ASK call's single question, or None (flag off, no closed answers, or several questions)."""
    from ..engine.task_updates import _pending
    from .phrases import clip

    if buttons_mode() != "on" or core is None or core.kind != "ASK" or len(core.facts) != 1:
        return None
    asked = [question for question in _pending(core.model_dump(mode="json")) if question.status == "asked"]
    found = buttons(asked[0]) if len(asked) == 1 else []
    if not found or len(found) > MAX_OPTIONS:
        return None
    options = [ReplyOption(key=f"answer-{index}", label=clip(label, 80), answer=clip(answer, 600))
               for index, (_value, label, answer) in enumerate(found, 1)]
    return ReplyChoices(header="Answer", question=clip(asked[0].question, 400), options=options, allow_other=True,
                        ordering="In the order the question names them.")


def family_choices(core) -> ReplyChoices | None:
    """clarify-menu-2026-11-01: on a CLARIFY, every result family as a button, with the row for the user's own words;
    None when NETZOO_CLARIFY_MENU is off or the call is not a CLARIFY."""
    import os

    from ..interpretation.result_families import families
    from .phrases import clip

    if os.environ.get("NETZOO_CLARIFY_MENU", "off").strip().lower() != "on" or core is None or core.kind != "CLARIFY":
        return None
    options = [ReplyOption(key=f"family-{item['key']}", label=clip(item["text"][:1].upper() + item["text"][1:], 80),
                           description=clip(", ".join(item["workflows"]), 260),
                           answer=clip(f"I want {item['text']}.", 600))
               for item in families()[:MAX_OPTIONS]]
    return ReplyChoices(header="Result", question="Which kind of result do you want?", options=options,
                        allow_other=True, ordering="Every kind of result the registered workflows give, in a fixed "
                                                   "order; not a recommendation.")
