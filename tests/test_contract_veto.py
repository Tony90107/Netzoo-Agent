"""Hybrid spec 2026-10-19, H1: the contract veto layer at the live system's DO (no model calls).

The live system picks the workflows; this layer only checks them. A veto needs the user's words and the contract's:
a setting's own contract line, an input-check text, a capability-sheet entry, the registry, or a clause the contract
check copied that is verbatim in that workflow's contract. Narrowing and unsure readings never veto; an unsure value
that flips the workflow adds one question; the layer is off unless NETZOO_CONTRACT_VETO=1.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import LLMUsage  # noqa: E402
from netzoo_agent_core.contracts.core_decision import CoreDecision  # noqa: E402
from netzoo_agent_core.contracts.slim_reading import ResultItem, SlimReading, Stated  # noqa: E402
from netzoo_agent_core.graph import contract_veto_call, hybrid_gate_call  # noqa: E402
from netzoo_agent_core.interpretation.contract_veto import (  # noqa: E402
    check_pairs, contract_veto, limit_needs, veto_notes, vetoed_core,
)
from netzoo_agent_core.interpretation.core_views import decline_reply  # noqa: E402
from netzoo_agent_core.interpretation.menu_requirements import workflow_contract  # noqa: E402
from netzoo_agent_core.interpretation.slim_reader import Needs  # noqa: E402


def fact(field: str, name: str, value: str = "", quote: str = "", values=(), workflow: str = "") -> Stated:
    return Stated(field=field, name=name, value=value, quote=quote or value, values=list(values), workflow=workflow)


def do(*workflows: str) -> CoreDecision:
    return CoreDecision(kind="DO", basis="results_given", workflows=list(workflows), run_allowed=True)


def test_a_setting_out_of_its_contract_vetoes_with_the_settings_own_line():
    slim = SlimReading(stated=[fact("B5", "lambda1", "0.3", "fix lambda1 at 0.3", workflow="DRAGON")])
    verdict = contract_veto(slim, ["DRAGON"], "Run DRAGON; fix lambda1 at 0.3")
    [violation] = verdict.violations["DRAGON"]
    assert violation.kind == "B5" and violation.user_quote == "fix lambda1 at 0.3"
    assert violation.contract_quote.startswith("setting lambda1 (") and violation.contract_quote in \
        workflow_contract("DRAGON")
    core = vetoed_core(do("DRAGON"), verdict)
    assert core.kind == "DECLINE" and core.basis == "contract_veto"
    reply = decline_reply(core)
    assert reply.startswith("NetZoo cannot run DRAGON for this:") and 'You wrote: "fix lambda1 at 0.3"' in reply


def test_a_count_over_the_cap_vetoes_with_the_input_checks_words():
    slim = SlimReading(stated=[fact("B6", "sample_count", "120", "120 matched samples"),
                               fact("B6", "feature_count", "2500", "2,000 transcripts and 500 proteins")])
    [violation] = contract_veto(slim, ["LIONESS-DRAGON"]).violations["LIONESS-DRAGON"]
    assert violation.kind == "B6" and violation.contract_quote == "runs above 20,000,000 values are refused before they start"
    assert contract_veto(slim.model_copy(update={"stated": [fact("B6", "sample_count", "120", "120 samples"),
                                                            fact("B6", "feature_count", "300", "300 genes")]}),
                         ["LIONESS-DRAGON"]).violations == {}


def test_settings_a_workflow_does_not_take_veto_by_the_registry():
    slim = SlimReading(stated=[fact("B5", "unregistered", "0.0005", "learning rate 0.0005", workflow="GIRAFFE")])
    [violation] = contract_veto(slim, ["GIRAFFE"]).violations["GIRAFFE"]
    assert violation.kind == "C7" and violation.source == "registry" and "learning rate" not in violation.contract_quote


def test_a_claim_vetoes_every_workflow_with_the_sheet_entry_and_offers_nothing_instead():
    slim = SlimReading(stated=[fact("C2", "claims", "causal", "causally drive the expression changes")])
    verdict = contract_veto(slim, ["DRAGON", "LIONESS-DRAGON"])
    assert verdict.vetoed == ["DRAGON", "LIONESS-DRAGON"] and verdict.nearest == []
    assert all(v.source == "sheet" and "cause" in v.contract_quote for vs in verdict.violations.values() for v in vs)


def test_a_data_form_with_a_sheet_entry_vetoes_without_a_model_check():
    slim = SlimReading(stated=[fact("C4", "data_unit", "single_cells", "these are single cells")])
    verdict = contract_veto(slim, ["LIONESS-PANDA"])
    assert verdict.violations["LIONESS-PANDA"][0].source == "sheet"
    assert check_pairs(slim, ["LIONESS-PANDA"]) == []


def test_a_fact_without_code_words_vetoes_only_on_a_verified_contract_clause():
    """Binary values for DRAGON: no sheet entry, so the contract check must copy the clause; a clause that is not in
    DRAGON's contract changes nothing (reported as unverified)."""
    slim = SlimReading(stated=[fact("C4", "value_type", "binary", "the methylation calls are 0/1")])
    pairs = check_pairs(slim, ["DRAGON"])
    assert [(p.kind, p.workflow, p.reason) for p in pairs] == [("C4", "DRAGON", "value_type=binary")]
    clause = "Values must be finite continuous numeric measurements."
    assert clause in workflow_contract("DRAGON")
    vetoed = contract_veto(slim, ["DRAGON"], "", {"p1": {"clause": clause, "verdict": "contradicted"}}, pairs)
    assert vetoed.violations["DRAGON"][0].contract_quote == clause
    made_up = contract_veto(slim, ["DRAGON"], "", {"p1": {"clause": "DRAGON rejects 0/1 data.",
                                                           "verdict": "contradicted"}}, pairs)
    assert made_up.violations == {} and made_up.unverified


