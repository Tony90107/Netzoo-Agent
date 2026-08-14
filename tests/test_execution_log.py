from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.decisions import TaskDecision
from netzoo_agent_core.execution_log import write_execution_markdown_log
from netzoo_agent_core.routing.results import structure_tool_result


def _decision(output_file: str) -> TaskDecision:
    return TaskDecision(
        action="run_panda", in_scope=True, should_execute=True, confidence=1.0,
        reason="test", output_file=output_file,
    )


def test_execution_log_records_command_preparation_and_failure(tmp_path: Path):
    path = write_execution_markdown_log(
        _decision(str(tmp_path / "panda.tsv")), action="run_panda",
        raw_output="Preparation:\n- formatted input\n\nCommand: `run-panda -o out.tsv`\nExit code: 1",
        status="failed", artifacts=[], warnings=["header inferred"], errors=["tool failed"],
        started_at=datetime(2026, 8, 14, 22, 9, 0, tzinfo=timezone.utc),
        finished_at=datetime(2026, 8, 14, 22, 10, 0, tzinfo=timezone.utc),
    )
    assert path is not None
    log = Path(path)
    assert log.name == "panda-execution-20260814-220900.md"
    text = log.read_text(encoding="utf-8")
    assert "```bash\nrun-panda -o out.tsv\n```" in text
    assert "formatted input" in text
    assert "## Errors" in text


def test_execution_log_uses_a_unique_filename(tmp_path: Path):
    decision = _decision(str(tmp_path / "panda.tsv"))
    started = datetime(2026, 8, 14, 22, 9, 0, tzinfo=timezone.utc)
    first = write_execution_markdown_log(decision, action="run_panda", raw_output="", status="success", artifacts=[], warnings=[], errors=[], started_at=started)
    second = write_execution_markdown_log(decision, action="run_panda", raw_output="", status="success", artifacts=[], warnings=[], errors=[], started_at=started)
    assert Path(first).name != Path(second).name


def test_structured_execute_result_writes_log_but_dry_run_does_not(tmp_path: Path):
    decision = _decision(str(tmp_path / "panda.tsv"))
    result = structure_tool_result(
        "run_panda", decision, "Command: `run-panda -o panda.tsv`\nExit code: 1",
        persist_log=True,
        persist_execution_log=True,
    )
    assert Path(result.metrics["execution_markdown_log"]).exists()
    dry_run = structure_tool_result(
        "run_panda", decision, "Dry run only. The agent selected this command but did not execute it.",
        persist_log=True,
        persist_execution_log=True,
    )
    assert "execution_markdown_log" not in dry_run.metrics
