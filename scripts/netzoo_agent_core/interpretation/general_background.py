"""General background beside a refusal that has no verified reason (couldn't-match-2026-11-18).

A DECLINE whose every part is layer 2 ("I couldn't match this to anything a registered NetZoo workflow produces")
said only what was checked and stopped there. The user (2026-11-18): that is too absolute and not general -- a
question outside NetZoo's workflows can often still be answered from general knowledge.

Two layers, kept apart:
1. Whether NetZoo can run it: the code's call, unchanged. Nothing here changes a call or adds a workflow.
2. General background: a model's short answer from general knowledge, under a label that says so. Code keeps only
   the sentences that name no NetZoo workflow and make no claim about NetZoo (claims about NetZoo's workflows come
   from their contracts only), and drops the paragraph when nothing reliable is left.
"""

from __future__ import annotations

import os
import re

from pydantic import BaseModel, Field

__all__ = ["GeneralBackground", "LABEL", "background_mode", "kept_sentences", "unmatched_quotes", "wanted",
           "with_background"]

LABEL = ("General background (from general knowledge, not checked against NetZoo's workflow contracts; it does not "
         "change the answer above):")
MAX_SENTENCES = 4
_EXTRA_NAMES = ("NetZoo", "netZooPy", "netZooR", "netZooM", "SPONGE", "SNAIL", "LIONESS")


class GeneralBackground(BaseModel):
    """The model's output: general knowledge about the request, never about NetZoo."""

    answerable: bool = Field(description=(
        "true when general scientific knowledge gives a reliable short answer to what the user asked; false when "
        "it does not, or the request is too unclear to answer."))
    background: str = Field(description=(
        "2-4 plain sentences of general background on the user's question: how this kind of analysis is usually "
        "approached and what kind of method or data it typically needs. Say nothing about what NetZoo or its "
        "workflows can or cannot do, and name no NetZoo workflow. Empty when answerable is false."))


def background_mode() -> str:
    """NETZOO_GENERAL_BACKGROUND: off (default) or on."""
    return "on" if os.environ.get("NETZOO_GENERAL_BACKGROUND", "off").strip().lower() == "on" else "off"


def wanted(core) -> bool:
    """A DECLINE with no verified reason: a full gap, or every declined part a layer-2 line."""
    from .reason_layers import is_unmatched

    if core is None or core.kind != "DECLINE":
        return False
    if core.basis == "full_gap":
        return True
    return bool(core.declined) and all(is_unmatched(part.line or "") for part in core.declined)


def unmatched_quotes(core, check=None) -> list[str]:
    """The user's words the refusal is about: the declined parts' quotes, else the check's unavailable results."""
    quotes = [part.quote for part in core.declined or [] if part.quote]
    if not quotes and check is not None:
        quotes = [item.quote for item in check.results() if item.status == "not_available" and item.quote]
    return list(dict.fromkeys(quotes))


def _names() -> tuple[str, ...]:
    from ..method_names import method_names

    return tuple(dict.fromkeys([*method_names(), *_EXTRA_NAMES]))


def kept_sentences(text: str) -> tuple[str, list[str]]:
    """(the sentences kept, the sentences dropped): a sentence naming NetZoo or any of its workflows is dropped."""
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", (text or "").strip()) if part.strip()]
    pattern = re.compile(r"\b(?:" + "|".join(re.escape(name) for name in _names()) + r")\b", re.IGNORECASE)
    kept = [sentence for sentence in sentences if not pattern.search(sentence)]
    dropped = [sentence for sentence in sentences if pattern.search(sentence)]
    return " ".join(kept[:MAX_SENTENCES]), dropped + kept[MAX_SENTENCES:]


def with_background(text: str, background: str, closing: str = "No files were inspected and no analysis ran.") -> str:
    """The reply with the labelled paragraph before its closing line (or at the end when it has none)."""
    if not background:
        return text
    paragraph = f"{LABEL}\n{background}"
    if text.rstrip().endswith(closing):
        head = text.rstrip()[: -len(closing)].rstrip()
        return f"{head}\n\n{paragraph}\n\n{closing}"
    return f"{text.rstrip()}\n\n{paragraph}"
