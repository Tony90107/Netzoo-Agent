"""Deterministic task hydration, file discovery, and demo-bundle selection."""

from __future__ import annotations

import json
import re
from pathlib import Path


from workflow_registry import (
    LOCAL_WORKFLOW_ACTIONS,
    REQUIRED_INPUTS,
    workflow_name as _workflow_name,
)

from .contracts import (
    Episode,
    InputEvidence,
    LIONESS_MODE_QUESTION,
    PROJECT_ROOT,
    PreferenceProposal,
    RouterDecision,
    TaskDecision,
    WorkflowPlan,
    _display_path,
    _is_demo_request,
    _ui_text,
)

from .validation import (
    _inspect_panda_inputs_impl,
    _resolve_user_path,
)

from .execution import (
    _expression_sample_count,
    _inspect_condor_inputs_impl,
)

from .routing import (
    CONTEXT7_LIBRARY_ALIASES,
    MIN_TOOL_CONFIDENCE,
    _extract_named_path,
    _score_candidate_file,
    has_direct_execution_intent,
    infer_advisory_capabilities,
    infer_goal_capabilities,
    inferred_execution_action,
    is_workflow_information_request,
    validate_task_text,
)

__all__ = [
    "INPUT_LABELS",
    "_candidate_keywords",
    "_choose_unambiguous_candidate",
    "_task_path",
    "_mentions_unspecified_data_directory",
    "_needs_lioness_mode_choice",
    "is_versioned_documentation_request",
    "documentation_library_for_task",
    "extract_preference_proposals",
    "hydrate_router_decision",
    "_lioness_mode_plan",
    "repair_router_decision",
    "deterministic_router_fallback",
    "_is_fatal_exception",
    "_best_named_file",
    "discover_demo_bundle",
    "reusable_episode_inputs",
]


INPUT_LABELS = {
    "expression_file": _ui_text("expression matrix"),
    "motif_file": _ui_text("motif/prior"),
    "ppi_file": _ui_text("PPI network"),
    "mirna_file": _ui_text("miRNA list"),
    "network_file": _ui_text("bipartite network"),
    "output_file": _ui_text("aggregate/network output"),
    "lioness_output": _ui_text("sample-specific LIONESS output"),
    "output_dir": _ui_text("CONDOR output directory"),
}


def _candidate_keywords(action: str, field_name: str) -> tuple[str, ...]:
    mode = "puma" if "puma" in action else "panda" if "panda" in action else ""
    if field_name == "expression_file":
        return ("expression", "expr")
    if field_name == "motif_file":
        return tuple(part for part in (mode, "motif", "prior") if part)
    if field_name == "ppi_file":
        return ("ppi",)
    if field_name == "mirna_file":
        return ("mirna", "mir")
    if field_name == "network_file":
        return ("condor", "bipartite", "network")
    return ()


def _choose_unambiguous_candidate(
    candidates: list[str], keywords: tuple[str, ...], nearby: Path
) -> tuple[str | None, str]:
    """Choose autonomously only when the best workspace candidate is defensible."""
    if not candidates:
        return None, "No matching file was found in the workspace."
    if len(candidates) == 1:
        return candidates[0], "The workspace contains exactly one matching candidate."

    scored = []
    for candidate in candidates:
        path = _resolve_user_path(candidate)
        scored.append((_score_candidate_file(path, keywords, nearby), candidate))
    scored.sort(key=lambda item: (-item[0], len(item[1]), item[1]))
    best_score, best = scored[0]
    second_score = scored[1][0]
    if best_score >= second_score + 15:
        return (
            best,
            f"The best candidate score ({best_score}) clearly exceeds the runner-up ({second_score}).",
        )
    return (
        None,
        f"The top candidate scores are too close ({best_score} vs {second_score}) for safe automatic selection.",
    )


def _task_path(task: str, field_name: str) -> str | None:
    aliases = {
        "expression_file": ("expression_file", "expression", "表現矩陣", "表現資料"),
        "motif_file": ("motif_file", "motif", "prior", "先驗", "調控先驗"),
        "ppi_file": ("ppi_file", "ppi", "PPI"),
        "mirna_file": ("mirna_file", "miRNA list", "mirna list", "miRNA", "mirna"),
        "network_file": ("network_file", "network", "bipartite", "二分網路", "網路"),
        "output_file": (
            "output_file",
            "aggregate output",
            "PANDA 輸出",
            "PUMA 輸出",
            "output",
            "輸出",
        ),
        "lioness_output": (
            "lioness_output",
            "lioness output",
            "LIONESS 輸出",
            "sample-specific output",
            "個體網路輸出",
        ),
        "output_dir": (
            "output_dir",
            "output dir",
            "output directory",
            "輸出資料夾",
            "輸出目錄",
        ),
    }
    return _extract_named_path(task, aliases.get(field_name, (field_name,)))


