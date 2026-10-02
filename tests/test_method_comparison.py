"""Log 302 (MS2): a card's Compare option compares exactly its workflows, through the real graph."""

from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core import settings  # noqa: E402
from netzoo_agent_core.cli.bootstrap import CliRuntime  # noqa: E402
from netzoo_agent_core.cli.conversation import run_conversation  # noqa: E402
from netzoo_agent_core.contracts import (  # noqa: E402
    AIMessage,
    IntentDecision,
    OutcomeEvidence,
    OutcomeHypothesis,
    RequestedOutcome,
)
from netzoo_agent_core.contracts.interaction import MethodComparison  # noqa: E402
from netzoo_agent_core.contracts.outcomes import SemanticInterpretation, SemanticReview  # noqa: E402
from netzoo_agent_core.engine.machine import ConversationMachine  # noqa: E402
from netzoo_agent_core.framework_compat import StateGraph  # noqa: E402
from netzoo_agent_core.graph.context import _GraphContext  # noqa: E402
from netzoo_agent_core.graph.topology import compile_graph  # noqa: E402
from netzoo_agent_core.memory import EpisodeStore, UserProfileStore  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402
from netzoo_agent_core.pricing import PriceCatalog  # noqa: E402
from netzoo_agent_core.runtime import configure_runtime  # noqa: E402
from netzoo_agent_core.trace_store import LocalTraceStore  # noqa: E402
from netzoo_agent_core.tracing import TraceRecorder  # noqa: E402

GOAL = (
    "I have expression, motif and PPI priors. I want to factorize gene expression "
    "using these priors into one cohort TF-to-gene network. Which workflow? Advice only."
)
TRIO = ["run_giraffe", "run_panda", "run_otter"]
pytestmark = pytest.mark.skipif(StateGraph is None, reason="Run in the project Docker environment.")


def tf_aggregate() -> OutcomeHypothesis:
    return OutcomeHypothesis(
        outcome=RequestedOutcome(
            operation="infer", artifact_type="regulatory_network", entity_types=["tf", "gene"],
            regulator_types=["tf"], target_types=["gene"], granularity="aggregate",
        ),
        confidence=0.95,
        evidence=[
            OutcomeEvidence(dimension=dimension, value=value, source="inferred",
                            rationale="The fixture supplies this dimension.")
            for dimension, value in (
                ("operation", "infer"), ("artifact_type", "regulatory_network"),
                ("regulator_type", "tf"), ("target_type", "gene"), ("granularity", "aggregate"),
            )
        ],
    )


@pytest.fixture
def runtime(tmp_path, request):
    policy = ProjectPolicyLoader(settings.PROJECT_ROOT).load()
    changes = {
        "PROJECT_ROOT": tmp_path, "SESSION_ROOT": tmp_path / "sessions",
        "TRACE_ROOT": tmp_path / "traces", "TOOL_LOG_ROOT": tmp_path / "tool_logs",
        "EXECUTE_TOOLS": False, "TEST_DATA_MODE": True, "TRACE_ENABLED": False,
        "TRANSIENT_TRACE": False,
    }
    previous = {key: getattr(settings, key) for key in changes}
    request.addfinalizer(lambda: configure_runtime(**previous))
    configure_runtime(**changes)
    store = LocalTraceStore(tmp_path / "traces")
    recorder = TraceRecorder(store)
    hypothesis = tf_aggregate()
    interpretation = SemanticInterpretation(
        request_mode="guidance", semantic_goal="aggregate TF-gene network",
        outcome_hypotheses=[hypothesis],
    )
    discriminator = Mock(invoke=Mock(return_value={"parsed": {
        "selection_tags": ["biologically_informed_matrix_factorization"],
        "evidence": [{
            "dimension": "selection_tag", "value": "biologically_informed_matrix_factorization",
            "source": "explicit", "text_span": "factorize gene expression",
            "rationale": "The request names matrix factorization.",
        }],
    }, "raw": object()}))
    context = _GraphContext(
        profile_id="default", profile_store=UserProfileStore(tmp_path / "profiles"),
        episode_store=EpisodeStore(tmp_path / "episodes"), project_policy=policy,
        recorder=recorder, price_catalog=PriceCatalog.from_environment(),
        semantic_interpreter=Mock(invoke=Mock(return_value=interpretation)),
        semantic_reviewer=Mock(invoke=Mock(return_value=SemanticReview(
            request_mode="guidance", semantic_goal=interpretation.semantic_goal,
            outcome_hypothesis=hypothesis,
        ))),
        intent_router=Mock(invoke=Mock(return_value=IntentDecision(
            mode="answer", confidence=0.99, reason="Workflow guidance requested.",
        ))),
        input_content_mapper=None,
        response_llm=Mock(invoke=Mock(return_value=AIMessage(content="Workflow response."))),
        semantic_model_name="fake", router_model_name="fake", response_model_name="fake",
        semantic_prompt="Interpret the request.", intent_prompt="Classify intent.",
        response_prompt="Explain validated facts.", router_max_tokens=1200,
        response_max_tokens=800, task_token_budget=20_000,
        semantic_discriminator=discriminator,
    )
    results = []

    def invoke(app, invocation):
        result = app.invoke(invocation)
        results.append(result)
        return result

    cli = CliRuntime(
        memory=SimpleNamespace(profile_id="default", profile_store=context.profile_store,
                               episode_store=context.episode_store),
        project_policy=policy, session_id="comparison-test", resume_id=None, conversation=[],
        pending_plan=None, active_usage=None, run_id=None, recorder=recorder, trace_store=store,
        ensure_trace_sync=lambda _: None, app=compile_graph(context), input_func=Mock(),
        invoke_graph_turn_func=invoke, reply_resolver=Mock(),
    )
    return SimpleNamespace(cli=cli, context=context, results=results, discriminator=discriminator)


