import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core.trace_redaction import (  # noqa: E402
    sanitize_payload,
    sanitize_text,
)


def test_sanitize_payload_removes_named_secrets_but_preserves_token_metrics():
    value = {
        "headers": {"Authorization": "Bearer sk-or-v1-secret-value"},
        "OPENROUTER_API_KEY": "sk-or-v1-second-secret",
        "token_usage": {"input_tokens": 120, "output_tokens": 30},
        "arguments": {"expression_file": Path("data/expression.tsv")},
    }

    sanitized, redactions = sanitize_payload(value)

    assert sanitized["headers"]["Authorization"] == "[REDACTED]"
    assert sanitized["OPENROUTER_API_KEY"] == "[REDACTED]"
    assert sanitized["token_usage"] == {"input_tokens": 120, "output_tokens": 30}
    assert sanitized["arguments"]["expression_file"] == "data/expression.tsv"
    assert {item.reason for item in redactions} == {"sensitive_key"}
    assert all("secret-value" not in item.model_dump_json() for item in redactions)


def test_sanitize_text_masks_private_key_cookie_bearer_and_openrouter_key():
    raw = (
        "Cookie: session=abc123\n"
        "Authorization: Bearer bearer-secret\n"
        "OPENROUTER_API_KEY=sk-or-v1-abcdefghijklmnop\n"
        "-----BEGIN PRIVATE KEY-----\nprivate-material\n-----END PRIVATE KEY-----"
    )

    sanitized, redactions = sanitize_text(raw)

    for secret in ("abc123", "bearer-secret", "abcdefghijklmnop", "private-material"):
        assert secret not in sanitized
    assert sanitized.count("[REDACTED]") == 4
    assert len(redactions) == 4


def test_sanitize_payload_bounds_large_lists_without_visiting_the_suffix():
    sanitized, redactions = sanitize_payload(list(range(1_005)))

    assert len(sanitized) == 1_001
    assert sanitized[-1] == {"truncated_items": 5}
    assert redactions == []


def test_sanitize_payload_never_calls_arbitrary_repr():
    class Dangerous:
        def __repr__(self):
            raise AssertionError("repr must not run on untrusted values")

    sanitized, redactions = sanitize_payload({"value": Dangerous()})

    assert sanitized == {"value": "[UNSUPPORTED:Dangerous]"}
    assert redactions[0].reason == "unsupported_type"