def test_narrowing_and_unsure_readings_never_veto():
    # an intent field (B1) is never read by this layer, and the gate does not narrow on it
    slim = SlimReading(stated=[fact("B1", "granularity", "per_sample", "one network per patient")])
    assert contract_veto(slim, ["OTTER"]).violations == {}
    # an unsure count that flips COBRA: one question, no veto
    unsure = SlimReading(data=[fact("A3", "expression", "has", "panel.tsv")],
                         stated=[fact("B6", "sample_count", "380", "380 patients"),
                                 fact("B6", "feature_count", quote="400 genes, or fewer than 350", values=("350", "400")),
                                 fact("B6", "single_feature_count", quote="400 genes, or fewer than 350",
                                      values=("350", "400"))])
    verdict = contract_veto(unsure, ["COBRA"])
    assert verdict.violations == {} and [(q.dimension, q.infeasible) for q in verdict.questions] == [
        ("feature_count", ("350",))]
    core = vetoed_core(do("COBRA"), verdict)
    assert core.kind == "ASK" and core.basis == "contract_veto_fact" and "350 or 400" in core.facts[0].question


def test_bonobos_declarations_are_asked_when_not_given():
    expression = [fact("A3", "expression", "has", "expr.tsv")]
    verdict = contract_veto(SlimReading(data=expression), ["BONOBO"])
    assert {q.dimension for q in verdict.questions} == {"setting:BONOBO.log_transformed", "setting:BONOBO.centered"}
    declared = SlimReading(data=expression,
                           stated=[fact("B4", "setting:log_transformed", "true", "log2", workflow="BONOBO"),
                                   fact("B4", "setting:centered", "true", "centered", workflow="BONOBO")])
    assert contract_veto(declared, ["BONOBO"]).questions == []


def test_a_passed_do_keeps_its_workflows_and_gains_disclosures_and_confirmations():
    slim = SlimReading(data=[fact("A3", "expression", "has", "expr.tsv")],
                       stated=[fact("D1", "groups", "responders and non-responders")])
    verdict = contract_veto(slim, ["LIONESS-PANDA"], "per-patient networks")
    core = vetoed_core(do("LIONESS-PANDA"), verdict)
    assert core.kind == "DO" and core.workflows == ["LIONESS-PANDA"] and core.run_allowed
    notes = veto_notes(core)
    assert "Good to know before running:" in notes and "not independent" in notes
    assert "Which samples should each per-sample network be estimated against?" in notes
    assert veto_notes(do("PANDA")) == ""  # the veto did not run: nothing is added


def test_one_vetoed_workflow_of_a_tie_leaves_the_others():
    slim = SlimReading(data=[fact("A3", "expression", "has", "expr.tsv")],
                       stated=[fact("B5", "lam", "1.5", "lam = 1.5", workflow="OTTER")])
    verdict = contract_veto(slim, ["PANDA", "OTTER", "GIRAFFE"])
    assert verdict.vetoed == ["OTTER"] and verdict.kept == ["PANDA", "GIRAFFE"]
    core = vetoed_core(do("PANDA", "OTTER", "GIRAFFE"), verdict)
    assert core.kind == "DO" and core.workflows == ["PANDA", "GIRAFFE"] and not core.run_allowed
    assert "NetZoo cannot run OTTER for this" in core.declined[0].line


