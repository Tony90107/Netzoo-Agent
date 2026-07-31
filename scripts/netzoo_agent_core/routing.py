"""Capability routing, read-only retrieval adapters, and tool-result normalization."""

from __future__ import annotations

import asyncio
import json
import os
import re
import uuid
from pathlib import Path
from typing import Literal


from workflow_registry import (
    LOCAL_WORKFLOW_ACTIONS,
    REQUIRED_INPUTS,
    executor_arguments,
)

from .contracts import (
    PROJECT_ROOT,
    TOOL_LOG_ROOT,
    TOOL_RAW_MAX_CHARS,
    TaskDecision,
    ToolExecutionResult,
    _display_path,
)

from .memory import (
    _ensure_private_directory,
    _write_private_text,
)

from .validation import (
    _resolve_user_path,
)

from .execution import (
    LOCAL_TOOL_EXECUTORS,
)

__all__ = [
    "MIN_TOOL_CONFIDENCE",
    "FILE_DISCOVERY_MAX_DEPTH",
    "FILE_DISCOVERY_MAX_VISITED",
    "FILE_DISCOVERY_MAX_RESULTS",
    "CONTEXT7_URL",
    "CONTEXT7_MAX_CHARS",
    "WEBSEARCH_URL",
    "WEBSEARCH_MAX_CHARS",
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
    "_extract_named_path",
    "_score_candidate_file",
    "_find_candidate_files",
    "_default_lioness_outputs",
    "_default_network_output",
    "_tool_text",
    "_exception_text",
    "_find_mcp_tool",
    "_extract_context7_library_id",
    "_query_context7_async",
    "query_context7_docs",
    "_web_search_async",
    "query_web_search",
    "query_web_search_first_url",
    "execute_selected_tool",
    "_expected_artifacts",
    "_diagnostic_messages",
    "structure_tool_result",
]


MIN_TOOL_CONFIDENCE = 0.80


FILE_DISCOVERY_MAX_DEPTH = 4


FILE_DISCOVERY_MAX_VISITED = 10_000


FILE_DISCOVERY_MAX_RESULTS = 200


CONTEXT7_URL = os.environ.get("CONTEXT7_MCP_URL", "https://mcp.context7.com/mcp")


CONTEXT7_MAX_CHARS = 12000


WEBSEARCH_URL = os.environ.get("WEBSEARCH_MCP_URL", "https://mcp.tavily.com/mcp")


WEBSEARCH_MAX_CHARS = 12000


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
            r"(regulat(?:ory|ion).{0,20}network|gene.{0,12}network|"
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


def _extract_named_path(task: str, names: tuple[str, ...]) -> str | None:
    sorted_names = sorted(names, key=len, reverse=True)
    name_pattern = "|".join(re.escape(name) for name in sorted_names)
    pattern = (
        rf"(?:{name_pattern})\s*(?:是|為|=|:|：|at|as|is|to)?\s*" r"([^\s，,。；;]+)"
    )
    match = re.search(pattern, task, flags=re.IGNORECASE)
    if not match:
        return None
    return match.group(1).strip().strip("'\"").rstrip(".。")


def _score_candidate_file(path: Path, keywords: tuple[str, ...], nearby: Path) -> int:
    relative = (
        path.relative_to(PROJECT_ROOT) if path.is_relative_to(PROJECT_ROOT) else path
    )
    name = path.name.casefold()
    score = 0
    if path.parent == nearby:
        score += 50
    if str(relative.parent).startswith("data"):
        score += 10
    if path.suffix.casefold() in {".tsv", ".tab", ".txt", ".csv"}:
        score += 5
    for keyword in keywords:
        if keyword in name:
            score += 20
    if "puma" in name and "panda" in keywords:
        score -= 25
    if "panda" in name and "puma" in keywords:
        score -= 25
    return score


