"""`explicit` asserts the request said it, so the request has to be quoted.

The rule was written in prompt prose (`llm.py`) and in no contract, while the
schema the provider actually receives said `text_span` was optional and
defaulted to null. The provider followed the schema. `_grounded_span` then
failed every such entry, so the contract was inviting the one shape it was
certain to reject: across 35 live rounds, 185 of the 188 entries in the
`ungrounded_evidence` family were this, and 79% of them cost the whole
interpretation rather than one field.

Enforcing it in Python alone would not have been enough. A `model_validator`
never reaches `model_json_schema()`, so the provider would still see an optional
field and the only change would be where the failure lands -- and it would land
on the worse path, since a first pass that fails to parse leaves no proposal to
patch and the retry falls back to a whole review. Both halves are pinned here.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    OutcomeEvidence, SemanticInterpretation,
)


def entry(**overrides) -> dict:
    return {
        "dimension": "operation", "value": "infer", "source": "explicit",
        "rationale": "The request asks for a network to be inferred.",
        **overrides,
    }


def test_an_explicit_entry_without_a_quote_is_refused():
    with pytest.raises(ValidationError):
        OutcomeEvidence.model_validate(entry())


def test_a_quote_of_nothing_but_whitespace_is_refused():
    """`min_length=1` alone let a space through, and a space grounds nothing."""
    with pytest.raises(ValidationError):
        OutcomeEvidence.model_validate(entry(text_span="   "))


def test_inference_is_still_never_asked_for_a_quote():
    """The rule is about what `explicit` claims, not about requiring quotes."""
    item = OutcomeEvidence.model_validate(entry(source="inferred"))

    assert item.text_span is None


def test_an_explicit_entry_that_quotes_the_request_is_unaffected():
    item = OutcomeEvidence.model_validate(entry(text_span="infer a network"))

    assert item.source == "explicit" and item.text_span == "infer a network"


def test_the_provider_is_shown_the_rule_and_not_only_held_to_it():
    """Otherwise the change moves the failure instead of preventing it.

    The branch has to survive nesting: the provider receives this entry inside
    SemanticInterpretation's `$defs`, never on its own.
    """
    nested = SemanticInterpretation.model_json_schema()["$defs"]["OutcomeEvidence"]
    explicit, inferred = nested["anyOf"]

    assert explicit["properties"]["source"]["enum"] == ["explicit"]
    assert "text_span" in explicit["required"]
    # A nullable type here would satisfy `required` while carrying no quote.
    assert explicit["properties"]["text_span"]["type"] == "string"
    assert inferred["properties"]["source"]["enum"] == ["inferred"]
    assert "text_span" not in inferred["required"]


def test_the_optional_declaration_the_provider_used_to_follow_is_gone():
    """`default: null` on the root field was the invitation, and it still is.

    The root keeps the field optional so `inferred` entries stay valid, which is
    exactly why the branch above has to exist -- this assertion records that the
    root alone would still say the quote may be omitted.
    """
    root = OutcomeEvidence.model_json_schema()

    assert "text_span" not in root["required"]
    assert root["anyOf"], "the branch is the only thing carrying the rule"


def test_each_branch_restates_every_required_property():
    """The defect that cost a whole live round, pinned.

    A branch listing only the properties it constrains is what JSON Schema
    means -- the root still supplies the rest. The provider does not read it
    that way: shown a branch naming only `source` and `text_span`, it returned
    evidence entries carrying only those two, and all 81 trials of a full round
    failed schema validation on the three missing fields. `RequestedOutcome`
    restates them for the same reason.
    """
    root = OutcomeEvidence.model_json_schema()

    for branch in root["anyOf"]:
        missing = [
            name for name in root["required"] if name not in branch["properties"]
        ]
        assert not missing, missing
        assert set(root["required"]) <= set(branch["required"])
