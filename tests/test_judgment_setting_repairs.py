"""Source-grounded regressions for H34, J17 and M25; no model calls or scientific runs."""
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.interpretation import method_conditions as methods
from netzoo_agent_core.workflow_conditions import (
    StatedSetting, boolean_value, combination_issues, conditions_for, setting_issue,
)


def reading(method, quote, *, settings=(), samples=None, samples_quote="", ask=""):
    return SimpleNamespace(named_method=method, named_method_quote=quote, quote=ask,
                           settings=[SimpleNamespace(name=n, quote=q, value_quote=v) for n, q, v in settings],
                           sample_count=samples, sample_count_quote=samples_quote, feature_counts=[])


@pytest.mark.parametrize("value", ["0.05", "0.5", "1.25", "confidence 0.05", "1e-3", "option1", "utf8"])
def test_decimal_fragments_are_never_boolean_tokens(value):
    assert boolean_value(value) is None


@pytest.mark.parametrize("value,quote,expected", [
    # "keep" alone settles nothing; the plain reader never reads a phrase it was not given (Claude split, 2026-10-21).
    ("keep", "keep the normalization by each patient's mutation burden", None),
    ("keep", "keep normalization off", None),
    ("keep false", "keep normalization false", False),
    ("keep true", "keep normalization true", True),
    ("keep the normalization by each patient's mutation burden.", "", None),
    ("keep normalization off.", "", False),
    ("maybe keep normalization", "", None),
    ("keep current settings", "", None),
    ("0", "", False), ("1", "", True), ("keep", "", None),
])
def test_keep_requires_context_and_preserves_negation(value, quote, expected):
    assert boolean_value(value, quote) is expected


def test_unparsed_explicit_value_is_unresolved_and_cannot_bind_a_default():
    conditions = conditions_for("SAMBAR")
    setting = {"name": "SAMBAR.norm_patient", "quote": "normalization is sparse-ish", "value": "sparse-ish"}
    assert setting_issue(conditions, StatedSetting(setting["name"], setting["quote"], setting["value"])) is None
    unresolved = methods.unresolved_settings({"named": "SAMBAR", "settings": [setting]}, ["sambar.subtypes"])
    assert unresolved and unresolved[0]["name"] == "SAMBAR.norm_patient"
    assert unresolved[0]["quote"] == setting["quote"]
    assert methods.run_setting_value(conditions.settings["norm_patient"], conditions, setting) is None
    assert methods.stated_no_value(conditions.settings["norm_patient"], setting) is False


def test_enum_alternatives_are_unresolved_but_a_concrete_unsupported_value_is_invalid():
    conditions = conditions_for("OTTER")
    alternatives = StatedSetting("OTTER.precision", "precision single or double", "single or double")
    unsupported = StatedSetting("OTTER.precision", "precision half", "half")
    assert setting_issue(conditions, alternatives) is None
    assert setting_issue(conditions, unsupported)
    method = {"named": "OTTER", "settings": [{"name": alternatives.name, "quote": alternatives.quote,
                                                  "value": alternatives.value}]}
    assert methods.unresolved_settings(method, ["otter.tf_gene_network"])


def _core(check, task, action="no_tool"):
    from netzoo_agent_core.contracts import TaskDecision
    from netzoo_agent_core.interpretation.core_decision import decide_core
    return decide_core(TaskDecision(action=action, in_scope=True, should_execute=action != "no_tool",
                                     confidence=1.0, reason="regression", capability_check=check), task)


def test_unparsed_boolean_is_ask_in_core_and_with_core_holds_execution():
    from test_method_conditions import _ask, _check
    from netzoo_agent_core.contracts import TaskDecision
    from netzoo_agent_core.interpretation.core_decision import decide_core, with_core
    task = "Run SAMBAR on 8 tumours with normalization sparse-ish."
    check = _check(task, _ask(task, ["sambar.subtypes"], named="SAMBAR", named_quote="SAMBAR",
                             scale="per_sample", settings=[("SAMBAR.norm_patient", "normalization sparse-ish", "sparse-ish")],
                             samples=8, samples_quote="8 tumours"))
    decision = TaskDecision(action="run_sambar", in_scope=True, should_execute=True, confidence=1.0,
                            reason="regression", capability_check=check)
    core = decide_core(decision, task)
    assert core.kind == "ASK"
    assert any("norm_patient" in fact.question and fact.user_quote == "normalization sparse-ish" for fact in core.facts)
    held = with_core(decision, core)
    assert held.action == "no_tool" and not held.should_execute


