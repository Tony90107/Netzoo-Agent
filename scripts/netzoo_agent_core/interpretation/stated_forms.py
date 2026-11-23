"""Typed reading fields corrected from the user's own words (stated-forms-2026-11-19, six-package scope).

Two misreads that ruled a doable six-package workflow out although the request's words say otherwise:

- spatial=uses_neighbors when the words only describe spatial data ("We ran spatial transcriptomics ... summed the
  spots into 32 annotated regions ... a co-expression network for each region", j11 C20, LIONESS-COEXPRESSION).
  It stands only when the request asks for neighbours to be used (neighbour, nearby, adjacent, borrow information,
  spatially smoothed ...); otherwise the ask reads not_spatial.
- scale=per_sample when the asked words want one pooled network per group ("a separate aggregate PANDA network for
  each time point", j4 S45, PANDA; "one network per stage, each built from all 12 samples of that stage"). Such an
  ask reads per_group.

Both are matched on the user's words by code; neither is the model's. needs_sign (needs-sign-2026-11-18) is applied
here too.
"""

from __future__ import annotations

import re

__all__ = ["NEIGHBOUR_WORDS", "POOLED_PER_GROUP", "SIGN_WORDS", "corrected_forms", "without_unasked_sign"]

# needs-sign-2026-11-18: words that ask whether a regulator activates or represses its targets. "how strongly" and "how
# active" are not among them (live B3: "which TFs control which genes, and how strongly" typed needs_sign=True 3 of 4
# times and ruled LIONESS-PANDA out).
SIGN_WORDS = re.compile(
    r"\b(?:activat\w*|repress\w*|inhibit\w*|sign(?:ed|s)?\b|positive(?:ly)? or negative(?:ly)?|"
    r"up\W*or down|up- or down|upregulat\w*|downregulat\w*|on or off|stimulat\w*|suppress\w*|direction of)",
    re.IGNORECASE)


def without_unasked_sign(task: str, proposal):
    """The reading with every typed `needs_sign` turned off when no words of the request ask for the sign
    (`SIGN_WORDS`, anywhere in it: "... and their signs" in another sentence still counts). Live B3: "which TFs
    control which genes, and how strongly" typed needs_sign=True and ruled LIONESS-PANDA out 3 of 4 times."""
    if SIGN_WORDS.search(task or "") or proposal is None:
        return proposal
    updates = {}
    for name in type(proposal).model_fields:
        sentence = getattr(proposal, name)
        if not (name[1:].isdigit() and hasattr(sentence, "asks")):
            continue
        if any(getattr(ask, "needs_sign", False) for ask in sentence.asks):
            updates[name] = sentence.model_copy(update={"asks": [
                ask.model_copy(update={"needs_sign": False}) if getattr(ask, "needs_sign", False) else ask
                for ask in sentence.asks]})
    return proposal.model_copy(update=updates) if updates else proposal


NEIGHBOUR_WORDS = re.compile(
    r"\b(?:neighbo\w*|nearby|adjacent|proximity|surrounding|borrow\w* (?:information|strength)|share strength|"
    r"spatially (?:smooth\w*|weighted|aware|varying|resolved network)|distance between (?:spots|cells))",
    re.IGNORECASE)

_GROUPS = (r"(?:stages?|time ?points?|visits?|tissues?|conditions?|groups?|arms?|treatments?|genotypes?|strains?|"
           r"diets?|regions?|cell types?|days?|weeks?|subtypes?|sites?|batches?|sexes|cohorts?|populations?)")
_PER_GROUP = re.compile(rf"\b(?:per|for each|for every|each)\W+(?:\w+\W+){{0,2}}?{_GROUPS}\b", re.IGNORECASE)
_POOLED = re.compile(
    r"\b(?:aggregate\w*|pooled|combined|each built|built (?:on|from) (?:all|the|that|each|its)|using all|from all|"
    r"not (?:a|one) network (?:per|for each) (?:sample|patient|individual|animal|donor|subject))", re.IGNORECASE)
POOLED_PER_GROUP = (_PER_GROUP, _POOLED)


#: dev-bank D024: single cells go to SCORPION (KNOWN_LIMITATIONS), so a bulk TF-network link on an ask the code read as
#: single cells is SCORPION's same result; "which pathways differ in their regulation across the donors" linked to
#: CONDOR's community enrichment is PORCUPINE's result.
_SINGLE_CELL_LINKS = {"panda.tf_gene_network": "scorpion.tf_gene_network",
                      "lioness_panda.per_sample_networks": "scorpion.per_group_networks"}
_PER_CELL = re.compile(r"\b(?:each|every|per)\s+(?:single\s+|individual\s+)?(?:cell|nucleus)\b|\bindividual cells?\b",
                       re.IGNORECASE)
_HETEROGENEOUS = re.compile(
    r"\bpathways?\b[^.]{0,60}\b(?:differ\w*|var(?:y|ies|ying|iable)|heterogene\w*)\b[^.]{0,40}\b(?:across|between|among)\b"
    r"[^.]{0,20}\b(?:donors|patients|samples|tumou?rs|individuals|people|subjects|participants)\b", re.IGNORECASE)


def _relinked(ask) -> list[str] | None:
    linked = list(getattr(ask, "delivered_by", None) or [])
    quote = getattr(ask, "quote", "") or ""
    # a network for each cell is no per-group SCORPION result ("A network for each cell" is declined)
    single = getattr(ask, "data_unit", None) == "single_cells" and not _PER_CELL.search(quote)
    new = [(_SINGLE_CELL_LINKS.get(key, key) if single else key) for key in linked]
    if "condor.enrichment" in new and _HETEROGENEOUS.search(quote) and re.search(r"regulat", quote, re.IGNORECASE):
        new = ["porcupine.heterogeneous_pathways" if key == "condor.enrichment" else key for key in new]
    new = list(dict.fromkeys(new))
    return new if new != linked else None


def _fixes(task: str, ask) -> dict:
    fix = {}
    if (linked := _relinked(ask)) is not None:
        fix["delivered_by"] = linked
    if getattr(ask, "spatial", None) == "uses_neighbors" and not NEIGHBOUR_WORDS.search(task or ""):
        fix["spatial"] = "not_spatial"
    quote = getattr(ask, "quote", "") or ""
    if getattr(ask, "scale", None) == "per_sample" and _PER_GROUP.search(quote) and _POOLED.search(quote):
        fix["scale"] = "per_group"
    return fix


def corrected_forms(task: str, proposal):
    """The reading with needs_sign, spatial and a pooled per-group scale corrected from the request's words."""
    proposal = without_unasked_sign(task, proposal)
    if proposal is None:
        return proposal
    updates = {}
    for name in type(proposal).model_fields:
        sentence = getattr(proposal, name)
        if not (name[1:].isdigit() and hasattr(sentence, "asks")):
            continue
        asks = [ask.model_copy(update=fix) if (fix := _fixes(task, ask)) else ask for ask in sentence.asks]
        if any(new is not old for new, old in zip(asks, sentence.asks)):
            updates[name] = sentence.model_copy(update={"asks": asks})
    return proposal.model_copy(update=updates) if updates else proposal