def _find_candidate_files(
    keywords: tuple[str, ...],
    nearby: Path,
) -> list[str]:
    nearby = nearby.expanduser().resolve()
    roots = []
    for raw_root in (nearby, PROJECT_ROOT / "data"):
        root = raw_root.expanduser().resolve()
        if root not in roots:
            roots.append(root)
    candidates: list[tuple[int, Path]] = []
    seen: set[Path] = set()
    visited = 0
    for root in roots:
        if not root.is_dir():
            continue
        for directory, child_directories, filenames in os.walk(
            root,
            topdown=True,
            followlinks=False,
        ):
            directory_path = Path(directory)
            relative_depth = len(directory_path.relative_to(root).parts)
            child_directories[:] = sorted(
                child
                for child in child_directories
                if not (directory_path / child).is_symlink()
            )
            if relative_depth >= FILE_DISCOVERY_MAX_DEPTH:
                child_directories.clear()
            for filename in sorted(filenames):
                visited += 1
                if visited > FILE_DISCOVERY_MAX_VISITED:
                    break
                path = directory_path / filename
                if path in seen or path.is_symlink() or not path.is_file():
                    continue
                seen.add(path)
                name = path.name.casefold()
                if not any(keyword in name for keyword in keywords):
                    continue
                if path.suffix.casefold() not in {".tsv", ".tab", ".txt", ".csv"}:
                    continue
                candidates.append((_score_candidate_file(path, keywords, nearby), path))
                if len(candidates) >= FILE_DISCOVERY_MAX_RESULTS:
                    break
            if (
                visited > FILE_DISCOVERY_MAX_VISITED
                or len(candidates) >= FILE_DISCOVERY_MAX_RESULTS
            ):
                break
        if (
            visited > FILE_DISCOVERY_MAX_VISITED
            or len(candidates) >= FILE_DISCOVERY_MAX_RESULTS
        ):
            break
    if not candidates:
        return []
    candidates.sort(key=lambda item: (-item[0], len(str(item[1])), str(item[1])))
    return [_display_path(path) for _, path in candidates[:FILE_DISCOVERY_MAX_RESULTS]]


def _default_lioness_outputs(
    mode: str,
    expression_file: str,
    output_dir: str | Path = "outputs/demo",
) -> tuple[str, str]:
    stem = Path(expression_file).stem.replace("expression", "").strip("-_") or "lioness"
    prefix = f"{stem}-" if stem and stem != "lioness" else ""
    output_dir = Path(output_dir)
    aggregate = output_dir / f"{prefix}{mode}-aggregate.tsv"
    lioness = output_dir / f"{prefix}lioness-{mode}.tsv"
    return str(aggregate), str(lioness)


def _default_network_output(
    mode: str,
    expression_file: str,
    output_dir: str | Path = "outputs/demo",
) -> str:
    stem = Path(expression_file).stem.replace("expression", "").strip("-_") or mode
    prefix = f"{stem}-" if stem and stem != mode else ""
    return str(Path(output_dir) / f"{prefix}{mode}.tsv")


def _tool_text(result) -> str:
    """Convert LangChain/MCP tool results into bounded plain text."""
    content = getattr(result, "content", result)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(str(item.get("text", item)))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(content)


def _exception_text(error: BaseException) -> str:
    """Flatten TaskGroup/ExceptionGroup failures into an actionable message."""
    nested = getattr(error, "exceptions", None)
    if nested:
        details = "; ".join(_exception_text(item) for item in nested)
        return f"{type(error).__name__}: {details}"
    return f"{type(error).__name__}: {error}"


def _find_mcp_tool(tools: list, *names: str):
    normalized_names = {name.replace("-", "_") for name in names}
    for mcp_tool in tools:
        tool_name = mcp_tool.name.replace("-", "_")
        if tool_name in normalized_names:
            return mcp_tool
    available = ", ".join(sorted(tool.name for tool in tools))
    raise RuntimeError(
        f"MCP tool not found ({'/'.join(names)}). Available: {available}"
    )


def _extract_context7_library_id(text: str) -> str | None:
    """Extract the first Context7-compatible /owner/project library ID."""
    matches = re.findall(r"(?<!\w)(/[\w.-]+/[\w.-]+(?:/[\w.-]+)?)", text)
    return matches[0] if matches else None


