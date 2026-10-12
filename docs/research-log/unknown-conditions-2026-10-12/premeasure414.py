"""Log 414 pre-measure: the candidate check call plus the condition check on seen requests and a designed bank.

Usage (repository root, provider key in the environment, OPENROUTER_CAPABILITY_MODEL set as live):
  python docs/research-log/unknown-conditions-2026-10-12/premeasure414.py <out.json> [name ...]

Per request: one check call with this checkout's schema, the verified other requirements, and -- when any
credited workflow pairs with one -- one condition-check call; records each result's status before and after.
No re-read, no second opinion. Every request here is seen (r17, f16, c18) or designed for this pre-measure.
"""
from __future__ import annotations

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LOG = HERE.parent
WORKTREES = ROOT.parent / ".worktrees"
sys.path.insert(0, str(ROOT / "scripts"))

from netzoo_agent_core.capability_sheet import entry  # noqa: E402
from netzoo_agent_core.contracts.capability_check import condition_check_model, proposal_model  # noqa: E402
from netzoo_agent_core.graph.capability_check_call import (  # noqa: E402
    _CONDITION_CHECK, _CONDITION_REDIRECT, _own_llm, build_capability_check_messages,
)
from netzoo_agent_core.contracts import HumanMessage, SystemMessage  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import (  # noqa: E402
    apply_condition_answers, apply_redirect_answers, build_capability_check, condition_pairs, redirect_pairs,
    stated_requirements, workflow_description,
)
from netzoo_agent_core.interpretation.semantic_repair import semantic_payload  # noqa: E402

SEEN = [("r17", "netzoo-score2-live", "rescore-2026-10-12/heldout17.json", "live", {"PL", "PS", "PI", "PQ", "MX", "K"}),
        ("f16", "netzoo-mt-cand", "follow-up-conditions-2026-10-12/heldout16.json", "cand", {"NC", "PC", "QS"}),
        ("c18", "netzoo-rc-cand", "request-conditions-2026-10-12/heldout18.json", "cand", {"CP", "XP"})]
DESIGNED = [  # with the workflows routing would plausibly offer, for the redirect step
    ("D1", "neg", "We want a TF-gene network for 60 samples from expression and PPI. It must be built without any prior knowledge of TF binding.", ["run_panda", "run_otter"]),
    ("D2", "neg", "We want a per-sample co-expression network for 90 samples. Every edge must have a direction.", ["run_lioness_coexpression", "run_bonobo"]),
    ("D3", "pos", "We want per-sample TF-gene networks for 50 samples from expression, motifs and PPI. Save the results as TSV files.", ["run_lioness_panda"]),
    ("D4", "pos", "We want one TF-gene network for 80 samples from expression, motifs and PPI. It must use our own motif prior file.", ["run_panda", "run_otter"]),
    ("D5", "pos", "We want a network between expression and methylation in 70 matched samples. Each edge needs a Benjamini-Hochberg adjusted p-value.", ["run_dragon"]),
    ("D6", "neg", "We want subtypes from somatic mutations of 120 tumors. The subtypes must come from consensus clustering with 1,000 resamplings.", ["run_sambar"]),
    ("D7", "pos", "We want communities of our bipartite TF-gene network. The communities must maximize bipartite modularity.", ["run_condor"]),
    ("D8", "neg", "We want each TF's activity per sample from expression, motifs and PPI of 80 samples. The activities must be signed, positive or negative.", ["run_giraffe"]),
    ("D9", "pos", "We want a co-expression network per sample for 40 samples. We will run it on our own cluster.", ["run_lioness_coexpression", "run_bonobo"]),
    ("D10", "pos", "We want one TF-gene network across 100 samples from expression, motifs and PPI. Use only the 60 tumor samples, not the normals.", ["run_panda"]),
]