def _mentions_unspecified_data_directory(task: str) -> bool:
    """Return True when the user asks for folder data without naming a path."""
    if not re.search(
        r"(資料夾|資料目錄|目錄|folder|directory|dir)",
        task,
        flags=re.IGNORECASE,
    ):
        return False
    path_like = re.search(
        r"([A-Za-z0-9_.~/-]+/[A-Za-z0-9_.~/-]*|\.{1,2}/[^\s，,。；;]+|/[^\s，,。；;]+)",
        task,
    )
    return path_like is None


def _needs_lioness_mode_choice(task: str) -> bool:
    """Return True for an execution request that names LIONESS but no base method."""
    normalized = task.casefold()
    if "lioness" not in normalized:
        return False
    if is_workflow_information_request(task):
        return False
    if not re.search(
        r"(run|execute|trial|test|demo|試跑|執行|跑|跑一次|測試|示範|分析)",
        normalized,
        flags=re.IGNORECASE,
    ):
        return False
    return not (
        "panda" in normalized
        or "puma" in normalized
        or re.search(
            r"(co[- _]?expression|coexpression|共表現|共同表現)",
            normalized,
            flags=re.IGNORECASE,
        )
    )


def is_versioned_documentation_request(task: str) -> bool:
    """Use retrieval only when current/version-specific documentation is material."""
    return bool(
        re.search(
            r"(latest|current|version|release|compatib|deprecated|changelog|"
            r"cli\s+(?:flag|option|argument)|install|upgrade|troubleshoot|"
            r"\bapi\b|documentation|docs|context7|[-–][A-Za-z]\b|"
            r"最新版|目前|版本|相容|棄用|安裝|升級|錯誤排除|文件|"
            r"參數(?:變更|更新))",
            task,
            flags=re.IGNORECASE,
        )
    )


def documentation_library_for_task(task: str) -> str | None:
    """Resolve an allow-listed documentation library without asking the LLM."""
    normalized = task.casefold()
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


def extract_preference_proposals(task: str) -> list[PreferenceProposal]:
    """Parse only explicit durable-preference requests from the latest user turn."""
    if not re.search(
        r"(remember|always|from now on|make .{0,20} default|"
        r"記住|永遠|從現在起|以後|設為預設|預設為)",
        task,
        flags=re.IGNORECASE,
    ):
        return []

    proposals: list[PreferenceProposal] = []
    output_match = re.search(
        r"(?:default\s+output(?:\s+directory|\s+dir)?|預設輸出(?:資料夾|目錄)?)"
        r"\s*(?:is|=|:|：|為|是)?\s*([^\s，,。；;]+)",
        task,
        flags=re.IGNORECASE,
    )
    if output_match:
        proposals.append(
            PreferenceProposal(
                key="default_output_dir",
                value=output_match.group(1).strip("'\".。"),
                reason="The user explicitly requested a persistent default output directory.",
            )
        )

    if re.search(
        r"(reuse|re-use|重用|沿用).{0,24}(last|previous|上次|之前).{0,12}(input|輸入)",
        task,
        re.IGNORECASE,
    ):
        disabled = bool(
            re.search(
                r"(do not|don't|never|不要|不可|停止).{0,20}(reuse|重用|沿用)",
                task,
                re.IGNORECASE,
            )
        )
        proposals.append(
            PreferenceProposal(
                key="reuse_last_inputs",
                value="false" if disabled else "true",
                reason="The user explicitly requested a persistent input-reuse preference.",
            )
        )

    if re.search(
        r"(demo|toy|示範|測試).{0,20}(autofill|auto.?fill|自動補|自動選)",
        task,
        re.IGNORECASE,
    ):
        disabled = bool(
            re.search(r"(do not|don't|never|不要|不可|關閉)", task, re.IGNORECASE)
        )
        proposals.append(
            PreferenceProposal(
                key="allow_demo_autofill",
                value="false" if disabled else "true",
                reason="The user explicitly requested a persistent demo-autofill preference.",
            )
        )

    preferred = None
    normalized = task.casefold()
    for label, value in (
        ("lioness co-expression", "lioness_coexpression"),
        ("lioness coexpression", "lioness_coexpression"),
        ("lioness-panda", "lioness_panda"),
        ("lioness panda", "lioness_panda"),
        ("lioness-puma", "lioness_puma"),
        ("lioness puma", "lioness_puma"),
        ("condor", "condor"),
        ("puma", "puma"),
        ("panda", "panda"),
    ):
        if label in normalized and re.search(
            r"(preferred|default|偏好|預設).{0,24}(workflow|流程|工作流)|"
            r"(workflow|流程|工作流).{0,24}(preferred|default|偏好|預設)",
            normalized,
            flags=re.IGNORECASE,
        ):
            preferred = value
            break
    if preferred:
        proposals.append(
            PreferenceProposal(
                key="preferred_workflow",
                value=preferred,
                reason="The user explicitly requested a persistent preferred workflow.",
            )
        )
    return proposals


