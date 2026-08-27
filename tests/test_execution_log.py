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
    assert log.name == "panda-execution-2026-08-15_06-09-00_TW.md"
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


def test_input_inspection_log_is_explicit_and_uses_user_paths(tmp_path: Path):
    decision = TaskDecision(
        action="inspect_inputs", in_scope=True, should_execute=True,
        confidence=1.0, reason="test", output_file=str(tmp_path / "panda.tsv"),
    )
    path = write_execution_markdown_log(
        decision,
        action="inspect_inputs",
        raw_output=(
            "Input inspection:\n"
            "- expression: /work/data/expression.tsv\n"
            "  shape: 10 rows x 2 columns"
        ),
        status="success", artifacts=[], warnings=[], errors=[],
        started_at=datetime(2026, 8, 14, 22, 9, 0, tzinfo=timezone.utc),
    )
    text = Path(path).read_text(encoding="utf-8")
    assert "Validation result: passed" in text
    assert "Not applicable — input inspection only." in text
    assert "/work/" not in text
    assert "data/expression.tsv" in text


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


def test_input_inspection_keeps_public_log_in_workflow_summary_only(tmp_path: Path):
    decision = TaskDecision(
        action="inspect_inputs", in_scope=True, should_execute=True,
        confidence=1.0, reason="test", output_file=str(tmp_path / "panda.tsv"),
    )
    result = structure_tool_result(
        "inspect_inputs", decision,
        "Input inspection passed\nExit code: 0",
        persist_log=True,
        persist_execution_log=True,
    )
    assert result.log_file
    assert "execution_markdown_log" not in result.metrics


def test_workflow_specific_input_inspection_does_not_write_a_public_log(tmp_path: Path):
    decision = TaskDecision(
        action="run_cobra", in_scope=True, should_execute=True,
        confidence=1.0, reason="test", output_dir=str(tmp_path),
    )
    result = structure_tool_result(
        "inspect_cobra_inputs", decision,
        "COBRA input inspection passed\nExit code: 0",
        persist_log=True,
        persist_execution_log=True,
    )
    assert result.log_file
    assert "execution_markdown_log" not in result.metrics


def test_execution_log_separates_notices_runtime_warnings_and_artifacts(tmp_path: Path):
    path = write_execution_markdown_log(
        _decision(str(tmp_path / "panda.tsv")),
        action="run_panda",
        raw_output=(
            "NEW: headers are enabled by default\n"
            "STDERR:\n"
            "UserWarning: pkg_resources is deprecated\n"
            "import pkg_resources\n"
            "Output file: `outputs/panda.tsv`\n"
            "Exit code: 0"
        ),
        status="success", artifacts=["outputs/panda.tsv"], warnings=[], errors=[],
    )
    text = Path(path).read_text(encoding="utf-8")
    assert "## Tool notices" in text
    assert "- headers are enabled by default" in text
    assert "## Warnings" in text
    assert "- pkg_resources is deprecated" in text
    assert "import pkg_resources" not in text
    assert "## Output artifacts" in text


def test_execution_log_preserves_hierarchy_and_renders_a_timeline(tmp_path: Path):
    path = write_execution_markdown_log(
        _decision(str(tmp_path / "panda.tsv")),
        action="run_panda",
        raw_output=(
            "Input inspection:\n"
            "- expression: /work/data/expression.tsv\n"
            "  format: expression matrix\n"
            "  shape: 1000 rows x 51 columns\n"
            "- motif: /work/data/motif.tsv\n"
            "  format: edge list\n"
            "\n"
            "- motif target genes overlapping expression genes: 913/913 (100.0%)\n"
            "  status: all IDs match.\n"
            "\n"
            "Command: `run-panda -o panda.tsv`\n"
            "STDOUT:\n"
            "Input data:\n"
            "Expression: data/expression.tsv\n"
            "Motif data: data/motif.tsv\n"
            "Start Panda run ...\n"
            "Loading motif data ...\n"
            "Computing panda on CPU\n"
            "Running panda took: 4.78 seconds!\n"
            "WARNING: output uses headers\n"
            "Use old_compatible=True for the previous format\n"
            "STDERR:\n"
            "UserWarning: pkg_resources is deprecated\n"
            "Exit code: 0\n"
            "NEW: headers are enabled by default"
        ),
        status="success",
        artifacts=["/work/panda.tsv"],
        warnings=[],
        errors=[],
        started_at=datetime(2026, 8, 14, 22, 9, 0, tzinfo=timezone.utc),
        finished_at=datetime(2026, 8, 14, 22, 9, 5, tzinfo=timezone.utc),
    )

    text = Path(path).read_text(encoding="utf-8")
    assert "- Duration: `5.00 seconds`" in text
    assert "- PANDA compute duration: `4.78 seconds`" in text
    assert "- Execution overhead: `0.22 seconds`" in text
    assert "### Expression" in text
    assert "- Format: expression matrix" in text
    assert "### Compatibility checks" in text
    assert "- Result: 913/913 (100.0%)" in text
    assert "- Overall validation: `passed`" in text
    assert "## Execution timeline" in text
    assert "1. Prepare inputs" in text
    assert "   - Input data:" in text
    assert "   - Expression: data/expression.tsv" in text
    assert "2. Run PANDA" in text
    assert "   - Device: CPU" in text
    assert "   - Compute duration: 4.78 seconds" in text
    assert "   - Result: completed" in text
    assert "   - Start PANDA run" not in text
    assert "   - Running PANDA algorithm" not in text
    assert "   - Computing PANDA on CPU" not in text
    assert "   - Running PANDA took: 4.78 seconds" not in text
    assert "- Exit code: `0`" in text
    assert "## Conclusion" in text
    assert "- WARNING: output uses headers" not in text
    assert "- Legacy headerless output is available with `old_compatible=True`." in text
    assert "15. Use old_compatible=True for the previous format" not in text
    assert "- pkg_resources is deprecated" in text


def test_execution_log_promotes_format_warning_and_reports_artifact_details(
    tmp_path: Path,
):
    artifact = tmp_path / "panda.tsv"
    artifact.write_bytes(b"gene\tTF1\n")
    started = datetime(2026, 8, 14, 22, 9, 0, 123000, tzinfo=timezone.utc)
    finished = datetime(2026, 8, 14, 22, 9, 5, 987000, tzinfo=timezone.utc)
    path = write_execution_markdown_log(
        _decision(str(artifact)),
        action="run_panda",
        raw_output=(
            "Command: `run-panda -o panda.tsv`\n"
            "WARNING: panda is now saved with the column names.\n"
            "Exit code: 0"
        ),
        status="success",
        artifacts=[str(artifact)],
        warnings=["panda is now saved with the column names."],
        errors=[],
        started_at=started,
        finished_at=finished,
    )

    text = Path(path).read_text(encoding="utf-8")
    assert "2026-08-15T06:09:00.123+08:00" in text
    assert "2026-08-15T06:09:05.987+08:00" in text
    assert "Duration: `5.86 seconds`" in text
    assert "PANDA output includes column headers by default." in text
    assert "panda is now saved with the column names." not in text
    assert "- Legacy headerless output is available with `old_compatible=True`." not in text
    assert f"- Path: `{artifact}`" in text
    assert "- Exists: `yes`" in text
    assert "- Size: `9 bytes`" in text
    assert "- Validation: `passed`" in text
