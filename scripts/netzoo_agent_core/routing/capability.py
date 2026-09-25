"""Deterministic task interpretation and execution authorization."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from workflow_registry import (
    ActionName,
    LOCAL_WORKFLOW_ACTIONS,
    REQUIRED_INPUTS,
)

from ..contracts import TaskDecision

__all__ = [
    "MIN_TOOL_CONFIDENCE",
    "CONTEXT7_LIBRARY_ALIASES",
    "UNSUPPORTED_DELIVERABLE_PATTERNS",
    "WORKFLOW_INFORMATION_PATTERNS",
    "is_workflow_information_request",
    "is_workflow_selection_request",
    "infer_goal_capabilities",
    "infer_advisory_capabilities",
    "inferred_execution_action",
    "has_direct_execution_intent",
    "has_explicit_execution_request",
    "has_direct_retrieval_request",
    "is_input_preflight_request",
    "apply_input_preflight_intent",
    "reconcile_request_mode",
    "validate_task_text",
    "normalize_context7_library",
    "enforce_capability_gate",
]


MIN_TOOL_CONFIDENCE = 0.80


@dataclass(frozen=True)
class _GoalCapabilityMatch:
    """A recognized goal's registered actions and their semantic relationship."""

    actions: list[str]
    relationship: Literal["single", "composition", "alternatives"]


CONTEXT7_LIBRARY_ALIASES = {
    "context7": "context7",
    "langchain": "langchain",
    "langgraph": "langgraph",
    "netzoo": "netZooPy",
    "netzoopy": "netZooPy",
    "openrouter": "openrouter",
    "panda": "netZooPy",
    "pandas": "pandas",
    "puma": "netZooPy",
    "pydantic": "pydantic",
}


UNSUPPORTED_DELIVERABLE_PATTERNS = (
    r"(找|尋找|偵測|檢測|辨識|identify|find|detect|call).{0,24}"
    r"(突變|變異|mutation|variant)",
    r"(突變|變異|mutation|variant).{0,24}"
    r"(找|尋找|偵測|檢測|辨識|identify|find|detect|call)",
    r"(sequence alignment|序列比對|differential expression|差異表現"
    r"|enrichment analysis|富集分析|protein structure|蛋白質結構)",
)


WORKFLOW_INFORMATION_PATTERNS = (
    r"\bif\s+i\s+(?:ask|want|wanted|need|were)\b.*\b(?:run|execute|use|do)\b",
    r"\bwhat\s+(?:input|inputs|file|files|data|parameter|parameters|argument|arguments)\s+"
    r"(?:do|should|must|would|will|can)\s+i\s+(?:need|provide|prepare|give|pass|use)\b",
    r"\bwhat\s+(?:input|inputs|file|files|data|parameter|parameters|argument|arguments)\s+"
    r"(?:does|do)\s+.{0,40}\b(?:need|require|take|accept)\b",
    r"\b(?:what|which)\s+(?:input|inputs|file|files|data|parameter|parameters|argument|arguments)\s+"
    r"(?:is|are)\s+(?:required|needed|necessary)\b",
    r"\bwhat\s+(?:do|should|must|would|will|can)\s+i\s+"
    r"(?:need|provide|prepare|give|pass|use)\b",
    r"\b(?:which|what)\s+(?:input|inputs|file|files|data|parameter|parameters|argument|arguments)\b"
    r".*\b(?:need|required|provide|prepare|format)\b",
    r"\b(?:required|needed|necessary)\s+"
    r"(?:input|inputs|file|files|data|parameter|parameters|argument|arguments)\b",
    r"\binput\s+(?:requirements?|format|schema)\b",
    r"\bhow\s+(?:do|should|can)\s+i\s+(?:run|use|prepare|set\s*up)\b",
    r"\bbefore\s+(?:i\s+)?(?:run|execute|use)\b.*"
    r"\b(?:need|provide|prepare|required|input|format)\b",
    r"(?:如果|假如|若).*?(?:跑|執行|使用|做).*?(?:需要|提供|準備|input|輸入|資料|檔案)",
    r"(?:需要|要|應該).*?(?:提供|準備).*?(?:什麼|哪些|input|輸入|資料|檔案)",
    r"(?:需要哪些|要哪些|需要什麼|要什麼).*?(?:input|輸入|資料|檔案)",
    r"(?:input|輸入|資料|檔案).*?(?:格式|要求|需要哪些|要哪些|應該提供)",
    r"(?:input|輸入).*?(?:是什麼|有哪些)",
    r"怎麼.*?(?:跑|執行|測試|檢查|驗證|使用|準備)",
    r"(?:怎麼|如何).*?(?:做|建立|建構|產生|推論|執行|測試|檢查|驗證|完成)",
    r"\b(?:how|what|which)\b.{0,80}\b(?:run|execute|test|dry[- ]?run|inspect|validate|check)\b",
    r"\bhow\s+(?:do|should|can|would)\s+i\s+"
    r"(?:build|create|make|infer|generate|produce|perform|complete)\b",
)


