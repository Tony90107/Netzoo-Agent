"""Deep modules implementing the NetZoo planner/executor/evaluator harness.

Most callers should use the stable orchestration seams exported here.  The historical
``scripts/netzoo_agent.py`` module remains a compatibility facade for existing imports
and the command line.
"""

from .contracts import (
    ArtifactValidationResult,
    EvaluationResult,
    InputEvidence,
    PlanEvaluationResult,
    TaskDecision,
    ToolExecutionResult,
    WorkflowPlan,
    WorkflowStep,
)
from .artifact_validation import ARTIFACT_WRITE_ACTIONS, validate_output_artifacts
from .compatibility import TOOLS, explain_panda_puma_io
from .bundles import BundleDiscovery, discover_coherent_bundle
from .evaluation import evaluate_step_result, evaluate_workflow_plan
from .graph import build_graph, invoke_graph_turn
from .outcomes import (
    effective_results,
    supersede_triggering_failure,
    terminal_failed,
)
from .planning import build_workflow_plan
from .path_safety import (
    condor_artifact_paths,
    resolved_output_collisions,
    validate_output_basename,
)
from .trace_contracts import TraceEvent
from .trace_store import LocalTraceStore, TraceIntegrityError
from .tracing import NullTraceRecorder, TraceRecorder
from .pricing import PriceCatalog

__all__ = [
    "ARTIFACT_WRITE_ACTIONS",
    "ArtifactValidationResult",
    "EvaluationResult",
    "BundleDiscovery",
    "InputEvidence",
    "PlanEvaluationResult",
    "TaskDecision",
    "TOOLS",
    "ToolExecutionResult",
    "WorkflowPlan",
    "WorkflowStep",
    "build_graph",
    "build_workflow_plan",
    "condor_artifact_paths",
    "discover_coherent_bundle",
    "evaluate_step_result",
    "evaluate_workflow_plan",
    "effective_results",
    "explain_panda_puma_io",
    "invoke_graph_turn",
    "resolved_output_collisions",
    "supersede_triggering_failure",
    "terminal_failed",
    "validate_output_basename",
    "validate_output_artifacts",
    "LocalTraceStore",
    "NullTraceRecorder",
    "PriceCatalog",
    "TraceEvent",
    "TraceIntegrityError",
    "TraceRecorder",
]
