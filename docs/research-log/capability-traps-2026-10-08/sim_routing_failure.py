"""Log 396: the capability check and its second opinion with routing failed (no match at all), live check model.

Usage (main repository root, provider key in .env, never printed):
  set -a; . ./.env; set +a; CODE_ROOT=<candidate checkout> python3 docs/research-log/capability-traps-2026-10-08/sim_routing_failure.py <heldout.json> <tag> <repeats>

For every item: the check call through `request_capability_check` (OPENROUTER_CAPABILITY_MODEL), then
`_with_capability_check` on a decision whose routing fell back with no candidate -- the situation of
TEST_PROMPTS r12 test9 -- so only the second opinion asked about cited near misses can stop a full gap.
Writes replay/<tag>.json and prints full gaps per family. Nothing else runs.
"""
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("CODE_ROOT", HERE.parents[2]))
sys.path.insert(0, str(ROOT / "scripts"))
from netzoo_agent_core.contracts import LLMUsage, TaskDecision  # noqa: E402
from netzoo_agent_core.graph import router_invocation as R  # noqa: E402
from netzoo_agent_core.graph.capability_check_call import request_capability_check  # noqa: E402
from netzoo_agent_core.llm import build_llm  # noqa: E402


class Recorder:
    def __init__(self):
        self.events = []

    def append(self, run_id, event_type, node, payload):
        self.events.append((event_type, payload))


def run(item, rep):
    context = SimpleNamespace(
        study_purpose_llm=build_llm("openai/gpt-4o-mini", 0.0, max_output_tokens=1200),
        semantic_model_name="openai/gpt-4o-mini", router_max_tokens=1200, task_token_budget=30000,
        price_catalog=None, recorder=Recorder())
    proposal, usage, _, status = request_capability_check(
        context, {}, item["prompt"], LLMUsage(budget_tokens=30000), [])
    row = {"id": item["id"], "family": item["family"], "rep": rep, "status": status}
    if proposal is None:
        return row
    failed = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.0,
                          reason="routing failed", capability_match_status="fallback")
    invocation = R._RouterInvocation(decision=failed, routing_state={}, usage=usage, budget_warnings=[],
                                     reason_code=None)
    check = R._with_capability_check(context, {}, item["prompt"], invocation, proposal).decision.capability_check
    second = [payload for kind, payload in context.recorder.events if kind == "routing.capability_second_opinion"]
    return {**row, "full_gap": check.full_gap, "check": check.model_dump(), "second_opinion": second}


def main(name, tag, repeats):
    items = json.loads((HERE / name).read_text())["items"]
    jobs = [(item, rep) for rep in range(1, repeats + 1) for item in items]
    with ThreadPoolExecutor(int(os.environ.get("PAR", "3"))) as pool:
        rows = list(pool.map(lambda job: run(*job), jobs))
    (HERE / "replay").mkdir(exist_ok=True)
    (HERE / "replay" / f"{tag}.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    summary = {}
    for row in rows:
        key = "UN" if row["family"] in "UN" else row["family"]
        bucket = summary.setdefault(key, {"n": 0, "full_gap": 0, "no_check": 0})
        bucket["n"] += 1
        bucket["full_gap"] += int(bool(row.get("full_gap")))
        bucket["no_check"] += int("full_gap" not in row)
    print(json.dumps(summary))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]))
