"""Log 246: transcriptome and exome-mutation wordings are current-input witnesses.

"transcript expression" and 「轉錄表現量」 were not seen, so request_facts never
listed an expression matrix, and a repair was not allowed to add one: the
expression reading of a two-hypothesis request lost its only input (Log 245).
Only nouns were added; the clause rules still decide the temporal scope.
"""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.interpretation.request_integrity import input_mentions  # noqa: E402


def scoped(task):
    return {(m.artifact, m.status) for m in input_mentions(task)}


@pytest.mark.parametrize("task, artifact", [
    ("This time we have whole-exome somatic mutation profiles and transcript expression.",
     "expression_matrix"),
    ("I have transcriptome data for 80 tumours.", "expression_matrix"),
    ("Each patient has one blood expression profile.", "expression_matrix"),
    ("這次我們同時擁有『全外顯子DNA突變分佈』與『轉錄表現量』。", "expression_matrix"),
    ("這次我們同時擁有『全外顯子DNA突變分佈』與『轉錄表現量』。", "mutation_matrix"),
    ("我有腫瘤的 DNA 突變譜。", "mutation_matrix"),
])
def test_the_new_wordings_are_current_inputs(task, artifact):
    assert (artifact, "current") in scoped(task)


@pytest.mark.parametrize("task, artifact", [
    ("We previously had transcript expression for another cohort.", "expression_matrix"),
    ("之前那批病人曾經有轉錄表現量。", "expression_matrix"),
    ("上次的全外顯子DNA突變分佈已經跑完了。", "mutation_matrix"),
])
def test_history_still_scopes_the_new_wordings(task, artifact):
    statuses = {status for name, status in scoped(task) if name == artifact}
    assert statuses and "current" not in statuses


def test_a_bare_transcript_is_not_an_expression_matrix():
    assert not scoped("Which transcript isoform should I report?")