def test_the_step_three_read_is_limit_fields_only():
    needs = limit_needs(SlimReading(results=[ResultItem(quote="x", said="menu_result", value="regulatory_network")]),
                        ["SAMBAR", "BONOBO", "OTTER"])
    assert needs.intents == () and needs.candidates == ("SAMBAR", "BONOBO", "OTTER")
    assert set(needs.conditions) == {"mutation_origin", "setting:BONOBO.log_transformed", "setting:BONOBO.centered"}


def _context(llm):
    return SimpleNamespace(study_purpose_llm=llm, semantic_model_name="openai/gpt-4o-mini", router_max_tokens=1200,
                           task_token_budget=200_000, price_catalog=None)


def test_the_hook_is_off_by_default_and_vetoes_a_live_do_when_on(monkeypatch):
    events = []
    monkeypatch.setattr(contract_veto_call, "record_event", lambda *a: events.append(a[2]))
    monkeypatch.setattr(hybrid_gate_call, "record_event", lambda *a: events.append(a[2]))
    monkeypatch.setattr(hybrid_gate_call, "preflight_budget",
                        lambda context, state, **kw: (SimpleNamespace(status="ok"), state["budget_warnings"]))
    monkeypatch.setattr(hybrid_gate_call, "append_llm_usage", lambda usage, **kw: usage)
    task = "Run GIRAFFE on our 44 biopsies with learning rate 0.0005."
    core_payload = {"items": [{"quote": "Run GIRAFFE on our 44 biopsies", "asks": "workflow_only", "result": "",
                               "results": [], "outside_name": ""}], "names": {"GIRAFFE": {"role": "target"}},
                    "data": [], "only_these": "", "run": "run", "run_quote": "Run GIRAFFE", "facts": [],
                    "unregistered_methods": []}
    seen = []

    class Model:
        def with_structured_output(self, schema, **kwargs):
            seen.append(schema.__name__)
            if schema.__name__ == "SlimCoreWire":
                return SimpleNamespace(invoke=lambda m: {"parsed": schema.model_validate(core_payload), "raw": None})
            payload = {"settings": [{"quote": "learning rate 0.0005", "workflow": "GIRAFFE", "control": "unregistered",
                                     "value": "0.0005", "values": [], "asks_to_set": True}]}
            payload.update({name: {"quote": "", "status": "not_said", "value": None, "values": []}
                            for name in schema.model_fields if name not in ("settings", "counts")})
            if "counts" in schema.model_fields:
                payload["counts"] = []
            return SimpleNamespace(invoke=lambda m: {"parsed": schema.model_validate(payload), "raw": None})

    state = {"budget_warnings": []}
    usage = LLMUsage(budget_tokens=200_000)
    core, *_ = contract_veto_call.apply_contract_veto(_context(Model()), state, None, do("GIRAFFE"), task, usage, [])
    assert core.kind == "DO" and seen == []  # off by default: no call
    monkeypatch.setenv("NETZOO_CONTRACT_VETO", "1")
    core, *_ = contract_veto_call.apply_contract_veto(_context(Model()), state, None, do("GIRAFFE"), task, usage, [])
    assert core.kind == "DECLINE" and core.basis == "contract_veto" and "core.contract_veto" in events
    assert seen[0] == "SlimCoreWire" and "SlimFocusWire" in seen

    class Broken:
        def with_structured_output(self, *args, **kwargs):
            raise RuntimeError("provider down")

    core, *_ = contract_veto_call.apply_contract_veto(_context(Broken()), state, None, do("GIRAFFE"), task, usage, [])
    assert core.kind == "DO"  # a failed read leaves the live call as it was


