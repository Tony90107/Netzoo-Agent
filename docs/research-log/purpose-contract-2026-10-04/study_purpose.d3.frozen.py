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
from typing import Callable, Literal, NamedTuple

__all__ = ["StudyPurpose", "study_purpose", "timepoint_count"]

Design = Literal["paired", "groups"]
Claim = Literal["group_difference", "individual_change", "regulator_change", "causal", "prediction"]

_I = re.I
_SUBJECTS = r"(?:patients?|individuals?|subjects?|donors?|participants?|mice|mouse|animals?|rats?|volunteers?|people|persons?)"
# Log 352 (D3): the design witnesses of the withdrawn v3 (Logs 348-349); conclusions keep
# v1+PN+CN, so _SUBJECTS above stays the conclusions' subject list.
_DESIGN_SUBJECTS = (
    r"(?:patients?|individuals?|subjects?|donors?|participants?|mice|mouse|animals?|rats?|volunteers?|people|"
    r"persons?|recipients?|women|men|children|infants|cases)"
)
_EVENT = (
    r"(?:treatment|therapy|drug|dosing|exposure|infection|vaccination|surgery|resection|intervention|"
    r"stimulation|challenge|transplant\w*|chemotherapy|immunotherapy|radiotherapy|diet|training|"
    r"knock\w*|operation|operative|induction|administration)"
)
# A moment in a patient's course or a study schedule, after "and at/on/after".
_TIME_ANCHOR = (
    r"(?:days?|weeks?|months?|years?|hours?|visits?|follow-?up|relapse|recurrence|discharge|remission|"
    r"progression|completion|(?:the\s+)?end|diagnosis|admission|baseline|surgery|delivery|birth|recovery|"
    r"convalescence|\d+)"
)
# Words that make "before ... and after" a processing step, not a sampling design.
_PROCESSING = re.compile(
    r"normali[sz]\w*|filter\w*|correct\w*|batch\w*|\bQC\b|quality\s+control|trimm\w*|align\w*|imput\w*|"
    r"transform\w*|scal(?:e|ed|ing)\b|threshold\w*|prun\w*|clean\w*|pre-?process\w*|integrat\w*|"
    r"denois\w*|smooth\w*|deconvol\w*|regress\w*\s+out|remov\w*|depths?|lanes?|librar\w*|standard\s+curve|spike-?ins?",
    _I,
)
_SAMPLING = re.compile(
    r"sampl\w*|biops\w*|collect\w*|taken|drawn|draws?|obtain\w*|profil\w*|measur\w*|sequenc\w*|specimens?|"
    r"blood|tissue|visits?|swabs?|aspirat\w*|resect\w*|arrays?|RNA-?seq|microarray\w*",
    _I,
)
# What a count can name without naming a group of individuals.
_UNIT_HEADS = re.compile(
    r"^(?:samples?|specimens?|biops\w*|replicates?|time\s?points?|genes?|TFs?|factors?|regulators?|miRNAs?|"
    r"features?|probes?|probesets?|cells?|reads?|lanes?|runs?|batches?|layers?|omics|datasets?|networks?|"
    r"edges?|modules?|clusters?|pathways?|days?|weeks?|months?|years?|hours?|minutes?|sites?|centers?|"
    r"centres?|hospitals?|visits?|draws?|metabolites?|proteins?|peaks?|CpGs?|loci|SNPs?|variants?|"
    r"mutations?|arrays?|chips?|libraries|wells?|plates?|slides?|sections?|regions?|tissues?|organs?|"
    r"conditions?|treatments?|doses?|drugs?|compounds?|timepoints?|bases?|kb|Mb)$",
    _I,
)
# Words that name one side of a contrast between groups of individuals.
_GROUP_SIDE = (
    r"(?:lean|obese|overweight|young|old|aged|elderly|treated|untreated|vehicle|mock|exposed|unexposed|"
    r"infected|uninfected|knock-?out|knock-?down|wild[- ]type|mutant|transgenic|carriers?|non-?carriers?|"
    r"affected|unaffected|sensitive|resistant|responders?|non-?responders?|healthy|diseased|smokers?|"
    r"non-?smokers?|survivors?|non-?survivors?|cases?|controls?|males?|females?|"
    r"symptomatic|asymptomatic|severe|mild|placebo|sham|deficient)"
)