def hydrate_router_decision(
    raw_decision: RouterDecision | TaskDecision | dict,
    task: str,
) -> TaskDecision:
    """Hydrate the small Router interface with deterministic task details."""
    if isinstance(raw_decision, TaskDecision):
        decision = raw_decision.model_copy(deep=True)
    else:
        route = RouterDecision.model_validate(raw_decision)
        decision = TaskDecision(
            action=route.action,
            in_scope=route.in_scope,
            should_execute=route.action != "no_tool",
            intent_type=route.intent_type,
            confidence=route.confidence,
            reason=route.reason,
            recommended_actions=route.recommended_actions,
        )

    for field_name in (
        "expression_file",
        "motif_file",
        "ppi_file",
        "mirna_file",
        "output_file",
        "lioness_output",
        "network_file",
        "output_dir",
    ):
        parsed = _task_path(task, field_name)
        if parsed:
            setattr(decision, field_name, parsed)

    prefix = _extract_named_path(task, ("prefix", "前綴"))
    if prefix:
        decision.prefix = prefix
    if re.search(
        r"(with[_ -]?header|include .{0,8}header|包含.{0,4}標頭)", task, re.IGNORECASE
    ):
        decision.with_header = True
    if re.search(r"(genes?|基因).{0,12}(rows?|列)", task, re.IGNORECASE):
        decision.genes_axis = "rows"
    elif re.search(r"(genes?|基因).{0,12}(columns?|cols?|欄)", task, re.IGNORECASE):
        decision.genes_axis = "columns"

    if decision.action == "query_context7":
        decision.library_name = documentation_library_for_task(task)
        decision.library_id = None
        decision.docs_query = task[:2_000]
    elif decision.action == "web_search":
        decision.web_query = task[:2_000]

    parsed_preferences = extract_preference_proposals(task)
    if parsed_preferences:
        existing = {proposal.key for proposal in decision.preference_updates}
        decision.preference_updates.extend(
            proposal for proposal in parsed_preferences if proposal.key not in existing
        )

    if decision.action in REQUIRED_INPUTS:
        decision.missing_inputs = [
            field_name
            for field_name in REQUIRED_INPUTS[decision.action]
            if not getattr(decision, field_name, None)
        ]
    decision.should_execute = decision.action != "no_tool"
    return decision


def _lioness_mode_plan(
    decision: TaskDecision,
    task: str,
    *,
    memory_notes: list[str],
    policy_hash: str | None,
) -> WorkflowPlan:
    """Build a resumable mode-selection step without guessing the LIONESS method."""
    candidates = [
        _ui_text("LIONESS PANDA - expression + motif/prior + PPI"),
        _ui_text("LIONESS PUMA - expression + TF/miRNA prior + PPI + miRNA list"),
        _ui_text("LIONESS co-expression - expression only"),
    ]
    question = _ui_text(LIONESS_MODE_QUESTION)
    mode_decision = decision.model_copy(
        update={
            "action": "no_tool",
            "in_scope": True,
            "should_execute": False,
            "confidence": max(decision.confidence, MIN_TOOL_CONFIDENCE),
            "reason": "A LIONESS run was requested, but its base method is ambiguous.",
            "missing_inputs": ["lioness_mode"],
        }
    )
    return WorkflowPlan(
        workflow="LIONESS",
        objective=f"Choose a LIONESS base method before continuing: {task}",
        decision=mode_decision.model_dump(),
        evidence=[
            InputEvidence(
                field="lioness_mode",
                status="missing",
                reason=_ui_text(
                    "LIONESS needs an explicit base method because PANDA, PUMA, and "
                    "co-expression require different inputs and produce different networks."
                ),
                candidates=candidates,
            )
        ],
        missing_inputs=["lioness_mode"],
        status="needs_input",
        question=question,
        memory_notes=memory_notes,
        policy_hash=policy_hash,
    )


