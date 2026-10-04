"""The comparison design and the kind of conclusion a request states (Log 342).

Log 341 (minimal pairs): with the data fixed and only the purpose sentence
changed, "does the regulatory network change after treatment across the
cohort?" got the same reply as the control "one network summarizing all 48
samples". The interpreter quoted the purpose sentence, but no typed field
carried it, so nothing downstream could use it: no comparison step, no word
that a pre/post design cannot show causation, and "predict whether a new
patient will respond" ended in semantic_fallback.

This module reads both facts from the request's own words, never from a
model: Log 341's condition recommender quoted the goal sentence for any
offered option, the A0 control included. No witness means None, and None
leaves every reply as it was. A witness in a clause that negates it ("This is
not causal", "we are not trying to predict") does not count. A number is no
witness ("24 patients" states no design).

Log 346 (PN): a conclusion is also negated by the rest of its own clause --
"Predicting relapse isn't the point; we want to see whose networks changed
most" read as a prediction request. Only conclusions: the design is what the
data are, and the user negates what to conclude from them.

Log 350 (CN): "cause" as a noun names a variable ("a donor table giving ...
cause of death") unless a verb asks for the cause ("identify the cause of").

Pure: nothing here selects, ranks or removes a workflow.
"""

from __future__ import annotations

import re
from typing import Literal, NamedTuple

__all__ = ["StudyPurpose", "study_purpose", "timepoint_count"]

Design = Literal["paired", "groups"]
Claim = Literal["group_difference", "individual_change", "regulator_change", "causal", "prediction"]

_I = re.I
_SUBJECTS = r"(?:patients?|individuals?|subjects?|donors?|participants?|mice|mouse|animals?|rats?|volunteers?|people|persons?)"
_EVENT = (
    r"(?:treatment|therapy|drug|dosing|exposure|infection|vaccination|surgery|resection|intervention|"
    r"stimulation|challenge|transplant\w*|chemotherapy|immunotherapy|radiotherapy|diet|training|"
    r"knock\w*|operation|operative|induction|administration)"
)

# Same individuals measured more than once.
_PAIRED = re.compile(
    r"\bbefore\s+and\s+(?:again\s+)?after\b|\bafter\s+and\s+before\b"
    r"|\bpre-?\s*(?:and|/|vs\.?|versus|or)\s*post-?\b"
    r"|\bpre-?" + _EVENT + r"\b.{0,80}\bpost-?" + _EVENT + r"\b"
    r"|\bat\s+baseline\s+and\s+(?:again\s+)?(?:after|at|on|following)\b"
    # "Three time points" alone is not pairing: mice are often sacrificed per time
    # point. Longitudinal and serial sampling are of the same individuals.
    r"|\blongitudinal(?:ly)?\b|\bserial(?:ly)?\s+(?:sampl\w*|biops\w*|collected|measured|specimens?|blood)\b"
    r"|\brepeated(?:ly)?\s+(?:sampl\w*|measur\w*|biops\w*|profil\w*)\b"
    # "Paired" alone often means two omics layers from the same samples ("150 paired
    # tumor samples" with mRNA and miRNA, a real session): it needs a time word.
    r"|\bpaired\s+(?:[\w-]+\s+){0,3}?(?:pre|post|before|after|baseline|time\s?points?|longitudinal)\b"
    r"|\bpaired\s+(?:design|pre-?\s*/\s*post)\b"
    r"|\bmatched\s+(?:pre|post|before|samples?\s+from\s+the\s+same|tumou?r[- ]normal|(?:adjacent\s+)?normal)\b"
    r"|\b(?:tumou?rs?|cancers?)\s+and\s+(?:their\s+|its\s+)?(?:paired\s+|matched\s+|adjacent\s+)normal\b[^.;]{0,40}\b(?:from|of|in)\s+(?:the\s+same|each|every)\b"
    r"|\b(?:each|every|the\s+same)\s+(?:patient|individual|subject|donor|participant|mouse|animal|rat|volunteer)s?\b"
    r"[^.;]{0,60}\b(?:sampled|biopsied|measured|profiled|sequenced|collected)\b[^.;]{0,40}"
    r"\b(?:before|after|twice|again|at\s+(?:two|three|four|\d+)|on\s+days?|weeks?\s+\d|over\s+time)\b"
    r"|\bthe\s+same\s+" + _SUBJECTS + r"\b[^.;]{0,60}\b(?:before|after|over\s+time|at\s+(?:two|three|\d+)\s+time)",
    _I,
)

