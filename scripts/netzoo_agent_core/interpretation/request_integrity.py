"""Bounded text checks for omitted request facts, never automatic field repair.

These lexical witnesses are deliberately independent of workflow names and of
the model's filled fields. They are not a complete natural-language parser.
"""
from dataclasses import dataclass
import re

from ..contracts.repair_scope import Issue


INPUT_PATTERNS = {
    # An exome assay named together with a dataset noun is the mutation matrix a
    # live round expected and the witnesses did not see, leaving the right tool
    # with no declared input. The assay name alone is not enough: "raw WES FASTQ
    # reads" is sequencing output, not a mutation matrix, and a bare \bWES\b
    # claimed it. Vocabulary only; scope is still decided by the clause rules.
    "mutation_matrix": r"\bsomatic mutations?\b|\bmutation (?:matrix|counts)\b|"
                       r"\bWES\s*(?:資料|矩陣)|全外顯子[^,，。]{0,6}(?:資料|矩陣)|"
                       r"\bwhole[- ]exome\b[^.]{0,20}\b(?:mutation|variant)s?\b|"
                       r"DNA\s*突變(?:資料|矩陣)|體細胞突變|突變矩陣",
    "expression_matrix": r"\bRNA[- ]?Seq\b|\b(?:gene )?expression (?:matrix|data|dataset)\b|"
                         r"(?:基因)?表現量?(?:矩陣|資料)",
}
_INPUT_EVIDENCE_PATTERNS = {
    **INPUT_PATTERNS,
    # These aliases validate only the meaning of an evidence quote. They do not
    # expand the temporal input witness above, whose deliberately small surface
    # is pinned by spelling and history corpus tests.
    "expression_matrix": INPUT_PATTERNS["expression_matrix"]
                         + r"|\bexpression\b(?=\s*[,，]|\s+inputs?\b)",
    "motif_prior": r"\b(?:TF[- ]?)?motifs?\b(?:\s+(?:priors?|data|file|matrix|inputs?)\b)?|"
                   r"(?:TF[- ]?)?motif[^。！？!?;；\n]{0,12}先驗",
    "ppi_prior": r"\bPPI\b(?:\s+(?:priors?|data|matrix|file|inputs?)\b)?|"
                 r"\bprotein[- ]protein interaction(?:s|\s+(?:priors?|data|matrix|file|inputs?))?\b|"
                 r"(?:蛋白質交互作用|蛋白質互作)[^。！？!?;；\n]{0,12}(?:先驗|資料|矩陣)?",
}
# Completion is bound to a verb, never to a bare adverb. Scope is decided per
# clause and a history hit overrides a current hit in the same clause, so a bare
# `already` would read "I already have an expression matrix" as history and make
# a declared current input vanish -- this module's scoping is shared with
# `input_mentions`. "I already finished my PANDA run last month" carried none of
# the original markers and was read as a live request to run PANDA.
_HISTORY = re.compile(
    r"\b(?:previously|historical|earlier|past|old)\b"
    r"|\b(?:already|just)\s+(?:ran|run|did|done|finished|completed|performed)\b"
    r"|\b(?:finished|completed)\s+(?:my|our|the|a|an)\b"
    r"|\blast\s+(?:week|month|year|time)\b"
    r"|\bused to\b"
    r"|曾經|之前|先前|過去|剛剛|跑完|上次|當初|已經(?:跑|做|執行|完成|用)",
    re.I,
)
_CURRENT = re.compile(r"\b(?:now|currently|current|have|received)\b|現在|目前|手邊|這份|我有|拿到|給了我", re.I)
_UNCERTAIN = re.compile(r"\b(?:if|hypothetical|might|would obtain|could obtain)\b|假如|假設|如果|尚未|還沒有", re.I)
_NEGATED = re.compile(r"\b(?:not|without|no)\b|不是|並非|沒有|不含", re.I)
_OUTPUT = re.compile(r"\b(?:produce[sd]?|generate[sd]?|create[sd]?)\b|產生|生成", re.I)
_PROPOSAL = re.compile(r"\b(?:can|could|should|would)\b|能不能|可以|是否|應該", re.I)
# A modal that governs "which tool do you recommend" is asking about the tool,
# not supposing the data. Without this, "Which workflow would you recommend ...
# from somatic mutation counts?" scoped its own dataset as hypothetical, and the
# run named the right tool while declaring no input at all.
_REQUEST_FRAMING = re.compile(
    r"\b(?:recommend|suggest)\b|\b(?:which|what)\s+(?:workflow|tool|method|pipeline)\b|"
    r"建議|推薦|哪(?:一)?(?:項|個|種)",
    re.I,
)
_PATIENT_CLUSTER = re.compile(
    r"\b(?:cluster\w*|group\w*|subtyp\w*)\s+(?:the\s+|cancer\s+)?patients?\b|"
    r"\bpatients?\b.{0,30}\b(?:cluster\w*|subtyp\w*|subgroups?)\b|"
    r"(?:病患|病人|患者|樣本).{0,40}(?:分群|分組|亞型)|"
    r"(?:分群|分組).{0,10}(?:病患|病人|患者)", re.I,
)
_GOAL_NEGATED = re.compile(r"\b(?:not|no|without)\b|不要|不做|不需要|不進行", re.I)
_REGULATORY_ROLE_PAIR = re.compile(
    r"\b(?P<regulator>TFs?|transcription\s+factors?|mi(?:cro)?[- ]?RNAs?)\b"
    r"(?:\s*(?:-|–|—)?\s*to\s*(?:-|–|—)?\s*|\s*(?:-|–|—|→)\s*)"
    r"(?P<target>genes?)\b",
    re.I,
)