class _Witness(NamedTuple):
    pattern: re.Pattern[str]
    # A check on (sentence, match) after the pattern; False rejects this match.
    check: Callable[[str, re.Match[str]], bool] | None = None


def _sampled_not_processed(sentence: str, match: re.Match[str]) -> bool:
    """"before X and after Y" names samples, not a processing step (Log 344)."""
    return bool(_SAMPLING.search(sentence)) and not _PROCESSING.search(match.group(0) + match.string[match.end():match.end() + 30])


def _not_processing(sentence: str, match: re.Match[str]) -> bool:
    return not _PROCESSING.search(match.group(0) + match.string[match.end():match.end() + 30])


def _two_groups_of_individuals(sentence: str, match: re.Match[str]) -> bool:
    """"40 X and 40 Y" names two groups unless either count names a unit ("24 patients and 48 samples")."""
    return not (_UNIT_HEADS.match(match.group("head1")) or _UNIT_HEADS.match(match.group("head2")))


# Two omics layers measured on the same samples are "paired" too (real sessions).
_OMICS = re.compile(r"matri\w*|layers?|omics|datasets?|assays?|modalit\w*|data\s+types?|platforms?", _I)


def _tissues_not_omics(sentence: str, match: re.Match[str]) -> bool:
    """"matched tumor and non-tumor tissue from the same patients", not two omics layers from them (Log 348)."""
    return not _OMICS.search(match.group(0))


def _different_sides(sentence: str, match: re.Match[str]) -> bool:
    return match.group("side1").lower().rstrip("s") != match.group("side2").lower().rstrip("s")


