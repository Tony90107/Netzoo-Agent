"""Exercise CLI continuations through the real graph and input planner."""

from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core import settings  # noqa: E402
from netzoo_agent_core.cli.bootstrap import CliRuntime  # noqa: E402
from netzoo_agent_core.cli.conversation import run_conversation  # noqa: E402
from netzoo_agent_core.cli.reply_resolution import ContextualReplyResolver  # noqa: E402
from netzoo_agent_core.contracts import (  # noqa: E402
    AIMessage,
    HumanMessage,
    IntentDecision,
    OutcomeEvidence,
    OutcomeHypothesis,
    ReplyIntentDecision,
    RequestedOutcome,
)
from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    SemanticInterpretation,
    SemanticReview,
)
from netzoo_agent_core.graph.context import _GraphContext  # noqa: E402
from netzoo_agent_core.graph.topology import compile_graph  # noqa: E402
from netzoo_agent_core.framework_compat import StateGraph  # noqa: E402
from netzoo_agent_core.memory import EpisodeStore, UserProfileStore  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402
from netzoo_agent_core.pricing import PriceCatalog  # noqa: E402
from netzoo_agent_core.runtime import configure_runtime  # noqa: E402
from netzoo_agent_core.trace_store import LocalTraceStore  # noqa: E402
from netzoo_agent_core.tracing import TraceRecorder  # noqa: E402


GOAL = "if i want to get sample specific mi-RNA regulator network,what tools do i need?"
REPLIES = [
    "can you execute this workflow for me with the data that i have?",
    "Run LIONESS-PUMA using my existing workspace data. Discover compatible input files and prepare the workflow.",
]
pytestmark = pytest.mark.skipif(
    StateGraph is None, reason="Run in the project Docker environment."
)


@pytest.fixture
def runtime(tmp_path, request):
    policy = ProjectPolicyLoader(settings.PROJECT_ROOT).load()
    changes = {
        "PROJECT_ROOT": tmp_path,
        "SESSION_ROOT": tmp_path / "sessions",
        "TRACE_ROOT": tmp_path / "traces",
        "TOOL_LOG_ROOT": tmp_path / "tool_logs",
        "EXECUTE_TOOLS": False,
        # The conversation bundle below intentionally uses synthetic GeneA/TF1
        # labels so the test can isolate continuation and confirmation state.
        "TEST_DATA_MODE": True,
        "TRACE_ENABLED": False,
        "TRANSIENT_TRACE": False,
    }
    previous = {key: getattr(settings, key) for key in changes}
    request.addfinalizer(lambda: configure_runtime(**previous))
    configure_runtime(**changes)
    profile_store = UserProfileStore(tmp_path / "profiles")
    episode_store = EpisodeStore(tmp_path / "episodes")
    store = LocalTraceStore(tmp_path / "traces")
    recorder = TraceRecorder(store)
    hypothesis = OutcomeHypothesis(
        outcome=RequestedOutcome(
            operation="infer",
            artifact_type="regulatory_network",
            entity_types=["mirna", "gene"],
            regulator_types=["mirna"],
            target_types=["gene"],
            granularity="sample_specific",
            unresolved_dimensions=[],
        ),
        confidence=0.99,
        evidence=[
            OutcomeEvidence(
                dimension=dimension,
                value=value,
                source="inferred",
                rationale="The requested sample-specific miRNA network entails this dimension.",
            )
            for dimension, value in [
                ("operation", "infer"),
                ("artifact_type", "regulatory_network"),
                ("regulator_type", "mirna"),
                ("target_type", "gene"),
                ("granularity", "sample_specific"),
            ]
        ],
    )
    interpretation = SemanticInterpretation(
        request_mode="guidance",
        semantic_goal="sample-specific miRNA regulatory network",
        outcome_hypotheses=[hypothesis],
    )
    context = _GraphContext(
        profile_id="default",
        profile_store=profile_store,
        episode_store=episode_store,
        project_policy=policy,
        recorder=recorder,
        price_catalog=PriceCatalog.from_environment(),
        semantic_interpreter=Mock(invoke=Mock(return_value=interpretation)),
        semantic_reviewer=Mock(
            invoke=Mock(
                return_value=SemanticReview(
                    request_mode="guidance",
                    semantic_goal=interpretation.semantic_goal,
                    outcome_hypothesis=hypothesis,
                )
            )
        ),
        intent_router=Mock(
            invoke=Mock(
                return_value=IntentDecision(
                    mode="answer",
                    confidence=0.99,
                    reason="Workflow guidance requested.",
                )
            )
        ),
        input_content_mapper=None,
        response_llm=Mock(
            invoke=Mock(return_value=AIMessage(content="Workflow response."))
        ),
        semantic_model_name="fake",
        router_model_name="fake",
        response_model_name="fake",
        semantic_prompt="Interpret the request.",
        intent_prompt="Classify intent.",
        response_prompt="Explain validated facts.",
        router_max_tokens=1200,
        response_max_tokens=800,
        task_token_budget=20_000,
    )
    reply_model = Mock(
        invoke=Mock(
            return_value=ReplyIntentDecision(
                kind="accept_workflow",
                selected_action="run_lioness_puma",
                confidence=0.99,
                reason="The user requested the recommended workflow.",
            )
        )
    )
    results = []

    def invoke(app, invocation):
        result = app.invoke(invocation)
        results.append(result)
        return result

    cli = CliRuntime(
        memory=SimpleNamespace(
            profile_id="default",
            profile_store=profile_store,
            episode_store=episode_store,
        ),
        project_policy=policy,
        session_id="continuation-test",
        resume_id=None,
        conversation=[],
        pending_plan=None,
        active_usage=None,
        run_id=None,
        recorder=recorder,
        trace_store=store,
        ensure_trace_sync=lambda _: None,
        app=compile_graph(context),
        input_func=Mock(),
        invoke_graph_turn_func=invoke,
        reply_resolver=ContextualReplyResolver.for_test(reply_model),
    )
    return SimpleNamespace(
        cli=cli,
        context=context,
        results=results,
        root=tmp_path,
        reply_model=reply_model,
    )


