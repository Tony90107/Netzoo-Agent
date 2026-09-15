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


def test_unknown_filenames_are_mapped_by_content_and_need_confirmation(
    tmp_path, monkeypatch
):
    # The fixtures below carry placeholder gene labels, so the plan only reaches
    # confirmation under Synthetic Test mode; in Planning mode the gene-authority
    # gate correctly refuses them. This test is about content role mapping.
    monkeypatch.setattr("netzoo_agent_core.settings.TEST_DATA_MODE", True)
    monkeypatch.setenv("NETZOO_GENE_CACHE_PATH", str(tmp_path / "gene.sqlite3"))
    monkeypatch.setenv("NETZOO_GENE_ONLINE_LOOKUP", "off")
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
        "run_panda": ("expression_file", "motif_file", "ppi_file"),
        "run_puma": ("expression_file", "motif_file", "ppi_file", "mirna_file"),
        "run_lioness_panda": ("expression_file", "motif_file", "ppi_file"),
        "run_lioness_puma": ("expression_file", "motif_file", "ppi_file", "mirna_file"),
        "run_lioness_coexpression": ("expression_file",),
        "run_condor": ("network_file",),
        "run_cobra": ("expression_file", "design_file"),
        "run_sambar": (
            "mutation_file", "exon_size_file", "cancer_gene_file", "pathway_file"
        ),
        "run_dragon": ("omics_layer_1", "omics_layer_2"),
        "run_otter": ("expression_file", "motif_file", "ppi_file"),
        "run_giraffe": ("expression_file", "motif_file", "ppi_file"),
        "run_bonobo": ("expression_file",),
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


def _panda_plan(task, mapper):
    return build_workflow_plan(
        TaskDecision(
            action="run_panda",
            in_scope=True,
            should_execute=True,
            confidence=1.0,
            reason="Run PANDA.",
        ),
        task,
        content_mapper=mapper,
    )


def _crossed_fixtures(tmp_path):
    """Correct contents behind misleading filenames, labelled by their names."""
    expression = _write(
        tmp_path / "motif.tsv", "gene\ts1\ts2\nG1\t1\t2\nG2\t2\t1\n"
    )
    motif = _write(tmp_path / "expression.tsv", "TF1\tG1\t1\nTF2\tG2\t1\n")
    ppi = _write(tmp_path / "ppi.tsv", "TF1\tTF2\t1\n")
    task = (
        f"Run PANDA with expression_file={motif} motif_file={expression} "
        f"ppi_file={ppi}."
    )
    return expression, motif, ppi, task


class ContentSniffingMapper:
    """Answer from the previews alone, the way an unbiased reader would.

    The correction probe withholds filenames, so a fake that keys off paths
    would not exercise it. This one reads the prompt it is actually given.
    """

    def __init__(self, confidence=0.92):
        self.confidence = confidence
        self.calls = []

    @staticmethod
    def _blocks(prompt):
        blocks = {}
        for chunk in prompt.split("FILE: ")[1:]:
            label, _, preview = chunk.partition("\nCONTENT PREVIEW:\n")
            blocks[label.strip()] = preview.split("\n\n")[0]
        return blocks

    def invoke(self, messages):
        self.calls.append(messages)
        prompt = messages[-1].content
        blocks = self._blocks(prompt)
        genes = {
            line.split("\t")[0]
            for preview in blocks.values()
            if preview.strip().lower().startswith("gene")
            for line in preview.strip().splitlines()[1:]
        }
        assignments = []
        for label, preview in blocks.items():
            lines = preview.strip().splitlines()
            first = lines[0] if lines else ""
            columns = first.split("\t")
            if first.lower().startswith("gene"):
                role = "expression"
            elif len(columns) == 3 and columns[1] in genes:
                # Both priors are three-column edge lists; only the motif's
                # second column holds target genes from the expression matrix.
                role = "motif"
            else:
                role = "ppi"
            assignments.append(
                {
                    "path": label,
                    "role": role,
                    "confidence": self.confidence,
                    "rationale": f"First row is {first!r}.",
                }
            )
        return InputRoleMapping(assignments=assignments)


