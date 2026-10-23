"""P0 (harness repair, 2026-10-23): the small fixtures in tests/fixtures/harness_repair/, run on this checkout.

Recorded fixtures are copies of six live readings (session.json + events.jsonl), decided again by ROUND-12's B2 replay
(`replay_full.replay`, no model calls); each reply's reasons are tagged as ROUND-20's `replies.py` tags them. Synthetic
fixtures build the smallest check a scenario needs, as tests/test_fact_check.py does, because the recorded readings
hold no clean case of it.

A fixture keeps `baseline` (what 91a8c2d9 does, written once by `record`) apart from `expected` (the spec's case).
`check` flags every fixture whose behaviour differs from its baseline on the fields the baseline has: in P1/P2 those
are the intended changes. Fields later code adds (P1: the `obligations` ledger) are printed, never compared.

Usage: python3 fixtures.py run | record | check
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = HERE.parent
ROOT = LOGS.parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "harness_repair"
MANIFEST = FIXTURES / "fixtures.json"
sys.path.insert(0, str(LOGS / "stability-round13-2026-10-21"))
import harness  # noqa: E402  (sets the import paths to this checkout's scripts)


def _module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def recorded(fixtures: list[dict]) -> dict[str, dict]:
    """B2 on each recorded fixture's reading, with the reasons its reply states."""
    import netzoo_agent_core.interpretation.core_decision as core_decision

    tag = _module("round20_replies", LOGS / "stated-reasons-2026-10-21" / "replies.py").tagged
    by_session, core = harness._gold()
    wanted = {(f["source"]["session"], f["source"]["turn"]): f["id"] for f in fixtures}
    original, seen, out = core_decision.decide_core, {}, {}

    def spy(decision, task="", **kwargs):
        seen["decision"], seen["core"] = decision, original(decision, task, **kwargs)
        return seen["core"]

    harness.ROOTS = [FIXTURES / "readings"]
    for _key, folder, sid, task, payload, reread, found, _n in harness.readings():
        fixture = wanted.get((sid, folder.name))
        if fixture is None:
            continue
        core_decision.decide_core = spy
        try:
            harness.replay_full.replay(folder, task, payload, reread, found)
        finally:
            core_decision.decide_core = original
        decision, call = seen["decision"], seen["core"]
        check = core_decision.with_core(decision, call).capability_check
        reasons = [[item.quote[:60], kind, text] for item in (check.results() if check else [])
                   if item.status in ("not_available", "partial") for kind, text in (tag(item, check) or [("R0", "")])]
        facts = decision.fact_check
        out[fixture] = {"gold": harness._label(sid, by_session, core), "kind": call.kind, "basis": call.basis,
                        "partial": call.partial,
                        "fact_agent": None if facts is None else {
                            "status": facts.status, "asked": [q.question for q in facts.accepted],
                            "rejected": [r.rule for r in facts.rejected], "legacy": [q.question for q in facts.legacy],
                            "legacy_kept": bool(call.evidence.get("legacy_kept"))},
                        "reasons": reasons, **_ledger(call)}
    return out


def _ledger(call) -> dict:
    """P1's obligations, when the code records them: (source, status, asked_as) and the question."""
    found = call.evidence.get("obligations")
    return {} if found is None else {"obligations": [[o["source"], o["status"], o["asked_as"], o["question"]]
                                                     for o in found]}


def synthetic_lift(source: dict) -> dict:
    from netzoo_agent_core.contracts import TaskDecision
    from netzoo_agent_core.contracts.capability_check import CapabilityCheck
    from netzoo_agent_core.contracts.fact_check import FactCheck
    from netzoo_agent_core.interpretation.core_decision import _facts, decide_core

    try:  # 91a8c2d9 lifts the waits when the agent asks; from P1 (2026-10-23) nothing is lifted
        from netzoo_agent_core.graph.fact_check_call import waits_after_agent
    except ImportError:
        def waits_after_agent(check, facts, task):
            return check
    check = CapabilityCheck.model_validate(source["check"])
    agent = FactCheck.model_validate(source["agent"])
    agent = agent.model_copy(update={"legacy": _facts(check, by_code=False)})
    lifted = waits_after_agent(check, agent, source["task"])
    decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="fixture",
                            capability_check=lifted, fact_check=agent)
    call = decide_core(decision, source["task"])
    return {"kind": call.kind, "basis": call.basis, "partial": call.partial,
            "rows": [[row.quote, row.status, row.delivered_by] for row in lifted.results()],
            "asked": [q.question for q in agent.accepted],
            "legacy_shadow": call.evidence.get("legacy_facts", []), "legacy_kept": bool(call.evidence.get("legacy_kept")),
            "core_asks": [q.question for q in call.facts], **_ledger(call)}


def synthetic_kept(source: dict) -> dict:
    sys.path.insert(0, str(ROOT / "tests"))
    from netzoo_agent_core.contracts.fact_check import FactProposals
    from netzoo_agent_core.interpretation.fact_check import kept_facts
    from netzoo_agent_core.policy import ProjectPolicyLoader
    from test_fact_check import _decision, _proposal  # the suite's own builders, so the fixture matches its tests

    policy = ProjectPolicyLoader(ROOT).load()
    proposals = FactProposals(facts=[_proposal(**extra) for extra in source["proposals"]])
    facts = kept_facts(source["task"], proposals, _decision(uncertain=tuple(source["uncertain"])), policy)
    found = {"asked": [q.user_quote for q in facts.accepted],
             "rejected": [[r.rule, r.proposal.get("user_quote")] for r in facts.rejected]}
    if hasattr(facts, "queued"):  # P1: past two questions, queued -- still open
        found["queued"] = [q.user_quote for q in facts.queued]
    return found


def observe() -> tuple[dict, dict]:
    manifest = json.loads(MANIFEST.read_text())
    fixtures = manifest["fixtures"]
    found = recorded([f for f in fixtures if f["source"]["kind"] == "recorded"])
    for f in fixtures:
        kind = f["source"]["kind"]
        if kind == "synthetic_lift":
            found[f["id"]] = synthetic_lift(f["source"])
        elif kind == "synthetic_kept":
            found[f["id"]] = synthetic_kept(f["source"])
    missing = [f["id"] for f in fixtures if f["id"] not in found]
    assert not missing, f"fixtures not found: {missing}"
    return manifest, found


def main(mode: str):
    manifest, found = observe()
    changed = []
    for f in manifest["fixtures"]:
        now = found[f["id"]]
        print(f"== {f['id']} {'/'.join(f['cases'])} {f['source'].get('session', f['source']['kind'])}")
        print(f"   now      {json.dumps(now, ensure_ascii=False)}")
        print(f"   expected {json.dumps(f['expected'], ensure_ascii=False)}")
        if mode == "check" and f.get("baseline") != {key: now.get(key) for key in f.get("baseline", {})}:
            changed.append(f["id"])
        if mode == "record":
            f["baseline"] = now
    if mode == "record":
        manifest["baseline_code"] = "91a8c2d9 (netzoo-agent/main da39e8ac)"
        MANIFEST.write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
        print(f"baseline written for {len(found)} fixtures")
    if mode == "check":
        print(f"changed from baseline: {changed or 'none'}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "run")
