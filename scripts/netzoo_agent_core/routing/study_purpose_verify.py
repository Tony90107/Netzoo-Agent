"""Deterministic verification of a model-proposed study purpose (Log 355).

Log 341: offered a list of conditions, the model quoted the request's goal
sentence for whichever it chose, the control request included. Log 354: the
same happens with study purposes -- unverified, the model's conclusions were
wrong 129 times in 387 proposals, mostly "regulator_change" for any request
naming TFs. A proposal therefore stands only on its own quote:

- the quote is in the request;
- it contains a cue word for the value it supports (the lists are loose: they
  reject a generic goal sentence, they do not decide the value);
- the cue is not negated before or after it in its clause, and is not "cause"
  as a noun (the word witnesses' _negated, PN and CN);
- "predict the target genes" is network inference, not prediction;
- a regulator change needs a regulator noun and a change ("regulatory
  network" names none);
- groups need a contrast, and a paired design is not two data types from the
  same samples or a technical pairing (paired-end reads, batches);
- Log 357 (b'): "the same" alone does not make two data types a design --
  only a time point or a condition does ("paired RNA-seq and methylation from
  the same resections" is one condition); and groups are not groups when the
  sentence splits the same individuals between the conditions ("organoids from
  10 donors were each split into an IL-22 well and a vehicle well");
- a group difference needs a verified design.

What survives is the StudyPurpose the reply layer reads; nothing here selects,
ranks or removes a workflow.
"""

from __future__ import annotations

import re

from ..contracts.study_purpose import StudyPurposeProposal
from .study_purpose import StudyPurpose, _cause_as_variable, _negated, _negated_after, _sentence

__all__ = ["verify_proposal"]

_I = re.I
_CLAIM_CUES = {
    "group_difference": re.compile(
        r"differ\w*|chang\w*|shift\w*|alter\w*|rewir\w*|reshap\w*|compar\w*|\bbetween\b|versus|\bvs\.?\b|"
        # Not "respond": "non-responders" names a group (Log 340).
        r"relative\s+to|disrupt\w*|reorgani\w*|remodel\w*|diverg\w*|perturb\w*|unlike|"
        r"affect\w*|depart\w*|deviat\w*|return\w*", _I),
    "individual_change": re.compile(
        r"\bwhich\b|\bwhose\b|\brank\w*|individual\w*|outlier\w*|atypical|unusual|stand\w*\s+out|"
        r"\bmost\b|\bleast\b|deviat\w*|\beach\s+(?:patient|individual|subject|donor|animal|mouse)", _I),
    # A regulator noun ("regulatory network" is none) and a change, difference or ranking.
    "regulator_change": re.compile(
        r"(?=[^.;?]*(?:transcription[- ]factors?|\bTFs?\b|\bregulators\b|miRNAs?|micro-?RNAs?|\bmiR-))"
        r"[^.;?]*?\b(?:chang\w*|differ\w*|shift\w*|gain\w*|los[et]\w*|var(?:y|ies|ied|iation|iable)|rank\w*|"
        r"most|least|rewir\w*|switch\w*|alter\w*|reshuffl\w*|deviat\w*)\b", _I),
    "causal": re.compile(
        r"\bcaus\w*|\bdriv\w*|responsib\w*|mechanis\w*|underl\w*|\bprove\w*|\bestablish\w*|demonstrat\w*|"
        r"attribut\w*|because|leads?\s+to|results?\s+in|induc\w*|trigger\w*|mediat\w*|\bpin\w*", _I),
    "prediction": re.compile(
        r"predict\w*|forecast\w*|classif\w*|\bflag\w*|diagnos\w*|prognos\w*|signature|risk|\bfuture\b|"
        r"\bnew\b|unseen|independent|\bwill\b|biomarker\w*", _I),
}
_DESIGN_CUES = {
    "paired": re.compile(
        r"\bsame\b|\beach\b|\bboth\b|before|after|again|\bpre\b|pre-|post-|\bpost\b|time|visit\w*|trimester\w*|"
        r"\bdays?\b|weeks?|months?|years?|split|halves|\bhalf\b|cross-?over|random\s+order|paired|matched|"
        r"repeat\w*|longitudinal|serial\w*|baseline|follow-?up|admission|discharge|diagnosis|relapse|recovery|"
        r"stable|during|from\s+the\s+same", _I),
    # A contrast: two sides joined, or named groups, levels or arms. "85 lines, each from a
    # different donor" is one collection.
    "groups": re.compile(
        r"\band\b|\bvs\.?\b|versus|\bor\b|between|compared|\bplus\b|groups?|arms?|levels?|doses?|"
        r"concentrations?|strains?|genotypes?|cohorts?", _I),
}
_TECHNICAL_PAIRING = re.compile(
    r"paired-end|read\s+pairs|matri\w*|layers?|omics|batch\w*|librar\w*|lanes?|replicates?|litters?|"
    r"normali[sz]\w*|filter\w*", _I)
