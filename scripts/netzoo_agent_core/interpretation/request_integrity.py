"""Bounded text checks for omitted request facts, never automatic field repair.

These lexical witnesses are deliberately independent of workflow names and of
the model's filled fields. They are not a complete natural-language parser.
"""
from dataclasses import dataclass
import re

from ..contracts.artifact_semantics import (
    ARTIFACT_SEMANTICS,
    is_outcome_not_applicable,
)
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
_CURRENT = re.compile(
    r"\b(?:now|currently|current|have|received|this time|this request|this analysis)\b"
    r"|現在|目前|手邊|這份|我有|拿到|給了我|這次|本次|這回|此次",
    re.I,
)
# 也許 / 或許 are the direct equivalents of `might`; the broader 可能 is left
# out because it also frames ordinary questions (是否可能).
_UNCERTAIN = re.compile(r"\b(?:if|hypothetical|might|would obtain|could obtain)\b|假如|假設|如果|尚未|還沒有|也許|或許", re.I)
# `不需要` / `不要` / `不用` / `無需` decline a result the way `not` does. Without
# them “不需要每位病患各自的網路” was read as a *stated* sample-specific request,
# so an explicit aggregate request carried both granularities and lost its
# witness.
_NEGATED = re.compile(r"\b(?:not|without|no)\b|不是|並非|沒有|不含|不需要|不要|不用|無需", re.I)
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
_EXPLICIT_ADVICE_INTENT = re.compile(
    r"\b(?:advice|advise|recommend(?:ed|s|ing|ation|ations)?|"
    r"suggest(?:ed|s|ing|ion|ions)?)\b|建議|推薦|諮詢",
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
    r"(?P<regulator>\bTFs?\b|\btranscription[- ]factors?\b|"
    r"\bmi(?:cro)?[- ]?RNAs?\b|\bmiR\b|微小核糖核酸|微小RNA|微RNA|轉錄因子)"
    r"(?:\s*(?:-|–|—)?\s*to\s*(?:-|–|—)?\s*|\s*(?:->|[-–—→])\s*|"
    r"\s*(?:regulat(?:e|es|ing)|如何調控|調控|作用於|對)\s*"
    # “microRNAs regulate their target genes” states the same bounded role
    # as “microRNA-to-gene”; keep the possessive target phrase attached to
    # this regulator instead of treating it as an unpaired role mention.
    r"(?:\b(?:their|its|the)\s+target\s+)?|"
    # The noun form: “TF regulation of genes”. Missing it let “both miRNA and
    # TF regulation of genes” reach DRAGON as an exact legacy answer.
    r"\s+regulation\s+of\s+)"
    r"(?P<target>\bgenes?\b|基因)",
    re.I,
)
_COORDINATED_REGULATORY_ROLE_PAIR = re.compile(
    r"\bboth\s+(?P<first>\bTFs?\b|\btranscription\s+factors?\b|"
    r"\bmi(?:cro)?[- ]?RNAs?\b)\s+and\s+"
    r"(?P<second>\bTFs?\b|\btranscription\s+factors?\b|"
    r"\bmi(?:cro)?[- ]?RNAs?\b)\s+regulation\s+of\s+(?P<target>\bgenes?\b)",
    re.I,
)
_GRANULARITY_PATTERNS = {
    "aggregate": re.compile(
        r"\b(?:aggregate|cohort[- ]wide|cohort[- ]level|population[- ]level)\b|"
        r"\b(?:one|single|shared|common)\s+cohort\s+networks?\b|"
        r"\b(?:one|single|shared|common)\s+(?:[\w-]+\s+){0,5}network\s+"
        r"for\s+(?:the\s+)?(?:whole|entire)\s+(?:cohort|population)\b|"
        r"\b(?:one|single|shared|common)\s+(?:cohort[- ]wide\s+)?network\s+"
        r"(?:shared\s+)?(?:across|for)\s+(?:the\s+)?(?:whole|entire)\s+cohort\b|"
        r"\bshared\s+(?:cohort[- ]wide\s+)?networks?\s+across\s+"
        r"(?:the\s+)?(?:(?:whole|entire|all)\s+)?(?:cohort|population|patients?|samples?)\b|"
        r"\b(?:one|single)\s+(?:[\w-]+\s+){0,3}network\s+shared\s+across\s+"
        r"(?:the\s+)?(?:whole|entire)\s+(?:cohort|population)\b|"
        # Chinese witnesses must reach a network noun, as every English one
        # does: bare 整體 matched “整體突變負荷量” (overall mutation burden), and
        # 單一 matched “單一樣本網路”, which is a single-*sample* network.
        r"(?:整體|群體|族群)(?:層級|層次)|"
        r"(?:整體|群體|族群)(?:的)?[^。！？!?;；\n，,]{0,8}(?:網路|網絡)|"
        r"(?:整群|全體|所有)(?:的)?(?:病患|病人|患者|樣本)?"
        r"[^。！？!?;；\n]{0,18}(?:共用|共同|合併|單一)(?:的)?"
        r"[^。！？!?;；\n]{0,18}網路|"
        r"(?:單一(?!(?:的)?(?:樣本|病患|病人|患者|個體))|共用|共同|合併成?)(?:的)?"
        r"(?:整體|群體|族群|全體|整群)?(?:病患|病人|患者|樣本)?"
        r"[^。！？!?;；\n]{0,16}網路",
        re.I,
    ),
    "sample_specific": re.compile(
        # Keep per-unit language attached to the output network. A phrase such
        # as “per-patient expression matrices” is an input description, not a
        # request for one network per patient.
        r"\b(?:sample|patient|subject)[- ]specific\s+(?:[\w-]+\s+){0,5}networks?\b|"
        r"\bper[- ](?:sample|patient|subject|person|individual)\s+"
        r"(?:[\w<>/→-]+\s+){0,4}networks?\b|"
        r"\b(?:separate|independently\s+estimated)\s+(?:[\w-]+\s+){0,3}networks?\s+"
        r"for\s+(?:each|every)\s+(?:sample|patient|subject|person|individual)s?\b|"
        r"\b(?:a\s+)?(?:separate|individual)\s+(?:[\w-]+\s+){0,6}networks?\s+"
        r"for\s+(?:each|every)\s+(?:individual\s+)?(?:sample|patient|subject)s?\b|"
        r"\b(?:one|a)\s+(?:(?:separate|independently|separately)\s+)?"
        r"(?:[\w-]+\s+){0,5}network\s+"
        r"(?:per\s+(?:sample|patient|subject)|for\s+(?:each|every)\s+"
        r"(?:individual\s+)?(?:sample|patient|subject)s?)\b|"
        # Also cover “for each individual ... their own network” and clauses
        # that state the per-patient relation with a verb instead of naming a
        # network noun (“estimate ... regulation ... separately in each
        # patient”).
        r"\bfor\s+(?:each|every)\s+(?:individual\s+)?"
        r"(?:sample|patient|subject|person|individual)\b[^.;!?]{0,100}"
        r"\b(?:their|its|one's)\s+own"
        r"(?:\s+(?!and\b|but\b|then\b|while\b)[\w-]+){0,7}\s+networks?\b|"
        r"\b(?:estimat\w*|infer\w*|construct\w*|build\w*|learn\w*)\b"
        r"[^.;!?]{0,120}\b(?:network\w*|regulat\w*|interaction\w*)\b"
        r"[^.;!?]{0,80}\bseparately\s+in\s+each\s+"
        r"(?:individual\s+)?(?:sample|patient|subject|person)\b|"
        r"\bnetworks?\s+(?:(?:estimated|inferred|constructed|built)\s+)?"
        r"for\s+(?:each|every)\s+(?:individual\s+)?"
        r"(?:sample|patient|subject|person|individual)s?\b|"
        # "The wiring differs from one patient to the next" states separate
        # network results even when the user calls the output a picture rather
        # than repeating the noun "network".
        r"\b(?:network\w*|wiring|edges?|links?)\b"
        r"[^.;!?]{0,120}\b(?:differ\w*|vary\w*|change\w*)\b"
        r"[^.;!?]{0,60}\bfrom one (?:sample|patient|subject|individual) "
        r"to (?:the )?next\b|"
        # Bound to a network noun in the same clause: “每個樣本狀態的 TFA 矩陣”
        # describes a per-sample matrix beside one aggregate network.
        r"(?:每(?:一)?(?:個|位)|各個|逐一|每位|各位)"
        r"(?:樣本|病患|病人|患者)(?:各自|個別|分別)?"
        r"[^。！？!?;；\n，,]{0,20}(?:網路|網絡)",
        re.I,
    ),
}


