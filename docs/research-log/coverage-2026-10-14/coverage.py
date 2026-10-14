"""Item 4 (2026-10-14): which gold requirements the recorded capability checks never read as a result, and where.

Usage (repository root): python docs/research-log/coverage-2026-10-14/coverage.py [out.json]

For every recorded single-turn session whose request is a held-out item with requirement-level gold (heldout11-19),
the last recorded check (after any re-read) is compared with the gold requirements: a requirement is read when a
result quote overlaps its words. A miss is placed by where its words sit:
- beyond: in a sentence after the twelfth (MAX_SENTENCES);
- remainder: in a sentence where another result was quoted, outside every result quote;
- context: inside a quote the check filed as context or a methods question;
- unread: in a sentence with no result quote.
Repeats of one item are counted per session; each item's misses are also listed once. No model is called.
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
WORKTREES = ROOT.parent / ".worktrees"
sys.path.insert(0, str(ROOT / "scripts"))

from netzoo_agent_core.contracts.capability_check import MAX_SENTENCES  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import _span, request_sentences  # noqa: E402

SETS = sorted((ROOT / "docs" / "research-log").rglob("heldout1[1-9].json"))


def gold_items():
    items = {}
    for path in SETS:
        for item in json.loads(path.read_text()).get("items", []):
            if isinstance(item, dict) and "requirements" in item and "prompt" in item:  # multi-turn items: not here
                items[" ".join(item["prompt"].split())] = {**item, "set": path.stem}
    return items


def last_check(events: Path):
    check = None
    for line in events.read_text().splitlines():
        if '"routing.capability_checked"' in line or '"routing.capability_reread"' in line:
            check = json.loads(line)["payload"].get("check") or check
    return check


def overlaps(a, b):
    return a is not None and b is not None and min(a[1], b[1]) > max(a[0], b[0])


def place(task, words, check):
    span = _span(task, words)
    if span is None:
        return "words_not_found"
    sentences = request_sentences(task)
    index = next((i for i, (s, e) in enumerate(sentences) if s <= span[0] < e), None)
    results = [_span(task, r["quote"]) for r in check["requirements"] if r["kind"] == "result"]
    if any(overlaps(span, r) for r in results):
        return "read"
    if index is not None and index >= MAX_SENTENCES:
        return "beyond"
    others = [_span(task, r["quote"]) for r in check["requirements"] if r["kind"] != "result"]
    if any(overlaps(span, o) for o in others):
        return "context"
    if index is not None and any(overlaps(sentences[index], r) for r in results):
        return "remainder"
    return "unread"


def main():
    gold = gold_items()
    counts, per_item = collections.Counter(), collections.defaultdict(collections.Counter)
    for session in sorted(WORKTREES.glob("*/.netzoo/sessions/*.json")):
        try:
            data = json.loads(session.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        users = [m["content"] for m in data.get("messages", []) if m.get("role") == "user"]
        if len(users) != 1 or not data.get("run_id"):
            continue
        item = gold.get(" ".join(users[0].split()))
        events = session.parents[1] / "traces" / str(data["run_id"]) / "events.jsonl"
        if item is None or not events.exists() or (check := last_check(events)) is None:
            continue
        counts["sessions"] += 1
        for requirement in item["requirements"]:
            where = place(users[0], requirement["words"], check)
            counts[(requirement["expect"], where)] += 1
            per_item[(item["set"], item["id"], requirement["words"], requirement["expect"])][where] += 1
    print("sessions:", counts.pop("sessions"))
    for expect in ("supported", "with_step", "needs_input", "not_supported"):
        row = {where: n for (e, where), n in counts.items() if e == expect}
        total = sum(row.values())
        print(f"{expect:14} n={total:4}  read={row.get('read', 0) / total:.0%}  " if total else expect,
              {k: v for k, v in sorted(row.items()) if k != "read"})
    missed = [(key, dict(where)) for key, where in per_item.items() if set(where) - {"read"}]
    print(f"\n{len(missed)} gold requirements missed at least once:")
    for (name, item_id, words, expect), where in sorted(missed):
        print(f"- {name} {item_id} [{expect}] {words!r}: {where}")
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(json.dumps([{"set": k[0], "id": k[1], "words": k[2], "expect": k[3], "where": w}
                                                 for k, w in missed], indent=1))


if __name__ == "__main__":
    main()
