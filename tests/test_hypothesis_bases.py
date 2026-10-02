"""Retain biological alternatives even when the classifier emits one endpoint."""

from pathlib import Path
import sys

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.outcomes import StatedHypothesisClaims
from netzoo_agent_core.graph.hypothesis_bases import (
    hypothesis_options,
    hypotheses_from_claims,
    invoke_hypothesis_matcher,
)
from netzoo_agent_core.interpretation.hypothesis_routes import render_hypothesis_routes
from test_hypothesis_routes import POLICY, decision, reading
from test_request_concerns import _context as _provider_context
from netzoo_agent_core.contracts import LLMUsage

ZH = (
    "我們收集了另一批病患的資料來做腫瘤分型，以預測化療抗藥性。這次我們同時擁有"
    "『全外顯子DNA突變分佈』與『轉錄表現量』。在決定分型依據時，團隊不知道該從"
    "『不可逆的DNA損傷累積』切入，還是從『細胞當下系統連線的動態重組』切入。"
    "針對這兩種截然不同的生化假設，工作流該如何設計？它們分別對應什麼工具？"
)
EN = (
    "We have whole-exome somatic mutation data and an RNA-seq expression matrix. "
    "For tumor subtyping to predict chemotherapy resistance, should we use accumulated "
    "DNA damage or current regulatory rewiring? Design a workflow for each hypothesis."
)
PAIRS = [
    ("run_sambar", "不可逆的DNA損傷累積"),
    ("run_lioness_panda", "細胞當下系統連線的動態重組"),
]


def _context(reply):
    # Script the scientific extraction; workflow selection is now deterministic.
    if isinstance(reply, dict) and "claims" in reply:
        from workflow_registry import OUTPUT_CAPABILITIES

        hypotheses = []
        algorithm_tags = {
            "message_passing",
            "leave_one_out_network_inference",
            "bayesian",
            "relaxed_graph_matching",
            "biologically_informed_matrix_factorization",
            "covariate_association",
        }
        for claim in reply["claims"]:
            cap = OUTPUT_CAPABILITIES.get(claim["basis"])
            item = dict(
                text_span=claim["text_span"],
                profile=cap.artifact_type if cap else "unknown",
                target_artifact=claim.get("target_artifact", "unknown"),
                granularity=next(iter(cap.granularities)) if cap else "unknown",
                regulators=sorted(cap.regulator_types) if cap else [],
                method_tags=sorted(cap.selection_tags & algorithm_tags) if cap else [],
            )
            if item not in hypotheses:
                hypotheses.append(item)
        reply = dict(
            question_mode=reply.get("question_mode", "single_goal"),
            hypotheses=hypotheses,
            concerns=reply.get("concerns", []),
        )
    return _provider_context(reply)


def collapsed():
    return decision(
        [
            reading(
                "sample_cluster_assignment",
                ["mutation_matrix"],
                granularity="aggregate",
                entities=["sample"],
            )
        ],
        matched=["run_sambar"],
    )


def claims(pairs=PAIRS):
    return StatedHypothesisClaims(
        question_mode="multiple_hypotheses",
        claims=[dict(basis=b, text_span=q) for b, q in pairs],
    )


@pytest.mark.parametrize("task", [ZH, EN])
def test_gate_survives_classifier_dropping_expression(task):
    assert {b for b, _ in hypothesis_options(collapsed(), task)} >= {
        b for b, _ in PAIRS
    }


def test_catalog_is_not_gated_on_modalities_or_tool_keywords():
    from workflow_registry import OUTPUT_CAPABILITIES

    assert {
        b for b, _ in hypothesis_options(collapsed(), "What should I investigate?")
    } == set(OUTPUT_CAPABILITIES) | {"unsupported"}


