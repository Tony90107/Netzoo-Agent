"""Registry-owned incompatibilities carried separately from recommendations."""
from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from workflow_registry import ACTION_DEFINITIONS, OUTPUT_CAPABILITIES

from ..contracts.outcomes import RejectedMethod


def rejected_methods_for(
    task: str, input_artifacts: Sequence[str], *, actions: Sequence[str] = (),
    capabilities=OUTPUT_CAPABILITIES, names: Mapping[str, str] | None = None,
) -> list[RejectedMethod]:
    """Inspect named/considered methods against known CURRENT inputs only.

    Mentions can be historical; the rejection is explicitly conditional on these
    inputs and never claims that a previous analysis used the wrong data.
    """
    current = set(input_artifacts) - {"unknown"}
    if not current:
        return []
    labels = names if names is not None else {action: spec.workflow for action, spec in ACTION_DEFINITIONS.items()}
    rejected = []
    for action, capability in capabilities.items():
        label = labels[action]
        words = re.split(r"[-_\s]+", label.casefold())
        mentioned = all(re.search(rf"(?<![a-z0-9]){re.escape(word)}(?![a-z0-9])", task.casefold()) for word in words)
        if action not in actions and not mentioned:
            continue
        incompatible = current.intersection(capability.incompatible_input_artifacts)
        unsupported = current.difference(capability.input_artifacts)
        if not incompatible and not unsupported:
            continue
        rejected.append(RejectedMethod(
            action=action, workflow=label,
            reason_code="incompatible_input" if incompatible else "unsupported_input",
            input_artifacts=sorted(incompatible or unsupported),
            accepted_input_artifacts=sorted(capability.input_artifacts),
            reason=(f"The registered {label} input contract does not accept "
                    f"{', '.join(sorted(incompatible or unsupported))} for this analysis; "
                    f"it accepts {', '.join(sorted(capability.input_artifacts))}."),
        ))
    return rejected
