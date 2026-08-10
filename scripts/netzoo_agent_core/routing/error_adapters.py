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


TOOL_ERROR_ADAPTERS = MappingProxyType(
    {
        "run_puma": (PumaToolErrorAdapter(),),
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