def test_grounding_rejects_invented_and_shared_quotes():
    options = hypothesis_options(collapsed(), ZH)
    accepted, rejected = hypotheses_from_claims(ZH, claims(), options)
    assert len(accepted) == 2 and not rejected
    accepted, rejected = hypotheses_from_claims(
        ZH,
        claims(
            [
                PAIRS[0],
                (PAIRS[1][0], PAIRS[0][1]),
                ("invented", "轉錄表現量"),
                (PAIRS[1][0], "not in request"),
            ]
        ),
        options,
    )
    assert not accepted and {item["reason"] for item in rejected} == {
        "not_offered", "quote_not_in_request"
    }
    accepted, rejected = hypotheses_from_claims(
        ZH, claims([PAIRS[0], (PAIRS[1][0], PAIRS[0][1])]), options
    )
    assert not accepted and rejected[-1]["reason"] == "fewer_than_two_grounded_hypotheses"


def test_model_schema_cannot_select_workflows():
    from netzoo_agent_core.graph.research_framing import framing_schema

    schema = framing_schema()
    with pytest.raises(ValidationError):
        schema.model_validate(
            {"hypotheses": [{"basis": "run_shell", "text_span": "x"}]}
        )
    assert schema.model_json_schema()["additionalProperties"] is False


def test_collapsed_routing_yields_two_concise_biological_routes():
    ctx = _context(dict(question_mode="multiple_hypotheses", hypotheses=[
        dict(text_span=PAIRS[0][1], profile="pathway_mutation_matrix", target_artifact="sample_cluster_assignment",
             target_span="腫瘤分型", granularity="aggregate"),
        dict(text_span=PAIRS[1][1], profile="regulatory_network", target_artifact="sample_cluster_assignment",
             target_span="腫瘤分型", granularity="sample_specific", regulators=["tf"]),
    ]))
    original = collapsed()
    advised, usage, _ = invoke_hypothesis_matcher(ctx, {}, ZH, original, LLMUsage(), [])
    assert len(advised.stated_hypotheses) == 2
    assert advised.action == original.action == "no_tool" and not advised.should_execute
    assert not advised.matched_actions and advised.capability_match_status == "ambiguous"
    assert [c.role for c in usage.calls] == ["hypothesis_bases"]
    text = render_hypothesis_routes(advised, POLICY, task=ZH)
    assert all(quote in text for _, quote in PAIRS)
    assert "SAMBAR" in text and "**LIONESS-PANDA**" in text
    # LIONESS-PANDA writes the PANDA cohort network itself; no arrow suggests two runs.
    assert "PANDA → LIONESS-PANDA" not in text and "so PANDA need not run first" in text
    for needed in ("somatic mutation matrix", "gene/exon-size", "cancer-gene list", "GMT pathway",
                   "expression matrix", "motif/prior", "PPI network"):
        assert needed in text
    assert "Algorithmic assumptions:" not in text and "`mutation_file`" not in text
    assert "Selected path:" not in text and "kmin" not in text
    assert "binding strength" in text and "held-out" in text
    assert "Which scientific question" in text and "parallel" in text
    assert "No files were inspected and no analysis ran." in text
    # A stored claim cannot be reused as evidence for a different follow-up.
    assert render_hypothesis_routes(advised, POLICY, task="Use SAMBAR only.") is None


@pytest.mark.parametrize(
    "reply", [{"claims": []}, RuntimeError("provider unavailable")]
)
def test_empty_or_failed_advisory_preserves_existing_guidance(reply):
    ctx = _context(reply)
    before = collapsed()
    after, usage, _ = invoke_hypothesis_matcher(ctx, {}, ZH, before, LLMUsage(), [])
    assert after == before and len(usage.calls) == 1


def test_execution_is_never_intercepted():
    before = collapsed().model_copy(
        update={"action": "run_sambar", "should_execute": True}
    )
    ctx = _context(claims().model_dump())
    after, usage, _ = invoke_hypothesis_matcher(ctx, {}, ZH, before, LLMUsage(), [])
    assert (
        after == before and not usage.calls and not ctx.selection_condition_llm.schemas
    )


