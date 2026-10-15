"""A workflow's contract as one text: what the fact agent reads and what its contract quotes must come from.

Core decision spec, phase 2 (section 6, R2 and R5). Built from the validated YAML policy spec only, so the agent sees
exactly the words a quote is checked against; `input_checks` entries must appear in this text (the policy loader
refuses a file where one does not).
"""

from __future__ import annotations

import re

__all__ = ["contract_text", "normalized"]


def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().casefold()


def contract_text(spec) -> str:
    capability = spec.output_capability
    lines = [f"{spec.workflow}: {spec.description}"]
    lines += [f"- {item}" for item in spec.conventions]
    for control in spec.controls:
        bounds = [f"allowed: {', '.join(map(str, control.allowed_values))}" if control.allowed_values else "",
                  f"minimum {control.minimum:g}" if control.minimum is not None else "",
                  f"maximum {control.maximum:g}" if control.maximum is not None else ""]
        detail = "; ".join(item for item in bounds if item)
        lines.append(f"- setting {control.name} ({control.control_type}{'; ' + detail if detail else ''}): "
                     f"{control.description}")
    lines += [f"- {note}" for note in getattr(capability, "guidance_notes", ()) or ()]
    if capability.handoff_contract:
        lines.append(f"- {capability.handoff_contract}")
    return "\n".join(lines)
