"""Log 313 exploration: every recorded multi_omic_network reading, and whether the request names a second layer.

Usage (repository root): python docs/research-log/unquoted-sibling-2026-10-02/scan_multiomic.py
`LAYER` is the prototype witness the pre-declaration quotes: any word for an
omics layer besides gene expression, or for combining layers.
"""
import gzip
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from netzoo_agent_core.contracts.outcomes import OutcomeHypothesis  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import match_semantic_request  # noqa: E402

LAYER = re.compile(
    r"omic|methylat|proteom|protein (?:abundance|level|expression)|metabolo|metabolite|lipid|phospho|"
    r"ATAC|chromatin|accessib|histone|ChIP|copy[- ]?number|\bCNVs?\b|genotyp|\bSNPs?\b|microbio|"
    r"small[- ]RNA|mi(?:cro)?[- ]?RNA (?:expression|levels?|profiles?|data)|layers?\b|two (?:data|measurement|assay)|"
    r"多體學|多组学|多組學|甲基化|蛋白質體|蛋白质组|代謝|代谢|染色質|染色质|層|层",
    re.I,
)


def traces():
    for path in sorted({*ROOT.glob("docs/research-log/**/live-*.json"), *ROOT.glob("docs/research-log/**/live-*.json.gz")}):
        if ".provider-error" in path.name or ".unpaired" in path.name:
            continue
        opener = gzip.open if path.suffix == ".gz" else open
        try:
            with opener(path, "rt", encoding="utf-8") as handle:
                report = json.load(handle)
        except (OSError, ValueError):
            continue
        for row in report.get("results", []) if isinstance(report, dict) else []:
            trace = row.get("_trace") if isinstance(row, dict) else None
            if trace and trace.get("decision"):
                yield row.get("id"), trace


def main():
    prompts, trials, changes, seen = {}, Counter(), defaultdict(Counter), set()
    for case, trace in traces():
        task, raw = trace["prompt"], trace["decision"].get("outcome_hypotheses") or []
        if not any(item["outcome"]["artifact_type"] == "multi_omic_network" for item in raw):
            continue
        witness = LAYER.search(task)
        prompts[(case, task)] = witness.group(0) if witness else None
        trials[(case, task)] += 1
        if witness:
            continue
        hypotheses = [OutcomeHypothesis.model_validate(item) for item in raw]
        kept = [h for h in hypotheses if h.outcome.artifact_type != "multi_omic_network"]
        key = json.dumps([task, raw], sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        before = match_semantic_request(task, hypotheses, request_mode="guidance")
        after = match_semantic_request(task, kept, request_mode="guidance") if kept else None
        changes[(case, task)][(len(hypotheses), before.status, tuple(before.matched_actions or before.hypothesis_actions),
                               after.status if after else "(no reading left: untouched)",
                               tuple((after.matched_actions or after.hypothesis_actions) if after else ()))] += 1
    named = {key: value for key, value in prompts.items() if value}
    print(f"prompts with a multi-omic reading: {len(prompts)} ({sum(trials.values())} trials); "
          f"naming a second layer: {len(named)} ({sum(trials[k] for k in named)} trials)")
    for (case, task), word in sorted(named.items(), key=lambda item: -trials[item[0]]):
        print(f"  kept  {trials[(case, task)]:3d}x {case} [{word}]")
    print("naming no second layer:")
    for (case, task), outcomes in sorted(changes.items(), key=lambda item: -trials[item[0]]):
        print(f"- {case} ({trials[(case, task)]} trials) | {' '.join(task.split())[:140]}")
        for (n, bs, ba, as_, aa), count in outcomes.most_common():
            print(f"    {count}x {n} reading(s): {bs} {list(ba)} -> {as_} {list(aa)}")


if __name__ == "__main__":
    main()
