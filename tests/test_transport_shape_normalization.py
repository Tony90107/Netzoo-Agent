"""An unambiguous single-key wrapper is the same literal, not a different meaning.

Live runs recorded `{"artifact_type": "mutation_matrix"}` inside `input_artifacts`,
where one enum string belongs: the model mirrors the outcome's own field names.
Unwrapping a single-key object loses nothing and the value is still validated
strictly against the closed vocabulary. Anything that would require a choice --
extra keys, an unknown key, a non-string value -- stays a located schema error.
This normalizes transport, never scientific meaning: no name is ever mapped.
"""
from pathlib import Path
import sys

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.outcomes import RequestedOutcome  # noqa: E402


def outcome(**overrides):
    return RequestedOutcome.model_validate({
        "operation": "analyze",
        "artifact_type": "sample_cluster_assignment",
        "granularity": "aggregate",
        **overrides,
    })


@pytest.mark.parametrize("key", ["artifact_type", "artifact", "type", "name", "value", "input_artifact"])
def test_a_single_key_wrapper_is_the_literal_it_wraps(key):
    assert outcome(input_artifacts=[{key: "mutation_matrix"}]).input_artifacts == ["mutation_matrix"]


def test_unwrapping_never_maps_a_name_onto_the_vocabulary():
    """`somatic_mutation` is an input modality, not an artifact type."""
    with pytest.raises(ValidationError) as raised:
        outcome(input_artifacts=[{"artifact_type": "somatic_mutation"}])

    issue = raised.value.errors()[0]
    assert list(issue["loc"]) == ["input_artifacts", 0]
    assert issue["input"] == "somatic_mutation"


@pytest.mark.parametrize("value, ids", [
    # A repeated-measurement run reclassified `{artifact_type, granularity}` as a
    # mirrored outcome object; it now has its own case below. A sibling key that
    # is not an outcome field still leaves the item's meaning undecided.
    ({"artifact_type": "mutation_matrix", "source": "explicit"}, "non-outcome-sibling"),
    ({"unexpected": "mutation_matrix"}, "unknown-key"),
    ({"artifact_type": {"nested": "mutation_matrix"}}, "non-string-value"),
    ({"artifact_type": ["mutation_matrix"]}, "list-value"),
    ({}, "empty-object"),
    (["mutation_matrix"], "list-item"),
])
def test_an_ambiguous_shape_stays_a_located_schema_error(value, ids):
    with pytest.raises(ValidationError) as raised:
        outcome(input_artifacts=[value])

    assert ["input_artifacts", 0] == list(raised.value.errors()[0]["loc"])


def test_a_malformed_container_is_still_reported_on_the_field():
    for container in ("mutation_matrix", 5, {"0": "mutation_matrix"}):
        with pytest.raises(ValidationError) as raised:
            outcome(input_artifacts=container)
        assert ["input_artifacts"] == list(raised.value.errors()[0]["loc"])


@pytest.mark.parametrize("field, value", [
    ("entity_types", "sample"),
    ("regulator_types", "tf"),
    ("target_types", "gene"),
])
def test_every_closed_vocabulary_list_shares_the_same_transport_rule(field, value):
    artifact = "regulatory_network" if field in {"regulator_types", "target_types"} else "sample_cluster_assignment"
    result = outcome(**{"artifact_type": artifact, field: [{"type": value}]})

    assert getattr(result, field) == [value]


@pytest.mark.parametrize("field", ["display_entities", "selection_tags", "unresolved_dimensions"])
def test_free_text_lists_are_never_unwrapped(field):
    """These carry arbitrary text, so an object there is a real error, not a wrapper."""
    with pytest.raises(ValidationError) as raised:
        outcome(**{field: [{"type": "anything"}]})

    assert [field, 0] == list(raised.value.errors()[0]["loc"])


# Observed live at 5 of 9 trials: the reviewer copies the repair message's
# `field_constraints` object into `input_artifacts`. Its key set matches
# `artifact_field_constraints()` exactly and carries no `operation`, which rules
# out the schema's artifact branches as the source.
OUTCOME_SHAPED_MIRRORS = {
    "two-field-echo": {"artifact_type": "mutation_matrix", "granularity": "aggregate"},
    "full-constraint-echo": {
        "artifact_type": "mutation_matrix", "entity_types": ["sample"],
        "granularity": "aggregate", "regulator_types": [], "target_types": [],
    },
}


@pytest.mark.parametrize("case", sorted(OUTCOME_SHAPED_MIRRORS), ids=sorted(OUTCOME_SHAPED_MIRRORS))
def test_an_outcome_shaped_mirror_is_the_literal_it_names(case):
    """Sibling outcome fields have no meaning inside one input item, so nothing
    representable is discarded by reading the artifact literal it names."""
    result = outcome(input_artifacts=[OUTCOME_SHAPED_MIRRORS[case]])

    assert result.input_artifacts == ["mutation_matrix"]


def test_a_mirror_still_maps_no_name_onto_the_vocabulary():
    with pytest.raises(ValidationError) as raised:
        outcome(input_artifacts=[{"artifact_type": "somatic_mutation", "granularity": "aggregate"}])

    assert raised.value.errors()[0]["input"] == "somatic_mutation"


@pytest.mark.parametrize("value", [
    {"artifact_type": "mutation_matrix", "unexpected": 1},
    {"granularity": "aggregate", "entity_types": ["sample"]},
    {"artifact_type": ["mutation_matrix"], "granularity": "aggregate"},
    {"artifact_type": "mutation_matrix", "type": "expression_matrix"},
])
def test_anything_that_is_not_a_clean_mirror_stays_an_error(value):
    with pytest.raises(ValidationError) as raised:
        outcome(input_artifacts=[value])

    assert ["input_artifacts", 0] == list(raised.value.errors()[0]["loc"])


def test_the_repair_message_labels_constraints_as_schema_not_values():
    from netzoo_agent_core.interpretation.semantic_repair import repair_feedback

    expected = repair_feedback(
        {"outcome_hypotheses": [{"outcome": {"operation": "analyze",
                                             "artifact_type": "sample_cluster_assignment",
                                             "granularity": "aggregate"},
                                 "confidence": 0.9, "evidence": []}]},
        ("hypothesis[0].missing_current_input:mutation_matrix",),
        "我有一份 DNA 突變資料，想對病患分群。",
    )[0]["expected"]

    note = expected["field_constraints_note"].casefold()
    assert "not values" in note
    assert "outcome" in note
