"""Closed-menu phase 1b, step 1: the requirement contract check.

No model calls: each workflow's contract text, the (requirement, candidate) pairs, the strict schema, and the rule that
met or contradicted stands only on a clause verbatim in that workflow's contract.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.menu_reading import MenuReading, Requirement, Said, Wanted  # noqa: E402
from netzoo_agent_core.graph.menu_reading_call import read_requirements  # noqa: E402
from netzoo_agent_core.interpretation.menu_decision import decide_menu  # noqa: E402
from netzoo_agent_core.interpretation.menu_requirements import (  # noqa: E402
    MAX_PAIRS, apply_verdicts, requirement_model, requirement_pairs, requirement_text, workflow_contract,
)

OTTER_CLAUSE = "Non-convex objective; netZooPy takes fixed gradient steps."
BONOBO_TASK = "We want a gene co-expression network for each of our 9 biopsies, with a p-value for every edge."


def said(value: str, quote: str) -> Said:
    return Said(status="stated", value=value, basis="explicit", quotes=[quote])


def bonobo_reading() -> MenuReading:
    return MenuReading(wanted=[Wanted(quote="a gene co-expression network for each of our 9 biopsies",
                                      artifact=said("coexpression_network", "a gene co-expression network"),
                                      granularity=said("per_sample", "for each of our 9 biopsies"),
                                      requirements=[Requirement(quote="with a p-value for every edge")])],
                       data=["expression"])


def test_a_workflow_contract_holds_its_policy_text_and_sheet_lines():
    text = workflow_contract("OTTER")
    assert text.startswith("OTTER: ") and OTTER_CLAUSE in text and "- does not give: " in text
    assert "- gives: " in workflow_contract("BONOBO")


def test_pairs_are_every_requirement_with_every_candidate():
    pairs = requirement_pairs(bonobo_reading(), ["BONOBO", "LIONESS-COEXPRESSION"])
    assert [(p.quote, p.workflow) for p in pairs] == [("with a p-value for every edge", "BONOBO"),
                                                       ("with a p-value for every edge", "LIONESS-COEXPRESSION")]
    many = MenuReading(wanted=[Wanted(quote="x", requirements=[Requirement(quote=f"r{i}") for i in range(10)])])
    assert len(requirement_pairs(many, ["BONOBO", "LIONESS-COEXPRESSION"])) == MAX_PAIRS
    text = requirement_text(BONOBO_TASK, pairs)
    assert 'p2. requirement "with a p-value for every edge" -- workflow LIONESS-COEXPRESSION' in text


def test_requirement_schema_is_strict():
    schema = requirement_model(3).model_json_schema()
    assert set(schema["properties"]) == {"p1", "p2", "p3"}
    pair = schema["$defs"]["RequirementVerdict"]
    assert pair["required"] == ["clause", "verdict"] and pair["additionalProperties"] is False


def test_a_verdict_stands_only_on_a_clause_of_that_workflows_contract():
    reading = bonobo_reading()
    pairs = requirement_pairs(reading, ["BONOBO", "LIONESS-COEXPRESSION"])
    bonobo_clause = next(line for line in workflow_contract("BONOBO").splitlines() if "p-value" in line)[2:60]
    merged, report = apply_verdicts(reading, pairs, {
        "p1": {"clause": bonobo_clause, "verdict": "met"},
        "p2": {"clause": "every edge gets a p-value", "verdict": "met"}})  # not LIONESS-COEXPRESSION's words
    assert merged.wanted[0].requirements[0].verdicts == {"BONOBO": "met", "LIONESS-COEXPRESSION": "not_addressed"}
    assert any("p2" in line for line in report.dropped)
    assert reading.wanted[0].requirements[0].verdicts == {}  # the first reading is left as it was
    decision = decide_menu(merged, BONOBO_TASK)
    assert decision.kind == "DO" and decision.workflows == ["BONOBO"]


def test_a_contradicted_requirement_rules_its_workflow_out():
    task = "Build an OTTER TF-gene network that is a convex, globally optimal solution."
    reading = MenuReading(wanted=[Wanted(quote="an OTTER TF-gene network", artifact=said(
        "regulatory_network", "TF-gene network"), requirements=[Requirement(quote="a convex, globally optimal solution")])],
        data=["expression", "motif_prior", "ppi"])
    pairs = requirement_pairs(reading, ["OTTER"])
    merged, _ = apply_verdicts(reading, pairs, {"p1": {"clause": OTTER_CLAUSE, "verdict": "contradicted"}})
    decision = decide_menu(merged, task)
    assert decision.kind == "DECLINE" and any("convex" in r for d in decision.declined for r in d.reasons)
    unproven, _ = apply_verdicts(reading, pairs, {"p1": {"clause": "", "verdict": "contradicted"}})
    assert decide_menu(unproven, task).kind == "ASK"  # not addressed: asked whether it is a must


def test_no_call_without_requirements_and_a_failed_call_keeps_the_reading():
    class Never:
        def with_structured_output(self, *args, **kwargs):
            raise AssertionError("no call")

    plain = MenuReading(wanted=[Wanted(quote="a network")])
    assert read_requirements("a network", plain, Never()) == (None, [])

    class Broken:
        def with_structured_output(self, *args, **kwargs):
            raise RuntimeError("provider down")

    read, pairs = read_requirements(BONOBO_TASK, bonobo_reading(), Broken())
    assert len(pairs) == 2 and read.reading == bonobo_reading() and "provider down" in read.error
