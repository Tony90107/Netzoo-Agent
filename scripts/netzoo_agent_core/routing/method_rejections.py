"""Registry-owned incompatibilities carried separately from recommendations."""
from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from workflow_registry import ACTION_DEFINITIONS, OUTPUT_CAPABILITIES

from ..contracts.outcomes import RejectedMethod


_GLASSO_MARKER = re.compile(
    r"\b(?:glasso|graphical\s+lasso|precision\s+matrix|inverse\s+covariance)\b"
    r"|逆共變異數|逆協方差|精度矩陣",
    re.IGNORECASE,
)
_BAYESIAN_OPTIMIZATION_MARKER = re.compile(
    r"\b(?:bayesian\s+optimization|bayesian\s+optimisation|hyperparameter)\b"
    r"|貝氏最佳化|貝葉斯最佳化|超參數",
    re.IGNORECASE,
)
_ACTIVE_LEARNING_GP_MARKER = re.compile(
    r"\b(?:active\s+learning|gaussian\s+process|parameter\s+bounds?|iteration\s+budget)\b"
    r"|主動學習|高斯程序|高斯過程|參數邊界|上下邊界|迭代預算",
    re.IGNORECASE,
)


def unsupported_algorithm_request(task: str) -> str | None:
    """Return a stable boundary key for known unsupported method combinations."""
    if _GLASSO_MARKER.search(task) and _BAYESIAN_OPTIMIZATION_MARKER.search(task):
        return "glasso_bayesian_optimization"
    if (
        _ACTIVE_LEARNING_GP_MARKER.search(task)
        and re.search(
            r"\b(?:motif|prior|regulatory|network)\b|先驗|調控|網路",
            task,
            re.IGNORECASE,
        )
    ):
        return "active_learning_gaussian_process"
    return None


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