# Different individuals in two or more groups.
_GROUP_NOUN = (
    r"(?:responders?|non-?responders?|cases?|controls?|healthy|patients?|tumou?rs?|normals?|"
    r"treated|untreated|exposed|unexposed|knock-?outs?|wild[- ]types?|mutants?|carriers?|non-?carriers?|"
    r"males?|females?|men|women|smokers?|non-?smokers?|survivors?|non-?survivors?|resistant|sensitive|"
    r"diseased|disease|benign|malignant|metastatic|primary|relapsed?|remission|groups?|cohorts?|arms?)"
)
_GROUPS = re.compile(
    r"\bnon-?responders?\b|\bresponders?\s+(?:and|vs\.?|versus|or)\s+non\b"
    r"|\bcases?\s+(?:and|vs\.?|versus)\s+(?:healthy\s+)?controls?\b|\bcase[- ]control\b"
    r"|\b(?:patients|cases)\s+(?:and|vs\.?|versus)\s+(?:healthy\s+|matched\s+)?(?:controls?|donors?|volunteers?)\b"
    r"|\bhealthy\s+(?:controls?|donors?|volunteers?|individuals?|subjects?)\b"
    r"|\b(?:two|three|four|\d+)\s+(?:groups|cohorts|arms|conditions)\b"
    r"|\b(?:between|across)\s+(?:the\s+)?(?:two|three|four|\d+|treatment|study|experimental|patient)\s+(?:groups|cohorts|arms|conditions)\b"
    r"|\b(?:males?\s+(?:and|vs\.?|versus)\s+females?|females?\s+(?:and|vs\.?|versus)\s+males?|men\s+and\s+women|women\s+and\s+men)\b"
    r"|\b(?:smokers?\s+(?:and|vs\.?|versus)\s+non-?smokers?)\b"
    r"|\b(?:treated|exposed|knock-?out|mutant|infected|diseased)\s+(?:\w+\s+)?(?:and|vs\.?|versus)\s+"
    r"(?:untreated|unexposed|control|wild[- ]type|uninfected|mock|healthy|vehicle)\b"
    r"|\b(?:tumou?rs?|cancers?)\s+(?:samples?\s+)?(?:and|vs\.?|versus)\s+(?:adjacent\s+)?normal\b"
    r"|\b" + _GROUP_NOUN + r"\s+(?:vs\.?|versus)\s+" + _GROUP_NOUN + r"\b",
    _I,
)

