"""What the request's own words state, read by code for the lean decider's rules (split out of lean/__init__.py,
2026-11-23, when it passed the 1,000-line review limit): loose quote matching, stated numbers, the data unit, raw counts
or another scale, normalization asked for, held inputs, one source per side, per-cell networks, priors in hand, the
user's doubt, expression stated gone, SCORPION's input conditions. Each reader returns the request's words it relied
on, so a refusal can quote them; none of them calls a model.
"""

from __future__ import annotations

_CJK = "\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff"


def _units(text: str) -> list[str]:
    """Words and single CJK characters, case-folded, with punctuation, symbols and spacing dropped."""
    import re

    return re.findall(rf"[{_CJK}]|[^\W{_CJK}_]+", (text or "").casefold().replace("_", " "))


def _found(task: str, quote: str) -> bool:
    """Whether the request says what the quote says, loosely (2026-11-20, user: the match need not be that exact).

    Found when the quote's words, ignoring case, punctuation, spacing and underscores ("min_cells 50" in "min_cells =
    50"), sit in the request in order; or when at least 60% of them, and two, appear in order within a passage at most
    twice the quote's length ("15 AD samples" in "15 Alzheimer's disease samples"). Chinese is compared character by
    character. A quote that is not found never stops anything here: its evidence is just not used.
    """
    from difflib import SequenceMatcher

    wanted, words = _units(quote), _units(task)
    if not wanted or not words:
        return False
    joined, target = " ".join(words), " ".join(wanted)
    if f" {target} " in f" {joined} ":
        return True
    if len(wanted) < 2:
        return False
    blocks = [b for b in SequenceMatcher(None, words, wanted, autojunk=False).get_matching_blocks() if b.size]
    for first in range(len(blocks)):
        matched = 0
        for last in range(first, len(blocks)):
            if blocks[last].a + blocks[last].size - blocks[first].a > 2 * len(wanted):
                break
            matched += blocks[last].size
            if matched >= 2 and matched >= 0.6 * len(wanted):
                return True
    return False


def _stated_value(task: str, value: str) -> bool:
    """A setting's value as the request writes it: its number, or its words."""
    from ..workflow_conditions import stated_numbers

    numbers = stated_numbers(value)
    return bool(numbers) and all(any(n == m for m in stated_numbers(task)) for n in numbers)


def _stated(task: str, number: int) -> bool:
    """The number itself is in the request (digits, or a number word the contract reader knows)."""
    from ..workflow_conditions import stated_numbers

    return any(float(number) == value for value in stated_numbers(task))


def _per_sample_version(workflow: str) -> str | None:
    """R4: the workflow that derives `workflow`'s per-sample networks and hands them to PORCUPINE."""
    action = f"run_{workflow.lower()}"
    from . import _specs

    for name, spec in _specs().items():
        capability = spec.get("output_capability") or {}
        if action in (capability.get("guidance_predecessors") or []) and "run_porcupine" in (
                capability.get("handoff_targets") or []):
            return name
    return None


_RE = __import__("re")
_CLAUSE = _RE.compile(r"[.;:!?\n，。；：！？]|,\s|、")
_NEGATION = _RE.compile(r"\b(?:no|not|never|without|deleted|discarded|lost|unavailable)\b|n't\b|沒有|沒|無|未|不|刪", _RE.I)
_NON_COUNT = _RE.compile(
    r"(?<![A-Za-z0-9])(?:log2?\s*\(?\s*)?(?:TPM|[FR]PKM)(?:\s*\+\s*1\s*\))?(?![A-Za-z0-9])"
    # CPM is also a gene (carboxypeptidase M): only as a unit ("log2 CPM", "CPM-normalized", "in CPM")
    r"|(?<![A-Za-z0-9])log2?\s*\(?\s*CPM(?![A-Za-z0-9])|(?<![A-Za-z0-9])CPM(?=[- ](?:normali|values?\b|matri|table|"
    r"units?\b|scale|transform))|\b(?:in|as|to)\s+CPM(?![A-Za-z0-9])"
    r"|(?<![A-Za-z0-9])log(?:2|10)?[- ]?(?:transformed|scale[d]?|values?|intensit(?:y|ies)|expression)"
    r"|(?<![A-Za-z0-9])RMA(?![A-Za-z0-9])|microarrays?|Affymetrix|BeadChip|(?:array|probe)[- ]intensit(?:y|ies)"
    r"|晶片|強度值|log2?\s*強度", _RE.I)
