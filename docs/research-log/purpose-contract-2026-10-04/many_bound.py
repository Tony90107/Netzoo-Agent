"""Log 367 review (no model call): how many many-labelled heldout11 items the frozen many-samples cue can reach.

Usage (repository root, with m_frozen.patch applied): python3 docs/research-log/purpose-contract-2026-10-04/many_bound.py
A many-samples quote is kept only when a cue in its sentence overlaps it, so an item whose prompt has
no cue anywhere can never be verified, whatever the model quotes.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
from netzoo_agent_core.routing.study_purpose_verify import _MANY_SAMPLES  # noqa: E402

items = json.loads((HERE / "heldout11" / "heldout.json").read_text())["items"]
many = [item for item in items if item["samples_per_individual"] == "many"]
reach = [item["id"] for item in many if _MANY_SAMPLES.search(item["prompt"])]
print(f"many-labelled items {len(many)}; at most {len(reach)} can be verified {reach} = {len(reach) / len(many):.0%} (M1 gate 80%)")
for item in many:
    if item["id"] not in reach:
        print(f"  no cue: {item['id']}: {item['data_sentence']}")
one = [item["id"] for item in items if item["samples_per_individual"] == "one" and _MANY_SAMPLES.search(item["prompt"])]
print(f"one-labelled items with a cue anywhere: {one}")