# A request that names both granularities while saying it has not chosen one.
# Each part is required in the same sentence, so "not sure which tool" alone,
# or a sentence naming one granularity, never qualifies.
_UNDECIDED = re.compile(
    r"\b(?:not|haven't|hasn't|have\s+not|has\s+not)\s+(?:yet\s+)?decided\b|"
    r"\bundecided\b|\bnot\s+sure\s+(?:whether|if)\b|"
    r"還沒(?:有)?決定|尚未決定|不確定(?:要|是)",
    re.I,
)
_AGGREGATE_ALTERNATIVE = re.compile(
    r"\bcohort\b|\baggregate\b|\bshared\b|\bone\s+(?:[\w-]+\s+){0,3}network\b|"
    r"整群|群體|共用|整體",
    re.I,
)
_SAMPLE_ALTERNATIVE = re.compile(
    r"\bper[- ](?:sample|patient|subject|person|individual)\b|"
    r"\b(?:each|every)\s+(?:sample|patient|subject|person|individual)\b|"
    r"\bsample[- ]specific\b|每位|每個|各自",
    re.I,
)
#: Network artifacts with no regulator or target roles. A stated
#: regulator-to-target relation cannot be carried by them, so choosing one
#: discards what the request said; a partition of a regulatory network
#: (`community_assignment`) is a different deliverable and is not listed.
_ROLELESS_NETWORKS = frozenset({"coexpression_network", "multi_omic_network"})
_REGULATORY_WITH_ENTITY_RULE = frozenset({
    "regulatory_network_and_tf_activity", "signed_regulatory_effect_network",
})


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