WORKFLOW_SELECTION_PATTERNS = (
    r"\b(?:which|what)\s+(?:tools?|workflows?|methods?|pipelines?)\b",
    r"\b(?:what|which)\s+(?:tools?|workflows?|methods?)\b.{0,80}\b(?:need|use)\b",
    r"\b(?:what|which)\s+(?:tools?|workflows?|methods?)\b.{0,80}\b(?:should|can)\s+i\s+use\b",
    r"(?:需要|要|應該用).*?(?:哪些|什麼).{0,20}(?:工具|workflow|方法)",
    r"(?:哪些|什麼).{0,20}(?:工具|workflow|方法).*?(?:需要|要|應該用)",
)

_EXPLICIT_ADVICE_INTENT = re.compile(
    r"\b(?:advice|advise|recommend(?:ed|s|ing|ation|ations)?|"
    r"suggest(?:ed|s|ing|ion|ions)?)\b|建議|推薦|諮詢",
    re.I,
)


# This is intentionally workflow-independent.  It only recognizes an
# imperative request to perform work now; it must not select a workflow or
# interpret the scientific result.  Information questions are filtered first
# so phrases such as "how do I run" remain advisory.
EXPLICIT_EXECUTION_PATTERNS = (
    r"(?:^|[，,。！？!?;；\n])\s*(?:請|幫我|替我|我要|我想(?:要)?|please\s+)?"
    r"(?:直接\s*)?(?:執行|跑|試跑|測試|檢查|驗證|分析)\b",
    r"(?:^|[，,。！？!?;；\n])\s*(?:請|幫我|替我|我要|我想(?:要)?)?"
    r"(?:用|使用)[^，,。！？!?;；\n]{1,400}?(?:執行|跑|試跑|測試|檢查|驗證|分析)\b",
    r"(?:^|[,.!?;\n])\s*(?:(?:please|can you|could you)\s+|"
    r"i\s+(?:want|need)\s+to\s+)?(?:directly\s+)?"
    r"(?:run|execute|perform|test|dry[- ]?run|inspect|validate|check)\b",
)


# Input preflight is an inspection request, not a workflow contract question or
# an authorization to run an analysis.  Keep this deliberately narrow: a
# concrete input binding plus an explicit validation/preflight marker is
# required, so ordinary questions such as ``PANDA 需要哪些輸入？`` remain
# informational.
_INPUT_PREFLIGHT_MARKER_PATTERNS = (
    r"\binput\s+preflight\b",
    r"\bpreflight\b",
    r"(?:輸入|檔案|資料).{0,12}(?:預檢|檢查|驗證)",
    r"(?:預檢|檢查|驗證).{0,12}(?:輸入|檔案|資料)",
    r"(?:只|僅)\s*(?:回報|返回|報告).{0,16}(?:輸入|檔案|基因|gene).{0,16}(?:結果|驗證|檢查|authority)",
    r"(?:不要|勿|不直接)\s*(?:執行|跑).{0,20}(?:分析|workflow|panda|puma)",
    r"\b(?:gene\s+authority|authority\s+lookup)\b",
)
_INPUT_PREFLIGHT_BINDING_PATTERN = re.compile(
    r"\b(?:expression_file|motif_file|ppi_file)\s*(?:=|:|：)",
    flags=re.IGNORECASE,
)

_DIRECT_RETRIEVAL_ACTION_PATTERN = re.compile(
    r"\b(?:web[- ]?search|context7)\b", flags=re.IGNORECASE
)
_DIRECT_RETRIEVAL_QUERY_PATTERN = re.compile(
    r"(?:搜尋|查詢|查找|查網路|上網|search|lookup|look\s+up|query)",
    flags=re.IGNORECASE,
)


def is_input_preflight_request(task: str) -> bool:
    """Return whether *task* explicitly requests input-only validation.

    The marker and binding requirements are intentionally independent of the
    LLM's selected action.  This lets a deterministic boundary repair a
    ``no_tool``/workflow-contract classification without inferring a
    scientific outcome or silently treating a normal requirements question as
    executable work.
    """
    if not _INPUT_PREFLIGHT_BINDING_PATTERN.search(task):
        return False
    return any(
        re.search(pattern, task, flags=re.IGNORECASE | re.DOTALL)
        for pattern in _INPUT_PREFLIGHT_MARKER_PATTERNS
    )