@pytest.mark.parametrize(
    "action", sorted(__import__("workflow_registry").OUTPUT_CAPABILITIES)
)
def test_every_registered_workflow_can_be_compared_without_ranking(action):
    """All 12 methods use the same path, including methods outside the original example."""
    task = 'Compare "first biological hypothesis" with "second biological hypothesis".'
    pairs = [
        (action, "first biological hypothesis"),
        ("unsupported", "second biological hypothesis"),
    ]
    before = collapsed()
    after, _, _ = invoke_hypothesis_matcher(
        _context(claims(pairs).model_dump()),
        {},
        task,
        before,
        LLMUsage(),
        [],
    )
    text = render_hypothesis_routes(after, POLICY, task=task)
    assert POLICY.workflows[action].workflow in text
    assert "You would need" in text and "The analysis would provide" in text
    assert "Algorithmic assumptions:" not in text and "Required inputs:" not in text
    assert "no registered workflow" in text.lower()
    assert "Selected path:" not in text and "(recommend)" not in text
    assert "Which scientific question" not in text  # A capability gap is not another candidate.


def test_three_hypotheses_are_all_retained():
    task = 'Compare "TF activity", "regulatory wiring", and "covariate-associated coexpression".'
    pairs = [
        ("run_giraffe", "TF activity"),
        ("run_lioness_panda", "regulatory wiring"),
        ("run_cobra", "covariate-associated coexpression"),
    ]
    after, _, _ = invoke_hypothesis_matcher(
        _context(claims(pairs).model_dump()),
        {},
        task,
        collapsed(),
        LLMUsage(),
        [],
    )
    text = render_hypothesis_routes(after, POLICY, task=task)
    assert all(quote in text for _, quote in pairs)
    assert all(name in text for name in ("GIRAFFE", "LIONESS-PANDA", "COBRA"))


def test_unresolved_goal_cannot_be_overridden_by_a_preferred_method():
    from netzoo_agent_core.interpretation.research_choices import (
        render_research_choices,
    )

    before = collapsed().model_copy(
        update={
            "capability_match_status": "ambiguous",
            "hypothesis_actions": ["run_panda", "run_otter", "run_giraffe"],
            "matched_actions": [],
        }
    )
    text = render_research_choices(
        before, POLICY, task="I do not know which network result I need."
    )
    assert all(name in text for name in ("PANDA", "OTTER", "GIRAFFE"))
    assert "Which scientific question" in text and "Selected path:" not in text


def test_one_hypothesis_can_have_multiple_algorithms_without_becoming_two_hypotheses():
    task = (
        'Compare "aggregate regulatory inference" with "sample-specific coexpression".'
    )
    pairs = [
        ("run_panda", "aggregate regulatory inference"),
        ("run_otter", "aggregate regulatory inference"),
        ("run_bonobo", "sample-specific coexpression"),
    ]
    after, _, _ = invoke_hypothesis_matcher(
        _context(claims(pairs).model_dump()),
        {},
        task,
        collapsed(),
        LLMUsage(),
        [],
    )
    text = render_hypothesis_routes(after, POLICY, task=task)
    assert all(quote in text for _, quote in pairs)
    assert text.count("**PANDA**") == text.count("**OTTER**") == text.count("**BONOBO**") == 1
    assert all(name in text for name in ("PANDA", "OTTER", "BONOBO"))


def test_clear_goal_concerns_share_the_one_advisory_call():
    before = collapsed().model_copy(update={"matched_actions": ["run_otter"]})
    reply = dict(
        question_mode="single_goal",
        claims=[],
        concerns=[dict(concern="memory_limit", text_span="ran out of memory")],
    )
    after, usage, _ = invoke_hypothesis_matcher(
        _context(reply),
        {},
        "Compare OTTER with alternatives; last time it ran out of memory.",
        before,
        LLMUsage(),
        [],
    )
    assert [c.concern for c in after.addressed_concerns] == ["memory_limit"]
    assert not after.stated_hypotheses and len(usage.calls) == 1


def test_no_second_advisory_call_and_budget_block_is_respected():
    ctx = _context(claims().model_dump())
    after, usage, warnings = invoke_hypothesis_matcher(
        ctx, {}, ZH, collapsed(), LLMUsage(), []
    )
    invoke_hypothesis_matcher(ctx, {}, ZH, after, usage, warnings)
    assert len(ctx.selection_condition_llm.schemas) == 1

    ctx.task_token_budget = 1
    before = collapsed()
    after, usage, _ = invoke_hypothesis_matcher(
        ctx, {}, ZH, before, LLMUsage(budget_tokens=1), []
    )
    assert after == before and usage.budget_exhausted
    assert len(ctx.selection_condition_llm.schemas) == 1


