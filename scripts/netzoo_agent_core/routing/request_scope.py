"""Positive, current mentions used by lexical capability boundaries."""

from __future__ import annotations

import re
from dataclasses import dataclass

from workflow_registry import RUN_ACTIONS

from ..interpretation.request_integrity import _scoped_clauses


_DECLINED_PREFIX = re.compile(
    r"\b(?:do\s+not|don't|does\s+not|doesn't|not|never|without|avoid|exclude|no)\b"
    r"|不要|不用|避免|不需要|不想",
    re.IGNORECASE,
)


def has_current_positive_mention(task: str, pattern: str | re.Pattern[str]) -> bool:
    """Ignore a historical or explicitly declined mention of a boundary term."""
    compiled = re.compile(pattern, re.IGNORECASE) if isinstance(pattern, str) else pattern
    for clause, scope in _scoped_clauses(task):
        if scope == "historical":
            continue
        for match in compiled.finditer(clause):
            if not _DECLINED_PREFIX.search(clause[max(0, match.start() - 48):match.start()]):
                return True
    return False


# Operation authority (diagnostics F1/F2, 2026-10-03). Which tool fits is the
# registry's question; whether the user asked for an operation now is this
# one. The deterministic rules that promote a request to execution used to
# search the whole message, so "Do not use WEB-SEARCH to search ..." was read as
# a search command and "不要執行分析" as an input-check request. They now read
# only the text that can grant authority, and a forbidding clause is kept as a
# ban that vetoes execution from any source.