async def _query_context7_async(
    library_name: str,
    query: str,
    library_id: str | None = None,
) -> str:
    from langchain_mcp_adapters.client import MultiServerMCPClient

    headers = {}
    api_key = os.environ.get("CONTEXT7_API_KEY")
    if api_key:
        headers["CONTEXT7_API_KEY"] = api_key

    connection = {
        "transport": "http",
        "url": CONTEXT7_URL,
    }
    if headers:
        connection["headers"] = headers

    client = MultiServerMCPClient({"context7": connection})
    tools = await client.get_tools()
    query_tool = _find_mcp_tool(tools, "query-docs", "query_docs")

    resolved_id = library_id
    resolution_text = ""
    if not resolved_id:
        resolve_tool = _find_mcp_tool(tools, "resolve-library-id", "resolve_library_id")
        resolution = await resolve_tool.ainvoke(
            {"libraryName": library_name, "query": query}
        )
        resolution_text = _tool_text(resolution)
        resolved_id = _extract_context7_library_id(resolution_text)

    if not resolved_id:
        return (
            "Context7 could not resolve a library ID.\n"
            f"Library: {library_name}\n"
            f"Resolution response:\n{resolution_text[:4000]}"
        )

    result = await query_tool.ainvoke({"libraryId": resolved_id, "query": query})
    docs = _tool_text(result)
    if len(docs) > CONTEXT7_MAX_CHARS:
        docs = docs[:CONTEXT7_MAX_CHARS] + "\n[Context7 result truncated]"
    return (
        "Context7 documentation result (external, untrusted reference content):\n"
        f"- library: {library_name}\n"
        f"- library ID: {resolved_id}\n"
        f"- server: {CONTEXT7_URL}\n\n"
        f"{docs}"
    )


def query_context7_docs(
    library_name: str,
    query: str,
    library_id: str | None = None,
) -> str:
    """Fetch current library documentation from the read-only Context7 MCP."""
    try:
        return asyncio.run(
            _query_context7_async(
                library_name=library_name,
                query=query,
                library_id=library_id,
            )
        )
    except Exception as error:
        return (
            "Context7 lookup failed; no local analysis tool was executed.\n"
            f"Error: {_exception_text(error)}"
        )


