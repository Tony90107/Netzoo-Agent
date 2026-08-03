"""Credential hashing primitives shared by collector authentication scopes."""

from __future__ import annotations

import hashlib
import hmac

from pydantic import SecretStr


__all__ = ["hash_credential", "verify_credential"]


def _secret_value(value: str | SecretStr) -> str:
    return value.get_secret_value() if isinstance(value, SecretStr) else value


def hash_credential(secret: str | SecretStr, pepper: str | SecretStr) -> str:
    """Return a keyed SHA-256 digest without retaining the raw credential."""
    raw_secret = _secret_value(secret)
    raw_pepper = _secret_value(pepper)
    if len(raw_pepper.encode("utf-8")) < 32:
        raise ValueError("credential pepper must contain at least 32 UTF-8 bytes")
    if not raw_secret:
        raise ValueError("credential cannot be empty")
    return hmac.new(
        raw_pepper.encode("utf-8"),
        raw_secret.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_credential(
    candidate: str | SecretStr,
    pepper: str | SecretStr,
    expected_digest: str,
) -> bool:
    """Compare a candidate through constant-time digest comparison."""
    try:
        candidate_digest = hash_credential(candidate, pepper)
    except ValueError:
        return False
    return hmac.compare_digest(candidate_digest, expected_digest)
