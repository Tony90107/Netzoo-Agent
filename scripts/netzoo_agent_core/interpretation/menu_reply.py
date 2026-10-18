"""The options card as an English reply (options-first decision, 2026-10-18; AGENTS.md: user-facing output is English).

Every sentence is built from the decision (`MenuDecision`), the defaults table's labels and the contracts' own words;
no model writes any of it at reply time. A refusal says plainly "NetZoo cannot ..." with the contract's words and the
nearest options that can be done; a question lists the options that fit so far, what each gives and what is still
open, then the questions, each with "not sure" and "none of these"; a free-text row lets the user name the method or
package they want.

Offline only: nothing in the live path calls it.
"""

from __future__ import annotations

import re

from ..capability_sheet import sheet_entries
from ..contracts.menu_reading import MenuDecision, Option, Question
from ..judgment_defaults import judgment_defaults

__all__ = ["FREE_TEXT", "render_menu_reply"]

FREE_TEXT = "Or type the method or package you want, in your own words."
_NOT_SURE = "Not sure -- suggest one"
_NONE = "None of these (please describe)"
_ASKED = {
    "artifact": "Which result do you want?",
    "artifact_group": "What kind of result do you want?",
    "granularity": "Do you want one result for all samples, one per group, or one per sample?",
    "integration": "One network joining the layers, or a separate one per layer?",
    "regulators": "Which regulators should the network have?",
    "layers": "Which two layers should be modeled together?",
    "sample_count": "How many samples are there?",
    "feature_count": "How many features will be modeled together?",
    "file": "What does the named file hold?",
}


def _question_text(question: Question) -> str:
    dimension = question.dimension
    if dimension.startswith("setting:"):
        workflow, control = dimension.split(":", 1)[1].split(".", 1)
        asked = f"Which value of {workflow}'s {control} applies?"
    elif dimension.startswith("requirement:"):
        asked = f'Is this a must: "{question.quote}"?'
    else:
        asked = _ASKED.get(dimension, f"Which is right about the {dimension.replace('_', ' ')}?")
    lines = [asked]
    if question.quote and not dimension.startswith("requirement:"):
        lines.append(f'  (You wrote: "{question.quote}")')
    lines += [f"  - {label}" for _value, label in question.options]
    lines += [f"  - {_NOT_SURE}", f"  - {_NONE}"]
    return "\n".join(lines)


def _means(artifact: str) -> str:
    table = judgment_defaults()
    names = [name.strip() for name in artifact.split(",")]
    return "; ".join(table.artifacts[name].means for name in names if name in table.artifacts)


def _option_text(n: int, option: Option) -> str:
    lines = [f"{n}. {option.workflow} -- {_means(option.artifact) or option.artifact}"]
    if option.difference:
        lines.append(f"   How it differs: {option.difference}")
    if option.good_for:
        lines.append(f"   Good for: {option.good_for}")
    if option.relevant:
        lines.append(f"   Matches {option.matched} of the {option.relevant} points you gave"
                     + (": " + "; ".join(f'"{quote}"' for quote in option.fits) if option.fits else "."))
    if option.to_confirm:
        lines.append("   Still to confirm: " + "; ".join(item.replace("_", " ") for item in option.to_confirm))
    return "\n".join(lines)


_FIELD = re.compile(r"^([a-z_]+)=([a-z_]+)$")


def _reason(reason: str) -> str:
    """A decision reason in the user's terms: a stated field by its label, a near miss by the sheet's words."""
    table = judgment_defaults()
    if reason.startswith("near_miss:"):
        entry = sheet_entries().get(reason.split(":", 1)[1])
        return f"it does not give {entry.text[0].lower()}{entry.text[1:].rstrip('.')}" if entry else reason
    match = _FIELD.match(reason)
    if match and match.group(1) in table.dimensions:
        name, value = match.groups()
        label = table.dimensions[name].options.get(value) or value.replace("_", " ")
        return f"the request says {name.replace('_', ' ')}: {label[0].lower()}{label[1:]}"
    return reason


def _cannot(decision: MenuDecision) -> list[str]:
    lines = []
    for part in decision.declined:
        what = f' "{part.quote}"' if part.quote else ""
        reasons = "; ".join(_reason(r) for r in part.reasons)
        lines.append(f"NetZoo cannot do{what}: {reasons}." if reasons else f"NetZoo cannot do{what}.")
    for item in decision.infeasible:
        lines.append(f"NetZoo cannot run {item.workflow} for this because {'; '.join(_reason(r) for r in item.reasons)}.")
        lines += [f'  The contract says: "{words}"' for words in item.contract]
    return lines


def render_menu_reply(decision: MenuDecision) -> str:
    """The reply for one decision, in English, from the decision alone."""
    out: list[str] = []
    if decision.kind == "UNCHECKED":
        return ("I could not check this request against the registered workflows, so I am not saying whether it "
                "can be done. Please send it again.")
    if decision.kind == "DECLINE":
        out += _cannot(decision)
        if decision.nearest:
            out += ["", "The nearest options NetZoo can run:"]
            out += [_option_text(n, option) for n, option in enumerate(decision.nearest, 1)]
        else:
            out += ["", "No registered workflow gives this."]
        out += ["", FREE_TEXT]
        return "\n".join(out)
    if decision.kind == "CLARIFY" and decision.evidence:
        out.append(f'You wrote "{decision.evidence[0]}", which does not yet say what result you want.')
    if decision.kind == "DO":
        if len(decision.options) == 1:
            out.append(f"This fits {decision.options[0].workflow}.")
        elif decision.options:
            out.append("These registered workflows give what you asked for; please choose one:")
    elif decision.options:
        out.append("The options that fit what you said so far:")
    out += [_option_text(n, option) for n, option in enumerate(decision.options, 1)]
    if decision.partial or (decision.kind != "DO" and (decision.declined or decision.infeasible)):
        out += ["", *(_cannot(decision))]
    if decision.questions:
        out += ["", "Before I go on:" if decision.kind == "ASK" else "To find the right result:"]
        out += [_question_text(question) for question in decision.questions]
    if decision.kind == "DO":
        if decision.assumptions:
            out += ["", "I am assuming: " + "; ".join(a.replace("_", " ").replace("=", " = ") for a in decision.assumptions)
                    + "."]
        if decision.steps:
            out += ["Outside NetZoo first: " + "; ".join(decision.steps) + "."]
        if decision.needs:
            out += ["The run will need: " + "; ".join(n.replace("|", " or ").replace("_", " ") for n in decision.needs)
                    + "."]
        if decision.unconfirmed:
            out += ["Not covered by the contract, please confirm: " + "; ".join(f'"{u}"' for u in decision.unconfirmed)]
        out += ["", "Nothing runs until you approve it."]
    out += ["", FREE_TEXT]
    return "\n".join(line for line in out).strip()