def _explicit_taxon_binding(task: str) -> str | None:
    """Extract a simple ``taxon=Genus species`` binding for preflight only."""
    match = re.search(
        r"\btaxon\s*(?:=|:|：)\s*"
        r"(?P<taxon>[A-Za-z][A-Za-z0-9_-]*(?:\s+[A-Za-z][A-Za-z0-9_-]*){0,2})"
        r"(?=\s*(?:$|[^\x00-\x7F]|[\n,，;；。]|(?:expression_file|motif_file|ppi_file|output_file)\s*(?:=|:|：)))",
        task,
        flags=re.IGNORECASE,
    )
    return match.group("taxon").strip() if match else None


def apply_input_preflight_intent(task_decision: TaskDecision, task: str) -> TaskDecision:
    """Promote an explicit input-preflight request to ``inspect_inputs``.

    This is a deterministic intent repair only.  File parsing, schema checks,
    gene authority lookup, and execution authorization remain downstream
    planner/executor responsibilities.
    """
    if not is_input_preflight_request(task):
        return task_decision
    missing = [
        field_name
        for field_name in REQUIRED_INPUTS["inspect_inputs"]
        if not getattr(task_decision, field_name, None)
    ]
    updates = {
        "action": "inspect_inputs",
        "in_scope": True,
        "should_execute": True,
        "intent_type": "inspect_input",
        "confidence": max(task_decision.confidence, MIN_TOOL_CONFIDENCE),
        "reason": "The user explicitly requested input preflight without analysis execution.",
        "candidate_actions": ["inspect_inputs", "no_tool"],
        "recommended_actions": ["inspect_inputs"],
        "matched_actions": ["inspect_inputs"],
        "alternative_actions": [],
        "mismatch_dimensions": [],
        "capability_match_status": "exact",
        "clarification_question": None,
        "missing_inputs": missing,
    }
    if not task_decision.taxon:
        taxon = _explicit_taxon_binding(task)
        if taxon:
            updates["taxon"] = taxon
    return task_decision.model_copy(update=updates)


def is_workflow_information_request(task: str) -> bool:
    """Return True when the user asks how/what to prepare, not to run now."""
    normalized = task.casefold()
    return any(
        re.search(pattern, normalized, flags=re.IGNORECASE | re.DOTALL)
        for pattern in WORKFLOW_INFORMATION_PATTERNS
    )


def is_workflow_selection_request(task: str) -> bool:
    """Return True when the user asks which workflow to use, not how to run it."""
    return any(
        re.search(pattern, task, flags=re.IGNORECASE | re.DOTALL)
        for pattern in WORKFLOW_SELECTION_PATTERNS
    )


def has_explicit_advice_intent(task: str) -> bool:
    """Return True when the user explicitly asks for advice or a recommendation."""
    return _EXPLICIT_ADVICE_INTENT.search(task) is not None


def infer_goal_capability_match(task: str) -> _GoalCapabilityMatch:
    """Return no domain guess; semantic interpretation owns workflow selection."""
    del task
    return _GoalCapabilityMatch([], "single")


def infer_goal_capabilities(task: str) -> list[str]:
    """Map a domain goal to the existing local tools without requiring tool names."""
    return infer_goal_capability_match(task).actions


def infer_advisory_capabilities(task: str) -> list[str]:
    """Keep advisory routing fail-closed until semantic matching is available."""
    del task
    return []


def inferred_execution_action(task: str) -> str | None:
    """Return the end-to-end local action that best satisfies a recognized goal."""
    recommendations = infer_goal_capabilities(task)
    return recommendations[-1] if recommendations else None


def has_direct_execution_intent(task: str) -> bool:
    """Require an instruction to act; goals phrased as how-to questions stay advisory."""
    if is_workflow_information_request(task):
        return False
    if has_explicit_execution_request(task):
        return True
    return bool(
        re.search(
            r"((?:請|幫我|替我).{0,24}(?:建立|建構|產生|推論|執行|跑|試跑|測試|檢查|驗證|分析|做)|"
            r"\b(?:please\s+)?(?:build|create|generate|infer|run|execute|perform|test|dry[- ]?run|inspect|validate|check)\b)",
            task,
            flags=re.IGNORECASE | re.DOTALL,
        )
    )


