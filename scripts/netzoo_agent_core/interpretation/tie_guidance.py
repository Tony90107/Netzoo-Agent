"""Explain a multi-candidate tie by what separates the candidates (Log 261).

The spec sheet listed every registered field of every candidate, with the
same mathematical note repeated for each method that shares a tag. A reader
needs three things instead: which kinds of result are on the table, what
makes each method different, and what it needs. Everything here comes from
the registry; nothing is keyed to a request's wording.
"""

from __future__ import annotations

from collections import Counter

from workflow_registry import OUTPUT_CAPABILITIES, SELECTION_TAG_GLOSSARY

from ..settings import INPUT_ROLE_FIELDS
from .extraction import INPUT_LABELS
from .method_philosophy import method_philosophies_for

_REGISTRY_TAGS = Counter(tag for cap in OUTPUT_CAPABILITIES.values() for tag in cap.selection_tags)


def _inputs(spec) -> str:
    labels = [INPUT_LABELS.get(f, f.replace("_", " ")) for f in spec.required_inputs if f in INPUT_ROLE_FIELDS]
    for group in spec.required_input_groups:
        options = [INPUT_LABELS.get(f, f.replace("_", " ")) for f in group if f in INPUT_ROLE_FIELDS]
        if options:
            labels.append("either " + " or ".join(options))
    if not labels:
        return ""
    return "Needs " + (", ".join(labels[:-1]) + " and " + labels[-1] if len(labels) > 1 else labels[0]) + "."


def _distinguishing_note(capability, shared: Counter, *, full: bool, said=frozenset()) -> str:
    """The note for the method's least-shared tag here, then registry-wide."""
    tags = [tag for tag in capability.selection_tags if method_philosophies_for([tag]) and tag not in said]
    if not tags:
        return ""
    tag = min(tags, key=lambda item: (shared[item], _REGISTRY_TAGS[item], item))
    note = method_philosophies_for([tag])[0]
    return note if full else note.split(". ", 1)[0].rstrip(".") + "."


def render_tie_guidance(decision, policy, *, family_label, assumptions: str = "") -> str | None:
    actions = [a for a in dict.fromkeys(decision.hypothesis_actions) if a in policy.workflows]
    if len(actions) < 2:
        return None
    caps = {a: policy.workflows[a].output_capability for a in actions}
    extensions: dict[str, list[str]] = {a: [] for a in actions}
    bases = []
    for action in actions:
        base = next((p for p in caps[action].guidance_predecessors if p in caps), None)
        if base is None:
            bases.append(action)
        else:
            extensions[base].append(action)
    shared = Counter(tag for cap in caps.values() for tag in cap.selection_tags)
    families: dict[str, list[str]] = {}
    for action in bases:
        families.setdefault(family_label(policy.workflows[action]), []).append(action)
    several_families = len(families) > 1
    method_tie = not several_families and len(bases) > 1 and not any(extensions.values())
    sections = [
        "Several registered methods fit this result; they differ in their modeling assumptions:"
        if method_tie else "I can map this to more than one compatible network result:"
    ]
    common = sorted(tag for tag, count in shared.items()
                    if count == len(actions) and method_philosophies_for([tag]) and tag in SELECTION_TAG_GLOSSARY)
    said = frozenset(common) if common and len(bases) > 1 else frozenset()
    if said:
        sections.append("All of them " + "; ".join(SELECTION_TAG_GLOSSARY[tag] for tag in common) + ".")
    for label, members in sorted(families.items()):
        lines = [f"**{label}**"] if several_families else []
        for action in members:
            spec = policy.workflows[action]
            # A family with one method: that method is the precise answer for
            # that reading, so its distinguishing mechanism is given in full.
            note = _distinguishing_note(caps[action], shared, full=several_families and len(members) == 1, said=said)
            extra = " ".join(f"Per-sample version: **{policy.workflows[e].workflow}**." for e in extensions[action])
            lines.append(f"- **{spec.workflow}** — " + " ".join(p for p in (note, extra, _inputs(spec)) if p))
        sections.append("\n".join(lines))
    if assumptions:
        sections.append(assumptions)
    if decision.clarification_question:
        sections.append(decision.clarification_question)
    sections.append("No files were inspected and no analysis ran.")
    return "\n\n".join(sections)
