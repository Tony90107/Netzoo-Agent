"""Log 309: a request that names no unit at all keeps no per-sample reading.

Test 1 of the ten-scenario doc (lung tissues, one aggregate TF network) was
read as one network per sample from the quote "across these tissues", in
English and Chinese alike, and LIONESS-PANDA was chosen outright 6/6. The
request names no sample, patient or other unit, so the per-sample scale and
tags are dropped before matching.
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    CapabilityMatch, OutcomeEvidence, OutcomeHypothesis, RequestedOutcome, SemanticInterpretation,
)
from netzoo_agent_core.graph.discriminator import _unstated_tags  # noqa: E402
from netzoo_agent_core.interpretation.request_integrity import granularity_mentions, per_unit_mention  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import match_semantic_request  # noqa: E402
from netzoo_agent_core.routing.scale_relaxation import drop_unnamed_scale, relax_unstated_scale  # noqa: E402

LUNG = ("We just finished RNA-seq on a batch of lung cancer tissues, and we also have standard transcription factor "
        "motif binding data and known protein-protein interaction data. We want to estimate how strongly each "
        "transcription factor regulates its target genes across these tissues, while also accounting for TFs that "
        "cooperate in complexes. What method should we use to build this network?")
LUNG_ZH = ("我們剛完成一批肺癌組織的轉錄組定序，手邊也有標準的轉錄因子結合基序資料和已知的蛋白質交互作用資料。"
           "我們想估計這批組織中每個轉錄因子對靶基因的整體調控強度，並希望同時考慮轉錄因子之間形成複合體的協同作用。"
           "請問該用什麼方法建構這樣的網路？")
HEART = ("We have microarray expression profiles from 40 heart failure patients with highly heterogeneous clinical "
         "presentations. A single population-level network would average away individual differences, but each "
         "patient contributed only one tissue biopsy, so a per-patient correlation cannot be computed. How can we "
         "reconstruct a separate regulatory network for each patient from this cohort?")


def _evidence(dimension, value, span):
    return OutcomeEvidence(dimension=dimension, value=value, source="explicit", text_span=span, rationale="Recorded.")


def _recorded_lung_reading():
    """The first-pass reading recorded for t1-en (docs/research-log/test12-2026-10-02)."""
    outcome = RequestedOutcome(
        operation="infer", input_artifacts=[], artifact_type="regulatory_network", entity_types=["tf", "gene"],
        display_entities=["transcription factors", "target genes"], regulator_types=["tf"], target_types=["gene"],
        selection_tags=["joint_grn_tfa_inference"], granularity="sample_specific",
    )
    evidence = [
        _evidence("operation", "infer", "estimate how strongly each transcription factor regulates its target genes"),
        _evidence("artifact_type", "regulatory_network", "build this network"),
        _evidence("granularity", "sample_specific", "across these tissues"),
        _evidence("entity_type", "gene", "target genes"),
        _evidence("target_type", "gene", "target genes"),
        _evidence("selection_tag", "joint_grn_tfa_inference",
                  "estimate how strongly each transcription factor regulates its target genes"),
        _evidence("regulator_type", "tf", "transcription factor regulates its target genes"),
    ]
    return SemanticInterpretation.model_construct(
        request_mode="guidance", semantic_goal="",
        outcome_hypotheses=[OutcomeHypothesis(outcome=outcome, confidence=0.9, evidence=evidence)],
    )


def test_test_1_names_no_unit_and_test_2_does():
    assert per_unit_mention(LUNG) is None and per_unit_mention(LUNG_ZH) is None
    assert per_unit_mention(HEART) is not None
    # "its own mRNA" is not a unit; "its own network" is.
    assert per_unit_mention("The TF's activity changes although its own mRNA barely changes.") is None
    assert per_unit_mention("Each sample should get its own regulatory network.") is not None


def test_every_stated_per_sample_scale_names_a_unit():
    # The loose unit witness covers every per-sample granularity pattern, so a
    # request whose scale is stated is never touched by the drop.
    prompts = set()
    for path in [*glob.glob(str(ROOT / "tests" / "*.json")),
                 *glob.glob(str(ROOT / "docs" / "research-log" / "**" / "*targeted*.json"), recursive=True),
                 *glob.glob(str(ROOT / "docs" / "research-log" / "blind" / "blind_*.json"))]:
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except ValueError:
            continue
        for item in data if isinstance(data, list) else []:
            if isinstance(item, dict) and isinstance(item.get("prompt"), str):
                prompts.add(item["prompt"])
    stated = [task for task in prompts
              if any(mention.granularity == "sample_specific" for mention in granularity_mentions(task))]
    assert len(stated) > 20
    assert [task for task in stated if per_unit_mention(task) is None] == []


def test_the_recorded_test_1_reading_becomes_a_tie_with_the_cohort_methods():
    reading = _recorded_lung_reading()
    assert match_semantic_request(LUNG, reading.outcome_hypotheses, request_mode="guidance").matched_actions \
        == ["run_lioness_panda"]
    dropped, changed = drop_unnamed_scale(LUNG, reading)
    assert changed == [{"granularity": "sample_specific", "selection_tags": []}]
    outcome = dropped.outcome_hypotheses[0].outcome
    assert outcome.granularity == "unknown"
    assert not any(item.dimension == "granularity" for item in dropped.outcome_hypotheses[0].evidence)
    match = match_semantic_request(LUNG, dropped.outcome_hypotheses, request_mode="guidance")
    assert match.status == "ambiguous" and not match.matched_actions
    assert set(match.hypothesis_actions) == {"run_panda", "run_lioness_panda", "run_otter", "run_giraffe"}
    # Several cohort methods remain, so the tie stands and asks about scale.
    assert relax_unstated_scale(LUNG, dropped, match, scale_dropped=True)[1] == match


def test_a_request_naming_a_unit_keeps_its_reading():
    reading = _recorded_lung_reading()
    assert drop_unnamed_scale(HEART, reading) == (reading, [])
    tagged = reading.model_copy(update={"outcome_hypotheses": [reading.outcome_hypotheses[0].model_copy(update={
        "outcome": reading.outcome_hypotheses[0].outcome.model_copy(update={
            "granularity": "unknown", "selection_tags": ["sample_specific", "message_passing"]}),
    })]})
    kept, changed = drop_unnamed_scale(LUNG, tagged)
    assert kept.outcome_hypotheses[0].outcome.selection_tags == ["message_passing"]
    assert changed == [{"granularity": "unknown", "selection_tags": ["sample_specific"]}]


def test_a_dropped_scale_tie_of_one_cohort_workflow_and_its_extension_ends_on_the_cohort_workflow():
    # Case 7 ("For the same individuals"): DD3's result is kept once the scale
    # is dropped before matching instead of after.
    task = "For the same individuals I have gene expression and methylation. Which sites and genes are directly associated?"
    outcome = RequestedOutcome(operation="infer", artifact_type="multi_omic_network", granularity="unknown")
    reading = SemanticInterpretation.model_construct(
        request_mode="guidance", semantic_goal="", outcome_hypotheses=[OutcomeHypothesis(outcome=outcome, confidence=0.9)])
    tie = CapabilityMatch(status="ambiguous", hypothesis_actions=["run_dragon", "run_lioness_dragon"])
    relaxed, match = relax_unstated_scale(task, reading, tie, scale_dropped=True)
    assert (match.status, match.matched_actions, match.match_basis) == ("fallback", ["run_dragon"], "assumed_outcome")
    assert relaxed.outcome_hypotheses[0].assumptions[-1] == (
        "No scale was stated; DRAGON gives one result for the whole cohort; "
        "LIONESS-DRAGON gives one result per sample.")
    # Only a scale this request's reading lost is folded; an unknown read by the model stays a question.
    assert relax_unstated_scale(task, reading, tie) == (reading, tie)


def test_the_discriminator_cannot_restore_a_dropped_per_sample_tag():
    quote = [_evidence("selection_tag", "sample_specific", "across these tissues")]
    assert _unstated_tags({"sample_specific"}, quote, LUNG) == {"sample_specific"}
    stated = [_evidence("selection_tag", "sample_specific", "reconstruct a separate regulatory network for each patient")]
    assert _unstated_tags({"sample_specific"}, stated, HEART) == set()
