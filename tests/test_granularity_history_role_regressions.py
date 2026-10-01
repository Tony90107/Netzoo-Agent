"""Regression pins for the 2026-09-23 traced live A/B (8 prompts x 3, gpt-4o-mini).

Each group is a failure class found in the raw traces, not in the summary:

* aggregate requests tied PUMA with LIONESS-PUMA although granularity was
  stated, so a correct first pass still ended in a granularity question;
* an inferred or paraphrased granularity quote hid a verbatim witness, so the
  semantic wrapper treated a stated dimension as unstated;
* Chinese negation (不需要) and bare nouns (整體, 單一樣本, 每個樣本) produced
  witnesses the request did not state;
* history/current and role/entity consistency, which the A/B could not isolate,
  are pinned here as matched pairs so a later change cannot move them silently.
"""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from workflow_registry import OUTPUT_CAPABILITIES  # noqa: E402
from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    OutcomeEvidence,
    OutcomeHypothesis,
    RequestedOutcome,
    SemanticInterpretation,
)
from netzoo_agent_core.interpretation.outcome_validation import (  # noqa: E402
    validate_outcome_hypotheses,
)
from netzoo_agent_core.interpretation.request_integrity import (  # noqa: E402
    granularity_mentions,
    input_mentions,
    request_integrity_issues,
)
from netzoo_agent_core.interpretation.stated_field_restoration import (  # noqa: E402
    restore_stated_fields,
)
from netzoo_agent_core.routing.outcome_matching import (  # noqa: E402
    match_requested_outcome,
    match_semantic_request,
)
from netzoo_agent_core.routing.requested_outcome_matching import (  # noqa: E402
    _without_superseded_successors,
)


def _evidence(dimension, value, span=None):
    return OutcomeEvidence(
        dimension=dimension,
        value=value,
        source="explicit" if span else "inferred",
        text_span=span,
        rationale="Recorded shape from the traced live round.",
    )


def _mirna_network(granularity, granularity_span=None, **extra):
    outcome = RequestedOutcome(
        operation="infer",
        artifact_type="regulatory_network",
        granularity=granularity,
        entity_types=["mirna", "gene"],
        regulator_types=["mirna"],
        target_types=["gene"],
        **extra,
    )
    return OutcomeHypothesis(
        outcome=outcome,
        confidence=0.9,
        evidence=[
            _evidence("operation", "infer"),
            _evidence("artifact_type", "regulatory_network", "regulatory network"),
            _evidence("granularity", granularity, granularity_span),
            _evidence("regulator_type", "mirna", "miRNA-to-gene"),
            _evidence("target_type", "gene", "miRNA-to-gene"),
        ],
    )


# --- aggregate vs sample-specific: terminal route, not pipeline ------------

COHORT_EN = (
    "Which method infers one miRNA-to-gene regulatory network shared across the "
    "whole cohort? I do not want a separate network per patient."
)
COHORT_ZH = "我只要整群病患共用的一張 miRNA 對基因調控網路，不需要每位病患各自的網路。請問適合哪個工具？"


@pytest.mark.parametrize("granularity,expected", [
    ("aggregate", "run_puma"),
    ("sample_specific", "run_lioness_puma"),
])
def test_stated_granularity_selects_one_mirna_route(granularity, expected):
    match = match_requested_outcome(_mirna_network(granularity).outcome)
    assert (match.status, match.matched_actions) == ("exact", [expected])


@pytest.mark.parametrize("span", [None, "shared across the whole cohort"])
def test_aggregate_guidance_is_exact_puma_whatever_the_granularity_support(span):
    """All six traced cohort trials: a correct first pass, then a granularity question."""
    match = match_semantic_request(
        COHORT_EN, [_mirna_network("aggregate", span)], request_mode="guidance",
    )
    assert (match.status, match.matched_actions) == ("exact", ["run_puma"])
    assert match.clarification_question is None


def test_pipeline_is_kept_when_its_first_stage_cannot_deliver_the_granularity():
    actions = ["run_puma", "run_lioness_puma"]
    assert _without_superseded_successors(
        actions, "sample_specific", OUTPUT_CAPABILITIES,
    ) == actions
    assert _without_superseded_successors(actions, "unknown", OUTPUT_CAPABILITIES) == actions
    assert _without_superseded_successors(
        actions, "aggregate", OUTPUT_CAPABILITIES,
    ) == ["run_puma"]