def repair_router_decision(raw_decision: TaskDecision, task: str) -> TaskDecision:
    """Repair under-routing while keeping execution tied to a recognized user goal."""
    normalized = task.casefold()
    inferred_recommendations = infer_goal_capabilities(task)
    recommendations = inferred_recommendations or raw_decision.recommended_actions
    if recommendations != raw_decision.recommended_actions:
        raw_decision = raw_decision.model_copy(
            update={"recommended_actions": recommendations}
        )

    documentation_library = documentation_library_for_task(task)
    if is_versioned_documentation_request(task) and documentation_library:
        return TaskDecision(
            action="query_context7",
            in_scope=True,
            should_execute=True,
            intent_type="answer_question",
            confidence=max(raw_decision.confidence, MIN_TOOL_CONFIDENCE),
            reason="The request requires current or version-specific package documentation.",
            library_name=documentation_library,
            docs_query=task[:2_000],
            recommended_actions=recommendations,
            preference_updates=raw_decision.preference_updates,
        )

    if is_workflow_information_request(task):
        named_recommendations = infer_advisory_capabilities(task)
        if not named_recommendations:
            named_recommendations = list(recommendations)
        if not named_recommendations:
            if "lioness" in normalized and "puma" in normalized:
                named_recommendations = ["run_puma", "run_lioness_puma"]
            elif "lioness" in normalized and "panda" in normalized:
                named_recommendations = ["run_panda", "run_lioness_panda"]
            elif "lioness" in normalized and re.search(
                r"(co[- _]?expression|coexpression|共表現|共同表現)", normalized
            ):
                named_recommendations = ["run_lioness_coexpression"]
            elif "puma" in normalized:
                named_recommendations = ["run_puma"]
            elif "panda" in normalized:
                named_recommendations = ["run_panda"]
            elif "condor" in normalized:
                named_recommendations = ["run_condor"]
        return TaskDecision(
            action="no_tool",
            in_scope=True,
            should_execute=False,
            intent_type="answer_question",
            confidence=max(raw_decision.confidence, MIN_TOOL_CONFIDENCE),
            reason="The request asks for stable workflow requirements or usage guidance.",
            recommended_actions=named_recommendations,
            preference_updates=raw_decision.preference_updates,
        )

    continuation_match = re.search(
        r"PREVIOUS_ACTION=(run_[a-z_]+)", task, flags=re.IGNORECASE
    )
    if continuation_match:
        action = continuation_match.group(1).casefold()
        if action in LOCAL_WORKFLOW_ACTIONS:
            repaired = raw_decision.model_dump()
            repaired.update(
                {
                    "action": action,
                    "in_scope": True,
                    "should_execute": True,
                    "confidence": max(raw_decision.confidence, MIN_TOOL_CONFIDENCE),
                    "reason": (
                        "Continuing a pending workflow; the previous action marker "
                        "overrides any router reclassification."
                    ),
                }
            )
            for field_name in REQUIRED_INPUTS.get(action, ()):
                parsed = _task_path(task, field_name)
                if parsed:
                    repaired[field_name] = parsed
            repaired["missing_inputs"] = [
                field_name
                for field_name in REQUIRED_INPUTS.get(action, ())
                if field_name not in {"output_file", "lioness_output", "output_dir"}
                and not repaired.get(field_name)
            ]
            return TaskDecision.model_validate(repaired)

    inferred_action = inferred_execution_action(task)
    if (
        inferred_action
        and has_direct_execution_intent(task)
        and raw_decision.action != inferred_action
        and (raw_decision.action == "no_tool" or raw_decision.action in recommendations)
    ):
        repaired = raw_decision.model_dump()
        repaired.update(
            {
                "action": inferred_action,
                "in_scope": True,
                "should_execute": True,
                "intent_type": "demo_run" if _is_demo_request(task) else "run_analysis",
                "confidence": max(raw_decision.confidence, MIN_TOOL_CONFIDENCE),
                "reason": (
                    "The requested deliverable maps to an allow-listed local workflow; "
                    "the user does not need to know or name the tool in advance."
                ),
                "recommended_actions": recommendations,
            }
        )
        repaired["missing_inputs"] = [
            field_name
            for field_name in REQUIRED_INPUTS[inferred_action]
            if not repaired.get(field_name)
        ]
        return TaskDecision.model_validate(repaired)

    if raw_decision.action != "no_tool":
        return raw_decision

    if is_workflow_information_request(task):
        return raw_decision.model_copy(
            update={
                "intent_type": "answer_question",
                "should_execute": False,
            }
        )

    run_intent = re.search(
        r"(run|execute|trial|test|demo|試跑|執行|跑|跑一次|測試|做測試|示範|分析)",
        normalized,
        flags=re.IGNORECASE,
    )
    lioness_action = None
    if "lioness" in normalized and run_intent:
        if "panda" in normalized:
            lioness_action = "run_lioness_panda"
        elif "puma" in normalized:
            lioness_action = "run_lioness_puma"
        elif re.search(
            r"(co[- _]?expression|coexpression|共表現|共同表現)",
            normalized,
            flags=re.IGNORECASE,
        ):
            lioness_action = "run_lioness_coexpression"
    if lioness_action:
        repaired = raw_decision.model_dump()
        repaired.update(
            {
                "action": lioness_action,
                "in_scope": True,
                "should_execute": True,
                "confidence": max(raw_decision.confidence, MIN_TOOL_CONFIDENCE),
                "reason": (
                    "Explicit LIONESS mode and run/test request; the Planner will "
                    "resolve inputs or ask for missing data."
                ),
            }
        )
        repaired["missing_inputs"] = [
            field_name
            for field_name in REQUIRED_INPUTS[lioness_action]
            if not repaired.get(field_name)
        ]
        return TaskDecision.model_validate(repaired)

    condor_run_intent = "condor" in normalized and re.search(
        r"(run|execute|trial|test|試跑|執行|跑|跑一次|測試|做測試|分析|community|module|社群|模組)",
        normalized,
        flags=re.IGNORECASE,
    )
    if not condor_run_intent:
        return raw_decision

    return TaskDecision(
        action="run_condor",
        in_scope=True,
        should_execute=True,
        confidence=max(raw_decision.confidence, MIN_TOOL_CONFIDENCE),
        reason=(
            "Explicit CONDOR run/test request; the Planner will resolve demo inputs "
            "or ask for missing paths."
        ),
        network_file=_task_path(task, "network_file"),
        output_dir=_task_path(task, "output_dir"),
        prefix=raw_decision.prefix,
        missing_inputs=["network_file", "output_dir"],
        recommended_actions=recommendations,
        preference_updates=raw_decision.preference_updates,
    )