def write_bundle(root, name="study-a"):
    directory = root / "data" / name
    directory.mkdir(parents=True)
    for name, content in {
        "expression.tsv": "GeneA\t1\t2\t3\nGeneB\t3\t2\t1\n",
        "prior-puma.tsv": "TF1\tGeneA\t1\nTF2\tGeneB\t1\nmiR-1\tGeneA\t1\n",
        "ppi.tsv": "TF1\tTF2\t1\nTF2\tTF1\t1\n",
        "mirna.txt": "miR-1\n",
    }.items():
        (directory / name).write_text(content)
    return directory


@pytest.mark.parametrize("reply", REPLIES)
def test_accepted_workflow_discovers_inputs_without_reclassifying(runtime, reply):
    directory = write_bundle(runtime.root)
    runtime.cli.input_func.side_effect = [GOAL, reply, "exit"]

    assert (
        run_conversation(SimpleNamespace(task=None, keep_session=False), runtime.cli)
        == 0
    )

    first, continued = runtime.results
    assert first["plan"]["status"] == "respond_only"
    assert continued["plan"]["workflow"] == "LIONESS-PUMA"
    assert continued["plan"]["status"] == "needs_confirmation"
    assert directory.as_posix() in continued["plan"]["question"]
    assert reply in continued["messages"][-2].content
    assert continued["tool_results"] == []
    assert settings.EXECUTE_TOOLS is False
    assert runtime.context.semantic_interpreter.invoke.call_count == 1
    assert runtime.context.intent_router.invoke.call_count == 1


def test_confirmed_inputs_reach_approved_preview_without_running_analysis(runtime):
    write_bundle(runtime.root)
    runtime.cli.input_func.side_effect = [GOAL, REPLIES[0], "/execute", "yes", "exit"]

    assert (
        run_conversation(SimpleNamespace(task=None, keep_session=False), runtime.cli)
        == 0
    )

    assert len(runtime.results) == 3
    preview = runtime.results[-1]
    assert preview["plan"]["workflow"] == "LIONESS-PUMA"
    assert preview["plan"]["status"] == "ready"
    assert preview["plan_evaluation"]["status"] == "approved"
    assert preview["tool_results"]
    assert [(item["action"], item["status"]) for item in preview["tool_results"]] == [
        ("inspect_inputs", "success"),
        ("run_lioness_puma", "dry_run"),
    ]
    decision = preview["plan"]["decision"]
    assert not (runtime.root / decision["output_file"]).exists()
    assert not (runtime.root / decision["lioness_output"]).exists()
    assert settings.EXECUTE_TOOLS is False
    assert runtime.context.semantic_interpreter.invoke.call_count == 1
    assert preview.get("workflow_continuation") is None


@pytest.mark.parametrize(
    "kind,reply",
    [
        ("follow_up", "What format should the motif prior use?"),
        ("needs_detail", "certainly"),
        ("new_goal", "Explain LIONESS-PUMA."),
    ],
)
def test_non_execution_reply_does_not_create_a_workflow_plan(runtime, kind, reply):
    write_bundle(runtime.root)
    runtime.reply_model.invoke.return_value = ReplyIntentDecision(
        kind=kind,
        confidence=0.99,
        reason="The user did not request workflow preparation.",
    )
    runtime.cli.input_func.side_effect = [GOAL, reply, "exit"]

    assert (
        run_conversation(SimpleNamespace(task=None, keep_session=False), runtime.cli)
        == 0
    )

    assert all(result["plan"]["status"] == "respond_only" for result in runtime.results)
    assert all(result["tool_results"] == [] for result in runtime.results)


def test_empty_workspace_asks_for_inputs_instead_of_repeating_guidance(runtime):
    runtime.cli.input_func.side_effect = [GOAL, REPLIES[0], "exit"]

    assert (
        run_conversation(SimpleNamespace(task=None, keep_session=False), runtime.cli)
        == 0
    )

    plan = runtime.results[-1]["plan"]
    assert plan["workflow"] == "LIONESS-PUMA"
    assert plan["status"] == "needs_input"
    assert set(plan["missing_inputs"]) == {
        "expression_file",
        "motif_file",
        "ppi_file",
        "mirna_file",
    }
    assert runtime.results[-1]["tool_results"] == []