def test_aggregate_tf_request_stays_a_real_method_choice():
    """Removing LIONESS-PANDA must not certify PANDA over OTTER or GIRAFFE."""
    outcome = RequestedOutcome(
        operation="infer", artifact_type="regulatory_network",
        granularity="aggregate", entity_types=["tf", "gene"],
        regulator_types=["tf"], target_types=["gene"],
    )
    match = match_requested_outcome(outcome)
    assert match.status == "ambiguous"
    semantic = match_semantic_request(
        "I want one cohort-wide TF-to-gene regulatory network.",
        [OutcomeHypothesis(outcome=outcome, confidence=0.9, evidence=[
            _evidence("artifact_type", "regulatory_network", "regulatory network"),
            _evidence("granularity", "aggregate", "cohort-wide"),
            _evidence("regulator_type", "tf", "TF-to-gene"),
        ])],
        request_mode="guidance",
    )
    assert semantic.status == "ambiguous"
    assert "run_lioness_panda" not in semantic.hypothesis_actions
    assert {"run_panda", "run_otter", "run_giraffe"} <= set(semantic.hypothesis_actions)


# --- granularity witnesses: stated means stated ---------------------------

@pytest.mark.parametrize("prompt,expected", [
    (COHORT_EN, ["aggregate"]),
    (COHORT_ZH, ["aggregate"]),
    ("我想知道每位病患各自的微小核糖核酸對基因的調控關係，請推薦能為每位病患建立一張調控網路的方法，先不用執行。",
     ["sample_specific"]),
    ("Which registered method estimates a separate microRNA-to-gene regulatory network for each person?",
     ["sample_specific"]),
    ("The wiring between transcription factors and their target genes differs from one patient to the next.",
     ["sample_specific"]),
    ("Which workflow infers a miRNA-to-gene regulatory network? I have not decided between one cohort network and separate per-patient networks, so please ask me.",
     ["aggregate", "sample_specific"]),
    # Matched pair, one phrase apart.
    ("我要每位病患各自的 miRNA 對基因調控網路。", ["sample_specific"]),
    ("我要整群病患共用的一張 miRNA 對基因調控網路。", ["aggregate"]),
    # None of these states a network granularity.
    ("不需要每位病患各自的網路。", []),
    ("不同病患的整體突變負荷量差異很大。", []),
    ("Gene expression differs from one patient to the next.", []),
    ("LIONESS 在數學上是怎麼定義「單一樣本網路」的？", []),
    ("另一個是能反映每個樣本狀態的 (TF x n) 轉錄因子活性矩陣。", []),
    # Log 292: the individual/person forms of "-specific networks" (Log 291's
    # missed positive), still bound to a network noun.
    ("We need individual-specific networks connecting metabolite and gene-expression features "
     "for every subject in our cohort.", ["sample_specific"]),
    ("I want person-specific partial-correlation networks linking both layers.", ["sample_specific"]),
    ("I want one cohort network showing how individual genes link across both layers.", ["aggregate"]),
    ("The model has individual-specific random effects.", []),
    ("For the same individuals I have gene expression and methylation tables.", []),
])
def test_granularity_witness_reports_only_stated_network_granularity(prompt, expected):
    assert sorted({m.granularity for m in granularity_mentions(prompt)}) == expected


def _chinese_first_pass(granularity_evidence):
    """The legacy mirna-chinese first pass, as recorded, before restoration."""
    return SemanticInterpretation(
        request_mode="guidance",
        semantic_goal="Per-patient miRNA regulatory networks",
        outcome_hypotheses=[OutcomeHypothesis(
            outcome=RequestedOutcome(
                operation="infer", artifact_type="regulatory_network",
                granularity="sample_specific", regulator_types=["mirna"],
                target_types=["gene"],
            ),
            confidence=0.9,
            evidence=[
                _evidence("operation", "infer", "每位病患各自的微小核糖核酸對基因的調控關係"),
                _evidence("artifact_type", "regulatory_network", "建立一張調控網路"),
                granularity_evidence,
            ],
        )],
    )


@pytest.mark.parametrize("granularity_evidence", [
    _evidence("granularity", "sample_specific"),
    # The claims first pass: an explicit quote the request never contains.
    _evidence("granularity", "sample_specific", "每位病患的調控網路"),
])
def test_witness_upgrades_weak_granularity_support_to_a_verbatim_quote(granularity_evidence):
    task = "我想知道每位病患各自的微小核糖核酸對基因的調控關係，請推薦能為每位病患建立一張調控網路的方法，先不用執行。"
    restored, record = restore_stated_fields(
        task, _chinese_first_pass(granularity_evidence),
        restore_explicit_scalar_evidence=True,
    )
    hypothesis = restored.outcome_hypotheses[0]
    granularity = [e for e in hypothesis.evidence if e.dimension == "granularity"]
    assert [(e.source, e.text_span) for e in granularity] == [
        ("explicit", "每位病患建立一張調控網路"),
    ]
    assert any(item["field"] == "granularity_evidence" for item in record)
    assert validate_outcome_hypotheses(task, restored.outcome_hypotheses).valid
    match = match_semantic_request(task, restored.outcome_hypotheses, request_mode="guidance")
    assert (match.status, match.matched_actions) == ("exact", ["run_lioness_puma"])


