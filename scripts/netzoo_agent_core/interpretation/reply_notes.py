"""Facts a tie's reply owes the user beyond the candidate list (Log 188).

Case 10 ("All I have is this expression matrix. Build me a network") was read
as a TF-to-gene network without any quote saying so, and the reply listed three
prior-needing tools as if they "all fit". Two registry- and content-derived
facts were missing, and they are added here without changing any candidate:

- when no reading quoted its artifact type, that the kind of result was
  assumed, which inputs every option additionally needs, and which registered
  workflows infer a different result from the stated inputs alone;
- which files in a folder routing read validated by content for an input role,
  and that they were not used.
"""

from __future__ import annotations

from workflow_registry import ACTION_DEFINITIONS, OUTPUT_CAPABILITIES, REQUIRED_INPUTS

from ..contracts.artifact_semantics import ARTIFACT_SEMANTICS
from ..presentation import _ui_text_with_user_data, user_data_token
from ..settings import INPUT_ROLE_FIELDS
from .inspected_answers import _NOT_INSPECTED, _ROLE_LABELS

__all__ = ["with_reply_notes"]

#: The input role a stated current input artifact supplies.
_ROLE_OF_ARTIFACT = {
    "expression_matrix": "expression_file",
    "coexpression_network": "coexpression_file",
    "mutation_matrix": "mutation_file",
    "regulatory_network": "network_file",
}


def _roles(action: str) -> set[str]:
    return {field for field in REQUIRED_INPUTS[action] if field in INPUT_ROLE_FIELDS}


def _result(artifact: str) -> str:
    rule = ARTIFACT_SEMANTICS.get(artifact)
    text = rule.description if rule is not None else artifact.replace("_", " ")
    return text.removeprefix("Inferred ")


def _assumption_note(decision) -> str | None:
    hypotheses = decision.outcome_hypotheses
    if not hypotheses or any(
        item.dimension == "artifact_type" and item.source == "explicit"
        for hypothesis in hypotheses for item in hypothesis.evidence
    ):
        return None
    artifacts = {h.outcome.artifact_type for h in hypotheses} - {"unknown"}
    stated = {
        _ROLE_OF_ARTIFACT[value] for h in hypotheses for value in h.outcome.input_artifacts
        if value in _ROLE_OF_ARTIFACT
    }
    if not artifacts or not stated:
        return None
    candidates = list(decision.hypothesis_actions)
    extra = set.intersection(*(_roles(action) - stated for action in candidates))
    alternatives = sorted((
        action for action, capability in OUTPUT_CAPABILITIES.items()
        if action not in candidates and action in REQUIRED_INPUTS
        and capability.operation == "infer" and _roles(action) and _roles(action) <= stated
        and capability.artifact_type not in artifacts
    ), key=lambda action: ACTION_DEFINITIONS[action].workflow)
    if not extra and not alternatives:
        return None
    lines = [
        "Your request does not say what the network should connect; the options above assume "
        + " or ".join(sorted(_result(artifact) for artifact in artifacts)) + "."
    ]
    if extra:
        labels = " and ".join(
            "a " + _ROLE_LABELS.get(field, field.replace("_", " ")) for field in sorted(extra)
        )
        lines.append(f"Every option above also needs {labels}.")
    if alternatives:
        results = sorted({_result(OUTPUT_CAPABILITIES[action].artifact_type) for action in alternatives})
        names = " and ".join(f"**{ACTION_DEFINITIONS[action].workflow}**" for action in alternatives)
        lines.append(f"If you meant {' or '.join(results)}, {names} need only the input you named.")
    return " ".join(lines)


def _discovery_note(decision, user_data: list[str]) -> str | None:
    entries = [item.split("=", 1) for item in decision.discovered_inputs if "=" in item]
    if not entries:
        return None

    def quoted(value: str) -> str:
        user_data.append(value)
        return user_data_token(len(user_data) - 1)

    by_folder: dict[str, list[str]] = {}
    for field, path in entries:
        folder, _, name = path.rpartition("/")
        by_folder.setdefault(folder + "/", []).append(
            f"`{quoted(name)}` as the {_ROLE_LABELS.get(field, field.replace('_', ' '))}"
        )
    found = "; ".join(
        f"in `{quoted(folder)}`, " + ", ".join(items) for folder, items in by_folder.items()
    )
    return (
        f"By content, these files validate for an input role: {found}. "
        "I have not used them; tell me whether they belong to this analysis."
    )


def with_reply_notes(text: str | None, decision) -> str | None:
    """Insert the notes above the reply's closing line, for an unrecommended tie."""
    if (
        text is None
        or decision.capability_match_status != "ambiguous"
        or len(decision.hypothesis_actions) < 2
        or decision.advisory_recommendation is not None
    ):
        return text
    user_data: list[str] = []
    notes = [note for note in (_assumption_note(decision), _discovery_note(decision, user_data)) if note]
    if not notes:
        return text
    block = _ui_text_with_user_data("\n\n".join(notes), user_data)
    if _NOT_INSPECTED in text:
        return text.replace(_NOT_INSPECTED, block + "\n\n" + _NOT_INSPECTED)
    return text + "\n\n" + block
