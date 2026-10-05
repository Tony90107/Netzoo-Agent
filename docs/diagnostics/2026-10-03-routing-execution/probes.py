"""Offline diagnostic witnesses, not model-accuracy or scientific execution tests.

Run from the repository: python docs/diagnostics/2026-10-03-routing-execution/probes.py
Only this directory receives JSON output. LLM calls, scientific API and writes
are stubbed where explicitly stated below. No search or real analysis is run.
"""
from pathlib import Path
import hashlib
import json
import sys
import time
from types import SimpleNamespace
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "tests")]

from netzoo_agent_core import execution, settings
from netzoo_agent_core.contracts import HumanMessage, IntentDecision, LLMUsage, TaskDecision
from netzoo_agent_core.contracts.outcomes import SemanticInterpretation
from netzoo_agent_core.evaluation import evaluate_workflow_plan
from netzoo_agent_core.graph import router_invocation, semantic_attempts
from netzoo_agent_core.interpretation.outcome_validation import validate_outcome_hypotheses
from netzoo_agent_core.interpretation.hydration import hydrate_router_decision
from netzoo_agent_core.llm import latest_user_task
from netzoo_agent_core.planning import build_workflow_plan
from netzoo_agent_core.policy import ProjectPolicyLoader
from netzoo_agent_core.pricing import PriceCatalog
from netzoo_agent_core.routing.capability import (
    apply_input_preflight_intent, has_direct_execution_intent,
    has_explicit_execution_request, reconcile_request_mode,
)
from netzoo_agent_core.routing.results import structure_tool_result
from netzoo_agent_core.tracing import NullTraceRecorder
from test_routing_evaluation import TASK, hypothesis