def test_explicit_comparison_precedes_endpoint_classification(monkeypatch):
    from netzoo_agent_core.graph import router_invocation

    def unexpected(*args, **kwargs):
        pytest.fail(
            "A validated comparison must not be collapsed by the endpoint classifier"
        )

    monkeypatch.setattr(router_invocation, "_invoke_semantic_interpreter", unexpected)
    result = router_invocation.invoke_router(_context(claims().model_dump()), {}, ZH)
    assert result.reason_code == "research_choices"
    assert result.routing_state["semantic_goal"]["request_mode"] == "guidance"
    assert result.decision.hypothesis_actions == ["run_sambar", "run_lioness_panda"]
    assert not result.decision.should_execute and result.decision.action == "no_tool"


def test_failed_explicit_comparison_cannot_fall_back_to_one_workflow(monkeypatch):
    from netzoo_agent_core.graph import router_invocation

    def unexpected(*args, **kwargs):
        pytest.fail("Failure must not silently select a single surviving workflow")

    monkeypatch.setattr(router_invocation, "_invoke_semantic_interpreter", unexpected)
    result = router_invocation.invoke_router(_context(RuntimeError("offline")), {}, ZH)
    assert result.reason_code == "research_choices_unavailable"
    assert not result.decision.matched_actions and not result.decision.should_execute


@pytest.mark.parametrize(
    "basis, artifact, scale, expected",
    [
        ("run_panda", "sample_cluster_assignment", "aggregate", ["run_lioness_panda"]),
        ("run_puma", "regulatory_network", "sample_specific", ["run_lioness_puma"]),
        ("run_dragon", "sample_cluster_assignment", "aggregate", []),
        ("run_panda", "tf_activity_matrix", "sample_specific", []),
        ("run_giraffe", "tf_activity_matrix", "sample_specific", ["run_giraffe"]),
    ],
)
def test_route_must_produce_the_requested_result_and_scale(
    basis, artifact, scale, expected
):
    from netzoo_agent_core.contracts.outcomes import HypothesisBasisClaim
    from netzoo_agent_core.graph.hypothesis_bases import compatible_bases

    claim = HypothesisBasisClaim(
        basis=basis,
        text_span="a quoted hypothesis",
        target_artifact=artifact,
        target_granularity=scale,
    )
    assert compatible_bases(claim) == expected


@pytest.mark.parametrize(
    "frame, expected",
    [
        (
            dict(profile="pathway_mutation_matrix", granularity="aggregate"),
            {"run_sambar"},
        ),
        (
            dict(profile="tf_activity_matrix", granularity="sample_specific"),
            {"run_giraffe"},
        ),
        (dict(profile="community_assignment", regulators=["tf"]), {"run_condor"}),
        # Log 290: with no scale either multi-omic workflow fits equally.
        (dict(profile="multi_omic_network"), {"run_dragon", "run_lioness_dragon"}),
        (
            dict(
                profile="coexpression_network",
                granularity="aggregate",
                method_tags=["covariate_association"],
            ),
            {"run_cobra"},
        ),
        (
            dict(profile="coexpression_network", granularity="sample_specific"),
            {"run_bonobo", "run_lioness_coexpression"},
        ),
        (
            dict(
                profile="regulatory_network",
                granularity="aggregate",
                regulators=["mirna"],
            ),
            {"run_puma"},
        ),
        (
            dict(
                profile="regulatory_network",
                granularity="sample_specific",
                regulators=["mirna"],
            ),
            {"run_lioness_puma"},
        ),
        (
            dict(
                profile="regulatory_network", granularity="aggregate", regulators=["tf"]
            ),
            {"run_panda", "run_otter"},
        ),
        (
            dict(
                profile="regulatory_network",
                granularity="aggregate",
                regulators=["tf"],
                method_tags=["relaxed_graph_matching"],
            ),
            {"run_otter"},
        ),
        (
            dict(
                profile="regulatory_network",
                granularity="sample_specific",
                regulators=["tf"],
            ),
            {"run_lioness_panda"},
        ),
        (
            dict(
                profile="regulatory_network",
                granularity="aggregate",
                regulators=["tf"],
                method_tags=["bayesian"],
            ),
            set(),
        ),
    ],
)
def test_scientific_quantities_select_only_compatible_registry_methods(frame, expected):
    from netzoo_agent_core.graph.research_framing import (
        ResearchHypothesis,
        actions_for_hypothesis,
    )

    assert (
        set(
            actions_for_hypothesis(
                ResearchHypothesis(text_span="scientific evidence", **frame)
            )
        )
        == expected
    )


