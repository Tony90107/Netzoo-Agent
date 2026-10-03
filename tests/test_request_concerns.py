"""Log 223: a guidance reply answers the practical concerns the request states.

Case 2 of the blind test says the last method "ran out of memory and took
forever to stop iterating"; the OTTER reply listed eight controls and said
nothing about either. The concern matcher offers the selected workflow's
registry-declared concerns, keeps a claim only if it was offered and its quote
is in the request, and the reply shows the registry's note with the quote.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import workflow_registry  # noqa: E402
from workflow_registry import ACTION_DEFINITIONS, OUTPUT_CAPABILITIES, REQUEST_CONCERNS, RequestConcern  # noqa: E402
import netzoo_agent as agent  # noqa: E402
from netzoo_agent_core.contracts import LLMUsage  # noqa: E402
from netzoo_agent_core.contracts.outcomes import StatedConcernClaims  # noqa: E402
import netzoo_agent_core.graph.request_concerns as request_concerns  # noqa: E402
import netzoo_agent_core.interpretation.verified_guidance as verified_guidance  # noqa: E402
from netzoo_agent_core.graph.request_concerns import (  # noqa: E402
    addressed_from_claims,
    concern_options,
    concern_schema,
    invoke_concern_matcher,
)
from evaluate_routing import _call_limit_errors  # noqa: E402

TASK = (
    "I need one consensus regulatory network for a tissue. Last time a similar method "
    "ran out of memory and took forever to stop iterating."
)
FIXTURE = (
    RequestConcern(
        concern="memory_limit", label="memory use is a limiting factor",
        note="Fixture note about memory.", controls=("precision",),
    ),
    RequestConcern(
        concern="iteration_stopping", label="the iterations take long or never stop",
        note="Fixture note about stopping.", controls=("iterations",),
    ),
)


@pytest.fixture
def otter_concerns(monkeypatch):
    table = {**REQUEST_CONCERNS, "run_otter": FIXTURE}
    monkeypatch.setattr(request_concerns, "REQUEST_CONCERNS", table)
    monkeypatch.setattr(verified_guidance, "REQUEST_CONCERNS", table)
    return table


class Adapter:
    def __init__(self, reply):
        self.reply = reply

    def invoke(self, _messages):
        if isinstance(self.reply, BaseException):
            raise self.reply
        return self.reply


class Provider:
    def __init__(self, reply):
        self.reply = reply
        self.schemas = []
        self.options = []

    def with_structured_output(self, schema, **options):
        self.schemas.append(schema)
        self.options.append(options)
        return Adapter(self.reply)


class Recorder:
    def __init__(self):
        self.events = []

    def append(self, run_id, event, node, data):
        self.events.append((event, data))


def _context(reply, **extra):
    return SimpleNamespace(
        selection_condition_llm=Provider(reply), semantic_claims=False,
        semantic_model_name="offline", router_max_tokens=2000,
        task_token_budget=100000, price_catalog=None, recorder=Recorder(), **extra,
    )


def _decision(**update):
    values = dict(
        action="no_tool", in_scope=True, should_execute=False, confidence=.95,
        reason="Guidance", capability_match_status="exact", match_basis="registry_features",
        matched_actions=["run_otter"], recommended_actions=["run_otter"],
    )
    values.update(update)
    return agent.TaskDecision(**values)


def _invoke(context, decision, task=TASK):
    return invoke_concern_matcher(context, {}, task, decision, LLMUsage(budget_tokens=100000), [])


def _claims(*pairs):
    return {"claims": [{"concern": concern, "text_span": span} for concern, span in pairs]}


# -- registry --------------------------------------------------------------


def test_every_declared_concern_points_to_what_its_workflow_declares():
    for action, concerns in REQUEST_CONCERNS.items():
        controls = {control.name for control in ACTION_DEFINITIONS[action].controls}
        artifacts = set(OUTPUT_CAPABILITIES[action].produced_artifacts) | {
            OUTPUT_CAPABILITIES[action].artifact_type
        }
        assert len({item.concern for item in concerns}) == len(concerns), action
        for item in concerns:
            assert item.note.strip() and item.label.strip(), (action, item.concern)
            assert item.controls or item.artifacts, (action, item.concern)
            assert set(item.controls) <= controls, (action, item.concern)
            assert set(item.artifacts) <= artifacts, (action, item.concern)


def test_a_concern_id_means_the_same_statement_for_every_workflow():
    labels = {}
    for concerns in REQUEST_CONCERNS.values():
        for item in concerns:
            assert labels.setdefault(item.concern, item.label) == item.label, item.concern


def test_concern_ids_and_labels_never_name_a_workflow():
    names = {definition.workflow.casefold() for definition in ACTION_DEFINITIONS.values()}
    for concerns in REQUEST_CONCERNS.values():
        for item in concerns:
            words = set(item.concern.casefold().split("_")) | set(item.label.casefold().split())
            assert not words & names, item.concern


# -- claims ------------------------------------------------------------------


def test_the_schema_offers_exactly_the_declared_concerns_in_strict_form():
    schema = concern_schema([("memory_limit", "a"), ("iteration_stopping", "b")]).model_json_schema()

    claim = schema["$defs"]["ConcernClaim"]
    assert claim["properties"]["concern"]["enum"] == ["memory_limit", "iteration_stopping"]
    assert claim["additionalProperties"] is False and set(claim["required"]) == {"concern", "text_span"}
    assert schema["required"] == ["claims"] and schema["additionalProperties"] is False


def test_only_offered_grounded_claims_are_kept(otter_concerns):
    claims = StatedConcernClaims.model_validate(_claims(
        ("memory_limit", "ran out of memory"),
        ("memory_limit", "ran out of memory"),
        ("iteration_stopping", "never converges at all"),
        ("gpu_available", "ran out of memory"),
    ))

    addressed, rejected = addressed_from_claims(TASK, claims, ["run_otter"])

    assert [(item.action, item.concern, item.text_span) for item in addressed] == [
        ("run_otter", "memory_limit", "ran out of memory"),
    ]
    assert rejected == [
        {"concern": "iteration_stopping", "reason": "quote_not_in_request"},
        {"concern": "gpu_available", "reason": "not_offered"},
    ]


# -- stage -------------------------------------------------------------------


def test_stated_concerns_attach_without_changing_the_decision(otter_concerns):
    context = _context({"parsed": _claims(
        ("memory_limit", "ran out of memory"),
        ("iteration_stopping", "took forever to stop iterating"),
    ), "raw": None})
    decision = _decision()

    advised, _, _ = _invoke(context, decision)

    assert [item.concern for item in advised.addressed_concerns] == ["memory_limit", "iteration_stopping"]
    for field in ("action", "should_execute", "capability_match_status", "matched_actions",
                  "recommended_actions", "clarification_question"):
        assert getattr(advised, field) == getattr(decision, field), field
    assert context.selection_condition_llm.options == [
        {"method": "function_calling", "include_raw": True, "strict": True},
    ]
    assert [event for event, _ in context.recorder.events] == [
        "routing.request_concerns_started", "routing.request_concerns_matched",
    ]


@pytest.mark.parametrize("update", [
    {"capability_match_status": "ambiguous", "matched_actions": [], "recommended_actions": []},
    {"should_execute": True, "action": "run_otter"},
    {"matched_actions": ["run_puma"], "recommended_actions": ["run_puma"]},
])
def test_no_call_outside_selected_guidance_with_declared_concerns(otter_concerns, monkeypatch, update):
    monkeypatch.setitem(otter_concerns, "run_puma", ())
    context = _context({"parsed": _claims(("memory_limit", "ran out of memory")), "raw": None})
    decision = _decision(**update)

    advised, _, _ = _invoke(context, decision)

    assert advised is decision
    assert context.selection_condition_llm.schemas == []


def test_the_claims_contract_makes_no_concern_call(otter_concerns):
    context = _context({"parsed": _claims(("memory_limit", "ran out of memory")), "raw": None})
    context.semantic_claims = True
    decision = _decision()

    assert _invoke(context, decision)[0] is decision
    assert context.selection_condition_llm.schemas == []


def test_a_failed_call_leaves_the_decision_as_it_was(otter_concerns):
    context = _context(RuntimeError("provider down"))
    decision = _decision()

    advised, usage, _ = _invoke(context, decision)

    assert advised is decision
    assert [call.role for call in usage.calls] == ["request_concerns"]
    assert context.recorder.events[-1][0] == "routing.request_concerns_failed"


# -- reply -------------------------------------------------------------------


def _reply(decision, task=TASK):
    policy = agent.ProjectPolicyLoader(agent.PROJECT_ROOT).load()
    return verified_guidance.render_verified_guidance(
        decision, verified_guidance.guidance_contract(decision, policy, task),
    )


def test_the_reply_answers_the_quoted_concern_and_lists_its_control_in_full(otter_concerns):
    decision = _decision(addressed_concerns=[
        {"action": "run_otter", "concern": "memory_limit", "text_span": "ran out of memory"},
    ])

    answer = _reply(decision)

    assert 'What you asked about:\n\n- "ran out of memory" — Fixture note about memory.' in answer
    matched = answer.split("Controls matching this request:\n\n", 1)[1].split("\n\n", 1)[0]
    assert matched.startswith("- `precision` (type=enum; default=double")
    other = answer.split("Other declared controls", 1)[1].split("\n", 1)[0]
    assert "`precision`" not in other and "`iterations`=60" in other
    assert answer.index("What you asked about") < answer.index("**OTTER**:")


def test_without_concerns_the_reply_is_unchanged(otter_concerns):
    assert "What you asked about" not in _reply(_decision())


# -- evaluator bounds --------------------------------------------------------

ROUTING = ["semantic_interpreter", "semantic_reviewer", "semantic_discriminator", "intent_router"]


def test_the_concern_call_is_advisory_and_bounded_once():
    assert _call_limit_errors([*ROUTING, "request_concerns"]) == []
    assert _call_limit_errors([*ROUTING, "request_concerns", "request_concerns"]) == [
        "call_limit: more than one advisory call",
    ]
    assert _call_limit_errors([*ROUTING, "selection_conditions", "request_concerns"]) == [
        "call_limit: more than one advisory call",
    ]


def test_the_registry_module_exports_the_table():
    assert workflow_registry.REQUEST_CONCERNS is REQUEST_CONCERNS


# -- wiring (Log 226: the first version was wired into the fallback path) -----


def test_the_router_runs_the_stage_once_after_preflight_on_the_main_path(monkeypatch):
    import netzoo_agent_core.graph.router_invocation as router_invocation
    from test_ambiguous_guidance_is_scored import row

    calls = []
    for name, label in (("apply_input_preflight_intent", "preflight"),
                        ("invoke_concern_matcher", "concerns")):
        original = getattr(router_invocation, name)

        def recorded(*args, _original=original, _label=label, **kwargs):
            calls.append(_label)
            return _original(*args, **kwargs)

        monkeypatch.setattr(router_invocation, name, recorded)

    row()

    assert calls == ["preflight", "concerns"]


def test_the_semantic_failure_path_makes_no_concern_call(monkeypatch):
    import netzoo_agent_core.graph.router_invocation as router_invocation
    from evaluate_routing import evaluate
    from test_ambiguous_guidance_is_scored import case
    from test_routing_evaluation import FixtureProvider
    from netzoo_agent_core.contracts.outcomes import SemanticInterpretation, SemanticPatch, SemanticReview

    calls = []
    monkeypatch.setattr(router_invocation, "invoke_concern_matcher",
                        lambda *args, **kwargs: calls.append("concerns"))
    provider = FixtureProvider()
    for schema in (SemanticInterpretation, SemanticReview, SemanticPatch):
        provider.responses[schema] = RuntimeError("semantic provider down")

    result = evaluate([case()], provider=provider, model_name="fixture")["results"][0]

    assert result["path"] == "semantic_fallback"
    assert calls == []


# -- Log 336: a downstream use stated in words ----------------------------------

TEST10 = ("We collected liver tissue from 90 patients across three disease stages (cirrhosis, early HCC, "
          "and advanced HCC), with one sample per patient and follow-up survival data. We want to find "
          "regulatory circuits that become progressively dysregulated with disease severity. Pairwise group "
          "comparisons are not enough; we want a network for each patient so we can model associations "
          "with disease stage and survival. What workflow would you recommend?")


def test_a_downstream_use_stated_in_words_is_a_concern_when_no_claim_names_it():
    addressed, rejected = request_concerns.addressed_from_claims(
        TEST10, StatedConcernClaims(claims=[]), ["run_panda", "run_lioness_panda"])
    assert rejected == []
    assert [(item.action, item.concern) for item in addressed] == [
        ("run_panda", "downstream_use"), ("run_lioness_panda", "downstream_use")]
    assert addressed[0].text_span == (
        "we want a network for each patient so we can model associations with disease stage and survival.")


def test_a_claimed_downstream_use_is_not_added_twice():
    claims = StatedConcernClaims.model_validate(_claims(("downstream_use", "model associations with disease stage")))
    addressed, _ = request_concerns.addressed_from_claims(TEST10, claims, ["run_lioness_panda"])
    assert [(item.concern, item.text_span) for item in addressed] == [
        ("downstream_use", "model associations with disease stage")]


def test_no_downstream_concern_without_the_words():
    task = "We want to estimate how strongly each transcription factor regulates its target genes. Which method?"
    assert request_concerns.addressed_from_claims(task, StatedConcernClaims(claims=[]), ["run_lioness_panda"]) == ([], [])


def test_the_lioness_note_covers_ordered_stages_and_survival():
    note = next(c.note for c in REQUEST_CONCERNS["run_lioness_panda"] if c.concern == "downstream_use")
    assert "Cox model" in note and "ordinal or linear regression on stage" in note
    assert "multiple-testing correction" in note and "cross-sectional" in note
