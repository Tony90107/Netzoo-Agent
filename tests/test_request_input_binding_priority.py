"""User-selected inputs survive routing, mapping and planning for every workflow."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from workflow_registry import ACTION_DEFINITIONS, RUN_ACTIONS
from netzoo_agent_core.contracts import TaskDecision
from netzoo_agent_core.interpretation.extraction import _task_path
from netzoo_agent_core.interpretation.hydration import hydrate_router_decision
from netzoo_agent_core.data.content_mapping import infer_input_roles
from netzoo_agent_core import build_workflow_plan
from netzoo_agent_core.settings import INPUT_ROLE_FIELDS
from netzoo_agent_core.interpretation.input_bindings import request_input_bindings


CASES = [
    (action, field)
    for action in sorted(RUN_ACTIONS)
    for field in sorted(set(ACTION_DEFINITIONS[action].required_inputs)
                        | set(ACTION_DEFINITIONS[action].optional_inputs))
    if field in INPUT_ROLE_FIELDS
]


@pytest.mark.parametrize("action,field", CASES)
def test_hydration_preserves_all_registered_input_roles(action, field):
    path = "data/study/selected.tsv"
    task = f"Use {field}=\"{path}\" for this analysis."
    decision = TaskDecision(action=action, in_scope=True, should_execute=True,
                            confidence=1, reason="test")

    hydrated = hydrate_router_decision(decision, task)

    assert getattr(hydrated, field) == path


@pytest.mark.parametrize("field,label", [
    ("motif_file", "prior regulatory table"),
    ("expression_file", "expression matrix"),
    ("design_file", "sample covariate design matrix"),
    ("ppi_file", "PPI network"),
    ("mirna_file", "miRNA list"),
    ("coexpression_file", "adjusted co-expression matrix"),
    ("network_file", "bipartite network"),
    ("mutation_file", "somatic mutation matrix"),
    ("exon_size_file", "exon size table"),
    ("cancer_gene_file", "cancer-gene list"),
    ("pathway_file", "GMT pathway file"),
    ("omics_layer_1", "layer 1"),
    ("omics_layer_2", "layer 2"),
])
def test_role_descriptions_bind_neutral_filenames(field, label):
    assert _task_path(f"My {label} (data/study/a.tsv) is the current input.", field) == "data/study/a.tsv"


@pytest.mark.parametrize("action,field", CASES)
def test_content_mapping_cannot_override_a_user_bound_role(tmp_path, action, field):
    chosen = tmp_path / "chosen.tsv"
    decoy = tmp_path / "decoy.tsv"
    chosen.write_text("id\tx\nA\t1\n")
    decoy.write_text("id\tx\nB\t2\n")

    class Mapper:
        def invoke(self, messages):
            return {"assignments": [{"role": field, "path": str(decoy), "confidence": 1}]}

    result = infer_input_roles(action, f"Use {field}={chosen}", [field], tmp_path, Mapper())
    assert field not in result


@pytest.mark.parametrize("action,field", CASES)
def test_planner_keeps_a_selected_input_when_memory_offers_another(tmp_path, monkeypatch, action, field):
    chosen = tmp_path / f"{field}.tsv"
    old = tmp_path / "old.tsv"
    chosen.write_text("id\tx\nA\t1\n")
    old.write_text("id\tx\nB\t2\n")
    monkeypatch.setattr("netzoo_agent_core.planning.evidence.reusable_episode_inputs",
                        lambda *_: ({field: str(old)}, "old episode"))
    decision = TaskDecision(action=action, in_scope=True, should_execute=True,
                            confidence=1, reason="test")

    plan = build_workflow_plan(decision, f"Use {action} with {field}={chosen}",
                               profile={"profile_id": "test", "preferences": {"reuse_last_inputs": True}})

    assert plan.decision[field] == str(chosen)


@pytest.mark.parametrize("action,field", CASES)
def test_sibling_filenames_resolve_from_any_selected_input_role(tmp_path, action, field):
    study = tmp_path / "data" / "study"
    study.mkdir(parents=True)
    task = f"Use {field}=data/study/chosen.tsv and expression_file=measurements.tsv in the same folder."
    if field == "expression_file":
        task = "Use expression_file=data/study/chosen.tsv and design_file=covariates.tsv in the same folder."

    selected = request_input_bindings(task, root=tmp_path)

    sibling = "design_file" if field == "expression_file" else "expression_file"
    assert selected.directory == study
    assert selected.values[field] == "data/study/chosen.tsv"
    assert selected.values[sibling] == f"data/study/{'covariates.tsv' if sibling == 'design_file' else 'measurements.tsv'}"


def test_output_folder_is_not_an_input_anchor(tmp_path):
    (tmp_path / "results").mkdir()
    selected = request_input_bindings("Use expression_file=measurements.tsv; output_dir=results/", root=tmp_path)
    assert selected.directory is None


def test_an_output_filename_does_not_establish_an_input_role(tmp_path):
    selected = request_input_bindings(
        "Save output_file=data/export/expression.tsv", root=tmp_path,
    )
    assert selected.values == {}
    assert selected.directory is None
    hydrated = hydrate_router_decision(
        TaskDecision(action="run_bonobo", in_scope=True, should_execute=True,
                     confidence=1, reason="test"),
        "Save output_file=data/export/expression.tsv",
    )
    assert hydrated.expression_file is None


@pytest.mark.parametrize("action,field", CASES)
def test_an_explicit_role_outranks_a_misleading_filename(tmp_path, action, field):
    misleading = "expression.tsv" if field == "ppi_file" else "ppi.tsv"
    path = f"data/study/{misleading}"
    selected = request_input_bindings(f"Use {field}={path}", root=tmp_path)

    assert selected.values == {field: path}


def test_same_folder_with_multiple_input_directories_requires_a_location(tmp_path):
    for directory in ("study_a", "study_b"):
        (tmp_path / directory).mkdir()
    selected = request_input_bindings(
        "Use expression_file=study_a/a.tsv and motif_file=study_b/b.tsv; "
        "ppi_file=c.tsv is in the same folder.", root=tmp_path,
    )
    assert selected.directory is None
    assert selected.issues
    assert "ppi_file" in selected.issues[0]
    assert selected.values["ppi_file"] == "c.tsv"


def test_planner_scopes_discovery_to_a_named_prior(tmp_path, monkeypatch):
    study = tmp_path / "study"
    study.mkdir()
    prior = study / "chosen.tsv"
    prior.write_text("TF1\tGeneA\t1\n")
    observed = []

    def mapper(action, task, fields, nearby, *_):
        observed.append(nearby)
        return {}

    monkeypatch.setattr("netzoo_agent_core.planning.evidence.infer_input_roles", mapper)
    plan = build_workflow_plan(
        TaskDecision(action="run_panda", in_scope=True, should_execute=True, confidence=1, reason="test"),
        f"Use my prior regulatory table ({prior}). Other inputs are in the same folder.",
    )

    assert observed == [study]
    assert plan.decision["motif_file"] == str(prior)