@pytest.mark.parametrize("control,words,expected", [
    ("log_transformed", "log2-transformed", True),
    ("log_transformed", "already log-transformed", True),
    ("log_transformed", "log10 transformed", True),
    ("log_transformed", "logarithmically transformed", True),
    ("log_transformed", "not log2-transformed", False),
    ("log_transformed", "untransformed", None),  # no negation word and not the control's own word: asked
    ("centered", "centered per gene", True),
    ("centered", "mean-centred per gene", None),  # another spelling than the control's name: asked
    ("centered", "gene-wise centered", True),
    ("centered", "not centered per gene", False),
    ("centered", "uncentered", None),
    ("centered", "uncentred", None),
    ("sparsify", "centered per gene", None),
    ("save_pvals", "log2-transformed", None),
])
def test_preparation_booleans_are_control_aware_and_share_validation_and_binding(control, words, expected):
    conditions = conditions_for("BONOBO")
    setting = {"name": f"BONOBO.{control}", "quote": words, "value": words}
    assert methods.run_setting_value(conditions.settings[control], conditions, setting) is expected
    unresolved = methods.unresolved_settings({"named": "BONOBO", "settings": [setting]}, ["bonobo.per_sample_networks"])
    assert bool(unresolved) is (expected is None)


def test_original_c40_preparation_reading_does_not_regress_to_an_unnecessary_question():
    import gzip
    import importlib.util
    import json
    from netzoo_agent_core.contracts import TaskDecision
    from netzoo_agent_core.interpretation.core_decision import decide_core
    source = Path(__file__).parents[1] / "docs/research-log/reading-coverage-2026-10-20"
    spec = importlib.util.spec_from_file_location("c40_frozen_replay", source / "replay.py")
    replay = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(replay)
    row = json.loads(gzip.decompress((source / "inputs.json.gz").read_bytes()))["29ce7f6f4c439fb8"]
    check, _ = replay.rebuild(row)
    decision = TaskDecision.model_validate(row["decision"]).model_copy(update={"capability_check": check})
    core = decide_core(decision, row["task"], reason_code=row["reason"] or "")
    assert core.kind == "DO" and not core.facts
    bound = methods.verified_controls(check, "run_bonobo")
    assert bound["log_transformed"] is True and bound["centered"] is True


def test_a_boolean_control_named_by_its_own_words_holds_without_a_phrase_list():
    """Claude split (2026-10-21): the control's own name, never a list of phrases, says the value words state it."""
    from netzoo_agent_core.workflow_conditions import control_boolean_value

    sambar = conditions_for("SAMBAR").settings
    assert control_boolean_value(sambar["norm_patient"], "keep the normalization by each patient's mutation burden")
    assert control_boolean_value(sambar["norm_patient"], "no normalization by patient burden") is False
    assert control_boolean_value(sambar["norm_patient"], "sparse-ish") is None
    assert control_boolean_value(sambar["cluster"], "") is None


def test_p20_a_hyphenated_sample_count_is_never_a_setting_value():
    """Claude split (2026-10-21): Codex's generic `name value` reader took "log-centered 20-sample" as centered=20 and
    asked what centered should be; settings come only from the reading's own setting quotes."""
    task = ("Please run BONOBO on a validated log-centered 20-sample expression file, with sparsify=true, "
            "save_pvals=false and confidence=0.01.")
    item = SimpleNamespace(named_method="BONOBO", named_method_quote="BONOBO", settings=[], sample_count=None,
                           sample_count_quote="", feature_counts=[], quote=task)
    method = methods.verified_method(task, item)
    assert not any(setting["name"] == "BONOBO.centered" for setting in method.get("settings", []))