_RAW_COUNTS = _RE.compile(
    r"raw\s+(?:\w+\s+){0,2}counts?|read[- ]counts?|integer\s+counts?|unnormali[sz]ed\s+counts?"
    r"|count\s+(?:matrix|table)|featureCounts|HTSeq|原始.{0,6}(?:counts?|計數)|read\s*count"
    r"|\bcounts?\b", _RE.I)  # bare "the counts are in data.tsv" (Gemini review): count data stated, no refusal
_OTHER_DATA = _RE.compile(r"\bpreviously\b|\bpublished\b|\bearlier\b|以前|之前|發表", _RE.I)


def _clauses(task: str) -> list[str]:
    return [part for part in _CLAUSE.split(task) if part.strip()]


def non_count_scale(task: str) -> str:
    """R8 (2026-11-21; advisor 2026-11-11: SNAIL takes raw counts): the words calling the expression TPM, FPKM, CPM,
    log values or microarray intensities, when no clause of the request states raw counts. Clauses with a negation
    are skipped both ways ("the read counts were not saved" is no raw-count statement; "not sure whether raw counts
    or TPM" states neither), and a scale in a clause about other data ("previously we published TPM") is no
    statement either. Any counts named (even "the counts are in data.tsv") means no refusal: a wrong refusal costs
    more than a run that SNAIL's own input check can still stop. Empty when the request states counts or no other
    scale."""
    plain = [part for part in _clauses(task) if not _NEGATION.search(part)]
    if any(_RAW_COUNTS.search(part) for part in plain):
        return ""
    return next((found.group(0).strip() for part in plain
                 if not _OTHER_DATA.search(part) and (found := _NON_COUNT.search(part))), "")


_ASK_NORMALIZE = _RE.compile(r"(?<![A-Za-z0-9])(?:py)?snail(?![A-Za-z0-9])|qsmooth|smooth[- _]?quantile"
                            r"|\bnormali[sz](?:e|es|ing|ation)\b|標準化|正規化", _RE.I)
_DONE = _RE.compile(r"\balready\b|\bpreviously\b|已|過", _RE.I)


def normalization_asked(task: str) -> bool:
    """The request asks for a normalization: SNAIL or smooth quantile named, or "normalize" (or its Chinese word) in a clause that
    does not say it was already done ("already normalized to log2 TPM", or the same in Chinese)."""
    return any(_ASK_NORMALIZE.search(part) and not _DONE.search(part) for part in _clauses(task))


_ARTIFACT_WORDS = {  # what a request calls an input artifact the contracts name in incompatible_input_artifacts
    "coexpression_network": (r"co-?expression\s+(?:networks?|matri(?:x|ces)|tables?|edges?)|共表現(?:網路|矩陣)",
                             "a co-expression network"),
    "mutation_matrix": (r"(?:somatic\s+)?mutation\s+(?:matri(?:x|ces)|tables?|calls)|突變矩陣", "a mutation matrix"),
}
_ACCEPTED_WORDS = {  # what a request calls an input the contract's input_artifacts accept
    "expression_matrix": r"expression|RNA-?seq|counts?\b|microarray|transcriptom|表現|表達|定序",
    "regulatory_network": r"TF[- ]?(?:to[- ])?(?:gene|target)|regulatory\s+networks?|LIONESS|PANDA|調控網路",
    "coexpression_network": _ARTIFACT_WORDS["coexpression_network"][0],
}
_HAS = _RE.compile(r"\b(?:computed|calculated|stored|saved|built|made|generated|exported|estimated|have|has|had|got|"
                   r"attached|uploaded|enclosed)\b|\bhere(?:'s| is| are)\b"
                   r"|手上|已經|已有|算好|建好|存成", _RE.I)
_WANTS = _RE.compile(r"\b(?:need|needs|want|wants|please|would\s+like|give\s+me|build|make|construct|get)\b"
                     r"|想要|需要|請|幫我", _RE.I)