def _content_truth(expression, motif, ppi, confidence=0.92):
    return ContentSniffingMapper(confidence)


def test_explicitly_crossed_roles_are_reported_as_crossed_not_only_as_shape_errors(
    tmp_path, monkeypatch
):
    monkeypatch.setattr("netzoo_agent_core.settings.TEST_DATA_MODE", True)
    monkeypatch.setenv("NETZOO_GENE_CACHE_PATH", str(tmp_path / "gene.sqlite3"))
    monkeypatch.setenv("NETZOO_GENE_ONLINE_LOOKUP", "off")
    expression, motif, ppi, task = _crossed_fixtures(tmp_path)

    plan = _panda_plan(task, _content_truth(expression, motif, ppi))

    assert plan.status == "needs_input"
    assert "the input roles are crossed" in plan.question
    assert f"expression_file: {motif.resolve()} does not match this role" in plan.question
    assert str(expression.resolve()) in plan.question
    assert f"motif_file: {expression.resolve()} does not match this role" in plan.question
    # The role hint replaces the generic remedy rather than being added to it.
    assert "Please provide corrected files" not in plan.question


def test_a_low_confidence_reassignment_is_not_reported_as_a_crossed_role(
    tmp_path, monkeypatch
):
    monkeypatch.setattr("netzoo_agent_core.settings.TEST_DATA_MODE", True)
    monkeypatch.setenv("NETZOO_GENE_CACHE_PATH", str(tmp_path / "gene.sqlite3"))
    monkeypatch.setenv("NETZOO_GENE_ONLINE_LOOKUP", "off")
    expression, motif, ppi, task = _crossed_fixtures(tmp_path)

    plan = _panda_plan(task, _content_truth(expression, motif, ppi, confidence=0.6))

    assert plan.status == "needs_input"
    assert "the input roles are crossed" not in plan.question
    assert "Please provide corrected files" in plan.question


def test_a_partial_reassignment_is_not_reported_as_a_crossed_role(
    tmp_path, monkeypatch
):
    monkeypatch.setattr("netzoo_agent_core.settings.TEST_DATA_MODE", True)
    monkeypatch.setenv("NETZOO_GENE_CACHE_PATH", str(tmp_path / "gene.sqlite3"))
    monkeypatch.setenv("NETZOO_GENE_ONLINE_LOOKUP", "off")
    expression, motif, ppi, task = _crossed_fixtures(tmp_path)
    partial = FakeContentMapper(
        [
            {
                "path": str(expression),
                "role": "expression",
                "confidence": 0.95,
                "rationale": "Gene-by-sample numeric matrix.",
            }
        ]
    )

    plan = _panda_plan(task, partial)

    assert "the input roles are crossed" not in plan.question


def test_a_valid_plan_never_pays_for_the_crossed_role_probe(tmp_path, monkeypatch):
    monkeypatch.setattr("netzoo_agent_core.settings.TEST_DATA_MODE", True)
    monkeypatch.setenv("NETZOO_GENE_CACHE_PATH", str(tmp_path / "gene.sqlite3"))
    monkeypatch.setenv("NETZOO_GENE_ONLINE_LOOKUP", "off")
    expression = _write(
        tmp_path / "expression.tsv", "gene\ts1\ts2\nG1\t1\t2\nG2\t2\t1\n"
    )
    motif = _write(tmp_path / "motif.tsv", "TF1\tG1\t1\nTF2\tG2\t1\n")
    ppi = _write(tmp_path / "ppi.tsv", "TF1\tTF2\t1\n")
    mapper = _content_truth(expression, motif, ppi)

    plan = _panda_plan(
        f"Run PANDA with expression_file={expression} motif_file={motif} "
        f"ppi_file={ppi}.",
        mapper,
    )

    assert plan.status != "needs_input"
    assert mapper.calls == []