# Same individuals measured more than once.
_PAIRED: tuple[_Witness, ...] = (
    _Witness(re.compile(r"\bbefore\s+and\s+(?:again\s+)?after\b|\bafter\s+and\s+before\b", _I), _not_processing),
    _Witness(re.compile(
        r"\bbefore\b[^.;]{1,60}?\band\s+(?:again\s+)?(?:[\w-]+\s+){0,4}?after\b", _I), _sampled_not_processed),
    _Witness(re.compile(r"\bpre-?\s*(?:and|/|vs\.?|versus|or)\s*post-?\b", _I), _not_processing),
    _Witness(re.compile(r"\bpre-?" + _EVENT + r"\b.{0,80}\bpost-?" + _EVENT + r"\b", _I)),
    _Witness(re.compile(r"\bat\s+baseline\s+and\s+(?:again\s+)?(?:after|at|on|following)\b", _I)),
    _Witness(re.compile(r"\bbaseline\b[^.;]{0,40}\bfollow-?up\b", _I)),
    # "during an acute attack and again six weeks after recovery"
    _Witness(re.compile(
        r"\b(?:during|at|on|in)\b[^.;]{1,40}?\band\s+again\s+(?:at|on|after|during|in|\d+|[\w-]+\s+"
        r"(?:days?|weeks?|months?|years?|hours?))\b", _I), _sampled_not_processed),
    # "matched tumor and adjacent non-tumor mucosa from the same 32 patients"
    _Witness(re.compile(
        r"\b(?:matched|paired)\b[^.;]{0,80}\bfrom\s+the\s+same\s+(?:\d+\s+)?(?:[\w-]+\s+){0,2}?" + _DESIGN_SUBJECTS + r"\b"
        r"|\b(?:tumou?rs?|cancers?|lesions?|lesional|diseased|affected)\s+and\s+(?:their\s+|its\s+)?"
        r"(?:paired\s+|matched\s+|adjacent\s+)?(?:non-?tumou?r|normal|non-?lesional|non-?cancerous|healthy|"
        r"unaffected|uninvolved)\b[^.;]{0,60}\bfrom\s+(?:the\s+same|each|every)\b", _I), _tissues_not_omics),
    # "each sampled at ICU admission and on day five", "at diagnosis and at relapse".
    _Witness(re.compile(
        r"\bat\s+(?:the\s+time\s+of\s+)?(?:[\w-]+\s+){0,3}?(?:diagnosis|admission|baseline|enrol?lment|entry|"
        r"surgery|presentation|birth|delivery|onset|day\s+\w+|week\s+\w+|visit\s+\w+)\b[^.;]{0,20}?"
        r"\band\s+(?:again\s+)?(?:at|on|after)\s+(?:the\s+)?(?:[\w-]+\s+){0,2}?" + _TIME_ANCHOR + r"\b", _I)),
    _Witness(re.compile(
        r"\b(?:admission|diagnosis|enrol?lment|presentation|baseline|onset)\s+and\s+(?:at\s+|on\s+)?(?:the\s+)?"
        r"(?:discharge|relapse|recurrence|remission|progression|follow-?up|recovery|convalescence|"
        r"day\s+\w+|week\s+\w+|month\s+\w+)\b", _I)),
    # "Three time points" alone is not pairing: mice are often sacrificed per time
    # point. Longitudinal and serial sampling are of the same individuals.
    _Witness(re.compile(
        r"\blongitudinal(?:ly)?\b|\bserial(?:ly)?\s+(?:sampl\w*|biops\w*|collected|measured|specimens?|blood)\b"
        r"|\brepeated(?:ly)?\s+(?:sampl\w*|measur\w*|biops\w*|profil\w*)\b"
        r"|\bwithin[- ](?:patient|subject|individual|person|donor|animal|mouse)\b"
        r"|\b(?:visits?|draws?|biopsies|samples|time\s?points)\s+(?:per|from\s+each)\s+(?:patient|participant|subject|donor|individual|person|animal|mouse)\b", _I)),
    # "Paired" alone often means two omics layers from the same samples ("150 paired
    # tumor samples" with mRNA and miRNA, a real session): it needs a time word.
    _Witness(re.compile(
        r"\bpaired\s+(?:[\w-]+\s+){0,3}?(?:pre|post|before|after|baseline|time\s?points?|longitudinal)\b"
        r"|\bpaired\s+(?:design|pre-?\s*/\s*post)\b|\bpaired\s+tumou?r[- ]normal\b|\btumou?r[- ]normal\s+pairs?\b"
        r"|\bmatched\s+pairs?\b"
        r"|\bmatched\s+(?:pre|post|before|samples?\s+from\s+the\s+same|tumou?r[- ]normal|(?:adjacent\s+)?normal)\b"
        r"|\b(?:tumou?rs?|cancers?)\s+and\s+(?:their\s+|its\s+)?(?:paired\s+|matched\s+|adjacent\s+)normal\b[^.;]{0,40}"
        r"\b(?:from|of|in)\s+(?:the\s+same|each|every)\b", _I)),
    _Witness(re.compile(
        r"\b(?:each|every|the\s+same)\s+(?:(?:patient|individual|subject|donor|participant|mouse|animal|rat|volunteer|"
        r"recipient|woman|man|child)s?\s+)?(?:[\w-]+\s+){0,6}?(?:was\s+|were\s+)?"
        r"(?:sampled|biopsied|measured|profiled|sequenced|collected|bled|swabbed|scanned)\b[^.;]{0,60}"
        r"\b(?:before|after|twice|again|at\s+(?:two|three|four|\d+)|on\s+days?|weeks?\s+\d|over\s+time)\b", _I),
        _not_processing),
    _Witness(re.compile(
        r"\bthe\s+same\s+" + _DESIGN_SUBJECTS + r"\b[^.;]{0,60}\b(?:before|after|over\s+time|at\s+(?:two|three|\d+)\s+time)", _I)),
)

