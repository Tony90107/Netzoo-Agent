"""Path (b) prototype: verify the model's proposals deterministically and score the strategies.

Usage (repository root): python3 docs/research-log/purpose-contract-2026-10-04/b_prototype/verify.py <tag> [--detail]
Reads b_prototype/<tag>-proposals.json (propose.py) and scores, against the labels:
  S0 witness   -- the live word witnesses (v1+PN+CN), no model;
  S1 model     -- the model's values, quotes only checked to be in the request;
  S2 verified  -- S1 plus the deterministic checks below;
  S3 union     -- the witness's design and conclusions when it finds them, else S2's.
Checks (S2): the quote is in the request; it contains a cue word for its value; the cue is
not negated before or after it in its clause (the witnesses' _negated, PN and CN); a
"predict" of targets or binding is network inference; a design quote naming a technical
pairing (paired-end, read pairs, omics layers, batches, normalization) is no design; a
group difference needs a verified design. Nothing calls a model.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from netzoo_agent_core.routing import study_purpose as witness  # noqa: E402

LABELS = {}
for name, path in {"dev340": HERE.parent / "dev_log340.json", "heldout1": HERE.parent / "heldout" / "heldout.json",
                   "heldout2": HERE.parent / "heldout2" / "heldout.json", "heldout3": HERE.parent / "heldout3" / "heldout.json",
                   "heldout4": HERE.parent / "heldout4" / "heldout.json"}.items():
    for item in json.loads(path.read_text())["items"]:
        LABELS[(name, item["id"])] = item

_I = re.I
CLAIM_CUES = {
    "group_difference": re.compile(
        r"differ\w*|chang\w*|shift\w*|alter\w*|rewir\w*|reshap\w*|compar\w*|\bbetween\b|versus|\bvs\.?\b|"
        r"relative\s+to|disrupt\w*|reorgani\w*|remodel\w*|diverg\w*|perturb\w*|unlike|"  # not "respond": "non-responders" names a group
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
DESIGN_CUES = {
    "paired": re.compile(
        r"\bsame\b|\beach\b|\bboth\b|before|after|again|\bpre\b|pre-|post-|\bpost\b|time|visit\w*|trimester\w*|"
        r"\bdays?\b|weeks?|months?|years?|split|halves|\bhalf\b|cross-?over|random\s+order|paired|matched|"
        r"repeat\w*|longitudinal|serial\w*|baseline|follow-?up|admission|discharge|diagnosis|relapse|recovery|"
        r"stable|during|from\s+the\s+same", _I),
    # A contrast: two sides joined, or named groups, levels or arms. "85 lines, each from a different
    # donor" is one collection.
    "groups": re.compile(
        r"\band\b|\bvs\.?\b|versus|\bor\b|between|compared|\bplus\b|groups?|arms?|levels?|doses?|"
        r"concentrations?|strains?|genotypes?|cohorts?", _I),
}
_TECHNICAL_PAIRING = re.compile(
    r"paired-end|read\s+pairs|matri\w*|layers?|omics|batch\w*|librar\w*|lanes?|replicates?|litters?|"
    r"normali[sz]\w*|filter\w*", _I)
_DATA_TYPE = re.compile(
    r"expression|methylation|RNA-?seq|microarray|arrays?|proteom\w*|metabolom\w*|small-?RNA|miRNA|ATAC|ChIP|"
    r"genotyp\w*|SNPs?|CNVs?|mutation\w*|transcriptom\w*", _I)
_PREDICT_NETWORK = re.compile(
    r"predict\w*\s+(?:the\s+|their\s+|its\s+)?(?:target\w*|binding|sites?|motifs?|interactions?|edges?|regulat\w*)", _I)


def _normal(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def locate(task: str, quote: str) -> int | None:
    """Start of the quote in the request (case and spacing ignored), or None."""
    quote = quote.strip().strip('"').strip()
    if not quote:
        return None
    index = task.find(quote)
    if index >= 0:
        return index
    normal_task, normal_quote = _normal(task), _normal(quote)
    index = normal_task.find(normal_quote)
    if index < 0:
        return None
    # Map back approximately: count non-collapsed characters (prototype precision is enough).
    return task.lower().find(normal_quote.split(" ")[0], max(0, index - 5))


def verify_claim(task: str, claim: str, quote: str) -> tuple[bool, str]:
    start = locate(task, quote)
    if start is None:
        return False, "quote_not_in_request"
    cue = CLAIM_CUES[claim].search(task, start, start + len(quote))
    if cue is None:
        return False, "no_cue"
    # Every cue of this kind in the quote must survive the negation checks; one surviving cue suffices.
    for match in CLAIM_CUES[claim].finditer(task, start, start + len(quote)):
        if witness._negated(task, match.start()) or witness._negated_after(task, match.end()):
            continue
        if claim == "causal" and witness._cause_as_variable(task, match):
            continue
        if claim == "prediction" and _PREDICT_NETWORK.match(task, match.start()):
            continue
        return True, "ok"
    return False, "negated_or_vetoed"


def verify_design(task: str, design: str, quote: str) -> tuple[bool, str]:
    if design == "none":
        return True, "none"
    start = locate(task, quote)
    if start is None:
        return False, "quote_not_in_request"
    span = task[start:start + len(quote)]
    if not DESIGN_CUES[design].search(span):
        return False, "no_cue"
    timed = re.search(r"\bsame\b|before|after|visit|trimester|split|cross|\bdays?\b|weeks?|months?|baseline", span, _I)
    if _TECHNICAL_PAIRING.search(span) and not timed:
        return False, "technical"
    # "matched expression and methylation arrays": two data types from the same samples.
    data_types = {m.group(0).lower() for m in _DATA_TYPE.finditer(span)}
    if design == "paired" and len(data_types) >= 2 and not timed:
        return False, "two_data_types"
    if witness._negated(task, start + 1) or re.search(r"\bno\s+(?:control|comparison)|\bnobody\b|\bnone\s+of", span, _I):
        return False, "negated"
    return True, "ok"


def model_result(row, verified: bool):
    proposal = row.get("proposal")
    if not proposal:
        return None
    task = row["prompt"]
    design = proposal["design"]
    if design != "none":
        ok, _ = verify_design(task, design, proposal["design_span"]) if verified else (
            locate(task, proposal["design_span"]) is not None, "")
        design = design if ok else "none"
    claims = []
    for item in proposal["claims"]:
        ok = (verify_claim(task, item["claim"], item["text_span"])[0] if verified
              else locate(task, item["text_span"]) is not None)
        if ok and item["claim"] not in claims:
            claims.append(item["claim"])
    if verified and design == "none":
        claims = [claim for claim in claims if claim != "group_difference"]
    return design, claims


def witness_result(task):
    purpose = witness.study_purpose(task)
    return purpose.design or "none", [claim for claim, _ in purpose.claims]


def strategies(row):
    w = witness_result(row["prompt"])
    m1 = model_result(row, False) or w
    m2 = model_result(row, True) or w
    union_design = w[0] if w[0] != "none" else m2[0]
    union_claims = w[1] or [c for c in m2[1] if c != "group_difference" or union_design != "none"]
    return {"S0 witness": w, "S1 model": m1, "S2 verified": m2, "S3 union": (union_design, union_claims)}


def score(rows):
    totals = defaultdict(Counter)
    errors = defaultdict(list)
    for row in rows:
        label = LABELS[(row["set"], row["id"])]
        for name, (design, claims) in strategies(row).items():
            t = totals[name]
            primary = claims[0] if claims else "none"
            if label["comparison_design"] != "none":
                t["design_labelled"] += 1
                t["design_hit"] += design == label["comparison_design"]
            if design != "none" and design != label["comparison_design"]:
                t["design_false"] += 1
                errors[name].append(f"design {row['set']}/{row['id']} r{row['rep']}: {label['comparison_design']} -> {design}")
            if label["claim_kind"] != "none":
                t["claim_labelled"] += 1
                t["claim_hit"] += primary == label["claim_kind"]
            if primary != "none" and primary != label["claim_kind"]:
                t["claim_false"] += 1
                errors[name].append(f"claim {row['set']}/{row['id']} r{row['rep']}: {label['claim_kind']} -> {claims}")
            if set(claims) & {"causal", "prediction"} - {label["claim_kind"]}:
                t["gap_false"] += 1
                errors[name].append(f"GAP {row['set']}/{row['id']} r{row['rep']}: {label['claim_kind']} -> {claims}")
    return totals, errors


def main(tag: str, detail: bool):
    rows = json.loads((HERE / f"{tag}-proposals.json").read_text())
    reps = sorted({row["rep"] for row in rows})
    print(f"{len(rows)} proposals, {len(reps)} repeats; counts are summed over repeats")
    for subset in (None, "dev340", "heldout1", "heldout2", "heldout3", "heldout4"):
        chosen = [row for row in rows if subset is None or row["set"] == subset]
        totals, errors = score(chosen)
        print(f"\n== {subset or 'ALL'} ==")
        for name, t in totals.items():
            print(f"  {name:12} design {t['design_hit']}/{t['design_labelled']} "
                  f"({t['design_hit'] / max(1, t['design_labelled']):.0%}) false {t['design_false']} | "
                  f"claim {t['claim_hit']}/{t['claim_labelled']} ({t['claim_hit'] / max(1, t['claim_labelled']):.0%}) "
                  f"false {t['claim_false']} | false gap {t['gap_false']}")
        if detail and subset is None:
            for name in ("S2 verified", "S3 union"):
                print(f"\n  errors {name}:")
                for line in sorted(set(errors[name])):
                    print("   ", line)


if __name__ == "__main__":
    main(sys.argv[1], "--detail" in sys.argv)
