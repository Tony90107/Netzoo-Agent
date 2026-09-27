"""Run the approved five-case Legacy stability sample with a hidden key prompt."""

from __future__ import annotations

import getpass
import os
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import evaluate_routing  # noqa: E402


CASE_IDS = (
    "gran-mirna-unstated-control",
    "gran-tf-ss-individual-en",
    "role-mirna-ss-en",
    "role-tf-agg-control-en",
    "zh-compare-patients-ss",
)
TRACE_PATH = (
    PROJECT_ROOT
    / "docs/research-log/live-semantic-stability-2026-09-25-legacy-5case-3repeat.json"
)


def main() -> int:
    prompted_for_key = not bool(os.environ.get("OPENROUTER_API_KEY"))
    if prompted_for_key:
        if not sys.stdin.isatty():
            print("Run this script from an interactive terminal to enter the API key securely.")
            return 2
        try:
            api_key = getpass.getpass("OpenRouter API key (input hidden): ")
        except (EOFError, KeyboardInterrupt):
            print("No API key entered; no provider calls were made.")
            return 2
        if not api_key:
            print("No API key entered; no provider calls were made.")
            return 2
        os.environ["OPENROUTER_API_KEY"] = api_key

    args = [
        "--scenarios", str(PROJECT_ROOT / "tests/routing_semantic_families.json"),
        "--semantic-contract", "legacy",
        "--review-policy", "when_needed",
        "--model", "openai/gpt-4o-mini",
        "--repeat", "3",
        "--max-calls", str(evaluate_routing.worst_case_calls(len(CASE_IDS), 3)),
        "--timeout", "60",
        "--trace-out", str(TRACE_PATH),
        "--json",
        "--live",
    ]
    for case_id in CASE_IDS:
        args.extend(("--case", case_id))

    try:
        return evaluate_routing.main(args)
    finally:
        if prompted_for_key:
            os.environ.pop("OPENROUTER_API_KEY", None)


if __name__ == "__main__":
    raise SystemExit(main())