def held_incompatible_input(task: str, workflow: str) -> tuple[str, str]:
    """R10 (2026-11-21, workflows/*.yaml output_capability.incompatible_input_artifacts): the artifact the request says
    the user already has (a clause with "computed", "stored", "we have"...; none with "need", "build", "please"...) that
    `workflow`'s contract lists as incompatible, when no clause names an input it accepts (input_artifacts) apart from
    it. ("label", "quote") or ("", ""). A co-expression network the user asks
    for (X003, X019) is a wanted result, not an input: its clause has a want word, so it is never read here."""
    from . import _specs

    spec = (_specs().get(workflow) or {}).get("output_capability") or {}
    plain = [part for part in _clauses(task) if not _NEGATION.search(part)]
    for accepted in spec.get("input_artifacts") or []:  # a usable input is stated too: the other data is background
        words = _ACCEPTED_WORDS.get(accepted)  # ("mutation calls and RNA-seq ... run PANDA on the RNA-seq", review)
        if words and any(_RE.search(words, part, _RE.I) and not _RE.search(
                "|".join(w for w, _ in _ARTIFACT_WORDS.values()), part, _RE.I) for part in plain):
            return "", ""
    for artifact in spec.get("incompatible_input_artifacts") or []:
        if artifact not in _ARTIFACT_WORDS:
            continue
        words, label = _ARTIFACT_WORDS[artifact]
        for part in _clauses(task):
            if (found := _RE.search(words, part, _RE.I)) and _HAS.search(part) and not _WANTS.search(part) \
                    and not _NEGATION.search(part):
                return label, found.group(0)
    return "", ""


_COMPARE = _RE.compile(  # two sides named: "between core and margin", "failing vs healthy", "腫瘤和正常之間"
    r"\bbetween\b.{1,80}?\band\b|\bversus\b|\bvs\.?(?!\w)|\bcompar\w*\b.{1,80}?\b(?:and|with|to|against)\b"
    r"|兩組|兩邊|(?:和|與|跟|及|對).{1,30}?之間|(?:比較|對照)", _RE.I | _RE.S)
_PER_CELL = _RE.compile(  # one network per cell is R6's (no workflow gives it), never a one-per-side comparison
    r"\b(?:each|every|per|individual|single)\s+(?:individual\s+)?cells?\b|\bcell[- ]to[- ]cell\b|between\s+cells"
    r"|每(?:一)?個?細胞|細胞(?:與|和|跟|到)細胞", _RE.I)
_INDIVIDUAL = r"(?:patients?|donors?|individuals?|subjects?|persons?|mice|mouse|animals?|病人|患者|捐贈者|個體|受試者|小鼠|老鼠)"
_SINGLE = _RE.compile(
    rf"\b(?:our|the|a|this)\s+only\s+(?:\w+\s+)?{_INDIVIDUAL}\b"
    rf"|\b(?:only|just)\s+one\s+(?:\w+\s+)?{_INDIVIDUAL}\b"
    rf"|\b(?:a\s+single|one|single)\s+(?!per\b|each\b|for\b|of\b)(?:[\w-]+\s+)?{_INDIVIDUAL}(?![\w-])"
    r"(?!\s+to\s+(?:the\s+)?(?:next|another|other))"
    rf"|(?<!每)(?:同一|只有一|僅一|單一|唯一|一)[位名個隻](?:[^\s，。；、]{{0,8}}?){_INDIVIDUAL}", _RE.I)
_REPLICATED = _RE.compile(
    r"\b(?:\d+|two|three|four|five|six|several|multiple)\s+(?:\w+\s+)?(?:replicates?|libraries|biopsies|captures|"
    r"runs|batches|sections|samples|donors|patients|time\s?points|stages|lanes|pools|slices|wells|organoids|lines|"
    r"visits)\b|\breplicates?\b|cell[- ]?types?|clusters?|重複|細胞類型|時間點", _RE.I)
_NO_REPLICATE = _RE.compile(r"\bno\s+(?:other\s+)?(?:donors?|patients?|individuals?|(?:biological\s+)?replicates?)"
                           r"(?:\s+(?:and|or)\s+no\s+(?:other\s+)?(?:donors?|patients?|replicates?))?"
                           r"|沒有(?:其他)?(?:捐贈者|病人|重複)", _RE.I)
_MANY_INDIVIDUALS = _RE.compile(r"\b(?:[2-9]|\d{2,}|two|three|four|five|six|seven|eight|nine|ten|several|multiple)\s+"
                               r"(?:\w+\s+)?(?:donors|patients|individuals|subjects|mice|animals)\b", _RE.I)
_THREE_PLUS_UNITS = _RE.compile(  # "exactly two biopsies" across two sides is one per side (F010); three or more may not be
    r"\b(?:[3-9]|\d{2,}|three|four|five|six|seven|eight|nine|ten|several|multiple)\s+(?:\w+\s+)?(?:replicates?|"
    r"libraries|biopsies|captures|runs|batches|sections|samples|time\s?points|stages|lanes|pools|slices|wells|"
    r"organoids|lines|visits|treated|controls?)\b", _RE.I)
