"""The window's TypeScript must be what the contracts currently say.

Two definitions of a plan agree only until someone forgets. During M3 three
view fields were mirrored by hand, and when generation replaced that the
compiler immediately found four fields of `WorkflowPlan` and four of
`NextTurnPrompt` that the hand-written copy had never had.

This fails when the committed file is stale. Regenerate with
``python scripts/generate_ui_types.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import generate_ui_types  # noqa: E402


def test_the_committed_typescript_matches_the_contracts():
    committed = generate_ui_types.OUTPUT
    assert committed.exists(), f"{committed} is missing; run generate_ui_types.py"

    assert committed.read_text(encoding="utf-8") == generate_ui_types.generate(), (
        "desktop/src/generated/contracts.ts is stale. "
        "Run `python scripts/generate_ui_types.py`."
    )


def test_generation_is_deterministic():
    """A generator whose output moved between runs could never police drift."""
    assert generate_ui_types.generate() == generate_ui_types.generate()


def test_every_root_reaches_the_output():
    text = generate_ui_types.generate()
    for model in generate_ui_types.ROOTS:
        assert f"export type {model.__name__} = {{" in text


def test_an_inexpressible_annotation_is_refused_rather_than_guessed():
    """Silence here would ship a type that lies about the wire."""
    with pytest.raises(generate_ui_types.Unsupported):
        generate_ui_types._render(complex, [])


def test_a_free_form_payload_is_unknown_not_any_shape():
    """`decision`, `arguments` and a trace event's `payload` vary by node."""
    assert generate_ui_types._render(dict, []) == "Record<string, unknown>"


def test_generated_file_is_marked_as_generated():
    assert "Do not edit" in generate_ui_types.OUTPUT.read_text(encoding="utf-8")
