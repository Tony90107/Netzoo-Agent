"""Log 380: the data-facts call (TF priors and miRNA) on a labelled set. Offline; production code only.

Usage (repository root, provider key in .env, never printed):
  set -a; . ./.env; set +a; python3 docs/research-log/applicability-2026-10-06/facts_eval.py <heldout.json> <tag> <repeats>
Same binding as the graph (gpt-4o-mini, temperature 0, strict function calling) and Log 376's
d_eval.py. Scores the verified readings against `priors_stated` and, when the set labels it,
`mirna_stated` (true -> stated; a request that negates miRNA -> ruled_out when the set says so).
Writes <tag>-calls.json beside this script.
"""
import json
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
from netzoo_agent_core.contracts.data_facts import DataFactsProposal  # noqa: E402
from netzoo_agent_core.graph.data_facts_call import build_data_facts_messages, verify_data_facts  # noqa: E402
from netzoo_agent_core.interpretation.semantic_repair import semantic_payload  # noqa: E402
from netzoo_agent_core.llm import build_llm  # noqa: E402


def call(llm, task):
    adapter = llm.with_structured_output(DataFactsProposal, method="function_calling", include_raw=True, strict=True)
    try:
        payload, _raw = semantic_payload(adapter.invoke(build_data_facts_messages(task)))
        if hasattr(payload, "model_dump"):
            payload = payload.model_dump()
        return DataFactsProposal.model_validate(payload).model_dump(), None
    except Exception as error:  # recorded, never retried
        return None, type(error).__name__


def mirna_label(item):
    if "mirna_label" in item:
        return item["mirna_label"]
    if item.get("mirna_stated") is True:
        return "stated"
    return None  # the set does not say: scored only for false "stated"


def main(path, tag, repeats):
    items = json.loads(Path(path).read_text())["items"]
    llm = build_llm("openai/gpt-4o-mini", 0.0, max_output_tokens=500, timeout_seconds=60)
    jobs = [(item, rep) for rep in range(1, repeats + 1) for item in items]
    with ThreadPoolExecutor(8) as pool:
        results = list(pool.map(lambda job: call(llm, job[0]["prompt"]), jobs))
    rows = [{"id": item["id"], "rep": rep, "prompt": item["prompt"], "proposal": proposal, "error": error}
            for (item, rep), (proposal, error) in zip(jobs, results)]
    (HERE / f"{tag}-calls.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    by_id = {item["id"]: item for item in items}
    priors, mirna, lines, failed = Counter(), Counter(), [], 0
    for row in rows:
        if row["proposal"] is None:
            failed += 1
            continue
        entry, rejected = verify_data_facts(row["prompt"], DataFactsProposal.model_validate(row["proposal"]))
        item = by_id[row["id"]]
        priors[(item.get("priors_stated"), entry["priors"])] += 1
        mirna[(mirna_label(item), entry["mirna"])] += 1
        if entry["priors"] != item.get("priors_stated") or (mirna_label(item) and entry["mirna"] != mirna_label(item)) \
                or (not mirna_label(item) and entry["mirna"] == "stated"):
            lines.append(f"   {row['id']} r{row['rep']}: priors {item.get('priors_stated')}->{entry['priors']} "
                         f"{row['proposal']['priors_span']!r}; mirna {mirna_label(item)}->{entry['mirna']} "
                         f"{row['proposal']['mirna_span']!r}; rejected {rejected}")
    def count(table, label=None, read=None, not_label=None):
        return sum(n for (l, r), n in table.items()
                   if (label is None or l == label) and (read is None or r == read) and (not_label is None or l != not_label))
    print(f"{tag}: {len(rows)} calls, {failed} failed")
    print("  priors: false stated", count(priors, read="stated", not_label="stated"),
          f"| stated recall {count(priors, 'stated', 'stated')}/{count(priors, 'stated')}"
          f"| ruled-out recall {count(priors, 'ruled_out', 'ruled_out')}/{count(priors, 'ruled_out')}"
          f"| unstated kept {count(priors, 'unstated', 'unstated')}/{count(priors, 'unstated')}")
    print("  mirna: false stated", count(mirna, read="stated", not_label="stated"),
          f"| stated recall {count(mirna, 'stated', 'stated')}/{count(mirna, 'stated')}"
          f"| ruled-out recall {count(mirna, 'ruled_out', 'ruled_out')}/{count(mirna, 'ruled_out')}")
    print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]))