# Quoted text is shown or discussed, not asked for: neither a quoted command
# nor a quoted prohibition is the user's own instruction.
_QUOTED = re.compile(r'"[^"\n]{1,400}"|“[^”\n]{1,400}”|「[^」\n]{1,400}」|『[^』\n]{1,400}』')
# Someone else's words. A relayed command grants nothing; a relayed
# prohibition still counts, because ignoring it could only add authority.
_REPORTED = re.compile(
    r"\b(?:said|says|told\s+(?:me|us)|wrote|writes|asked\s+(?:me|us)\s+to|according\s+to)\b"
    r"|(?:老師|老师|教授|同事|學長|學姊|老闆|主管|審稿人|他們|他|她|有人|文件|教學|論文|README)"
    r"\s*(?:說|说|寫|写|建議|建议|提到|要我|叫我)",
    re.IGNORECASE,
)
_NEGATOR = re.compile(
    r"\b(?:do\s+not|does\s+not|don['’]?t|never|must\s+not|mustn['’]?t|should\s+not|shouldn['’]?t"
    r"|no\s+need\s+to|not\s+to|without|avoid|refrain\s+from|instead\s+of|rather\s+than)\b"
    r"|\bno\s+(?=(?:web[- ]?search|search(?:es|ing)?|execution|analysis|downloads?|inspection)\b)"
    r"|不要|不用|别|別|勿|不需要|不必|無需|无需|不准|禁止|不是要|沒有要|没有要|不想",
    re.IGNORECASE,
)
# "Don't forget to run", "別忘了檢查": the negation is not about the operation.
_NOT_A_BAN = re.compile(r"\s*(?:forget|hesitate|worry|mind)\b|\s*(?:忘|擔心|担心|客氣|客气)", re.IGNORECASE)
# A negation reaches the operations after it up to the next coordinated
# instruction ("..., just run it", "不要搜尋，直接跑").
_BAN_STOP = re.compile(
    r"\b(?:and\s+then|then|but|instead|just)\b|然後|然后|接著|接着|但是|但|而是",
    re.IGNORECASE,
)
_COORDINATION = re.compile(r"\s+or\s+|\s*(?:或者|或是|或|也不要|、)\s*", re.IGNORECASE)
_RETRIEVE_TERM = re.compile(
    r"\b(?:web[- ]?search|context7|search(?:es|ing)?|google|browse|look(?:ing)?\s+up|lookup"
    r"|internet|online|the\s+web)\b"
    r"|搜尋|搜索|上網|上网|查網路|查网路|聯網|联网|查詢|查询|查找|檢索|检索|文獻|文献",
    re.IGNORECASE,
)
_INSPECT_TERM = re.compile(
    r"\b(?:inspect(?:ion|ing)?|check(?:s|ing)?|validat(?:e|ion|ing)|verif(?:y|ication|ying)|preflight)\b"
    r"|檢查|检查|驗證|验证|預檢|预检|核對|核对",
    re.IGNORECASE,
)
_ACQUIRE_TERM = re.compile(r"\b(?:download(?:ing|s)?|fetch(?:ing)?)\b|下載|下载", re.IGNORECASE)
# A run word used as a noun ("the analysis output", "分析結果") names a thing,
# not the forbidden operation; nor does a CLI command name ("不要輸入 /execute"
# asks for the dry-run preview, not for no plan at all). English "test" is left
# out: in a research request it is a statistical test ("without testing
# anything"), while 測試 stays a software test.
_RUN_TERM = re.compile(
    r"(?:(?<!/)\b(?:run(?:s|ning)?|execut(?:e|ion|ing)|perform(?:ing)?|launch(?:ing)?|comput(?:e|ing)"
    r"|analy[sz](?:e|is|ing)|dry[- ]?run)\b"
    r"(?!\s*(?:outputs?|results?|folders?|files?|data|datasets?|mode|directory|dir|reports?|sets?|logs?)\b)"
    r"|(?:執行|执行|試跑|跑|運行|运行|分析|計算|计算|運算|运算|推論|推断|測試|测试)"
    r"(?!結果|结果|資料|资料|數據|数据|檔|档|模式|輸出|输出|報告|报告))",
    re.IGNORECASE,
)
# "use"/"用" forbids running only with a named workflow ("不要用 LIONESS");
# "don't use my old file" forbids nothing.
_GENERIC_VERB = re.compile(r"\b(?:use|using|call|do)\b|使用|用|做", re.IGNORECASE)
_ANYTHING = re.compile(
    r"\b(?:anything|any\s+(?:tools?|commands?|operations?|workflows?|code))\b"
    r"|任何(?:東西|东西|工具|操作|指令|動作|动作|事|程式|程序)|什麼都不|什么都不",
    re.IGNORECASE,
)
# Registry-derived workflow names that narrow a run ban ("不要執行 PANDA").
_WORKFLOW_TOKENS = tuple(sorted(
    {token for action in RUN_ACTIONS for token in action.removeprefix("run_").split("_")}
    - {"coexpression"}
))
_WORKFLOW_TOKEN = re.compile(
    r"(?<![A-Za-z0-9])(" + "|".join(_WORKFLOW_TOKENS) + r")(?![A-Za-z0-9])", re.IGNORECASE,
)
_EXPLAIN_ONLY = re.compile(
    r"\b(?:only|just|merely|simply)\s+(?:explain|describe|discuss|outline)\b"
    r"|\b(?:explain|explanation|describe|description|guidance|advice)\s+only\b"
    r"|只(?:要|需|需要|想)?\s*(?:解釋|解释|說明|说明|講解|讲解|介紹|介绍)"
    r"|僅(?:需)?\s*(?:解釋|解释|說明|说明)|(?:解釋|解释|說明|说明)就好",
    re.IGNORECASE,
)
# A request for a preview, dry run or plan. A run ban beside it means "not
# now", which preview mode and the separate /execute confirmation enforce.
_PREVIEW_CUE = re.compile(
    r"\b(?:dry[- ]?run|preview|prepare|set\s+up)\b|\b(?:work|workflow|execution)\s*plan\b"
    r"|預覽|预览|準備|准备",
    re.IGNORECASE,
)
_NEGATED_RESTRICTION = re.compile(r"(?:\bnot|n['’]t|不)\s*$", re.IGNORECASE)


