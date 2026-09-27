"""Log 202: a community assignment of a regulator-gene network holds both sides.

Chinese Case 9 ("一群調控因子是一起管一群基因的") was read as analyze
community_assignment with entities [tf, gene]. CONDOR declares `gene` only, so
the reading had no candidate at all. The communities partition the analyzed
network's nodes -- its regulators and its genes -- so matching supports both;
CONDOR's declaration is unchanged, which keeps the specificity ranking intact.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from netzoo_agent_core.contracts.outcomes import OutcomeHypothesis, RequestedOutcome  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import match_outcome_hypotheses  # noqa: E402
from workflow_registry import OUTPUT_CAPABILITIES  # noqa: E402


def _match(**fields):
    outcome = RequestedOutcome(**{"operation": "analyze", "granularity": "aggregate", **fields})
    return match_outcome_hypotheses([OutcomeHypothesis(outcome=outcome, confidence=0.9)])


@pytest.mark.parametrize("entities", [["tf", "gene"], ["mirna", "gene"], ["tf"], ["gene"]])
def test_regulator_and_gene_communities_select_condor(entities):
    match = _match(artifact_type="community_assignment", entity_types=entities)

    assert (match.status, match.matched_actions) == ("exact", ["run_condor"])


def test_the_declaration_and_vague_readings_are_unchanged():
    assert OUTPUT_CAPABILITIES["run_condor"].entity_types == frozenset({"gene"})
    match = _match(artifact_type="unknown", entity_types=["gene"])

    assert "run_condor" in match.hypothesis_actions