def test_witness_never_rewrites_a_different_granularity_value():
    task = "我要整群病患共用的一張 miRNA 對基因調控網路。"
    source = _chinese_first_pass(_evidence("granularity", "sample_specific"))
    restored, _ = restore_stated_fields(task, source, restore_explicit_scalar_evidence=True)
    hypothesis = restored.outcome_hypotheses[0]
    assert hypothesis.outcome.granularity == "sample_specific"
    assert [e.source for e in hypothesis.evidence if e.dimension == "granularity"] == ["inferred"]


# --- history vs current inputs --------------------------------------------

@pytest.mark.parametrize("prompt,expected", [
    ("Previously I ran PANDA on an expression matrix. This time I want to subtype "
     "patients from somatic mutations.",
     {("expression_matrix", "historical"), ("mutation_matrix", "current")}),
    ("Last month I used somatic mutations for SAMBAR; this time I have an expression "
     "matrix and want a coexpression network.",
     {("mutation_matrix", "historical"), ("expression_matrix", "current")}),
    ("之前用表現量矩陣跑過 PANDA，這次我要用體細胞突變資料做病患分群。",
     {("expression_matrix", "historical"), ("mutation_matrix", "current")}),
    ("上次用體細胞突變做過分群，本次我有基因表現量矩陣，想建立共表現網路。",
     {("mutation_matrix", "historical"), ("expression_matrix", "current")}),
    # Controls: the same data is still in hand, so it must stay current.
    ("I previously ran PANDA. I still have the same expression matrix and now want "
     "per-patient networks.", {("expression_matrix", "current")}),
    ("If I obtain somatic mutations later, which tool would cluster patients? For now I "
     "only have an expression matrix.",
     {("mutation_matrix", "uncertain"), ("expression_matrix", "current")}),
    ("我沒有表現量矩陣，只有體細胞突變資料。",
     {("expression_matrix", "negated"), ("mutation_matrix", "current")}),
])
def test_input_scope_separates_history_from_current(prompt, expected):
    assert {(m.artifact, m.status) for m in input_mentions(prompt)} == expected


def test_reused_historical_input_is_not_flagged_as_noncurrent():
    task = "之前用表現量矩陣跑過 PANDA。現在手邊還是同一份表現量矩陣，想做每位病患各自的調控網路。"
    outcome = RequestedOutcome(
        operation="infer", artifact_type="regulatory_network",
        granularity="sample_specific", input_artifacts=["expression_matrix"],
    )
    assert not [str(i) for i in request_integrity_issues(task, outcome)
                if "input" in str(i)]


@pytest.mark.parametrize("task", [
    "Previously I ran PANDA on an expression matrix. This time I want to subtype "
    "patients from somatic mutations.",
    "之前用表現量矩陣跑過 PANDA，這次我要用體細胞突變資料做病患分群。",
])
def test_historical_input_in_the_outcome_is_an_issue_and_the_current_one_is_required(task):
    stale = RequestedOutcome(
        operation="analyze", artifact_type="sample_cluster_assignment",
        granularity="aggregate", entity_types=["sample"],
        input_artifacts=["expression_matrix"],
    )
    issues = {str(i) for i in request_integrity_issues(task, stale)}
    assert "noncurrent_input:expression_matrix" in issues
    assert "missing_current_input:mutation_matrix" in issues


def test_history_granularity_does_not_leak_into_the_current_goal():
    for task in (
        "Previously I built a per-patient network; this time I want one miRNA-to-gene "
        "regulatory network shared across the whole cohort.",
        "之前做過每位病患各自的調控網路，這次只要整群病患共用的一張 miRNA 對基因調控網路。",
    ):
        assert [m.granularity for m in granularity_mentions(task)] == ["aggregate"]


# --- role / entity consistency --------------------------------------------