_ONE_PER_SIDE = _RE.compile(  # "one donor per condition" (Gemini review); the unit is named: "one network per condition"
    r"\b(?:one|a\s+single)\s+(?:donor|patient|individual|subject|mouse|animal|sample|library|biopsy)\s+"
    r"(?:per|for\s+each|in\s+each)\s+(?:condition|group|side|arm|region|state|genotype|treatment)\b", _RE.I)


def single_source_comparison(task: str) -> str:
    """R9 (2026-11-21, scorpion.yaml: "A comparison needs compare_by in group_by and at least two built networks on each
    side"): the words stating a single patient or donor, in a request that compares two named sides and names no
    replicate, other grouping column or second individual. A request about each cell (X032: per-cell networks) is
    left to R6, whose refusal states no reason: R9's reason would be wrong there. Empty otherwise."""
    if not _COMPARE.search(task) or _PER_CELL.search(task):
        return ""
    plain = " . ".join(part for part in _clauses(task) if not _NEGATION.search(part))
    if (none := _NO_REPLICATE.search(task)) and not _MANY_INDIVIDUALS.search(plain) \
            and not _THREE_PLUS_UNITS.search(plain):  # "6 organoids (3 treated vs 3 control)" can (review)
        return none.group(0).strip()  # F010: "There are no other donors and no replicates."
    if _REPLICATED.search(plain):
        return ""
    found = _SINGLE.search(task) or _ONE_PER_SIDE.search(task)
    return found.group(0).strip() if found else ""


_DOUBT = _RE.compile(
    r"\bnot\s+sure\b|\bunsure\b|\bdon'?t\s+know\b|\bdo\s+not\s+know\b|\bhaven'?t\s+(?:decided|settled|found\s+out|"
    r"checked)|\bnot\s+(?:yet\s+)?(?:decided|settled|certain)\b|\bmay\s+or\s+may\s+not\b|\bno\s+idea\b|"
    r"\bwondering\s+whether\b|不確定|不知道|還沒決定|還沒確定|不清楚|還在問|沒把握", _RE.I)


def stated_doubt(task: str) -> str:
    """R1's second source (2026-11-21, F036): the user's own words of doubt in their newest words, found by code when
    the form's unsure_quote is empty. Replayed on every saved form: R1 turned 30 gold-do questions into runs and none
    of them has these words; 3 gold-ask ones do."""
    found = _DOUBT.search(latest_words(task))
    return found.group(0) if found else ""


_PRIORS_HELD = _RE.compile(  # motif or PPI priors only: a miRNA-target "prior" is not what SPONGE builds (L079)
    r"\b(?:motif|PPI|protein[- ]protein)\b.{0,80}?\b(?:priors?|files?|networks?|edge lists?)\b"
    r"|\bpriors?\b.{0,40}?\b(?:motif|PPI)\b", _RE.I)
_BUILD_WORDS = _RE.compile(  # any build of priors asked for keeps SPONGE ("also build human priors for SOX2")
    r"\b(?:build|generate|create|make|construct|produce|prepare|derive)\w*\b.{0,40}?\bpriors?\b"
    r"|\bSPONGE\b|建立.{0,10}先驗|產生.{0,10}先驗", _RE.I)
_HOLD = _RE.compile(r"\b(?:have|has|had|ready|available|on hand|in hand|prepared|got)\b|手上|已有|準備好", _RE.I)


def priors_on_hand(task: str) -> bool:
    """The request says the user already has motif and PPI priors (a clause naming priors with "have", "ready",
    "available"... and no negation)."""
    return any(_PRIORS_HELD.search(part) and _HOLD.search(part) and not _NEGATION.search(part)
               for part in _clauses(task))


_LATER = _RE.compile(r"\b(?:afterwards?|later|downstream|next step|follow[- ]up analys\w*|eventually)\b|之後|以後|後續",
                    _RE.I)


def doubt_before_run(task: str) -> str:
    """R1 the other way (2026-11-22, user: why run it when the user already said they are not sure?): the user's own words of doubt, in their
    newest words, about something this run depends on -- the clause holding the doubt words, unless it is about a
    later step ("whether I'll look at individual samples afterwards", F030). Empty when there is none."""
    words = latest_words(task)
    for part in _RE.split(r"[.;!?\n。；！？]", words):
        if _DOUBT.search(part) and not _LATER.search(part):
            return part.strip()
    return ""


