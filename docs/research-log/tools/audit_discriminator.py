"""Audit the semantic discriminator across recorded legacy traces (Log 212).

Usage: python docs/research-log/tools/audit_discriminator.py [--since-log N]

For every traced trial where the discriminator ran, reports whether it ended
accepted (the tie became an exact match), rejected or failed, and grades each
accepted workflow against the expected answer where one is known: the routing
corpora, the blind expectations, and the Log 168 tie prompts. `--since-log N`
keeps only recordings made with the code of Log N or later (default 176, the
first rounds after Log 174 stopped restating tags from discriminating).

Only discriminator events are read (`routing.semantic_discriminator_*`); other
events also end in `_accepted`.
"""
import argparse
import collections
import json
import re

from traces import RESEARCH, ROOT, report_paths, load_report


def expectations() -> dict:
    expected = {}
    for name in ("routing_semantic_families.json", "routing_semantic_variants.json", "routing_scenarios.json"):
        for case in json.loads((ROOT / "tests" / name).read_text(encoding="utf-8")):
            status = case["expected"]["status"]
            expected[case["id"]] = set(case["expected"].get("actions") or []) if status == "exact" else None
    for key, case in json.loads((RESEARCH / "blind" / "expectations.json").read_text(encoding="utf-8")).items():
        if key.startswith("case"):
            for language in ("en", "zh"):
                expected[f"{key}-{language}"] = set(case["accept"]) or None
    expected.update({
        "t1-otter": {"run_otter"}, "t1-giraffe": {"run_giraffe"}, "t1-panda": {"run_panda"},
        "t2-cobra": {"run_cobra"}, "t2-lioness": {"run_lioness_coexpression"},
    })
    return expected


def recorded_after(name: str, since: int) -> bool:
    found = re.search(r"trace_?log(\d+)", name)
    if found:
        return int(found.group(1)) >= since
    if since <= 180:
        return bool(re.search(r"trace18\d|trace_blind|2026-09-27", name))
    return "2026-09-27" in name


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--since-log", type=int, default=176)
    args = parser.parse_args()
    expected = expectations()
    outcomes = collections.Counter(); accepted = collections.Counter(); rejected = collections.Counter()
    tokens = []; trials = 0
    for path in report_paths():
        if not recorded_after(path.name, args.since_log):
            continue
        report = load_report(path)
        if report.get("metadata", {}).get("semantic_contract") != "legacy":
            continue
        for row in report["results"]:
            trace = row.get("_trace")
            if not trace:
                continue
            trials += 1
            events = [e for e in trace["events"] if e["type"].startswith("routing.semantic_discriminator_")]
            if not events:
                continue
            tokens.extend(c["usage"]["total_tokens"] for c in trace["calls"]
                          if c["schema"] == "SemanticDiscriminator" and (c.get("usage") or {}).get("total_tokens"))
            kinds = {e["type"].rsplit("_", 1)[-1]: e["payload"] for e in events}
            final = next((kind for kind in ("accepted", "failed", "rejected") if kind in kinds), "none")
            outcomes[final] += 1
            if final == "accepted":
                actions = set(kinds["accepted"].get("matched_actions") or [])
                answer = expected.get(row["id"], "unknown")
                verdict = ("no expectation" if answer == "unknown" else "expected a tie" if answer is None
                           else "right" if actions <= answer else "WRONG")
                accepted[(row["id"], tuple(kinds["accepted"].get("selection_tags") or []), tuple(sorted(actions)), verdict)] += 1
            if final == "rejected":
                rejected[kinds["rejected"].get("reason")] += 1
    print(f"legacy trials recorded since Log {args.since_log}: {trials}; discriminator runs: {sum(outcomes.values())}")
    print("final outcomes:", dict(outcomes))
    print("accepted (id, tags, workflows, verdict):")
    for key, count in accepted.most_common():
        print(f"  {count} {key}")
    print("rejection reasons:", dict(rejected))
    if tokens:
        print(f"tokens per discriminator call: mean {sum(tokens) // len(tokens)} over {len(tokens)} calls")


if __name__ == "__main__":
    main()
