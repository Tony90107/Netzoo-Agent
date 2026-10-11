"""Audit probes, not production changes or biological runs.

Run with the project's dependencies: python this_file.py /path/to/netzoo_agent
Only temporary files are written. A simulated unavailable DRAGON API is used.
Outputs describe observed behavior; they are not regression expectations.
"""
import asyncio
import json
import os
from pathlib import Path
import queue
import sys
import tempfile
import threading
from unittest.mock import patch

root = Path(sys.argv[1]).resolve()
os.chdir(root)
sys.path.insert(0, str(root / "scripts"))
os.environ["NETZOO_GENE_ONLINE_LOOKUP"] = "off"

import numpy as np
from netzoo_agent_core import command, execution, settings
from netzoo_agent_core.contracts import TaskDecision
from netzoo_agent_core.data.artifacts import validate_output_artifacts
from netzoo_agent_core.evaluation.plan_review import evaluate_workflow_plan
from netzoo_agent_core.planning import build_workflow_plan
from netzoo_agent_core.routing.discovery import _default_network_output
from netzoo_agent_core.routing.results import structure_tool_result
from netzoo_agent_core.runtime import configure_runtime
from netzoo_agent_core.server.supervisor import SessionSupervisor
from netzoo_agent_core.session_outputs import session_output_dir, session_output_scope

def emit(case, **values):
    print(json.dumps({"case": case, **values}, ensure_ascii=False))

def decision(action, **fields):
    return TaskDecision(action=action, in_scope=True, should_execute=True,
                        confidence=1, reason="Audit fixture", **fields)

with tempfile.TemporaryDirectory() as folder:
    tmp = Path(folder)
    a, b, output = tmp / "a.tsv", tmp / "b.tsv", tmp / "dragon.tsv"
    a.write_text("sample\tgeneA\ns1\t1\ns2\t2\ns3\t4\ns4\t3\n")
    b.write_text("sample\tproteinB\ns1\t3\ns2\t1\ns3\t2\ns4\t4\n")
    output.write_text("node_id\tlayer1::geneA\tlayer2::proteinB\nlayer1::geneA\t1\t0.2\nlayer2::proteinB\t0.2\t1\n")
    before = output.stat().st_mtime_ns
    fn = getattr(execution.run_dragon, "func", execution.run_dragon)
    with patch.object(settings, "EXECUTE_TOOLS", True), patch.object(
        execution, "_load_dragon_api", side_effect=RuntimeError("audit simulated API outage")
    ):
        raw = fn(str(a), str(b), str(output))
    d = decision("run_dragon", omics_layer_1=str(a), omics_layer_2=str(b),
                 output_file=str(output), output_format="matrix")
    result = structure_tool_result(d.action, d, raw)
    emit("F1_failed_dragon_reuses_old_artifact", raw=raw, status=result.status,
         errors=result.errors, old_file_unchanged=before == output.stat().st_mtime_ns)

    output = tmp / "panda.tsv"
    output.write_text("TF_A\tGENE_A\tinf\nTF_B\tGENE_B\t-inf\n")
    d = decision("run_panda", output_file=str(output))
    validation = validate_output_artifacts(d.action, d)
    result = structure_tool_result(d.action, d, "Exit code: 0\nOutput file: " + str(output))
    emit("F2_nonfinite_panda", artifact_ok=validation.ok, errors=validation.errors,
         status=result.status)
    output.write_text("TF_A\tGENE_A\t0.2\nTF_B\tGENE_B\t0.3\n")
    sample_output = tmp / "lioness.npy"
    np.save(sample_output, np.array([[np.nan, np.inf], [np.inf, np.nan]]))
    d = d.model_copy(update={"action": "run_lioness_panda", "lioness_output": str(sample_output)})
    validation = validate_output_artifacts(d.action, d)
    emit("F2_nonfinite_lioness", artifact_ok=validation.ok, errors=validation.errors)

    output.write_text("earlier result\n")
    task = ("Run PANDA with expression_file=data/lioness-toy/expression.tsv "
            "motif_file=data/lioness-toy/motif-panda.tsv "
            f"ppi_file=data/lioness-toy/ppi.tsv output_file={output}")
    d = decision("run_panda", expression_file="data/lioness-toy/expression.tsv",
                 motif_file="data/lioness-toy/motif-panda.tsv",
                 ppi_file="data/lioness-toy/ppi.tsv", output_file=str(output))
    configure_runtime(TEST_DATA_MODE=True)
    plan = build_workflow_plan(d, task)
    evaluation = evaluate_workflow_plan(plan, task)
    # This benign substitute is the only subprocess. It touches a temporary file.
    with patch.object(command, "EXECUTE_TOOLS", True):
        result = command._run_command([
            sys.executable, "-c",
            'from pathlib import Path; import sys; Path(sys.argv[1]).write_text("new result\\n")',
            str(output),
        ], str(output))
    with session_output_scope("audit"):
        path1 = _default_network_output("panda", "data/expression.tsv", session_output_dir())
        path2 = _default_network_output("panda", "data/expression.tsv", session_output_dir())
    emit("F3_existing_output", plan_status=plan.status, evaluation=evaluation.status,
         content_after=output.read_text().strip(), repeated_default_same=path1 == path2,
         default=path1)

class DeadWorker:
    pid = None
    def start(self): pass
    def is_alive(self): return False
    def join(self, timeout=None): pass
    def terminate(self): pass

async def check_pump_cleanup():
    supervisor = SessionSupervisor(process_factory=lambda *a: DeadWorker(), queue_factory=queue.Queue)
    await supervisor.start()
    for i in range(3):
        sid = f"audit-dead-{i}"
        await supervisor.create(sid, {})
        await supervisor.close(sid)
    emit("F7_closed_worker_pumps", sessions=supervisor.list_sessions(),
         remaining_threads=[t.name for t in threading.enumerate()
                            if t.name.startswith("netzoo-session-audit-dead-")])
    await supervisor.shutdown()

asyncio.run(check_pump_cleanup())