def _roles(evidence, **outcome):
    body = {
        "operation": "infer", "input_artifacts": [],
        "artifact_type": "regulatory_network", "granularity": "sample_specific",
        **outcome,
    }
    return SemanticInterpretation.model_validate({
        "request_mode": "guidance", "semantic_goal": "Networks",
        "outcome_hypotheses": [{
            "outcome": body, "confidence": 0.9,
            "evidence": [
                {"dimension": d, "value": v, "source": "inferred", "rationale": "r"}
                for d, v in evidence
            ],
        }],
    })


NO_PHRASE = "Which method gives one regulatory network for each patient?"


@pytest.mark.parametrize("regulators,expected_entities", [
    (["mirna"], {"mirna", "gene"}),
    (["tf"], {"tf", "gene"}),
    (["tf", "mirna"], {"tf", "mirna", "gene"}),
])
def test_supported_roles_entail_their_entities(regulators, expected_entities):
    source = _roles(
        [("regulator_type", r) for r in regulators] + [("target_type", "gene")],
        regulator_types=regulators, target_types=["gene"], entity_types=[],
    )
    restored, _ = restore_stated_fields(NO_PHRASE, source)
    assert set(restored.outcome_hypotheses[0].outcome.entity_types) == expected_entities


def test_unknown_or_unsupported_roles_add_no_entity():
    unknown = _roles([], regulator_types=["unknown"], target_types=["unknown"], entity_types=[])
    unsupported = _roles([], regulator_types=["mirna"], target_types=["gene"], entity_types=[])
    for source in (unknown, unsupported):
        restored, _ = restore_stated_fields(NO_PHRASE, source)
        assert restored.outcome_hypotheses[0].outcome.entity_types == []


def test_role_phrase_replaces_unknown_role_without_duplicating_entities():
    task = "I want one TF-to-gene regulatory network for each patient."
    source = _roles(
        [], regulator_types=["unknown"], target_types=["gene"], entity_types=["tf", "gene"],
    )
    restored, _ = restore_stated_fields(task, source, restore_explicit_scalar_evidence=True)
    outcome = restored.outcome_hypotheses[0].outcome
    assert outcome.regulator_types == ["tf"]
    assert sorted(outcome.entity_types) == ["gene", "tf"]


@pytest.mark.parametrize("artifact,task,regulator,kept", [
    (
        "regulatory_network",
        "我想知道每位病患各自的微小核糖核酸對基因的調控關係，"
        "請推薦能為每位病患建立一張調控網路的方法，先不用執行。",
        "mirna",
        ["mirna", "gene"],
    ),
    # A TF-by-sample activity matrix really has sample rows; nothing is dropped.
    (
        "regulatory_network_and_tf_activity",
        "I want an aggregate TF-to-gene network and TF activity values across samples.",
        "tf",
        ["tf", "gene", "sample"],
    ),
])
def test_sample_entity_depends_on_the_selected_output_artifact(
    artifact, task, regulator, kept,
):
    """Per-sample network indexing is not a node; TF activity has sample rows."""
    source = _roles(
        [("regulator_type", regulator), ("target_type", "gene")],
        artifact_type=artifact, regulator_types=[regulator], target_types=["gene"],
        entity_types=[regulator, "gene", "sample"],
    )
    restored, _ = restore_stated_fields(task, source, restore_explicit_scalar_evidence=True)
    assert restored.outcome_hypotheses[0].outcome.entity_types == kept


@pytest.mark.parametrize("task,goal", [
    ("If I later obtain somatic mutation data I might cluster patients, but right now I "
     "have an expression matrix and want a separate TF-to-gene regulatory network for "
     "each sample. Which workflow? Advice only.", False),
    ("假如之後拿到突變資料，也許會把病患分群；但現在我只要每個樣本的調控網路。", False),
    # Controls: a stated current clustering goal is still recognised.
    ("Previously I ran PANDA on an expression matrix. This time I want to cluster "
     "patients into subtypes from somatic mutation data.", True),
    ("之前用基因表現量矩陣跑過 PANDA，這次我想用體細胞突變資料把病患分成亞型。", True),
])
def test_a_hypothetical_clustering_goal_is_not_the_current_goal(task, goal):
    from netzoo_agent_core.interpretation.request_integrity import patient_clustering_goal
    assert patient_clustering_goal(task) is goal


# --- F7: request-consistency rules found by the traced F6 round ------------



def _main_corpus_prompt(case_id):
    import json
    corpus = Path(__file__).parent / "routing_scenarios.json"
    return next(c["prompt"] for c in json.loads(corpus.read_text()) if c["id"] == case_id)


