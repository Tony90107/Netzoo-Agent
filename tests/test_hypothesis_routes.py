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
    assert "No registered workflow produces this result from these inputs." in second
    assert "**LIONESS-PANDA**" in second  # accepts an expression matrix
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
