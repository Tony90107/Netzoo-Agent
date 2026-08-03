"""Secret redaction for trace payloads before their first local write."""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


__all__ = ["Redaction", "sanitize_payload", "sanitize_text"]


REDACTED = "[REDACTED]"
MAX_DEPTH = 12
MAX_LIST_ITEMS = 1_000
SAFE_TOKEN_KEYS = frozenset(
    {
        "cache_read_tokens",
        "cache_write_tokens",
        "input_tokens",
        "output_tokens",
        "reserved_output_tokens",
        "token_usage",
        "total_tokens",
    }
)
SENSITIVE_KEY_PARTS = frozenset(
    {
        "apikey",
        "authorization",
        "clientsecret",
        "cookie",
        "credential",
        "password",
        "privatekey",
        "refreshtoken",
        "secret",
    }
)


class Redaction(BaseModel):
    """Non-sensitive evidence that a value was removed."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str
    reason: Literal["sensitive_key", "secret_pattern", "unsupported_type"]


def _normalized_key(key: str) -> str:
    return "".join(character for character in key.casefold() if character.isalnum())


def _is_sensitive_key(key: str) -> bool:
    normalized = _normalized_key(key)
    if key.casefold() in SAFE_TOKEN_KEYS:
        return False
    if normalized in {"token", "accesstoken"}:
        return True
    return any(part in normalized for part in SENSITIVE_KEY_PARTS)


_TEXT_PATTERNS = (
    re.compile(
        r"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----.*?"
        r"-----END (?:[A-Z0-9 ]+ )?PRIVATE KEY-----",
        re.DOTALL,
    ),
    re.compile(r"(?im)^\s*cookie\s*:\s*[^\r\n]+"),
    re.compile(r"(?im)^\s*authorization\s*:\s*bearer\s+[^\s\r\n]+"),
    re.compile(r"(?im)^\s*[A-Z][A-Z0-9_]*(?:API_KEY|TOKEN|PASSWORD|SECRET)\s*=\s*[^\s\r\n]+"),
    re.compile(r"\bsk-or-v1-[A-Za-z0-9_-]{8,}\b"),
)


def sanitize_text(text: str, *, path: str = "$") -> tuple[str, list[Redaction]]:
    """Mask recognized credentials without retaining matched substrings."""
    sanitized = text
    redactions: list[Redaction] = []
    for pattern in _TEXT_PATTERNS:
        sanitized, count = pattern.subn(REDACTED, sanitized)
        redactions.extend(
            Redaction(path=path, reason="secret_pattern") for _index in range(count)
        )
    return sanitized, redactions


def _path(parent: str, key: str | int) -> str:
    return f"{parent}[{key}]" if isinstance(key, int) else f"{parent}.{key}"


def sanitize_payload(value: object) -> tuple[object, list[Redaction]]:
    """Convert a value to bounded JSON-safe data and remove secrets recursively."""

    def visit(item: object, path: str, depth: int) -> tuple[object, list[Redaction]]:
        if depth > MAX_DEPTH:
            return "[UNSUPPORTED:max-depth]", [
                Redaction(path=path, reason="unsupported_type")
            ]
        if item is None or isinstance(item, (bool, int, float)):
            return item, []
        if isinstance(item, str):
            return sanitize_text(item, path=path)
        if isinstance(item, (Path, UUID, date, datetime)):
            return str(item), []
        if isinstance(item, BaseModel):
            return visit(item.model_dump(mode="json"), path, depth + 1)
        if isinstance(item, dict):
            cleaned: dict[str, object] = {}
            redactions: list[Redaction] = []
            for raw_key, child in item.items():
                key = (
                    str(raw_key)
                    if isinstance(raw_key, (str, int, float, bool, UUID))
                    else f"[UNSUPPORTED_KEY:{type(raw_key).__name__}]"
                )
                child_path = _path(path, key)
                if _is_sensitive_key(key):
                    cleaned[key] = REDACTED
                    redactions.append(
                        Redaction(path=child_path, reason="sensitive_key")
                    )
                    continue
                safe_child, child_redactions = visit(child, child_path, depth + 1)
                cleaned[key] = safe_child
                redactions.extend(child_redactions)
            return cleaned, redactions
        if isinstance(item, (list, tuple)):
            cleaned_list: list[object] = []
            redactions: list[Redaction] = []
            for index, child in enumerate(item[:MAX_LIST_ITEMS]):
                safe_child, child_redactions = visit(
                    child,
                    _path(path, index),
                    depth + 1,
                )
                cleaned_list.append(safe_child)
                redactions.extend(child_redactions)
            if len(item) > MAX_LIST_ITEMS:
                cleaned_list.append({"truncated_items": len(item) - MAX_LIST_ITEMS})
            return cleaned_list, redactions
        return f"[UNSUPPORTED:{type(item).__name__}]", [
            Redaction(path=path, reason="unsupported_type")
        ]

    return visit(value, "$", 0)