def has_explicit_execution_request(task: str) -> bool:
    """Return whether the task explicitly asks the agent to perform work now.

    This narrow signal is separate from workflow matching.  It is used only to
    reconcile a model's request-mode reading when the user used an imperative
    execution phrase such as ``請試跑`` or ``please run``.
    """
    if is_workflow_information_request(task):
        return False
    return any(
        re.search(pattern, task, flags=re.IGNORECASE | re.DOTALL)
        for pattern in EXPLICIT_EXECUTION_PATTERNS
    )


def has_direct_retrieval_request(task: str) -> bool:
    """Recognize an imperative Websearch/Context7 request.

    Retrieval is a direct tool operation even when the request does not use a
    workflow verb such as ``run`` or ``execute``.  Informational questions are
    excluded so ``How do I use WEB-SEARCH?`` remains guidance-only.
    """
    return (
        not is_workflow_information_request(task)
        and bool(_DIRECT_RETRIEVAL_ACTION_PATTERN.search(task))
        and bool(_DIRECT_RETRIEVAL_QUERY_PATTERN.search(task))
    )


def reconcile_request_mode(task: str, request_mode: str) -> str:
    """Preserve explicit execution and classify workflow questions as guidance."""
    if request_mode != "execute" and (
        has_explicit_execution_request(task)
        or has_direct_retrieval_request(task)
    ):
        return "execute"
    if request_mode == "unknown" and (
        is_workflow_selection_request(task)
        or has_explicit_advice_intent(task)
    ):
        return "guidance"
    return request_mode


def validate_task_text(
    task: str,
    action: str,
    *,
    matched_actions: Sequence[ActionName] = (),
) -> str | None:
    """Return a rejection reason when user text cannot authorize the action."""
    normalized = task.casefold()
    for pattern in UNSUPPORTED_DELIVERABLE_PATTERNS:
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            return "The requested deliverable is not supported by the NetZoo agent."

    if action in LOCAL_WORKFLOW_ACTIONS and is_workflow_information_request(task):
        return (
            "The user is asking for workflow requirements or usage information, "
            "not authorizing local tool execution."
        )

    semantic_execution = (
        has_direct_execution_intent(task) and action in matched_actions
    )

    if action == "run_panda" and "panda" not in normalized and not semantic_execution:
        return "The task objective must specifically match PANDA before it can run."
    if action == "run_puma" and "puma" not in normalized and not semantic_execution:
        return "The task objective must specifically match PUMA before it can run."
    if (
        action == "run_lioness_panda"
        and not all(tool_name in normalized for tool_name in ("lioness", "panda"))
        and not semantic_execution
    ):
        return "The task objective must specifically match LIONESS-PANDA before it can run."
    if (
        action == "run_lioness_puma"
        and not all(tool_name in normalized for tool_name in ("lioness", "puma"))
        and not semantic_execution
    ):
        return (
            "The task objective must specifically match LIONESS-PUMA before it can run."
        )
    if (
        action == "run_lioness_coexpression"
        and (
            "lioness" not in normalized
            or not re.search(r"(co[- _]?expression|共表現|共同表現)", normalized)
        )
        and not semantic_execution
    ):
        return "The user must explicitly request LIONESS co-expression."
    if action == "run_condor":
        if "condor" not in normalized and not semantic_execution:
            return (
                "The task objective must specifically match CONDOR before it can run."
            )
        if not semantic_execution and not re.search(
            r"(run|execute|trial|test|試跑|執行|跑|分析|community|module|社群|模組)",
            normalized,
            flags=re.IGNORECASE,
        ):
            return "The user must explicitly request CONDOR execution or analysis."
    if action == "run_cobra" and "cobra" not in normalized and not semantic_execution:
        return "The user must explicitly request COBRA or covariate-aware co-expression analysis."
    if action == "run_sambar" and "sambar" not in normalized and not semantic_execution:
        return "The user must explicitly request SAMBAR or somatic-mutation pathway subtyping."
    if action == "run_dragon":
        if "dragon" not in normalized and not semantic_execution:
            return "The task objective must specifically match DRAGON before it can run."
        if not semantic_execution and not re.search(
            r"(run|execute|trial|test|試跑|執行|跑|分析|network|graphical model|partial correlation|multi.?omic|多組學|多體學)",
            normalized,
            flags=re.IGNORECASE,
        ):
            return "The user must explicitly request DRAGON execution or analysis."
    if action == "run_otter":
        if "otter" not in normalized and not semantic_execution:
            return "The task objective must specifically match OTTER before it can run."
        if not semantic_execution and not re.search(
            r"(run|execute|trial|test|試跑|執行|跑|分析|regulatory|relaxed.?graph|調控|推論)",
            normalized,
            flags=re.IGNORECASE,
        ):
            return "The user must explicitly request OTTER execution or analysis."
    if action == "run_giraffe":
        if "giraffe" not in normalized and not semantic_execution:
            return "The task objective must specifically match netZooPy GIRAFFE before it can run."
        if not semantic_execution and not re.search(
            r"(run|execute|trial|test|試跑|執行|跑|分析|regulatory|tfa|調控|推論)",
            normalized,
            flags=re.IGNORECASE,
        ):
            return "The user must explicitly request netZooPy GIRAFFE execution or analysis."
    if action == "run_bonobo":
        if "bonobo" not in normalized and not semantic_execution:
            return "The task objective must specifically match BONOBO before it can run."
        if not semantic_execution and not re.search(
            r"(run|execute|trial|test|試跑|執行|跑|分析|co.?expression|共表現|共同表現|sample.?specific|個體|樣本)",
            normalized,
            flags=re.IGNORECASE,
        ):
            return "The user must explicitly request BONOBO execution or sample-specific co-expression analysis."
    if action == "inspect_otter_inputs" and "otter" not in normalized:
        return "The user must explicitly name OTTER before inspecting its input."
    if action == "inspect_giraffe_inputs" and "giraffe" not in normalized:
        return "The user must explicitly name netZooPy GIRAFFE before inspecting its input."
    if action == "inspect_bonobo_inputs" and "bonobo" not in normalized:
        return "The user must explicitly name BONOBO before inspecting its input."
    if action == "inspect_condor_inputs" and "condor" not in normalized:
        return "The user must explicitly name CONDOR before inspecting its input."
    if action == "inspect_inputs" and not any(
        tool_name in normalized for tool_name in ("panda", "puma")
    ):
        return "The user must explicitly name PANDA or PUMA before inspecting inputs."
    if action == "convert_expression" and not re.search(
        r"(co[- _]?expression|correlation matrix|共表現|共同表現|相關矩陣)",
        normalized,
        flags=re.IGNORECASE,
    ):
        return "The user must explicitly request a co-expression or correlation matrix."
    if action == "format_expression" and not re.search(
        r"(format|reformat|transpose|整理|格式|轉置|row|column|列|欄)",
        normalized,
        flags=re.IGNORECASE,
    ):
        return (
            "The user must explicitly request expression formatting or reorientation."
        )
    if action == "web_search" and not re.search(
        r"(web|search|搜尋|查網路|上網|最新|目前|current|latest|literature|文獻)",
        normalized,
        flags=re.IGNORECASE,
    ):
        return "The user must explicitly request a search or current information."
    return None


