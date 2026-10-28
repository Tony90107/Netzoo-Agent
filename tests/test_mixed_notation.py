"""mixed-notation-2026-10-28: digits beside a number word are never count candidates (j3 R35, R22); runs written
in one notation keep their values. The quotes are every side-by-side / context run of the recorded checks."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.interpretation.count_words import candidate_runs, side_by_side_values  # noqa: E402

MIXED = [("Layer one is 60 metabolites", 60), ("layer two is 90 proteins", 90),
         ("layer one being 300 proteins", 300), ("the full one has 1,500 transcripts and 600 proteins", 1500)]
SAME = [("I'm not sure whether the cohort has 10 or 15 tumors after the last exclusion round.", [10, 15]),
        ("two or four of the biopsies", [2, 4]), ("covers either 100 or 200 patients", [100, 200]),
        ("either two or three samples", [2, 3]), ("testing between two and five of them.", [2, 5]),
        ("subtypes with 2 to 4 clusters", [2, 4]), ("I want two to four subtypes.", [2, 4]),
        ("Group the tumors into 2 to 5 subtypes by pathway mutation scores.", [2, 5]),
        ("sampled at stages 2, 3 and 4", [2, 3, 4])]


@pytest.mark.parametrize("text,value", MIXED)
def test_a_label_beside_a_count_is_no_candidate(text, value):
    assert side_by_side_values(text, float(value)) == []
    assert candidate_runs(text) == []


@pytest.mark.parametrize("text,values", SAME)
def test_candidates_in_one_notation_are_kept(text, values):
    assert [found for found, _start, _end in candidate_runs(text)] == [[float(v) for v in values]]
    assert side_by_side_values(text, float(values[-1])) == [float(v) for v in values]