# The kind of conclusion. Tried in this order; the first is the primary claim.
# "respond" is left out: "30 from immunotherapy responders" states a group, not a change.
_CHANGE = r"(?:chang\w*|differ\w*|shift\w*|alter\w*|rewir\w*|gain\w*|los[et]\w*|switch\w*|reprogramm\w*|perturb\w*|diverg\w*)"
# A population-level scope. "Whether the patients' gene regulation changes after
# treatment" (Log 340 A5, the user's own example) names none: it may mean the
# cohort, each patient or the regulators, so it stays unknown and is asked.
_POPULATION = (
    r"(?:across|in|for|over)\s+(?:the\s+)?(?:whole\s+|entire\s+)?(?:cohort|population|group|study\s+population)\b"
    r"|\boverall\b|\bon\s+average\b|\bat\s+the\s+(?:group|cohort|population)\s+level\b|\bas\s+a\s+(?:whole|group)\b"
    r"|\bgroup[- ]level\b|\bpopulation[- ]level\b|\bcohort[- ]level\b"
)
_CLAIMS: tuple[tuple[Claim, re.Pattern[str]], ...] = (
    ("causal", re.compile(
        r"\bcaus(?:e|es|ed|ing|al|ally|ality|ation|ative)\b"
        r"|\bresponsible\s+for\b"
        r"|\b(?:prove|establish|demonstrate)\s+(?:that\s+)?[^.;]{0,80}\b(?:leads?\s+to|results?\s+in|induces?|triggers?|drives?)\b",
        _I,
    )),
    ("prediction", re.compile(
        r"\bpredict(?:s|ing|ion|ions|ive|or|ors)?\b(?!\s+(?:targets?|binding|sites?|motifs?|interactions?))"
        r"|\bclassifier\b|\bprognostic\s+(?:model|signature|score|tool)\b|\brisk\s+(?:score|model)\b|\bforecast\w*\b",
        _I,
    )),
    ("individual_change", re.compile(
        # "Which patients belong to which subtype" is a grouping, not a change.
        r"\bwhich\s+(?:of\s+the\s+)?(?:individual\s+)?" + _SUBJECTS + r"\b[^.;?]{0,60}\b(?:" + _CHANGE + r"|most|largest|"
        r"strongest|biggest|greatest|outliers?|unusual|deviat\w*|stand\s+out)\b"
        r"|\b" + _SUBJECTS + r"\s+whose\b[^.;?]{0,60}\b(?:" + _CHANGE + r"|most|largest|outliers?|unusual|deviat\w*)\b"
        r"|\b(?:patient|individual|subject|donor|per-patient|per-individual)[- ](?:level|specific)\s+(?:changes?|differences?|responses?|rewiring|shifts?)\b"
        r"|\bin\s+(?:their|its)\s+own\s+(?:regulatory\s+)?(?:network|wiring|regulation)\b",
        _I,
    )),
    ("regulator_change", re.compile(
        r"\b(?:which|what)\s+(?:key\s+)?(?:transcription\s+factors?|TFs?|regulators?|micro-?RNAs?|miRNAs?)\b[^.;?]{0,80}\b" + _CHANGE
        + r"|\b(?:transcription\s+factors?|TFs?|regulators?|micro-?RNAs?|miRNAs?)\s+(?:that|whose|which)\b[^.;?]{0,60}\b" + _CHANGE
        + r"|\bdifferential(?:ly)?\s+(?:targeting|targeted|activ\w*|regulat\w*\s+(?:TFs?|transcription\s+factors?|regulators?))\b"
        r"|\bkey\s+(?:transcription\s+factors?|TFs?|regulators?)\s+(?:between|that\s+distinguish|underlying|driving)\b",
        _I,
    )),
    ("group_difference", re.compile(
        r"\b" + _CHANGE + r"\b[^.;?]{0,40}\b(?:between|among)\b"
        r"|\bcompar\w*\b[^.;?]{0,60}\b(?:between|against|versus|vs\.?)\b"
        r"|\b" + _CHANGE + r"\b[^.;?]{0,60}\b(?:" + _POPULATION + r")"
        r"|\b(?:" + _POPULATION + r")[^.;?]{0,60}\b" + _CHANGE + r"\b",
        _I,
    )),
)
# Claims that only mean something against a stated comparison: "the difference
# between PANDA and PUMA" is not a group difference.
_NEEDS_DESIGN = frozenset({"group_difference"})

_CLAUSE_BREAK = re.compile(r"[.;:!?,()\n。；：！？，、（）]|\s[-–—]\s|\bbut\b|\bwhereas\b|\binstead\b", _I)
_NEGATION = re.compile(
    r"\b(?:not|no|never|nor|neither|without|cannot|avoid\w*)\b|n't\b|\brather\s+than\b|\binstead\s+of\b"
    r"|\bbeyond\s+the\s+scope\b|\bnot\s+(?:interested|trying|aiming|looking)\b"
    # A real session: "這是無向的統計關聯網路，不是 causal 或 TF-gene regulatory network".
    r"|不是|不|非|沒有|没有|無|无|並非|并非|而非",
    _I,
)
_SENTENCE_END = re.compile(r"[.!?](?=\s|$)|\n")
# Log 346: a negation after the witness, with the witness as what is negated:
# "Predicting relapse isn't the point" (second held-out set, T2).
_GOAL_NOUN = (
    r"(?:point|goal|aim|focus|question|purpose|interest|concern|objective|priority|intention|plan|idea|"
    r"target|task|agenda)"
)
_NEGATED_AFTER = re.compile(
    r"^[^.;:!?,]{0,40}?\b(?:is|are|was|were|'s|'re)\s*(?:n't|not)\s+(?:really\s+|actually\s+)?"
    r"(?:the\s+|our\s+|my\s+|a\s+|an\s+|what\s+(?:we|i)\b|why\b|needed\b|required\b|necessary\b|relevant\b|"
    r"important\b|of\s+interest\b|in\s+scope\b)"
    r"|^[^.;:!?,]{0,40}?\b(?:isn't|aren't|wasn't|weren't)\s+(?:really\s+|actually\s+)?"
    r"(?:the\s+|our\s+|my\s+|a\s+|an\s+|what\s+(?:we|i)\b|why\b|needed\b|required\b|necessary\b|relevant\b|"
    r"important\b|of\s+interest\b|in\s+scope\b)"
    r"|^[^.;:!?,]{0,40}?\b(?:is|are|was|were|'s|'re)\s+(?:out\s+of\s+scope|beyond\s+(?:the|our)\s+scope|"
    r"beside\s+the\s+point|irrelevant|secondary|not\s+(?:our|my|the)\s+" + _GOAL_NOUN + r")",
    _I,
)

