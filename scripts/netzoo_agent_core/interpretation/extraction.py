"""Deterministic extraction of task paths, intent details, and preferences."""

from __future__ import annotations

import re
from pathlib import Path

from ..contracts import PROJECT_ROOT, PreferenceProposal, _ui_text
from ..routing import (
    CONTEXT7_LIBRARY_ALIASES,
    _extract_named_path,
    is_workflow_information_request,
)

__all__: list[str] = []


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


_PATHLIKE_SUFFIXES = frozenset({".tsv", ".tab", ".txt", ".csv", ".npy"})


def extract_workspace_subpath(
    task: str,
    workspace_root: Path = PROJECT_ROOT,
) -> str | None:
    """Extract one explicit filesystem-shaped token only when it stays in workspace."""
    root = workspace_root.expanduser().resolve()
    candidates = re.findall(r"['\"]([^'\"]+)['\"]|([^\s，,。；;]+)", task)
    for quoted, plain in candidates:
        token = (quoted or plain).strip().rstrip(".。:：")
        if not token or "://" in token or not _looks_like_path(token):
            continue
        path = Path(token).expanduser()
        candidate = path.resolve() if path.is_absolute() else (root / path).resolve()
        if not candidate.is_relative_to(root):
            continue
        if candidate.is_file():
            candidate = candidate.parent
        rendered = candidate.relative_to(root).as_posix()
        return rendered or "."
    return None


def _looks_like_path(value: str) -> bool:
    token = value.strip().rstrip(".。").casefold()
    return token not in _PATHLIKE_SUFFIXES and bool(
        "/" in token
        or "\\" in token
        or token.startswith((".", "~"))
        or any(token.endswith(suffix) for suffix in _PATHLIKE_SUFFIXES)
    )


def _alias_pattern(aliases: tuple[str, ...]) -> str:
    ordered = sorted(aliases, key=len, reverse=True)
    return "|".join(re.escape(alias) for alias in ordered)


def _has_explicit_file_binding(task: str, aliases: tuple[str, ...]) -> bool:
    names = _alias_pattern(aliases)
    return bool(
        re.search(
            rf"(?:{names})\s*(?:(?:是|為|=|:|：)|\b(?:at|as|is|to)\b|['\"])",
            task,
            flags=re.IGNORECASE,
        )
    )


def _reverse_named_path(task: str, aliases: tuple[str, ...]) -> str | None:
    names = _alias_pattern(aliases)
    match = re.search(
        rf"(?:(?P<quote>['\"])(?P<quoted>.*?)(?P=quote)|"
        rf"(?P<plain>[^\s，,。；;]+))\s+(?:as|for)\s+(?:the\s+)?(?:{names})",
        task,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    value = match.group("quoted") or match.group("plain")
    cleaned = value.strip().rstrip(".。")
    return cleaned if match.group("quote") or _looks_like_path(cleaned) else None


def _task_path(task: str, field_name: str) -> str | None:
    aliases_by_field = {
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
    aliases = aliases_by_field.get(field_name, (field_name,))
    reversed_path = _reverse_named_path(task, aliases)
    if reversed_path:
        return reversed_path
    parsed = _extract_named_path(task, aliases)
    if parsed and (
        _looks_like_path(parsed) or _has_explicit_file_binding(task, aliases)
    ):
        return parsed
    return None


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