def main():
    observations = {}
    policy = ProjectPolicyLoader(ROOT).load()
    ctx = SimpleNamespace(project_policy=policy, recorder=NullTraceRecorder(),
                          task_token_budget=30000, selection_condition_llm=None)
    interpretation = SemanticInterpretation.model_validate({
        "request_mode": "guidance", "semantic_goal": "Cohort grouping",
        "outcome_hypotheses": [hypothesis()],
    })
    observations["F1_denied_retrieval"] = []
    for prefix in ("Do not use WEB-SEARCH to search for PANDA papers. ",
                   "不要用 WEB-SEARCH 搜尋 PANDA 文獻。 "):
        task = prefix + TASK
        validated = validate_outcome_hypotheses(task, interpretation.outcome_hypotheses, "guidance")
        assert validated.valid, validated.issues
        usage = LLMUsage(budget_tokens=30000)
        # Script the three model boundaries. Real deterministic routing,
        # assembly, hydration, planning and plan evaluation remain in use.
        with patch.object(router_invocation, "_invoke_semantic_interpreter", return_value=(
            interpretation, usage, [], None, frozenset()
        )), patch.object(router_invocation, "_invoke_semantic_discriminator", side_effect=(
            lambda c, s, t, i, m, u, w: (i, m, u, w)
        )), patch.object(router_invocation, "_invoke_intent_router", return_value=(
            IntentDecision(mode="answer", confidence=1, reason="Answer only; search is forbidden."),
            usage, [], False
        )):
            result = router_invocation.invoke_router(ctx, {}, task)
            plan = build_workflow_plan(result.decision, task, project_policy=policy)
            review = evaluate_workflow_plan(plan, task, policy)
        observations["F1_denied_retrieval"].append({
            "task": task, "semantic_evidence_valid": validated.valid,
            "scripted_intent": "answer", "action": result.decision.action,
            "should_execute": result.decision.should_execute,
            "plan_status": plan.status, "review_status": review.status,
        })

    observations["F2_preflight_promotion"] = []
    for task in (
        "Only explain input preflight; do not inspect anything. expression_file=demo.tsv",
        "不要執行分析，expression_file=demo.tsv，只要解釋 PANDA。",
    ):
        decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False,
                                confidence=1, reason="Explanation only")
        result = apply_input_preflight_intent(hydrate_router_decision(decision, task), task)
        observations["F2_preflight_promotion"].append({
            "task": task, "action": result.action, "should_execute": result.should_execute,
            "missing_inputs": result.missing_inputs,
        })

    task = "Do not execute anything; explain only.\n" + "x" * 6050 + "\nRun PANDA"
    clipped = latest_user_task([HumanMessage(content=task)])
    observations["F3_context_truncation"] = {
        "original_length": len(task), "routing_length": len(clipped),
        "prohibition_preserved": "Do not execute" in clipped,
        "reconciled_answer": reconcile_request_mode(clipped, "answer"),
    }

    decision = TaskDecision(action="web_search", in_scope=True, should_execute=True,
                            confidence=1, reason="Search", web_query="documentation")
    observations["F4_result_text"] = [
        {"raw": raw, "status": structure_tool_result("web_search", decision, raw).status}
        for raw in ("Search documentation: dry-run is supported.",
                    "The documentation explains how to debug a traceback.",
                    "Documentation was retrieved successfully.")
    ]

    # Replace numerical computation, validation and artifact writing. A bounded
    # 30ms API stub witnesses whether the configured 1ms deadline is applied.
    import numpy as np
    import pandas as pd
    frame = pd.DataFrame([[1., 2.], [2., 3.], [3., 5.]], columns=["A", "B"])

    def slow_api(*args):
        time.sleep(.03)
        return np.eye(4), None

    api = SimpleNamespace(get_precision_matrix_dragon=slow_api,
                          get_partial_correlation_dragon=lambda *args: np.eye(4))
    with patch.object(settings, "EXECUTE_TOOLS", True), \
         patch.object(settings, "TOOL_TIMEOUT_SECONDS", .001), \
         patch.object(execution, "inspect_dragon_inputs_impl", return_value=("valid", True)), \
         patch.object(execution, "load_and_align_dragon_layers", return_value=(frame, frame, [])), \
         patch.object(execution, "_load_dragon_api", return_value=api), \
         patch.object(execution, "write_dragon_matrix", return_value="mock-output.tsv"):
        started = time.monotonic()
        output = execution.run_dragon.invoke({
            "omics_layer_1": "mock-a.tsv", "omics_layer_2": "mock-b.tsv",
            "output_file": "mock-output.tsv", "lambda1": .1, "lambda2": .1,
        })
        observations["F5_api_timeout"] = {
            "configured_seconds": .001, "elapsed_seconds": round(time.monotonic() - started, 4),
            "completed": "API execution completed" in output,
        }

    recorder = Mock()
    semantic_ctx = SimpleNamespace(
        semantic_interpreter=Mock(invoke=Mock(return_value=interpretation.model_dump())),
        semantic_reviewer=Mock(), semantic_prompt="Interpret.", semantic_model_name="fake",
        router_max_tokens=1200, task_token_budget=30000, price_catalog=PriceCatalog.from_environment(),
        recorder=recorder, review_policy="always",
    )
    with patch.object(semantic_attempts, "preflight_budget", side_effect=[
        (SimpleNamespace(status="ok"), []), (SimpleNamespace(status="blocked"), []),
    ]):
        result = semantic_attempts.invoke_semantic_interpreter(
            semantic_ctx, {}, TASK, LLMUsage(budget_tokens=30000)
        )
    observations["F6_budget_loses_valid_first_pass"] = {
        "review_policy": "always", "interpretation_preserved": result[0] is not None,
        "budget_exhausted": result[1].budget_exhausted,
        "calls": [{"role": c.role, "status": c.status} for c in result[1].calls],
        "review_calls": semantic_ctx.semantic_reviewer.invoke.call_count,
        "events": [{"type": c.args[1], "payload": c.args[3]} for c in recorder.append.call_args_list],
    }

    observations["F7_cjk_boundary"] = [
        {"task": task, "explicit": has_explicit_execution_request(task),
         "direct": has_direct_execution_intent(task),
         "reconciled_answer": reconcile_request_mode(task, "answer")}
        for task in ("請執行PANDA", "請執行 PANDA")
    ]
    observed_files = [
        "scripts/netzoo_agent_core/graph/router_invocation.py",
        "scripts/netzoo_agent_core/graph/semantic_attempts.py",
        "scripts/netzoo_agent_core/routing/capability.py",
        "scripts/netzoo_agent_core/routing/results.py",
        "scripts/netzoo_agent_core/llm.py",
        "scripts/netzoo_agent_core/execution.py",
        "scripts/netzoo_agent_core/evaluation/plan_review.py",
    ]
    observations["source_sha256"] = {
        p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in observed_files
    }
    target = Path(__file__).with_name("observations.json")
    target.write_text(json.dumps(observations, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(observations, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
