"""Log 355 W1/W2: the implemented study-purpose call on a held-out set, scored against the live witnesses.

Usage (repository root, provider key in .env, never printed):
  set -a; . ./.env; set +a; python3 docs/research-log/purpose-contract-2026-10-04/b_eval.py <heldout.json> <tag> <repeats> [--base-verify <frozen verify.py>]

Log 361: with --base-verify, the same calls are also scored with that frozen
verification (the live version), which is then the baseline.

Uses the production modules only: llm.build_study_purpose_messages, the
StudyPurposeProposal contract and routing.study_purpose_verify.verify_proposal,
with openai/gpt-4o-mini at temperature 0 and strict function calling, as the
graph binds them. Writes <tag>-calls.json beside this script and prints the
counts (summed over repeats). The baseline is routing.study_purpose (the live
witnesses), which needs no call.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from netzoo_agent_core.contracts.study_purpose import StudyPurposeProposal  # noqa: E402
from netzoo_agent_core.interpretation.semantic_repair import semantic_payload  # noqa: E402
from netzoo_agent_core.llm import build_llm, build_study_purpose_messages  # noqa: E402
from netzoo_agent_core.routing.study_purpose import study_purpose  # noqa: E402
from netzoo_agent_core.routing.study_purpose_verify import verify_proposal  # noqa: E402


def call(llm, task):
    adapter = llm.with_structured_output(StudyPurposeProposal, method="function_calling", include_raw=True, strict=True)
    try:
        payload, _raw = semantic_payload(adapter.invoke(build_study_purpose_messages(task)))
        if hasattr(payload, "model_dump"):
            payload = payload.model_dump()
        return StudyPurposeProposal.model_validate(payload).model_dump(), None
    except Exception as error:  # recorded, never retried
        return None, type(error).__name__


def score(rows, reading):
    t = Counter()
    errors = []
    for row in rows:
        label = row["label"]
        design, claims = reading(row)
        primary = claims[0] if claims else "none"
        if label["comparison_design"] != "none":
            t["design_labelled"] += 1
            t["design_hit"] += design == label["comparison_design"]
        if design != "none" and design != label["comparison_design"]:
            t["design_false"] += 1
            errors.append(f"design {row['id']} r{row['rep']}: {label['comparison_design']} -> {design}")
        if label["claim_kind"] != "none":
            t["claim_labelled"] += 1
            t["claim_hit"] += primary == label["claim_kind"]
        if primary != "none" and primary != label["claim_kind"]:
            t["claim_false"] += 1
            errors.append(f"claim {row['id']} r{row['rep']}: {label['claim_kind']} -> {claims}")
        if set(claims) & {"causal", "prediction"} - {label["claim_kind"]}:
            t["gap_false"] += 1
            errors.append(f"GAP {row['id']} r{row['rep']}: {label['claim_kind']} -> {claims}")
    return t, errors


def witness_reading(row):
    purpose = study_purpose(row["prompt"])
    return purpose.design or "none", [claim for claim, _ in purpose.claims]


def model_reading(row):
    if row["proposal"] is None:  # a failed call falls back to the witnesses, as the graph does
        return witness_reading(row)
    purpose, _ = verify_proposal(row["prompt"], StudyPurposeProposal.model_validate(row["proposal"]))
    return purpose.design or "none", [claim for claim, _ in purpose.claims]


def _frozen_verify(path):
    """verify_proposal from a frozen copy, with its package-relative imports resolved."""
    source = Path(path).read_text().replace(
        "from ..contracts.study_purpose", "from netzoo_agent_core.contracts.study_purpose").replace(
        "from .study_purpose", "from netzoo_agent_core.routing.study_purpose")
    namespace = {}
    exec(compile(source, str(path), "exec"), namespace)
    return namespace["verify_proposal"]


def main(path, tag, repeats, base_verify=None):
    items = json.loads(Path(path).read_text())["items"]
    llm = build_llm("openai/gpt-4o-mini", 0.0, max_output_tokens=2000, timeout_seconds=60)
    jobs = [(item, rep) for rep in range(1, repeats + 1) for item in items]
    with ThreadPoolExecutor(8) as pool:
        results = list(pool.map(lambda job: call(llm, job[0]["prompt"]), jobs))
    rows = [{"id": item["id"], "rep": rep, "prompt": item["prompt"], "label": item, "proposal": proposal, "error": error}
            for (item, rep), (proposal, error) in zip(jobs, results)]
    (HERE / f"{tag}-calls.json").write_text(json.dumps(
        [{k: v for k, v in row.items() if k != "label"} for row in rows], ensure_ascii=False, indent=1))
    print(f"{len(rows)} calls, {sum(1 for row in rows if row['error'])} failed")
    readings = [("witness", witness_reading)]
    if base_verify:
        frozen = _frozen_verify(base_verify)

        def base_reading(row):
            if row["proposal"] is None:
                return witness_reading(row)
            purpose, _ = frozen(row["prompt"], StudyPurposeProposal.model_validate(row["proposal"]))
            return purpose.design or "none", [claim for claim, _ in purpose.claims]
        readings.append((f"base {Path(base_verify).parent.name}", base_reading))
    readings.append(("model + verification", model_reading))
    for name, reading in readings:
        t, errors = score(rows, reading)
        print(f"{name:22} design {t['design_hit']}/{t['design_labelled']} ({t['design_hit'] / max(1, t['design_labelled']):.0%}) "
              f"false {t['design_false']} | claim {t['claim_hit']}/{t['claim_labelled']} "
              f"({t['claim_hit'] / max(1, t['claim_labelled']):.0%}) false {t['claim_false']} | false gap {t['gap_false']}")
        for line in errors:
            print("   ", line)


if __name__ == "__main__":
    base = sys.argv[sys.argv.index("--base-verify") + 1] if "--base-verify" in sys.argv else None
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]), base)