def test_words_that_set_nothing_are_no_setting_and_settings_are_no_method():
    """H1 debug on the seen h1-h3 live DOs: five false refusals came from settings the words never set."""
    from netzoo_agent_core.interpretation.slim_reader import merge_focus
    task = ("Go ahead and run it now. Leave lambda1 and lambda2 empty so they're estimated; output in modules/brain/. "
            "Sparsify with bonobo_confidence 0.01.")
    needs = Needs(candidates=("DRAGON", "CONDOR", "BONOBO"))
    slim, report = merge_focus(SlimReading(), {"settings": [
        {"quote": "Go ahead and run it now", "workflow": "DRAGON", "control": "unregistered", "value": "",
         "values": [], "asks_to_set": True},
        {"quote": "Leave lambda1 and lambda2 empty", "workflow": "DRAGON", "control": "lambda1", "value": "",
         "values": [], "asks_to_set": True},
        {"quote": "output in modules/brain/", "workflow": "CONDOR", "control": "unregistered", "value": "modules/brain/",
         "values": [], "asks_to_set": True},
        {"quote": "Sparsify with bonobo_confidence 0.01", "workflow": "BONOBO", "control": "bonobo_confidence",
         "value": "0.01", "values": [], "asks_to_set": True}]}, task, needs)
    assert [(f.name, f.value) for f in slim.stated] == [("bonobo_confidence", "0.01")] and len(report.dropped) == 3
    with_method = slim.model_copy(update={"unregistered_methods": ["Sparsify with bonobo_confidence 0.01"]})
    assert not any(v.kind == "C5" for v in contract_veto(with_method, ["BONOBO"], task).violations.get("BONOBO", []))
    real = SlimReading(unregistered_methods=["TIGER"])
    assert contract_veto(real, ["PANDA"]).violations["PANDA"][0].kind == "C5"
    # a listed value of the workflow's own control names that setting (OTTER's output_format edge_list)
    assert contract_veto(SlimReading(unregistered_methods=["edge-list output"]), ["OTTER"]).violations == {}
    # another workflow's control ("iterations" is OTTER's) does not make GIRAFFE's optimizer change a setting of its own
    optimizer = SlimReading(unregistered_methods=["change the optimizer: learning rate 0.0005, 5,000 iterations"])
    assert contract_veto(optimizer, ["GIRAFFE"]).violations["GIRAFFE"][0].kind == "C5"


def test_core_data_never_mentioned_is_asked_once_in_the_same_reply_never_vetoed():
    """User decision 2026-10-19: a chosen workflow's core data, neither had nor lacked in the words, is asked."""
    unmentioned = contract_veto(SlimReading(), ["SAMBAR"], "Group our tumours with SAMBAR.")
    assert unmentioned.violations == {}
    [question] = [q for q in unmentioned.questions if q.dimension.startswith("data:")]
    assert question.dimension == "data:mutation_calls"
    core = vetoed_core(do("SAMBAR"), unmentioned)
    assert core.kind == "ASK" and core.facts[0].question.startswith("Do you have somatic mutation calls")
    had = SlimReading(data=[fact("A3", "mutation_calls", "has", "mut.csv")])
    assert not any(q.dimension.startswith("data:") for q in contract_veto(had, ["SAMBAR"]).questions)
    lacked = SlimReading(data=[fact("A3", "mutation_calls", "lacks", "we have no mutation calls")])
    assert not any(q.dimension.startswith("data:") for q in contract_veto(lacked, ["SAMBAR"]).questions)
    # one question for every chosen workflow's unmentioned core data; OTTER takes either table
    tie = contract_veto(SlimReading(data=[fact("A3", "coexpression_matrix", "has", "coexp.npy")]),
                        ["PANDA", "OTTER"])
    assert [q.dimension for q in tie.questions] == ["data:expression"]
    layers = contract_veto(SlimReading(data=[fact("A3", "expression", "has", "rna.csv")]), ["DRAGON"])
    assert [q.dimension for q in layers.questions] == ["data:two_layers"]


def test_core_data_step_one_missed_is_read_once_in_step_three():
    """H2 prep (debug on seen sets): step 1 wrote no data for "Run PANDA now on data/gtex_liver_expr.txt ..."; the
    limit read gets one cell for a chosen workflow's core data step 1 did not mention, and a named file counts."""
    from netzoo_agent_core.interpretation.slim_reader import focus_model, merge_focus
    task = "Run PANDA now on data/liver_expr.txt with motif.txt and ppi.txt."
    needs = limit_needs(SlimReading(), ["PANDA"])
    assert needs.data == ("expression",) and ("has_expression", -2, "data:expression") in needs.cells()
    assert "has_expression" in focus_model(needs).model_json_schema()["properties"]
    slim, _ = merge_focus(SlimReading(), {"has_expression": {"quote": "data/liver_expr.txt", "status": "stated",
                                                             "value": "has", "values": []}, "settings": []}, task, needs)
    assert [(d.name, d.value) for d in slim.data] == [("expression", "has")]
    assert not any(q.dimension.startswith("data:") for q in contract_veto(slim, ["PANDA"], task).questions)
    assert limit_needs(slim, ["PANDA"]).data == ()  # read once: mentioned now, never read again
