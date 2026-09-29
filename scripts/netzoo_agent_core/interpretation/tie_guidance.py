"""Explain a multi-candidate tie by what separates the candidates (Log 261).

The spec sheet listed every registered field of every candidate, with the
same mathematical note repeated for each method that shares a tag. A reader
needs three things instead: which kinds of result are on the table, what
makes each method different, and what it needs. Everything here comes from
the registry; nothing is keyed to a request's wording.
"""

from __future__ import annotations

from collections import Counter

from workflow_registry import OUTPUT_CAPABILITIES, REQUEST_CONCERNS, SELECTION_TAG_GLOSSARY

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


def concern_section(decision, policy, actions) -> str:
    """The registry's answer to each concern the request stated, per listed method (Log 263)."""
    by_concern: dict[str, list[str]] = {}
    labels: dict[str, str] = {}
    for item in decision.addressed_concerns:
        if item.action not in actions or item.action not in policy.workflows:
            continue
        declared = next((c for c in REQUEST_CONCERNS.get(item.action, ()) if c.concern == item.concern), None)
        if declared is None:
            continue
        labels[item.concern] = declared.label
        line = f"- **{policy.workflows[item.action].workflow}** — {declared.note}"
        if line not in by_concern.setdefault(item.concern, []):
            by_concern[item.concern].append(line)
    return "\n\n".join(f"About your concern that {labels[c]}:\n" + "\n".join(lines)
                        for c, lines in by_concern.items())


def concern_section_for_workflow(decision, policy, action) -> str:
    """Stated concerns one named workflow answers, matched by concern id (Log 275).

    Concerns are recorded for the tie's candidates; a card for the workflow the
    user named answers the same concern ids from that workflow's own notes.
    """
    declared = {c.concern: c for c in REQUEST_CONCERNS.get(action, ())}
    workflow = policy.workflows[action].workflow
    return "\n\n".join(
        f"About your concern that {declared[concern].label}:\n- **{workflow}** — {declared[concern].note}"
        for concern in dict.fromkeys(item.concern for item in decision.addressed_concerns)
        if concern in declared
    )


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
    if concerns := concern_section(decision, policy, actions):
        sections.append(concerns)
    if assumptions:
        sections.append(assumptions)
    if decision.clarification_question:
        sections.append(decision.clarification_question)
    sections.append("No files were inspected and no analysis ran.")
    return "\n\n".join(sections)