@pytest.mark.parametrize("task,artifact,fires", [
    ("cohort-wide miRNA-gene network, which tool?", "multi_omic_network", True),
    ("per-sample miRNA-gene networks, which tool?", "coexpression_network", True),
    # A stated regulatory role on a regulatory network is what it should be.
    ("cohort-wide miRNA-gene network, which tool?", "regulatory_network", False),
])
def test_stated_roles_cannot_be_carried_by_a_roleless_network(task, artifact, fires):
    outcome = RequestedOutcome(operation="infer", artifact_type=artifact, granularity="aggregate")
    codes = {str(i).split(":")[0] for i in request_integrity_issues(task, outcome)}
    assert ("stated_roles_conflict" in codes) is fires


def test_communities_of_a_regulatory_network_are_not_a_roles_conflict():
    """bipartite-communities says TF-to-gene and correctly asks for CONDOR's partition."""
    outcome = RequestedOutcome(
        operation="analyze", artifact_type="community_assignment", granularity="aggregate",
    )
    task = _main_corpus_prompt("bipartite-communities")
    assert not any(
        str(i).startswith("stated_roles_conflict") for i in request_integrity_issues(task, outcome)
    )


def test_a_two_layer_multi_omic_request_is_not_a_roles_conflict():
    outcome = RequestedOutcome(
        operation="infer", artifact_type="multi_omic_network", granularity="aggregate",
    )
    task = _main_corpus_prompt("two-layer-network")
    assert not any(
        str(i).startswith("stated_roles_conflict") for i in request_integrity_issues(task, outcome)
    )


OPEN_TASK = (
    "Which workflow infers a miRNA-to-gene regulatory network? I have not decided "
    "between one cohort network and separate per-patient networks, so please ask me."
)


@pytest.mark.parametrize("granularities,fires", [
    (["aggregate"], True),
    (["sample_specific", "sample_specific"], True),
    # Keeping the choice open is how the passing trials answered.
    (["unknown", "sample_specific"], False),
    (["aggregate", "sample_specific"], False),
    (["unknown"], False),
])
def test_an_open_granularity_may_not_be_decided_for_the_user(granularities, fires):
    hypotheses = [_mirna_network(g) for g in granularities]
    issues = validate_outcome_hypotheses(OPEN_TASK, hypotheses).issues
    assert any("undecided_granularity" in str(i) for i in issues) is fires


def test_a_stated_granularity_is_never_treated_as_open():
    assert not any(
        "undecided_granularity" in str(i)
        for i in validate_outcome_hypotheses(COHORT_EN, [_mirna_network("aggregate")]).issues
    )
    from netzoo_agent_core.interpretation.request_integrity import granularity_left_open
    assert granularity_left_open(_main_corpus_prompt("missing-granularity"))
    assert not granularity_left_open("I am not sure which tool to use for per-patient networks.")


@pytest.mark.parametrize("task,expected", [
    # Held out: none of these phrasings is in a routing corpus.
    ("a network describing miRNA regulation of genes in each tumor", ["mirna"]),
    ("transcription factor regulation of genes across the cohort", ["tf"]),
    ("gene regulation of metabolism", []),
    ("TF regulation of pathways", []),
    ("I do not want TF regulation of genes", []),
])
def test_noun_form_regulation_is_a_role_witness(task, expected):
    from netzoo_agent_core.interpretation.request_integrity import regulatory_role_mentions
    assert [m.regulator_type for m in regulatory_role_mentions(task)] == expected


@pytest.mark.parametrize("artifact,fires", [
    ("regulatory_network_and_tf_activity", True),   # no miRNA in its ontology
    ("signed_regulatory_effect_network", True),
    ("regulatory_network", False),
])
def test_a_stated_regulator_the_artifact_excludes_is_a_roles_conflict(artifact, fires):
    task = "我想要一張整群病患共用、同時包含轉錄因子與 miRNA 調控基因的網路，請推薦方法。"
    outcome = RequestedOutcome(operation="infer", artifact_type=artifact, granularity="aggregate")
    codes = {str(i).split(":")[0] for i in request_integrity_issues(task, outcome)}
    assert ("stated_roles_conflict" in codes) is fires


def test_a_stated_tf_role_fits_the_tf_activity_artifact():
    task = "I want TF-to-gene regulation plus TF activity for the cohort."
    outcome = RequestedOutcome(
        operation="infer", artifact_type="regulatory_network_and_tf_activity", granularity="aggregate",
    )
    assert not any(
        str(i).startswith("stated_roles_conflict") for i in request_integrity_issues(task, outcome)
    )
