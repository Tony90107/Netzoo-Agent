"""Deterministic task interpretation and execution authorization."""

from __future__ import annotations

import re

from workflow_registry import LOCAL_WORKFLOW_ACTIONS, REQUIRED_INPUTS

from ..contracts import TaskDecision

__all__ = [
    "MIN_TOOL_CONFIDENCE",
    "CONTEXT7_LIBRARY_ALIASES",
    "UNSUPPORTED_DELIVERABLE_PATTERNS",
    "WORKFLOW_INFORMATION_PATTERNS",
    "is_workflow_information_request",
    "infer_goal_capabilities",
    "infer_advisory_capabilities",
    "inferred_execution_action",
    "has_direct_execution_intent",
    "validate_task_text",
    "normalize_context7_library",
    "enforce_capability_gate",
]


MIN_TOOL_CONFIDENCE = 0.80


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
    r"怎麼.*?(?:跑|執行|使用|準備)",
    r"(?:怎麼|如何).*?(?:做|建立|建構|產生|推論|完成)",
    r"\bhow\s+(?:do|should|can|would)\s+i\s+"
    r"(?:build|create|make|infer|generate|produce|perform|complete)\b",
)


def is_workflow_information_request(task: str) -> bool:
    """Return True when the user asks how/what to prepare, not to run now."""
    normalized = task.casefold()
    return any(
        re.search(pattern, normalized, flags=re.IGNORECASE | re.DOTALL)
        for pattern in WORKFLOW_INFORMATION_PATTERNS
    )


def infer_goal_capabilities(task: str) -> list[str]:
    """Map a domain goal to the existing local tools without requiring tool names."""
    normalized = task.casefold()
    sample_specific = bool(
        re.search(
            r"(sample[\s_-]*(?:specific|spefic|specfic)|per[\s_-]*sample|"
            r"individual[\s_-]*specific|樣本(?:特異|特定)|個體(?:特異|特定|化))",
            normalized,
            flags=re.IGNORECASE,
        )
    )
    mirna = bool(
        re.search(
            r"(mi[\s_-]*rna|mirna|micro[\s_-]*rna|微小\s*rna)",
            normalized,
            flags=re.IGNORECASE,
        )
    )
    coexpression = bool(
        re.search(
            r"(co[\s_-]*expression|correlation\s+(?:network|matrix)|共表現|共同表現)",
            normalized,
            flags=re.IGNORECASE,
        )
    )
    regulatory_network = bool(
        re.search(
            r"(regulat(?:ory|ion|or).{0,20}network|gene.{0,12}network|"
            r"調控.{0,8}網路|基因.{0,8}網路|network\s+inference)",
            normalized,
            flags=re.IGNORECASE,
        )
    )
    tf = bool(
        re.search(
            r"(transcription\s+factor|\btf(?:s)?\b|轉錄因子)",
            normalized,
            flags=re.IGNORECASE,
        )
    )
    bipartite = bool(re.search(r"(bipartite|二分|雙部)", normalized))
    communities = bool(re.search(r"(communit(?:y|ies)|modules?|社群|模組)", normalized))

    # Recommendations describe the conceptual composition. The final item is the
    # end-to-end execution action selected when the user asks the agent to do it.
    if sample_specific and mirna and regulatory_network:
        return ["run_puma", "run_lioness_puma"]
    if mirna and regulatory_network:
        return ["run_puma"]
    if sample_specific and tf and regulatory_network:
        return ["run_panda", "run_lioness_panda"]
    if sample_specific and regulatory_network:
        return ["run_lioness_panda", "run_lioness_puma"]
    if tf and regulatory_network:
        return ["run_panda"]
    if sample_specific and coexpression:
        return ["run_lioness_coexpression"]
    if bipartite and communities:
        return ["run_condor"]
    return []


def infer_advisory_capabilities(task: str) -> list[str]:
    """Recommend a workflow for guidance questions without authorizing execution."""
    recommendations = infer_goal_capabilities(task)
    if recommendations:
        return recommendations
    normalized = task.casefold()
    if re.search(
        r"(sample[\s_-]*(?:specific|spefic|specfic)|per[\s_-]*sample).{0,40}"
        r"(mi[\s_-]*rna|mirna|micro[\s_-]*rna)",
        normalized,
        flags=re.IGNORECASE,
    ):
        return ["run_puma", "run_lioness_puma"]
    return []


def inferred_execution_action(task: str) -> str | None:
    """Return the end-to-end local action that best satisfies a recognized goal."""
    recommendations = infer_goal_capabilities(task)
    return recommendations[-1] if recommendations else None


def has_direct_execution_intent(task: str) -> bool:
    """Require an instruction to act; goals phrased as how-to questions stay advisory."""
    if is_workflow_information_request(task):
        return False
    return bool(
        re.search(
            r"((?:請|幫我|替我).{0,24}(?:建立|建構|產生|推論|執行|跑|分析|做)|"
            r"\b(?:please\s+)?(?:build|create|generate|infer|run|execute|perform)\b)",
            task,
            flags=re.IGNORECASE | re.DOTALL,
        )
    )


def validate_task_text(task: str, action: str) -> str | None:
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

    inferred_action = inferred_execution_action(task)
    semantic_execution = has_direct_execution_intent(task) and inferred_action == action

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
    """Convert uncertain, unsupported, or incomplete decisions into no_tool."""
    if user_task and not decision.recommended_actions:
        decision.recommended_actions = infer_goal_capabilities(user_task)
    if decision.action == "no_tool":
        decision.should_execute = False
        return decision

    if decision.action == "query_context7":
        decision.library_name = normalize_context7_library(decision.library_name)
        # Never let model-generated IDs bypass the library allow-list.
        decision.library_id = None

    missing = [
        field_name
        for field_name in REQUIRED_INPUTS[decision.action]
        if not getattr(decision, field_name)
    ]
    missing = sorted(set([*decision.missing_inputs, *missing]))

    rejection_reasons = []
    if user_task:
        task_rejection = validate_task_text(user_task, decision.action)
        if task_rejection:
            rejection_reasons.append(task_rejection)
    if (
        decision.action in LOCAL_WORKFLOW_ACTIONS
        and decision.intent_type == "answer_question"
    ):
        rejection_reasons.append(
            "The request was classified as an information question, not an execution request."
        )
    if not decision.in_scope:
        rejection_reasons.append(
            "The task is outside the NetZoo agent capability scope."
        )
    if not decision.should_execute:
        rejection_reasons.append("No tool execution is required for this request.")
    if decision.confidence < MIN_TOOL_CONFIDENCE:
        rejection_reasons.append(
            f"Tool-selection confidence is too low ({decision.confidence:.2f} < {MIN_TOOL_CONFIDENCE:.2f})."
        )
    if missing:
        rejection_reasons.append("Missing required inputs: " + ", ".join(missing))

    if rejection_reasons:
        return TaskDecision(
            action="no_tool",
            in_scope=decision.in_scope,
            should_execute=False,
            confidence=decision.confidence,
            reason="；".join(rejection_reasons),
            recommended_actions=decision.recommended_actions,
            missing_inputs=missing,
        )
    return decision
