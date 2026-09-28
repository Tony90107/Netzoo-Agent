"""Log 242: competing readings are judged together and each gets its own repair.

A request stating two hypotheses, each over part of the stated data, lost the
second reading in 8 of 18 traced trials (Log 241). The patch repaired only the
reading it adjudicated as primary, and every reading was required to carry
every stated input, so the other was dropped without a word.
"""
from copy import deepcopy
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import IntentDecision  # noqa: E402
from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    OutcomeHypothesis, SemanticInterpretation, SemanticPatch,
)
from netzoo_agent_core.graph.sibling_repair import sibling_patch_schema  # noqa: E402
from netzoo_agent_core.interpretation.outcome_validation import (  # noqa: E402
    validate_outcome_hypotheses,
)

from evaluate_routing import RoutingScenario, _call_limit_errors, evaluate  # noqa: E402


TASK = (
    "I have somatic mutation calls and an RNA-seq expression matrix for the same tumours. "
    "Two hypotheses: either pathway-level mutation scores separate them, or each patient has "
    "its own TF-to-gene regulatory network. Which workflow fits each?"
)


def evidence(dimension, value, span=None):
    return {"dimension": dimension, "value": value, "source": "explicit" if span else "inferred",
            "text_span": span, "rationale": "Scripted."}


def mutation_reading():
    return {
        "outcome": {"operation": "analyze", "input_artifacts": ["mutation_matrix"],
                    "artifact_type": "pathway_mutation_matrix",
                    "entity_types": ["pathway", "sample"], "granularity": "aggregate"},
        "confidence": 0.8,
        "evidence": [
            evidence("operation", "analyze"),
            evidence("input_artifact", "mutation_matrix", "somatic mutation calls"),
            evidence("artifact_type", "pathway_mutation_matrix", "pathway-level mutation scores"),
            evidence("granularity", "aggregate"),
        ],
    }


def network_reading(*, with_input=True):
    item = {
        "outcome": {"operation": "infer", "input_artifacts": ["expression_matrix"] if with_input else [],
                    "artifact_type": "regulatory_network", "entity_types": ["tf", "gene"],
                    "regulator_types": ["tf"], "target_types": ["gene"],
                    "granularity": "sample_specific"},
        "confidence": 0.7,
        "evidence": [
            evidence("operation", "infer"),
            evidence("artifact_type", "regulatory_network", "TF-to-gene regulatory network"),
            evidence("regulator_type", "tf", "TF-to-gene"),
            evidence("target_type", "gene", "TF-to-gene"),
            evidence("granularity", "sample_specific", "each patient has its own"),
        ],
    }
    if with_input:
        item["evidence"].append(evidence("input_artifact", "expression_matrix", "RNA-seq expression matrix"))
    return item


def issues_of(*items):
    hypotheses = [OutcomeHypothesis.model_validate(deepcopy(item)) for item in items]
    return validate_outcome_hypotheses(TASK, hypotheses, "guidance").issues


def test_each_stated_input_is_required_of_the_interpretation_not_of_every_reading():
    assert issues_of(mutation_reading(), network_reading()) == ()
    # Alone, each reading still omits the other's input.
    assert issues_of(mutation_reading()) == ("hypothesis[0].missing_current_input:expression_matrix",)


def test_an_input_every_reading_omits_is_still_missing_on_each():
    first, second = mutation_reading(), network_reading()
    for item in (first, second):
        item["outcome"]["input_artifacts"] = [
            value for value in item["outcome"]["input_artifacts"] if value != "mutation_matrix"
        ]
        item["evidence"] = [e for e in item["evidence"] if e["value"] != "mutation_matrix"]
    issues = issues_of(first, second)
    assert "hypothesis[0].missing_current_input:mutation_matrix" in issues
    assert "hypothesis[1].missing_current_input:mutation_matrix" in issues