def test_unquoted_downstream_goal_cannot_invent_clustering():
    from netzoo_agent_core.graph.research_framing import ResearchFraming, framed_claims

    task = "Compare TF activity with each patient's regulatory wiring."
    framing = ResearchFraming(
        question_mode="multiple_hypotheses",
        hypotheses=[
            dict(
                text_span="TF activity",
                profile="tf_activity_matrix",
                target_artifact="sample_cluster_assignment",
                target_span="discover patient subtypes",
                granularity="sample_specific",
            ),
            dict(
                text_span="each patient's regulatory wiring",
                profile="regulatory_network",
                target_artifact="sample_cluster_assignment",
                granularity="sample_specific",
                regulators=["tf"],
            ),
        ],
    )
    result = framed_claims(framing, task)
    assert {c.target_artifact for c in result.claims} == {
        "tf_activity_matrix",
        "regulatory_network",
    }
    assert {c.basis for c in result.claims} == {"run_giraffe", "run_lioness_panda"}


def test_downstream_goal_is_local_to_its_hypothesis():
    from netzoo_agent_core.contracts.outcomes import StatedHypothesis

    task = "Compare tumor subtypes with TF activity."
    d = collapsed().model_copy(
        update={
            "stated_hypotheses": [
                StatedHypothesis(
                    axis="multiple_hypotheses",
                    basis="run_sambar",
                    text_span="tumor subtypes",
                    target_artifact="sample_cluster_assignment",
                ),
                StatedHypothesis(
                    axis="multiple_hypotheses",
                    basis="run_giraffe",
                    text_span="TF activity",
                    target_artifact="tf_activity_matrix",
                ),
            ]
        }
    )
    text = render_hypothesis_routes(d, POLICY, task=task)
    assert "GIRAFFE" in text
    assert "Clustering the samples on that matrix" not in text


def test_unsupported_hypothesis_is_not_relabelled_as_a_related_tool():
    from netzoo_agent_core.contracts.outcomes import StatedHypothesis

    d = collapsed().model_copy(
        update={
            "stated_hypotheses": [
                StatedHypothesis(
                    axis="multiple_hypotheses",
                    basis="unsupported",
                    text_span="Bayesian TF prior uncertainty",
                    target_artifact="regulatory_network",
                ),
                StatedHypothesis(
                    axis="multiple_hypotheses",
                    basis="run_bonobo",
                    text_span="Bayesian coexpression",
                    target_artifact="coexpression_network",
                ),
            ]
        }
    )
    text = render_hypothesis_routes(
        d,
        POLICY,
        task="Compare Bayesian TF prior uncertainty with Bayesian coexpression.",
    )
    assert "no registered workflow" in text.lower() and "BONOBO" in text
    assert "PANDA" not in text


def test_invalid_third_hypothesis_cannot_be_silently_dropped():
    supplied = claims([*PAIRS, ("run_cobra", "a fabricated third hypothesis")])
    accepted, rejected = hypotheses_from_claims(
        ZH, supplied, hypothesis_options(collapsed(), ZH)
    )
    assert not accepted and rejected[-1]["reason"] == "quote_not_in_request"


def test_missing_comparison_provider_cannot_select_one_workflow(monkeypatch):
    from netzoo_agent_core.graph import router_invocation

    ctx = _context(claims().model_dump())
    ctx.selection_condition_llm = None

    def unexpected(*args, **kwargs):
        pytest.fail(
            "Unavailable comparison provider must not collapse explicit alternatives"
        )

    monkeypatch.setattr(router_invocation, "_invoke_semantic_interpreter", unexpected)
    result = router_invocation.invoke_router(ctx, {}, ZH)
    assert result.reason_code == "research_choices_unavailable"
    assert result.decision.action == "no_tool" and not result.decision.matched_actions