_PER_CELL_NETWORK = _RE.compile(
    r"\b(?:network|PANDA|LIONESS)\w*\b[^.;]{0,60}?\b(?:for|per|of)\s+(?:each|every|every single|each single)\s+"
    r"(?:individual\s+)?cell\b(?![- ]?(?:types?|lines?|populations?|clusters?|states?|groups?))"
    r"|\b(?:each|every)\s+(?:individual\s+|single\s+)?cell\b(?![- ]?(?:types?|lines?|populations?|clusters?|states?|groups?))"
    r"[^.;]{0,40}?\b(?:its|their|own|separate)\b[^.;]{0,30}?\bnetwork"
    r"|\b(?:that|this|each|every|the)\s+cell'?s\s+own\b[^.;]{0,40}?\bnetwork"
    r"|\bfor\s+each\s+of\s+the\s+[^.;]{0,40}?\bcells\b[^.;]{0,80}?\bown\b[^.;]{0,40}?\bnetwork"
    r"|每(?:一)?(?:個|顆)細胞(?!類型|株|群)[^。；]{0,20}?網路", _RE.I)


def per_cell_networks(task: str) -> str:
    """R11 (2026-11-22; scorpion.yaml: one network per group of cells): the request's words asking for a network for
    each individual cell. A cell type, line, population or cluster is a group, not a cell."""
    found = _PER_CELL_NETWORK.search(task)
    return found.group(0).strip() if found else ""


_PER_SAMPLE = _RE.compile(r"\b(?:each|every|per|individual|separate|own)\b|sample-specific|patient-specific|每(?:一)?(?:個|位|隻)", _RE.I)
_NAMED_SCORPION = _RE.compile(r"(?<![A-Za-z0-9])SCORPION(?![A-Za-z0-9])", _RE.I)
_NAMED_BULK_TOOL = _RE.compile(r"(?<![\w-])(?:LIONESS(?:-PANDA)?|PANDA)(?![\w-])", _RE.I)


def data_unit_label(task: str) -> str:
    from ..routing.data_unit import data_unit_of

    return "single cells" if data_unit_of(task) == "single_cells" else "bulk samples"


def _data_unit_swap(task: str, steps: list[str]) -> list[str]:
    """R12 (2026-11-22; KNOWN_LIMITATIONS: "SCORPION is only for single cells, and only single cells go to SCORPION",
    read by code from the request's words, pseudo-bulk counting as bulk -- routing.data_unit): a network workflow the
    model chose for the other data unit is swapped, unless the user named it. Bulk SCORPION becomes LIONESS-PANDA when
    the request asks for one network per sample or patient, else PANDA; single-cell PANDA/LIONESS-PANDA becomes
    SCORPION."""
    from ..routing.data_unit import data_unit_of

    unit = data_unit_of(task)
    out = list(steps)
    from ..routing.data_unit import _SINGLE_CELL

    # Only with no single-cell word at all: "either the cell-level matrix or the pseudo-bulk one" offers both (D007).
    if unit == "bulk_samples" and "SCORPION" in out and not _NAMED_SCORPION.search(task) and not _SINGLE_CELL.search(task):
        out[out.index("SCORPION")] = "LIONESS-PANDA" if _PER_SAMPLE.search(task) else "PANDA"
    stated_bulk = any(_RE.search(r"\bbulk\b|整體組織|塊狀", part, _RE.I) and not _NEGATION.search(part)
                      for part in _clauses(task))  # "bulk RNA-seq ... single-cell only as a reference" (review)
    if unit == "single_cells" and not _NAMED_BULK_TOOL.search(task) and not stated_bulk:
        bulk = [name for name in out if name in ("PANDA", "LIONESS-PANDA")]
        if bulk and "SCORPION" not in out:
            out[out.index(bulk[0])] = "SCORPION"
            out = [name for name in out if name not in ("PANDA", "LIONESS-PANDA")]
    return list(dict.fromkeys(out))


_EXPRESSION_HELD = _RE.compile(r"\b(?:expression|RNA-?seq|counts?|TPM|CPM|[FR]PKM|microarray|transcriptom\w*|"
                              r"batch[- ]corrected|normali[sz]ed\s+(?:matrix|data|values|table))\b|表現|表達|定序", _RE.I)