def deterministic_router_fallback(
    task: str, error: BaseException | None = None
) -> TaskDecision:
    """Classify obvious local run intents when the provider/router fails."""
    normalized = task.casefold()
    recommendations = infer_goal_capabilities(task)
    reason = (
        "The LLM router failed, so the agent used a deterministic fallback for an "
        "explicit local workflow request."
    )
    if error is not None:
        reason += f" Provider error: {type(error).__name__}."

    documentation_library = documentation_library_for_task(task)
    if is_versioned_documentation_request(task) and documentation_library:
        return TaskDecision(
            action="query_context7",
            in_scope=True,
            should_execute=True,
            intent_type="answer_question",
            confidence=1.0,
            reason="Deterministic routing selected current package documentation.",
            library_name=documentation_library,
            docs_query=task[:2_000],
        )

    rejection = validate_task_text(task, "no_tool")
    if rejection:
        return TaskDecision(
            action="no_tool",
            in_scope=False,
            should_execute=False,
            intent_type="unknown",
            confidence=1.0,
            reason=rejection,
        )
    if is_workflow_information_request(task):
        recommendations = infer_advisory_capabilities(task)
        return TaskDecision(
            action="no_tool",
            in_scope=True,
            should_execute=False,
            intent_type="answer_question",
            confidence=1.0,
            reason=(
                "The request asks for workflow requirements or usage information, "
                "not local execution."
            ),
            recommended_actions=recommendations,
        )

    run_intent = has_direct_execution_intent(task) or re.search(
        r"(run|execute|trial|test|demo|試跑|執行|跑|跑一次|測試|做測試|示範|分析)",
        normalized,
        flags=re.IGNORECASE,
    )
    if not run_intent:
        return TaskDecision(
            action="no_tool",
            in_scope=True,
            should_execute=False,
            intent_type="unknown",
            confidence=1.0,
            reason="The provider failed and no deterministic local workflow intent was found.",
            recommended_actions=recommendations,
        )

    action = (
        inferred_execution_action(task) if has_direct_execution_intent(task) else None
    )
    if "lioness" in normalized:
        if "panda" in normalized:
            action = "run_lioness_panda"
        elif "puma" in normalized:
            action = "run_lioness_puma"
        elif re.search(
            r"(co[- _]?expression|coexpression|共表現|共同表現)",
            normalized,
            flags=re.IGNORECASE,
        ):
            action = "run_lioness_coexpression"
        else:
            return TaskDecision(
                action="no_tool",
                in_scope=True,
                should_execute=False,
                intent_type="demo_run" if _is_demo_request(task) else "run_analysis",
                confidence=1.0,
                reason="A LIONESS run was requested, but its base method is ambiguous.",
                missing_inputs=["lioness_mode"],
            )
    elif action is None and "panda" in normalized:
        action = "run_panda"
    elif action is None and "puma" in normalized:
        action = "run_puma"
    elif action is None and "condor" in normalized:
        action = "run_condor"

    if action is None:
        return TaskDecision(
            action="no_tool",
            in_scope=True,
            should_execute=False,
            intent_type="unknown",
            confidence=1.0,
            reason=(
                "The provider failed and the task did not identify an allow-listed "
                "workflow by either name or objective."
            ),
            recommended_actions=recommendations,
        )

    values = {
        "action": action,
        "in_scope": True,
        "should_execute": True,
        "intent_type": "demo_run" if _is_demo_request(task) else "run_analysis",
        "confidence": 1.0,
        "reason": reason,
        "recommended_actions": recommendations,
        "missing_inputs": [
            field_name
            for field_name in REQUIRED_INPUTS[action]
            if field_name not in {"output_file", "lioness_output", "output_dir"}
        ],
    }
    for field_name in REQUIRED_INPUTS[action]:
        parsed = _task_path(task, field_name)
        if parsed:
            values[field_name] = parsed
    return TaskDecision(**values)


