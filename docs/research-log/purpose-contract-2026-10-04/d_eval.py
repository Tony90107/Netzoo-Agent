"""Log 376 D-gates: the data-facts call (what a request says about its TF priors), on a held-out set.

Usage (repository root, provider key in .env, never printed):
  set -a; . ./.env; set +a; python3 docs/research-log/purpose-contract-2026-10-04/d_eval.py <heldout.json> <tag> <repeats>
Production modules only (llm.build_data_facts_messages, DataFactsProposal,
graph.data_facts_call.verify_data_facts), gpt-4o-mini at temperature 0, strict
function calling, as the graph binds them. Scores the verified reading against the
label `priors_stated`. Writes <tag>-calls.json beside this script.
"""
import json
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
from netzoo_agent_core.contracts.data_facts import DataFactsProposal  # noqa: E402
from netzoo_agent_core.graph.data_facts_call import verify_data_facts  # noqa: E402
from netzoo_agent_core.interpretation.semantic_repair import semantic_payload  # noqa: E402
from netzoo_agent_core.llm import build_data_facts_messages, build_llm  # noqa: E402


def call(llm, task):
    adapter = llm.with_structured_output(DataFactsProposal, method="function_calling", include_raw=True, strict=True)
    try:
        payload, _raw = semantic_payload(adapter.invoke(build_data_facts_messages(task)))
        if hasattr(payload, "model_dump"):
            payload = payload.model_dump()
        return DataFactsProposal.model_validate(payload).model_dump(), None
    except Exception as error:  # recorded, never retried
        return None, type(error).__name__


def main(path, tag, repeats):
    items = json.loads(Path(path).read_text())["items"]
    llm = build_llm("openai/gpt-4o-mini", 0.0, max_output_tokens=500, timeout_seconds=60)
    jobs = [(item, rep) for rep in range(1, repeats + 1) for item in items]
    with ThreadPoolExecutor(8) as pool:
        results = list(pool.map(lambda job: call(llm, job[0]["prompt"]), jobs))
    rows = [{"id": item["id"], "rep": rep, "prompt": item["prompt"], "proposal": proposal, "error": error}
            for (item, rep), (proposal, error) in zip(jobs, results)]
    (HERE / f"{tag}-calls.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    labels = {item["id"]: item.get("priors_stated") for item in items}
    confusion, lines = Counter(), []
    for row in rows:
        if row["proposal"] is None:
            confusion["failed"] += 1
            continue
        entry, rejected = verify_data_facts(row["prompt"], DataFactsProposal.model_validate(row["proposal"]))
        label = labels[row["id"]]
        confusion[(label, entry["priors"])] += 1
        if entry["priors"] != label:
            lines.append(f"   {row['id']} r{row['rep']}: label {label} | proposed {row['proposal']['priors']} "
                         f"{row['proposal']['priors_span']!r} | verified {entry['priors']} | rejected {rejected}")
    stated_false = sum(n for key, n in confusion.items() if isinstance(key, tuple) and key[1] == "stated" and key[0] != "stated")
    stated = [n for key, n in confusion.items() if isinstance(key, tuple) and key[0] == "stated"]
    print(f"{len(rows)} calls, {confusion['failed']} failed")
    print("priors (label, verified):", dict(sorted(((k, v) for k, v in confusion.items() if k != "failed"), key=str)))
    print(f"P1 read as stated when not stated: {stated_false}; P3 stated recall: "
          f"{confusion[('stated', 'stated')]}/{sum(stated)}; P2 ruled-out recall: "
          f"{confusion[('ruled_out', 'ruled_out')]}/{sum(n for k, n in confusion.items() if isinstance(k, tuple) and k[0] == 'ruled_out')}")
    print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]))
