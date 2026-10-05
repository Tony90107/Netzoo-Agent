"""Log 367 M-gates: the study-purpose call with many_samples_span, on a held-out set.

Usage (repository root, provider key in .env, never printed):
  set -a; . ./.env; set +a; python3 docs/research-log/purpose-contract-2026-10-04/m_eval.py <heldout.json> <tag> <repeats>
Production modules only (llm.build_study_purpose_messages, StudyPurposeProposal,
verify_proposal), gpt-4o-mini at temperature 0, strict function calling, as the
graph binds them. Scores the verified many-samples reading against the label
`samples_per_individual` ("one" / "many"; heldout10, written before the field,
is read as many for T1 and T2 only), and the design and conclusions with b_eval's
score, so the same command in the baseline worktree's b_eval gives the comparison.
Writes <tag>-calls.json beside this script.
"""
import json
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import b_eval  # noqa: E402
from netzoo_agent_core.contracts.study_purpose import StudyPurposeProposal  # noqa: E402
from netzoo_agent_core.llm import build_llm  # noqa: E402
from netzoo_agent_core.routing.study_purpose_verify import verify_proposal  # noqa: E402

HELDOUT10_MANY = {"T1", "T2"}


def label_many(item, path):
    if "samples_per_individual" in item:
        return item["samples_per_individual"] == "many"
    return "heldout10" in str(path) and item["id"] in HELDOUT10_MANY


def main(path, tag, repeats):
    items = json.loads(Path(path).read_text())["items"]
    llm = build_llm("openai/gpt-4o-mini", 0.0, max_output_tokens=2000, timeout_seconds=60)
    jobs = [(item, rep) for rep in range(1, repeats + 1) for item in items]
    with ThreadPoolExecutor(8) as pool:
        results = list(pool.map(lambda job: b_eval.call(llm, job[0]["prompt"]), jobs))
    rows = [{"id": item["id"], "rep": rep, "prompt": item["prompt"], "label": item, "proposal": proposal, "error": error}
            for (item, rep), (proposal, error) in zip(jobs, results)]
    (HERE / f"{tag}-calls.json").write_text(json.dumps(
        [{k: v for k, v in row.items() if k != "label"} for row in rows], ensure_ascii=False, indent=1))
    print(f"{len(rows)} calls, {sum(1 for row in rows if row['error'])} failed")
    m, lines = Counter(), []
    for row in rows:
        many_label = label_many(row["label"], path)
        if row["proposal"] is None:
            m["failed_calls"] += 1
            continue
        purpose, rejected = verify_proposal(row["prompt"], StudyPurposeProposal.model_validate(row["proposal"]))
        verified = bool(purpose.many_samples_quote)
        proposed = row["proposal"].get("many_samples_span", "")
        m["many_labelled"] += many_label
        m["many_hit"] += many_label and verified
        m["false_many"] += verified and not many_label
        m["proposed_on_one"] += bool(proposed.strip()) and not many_label
        if verified != many_label or (proposed.strip() and not verified):
            lines.append(f"   {row['id']} r{row['rep']}: label {'many' if many_label else 'one'} | proposed {proposed!r} "
                         f"| verified {purpose.many_samples_quote!r} | rejected {[r for r in rejected if r['field'] == 'many_samples']}")
    print(f"many samples: hit {m['many_hit']}/{m['many_labelled']}, false {m['false_many']} "
          f"(proposed on one-sample items {m['proposed_on_one']}), failed calls {m['failed_calls']}")
    print("\n".join(lines))
    t, errors = b_eval.score(rows, b_eval.model_reading)
    print(f"design {t['design_hit']}/{t['design_labelled']} false {t['design_false']} | claim {t['claim_hit']}/"
          f"{t['claim_labelled']} false {t['claim_false']} | false gap {t['gap_false']}")
    for line in errors:
        print("   ", line)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]))
