"""Answer buttons for a pending question (docs/research-log/answer-buttons-2026-10-31): which answers it offers.

One rule shared by the reply card (what the buttons show and send) and the binder (which option a sent button answer
names), so a click always binds the option it shows:
  - a question with options (a dimension, a count judged in code, a choice): one button per option, its own words;
  - a yes/no question (an agent question, a Jev question -- data confirm, input exists, "did you mean X's result?" --
    or a boolean setting of a workflow): Yes / No;
  - anything else: no buttons (typed answers only, as before).
Off by default: NETZOO_ANSWER_BUTTONS=on.
"""
from __future__ import annotations

import os
import re
from functools import lru_cache

__all__ = ["buttons", "buttons_mode"]

COUNTED = {"sample_count": "samples", "feature_count": "features", "omics_layers": "layers"}
NUMBER = re.compile(r"\d[\d,]*(\.\d+)?")


def buttons_mode() -> str:
    return "on" if os.environ.get("NETZOO_ANSWER_BUTTONS", "off").strip().lower() == "on" else "off"


@lru_cache(maxsize=64)
def _boolean_setting(what: str) -> bool:
    """Whether `WORKFLOW.setting` names a boolean control of that workflow's contract."""
    from pathlib import Path

    import yaml

    workflow, _, name = what.partition(".")
    if not workflow or not name:
        return False
    for path in sorted((Path(__file__).resolve().parents[3] / "workflows").glob("*.yaml")):
        spec = yaml.safe_load(path.read_text())
        if spec.get("workflow") == workflow:
            return any(c.get("name") == name and c.get("type") == "boolean" for c in spec.get("controls") or [])
    return False


def buttons(question) -> list[tuple[str, str, str]]:
    """(value bound, label shown, answer sent) for each button of a pending question, in order; [] for none."""
    options = list(getattr(question, "options", None) or ())
    labels = dict(getattr(question, "labels", None) or {})
    what = str(getattr(question, "what", "") or "")
    if options:
        found = []
        for value in options:
            words = (labels.get(value) or value).strip()
            answer = words[:1].upper() + words[1:]
            # button-labels-2026-11-01: a card numbers its buttons 1, 2, ...; a bare number as a label collided with
            # them (the user chose item 2, the button "5"). The label says what it counts; the click still sends it.
            label = f"{answer} {COUNTED.get(what, '')}".strip() if NUMBER.fullmatch(answer) and what in COUNTED \
                else (f"Value {answer}" if NUMBER.fullmatch(answer) else answer)
            found.append((value, label, answer))
        return found
    if what.startswith("jev_link:"):  # round 2 (A16): the answer names the workflow, so the next reading can use it
        name = what.split(":", 1)[1]
        return [("yes", "Yes", f"Yes, I mean {name}'s result."), ("no", "No", f"No, not {name}'s result.")]
    if getattr(question, "yes_no", False) or what.startswith("jev:") or _boolean_setting(what):
        return [("yes", "Yes", "Yes"), ("no", "No", "No")]
    return []
