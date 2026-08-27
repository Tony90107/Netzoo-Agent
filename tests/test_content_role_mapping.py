from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core import TaskDecision, build_workflow_plan  # noqa: E402
from netzoo_agent_core.contracts import InputRoleMapping  # noqa: E402
from netzoo_agent_core.data.content_mapping import infer_input_roles  # noqa: E402


class FakeContentMapper:
    def __init__(self, assignments):
        self.assignments = assignments
        self.calls = []

    def invoke(self, messages):
        self.calls.append(messages)
        return InputRoleMapping(assignments=self.assignments)


def _write(path: Path, content: str = "id\tvalue\nA\t1\n") -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def test_unknown_filenames_are_mapped_by_content_and_need_confirmation(tmp_path):
    expression = _write(
        tmp_path / "a.tsv",
        "gene\ts1\ts2\nG1\t1\t2\nG2\t2\t1\n",
    )
    motif = _write(tmp_path / "b.tsv", "TF1\tG1\t1\nTF2\tG2\t1\n")
    ppi = _write(tmp_path / "c.tsv", "TF1\tTF2\t1\n")
    mapper = FakeContentMapper(
        [
            {
                "path": str(ppi),
                "role": "ppi",
                "confidence": 0.81,
                "rationale": "Two regulator identifiers and a numeric edge weight.",
            },
            {
                "path": str(expression),
                "role": "expr",
                "confidence": 0.96,
                "rationale": "First column is gene IDs and remaining columns are samples.",
            },
            {
                "path": str(motif),
                "role": "prior",
                "confidence": 0.88,
                "rationale": "Regulator-to-gene weighted edge list.",
            },
        ]
    )

    plan = build_workflow_plan(
        TaskDecision(
            action="run_panda",
            in_scope=True,
            should_execute=True,
            confidence=1.0,
            reason="Run PANDA on the three local files.",
        ),
        f"Run PANDA with {expression}, {motif}, and {ppi}.",
        content_mapper=mapper,
    )

    assert len(mapper.calls) == 1
    assert plan.status == "needs_confirmation"
    evidence = {
        item.field: item
        for item in plan.evidence
        if item.field in {"expression_file", "motif_file", "ppi_file"}
    }
    assert evidence["expression_file"].value == str(expression.resolve())
    assert evidence["motif_file"].value == str(motif.resolve())
    assert evidence["ppi_file"].value == str(ppi.resolve())
    assert "confidence 0.96" in evidence["expression_file"].reason
    assert "gene IDs" in evidence["expression_file"].reason
    assert "Awaiting user confirmation" in evidence["ppi_file"].reason


def test_mapping_ranks_candidates_and_keeps_the_highest_confidence_assignment(tmp_path):
    first = _write(tmp_path / "a.tsv")
    second = _write(tmp_path / "b.tsv")
    mapper = FakeContentMapper(
        [
            {"path": str(first), "role": "expression", "confidence": 0.61},
            {"path": str(second), "role": "expression", "confidence": 0.93},
            {"path": str(second), "role": "ppi", "confidence": 0.92},
        ]
    )

    result = infer_input_roles(
        "run PANDA",
        f"run PANDA with {first} and {second}",
        ["expression_file", "ppi_file"],
        tmp_path,
        mapper,
    )

    assert result["expression_file"].path == str(second.resolve())
    assert result["expression_file"].confidence == 0.93
    assert "ppi_file" not in result


def test_content_mapping_is_available_for_all_registered_netzoopy_input_roles(tmp_path):
    cases = {
        "run_puma": ("expression_file", "motif_file", "ppi_file", "mirna_file"),
        "run_lioness_panda": ("expression_file", "motif_file", "ppi_file"),
        "run_lioness_puma": ("expression_file", "motif_file", "ppi_file", "mirna_file"),
        "run_lioness_coexpression": ("expression_file",),
        "run_condor": ("network_file",),
        "run_cobra": ("expression_file", "design_file"),
        "inspect_inputs": ("expression_file", "motif_file", "ppi_file"),
        "inspect_condor_inputs": ("network_file",),
        "inspect_cobra_inputs": ("expression_file", "design_file"),
        "format_expression": ("expression_file",),
        "convert_expression": ("expression_file",),
    }
    for index, (action, fields) in enumerate(cases.items()):
        paths = [_write(tmp_path / f"{index}-{position}.tsv") for position, _ in enumerate(fields)]
        mapper = FakeContentMapper(
            [
                {
                    "path": str(path),
                    "role": field,
                    "confidence": 0.9,
                    "rationale": f"Content matches {field}.",
                }
                for path, field in zip(paths, fields)
            ]
        )
        task = f"Use {action}: " + ", ".join(str(path) for path in paths)
        plan = build_workflow_plan(
            TaskDecision(
                action=action,
                in_scope=True,
                should_execute=True,
                confidence=1.0,
                reason=f"Run {action}.",
            ),
            task,
            content_mapper=mapper,
        )
        mapped = {
            item.field
            for item in plan.evidence
            if item.reason.startswith("Role inferred from file contents by the LLM")
        }
        assert set(fields) <= mapped, (action, plan.status, plan.evidence)