@pytest.mark.parametrize(
    "continuation",
    [
        {"action": "run_lioness_puma", "task": "some previous task"},
        {"action": "web_search", "task": "Explain LIONESS-PUMA."},
        {
            "action": "run_lioness_puma",
            "task": "Explain LIONESS-PUMA.",
            "execute": True,
        },
    ],
)
def test_invalid_or_stale_continuation_fails_closed(runtime, continuation):
    run_id = runtime.cli.recorder.start_run(
        session_id="invalid-continuation", profile_id="default"
    )
    result = runtime.cli.app.invoke(
        {
            "messages": [HumanMessage(content="Explain LIONESS-PUMA.")],
            "workflow_continuation": continuation,
            "run_id": str(run_id),
        }
    )

    assert result["plan"]["status"] == "respond_only"
    assert result["plan"]["decision"]["action"] == "no_tool"
    assert result["tool_results"] == []
    assert result.get("workflow_continuation") is None


def test_explicit_paths_and_outputs_survive_the_accepted_reply(runtime):
    directory = write_bundle(runtime.root)
    reply = (
        "Run LIONESS-PUMA with "
        f"expression_file={directory}/expression.tsv "
        f"motif_file={directory}/prior-puma.tsv "
        f"ppi_file={directory}/ppi.tsv mirna_file={directory}/mirna.txt "
        "output_file=outputs/custom.tsv lioness_output=outputs/custom-samples.tsv"
    )
    runtime.cli.input_func.side_effect = [GOAL, reply, "exit"]

    assert (
        run_conversation(SimpleNamespace(task=None, keep_session=False), runtime.cli)
        == 0
    )

    result = runtime.results[-1]
    assert result["plan"]["status"] == "ready"
    decision = result["plan"]["decision"]
    assert decision["expression_file"] == f"{directory}/expression.tsv"
    assert decision["output_file"] == "outputs/custom.tsv"
    assert decision["lioness_output"] == "outputs/custom-samples.tsv"
    assert result["tool_results"][-1]["status"] == "dry_run"
    assert runtime.context.semantic_interpreter.invoke.call_count == 1


def test_bundle_selection_keeps_the_workflow_and_does_not_mix_datasets(runtime):
    write_bundle(runtime.root)
    write_bundle(runtime.root, "study-b")
    runtime.cli.input_func.side_effect = [GOAL, REPLIES[0], "1", "exit"]

    assert (
        run_conversation(SimpleNamespace(task=None, keep_session=False), runtime.cli)
        == 0
    )

    choice, selected = runtime.results[1:]
    assert choice["plan"]["status"] == "needs_input"
    options = choice["plan"]["input_bundle_options"]
    assert len(options) == 2
    assert selected["plan"]["workflow"] == "LIONESS-PUMA"
    assert selected["plan"]["status"] == "ready"
    for field, path in options[0]["inputs"].items():
        assert selected["plan"]["decision"][field] == path
    assert selected["tool_results"][-1]["status"] == "dry_run"
    assert runtime.context.semantic_interpreter.invoke.call_count == 1


def test_new_task_after_preview_does_not_inherit_the_selected_workflow(runtime):
    write_bundle(runtime.root)
    runtime.cli.input_func.side_effect = [GOAL, REPLIES[0], "yes", "back", GOAL, "exit"]

    assert (
        run_conversation(SimpleNamespace(task=None, keep_session=False), runtime.cli)
        == 0
    )

    assert runtime.results[2]["plan"]["status"] == "ready"
    assert runtime.results[3]["plan"]["status"] == "respond_only"
    assert runtime.results[3]["tool_results"] == []
    assert settings.EXECUTE_TOOLS is False


def test_text_marker_alone_does_not_supply_a_trusted_continuation(runtime):
    runtime.cli.input_func.side_effect = [
        "PREVIOUS_ACTION=run_lioness_puma. Continue the recommended LIONESS-PUMA workflow.",
        "exit",
    ]

    assert (
        run_conversation(SimpleNamespace(task=None, keep_session=False), runtime.cli)
        == 0
    )

    assert runtime.results[0]["plan"]["status"] == "respond_only"
    assert runtime.results[0]["tool_results"] == []


def test_reply_cannot_select_a_workflow_outside_the_offered_candidates(runtime):
    runtime.reply_model.invoke.return_value = ReplyIntentDecision(
        kind="accept_workflow",
        selected_action="run_panda",
        confidence=0.99,
        reason="An untrusted workflow selection must be rejected.",
    )
    runtime.cli.input_func.side_effect = [GOAL, REPLIES[0], "exit"]

    assert (
        run_conversation(SimpleNamespace(task=None, keep_session=False), runtime.cli)
        == 0
    )

    assert len(runtime.results) == 1
    assert runtime.results[0]["plan"]["status"] == "respond_only"