@dataclass(frozen=True)
class GranularityMention:
    granularity: str
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
        coordinated = []
        for match in _COORDINATED_REGULATORY_ROLE_PAIR.finditer(clause):
            if _NEGATED.search(clause[:match.start()]):
                continue
            coordinated.append(match.span())
            for group in ("first", "second"):
                regulator = _normalize_regulator(match.group(group))
                mentions.append(RegulatoryRoleMention(
                    regulator_type=regulator,
                    target_type="gene",
                    entity_types=(regulator, "gene"),
                    text_span=match.group(0),
                ))
        for match in _REGULATORY_ROLE_PAIR.finditer(clause):
            if any(start <= match.start() and match.end() <= end for start, end in coordinated):
                continue
            if _NEGATED.search(clause[:match.start()]):
                continue
            regulator = _normalize_regulator(match.group("regulator"))
            mentions.append(RegulatoryRoleMention(
                regulator_type=regulator,
                target_type="gene",
                entity_types=(regulator, "gene"),
                text_span=match.group(0),
            ))
    return tuple(mentions)


def _normalize_regulator(regulator_text: str) -> str:
    regulator_text = regulator_text.casefold()
    return "tf" if (
        regulator_text.startswith("tf")
        or regulator_text.startswith("transcription")
        or regulator_text == "轉錄因子"
    ) else "mirna"


