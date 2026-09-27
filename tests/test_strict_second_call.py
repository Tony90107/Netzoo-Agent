"""Log 208: the patch, the usual second semantic call, is bound strict.

The fallbacks left under the current code were second-call replies that broke
the schema: explicit evidence without a quote, an evidence dimension spelled
`input_artifacts`, an out-of-vocabulary `unresolved_dimensions` entry. The
patch schema now reaches the provider in strict-mode form; what validation
accepts is unchanged. The first pass, the whole review (2 of 79 second calls
in the current-code record; strict would more than double its input) and the
discriminator are not touched.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import netzoo_agent_core.graph.factory as factory  # noqa: E402
from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    SemanticDiscriminator,
    SemanticInterpretation,
    SemanticPatch,
    SemanticReview,
)
from netzoo_agent_core.contracts.strict_schema import strict_json_schema  # noqa: E402


def _objects(node):
    if isinstance(node, dict):
        if isinstance(node.get("properties"), dict):
            yield node
        for value in node.values():
            yield from _objects(value)
    elif isinstance(node, list):
        for item in node:
            yield from _objects(item)


def test_every_object_lists_every_property_and_nothing_else():
    schema = SemanticPatch.model_json_schema()
    objects = list(_objects(schema))

    assert objects
    for node in objects:
        assert set(node["required"]) == set(node["properties"])
        assert node["additionalProperties"] is False
        assert "anyOf" not in node, "strict mode rejects properties beside branches"
    assert '"default"' not in json.dumps(schema)


def test_explicit_evidence_must_quote_and_inferred_cannot():
    evidence = SemanticPatch.model_json_schema()["$defs"]["OutcomeEvidence"]["anyOf"]
    explicit, inferred = evidence

    assert explicit["properties"]["source"]["enum"] == ["explicit"]
    assert "text_span" in explicit["required"]
    assert inferred["properties"]["source"]["enum"] == ["inferred"]
    assert "text_span" not in inferred["properties"]
    assert set(explicit["properties"]["dimension"]["enum"]) >= {"input_artifact", "artifact_type"}


def test_null_means_the_same_as_omitting_a_field():
    omitted = SemanticPatch.model_validate({"hypothesis_index": 0, "outcome": {"granularity": "aggregate"}})
    nulls = SemanticPatch.model_validate({
        "hypothesis_index": 0, "request_mode": None, "semantic_goal": None, "confidence": None,
        "outcome": {field: None for field in SemanticPatch.model_fields["outcome"].annotation.model_fields}
        | {"granularity": "aggregate"},
        "evidence_removals": [], "evidence_additions": [], "assumptions": None,
    })

    assert nulls == omitted


def test_the_first_pass_the_review_and_the_discriminator_are_not_touched():
    def digest(model):
        return hashlib.sha256(json.dumps(model.model_json_schema(), sort_keys=True).encode()).hexdigest()[:12]

    # Values at 4d11fef, before Log 208.
    assert digest(SemanticInterpretation) == "f9ef84d1326b"
    assert digest(SemanticReview) == "c6fa6eb609a1"
    assert digest(SemanticDiscriminator) == "af2e0c9dff2f"


def test_a_nullable_field_keeps_its_type():
    schema = strict_json_schema({
        "type": "object",
        "properties": {"a": {"anyOf": [{"type": "string"}, {"type": "null"}], "default": None},
                       "b": {"type": "integer", "default": 0}},
    })

    assert schema["required"] == ["a", "b"]
    assert schema["properties"]["a"]["anyOf"] == [{"type": "string"}, {"type": "null"}]
    assert schema["properties"]["b"] == {"type": "integer"}


def test_production_binds_only_the_patch_strict(monkeypatch):
    monkeypatch.setenv("NETZOO_ROUTER_MODEL_ALLOWLIST", "fake")
    monkeypatch.setenv("NETZOO_RESPONSE_MODEL_ALLOWLIST", "fake")
    bindings = []

    class Recorder:
        def with_structured_output(self, schema, **options):
            bindings.append((schema, options))
            return self

        def invoke(self, _messages):
            raise AssertionError("not called")

    monkeypatch.setattr(factory, "build_llm", lambda *_args, **_kwargs: Recorder())
    factory.build_graph("fake", 0.0, router_model_name="fake", semantic_contract="legacy")

    strict = {schema: options.get("strict", False) for schema, options in bindings}
    assert strict[SemanticPatch] is True
    assert not any(strict[schema] for schema in (SemanticInterpretation, SemanticReview, SemanticDiscriminator))