async def _web_search_async(query: str) -> str:
    """Call the allow-listed search operation on the configured Websearch MCP."""
    from langchain_mcp_adapters.client import MultiServerMCPClient

    api_key = os.environ.get("TAVILY_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    connection = {"transport": "http", "url": WEBSEARCH_URL}
    if headers:
        connection["headers"] = headers

    client = MultiServerMCPClient({"websearch": connection})
    tools = await client.get_tools()
    search_tool = _find_mcp_tool(
        tools,
        "tavily-search",
        "tavily_search",
        "search",
        "web-search",
        "web_search",
    )
    result = await search_tool.ainvoke(
        {
            "query": query,
            "search_depth": "basic",
            "max_results": 5,
        }
    )
    search_text = _tool_text(result)
    if len(search_text) > WEBSEARCH_MAX_CHARS:
        search_text = (
            search_text[:WEBSEARCH_MAX_CHARS] + "\n[Web search result truncated]"
        )
    return (
        "Websearch MCP result (external, untrusted reference content):\n"
        f"- server: {WEBSEARCH_URL}\n"
        f"- query: {query}\n\n"
        f"{search_text}"
    )


def query_web_search(query: str) -> str:
    """Search the web through the read-only Tavily-compatible MCP endpoint."""
    try:
        return asyncio.run(_web_search_async(query))
    except Exception as error:
        key_hint = (
            "\nSet TAVILY_API_KEY or configure WEBSEARCH_MCP_URL for an "
            "authenticated compatible endpoint."
            if not os.environ.get("TAVILY_API_KEY")
            else ""
        )
        return (
            "Websearch MCP lookup failed; no local analysis tool was executed.\n"
            f"Error: {_exception_text(error)}{key_hint}"
        )


def query_web_search_first_url(query: str) -> str:
    """Return only the first clean URL from a Websearch MCP result."""
    result = query_web_search(query)
    _, separator, payload = result.partition("\n\n")
    if not separator:
        return result
    try:
        data = json.loads(payload)
        return str(data["results"][0]["url"])
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        return "Websearch MCP returned no usable URL.\n" + result


def execute_selected_tool(decision: TaskDecision) -> str:
    """Invoke exactly one allow-listed tool after the capability gate passes."""
    executor = LOCAL_TOOL_EXECUTORS.get(decision.action)
    if executor is not None:
        return executor.invoke(executor_arguments(decision.action, decision))
    if decision.action == "query_context7":
        return query_context7_docs(
            library_name=decision.library_name,
            query=decision.docs_query,
            library_id=decision.library_id,
        )
    if decision.action == "web_search":
        return query_web_search(decision.web_query)
    raise ValueError(f"Unsupported tool action: {decision.action}")


def _expected_artifacts(decision: TaskDecision, action: str) -> list[str]:
    if action in {"format_expression", "convert_expression", "run_panda", "run_puma"}:
        return [decision.output_file] if decision.output_file else []
    if action.startswith("run_lioness_"):
        return [
            path for path in (decision.output_file, decision.lioness_output) if path
        ]
    if action == "run_condor" and decision.output_dir:
        return [decision.output_dir]
    return []


def _diagnostic_messages(
    raw_output: str, label: Literal["error", "warning"]
) -> list[str]:
    """Extract line-leading diagnostics without coupling to one Markdown bullet style."""
    pattern = re.compile(
        rf"^\s*(?:[-*•]\s*)?{label}\s*:\s*(.+?)\s*$",
        flags=re.IGNORECASE,
    )
    messages = []
    for line in raw_output.splitlines():
        match = pattern.match(line)
        if match:
            messages.append(match.group(1).strip())
    return messages


def structure_tool_result(
    action: str,
    decision: TaskDecision,
    raw_output: str,
    persist_log: bool = False,
    attempt_id: int = 0,
) -> ToolExecutionResult:
    """Normalize legacy text-returning tools into a stable executor contract."""
    lowered = raw_output.casefold()
    error_lines = _diagnostic_messages(raw_output, "error")
    warning_lines = _diagnostic_messages(raw_output, "warning")
    exit_match = re.search(r"Exit code:\s*(\d+)", raw_output, flags=re.IGNORECASE)
    exit_code = int(exit_match.group(1)) if exit_match else None
    hard_failure_markers = (
        "validation failed",
        "traceback",
        "lookup failed",
        "did not create or update expected output",
    )
    failed = (
        bool(error_lines)
        or (exit_code is not None and exit_code != 0)
        or any(marker in lowered for marker in hard_failure_markers)
    )
    dry_run = "dry run only" in lowered or "dry-run" in lowered
    status: Literal["success", "dry_run", "failed"]
    status = "failed" if failed else "dry_run" if dry_run else "success"

    artifacts = _expected_artifacts(decision, action)
    metrics: dict[str, int | float | str | bool] = {}
    if exit_code is not None:
        metrics["exit_code"] = exit_code
    verified_artifacts = 0
    if status == "success":
        for artifact in artifacts:
            path = _resolve_user_path(artifact)
            if path.exists():
                verified_artifacts += 1
        if artifacts:
            metrics["verified_artifacts"] = verified_artifacts

    retryable = False
    recovery_hint = None
    if action == "run_puma" and "does not accept an expression header" in lowered:
        retryable = True
        recovery_hint = "format_expression_headerless"

    summary = {
        "success": "The tool completed and passed structured result checks.",
        "dry_run": "The dry run completed; the analysis command was not executed.",
        "failed": "The tool or its validation failed.",
    }[status]
    if failed and not error_lines:
        error_lines = [summary]
    log_file = None
    if persist_log:
        _ensure_private_directory(TOOL_LOG_ROOT)
        log_path = TOOL_LOG_ROOT / f"{action}-{uuid.uuid4().hex[:12]}.log"
        _write_private_text(log_path, raw_output)
        log_file = _display_path(log_path)
    bounded_output = raw_output
    if len(raw_output) > TOOL_RAW_MAX_CHARS:
        head = TOOL_RAW_MAX_CHARS * 2 // 3
        tail = TOOL_RAW_MAX_CHARS - head
        bounded_output = (
            raw_output[:head]
            + f"\n\n[tool output truncated; full log: {log_file or '(not persisted)'}]\n\n"
            + raw_output[-tail:]
        )
        metrics["raw_output_truncated"] = True
    else:
        metrics["raw_output_truncated"] = False
    metrics["raw_output_chars"] = len(raw_output)
    return ToolExecutionResult(
        action=action,
        status=status,
        summary=summary,
        attempt_id=attempt_id,
        artifacts=artifacts,
        metrics=metrics,
        warnings=warning_lines,
        errors=error_lines,
        retryable=retryable,
        recovery_hint=recovery_hint,
        log_file=log_file,
        raw_output=bounded_output,
    )