def jobs():
    for tag, tree, items_path, arm, families in SEEN:
        for item in json.loads((LOG / items_path).read_text())["items"]:
            if item["family"] not in families or (tag == "r17" and item["id"].startswith("KN")):
                continue
            if tag == "f16" and item["family"] == "NC" and item["id"] != "NC7":
                continue
            data = json.loads((WORKTREES / tree / ".netzoo" / "sessions" / f"ve-{tag}-{arm}-{item['id']}-1.json").read_text())
            users = [m["content"] for m in data["messages"] if m["role"] == "user"]
            gold = "neg" if all(r["expect"] == "not_supported" for r in item["requirements"]) else "pos"
            decision = (data.get("plan") or {}).get("decision") or {}
            offered = [*decision.get("matched_actions", []), *decision.get("hypothesis_actions", []),
                       *decision.get("recommended_actions", [])]
            yield {"name": f"{tag}-{item['id']}", "gold": gold, "task": users[-1], "offered": offered}
    for name, gold, task, offered in DESIGNED:
        yield {"name": name, "gold": gold, "task": task, "offered": offered}


def run(job):
    llm = _own_llm(os.environ["OPENROUTER_CAPABILITY_MODEL"], int(os.environ.get("OPENROUTER_CAPABILITY_MAX_TOKENS", "9000")))
    messages, count = build_capability_check_messages(job["task"])
    schema = proposal_model(count)
    try:
        adapter = llm.with_structured_output(schema, method="function_calling", include_raw=True, strict=True)
        payload, _raw = semantic_payload(adapter.invoke(messages))
        proposal = schema.model_validate(payload.model_dump() if hasattr(payload, "model_dump") else payload)
    except Exception as error:  # noqa: BLE001
        return {**job, "error": f"check: {type(error).__name__}: {str(error)[:150]}"}
    check, _ = build_capability_check(job["task"], proposal)
    stated = stated_requirements(job["task"], proposal, check)
    pairs = condition_pairs(check, stated)
    row = {**job, "others": [o.model_dump() for o in proposal.conditions.other_requirements], "stated": stated,
           "before": [(r.quote, r.status) for r in check.results()], "pairs": [[i, a, q] for i, a, _k, q in pairs]}
    def ask(system, these):
        shown = [(check.requirements[i].quote, q, entry(k[0]).workflow, workflow_description(k)) for i, _a, k, q in these]
        listed = "\n".join(f'{n}. Asked result: "{a}" | Stated requirement: "{s}" | {w} produces: {p}'
                           for n, (a, s, w, p) in enumerate(shown, 1))
        cschema = condition_check_model(len(these))
        adapter = llm.with_structured_output(cschema, method="function_calling", include_raw=True, strict=True)
        payload, _raw = semantic_payload(adapter.invoke([SystemMessage(content=system), HumanMessage(content=listed)]))
        parsed = cschema.model_validate(payload.model_dump() if hasattr(payload, "model_dump") else payload)
        return [getattr(parsed, f"a{n}") for n in range(1, len(these) + 1)]

    if pairs:
        try:
            answers = ask(_CONDITION_CHECK, pairs)
            check = apply_condition_answers(check, pairs, answers)
            row["answers"] = answers
            redirect = redirect_pairs(check, list(dict.fromkeys(job["offered"]))[:4])
            row["redirect"] = [[i, a, q] for i, a, _k, q in redirect]
            if redirect:
                redirected = ask(_CONDITION_REDIRECT, redirect)
                check = apply_redirect_answers(check, redirect, redirected)
                row["redirected"] = redirected
        except Exception as error:  # noqa: BLE001
            row["condition_error"] = f"{type(error).__name__}: {str(error)[:150]}"
    row["after"] = [(r.quote, r.status) for r in check.results()]
    row["full_gap"] = check.full_gap
    return row


def main():
    only = set(sys.argv[2:])  # optional request names
    with ThreadPoolExecutor(4) as pool:
        rows = list(pool.map(run, [job for job in jobs() if not only or job["name"] in only]))
    Path(sys.argv[1]).write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    print(f"{len(rows)} rows, errors {sum('error' in r for r in rows)}")


if __name__ == "__main__":
    main()