def granularity_mentions(task: str) -> tuple[GranularityMention, ...]:
    """Return explicit, current output-granularity phrases.

    These witnesses only quote a closed vocabulary value already present in
    the request.  They do not infer granularity from a workflow name, input
    shape, or conversational candidate.
    """
    mentions = []
    for clause, scope in _scoped_clauses(task):
        if scope != "current":
            continue
        for granularity, pattern in _GRANULARITY_PATTERNS.items():
            for match in pattern.finditer(clause):
                negative = _NEGATED.search(clause[:match.start()])
                if negative:
                    # In "not decided between aggregate and sample-specific,"
                    # not negates the decision, not either alternative.
                    undecided = _UNDECIDED.search(clause)
                    if not (
                        undecided
                        and undecided.start() <= negative.start()
                        and negative.end() <= undecided.end()
                    ):
                        continue
                mentions.append(GranularityMention(
                    granularity=granularity,
                    text_span=match.group(0),
                ))
    return tuple(mentions)


def confirmed_current_inputs(task: str) -> set[str]:
    """Return the artifacts these witnesses locate in the request as current."""
    return {item.artifact for item in input_mentions(task) if item.status == "current"}


def has_explicit_advice_intent(task: str) -> bool:
    """Whether the request explicitly asks for advice or a recommendation."""
    return _EXPLICIT_ADVICE_INTENT.search(task) is not None


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
    # Current inputs are required when the outcome describes a scientific
    # result. A no-result explanation can mention available data without
    # requesting a workflow; requiring its inputs here would turn the coherent
    # `explain / unknown / not_applicable` outcome into an impossible repair:
    # adding the input itself makes that outcome inconsistent.
    missing_current = (
        [] if is_outcome_not_applicable(outcome)
        else [Issue(f"missing_current_input:{artifact}", {"input_artifacts"})
              for artifact in sorted(current - supplied)]
    )
    # Both input rules compare the request's witnesses against one field.
    issues = (
        missing_current
        + [Issue(f"noncurrent_input:{artifact}", {"input_artifacts"})
           for artifact in sorted(noncurrent & supplied)]
    )
    stated_roles = regulatory_role_mentions(task)
    entity_rule = ARTIFACT_SEMANTICS[outcome.artifact_type].entities
    if stated_roles and (
        outcome.artifact_type in _ROLELESS_NETWORKS
        # A regulatory artifact whose ontology excludes a stated regulator: the
        # TF-activity product has no miRNA, so restoration's attempt to add the
        # stated miRNA role was refused and the role vanished without a trace.
        or (
            outcome.artifact_type in _REGULATORY_WITH_ENTITY_RULE
            and entity_rule is not None
            and any(item.regulator_type not in entity_rule for item in stated_roles)
        )
    ):
        # Traced 2026-09-23: “miRNA-gene network” and “both miRNA and TF
        # regulation of genes” read as multi-omic networks lost their roles in
        # restoration, and the review then deleted the conflicting evidence, so
        # DRAGON was recommended -- as fallback in claims, as exact in legacy.
        issues.append(Issue(
            f"stated_roles_conflict:{outcome.artifact_type}", {"artifact_type"},
        ))
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
            # A supposed goal is not the current one, exactly as a supposed
            # input is not a current input in `input_mentions`. “If I later
            # obtain somatic mutation data I might cluster patients, but right
            # now … a separate TF-to-gene network for each sample” forced a
            # clustering artifact onto the network request in all six traced
            # trials of both contracts.
            if _UNCERTAIN.search(clause[:match.start()]):
                continue
            if not _GOAL_NEGATED.search(clause[:match.end()]):
                return True
    return False


def granularity_left_open(task: str) -> bool:
    """Whether one sentence names both granularities and says neither is chosen."""
    return any(
        _UNDECIDED.search(sentence)
        and _AGGREGATE_ALTERNATIVE.search(sentence)
        and _SAMPLE_ALTERNATIVE.search(sentence)
        for sentence in re.split(r"[。！？!?;；\n]|\.(?:\s|$)", task)
    )