def _is_fatal_exception(error: BaseException) -> bool:
    return isinstance(error, (KeyboardInterrupt, SystemExit, GeneratorExit))


def _best_named_file(directory: Path, keywords: tuple[str, ...]) -> Path | None:
    candidates = [
        path
        for path in directory.iterdir()
        if path.is_file()
        and path.suffix.casefold() in {".tsv", ".tab", ".txt", ".csv"}
        and any(keyword in path.name.casefold() for keyword in keywords)
    ]
    if not candidates:
        return None
    candidates.sort(
        key=lambda path: (
            -_score_candidate_file(path, keywords, directory),
            len(path.name),
            path.name,
        )
    )
    return candidates[0]


def discover_demo_bundle(action: str) -> tuple[dict[str, str], str] | None:
    """Find a coherent toy dataset as a bundle, then validate cross-file compatibility."""
    data_root = PROJECT_ROOT / "data"
    if action == "run_condor":
        candidates: list[tuple[int, Path]] = []
        for path in data_root.rglob("*"):
            if not path.is_file() or path.suffix.casefold() not in {
                ".tsv",
                ".txt",
                ".csv",
            }:
                continue
            name = path.name.casefold()
            if "condor" not in name and "bipartite" not in name:
                continue
            _, ok = _inspect_condor_inputs_impl(str(path))
            if ok:
                score = 100 if "condor-toy" in str(path.parent).casefold() else 20
                candidates.append((score, path))
        if not candidates:
            return None
        candidates.sort(key=lambda item: (-item[0], str(item[1])))
        best_score, best = candidates[0]
        if len(candidates) > 1 and best_score < candidates[1][0] + 15:
            return None
        return (
            {"network_file": _display_path(best)},
            "Demo intent: selected a complete CONDOR toy bundle that passed format validation.",
        )

    if action == "run_lioness_coexpression":
        candidates: list[tuple[int, Path]] = []
        for expression in data_root.rglob("*"):
            if (
                not expression.is_file()
                or "expression" not in expression.name.casefold()
            ):
                continue
            sample_count, error = _expression_sample_count(str(expression))
            if error or sample_count < 3:
                continue
            location = str(expression.parent).casefold()
            score = 0
            if "lioness" in location:
                score += 100
            if "toy" in location:
                score += 20
            if "manual" in location:
                score -= 30
            candidates.append((score, expression))
        if not candidates:
            return None
        candidates.sort(key=lambda item: (-item[0], str(item[1])))
        best_score, best = candidates[0]
        if len(candidates) > 1 and best_score < candidates[1][0] + 15:
            return None
        return (
            {"expression_file": _display_path(best)},
            "Demo intent: selected a LIONESS expression dataset with at least three samples.",
        )

    if action not in {
        "run_panda",
        "run_puma",
        "run_lioness_panda",
        "run_lioness_puma",
    }:
        return None
    mode = "puma" if "puma" in action else "panda"
    candidates: list[tuple[int, dict[str, str]]] = []
    for expression in data_root.rglob("*"):
        if not expression.is_file() or "expression" not in expression.name.casefold():
            continue
        directory = expression.parent
        motif = _best_named_file(directory, (mode, "motif", "prior"))
        ppi = _best_named_file(directory, ("ppi",))
        mirna = (
            _best_named_file(directory, ("mirna", "mir")) if mode == "puma" else None
        )
        if not motif or not ppi or (mode == "puma" and not mirna):
            continue
        _, ok, _ = _inspect_panda_inputs_impl(
            str(expression), str(motif), str(ppi), str(mirna or "")
        )
        sample_count, _ = _expression_sample_count(str(expression))
        if not ok or ("lioness" in action and sample_count < 3):
            continue
        bundle = {
            "expression_file": _display_path(expression),
            "motif_file": _display_path(motif),
            "ppi_file": _display_path(ppi),
        }
        if mirna:
            bundle["mirna_file"] = _display_path(mirna)
        location = str(directory).casefold()
        score = 0
        if "lioness" in action and "lioness" in location:
            score += 100
        if action in {"run_panda", "run_puma"} and "official-toy" in location:
            score += 100
        if mode in location or mode in motif.name.casefold():
            score += 30
        if "toy" in location:
            score += 20
        if "manual" in location:
            score -= 30
        candidates.append((score, bundle))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (-item[0], json.dumps(item[1], sort_keys=True)))
    best_score, best_bundle = candidates[0]
    if len(candidates) > 1 and best_score < candidates[1][0] + 15:
        return None
    return (
        best_bundle,
        (
            "Demo intent: files are complete in one dataset directory and expression/prior/PPI"
            + ("/miRNA" if mode == "puma" else "")
            + " identifier validation passed."
        ),
    )