_NETWORKS_HELD = _RE.compile(
    r"\bnetworks?\b[^.;]{0,60}?\b(?:computed|built|made|generated|have|from|table|file|output)\b"
    r"|\b(?:computed|built|made|generated|have)\b[^.;]{0,60}?\bnetworks?\b|\btf\b[^.;]{0,20}\bgene\b[^.;]{0,20}columns?"
    r"|LIONESS(?:-PANDA)? (?:output|table|networks?)|網路(?:表|檔)", _RE.I)


def expression_without_networks(task: str) -> bool:
    """R4 for a PORCUPINE first step (2026-11-22, L018; porcupine.yaml: expression_matrix is an incompatible input,
    LIONESS-PANDA hands its sample-specific networks to PORCUPINE): the request states expression data and no network
    table of its own."""
    plain = " . ".join(part for part in _clauses(task) if not _NEGATION.search(part))
    return bool(_EXPRESSION_HELD.search(plain)) and not _NETWORKS_HELD.search(plain)


_GONE = _RE.compile(r"\b(?:deleted|lost|gone|discarded|no longer (?:exists?|available|there)|can'?t be recovered|"
                   r"cannot be recovered|were not (?:kept|saved)|was not (?:kept|saved)|never (?:kept|saved))\b", _RE.I)
_EXPRESSION_WORDS = _RE.compile(r"\b(?:expression(?: data| matrix| values| table)?|RNA-?seq data|raw counts|count matrix|"
                                r"read counts|normali[sz]ed data)\b", _RE.I)


def expression_gone(task: str) -> str:
    """R13 (2026-11-23, A114; every in-scope workflow's required inputs include an expression matrix and none produces
    one): the clause saying the user's expression data no longer exist ("the original expression data were deleted and
    can't be recovered"), when no clause says they still have one. Empty otherwise."""
    gone = [part.strip() for part in _clauses(task) if _EXPRESSION_WORDS.search(part) and _GONE.search(part)]
    if not gone:
        return ""
    # Any other clause naming expression data (TPM, counts, RNA-seq ...) means some expression is still there: "we
    # kept only the TPM matrix; the read counts were not saved" is R8's case, not this one.
    held = any(_EXPRESSION_HELD.search(part) and not _GONE.search(part) and not _NEGATION.search(part)
               for part in _clauses(task))
    return "" if held else gone[0]


_FEW_CELLS = _RE.compile(r"\b(?:only\s+)?(\d{1,2})\s+(?:single\s+)?(?:cells|nuclei)\b(?:\s+in\s+total|\s+in\s+all|\s+altogether)?",
                         _RE.I)
_FILTERED = _RE.compile(r"\b(?:filter(?:ed)?(?: out)?|removed?|discard(?:ed)?|exclud(?:ed|e)|dropped|QC)\b", _RE.I)
_NEGATIVE_VALUES = _RE.compile(r"\bz-?scores?\b|\bnegative values?\b|\bscaled\b[^.;]{0,30}\b(?:matrix|data)\b", _RE.I)


def scorpion_input_broken(task: str) -> tuple[str, str] | None:
    """R14 (2026-11-23; scorpion.yaml "A network is built only for a group of at least 30 cells", "SCORPION never uses
    fewer than 30"; scorpion_io: non-negative values only): ("label", code-written reason) when the request states fewer
    than 30 cells in total, or that its only matrix holds negative (scaled, z-score) values with no counts left."""
    many = any(int(n.replace(",", "")) >= 30 for n in _RE.findall(r"\b(\d[\d,]*)\s+(?:single\s+)?(?:cells|nuclei)\b", task, _RE.I))
    for part in _clauses(task):
        found = _FEW_CELLS.search(part)
        if (found and int(found.group(1)) < 30 and not many and not _FILTERED.search(part)
                and _RE.search(r"\b(?:only|total|in all|altogether)\b", part, _RE.I)):  # review: "filtered out only 15"
            return (found.group(0), f'SCORPION builds a network only from a group of at least 30 cells, and the request '
                                    f'has "{found.group(0).strip()}".')
    negative = next((part.strip() for part in _clauses(task) if _NEGATIVE_VALUES.search(part)), "")
    if negative and expression_gone(task):
        return ("negative values", f'SCORPION reads non-negative counts, and the request says "{negative}" while '
                                   f'"{expression_gone(task)}".')
    return None


FOLLOW_UP = "\nUser follow-up: "


def latest_words(task: str) -> str:
    """The user's newest words: the follow-up of a combined turn, else the whole request."""
    return task.rsplit(FOLLOW_UP, 1)[1] if FOLLOW_UP in task else task