@dataclass(frozen=True)
class InputMention:
    artifact: str
    status: str
    text_span: str


@dataclass(frozen=True)
class RegulatoryRoleMention:
    regulator_type: str
    target_type: str
    entity_types: tuple[str, str]
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
                elif (
                    _PROPOSAL.search(prefix)
                    and not _CURRENT.search(prefix)
                    and not _REQUEST_FRAMING.search(prefix)
                ):
                    status = "uncertain"
                mentions.append(InputMention(artifact, status, match.group()))
    return tuple(mentions)


def regulatory_role_mentions(task: str) -> tuple[RegulatoryRoleMention, ...]:
    """Return only explicit current regulator-to-target role phrases."""
    mentions = []
    for clause, scope in _scoped_clauses(task):
        if scope != "current":
            continue
        for match in _REGULATORY_ROLE_PAIR.finditer(clause):
            if _NEGATED.search(clause[:match.start()]):
                continue
            regulator_text = match.group("regulator").casefold()
            regulator = "tf" if (
                regulator_text.startswith("tf")
                or regulator_text.startswith("transcription")
            ) else "mirna"
            mentions.append(RegulatoryRoleMention(
                regulator_type=regulator,
                target_type="gene",
                entity_types=(regulator, "gene"),
                text_span=match.group(0),
            ))
    return tuple(mentions)


def confirmed_current_inputs(task: str) -> set[str]:
    """Return the artifacts these witnesses locate in the request as current."""
    return {item.artifact for item in input_mentions(task) if item.status == "current"}


def canonical_input_artifacts_in_text(text: str) -> frozenset[str]:
    """Map known input words in one evidence quote to canonical artifacts."""
    return frozenset(
        artifact
        for artifact, pattern in _INPUT_EVIDENCE_PATTERNS.items()
        if re.search(pattern, text, re.I)
    )


def request_integrity_issues(task: str, outcome) -> list[str]:
    mentions = input_mentions(task)
    current = {m.artifact for m in mentions if m.status == "current"}
    noncurrent = {m.artifact for m in mentions if m.status != "current"} - current
    supplied = set(outcome.input_artifacts)
    # Both input rules compared the request's witnesses against one field.
    issues = (
        [Issue(f"missing_current_input:{artifact}", {"input_artifacts"})
         for artifact in sorted(current - supplied)]
        + [Issue(f"noncurrent_input:{artifact}", {"input_artifacts"})
           for artifact in sorted(noncurrent & supplied)]
    )
    if patient_clustering_goal(task) and outcome.artifact_type != "sample_cluster_assignment":
        # Read `artifact_type` only. What the corrected artifact then constrains
        # is opened by the ontology at merge time, not listed here.
        issues.append(Issue(
            "terminal_goal_conflict:sample_cluster_assignment", {"artifact_type"},
        ))
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