# Log 357: a time point or a condition, without "same" -- "the same 80 resections" is one condition.
_TIMED = re.compile(
    r"before|after|visit|trimester|split|cross|\bdays?\b|weeks?|months?|baseline|again|follow-?up|"
    r"treat\w*|exposure|stimulat\w*|condition", _I)
# Log 357: the same individuals split between the conditions, which is no group comparison.
_SAME_INDIVIDUALS = re.compile(
    r"\b(?:each|every)\b[^.;]{0,60}\bsplit\b|\bsplit\s+(?:into|between)\b|\bhalves\b|\bone\s+half\b|"
    r"\bfrom\s+the\s+same\s+(?:\d+\s+)?(?:[\w-]+\s+){0,2}?(?:patients?|donors?|individuals?|subjects?|animals?|mice|"
    r"people|participants?|women|men|children|volunteers?)\b|\bwithin[- ](?:donor|patient|subject|individual|animal)\b", _I)
_DATA_TYPE = re.compile(
    r"expression|methylation|RNA-?seq|microarray|arrays?|proteom\w*|metabolom\w*|small-?RNA|miRNA|ATAC|ChIP|"
    r"genotyp\w*|SNPs?|CNVs?|mutation\w*|transcriptom\w*", _I)
_PREDICT_NETWORK = re.compile(
    r"predict\w*\s+(?:the\s+|their\s+|its\s+)?(?:target\w*|binding|sites?|motifs?|interactions?|edges?|regulat\w*)", _I)
_NO_COMPARISON = re.compile(r"\bno\s+(?:control|comparison)|\bnobody\b|\bnone\s+of", _I)


def _locate(task: str, quote: str) -> tuple[int, int] | None:
    """(start, end) of the quote in the request, ignoring case and spacing, or None."""
    quote = quote.strip().strip('"“”').strip()
    if not quote:
        return None
    index = task.find(quote)
    if index >= 0:
        return index, index + len(quote)
    pattern = r"\s+".join(re.escape(word) for word in quote.split())
    match = re.search(pattern, task, _I)
    return (match.start(), match.end()) if match else None


def _claim_reason(task: str, claim: str, quote: str) -> str:
    span = _locate(task, quote)
    if span is None:
        return "quote_not_in_request"
    cues = list(_CLAIM_CUES[claim].finditer(task, *span))
    if not cues:
        return "no_cue"
    for match in cues:
        if _negated(task, match.start()) or _negated_after(task, match.end()):
            continue
        if claim == "causal" and _cause_as_variable(task, match):
            continue
        if claim == "prediction" and _PREDICT_NETWORK.match(task, match.start()):
            continue
        return "ok"
    return "negated_or_vetoed"


def _design_reason(task: str, design: str, quote: str) -> str:
    located = _locate(task, quote)
    if located is None:
        return "quote_not_in_request"
    span = task[located[0]:located[1]]
    if not _DESIGN_CUES[design].search(span):
        return "no_cue"
    timed = _TIMED.search(span)
    if _TECHNICAL_PAIRING.search(span) and not timed:
        return "technical"
    if design == "paired" and len({m.group(0).lower() for m in _DATA_TYPE.finditer(span)}) >= 2 and not timed:
        return "two_data_types"
    if _negated(task, located[0] + 1) or _NO_COMPARISON.search(span):
        return "negated"
    if design == "groups" and _SAME_INDIVIDUALS.search(_sentence(task, located[0], located[1])):
        return "same_individuals"
    return "ok"


def verify_proposal(task: str, proposal: StudyPurposeProposal) -> tuple[StudyPurpose, list[dict]]:
    """The verified StudyPurpose and every rejected part of the proposal, with its reason."""
    rejected: list[dict] = []
    design, design_quote = None, ""
    if proposal.design != "none":
        reason = _design_reason(task, proposal.design, proposal.design_span)
        if reason == "ok":
            design, design_quote = proposal.design, proposal.design_span.strip()
        else:
            rejected.append({"field": "design", "value": proposal.design, "reason": reason})
    claims: list[tuple[str, str]] = []
    for item in proposal.claims:
        reason = _claim_reason(task, item.claim, item.text_span)
        if reason == "ok" and item.claim == "group_difference" and design is None:
            reason = "needs_design"
        if reason != "ok":
            rejected.append({"field": "claim", "value": item.claim, "reason": reason})
        elif item.claim not in {claim for claim, _ in claims}:
            claims.append((item.claim, item.text_span.strip()))
    return StudyPurpose(design, design_quote, tuple(claims)), rejected
