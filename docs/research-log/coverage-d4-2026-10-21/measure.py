"""ROUND-16 (literature review D4), offline and $0: how much of each request no typed field of the reading quotes, and
whether that goes with wrong calls.

For every recorded reading (harness.readings, 1,045; 757 with a gold call) the reading's quotes are sorted into
  typed     an ask, a methods question, or any field holding a value (counts, settings, method, conditions, goal,
            candidates, unknowns, ruled-out or only inputs) -- every `quote`/`*_quote` string and `about_methods` item
  context   `has` items: words filed as background, no value taken from them
and each request sentence (`request_sentences`) is typed (a typed quote touches it), context-only, or untouched. Each
stated number -- digits, or a number word as count_words reads them -- outside a file name is typed (inside a typed
quote), context-only or untouched. "After re-read" adds the recorded re-read's asks (Log 406). Calls are this
checkout's B2 calls (usage-fields-2026-10-21/harness-after.json); wrong calls are split permissive (gold DECLINE, ASK
or CLARIFY judged DO) and strict (gold DO judged otherwise).

Usage: python3 measure.py OUT.json
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "stability-round13-2026-10-21"))
import harness  # noqa: E402  (sets the import paths)


def _quotes(value, path=()):
    """(kind, quote) for every quote string in a reading payload: context for `has` items, typed otherwise."""
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, str) and (key == "quote" or key.endswith("_quote") or key == "text_span"):
                if item.strip():
                    yield ("context" if "has" in path else "typed"), item
            else:
                yield from _quotes(item, (*path, key))
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, str) and path and path[-1] in ("has", "about_methods"):
                if item.strip():
                    yield ("context" if path[-1] == "has" else "typed"), item
            else:
                yield from _quotes(item, path)


def _numbers(task: str) -> list[tuple[int, int, str]]:
    from netzoo_agent_core.interpretation.discovery import _UNLABELED_PATH_RE
    from netzoo_agent_core.workflow_conditions import _NUMBER, _WORDS

    files = [m.span(1) for m in _UNLABELED_PATH_RE.finditer(task)]
    found = [(m.start(), m.end(), m.group()) for m in _NUMBER.finditer(task) if re.search(r"\d", m.group())]
    words = re.compile(r"\b(" + "|".join(sorted(_WORDS, key=len, reverse=True)) + r")\b", re.I)
    found += [(m.start(), m.end(), m.group()) for m in words.finditer(task)]
    return [n for n in found if not any(a <= n[0] < b for a, b in files)]


def _state(span, typed, context) -> str:
    def touches(spans):
        return any(a < span[1] and span[0] < b for a, b in spans)
    return "typed" if touches(typed) else "context" if touches(context) else "untouched"


def measure_one(task, payload, reread):
    from netzoo_agent_core.interpretation.sentence_ownership import request_sentences
    from netzoo_agent_core.interpretation.request_spans import _span

    quotes = list(_quotes(payload))
    reread_quotes = [("typed", ask["quote"]) for name, sentence in ((reread or {}).get("reread") or {}).items()
                     if name[1:].isdigit() for ask in sentence.get("asks") or [] if ask.get("quote")]
    out = {}
    for stage, chosen in (("first", quotes), ("after_reread", quotes + reread_quotes)):
        typed = [s for kind, q in chosen if kind == "typed" and (s := _span(task, q))]
        context = [s for kind, q in chosen if kind == "context" and (s := _span(task, q))]
        sentences = [(s, e, _state((s, e), typed, context)) for s, e in request_sentences(task)
                     if re.search(r"\w", task[s:e])]
        numbers = [(s, e, text, _state((s, e), typed, context)) for s, e, text in _numbers(task)]
        out[stage] = {"sentences": [[s, e, state] for s, e, state in sentences],
                      "numbers": [[s, e, text, state] for s, e, text, state in numbers]}
    return out


def main(out: str):
    calls = json.loads((HERE.parent / "usage-fields-2026-10-21/harness-after.json").read_text())
    rows = []
    for key, folder, sid, task, payload, reread, found, _n in harness.readings():
        call = calls.get(key, {})
        rows.append({"key": key, "session": sid, "turn": folder.name, "gold": call.get("gold"),
                     "kind": call.get("kind"), "task": task, "reread": bool(reread and reread.get("reread")),
                     **measure_one(task, payload, reread)})
    Path(out).write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    report(rows)


def _wrong(row) -> str:
    if row["kind"] == row["gold"]:
        return "right"
    if row["kind"] == "DO":
        return "permissive"
    if row["gold"] == "DO":
        return "strict"
    return "other"


def report(rows):
    for stage in ("first", "after_reread"):
        sentences = Counter(state for r in rows for _s, _e, state in r[stage]["sentences"])
        numbers = Counter(state for r in rows for *_x, state in r[stage]["numbers"])
        print(f"== {stage}: sentences {dict(sentences)}; numbers {dict(numbers)}")
    labelled = [r for r in rows if r["gold"]]
    print(f"\n== {len(labelled)} labelled readings: calls by whether an untouched sentence / an untyped number is left")
    for stage in ("first", "after_reread"):
        for name, test in (
                ("untouched sentence", lambda r: any(st == "untouched" for *_x, st in r[stage]["sentences"])),
                ("number not typed", lambda r: any(st != "typed" for *_x, st in r[stage]["numbers"])),
                ("number untouched", lambda r: any(st == "untouched" for *_x, st in r[stage]["numbers"]))):
            for has in (True, False):
                group = [r for r in labelled if test(r) == has]
                outcome = Counter(_wrong(r) for r in group)
                wrong = len(group) - outcome["right"]
                print(f"  {stage:12} {name:18} {'yes' if has else 'no ':3} n={len(group):3} wrong {wrong:3} "
                      f"({wrong / max(1, len(group)):.0%}) {dict(outcome)}")


if __name__ == "__main__":
    main(sys.argv[1])