@dataclass(frozen=True)
class OperationBan:
    """One operation the user's own words forbid, with the words that forbid it."""

    kind: str
    tools: tuple[str, ...]
    quote: str


@dataclass(frozen=True)
class OperationScope:
    """The authority-bearing reading of one request.

    ``admissible_text`` keeps only current, unquoted, unreported, non-negated,
    non-explain-only clause text; positive cues are searched there. Bans and
    the explain-only marker are read from the same clauses.
    """

    admissible_text: str
    bans: tuple[OperationBan, ...]
    explain_only: str | None
    preview_requested: bool = False


def _ban_kinds(span: str) -> tuple[set[str], tuple[str, ...]]:
    kinds: set[str] = set()
    if _RETRIEVE_TERM.search(span):
        kinds.add("retrieve")
    if _INSPECT_TERM.search(span):
        kinds.add("inspect")
    if _ACQUIRE_TERM.search(span):
        kinds.add("acquire")
    tools = tuple(dict.fromkeys(m.group(1).casefold() for m in _WORKFLOW_TOKEN.finditer(span)))
    run_verb = _RUN_TERM.search(span) is not None
    generic_verb = _GENERIC_VERB.search(span) is not None
    if not kinds and (run_verb or (tools and generic_verb)):
        # "run the search" is a search; a bare run verb is an analysis.
        kinds.add("run")
    if _ANYTHING.search(span) and kinds <= {"run"} and (run_verb or generic_verb):
        return {"any"}, ()
    return kinds, tools if kinds == {"run"} else ()


def _clause_ban(clause: str) -> tuple[int, list[OperationBan]] | None:
    """Return where the first forbidding negation starts and what it forbids."""
    for negation in _NEGATOR.finditer(clause):
        if _NOT_A_BAN.match(clause, negation.end()):
            continue
        rest = clause[negation.end():negation.end() + 80]
        stop = _BAN_STOP.search(rest)
        span = rest[:stop.start()] if stop else rest
        # One negation reaches every coordinated operation: "do not search the
        # web or run anything" forbids both.
        bans = [
            OperationBan(kind, tools, clause[negation.start():negation.end() + len(span)].strip())
            for part in _COORDINATION.split(span)
            for kinds, tools in [_ban_kinds(part)]
            for kind in sorted(kinds)
        ]
        if bans:
            return negation.start(), list(dict.fromkeys(bans))
    return None


def _explain_only_marker(clause: str) -> re.Match[str] | None:
    for marker in _EXPLAIN_ONLY.finditer(clause):
        if not _NEGATED_RESTRICTION.search(clause[max(0, marker.start() - 8):marker.start()]):
            return marker
    return None


def operation_scope(task: str) -> OperationScope:
    """Split one request into authority-bearing text, bans and explain-only."""
    unquoted = _QUOTED.sub(lambda match: " " * len(match.group()), task)
    kept: list[str] = []
    bans: list[OperationBan] = []
    explain_only: str | None = None
    for clause, scope in _scoped_clauses(unquoted):
        if scope == "historical":
            continue
        ban = _clause_ban(clause)
        if ban is not None:
            bans.extend(ban[1])
        marker = _explain_only_marker(clause)
        if marker is not None:
            explain_only = explain_only or marker.group().strip()
        if _REPORTED.search(clause):
            continue
        cut = min(
            [index for index in (ban[0] if ban else None, marker.start() if marker else None)
             if index is not None],
            default=len(clause),
        )
        kept.append(clause[:cut])
    admissible = "\n".join(kept)
    return OperationScope(
        admissible, tuple(dict.fromkeys(bans)), explain_only,
        preview_requested=_PREVIEW_CUE.search(admissible) is not None,
    )


def admissible_request_text(task: str) -> str:
    """The part of *task* that can authorize an operation."""
    return operation_scope(task).admissible_text
