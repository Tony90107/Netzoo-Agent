"""Tool-owned error adaptation behind a stable typed interface."""

from __future__ import annotations

import re
from types import MappingProxyType
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from ..contracts.results import PUMA_EXPRESSION_HEADER_UNSUPPORTED

__all__ = [
    "PUMA_EXPRESSION_HEADER_UNSUPPORTED",
    "ToolErrorAdapter",
    "ToolErrorContext",
    "ToolErrorDiagnosis",
    "adapt_tool_error",
    "extract_reported_error_codes",
]


_ERROR_CODE_PATTERN = re.compile(
    r"^\s*error\s+code\s*:\s*([A-Z][A-Z0-9_]*)\s*$",
    flags=re.IGNORECASE,
)


class ToolErrorDiagnosis(BaseModel):
    """A tool adapter's bounded interpretation of one known failure."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    error_code: str
    retryable: bool = False
    recovery_action: str | None = None
    evidence: list[str] = Field(default_factory=list)


class ToolErrorContext(BaseModel):
    """Generic failure facts made available to a tool-owned adapter."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    action: str
    reported_error_codes: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    exit_code: int | None = None


class ToolErrorAdapter(Protocol):
    """Translate known tool-owned failure facts into a typed diagnosis."""

    def adapt(self, context: ToolErrorContext) -> ToolErrorDiagnosis | None: ...


class PumaToolErrorAdapter:
    """Recognize stable PUMA machine codes without depending on prose."""

    def adapt(self, context: ToolErrorContext) -> ToolErrorDiagnosis | None:
        if PUMA_EXPRESSION_HEADER_UNSUPPORTED not in context.reported_error_codes:
            return None
        return ToolErrorDiagnosis(
            error_code=PUMA_EXPRESSION_HEADER_UNSUPPORTED,
            retryable=True,
            recovery_action="format_expression_headerless",
            evidence=list(context.errors),
        )


class GiraffeToolErrorAdapter:
    """Translate GIRAFFE runtime failures into actionable categories."""

    _CODES = frozenset(
        {
            "GIRAFFE_NETZOOPY_MISSING",
            "GIRAFFE_VERSION_UNSUPPORTED",
            "GIRAFFE_API_UNAVAILABLE",
            "GIRAFFE_INPUT_FORMAT_ERROR",
            "GIRAFFE_API_ERROR",
            "GIRAFFE_OUTPUT_SHAPE_INVALID",
            "GIRAFFE_OUTPUT_ERROR",
            "GIRAFFE_OUTPUT_INVALID",
            "GIRAFFE_RUNTIME_ERROR",
            "GIRAFFE_OUTPUT_OVERWRITES_INPUT",
        }
    )

    def adapt(self, context: ToolErrorContext) -> ToolErrorDiagnosis | None:
        code = next(
            (item for item in context.reported_error_codes if item in self._CODES),
            None,
        )
        if code is None:
            return None
        retryable = code in {
            "GIRAFFE_NETZOOPY_MISSING",
            "GIRAFFE_VERSION_UNSUPPORTED",
            "GIRAFFE_API_UNAVAILABLE",
            "GIRAFFE_API_ERROR",
            "GIRAFFE_RUNTIME_ERROR",
        }
        recovery = {
            "GIRAFFE_NETZOOPY_MISSING": "run_in_pinned_docker_runtime",
            "GIRAFFE_VERSION_UNSUPPORTED": "use_pinned_netzoopy_version",
            "GIRAFFE_API_UNAVAILABLE": "reverify_netzoopy_giraffe_api",
            "GIRAFFE_API_ERROR": "inspect_giraffe_runtime_and_inputs",
            "GIRAFFE_RUNTIME_ERROR": "inspect_giraffe_execution_log",
        }.get(code)
        return ToolErrorDiagnosis(
            error_code=code,
            retryable=retryable,
            recovery_action=recovery,
            evidence=list(context.errors),
        )


class BonoboToolErrorAdapter:
    """Translate BONOBO runtime failures into stable typed categories."""

    _CODES = frozenset(
        {
            "BONOBO_INPUT_INVALID",
            "BONOBO_OUTPUT_FORMAT_UNSUPPORTED",
            "BONOBO_PRECISION_UNSUPPORTED",
            "BONOBO_PVALUES_REQUIRE_SPARSIFY",
            "BONOBO_NETZOOPY_MISSING",
            "BONOBO_VERSION_UNSUPPORTED",
            "BONOBO_API_UNAVAILABLE",
            "BONOBO_API_ERROR",
            "BONOBO_OUTPUT_OVERWRITES_INPUT",
            "BONOBO_OUTPUT_ERROR",
            "BONOBO_OUTPUT_INVALID",
            "BONOBO_RUNTIME_ERROR",
        }
    )

    def adapt(self, context: ToolErrorContext) -> ToolErrorDiagnosis | None:
        code = next(
            (item for item in context.reported_error_codes if item in self._CODES),
            None,
        )
        if code is None:
            return None
        retryable = code in {
            "BONOBO_NETZOOPY_MISSING",
            "BONOBO_VERSION_UNSUPPORTED",
            "BONOBO_API_UNAVAILABLE",
            "BONOBO_API_ERROR",
            "BONOBO_OUTPUT_ERROR",
            "BONOBO_RUNTIME_ERROR",
        }
        recovery = {
            "BONOBO_NETZOOPY_MISSING": "run_in_pinned_docker_runtime",
            "BONOBO_VERSION_UNSUPPORTED": "use_pinned_netzoopy_version",
            "BONOBO_API_UNAVAILABLE": "reverify_netzoopy_bonobo_api",
            "BONOBO_API_ERROR": "inspect_bonobo_runtime_and_inputs",
            "BONOBO_OUTPUT_ERROR": "inspect_bonobo_output_directory",
            "BONOBO_OUTPUT_INVALID": "inspect_bonobo_artifacts",
            "BONOBO_RUNTIME_ERROR": "inspect_bonobo_execution_log",
        }.get(code)
        return ToolErrorDiagnosis(
            error_code=code,
            retryable=retryable,
            recovery_action=recovery,
            evidence=list(context.errors),
        )


TOOL_ERROR_ADAPTERS = MappingProxyType(
    {
        "run_puma": (PumaToolErrorAdapter(),),
        "run_giraffe": (GiraffeToolErrorAdapter(),),
        "run_bonobo": (BonoboToolErrorAdapter(),),
    }
)


def extract_reported_error_codes(raw_output: str) -> list[str]:
    """Extract stable line-leading machine codes while preserving order."""
    codes: list[str] = []
    for line in raw_output.splitlines():
        match = _ERROR_CODE_PATTERN.match(line)
        if not match:
            continue
        code = match.group(1).upper()
        if code not in codes:
            codes.append(code)
    return codes


def adapt_tool_error(context: ToolErrorContext) -> ToolErrorDiagnosis | None:
    """Return the first diagnosis from adapters registered for this action."""
    for adapter in TOOL_ERROR_ADAPTERS.get(context.action, ()):
        diagnosis = adapter.adapt(context)
        if diagnosis is not None:
            return diagnosis
    return None
