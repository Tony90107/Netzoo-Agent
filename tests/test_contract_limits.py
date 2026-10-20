"""Core decision spec, phase 4a (section 12.2): a contract limit a request can decide is checked at request level.

Round p0-p3 C57 ("48-gene NanoString panel on 600 patients"): the counts were read right, but COBRA's "more genes
than samples" lived only in its input check, so COBRA was offered in all four rounds. The rule is now one function
both call; every input_checks entry says whether a request can decide it, and a request one must map to a limit.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

import pytest  # noqa: E402

from netzoo_agent_core.contract_text import check_limit, check_scope, check_text  # noqa: E402
from netzoo_agent_core.data import cobra  # noqa: E402
from netzoo_agent_core.interpretation.method_conditions import method_fitting  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyError, ProjectPolicyLoader  # noqa: E402
from netzoo_agent_core.workflow_conditions import (  # noqa: E402
    StatedSetting, combination_issues, conditions_for, data_issue,
)

ROOT = Path(__file__).parents[1]


@pytest.fixture(scope="module")
def policy():
    return ProjectPolicyLoader(ROOT).load()


def _limit_holds(workflow: str, limit: str) -> bool:
    """Whether the request-level limit an input_checks entry names exists and acts for this workflow."""
    conditions = conditions_for(workflow)
    if limit == "min_samples":
        return conditions.min_samples is not None
    if limit == "max_values":
        return conditions.max_values is not None and conditions.size is not None
    if limit == "omics_layers":
        return conditions.omics_layers > 0
    if limit.startswith("relation:"):
        return conditions.relation_name == limit.split(":", 1)[1] and conditions.relation is not None
    if limit.startswith("setting:"):
        name = limit.split(":", 1)[1].split("<")[0].split(">")[0]
        stated = [StatedSetting(f"{workflow}.{name}", f"{name} 9", "9")]
        return f"{workflow}.{name}".split(".")[1] in conditions.settings and bool(combination_issues(conditions, stated, 2))
    if limit.startswith("refuses_input:"):  # ROUND-02 D: data the user asks to give the workflow as its input
        from netzoo_agent_core.contracts.slim_reading import SlimReading, Stated
        from netzoo_agent_core.interpretation.contract_veto import contract_veto
        fed = Stated(field="A3", name=limit.split(":", 1)[1], value="has", quote="the file", workflow=workflow)
        return any(v.kind == "C8" for v in contract_veto(SlimReading(data=[fed]), [workflow]).violations.get(workflow, []))
    return False


def test_every_request_scope_input_check_maps_to_a_limit_that_acts(policy):
    """The completeness test: a contract limit a request can decide never stays request-blind."""
    request = [(spec.workflow, check_text(item), check_limit(item)) for spec in policy.workflows.values()
               for item in spec.input_checks if check_scope(item) == "request"]
    assert len(request) == 13  # ROUND-02 D: LIONESS-PANDA refuses an aggregate co-expression input; ROUND-10: DRAGON,
    # GIRAFFE and COBRA state the sample minimum their preflight enforces
    missing = [(workflow, text, limit) for workflow, text, limit in request if not _limit_holds(workflow, limit)]
    assert missing == []


def test_cobra_rule_is_one_function_the_input_check_and_the_request_check_both_follow(tmp_path):
    """The consistency test: COBRA's real input check and the request-level limit agree at the boundary."""
    def tables(genes, samples):
        ids = [f"S{index}" for index in range(samples)]
        expression = tmp_path / f"expr_{genes}x{samples}.tsv"
        expression.write_text("gene\t" + "\t".join(ids) + "\n" + "".join(
            f"G{g}\t" + "\t".join(str((g + 1) * (s + 2) % 7 + 0.5) for s in range(samples)) + "\n" for g in range(genes)))
        design = tmp_path / f"design_{genes}x{samples}.tsv"
        design.write_text("sample\tbatch\n" + "".join(f"{sample}\t{index % 2}\n" for index, sample in enumerate(ids)))
        return str(expression), str(design)

    conditions = conditions_for("COBRA")
    for genes, samples in ((5, 6), (6, 6), (7, 6)):
        try:
            cobra.load_cobra_inputs(*tables(genes, samples))
            input_check = None
        except ValueError as error:
            input_check = "COBRA requires more genes than samples" if "more genes than samples" in str(error) else None
        request = data_issue(conditions, samples, genes, genes)
        assert (input_check is None) == (request is None), (genes, samples, input_check, request)
    expression, design = tables(7, 6)
    cobra.load_cobra_inputs(expression, design)  # the passing side loads cleanly, so the agreement above is not vacuous


