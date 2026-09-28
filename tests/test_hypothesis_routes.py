"""Log 248: readings that would collapse into one workflow are answered one by one."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from evaluate_routing import ProjectPolicyLoader  # noqa: E402
from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.interpretation.hypothesis_routes import render_hypothesis_routes  # noqa: E402

ROOT = Path(__file__).parents[1]
POLICY = ProjectPolicyLoader(ROOT).load()

TASK = (
    "We have expression data from drug-resistant and sensitive cell lines. One hypothesis is "
    "that transcription factors rewire their target genes; the other is that microRNAs "
    "silence the genes. For each hypothesis, what workflow should we build?"
)


def evidence(dimension, value, span=None):
    return {"dimension": dimension, "value": value, "source": "explicit" if span else "inferred",
            "text_span": span, "rationale": "Scripted."}


def reading(artifact, inputs, regulators=(), granularity="sample_specific", quote=None, entities=None):
    items = [evidence("artifact_type", artifact, quote)] if quote else []
    return {
        "outcome": {"operation": "infer", "input_artifacts": list(inputs), "artifact_type": artifact,
                    "entity_types": entities or [*regulators, "gene"],
                    "regulator_types": list(regulators),
                    "target_types": ["gene"] if regulators else [], "granularity": granularity},
        "confidence": 0.8, "evidence": items,
    }


def decision(hypotheses, *, status="exact", matched=(), tied=(), action="no_tool"):
    return TaskDecision.model_validate({
        "action": action, "in_scope": True, "should_execute": False, "confidence": 0.9, "reason": "Scripted.",
        "capability_match_status": status, "matched_actions": list(matched),
        "hypothesis_actions": list(tied), "outcome_hypotheses": hypotheses,
    })


TF = reading("regulatory_network", ["expression_matrix"], ["tf"],
             quote="transcription factors rewire their target genes")
MIRNA = reading("regulatory_network", [], ["mirna"], quote="microRNAs silence the genes")


def test_readings_collapsed_into_one_workflow_get_one_section_each():
    text = render_hypothesis_routes(decision([TF, MIRNA], matched=["run_lioness_puma"]), POLICY, task=TASK)
    assert '**Reading 1 -- "transcription factors rewire their target genes"**' in text
    assert '**Reading 2 -- "microRNAs silence the genes"**' in text
    first, second = text.split("**Reading 2")
    assert "LIONESS-PANDA" in first and "Method premise:" in first and "Required inputs:" in first
    assert "LIONESS-PUMA" in second and "miRNA list" in second
    # A TF reading also fits PUMA's TF/miRNA network; the registry, not this
    # renderer, decides which workflows each reading lists.
    assert "Which reading should we start with: 1 (LIONESS-PANDA or LIONESS-PUMA), 2 (LIONESS-PUMA)?" in text
    assert text.endswith("No files were inspected and no analysis ran.")


def test_a_tie_that_already_lists_every_readings_workflows_is_unchanged():
    tied = decision([TF, MIRNA], status="ambiguous",
                    tied=["run_lioness_panda", "run_lioness_puma"])
    assert render_hypothesis_routes(tied, POLICY, task=TASK) is None


def test_a_reading_without_a_workflow_is_named_with_what_its_inputs_can_give():
    task = ("We have whole-exome somatic mutation data and an expression matrix. Subtype "
            "from 'accumulated DNA damage' or from 'rewiring of regulatory connections'?")
    mutation = reading("sample_cluster_assignment", ["mutation_matrix"], granularity="aggregate",
                       quote="accumulated DNA damage", entities=["sample"])
    expression = reading("sample_cluster_assignment", ["expression_matrix"], granularity="aggregate",
                         quote="rewiring of regulatory connections", entities=["sample"])
    text = render_hypothesis_routes(decision([mutation, expression], matched=["run_sambar"]),
                                    POLICY, task=task)
    first, second = text.split("**Reading 2")
    assert "SAMBAR" in first
    # Log 252: expression-based subtyping has a registered composition.
    assert "No registered workflow assigns samples to clusters from expression." in second
    assert "- **LIONESS-PANDA** gives a TF-by-sample out-degree matrix" in second
    assert "is not a NetZoo workflow; run it separately." in second
    assert "2 (a profile from LIONESS-PANDA / LIONESS-PUMA / GIRAFFE / BONOBO / " \
           "LIONESS-COEXPRESSION, then clustering outside NetZoo)" in text


def test_a_reading_without_a_workflow_or_composition_names_what_its_inputs_give():
    task = ("We have somatic mutation data and a measurement dataset. Subtype from "
            "'accumulated DNA damage' or from 'the measured features'?")
    mutation = reading("sample_cluster_assignment", ["mutation_matrix"], granularity="aggregate",
                       quote="accumulated DNA damage", entities=["sample"])
    measured = reading("sample_cluster_assignment", ["measurement_dataset"], granularity="aggregate",
                       quote="the measured features", entities=["sample"])
    text = render_hypothesis_routes(decision([mutation, measured], matched=["run_sambar"]),
                                    POLICY, task=task)
    second = text.split("**Reading 2")[1]
    assert "No registered workflow produces this result from these inputs." in second
    assert "**DRAGON**" in second  # accepts a measurement dataset
    assert "2 (no registered workflow)" in text


def test_one_reading_after_dropping_restated_inputs_and_input_gaps_is_not_rewritten():
    restated = reading("expression_matrix", ["expression_matrix"])
    gap = reading("regulatory_network", [], ["tf"])
    assert render_hypothesis_routes(decision([TF, restated, gap], matched=["run_lioness_panda"]),
                                    POLICY, task=TASK) is None


def test_a_users_own_words_in_any_language_are_quoted_back():
    task = "我們不確定是『轉錄因子改變目標基因』還是『微小RNA抑制基因』，這次有表現量資料。"
    tf = reading("regulatory_network", ["expression_matrix"], ["tf"], quote="轉錄因子改變目標基因")
    mirna = reading("regulatory_network", [], ["mirna"], quote="微小RNA抑制基因")
    text = render_hypothesis_routes(decision([tf, mirna], matched=["run_lioness_puma"]), POLICY, task=task)
    assert '"轉錄因子改變目標基因"' in text and '"微小RNA抑制基因"' in text


def test_a_quote_the_request_does_not_contain_is_never_shown():
    invented = reading("regulatory_network", [], ["mirna"], quote="miRNA sponges")
    text = render_hypothesis_routes(decision([TF, invented], matched=["run_lioness_puma"]), POLICY, task=TASK)
    assert "miRNA sponges" not in text
    assert "**Reading 2 -- sample-specific regulatory networks**" in text


def test_an_execution_turn_is_never_rewritten():
    assert render_hypothesis_routes(
        decision([TF, MIRNA], matched=["run_lioness_puma"], action="run_lioness_puma"),
        POLICY, task=TASK,
    ) is None


# Log 250: one reading whose inputs no workflow takes together is split by input.
SUBTYPE_TASK = ("This time we have whole-exome somatic mutation profiles and transcript expression. "
                "How should we subtype tumours?")


def subtype_reading(inputs):
    item = reading("sample_cluster_assignment", inputs, granularity="aggregate", entities=["sample"])
    item["outcome"]["operation"] = "analyze"
    item["evidence"] = [evidence("input_artifact", "mutation_matrix", "whole-exome somatic mutation"),
                        evidence("input_artifact", "expression_matrix", "transcript expression")]
    item["evidence"] = [e for e in item["evidence"] if e["value"] in inputs]
    return item


def test_inputs_no_workflow_takes_together_are_listed_one_by_one():
    both = subtype_reading(["expression_matrix", "mutation_matrix"])
    text = render_hypothesis_routes(decision([both], status="unsupported"), POLICY, task=SUBTYPE_TASK)
    assert text.startswith("No single registered workflow produces this result from all the stated inputs")
    mutation, expression = text.split("- From the expression matrix:")
    assert "- From the mutation matrix:" in mutation and "SAMBAR" in mutation
    assert "No registered workflow assigns samples to clusters from expression." in expression
    assert "- **GIRAFFE** gives its TF-by-sample activity matrix" in expression
    assert "the mutation matrix (SAMBAR), the expression matrix (a profile from LIONESS-PANDA" in text


def test_one_reading_that_only_a_composition_reaches_is_answered_with_it():
    only = subtype_reading(["expression_matrix"])
    text = render_hypothesis_routes(decision([only], status="ambiguous"), POLICY, task=SUBTYPE_TASK)
    assert text.startswith("Here is how registered workflows can reach this result")
    for workflow in ("LIONESS-PANDA", "LIONESS-PUMA", "GIRAFFE", "BONOBO", "LIONESS-COEXPRESSION"):
        assert f"- **{workflow}** gives " in text
    assert text.count("  - Required inputs:") == 5
    assert "not statistically independent" in text
    assert "has to be tested against that outcome" in text
    assert ("Which per-sample profile should we start with: LIONESS-PANDA, LIONESS-PUMA, "
            "GIRAFFE, BONOBO or LIONESS-COEXPRESSION?") in text


def test_compositions_name_only_registered_workflows_and_are_never_capabilities():
    from workflow_registry import GUIDANCE_COMPOSITIONS, OUTPUT_CAPABILITIES
    from netzoo_agent_core.contracts.artifact_semantics import ARTIFACT_SEMANTICS
    for (artifact, source), composition in GUIDANCE_COMPOSITIONS.items():
        assert artifact in ARTIFACT_SEMANTICS and source in ARTIFACT_SEMANTICS
        # A composition exists only where no registered workflow reaches the result.
        assert not any(
            artifact in {*c.produced_artifacts, c.artifact_type} and source in c.input_artifacts
            and source not in c.incompatible_input_artifacts
            for c in OUTPUT_CAPABILITIES.values()
        )
        for action, _ in composition.sources:
            assert action in OUTPUT_CAPABILITIES
            assert source in OUTPUT_CAPABILITIES[action].input_artifacts


def test_a_reading_one_workflow_serves_is_not_split():
    only = subtype_reading(["mutation_matrix"])
    assert render_hypothesis_routes(decision([only], matched=["run_sambar"]), POLICY,
                                    task=SUBTYPE_TASK) is None


def test_a_split_that_finds_no_workflow_for_any_input_says_nothing_new():
    task = "We have an expression matrix and a measurement dataset. Cluster the patients."
    item = reading("sample_cluster_assignment", ["expression_matrix", "measurement_dataset"],
                   granularity="aggregate", entities=["sample"])
    item["outcome"]["operation"] = "analyze"
    assert render_hypothesis_routes(decision([item], status="unsupported"), POLICY, task=task) is None