def test_the_sibling_schema_fixes_the_index_and_is_strict_compatible():
    schema = sibling_patch_schema(1)
    assert issubclass(schema, SemanticPatch)
    wire = schema.model_json_schema()
    assert wire["properties"]["hypothesis_index"]["enum"] == [1]
    assert wire["additionalProperties"] is False
    assert schema.model_validate({"hypothesis_index": 1}).hypothesis_index == 1
    try:
        schema.model_validate({"hypothesis_index": 0})
    except Exception:
        pass
    else:
        raise AssertionError("a sibling repair must not name another reading")


class SiblingProvider:
    def __init__(self, sibling_reply):
        self.sibling_reply = sibling_reply
        self.calls = []

    def with_structured_output(self, schema, **kwargs):
        provider = self

        class Adapter:
            def invoke(self, messages):
                provider.calls.append((schema.__name__, kwargs, messages))
                if schema is IntentDecision:
                    return {"mode": "answer", "confidence": 0.95, "reason": "Guidance only."}
                if schema is SemanticInterpretation:
                    return {"request_mode": "guidance", "semantic_goal": "Compare two hypotheses",
                            "outcome_hypotheses": [mutation_reading(),
                                                   network_reading(with_input=False)]}
                if schema.__name__ == "SiblingSemanticPatch":
                    reply = provider.sibling_reply
                    if isinstance(reply, BaseException):
                        raise reply
                    return deepcopy(reply)
                if schema is SemanticPatch:
                    return {"hypothesis_index": 0}
                raise AssertionError(f"unexpected call {schema.__name__}")

        return Adapter()


def scenario():
    return RoutingScenario.model_validate({
        "id": "sibling-repair", "language": "en", "category": "positive", "prompt": TASK,
        "expected": {"status": "ambiguous", "actions": []},
    })


def run(provider):
    return evaluate([scenario()], provider=provider, model_name="fixture",
                    review_policy="when_needed")["results"][0]


def test_a_reading_the_patch_left_invalid_gets_its_own_strict_repair():
    provider = SiblingProvider({
        "hypothesis_index": 1,
        "outcome": {"input_artifacts": ["expression_matrix"]},
        "evidence_additions": [
            evidence("input_artifact", "expression_matrix", "RNA-seq expression matrix"),
        ],
    })
    row = run(provider)
    names = [name for name, _, _ in provider.calls]
    assert names.count("SiblingSemanticPatch") == 1
    sibling = next(call for call in provider.calls if call[0] == "SiblingSemanticPatch")
    assert sibling[1] == {"method": "function_calling", "include_raw": True, "strict": True}
    system = sibling[2][0].content
    assert "hypothesis_index is fixed to 1" in system
    assert "primary scientific outcome" not in system
    assert "hypothesis[1].missing_current_input:expression_matrix" in sibling[2][-1].content
    # Both readings reach routing, so the reply can present both.
    assert row["status"] == "ambiguous"
    assert {"run_sambar", "run_lioness_panda"} <= set(row["hypothesis_actions"])
    assert "SAMBAR" in row["answer"] and "LIONESS-PANDA" in row["answer"]
    assert "semantic_sibling_repair" in row["call_roles"]
    assert not _call_limit_errors(row["call_roles"])


def test_a_failed_sibling_repair_relaxes_nothing():
    # No reading carries the stated expression matrix once the repair fails, so
    # the interpretation still fails exactly as it did before Log 242.
    row = run(SiblingProvider(ValueError("provider rejected the call")))
    assert row["status"] is None and row["hypothesis_actions"] == []
    assert row["call_roles"].count("semantic_sibling_repair") == 1
    assert row["call_statuses"][row["call_roles"].index("semantic_sibling_repair")] == "failed"


def test_three_sibling_repairs_would_break_the_bound():
    roles = ["semantic_interpreter", "semantic_reviewer", *["semantic_sibling_repair"] * 3]
    assert _call_limit_errors(roles) == ["call_limit: more than two sibling repairs"]
