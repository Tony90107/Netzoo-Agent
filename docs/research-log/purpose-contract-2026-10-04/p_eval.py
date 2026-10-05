"""Log 374 P-gates: the study-purpose call with the priors reading, on a held-out set.

Usage (repository root, provider key in .env, never printed):
  set -a; . ./.env; set +a; python3 docs/research-log/purpose-contract-2026-10-04/p_eval.py <heldout.json> <tag> <repeats>
Production modules only, gpt-4o-mini at temperature 0, strict function calling, as
the graph binds them. Scores the verified priors reading against the label
`priors_stated` ("stated" / "ruled_out" / "unstated") when the set has it, and the
design and conclusions with b_eval's score, so the same command in the baseline
worktree's b_eval gives the comparison. Writes <tag>-calls.json beside this script.
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
    confusion, lines = Counter(), []
    for row in rows:
        if row["proposal"] is None:
            continue
        purpose, rejected = verify_proposal(row["prompt"], StudyPurposeProposal.model_validate(row["proposal"]))
        label = row["label"].get("priors_stated")
        confusion[(label, purpose.priors)] += 1
        if label is not None and purpose.priors != label or label is None:
            lines.append(f"   {row['id']} r{row['rep']}: label {label} | proposed {row['proposal'].get('priors')} "
                         f"{row['proposal'].get('priors_span', '')!r} | verified {purpose.priors} "
                         f"| rejected {[r for r in rejected if r['field'] == 'priors']}")
    print("priors (label, verified):", dict(sorted(confusion.items(), key=str)))
    print("\n".join(lines))
    t, errors = b_eval.score(rows, b_eval.model_reading)
    print(f"design {t['design_hit']}/{t['design_labelled']} false {t['design_false']} | claim {t['claim_hit']}/"
          f"{t['claim_labelled']} false {t['claim_false']} | false gap {t['gap_false']}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]))
