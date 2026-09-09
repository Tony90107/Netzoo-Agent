"""The harness could not write down the commonest request there is.

Every one of the first twenty-seven prompts asks which tool to use, so the
scorer simply required `guidance` of all of them and counted any authorized
action as a safety failure. That is not a property of routing; it is a property
of the corpus, and it meant "run this named tool on these files" could not be
expressed as a case at all -- so the class stayed untested while the gate stayed
green at 1550 tests (Log 123/124).

`request_mode` on the expectation makes the case writable. It defaults to
`guidance`, so the twenty-seven score exactly as they did; the tests below hold
that default shut, because an accidental change to it would silently rescore the
entire corpus and every number ever taken from it.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from evaluate_routing import load_scenarios  # noqa: E402

CORPUS_PATH = Path(__file__).parents[1] / "tests" / "routing_scenarios.json"
RAW = json.loads(CORPUS_PATH.read_text())
CASES = {case.id: case for case in load_scenarios(CORPUS_PATH)}

#: The only cases that ask for something to be run rather than recommended.
EXECUTE_CASES = {"run-named-panda-with-files", "run-two-named-tools"}


def test_a_case_that_does_not_say_otherwise_is_still_a_guidance_case():
    silent = [item["id"] for item in RAW if "request_mode" not in item["expected"]]

    assert silent, "the default is what keeps the existing corpus comparable"
    assert all(CASES[case_id].expected.request_mode == "guidance" for case_id in silent)


def test_exactly_the_named_run_cases_ask_for_execution():
    declared = {
        case_id for case_id, case in CASES.items()
        if case.expected.request_mode == "execute"
    }

    assert declared == EXECUTE_CASES


def test_the_class_that_was_missing_is_now_in_the_corpus():
    """Six of twenty-seven prompts named a tool and all six named it as history.

    The three added cases are the three ways naming a tool can end: it is the
    request, it is finished work, or there are two of them and the request is a
    question.
    """
    assert CASES["run-named-panda-with-files"].expected.actions == ["run_panda"]
    assert CASES["run-named-tool-finished-then-new-goal"].expected.forbidden_actions == [
        "run_panda"
    ]
    assert CASES["run-two-named-tools"].expected.require_clarification
    assert CASES["run-two-named-tools"].expected.actions == []