def compare_answer(runtime):
    """The Compare option's text on the first reply's card, as the window submits it."""
    machine = ConversationMachine(SimpleNamespace(task=None), runtime.cli)
    machine._accept_task(GOAL)
    machine.run_turn()
    options = machine.state.reply_card["next_steps"]
    return machine, next(option for option in options if option["key"] == "compare-others")


def test_the_narrowed_card_offers_a_typed_comparison_of_its_tie(runtime):
    _, compare = compare_answer(runtime)

    assert compare["resolution"] == "compare_workflows"
    assert compare["compare_actions"] == TRIO
    assert compare["answer"].startswith("Compare GIRAFFE with PANDA and OTTER for this goal.")


def test_picking_compare_shows_exactly_those_workflows_without_rerouting(runtime):
    runtime.cli.input_func.side_effect = [GOAL, "Compare GIRAFFE with PANDA and OTTER for this goal. "
                                          "How do their assumptions differ, and which fits my study?", "exit"]

    assert run_conversation(SimpleNamespace(task=None, keep_session=False), runtime.cli) == 0

    first, compared = runtime.results
    assert first["plan"]["decision"]["matched_actions"] == ["run_giraffe"]
    decision = compared["plan"]["decision"]
    assert decision["capability_match_status"] == "ambiguous"
    assert decision["hypothesis_actions"] == TRIO
    assert decision["matched_actions"] == [] and decision["action"] == "no_tool"
    assert decision["requested_outcome"]["artifact_type"] == "regulatory_network"
    assert compared["tool_results"] == []
    # The comparison re-reads nothing: one interpretation and one discriminator call in all.
    assert runtime.context.semantic_interpreter.invoke.call_count == 1
    assert runtime.discriminator.invoke.call_count == 1
    assert "Previous NetZoo goal:" in compared["messages"][-2].content
    assert compared.get("method_comparison") is None
    for name in ("PANDA", "OTTER", "GIRAFFE"):
        assert name in compared["messages"][-1].content


def test_the_choice_after_a_comparison_is_its_workflows(runtime):
    machine, compare = compare_answer(runtime)
    machine._submit_option(compare)
    assert machine.state.pending_comparison.actions == TRIO
    machine.run_turn()

    card = machine.state.reply_card
    assert card["kind"] == "method_choice"
    assert {option["action"] for option in card["choices"]["options"]} == set(TRIO)
    assert all(option["resolution"] == "confirm_workflow" for option in card["choices"]["options"])
    assert machine.state.pending_comparison is None


@pytest.mark.parametrize("actions", [["run_giraffe"], ["run_giraffe", "web_search"], ["run_panda", "run_panda"]])
def test_an_invalid_comparison_is_an_ordinary_follow_up(runtime, actions):
    machine, compare = compare_answer(runtime)
    machine._submit_option({**compare, "compare_actions": actions})

    assert machine.state.pending_comparison is None
    assert machine.state.pending_task.startswith("Previous NetZoo goal:")


def test_a_stale_comparison_is_routed_as_usual(runtime):
    run_id = runtime.cli.recorder.start_run(session_id="stale-comparison", profile_id="default")
    stale = MethodComparison(actions=["run_panda", "run_otter"], task="some previous task").model_dump()
    from netzoo_agent_core.contracts import HumanMessage

    result = runtime.cli.app.invoke({
        "messages": [HumanMessage(content=GOAL)], "method_comparison": stale, "run_id": str(run_id),
    })

    assert result["plan"]["decision"]["matched_actions"] == ["run_giraffe"]
    assert runtime.context.semantic_interpreter.invoke.call_count == 1
