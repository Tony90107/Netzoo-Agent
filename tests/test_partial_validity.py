"""Log 156: an unrepaired invalid reading no longer sinks a valid one."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    OutcomeEvidence,
    OutcomeHypothesis,
    RequestedOutcome,
    SemanticInterpretation,
)
from netzoo_agent_core.graph.partial_validity import keep_valid_hypotheses  # noqa: E402
from netzoo_agent_core.interpretation.outcome_validation import validate_outcome_hypotheses  # noqa: E402
from netzoo_agent_core.pricing import PriceCatalog  # noqa: E402
from netzoo_agent_core.trace_store import LocalTraceStore  # noqa: E402
from netzoo_agent_core.tracing import TraceRecorder  # noqa: E402

TASK = "I believe each patient's regulatory wiring is different; I want per-TF targeting per patient."
SPAN = "each patient's regulatory wiring is different"


def _valid() -> OutcomeHypothesis:
    return OutcomeHypothesis(
        outcome=RequestedOutcome(operation="infer", artifact_type="regulatory_network",
                                 granularity="sample_specific"),
        confidence=0.9,
        evidence=[OutcomeEvidence(dimension=d, value=v, source="explicit", text_span=SPAN, rationale="t")
                  for d, v in (("artifact_type", "regulatory_network"), ("granularity", "sample_specific"))],
    )


def _invalid() -> OutcomeHypothesis:
    """Quotes evidence the request does not contain."""
    return OutcomeHypothesis(
        outcome=RequestedOutcome(operation="infer", artifact_type="expression_matrix",
                                 granularity="sample_specific", entity_types=["gene"]),
        confidence=0.8,
        evidence=[OutcomeEvidence(dimension="artifact_type", value="expression_matrix",
                                  source="explicit", text_span="an expression matrix", rationale="t")],
    )


def _context(tmp_path):
    store = LocalTraceStore(tmp_path / "traces")
    recorder = TraceRecorder(store)
    run_id = recorder.start_run(session_id="log156", profile_id="default")
    return SimpleNamespace(recorder=recorder, price_catalog=PriceCatalog()), {"run_id": str(run_id)}, store, run_id


def _run(tmp_path, hypotheses):
    interpretation = SemanticInterpretation(request_mode="guidance", semantic_goal="g",
                                            outcome_hypotheses=hypotheses)
    validation = validate_outcome_hypotheses(
        TASK, [h.model_copy(deep=True) for h in hypotheses], "guidance")
    context, state, store, run_id = _context(tmp_path)
    kept, result = keep_valid_hypotheses(context, state, TASK, interpretation, validation, 1)
    return interpretation, validation, kept, result, store.read_events(run_id)


def test_the_valid_reading_survives_an_unrepaired_invalid_one(tmp_path):
    original, before, kept, after, events = _run(tmp_path, [_valid(), _invalid()])

    assert not before.valid
    assert after.valid
    assert [h.outcome.artifact_type for h in kept.outcome_hypotheses] == ["regulatory_network"]
    dropped = [e for e in events if e.event_type == "routing.invalid_hypotheses_dropped"]
    assert dropped and dropped[0].payload["dropped"][0]["hypothesis"] == 1


def test_nothing_changes_when_every_reading_is_invalid(tmp_path):
    original, before, kept, after, _ = _run(tmp_path, [_invalid(), _invalid()])

    assert kept is original and after is before and not after.valid


def test_nothing_changes_when_every_reading_is_valid(tmp_path):
    original, before, kept, after, _ = _run(tmp_path, [_valid(), _valid()])

    assert before.valid and kept is original


def test_a_single_invalid_reading_is_still_rejected(tmp_path):
    original, before, kept, after, _ = _run(tmp_path, [_invalid()])

    assert kept is original and not after.valid
