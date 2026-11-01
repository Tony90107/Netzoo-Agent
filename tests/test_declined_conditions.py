"""declined-conditions-2026-10-31: a DECLINE whose every line is "couldn't match" asks the guard's data confirm when the
guard's typed check rules the named (else Jev-picked) workflows out; everything else is left as it came; off by
default."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.core_decision import CoreDecision, DeclinedPart  # noqa: E402
from netzoo_agent_core.graph import declined_conditions_call as dc  # noqa: E402
from netzoo_agent_core.interpretation.reason_layers import UNMATCHED  # noqa: E402

# j9 A31
TASK = ("I'd like a DRAGON network linking serum proteins and metabolites. The proteomics comes from 50 patients in our "
        "Boston cohort and the metabolomics from 50 different patients in the Milan cohort, so no individual has both "
        "measurements.")
ASKED = "I'd like a DRAGON network linking serum proteins and metabolites."
SAME_LINE = "Layer 2 is reordered to layer 1 only after exact sample-ID set equality is proven."
VIOLATED = {"violated": SAME_LINE, "workflow": "DRAGON", "sentence": "The proteomics comes from 50 patients in our "
            "Boston cohort and the metabolomics from 50 different patients in the Milan cohort, so no individual has "
            "both measurements.", "data": ("several", 0.9), "same_samples": ("no", 0.95)}


def _decline(line=f'"{ASKED}" -- {UNMATCHED}', basis="full_gap", kind="DECLINE"):
    return CoreDecision(kind=kind, basis=basis, declined=[DeclinedPart(quote=ASKED, line=line)])


class _Events(list):
    """Recorded events, plus the workflows each typed check was asked about (`checked`)."""


def _on(monkeypatch, typed=VIOLATED, pick=("DRAGON", 0.9)):
    monkeypatch.setenv("NETZOO_DECLINED_CONDITIONS", "on")
    monkeypatch.setenv("NETZOO_JEV_GUARD", "on")
    events, checked = _Events(), []
    monkeypatch.setattr(dc, "record_event", lambda *a: events.append(a[2:]))
    monkeypatch.setattr(dc, "check_result", lambda task: {"result": pick[0], "confidence": pick[1]})

    def typed_check(task, workflows):
        checked.append(list(workflows))
        return {**typed, "checked": list(workflows)}
    monkeypatch.setattr(dc, "check_typed_data", typed_check)
    events.checked = checked
    return events


def test_only_a_result_level_decline_with_layer_two_lines_qualifies():
    assert dc.generic_decline(_decline())
    assert not dc.generic_decline(_decline(line=f'"{ASKED}" -- not available here as asked. DRAGON: two layers'))
    assert not dc.generic_decline(_decline(basis="jev_answer"))
    assert not dc.generic_decline(CoreDecision(kind="DO", basis="results_given"))


def test_named_candidates_use_the_registry_spelling():
    assert dc.named_candidates(TASK) == ["DRAGON"]
    assert dc.named_candidates("Run LIONESS-PANDA on 40 samples.") == ["LIONESS-PANDA"]
    assert dc.named_candidates("our panda cohort") == []


def test_off_by_default_nothing_is_called(monkeypatch):
    monkeypatch.delenv("NETZOO_DECLINED_CONDITIONS", raising=False)
    monkeypatch.setattr(dc, "check_typed_data", lambda *a: (_ for _ in ()).throw(AssertionError("called")))
    core = _decline()
    assert dc.apply_declined_conditions(None, {}, core, TASK) is core


def test_on_a_typed_violation_becomes_the_guards_data_confirm(monkeypatch):
    events = _on(monkeypatch)
    after = dc.apply_declined_conditions(None, {}, _decline(), TASK)
    assert (after.kind, after.basis) == ("ASK", "jev_condition")
    fact = after.facts[0]
    assert fact.depends_on == "jev:condition" and fact.contract_quote == SAME_LINE
    assert fact.user_quote == VIOLATED["sentence"]
    assert after.evidence["jev_condition"]["kind_before"] == "DECLINE"
    assert events[-1][0] == "core.declined_conditions" and events[-1][2]["source"] == "jev_result"


def test_on_no_violation_or_a_confirm_already_asked_leaves_the_decline(monkeypatch):
    _on(monkeypatch, typed={"violated": None, "data": ("several", 0.9)})
    core = _decline()
    assert dc.apply_declined_conditions(None, {}, core, TASK) is core
    _on(monkeypatch)
    asked = {"task_state": {"pending": [{"what": "jev:condition"}]}}
    assert dc.apply_declined_conditions(None, asked, core, TASK) is core


def test_the_candidate_is_only_jevs_confident_pick(monkeypatch):
    events = _on(monkeypatch, pick=("CONDOR", 0.6))
    task = "I have a gene-gene co-expression edge list from 200 liver samples. I'd like it split into communities."
    core = _decline()
    assert dc.apply_declined_conditions(None, {}, core, task) is core
    assert events[-1][2]["action"] == "no_candidate"
    events = _on(monkeypatch, pick=("CONDOR", 0.9))
    after = dc.apply_declined_conditions(None, {}, core, task)
    assert after.kind == "ASK" and events[-1][2]["source"] == "jev_result"


def test_a_workflow_named_only_as_the_files_source_is_not_a_candidate(monkeypatch):
    """Round 1's j2 Q34: DRAGON made the file, CONDOR is asked; only the asked result's workflow is checked."""
    task = ("I already ran DRAGON on our methylation and expression layers and saved the partial-correlation matrix. "
            "Now I want CONDOR to find communities directly in that DRAGON matrix.")
    events = _on(monkeypatch, pick=("CONDOR", 0.95))
    dc.apply_declined_conditions(None, {}, _decline(), task)
    assert events.checked == [["CONDOR"]]


def test_shadow_records_but_leaves_the_decline(monkeypatch):
    events = _on(monkeypatch)
    monkeypatch.setenv("NETZOO_DECLINED_CONDITIONS", "shadow")
    core = _decline()
    assert dc.apply_declined_conditions(None, {}, core, TASK) is core
    assert events[-1][2]["applied"] is False and events[-1][2]["action"] == "ask"


def test_a_failed_read_leaves_the_decline(monkeypatch):
    events = _on(monkeypatch)
    monkeypatch.setattr(dc, "check_typed_data", lambda *a: (_ for _ in ()).throw(RuntimeError("no_key")))
    core = _decline()
    assert dc.apply_declined_conditions(None, {}, core, TASK) is core
    assert events[-1][2]["action"] == "not_run"


def test_left_without_the_guard(monkeypatch):
    """Review 2026-11-01 (a): only the guard binds the user's "yes" to the data confirm, so nothing is asked without it."""
    _on(monkeypatch)
    monkeypatch.setenv("NETZOO_JEV_GUARD", "off")
    core = _decline()
    assert dc.apply_declined_conditions(None, {}, core, TASK) is core


def test_left_on_all_results_not_available(monkeypatch):
    """Review 2026-11-01 (b): the answer path replaces the reason on `full_gap` only."""
    _on(monkeypatch)
    core = _decline(basis="all_results_not_available")
    assert dc.apply_declined_conditions(None, {}, core, TASK) is core