_NUMBER_WORDS = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "twice": 2}
_TIMEPOINTS = re.compile(
    r"\b(?P<n>two|three|four|five|six|\d+)\s+(?:time\s?points?|visits|occasions|sampling\s+times)\b"
    r"|\b(?P<twice>twice)\b"
    r"|(?P<pair>\bbefore\s+and\s+(?:again\s+)?after\b|\bpre-?\s*(?:and|/|vs\.?|versus)\s*post-?\b)",
    _I,
)


class StudyPurpose(NamedTuple):
    design: Design | None = None
    design_quote: str = ""
    claims: tuple[tuple[Claim, str], ...] = ()

    @property
    def claim(self) -> Claim | None:
        """The primary claim: the first one in `_CLAIMS` order."""
        return self.claims[0][0] if self.claims else None

    @property
    def claim_quote(self) -> str:
        return self.claims[0][1] if self.claims else ""


def _sentence(task: str, start: int, end: int) -> str:
    left = max((m.end() for m in _SENTENCE_END.finditer(task, 0, start)), default=0)
    right = next((m.start() + 1 for m in _SENTENCE_END.finditer(task, end)), len(task))
    sentence = task[left:right].strip()
    return sentence if len(sentence) <= 300 else task[start:end]


def _negated(task: str, start: int) -> bool:
    """A negation earlier in the witness's own clause ("This is not causal")."""
    clause_start = max((m.end() for m in _CLAUSE_BREAK.finditer(task, 0, start)), default=0)
    return bool(_NEGATION.search(task, clause_start, start))


# Log 350 (CN): "cause" as a noun names a variable, not a claim -- "a donor
# table giving age, sex, RNA integrity and cause of death" (third held-out set,
# T8). It is a claim only after a verb asking for the cause: "identify the
# cause of the rewiring".
_CAUSE_NOUN = re.compile(r"^causes?$", _I)
_NOUN_AFTER = re.compile(r"^(?:\s+of\b|-)", _I)
_ASKS_FOR_CAUSE = re.compile(
    r"\b(?:find|identify|determine|establish|discover|uncover|reveal|pinpoint|trace|explain|show|prove|"
    r"demonstrate|understand|learn|know|test|confirm)\w*\b[^.;:!?,]{0,60}$",
    _I,
)


def _cause_as_variable(task: str, match: re.Match[str]) -> bool:
    """"cause of death" or "cause-specific" with no verb asking for the cause (Log 350)."""
    if not (_CAUSE_NOUN.match(match.group(0)) and _NOUN_AFTER.match(task[match.end():])):
        return False
    clause_start = max((m.end() for m in _CLAUSE_BREAK.finditer(task, 0, match.start())), default=0)
    return not _ASKS_FOR_CAUSE.search(task[clause_start:match.start()])


def _negated_after(task: str, end: int) -> bool:
    """The rest of the witness's clause negates it ("Predicting relapse isn't the point")."""
    return bool(_NEGATED_AFTER.search(task[end:]))


def _witness(pattern: re.Pattern[str], task: str, *, claim: bool = False) -> str | None:
    for match in pattern.finditer(task):
        if _negated(task, match.start()) or claim and (
                _negated_after(task, match.end()) or _cause_as_variable(task, match)):
            continue
        return _sentence(task, match.start(), match.end())
    return None


def study_purpose(task: str) -> StudyPurpose:
    """The design and claims the request states in words; empty when it states none."""
    design: Design | None = None
    design_quote = ""
    for value, pattern in (("paired", _PAIRED), ("groups", _GROUPS)):
        if quote := _witness(pattern, task):
            design, design_quote = value, quote
            break
    claims = []
    for claim, pattern in _CLAIMS:
        if claim in _NEEDS_DESIGN and design is None:
            continue
        if quote := _witness(pattern, task, claim=True):
            claims.append((claim, quote))
    return StudyPurpose(design, design_quote, tuple(claims))


def timepoint_count(task: str) -> int | None:
    """How many samples each individual gives, when the words say it (before and after = 2)."""
    for match in _TIMEPOINTS.finditer(task):
        if _negated(task, match.start()):
            continue
        if match.group("pair") or match.group("twice"):
            return 2
        word = match.group("n").lower()
        return int(word) if word.isdigit() else _NUMBER_WORDS.get(word)
    return None