def normalize_context7_library(library_name: str | None) -> str | None:
    """Map router output to an allow-listed project dependency."""
    if not library_name:
        return None
    normalized = library_name.casefold().replace("-", "").replace("_", "").strip()
    exact_match = CONTEXT7_LIBRARY_ALIASES.get(normalized)
    if exact_match:
        return exact_match

    # Structured-output models sometimes return labels such as
    # "netZooPy (PANDA/PUMA)" instead of the bare package name.
    for alias in (
        "context7",
        "langchain",
        "langgraph",
        "openrouter",
        "pydantic",
        "pandas",
        "netzoopy",
        "netzoo",
        "puma",
        "panda",
    ):
        if alias in normalized:
            return CONTEXT7_LIBRARY_ALIASES[alias]
    return None


def enforce_capability_gate(
    decision: TaskDecision, user_task: str | None = None
) -> TaskDecision:
    """Apply non-semantic safety checks to an LLM-owned routing selection."""
    if decision.action == "no_tool":
        decision.should_execute = False
        return decision

    if decision.action == "query_context7":
        decision.library_name = normalize_context7_library(decision.library_name)
        # Never let model-generated IDs bypass the library allow-list.
        decision.library_id = None
        if decision.library_name is None:
            return decision.model_copy(
                update={
                    "action": "no_tool",
                    "should_execute": False,
                    "clarification_question": (
                        "Which supported library should be used for the documentation lookup?"
                    ),
                }
            )

    missing = [
        field_name
        for field_name in REQUIRED_INPUTS[decision.action]
        if not getattr(decision, field_name)
    ]
    missing = sorted(set([*decision.missing_inputs, *missing]))

    # Action membership is schema-enforced. Missing fields are planner evidence,
    # not a reason to reinterpret the user's intent or change the selected tool.
    decision.missing_inputs = missing
    decision.should_execute = True
    return decision
