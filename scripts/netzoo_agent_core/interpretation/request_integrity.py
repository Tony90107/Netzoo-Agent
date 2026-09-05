"""Bounded text checks for omitted request facts, never automatic field repair.

These lexical witnesses are deliberately independent of workflow names and of
the model's filled fields. They are not a complete natural-language parser.
"""
from dataclasses import dataclass
import re


INPUT_PATTERNS = {
    "mutation_matrix": r"\bsomatic mutations?\b|\bmutation (?:matrix|counts)\b|"
                       r"DNA\s*突變(?:資料|矩陣)|體細胞突變|突變矩陣",
    "expression_matrix": r"\bRNA[- ]?Seq\b|\b(?:gene )?expression (?:matrix|data|dataset)\b|"
                         r"(?:基因)?表現量?(?:矩陣|資料)",
}
_HISTORY = re.compile(r"\b(?:previously|historical|earlier|past|old)\b|曾經|之前|先前|過去|剛剛|跑完", re.I)
_CURRENT = re.compile(r"\b(?:now|currently|current|have|received)\b|現在|目前|手邊|這份|我有|拿到|給了我", re.I)
_UNCERTAIN = re.compile(r"\b(?:if|hypothetical|might|would obtain|could obtain)\b|假如|假設|如果|尚未|還沒有", re.I)
_NEGATED = re.compile(r"\b(?:not|without|no)\b|不是|並非|沒有|不含", re.I)
_OUTPUT = re.compile(r"\b(?:produce[sd]?|generate[sd]?|create[sd]?)\b|產生|生成", re.I)
_PROPOSAL = re.compile(r"\b(?:can|could|should|would)\b|能不能|可以|是否|應該", re.I)
_PATIENT_CLUSTER = re.compile(
    r"\b(?:cluster\w*|group\w*|subtyp\w*)\s+(?:the\s+|cancer\s+)?patients?\b|"
    r"\bpatients?\b.{0,30}\b(?:cluster\w*|subtyp\w*|subgroups?)\b|"
    r"(?:病患|病人|患者|樣本).{0,40}(?:分群|分組|亞型)|"
    r"(?:分群|分組).{0,10}(?:病患|病人|患者)", re.I,
)
_GOAL_NEGATED = re.compile(r"\b(?:not|no|without)\b|不要|不做|不需要|不進行", re.I)


# A request that asks which method fits, or whether a named one does, is asking
# for guidance. `unknown` is for a request that takes no position at all, and
# `execute` needs an instruction to work now -- reporting a finished run is not
# one, so historical clauses are excluded the same way they are for data.
_METHOD_QUESTION = re.compile(
    r"哪(?:一)?(?:個|些|種)|有沒有|該不該|是不是.{0,8}(?:應該|可以)|推薦|建議|"
    r"(?:應該|可以|可不可以|能不能|適(?:合|用)).{0,12}(?:用|使用|丟進|交給|處理|分析)|"
    r"\bwhich (?:tool|workflow|method|package)\b|\bwhat tool\b|"
    r"\bshould i\b|\bcan i (?:use|feed|apply)\b|\bis .{0,20}(?:suitable|appropriate)\b|"
    r"\bdo i need\b|\bhow (?:do|should) i\b|\bwhat (?:is|are) the (?:steps|options)\b|"
    r"\brecommend\b|\badvice\b|\bdoes .{0,60}(?:produce|support|accept)\b|"
    r"\bcan .{0,40}(?:produce|handle|accept)\b",
    re.I,
)
_EXECUTE_INSTRUCTION = re.compile(
    r"幫我(?:跑|執行|做|建立)|請(?:執行|跑|建立)|現在(?:就)?(?:跑|執行|開始)|"
    r"開始(?:執行|分析|跑)|\b(?:please )?run (?:it|this|the|sambar|panda|lioness)\b|"
    r"\bexecute\b|\bstart the (?:analysis|run|pipeline)\b|\bbuild (?:it|the) .{0,20}now\b",
    re.I,
)
# "Do not run it" is the opposite of a work order, and appears in prompts that
# state a goal and then withhold authorization.
_INSTRUCTION_NEGATED = re.compile(
    r"不要|不用|不需要|別|請勿|\bdo(?:n't| not)\b|\bnever\b|\bwithout\b", re.I
)


@dataclass(frozen=True)
class InputMention:
    artifact: str
    status: str
    text_span: str


def _scoped_clauses(task: str):
    """A comma alone does not end a historical scope."""
    for sentence in re.split(r"[。！？!?;；\n]|\.(?:\s|$)", task):
        scope = "current"
        for clause in re.split(r"[,，]|(?=\b(?:now|currently|but)\b|現在|目前|但現在)", sentence, flags=re.I):
            if _HISTORY.search(clause):
                scope = "historical"
            elif _CURRENT.search(clause):
                scope = "current"
            yield clause, scope


def input_mentions(task: str) -> tuple[InputMention, ...]:
    """Retain temporal scope across comma clauses, resetting at sentence ends."""
    mentions = []
    for clause, scope in _scoped_clauses(task):
        for artifact, pattern in INPUT_PATTERNS.items():
            for match in re.finditer(pattern, clause, re.I):
                prefix = clause[:match.start()]
                status = scope
                if _UNCERTAIN.search(prefix):
                    status = "uncertain"
                elif _NEGATED.search(prefix):
                    status = "negated"
                elif _OUTPUT.search(prefix):
                    status = "proposed_output"
                elif _PROPOSAL.search(prefix) and not _CURRENT.search(prefix):
                    status = "uncertain"
                mentions.append(InputMention(artifact, status, match.group()))
    return tuple(mentions)


def execution_instruction(task: str) -> bool:
    """Report an instruction to work now, ignoring runs the user already did."""
    for clause, scope in _scoped_clauses(task):
        if scope == "historical":
            continue
        match = _EXECUTE_INSTRUCTION.search(clause)
        if match and not _INSTRUCTION_NEGATED.search(clause[:match.end()]):
            return True
    return False


def guidance_request(task: str) -> bool:
    """Report a request that asks about methods without ordering the work."""
    return bool(_METHOD_QUESTION.search(task)) and not execution_instruction(task)


def request_mode_issues(task: str, request_mode: str | None) -> list[str]:
    """Flag a request_mode the request's own wording does not support."""
    if request_mode in {None, "guidance"} or not guidance_request(task):
        return []
    return ["request_mode_conflict:guidance"]


def request_integrity_issues(task: str, outcome) -> list[str]:
    mentions = input_mentions(task)
    current = {m.artifact for m in mentions if m.status == "current"}
    noncurrent = {m.artifact for m in mentions if m.status != "current"} - current
    supplied = set(outcome.input_artifacts)
    issues = (
        [f"missing_current_input:{artifact}" for artifact in sorted(current - supplied)]
        + [f"noncurrent_input:{artifact}" for artifact in sorted(noncurrent & supplied)]
    )
    if patient_clustering_goal(task) and outcome.artifact_type != "sample_cluster_assignment":
        issues.append("terminal_goal_conflict:sample_cluster_assignment")
    return issues


def patient_clustering_goal(task: str) -> bool:
    """Recognize explicit patient grouping, excluding history and negated goals.

    Do not infer a network type or choose an intermediate distance artifact.
    Unrecognized or competing goals remain the semantic reviewer's responsibility.
    """
    for clause, scope in _scoped_clauses(task):
        if scope == "historical":
            continue
        for match in _PATIENT_CLUSTER.finditer(clause):
            if not _GOAL_NEGATED.search(clause[:match.end()]):
                return True
    return False