_GROUP_NOUN = (
    r"(?:responders?|non-?responders?|cases?|controls?|healthy|patients?|tumou?rs?|normals?|"
    r"treated|untreated|exposed|unexposed|knock-?outs?|wild[- ]types?|mutants?|carriers?|non-?carriers?|"
    r"males?|females?|men|women|smokers?|non-?smokers?|survivors?|non-?survivors?|resistant|sensitive|"
    r"diseased|disease|benign|malignant|metastatic|primary|relapsed?|remission|groups?|cohorts?|arms?|"
    r"lean|obese|young|old|aged|vehicle|placebo|sham)"
)
# Different individuals in two or more groups.
_GROUPS: tuple[_Witness, ...] = (
    _Witness(re.compile(
        r"\bnon-?responders?\b|\bresponders?\s+(?:and|vs\.?|versus|or)\s+non\b"
        r"|\bcases?\s+(?:and|vs\.?|versus)\s+(?:healthy\s+)?controls?\b|\bcase[- ]control\b"
        r"|\b(?:patients|cases)\s+(?:and|vs\.?|versus)\s+(?:healthy\s+|matched\s+)?(?:controls?|donors?|volunteers?)\b"
        # "210 healthy volunteers" is one group; healthy *controls* are compared with someone.
        r"|\bhealthy\s+controls?\b"
        r"|\b(?:two|three|four|\d+|both)\s+(?:groups|cohorts|arms|genotypes|strains|diets|sexes|populations)\b"
        r"|\b(?:between|across)\s+(?:the\s+)?(?:two|three|four|\d+|treatment|study|experimental|patient)\s+"
        r"(?:groups|cohorts|arms|conditions|genotypes|strains|diets)\b"
        r"|\b(?:males?\s+(?:and|vs\.?|versus)\s+females?|females?\s+(?:and|vs\.?|versus)\s+males?|men\s+and\s+women|women\s+and\s+men)\b"
        r"|\b(?:smokers?\s+(?:and|vs\.?|versus)\s+non-?smokers?)\b"
        r"|\b(?:treated|exposed|knock-?out|mutant|infected|diseased)\s+(?:\w+\s+)?(?:and|vs\.?|versus)\s+"
        r"(?:untreated|unexposed|control|wild[- ]type|uninfected|mock|healthy|vehicle)\b"
        r"|\b(?:tumou?rs?|cancers?)\s+(?:samples?\s+)?(?:and|vs\.?|versus)\s+(?:adjacent\s+)?normal\b"
        r"|\b" + _GROUP_NOUN + r"\s+(?:vs\.?|versus)\s+" + _GROUP_NOUN + r"\b",
        _I,
    )),
    # "40 schizophrenia donors and 40 age-matched controls", "12 wild-type and 12 knockout mice".
    _Witness(re.compile(
        r"\b\d+\s+(?:from\s+)?(?:[\w-]+\s+){0,5}?(?P<head1>[\w-]+)\s+(?:and|vs\.?|versus|plus)\s+"
        r"\d+\s+(?:from\s+)?(?:[\w-]+\s+){0,5}?(?P<head2>[\w-]+)", _I), _two_groups_of_individuals),
    # "four replicate pools at each of vehicle and three bisphenol S concentrations" (Log 352).
    _Witness(re.compile(
        r"\b(?:two|three|four|five|six|\d+)\s+(?:dose|dosage|concentration|exposure|treatment)\s+(?:groups|arms)\b"
        r"|\b(?:vehicle|control|placebo|sham)\b[^.;]{0,30}\band\s+(?:two|three|four|five|six|\d+)\s+(?:[\w-]+\s+){0,3}?"
        r"(?:concentrations|doses|dosages|dose\s+levels)\b", _I), _not_processing),
    # "lean and obese women", "wild-type and Nrf2-knockout mice", "vehicle- or drug-treated rats".
    _Witness(re.compile(
        r"\b(?P<side1>" + _GROUP_SIDE + r")\b[\w\s-]{0,30}?\b(?:and|vs\.?|versus|or)\s+(?:\d+\s+)?(?:[\w-]+[\s-]+){0,2}?"
        r"(?P<side2>" + _GROUP_SIDE + r")\b", _I), _different_sides),
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
    r"|(?P<pair>\bbefore\s+and\s+(?:again\s+)?after\b|\bpre-?\s*(?:and|/|vs\.?|versus)\s*post-?\b"
    r"|\bbefore\b[^.;]{1,60}?\band\s+(?:again\s+)?(?:[\w-]+\s+){0,4}?after\b)",
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


def _witness(witness: _Witness | re.Pattern[str], task: str, *, claim: bool = False) -> str | None:
    pattern, check = (witness, None) if isinstance(witness, re.Pattern) else witness
    for match in pattern.finditer(task):
        if _negated(task, match.start()) or claim and (
                _negated_after(task, match.end()) or _cause_as_variable(task, match)):
            continue
        sentence = _sentence(task, match.start(), match.end())
        if check is None or check(sentence, match):
            return sentence
    return None


def study_purpose(task: str) -> StudyPurpose:
    """The design and claims the request states in words; empty when it states none."""
    design: Design | None = None
    design_quote = ""
    for value, witnesses in (("paired", _PAIRED), ("groups", _GROUPS)):
        if quote := next((found for witness in witnesses if (found := _witness(witness, task))), None):
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
