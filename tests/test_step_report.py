"""The terminal's step list: findings stream as they happen, and only recorded facts are printed."""

from netzoo_agent_core import presentation
from netzoo_agent_core.step_report import StepReporter, stage_lines


def _event(sequence, node, kind, payload=None, run="run-1"):
    return {"run_id": run, "node": node, "event_type": kind, "payload": payload or {}, "sequence": sequence}


def test_findings_print_as_they_arrive_and_the_step_closes_with_its_duration():
    printed = []
    report = StepReporter(printed.append)
    report(_event(1, "cli", "run.started"))
    report(_event(2, "apply_project_policy", "node.started"))
    report(_event(3, "apply_project_policy", "policy.loaded", {"agents_path": "AGENTS.md"}))
    report(_event(4, "apply_project_policy", "node.finished", {"duration_ms": 3}))
    report(_event(5, "classify", "node.started"))
    report(_event(6, "llm", "llm.started", {"role": "semantic_interpreter", "label": "reading the request"}))
    report(_event(7, "classify", "routing.capability_checked", {"check": {"requirements": [
        {"kind": "result", "quote": "one network per sample", "status": "available",
         "delivered_by": ["lioness_panda.per_sample_networks"]},
        {"kind": "result", "quote": "unsettled", "status": "not_available"}]}}))
    assert printed == [["▸ Reading your request", "    Checked what the methods can do",
                        "      “one network per sample” → LIONESS-PANDA (per sample networks)"]]
    report(_event(8, "classify", "core.decision", {"kind": "DO", "basis": "results_given", "workflows": ["LIONESS-PANDA"]}))
    report(_event(9, "classify", "llm.completed", {"model": "openai/gpt-4o-mini", "role": "capability_check", "total_tokens": 900}))
    report(_event(10, "classify", "node.finished", {"duration_ms": 12_300}))
    assert printed[1] == ["    Decision: LIONESS-PANDA can give what you asked for"]
    assert printed[2] == ["    gpt-4o-mini · 1 call (check what the methods can do) · 900 tokens", "  ✓ Read your request  (12 s)"]
    report(_event(11, "evaluate_plan", "node.started"))
    report(_event(12, "evaluate_plan", "node.finished", {"duration_ms": 2}))
    assert printed[3] == ["✓ Checked the plan  (<1 s)"]
    report(_event(13, "cli", "run.paused", {"status": "pending"}))
    assert printed[4] == ["── Waiting for you · 12 s · 2 steps · 1 model call"]
    assert not any("AGENTS.md" in line for block in printed for line in block)  # bookkeeping stays quiet


def test_a_failed_tool_lists_its_problems_and_log():
    rows = [{"type": "tool.started", "payload": {"action": "inspect_inputs"}},
            {"type": "tool.completed", "payload": {"action": "inspect_inputs", "status": "failed", "summary": "Validation failed",
                                                    "errors": ["genes not recognised"], "log_file": ".netzoo/logs/x.log"}}]
    lines = stage_lines("execute_tool", rows)
    assert "  Problem: genes not recognised" in lines and "  Log: .netzoo/logs/x.log" in lines
    printed = []
    report = StepReporter(printed.append)
    report(_event(1, "execute_tool", "node.started"))
    for row in rows:
        report(_event(2, "execute_tool", row["type"], row["payload"]))
    report(_event(3, "execute_tool", "node.finished", {"duration_ms": 900}))
    assert printed[-1] == ["  ✗ Checked the input files  (<1 s)"]


def test_the_step_list_replaces_the_older_one_line_summaries_but_not_warnings(capsys):
    presentation._COMMITTED_ACTIVITY_KEYS.clear()
    presentation._STEP_REPORT_ACTIVE = True
    try:
        presentation._commit_public_activity("a", "✓ Workflow — PANDA")
        presentation._commit_public_activity("b", "! Fallback recommendation — not an exact semantic match")
    finally:
        presentation._STEP_REPORT_ACTIVE = False
        presentation._COMMITTED_ACTIVITY_KEYS.clear()
    out = capsys.readouterr().out
    assert "Workflow — PANDA" not in out and "Fallback recommendation" in out
