"""Log 309 exploration: recorded per-sample readings whose request has no per-unit word.

Usage (repository root): python docs/research-log/scale-unit-2026-10-02/scan_unit.py
Reads every traced report under docs/research-log/ and prints, per distinct
prompt, the readings that claim a per-sample scale (granularity or the
`sample_specific` tag) while the request names no unit (sample, patient, ...).
`PER_UNIT` is the prototype the pre-declaration (Log 309) quotes.
"""
import gzip
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RESEARCH = ROOT / "docs" / "research-log"

_UNIT = (r"(?:samples?|patients?|subjects?|persons?|people|individuals?|donors?|participants?|cases?|"
         r"specimens?|biops(?:y|ies)|mice|mouse|animals?|cell[- ]lines?|tumou?rs?)")
# Any word that names one unit at a time. Loose on purpose: it only decides
# that a per-sample reading has *no* support at all in the request.
PER_UNIT = re.compile(
    r"\b(?:each|every)\b(?:\s+(?:one\s+)?of)?(?:\s+(?:the|our|these|those|its|their|all|\d+))*"
    r"(?:\s+[\w-]+)?\s+" + _UNIT + r"\b|"
    r"\bper[- ](?:[\w-]+[- ])?" + _UNIT + r"\b|"
    r"\b(?:individual|single|separate)\s+(?:[\w-]+\s+)?" + _UNIT + r"\b|"
    r"\b(?:sample|patient|subject|person|individual|donor|participant|tumou?r|case)[- ](?:specific|level|wise)\b|"
    r"\b(?:individuali[sz]ed|personali[sz]ed)\b|\bsingle[- ]sample\b|\bleave[- ]one[- ]out\b|"
    r"\bfrom one \w+ to (?:the )?(?:next|another)\b|\b(?:their|its|his|her)\s+own\s+(?:[\w-]+\s+){0,4}networks?\b|"
    r"每(?:一)?(?:個|位|名|例|隻)?(?:樣本|病患|病人|患者|個體|受試者|捐贈者|腫瘤|小鼠|人)|"
    r"各(?:個|位)?(?:樣本|病患|病人|患者|個體)|個別|各自|單一樣本|個體|樣本特異|病患特異|個人化|逐一|留一",
    re.I,
)


def per_unit_mention(task):
    match = PER_UNIT.search(task)
    return match.group(0) if match else None


def main():
    seen = {}
    for path in sorted({*RESEARCH.glob("**/live-*.json"), *RESEARCH.glob("**/live-*.json.gz")}):
        if ".provider-error" in path.name or ".unpaired" in path.name:  # void by rule, never analyzed
            continue
        opener = gzip.open if path.suffix == ".gz" else open
        try:
            with opener(path, "rt", encoding="utf-8") as handle:
                report = json.load(handle)
        except (OSError, ValueError):
            continue
        for row in report.get("results", []) if isinstance(report, dict) else []:
            trace = row.get("_trace") if isinstance(row, dict) else None
            if not trace or not trace.get("decision"):
                continue
            hypotheses = trace["decision"].get("outcome_hypotheses") or []
            if not any(h["outcome"].get("granularity") == "sample_specific"
                       or "sample_specific" in (h["outcome"].get("selection_tags") or []) for h in hypotheses):
                continue
            entry = seen.setdefault(trace["prompt"], [0, set(), row.get("id")])
            entry[0] += 1
            decision = trace["decision"]
            entry[1].add((decision.get("capability_match_status"), tuple(decision.get("matched_actions") or ())))
    unnamed = [(task, value) for task, value in seen.items() if per_unit_mention(task) is None]
    print("distinct prompts with a per-sample reading:", len(seen), "trials", sum(v[0] for v in seen.values()))
    print("without a per-unit word:", len(unnamed), "trials", sum(v[0] for _, v in unnamed))
    for task, (count, endings, case) in sorted(unnamed, key=lambda item: -item[1][0]):
        print("-", count, case, sorted(endings)[:3], "|", " ".join(task.split())[:230])


if __name__ == "__main__":
    main()