def reusable_episode_inputs(
    action: str, episodes: list[Episode]
) -> tuple[dict[str, str], str] | None:
    expected_workflow = _workflow_name(action)
    for episode in episodes:
        if episode.status != "completed" or episode.workflow != expected_workflow:
            continue
        required_fields = [
            field_name
            for field_name in REQUIRED_INPUTS.get(action, ())
            if field_name not in {"output_file", "lioness_output", "output_dir"}
        ]
        if any(field_name not in episode.inputs for field_name in required_fields):
            continue
        values = {
            field_name: episode.inputs[field_name] for field_name in required_fields
        }
        if any(not _resolve_user_path(path).exists() for path in values.values()):
            continue
        if action == "run_condor":
            _, ok = _inspect_condor_inputs_impl(values["network_file"])
        elif action in {
            "run_panda",
            "run_puma",
            "run_lioness_panda",
            "run_lioness_puma",
        }:
            _, ok, _ = _inspect_panda_inputs_impl(
                values["expression_file"],
                values["motif_file"],
                values["ppi_file"],
                values.get("mirna_file", ""),
            )
            if ok and "lioness" in action:
                sample_count, _ = _expression_sample_count(values["expression_file"])
                ok = sample_count >= 3
        else:
            ok = True
        if ok:
            return (
                values,
                f"Reused validated inputs from successful episode {episode.episode_id[:8]} under the confirmed reuse_last_inputs preference.",
            )
    return None