def test_the_relation_is_judged_on_one_stated_feature_count_only():
    conditions = conditions_for("COBRA")
    assert data_issue(conditions, 600, 48, 48) == ("COBRA requires more genes than samples; the request has 48 genes "
                                                   "and 600 samples")
    assert data_issue(conditions, 600, 48, None) is None  # two data types' counts: never summed into "genes"
    assert data_issue(conditions, None, 48, 48) is None  # an unstated sample count is never assumed
    assert data_issue(conditions, 140, 18000, 18000) is None


def test_method_fitting_drops_cobra_for_too_few_genes_with_the_contract_reason():
    kept, limits, _instead, _defaults = method_fitting({"samples": 600, "features": 48, "feature_counts": 1},
                                                       ["cobra.covariate_components"])
    assert kept == [] and "COBRA requires more genes than samples" in limits[0]
    kept, limits, _, _ = method_fitting({"samples": 600, "features": 48, "feature_counts": 2},
                                        ["cobra.covariate_components"])
    assert kept == ["cobra.covariate_components"] and limits == []


@pytest.mark.parametrize("entry, ok", [
    ('  - text: "at least three total samples"\n    scope: request\n    limit: "min_samples"\n', True),
    ('  - "at least three total samples"\n', True),  # a plain string is scope file
    ('  - text: "at least three total samples"\n    scope: request\n', False),  # request without its limit
    ('  - text: "at least three total samples"\n    scope: file\n    limit: "min_samples"\n', False),
    ('  - text: "at least three total samples"\n    scope: request\n    limit: "whatever"\n', False),
])
def test_the_loader_holds_scope_and_limit(tmp_path, entry, ok):
    source = (ROOT / "workflows" / "bonobo.yaml").read_text()
    head = source.split("input_checks:\n")[0]
    path = tmp_path / "bonobo.yaml"
    path.write_text(head + "input_checks:\n" + entry)
    if ok:
        ProjectPolicyLoader._load_workflow_spec(path)
    else:
        with pytest.raises(ProjectPolicyError, match="scope request"):
            ProjectPolicyLoader._load_workflow_spec(path)


def test_an_enum_value_is_named_by_its_spelling_or_the_contracts_other_name_for_it():
    """p3-p4c C52: "saved as HDF5" named neither .h5 nor .hdf, so BONOBO was declined for its own default format."""
    from netzoo_agent_core.workflow_conditions import enum_value, setting_issue

    conditions = conditions_for("BONOBO")
    limit = conditions.settings["bonobo_output_format"]
    assert [enum_value(limit, words) for words in ("HDF5", ".hdf", "csv", "HDF5 or CSV")] == [".h5", ".hdf", ".csv", None]
    assert setting_issue(conditions, StatedSetting("BONOBO.bonobo_output_format", "saved as HDF5", "HDF5")) is None


def test_the_loader_holds_value_names_to_allowed_values(tmp_path):
    """Even where the registry and the YAML agree, another name must name an allowed value."""
    from dataclasses import replace

    from netzoo_agent_core.contracts import TaskDecision
    from netzoo_agent_core.policy import _control_from_spec, _validate_controls
    from workflow_registry import ACTION_DEFINITIONS

    source = (ROOT / "workflows" / "bonobo.yaml").read_text()
    assert "      HDF5: .h5\n" in source
    path = tmp_path / "bonobo.yaml"
    path.write_text(source.replace("      HDF5: .h5\n", "      HDF5: .hdf5\n"))
    spec = ProjectPolicyLoader._load_workflow_spec(path)
    definition = replace(ACTION_DEFINITIONS["run_bonobo"], controls=tuple(map(_control_from_spec, spec.controls)))
    with pytest.raises(ProjectPolicyError, match="value_names must name allowed enum values"):
        _validate_controls("run_bonobo", spec, definition, set(TaskDecision.model_fields))


def test_the_requests_feature_counts_reach_an_ask_with_their_number_of_data_types():
    """Phase 5b review: the request's features reached an ask without feature_counts, so `_single` read a sum over
    two data types as one count and a relation could be judged on it."""
    from netzoo_agent_core.interpretation.method_conditions import _single, with_request_method

    whole = {"features": 348, "feature_counts": 2, "feature_items": [[0, 5, 48], [10, 15, 300]]}
    merged = with_request_method({"samples": 600, "samples_quote": "600 patients"}, whole)
    assert (merged["features"], merged["feature_counts"], _single(merged)) == (348, 2, None)
    assert data_issue(conditions_for("COBRA"), 600, merged["features"], _single(merged)) is None
