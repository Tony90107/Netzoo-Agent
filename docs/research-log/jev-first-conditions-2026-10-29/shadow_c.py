"""jev-first-conditions phase B' (ROUND.md): arms M, H, HB, H+group_membership rebuilt with the pure-code check and
then the app's condition check (gpt-4o-mini, cached per exact pair list), scored as phases A/B.

Usage: python3 shadow_c.py run      (model calls cached in llm-cache.json; stops at the cost cap)
       python3 shadow_c.py score    (no calls; uncached pair lists leave their rows unchecked, as a failed call)
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
A, B = HERE.parent / "jev-first-links-2026-10-29", HERE.parent / "jev-first-fields-2026-10-29"
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
sys.path.insert(0, str(A))
sys.path.insert(0, str(B))

import shadow as phase_a  # noqa: E402
import shadow_b as phase_b  # noqa: E402

CACHE = HERE / "llm-cache.json"
CAP_USD = 1.00
ARMS = {"M": None, "H": (), "HB": phase_b.FIELDS, "H+group_membership": ("group_membership",)}
PRICE = {"in": 0.15e-6, "out": 0.60e-6}  # gpt-4o-mini per token (OpenRouter list price)
_LOCK = threading.Lock()


def _cache() -> dict:
    return json.loads(CACHE.read_text()) if CACHE.exists() else {}


def proposals():
    """(where, item, task, gold row, {arm: proposal dict}) per reading."""
    golds, (_options, ids) = phase_a.gold(), phase_a.menu()
    links, fields = phase_a._cache(), phase_b._cache()
    for folder, item, proposal in phase_a.readings(golds):
        task = golds[item]["prompt"]
        base = copy.deepcopy(proposal)
        for name, index, ask in phase_a.asks(proposal):
            found = links.get(phase_a._key(task, ask["quote"]))
            if found and "error" not in found and found["confidence"] >= phase_a.THRESHOLD:
                base[name]["asks"][index]["delivered_by"] = [ids[found["choice"]]] if found["choice"] in ids else []
        arms = {}
        for arm, chosen in ARMS.items():
            if chosen is None:
                arms[arm] = proposal
                continue
            built = copy.deepcopy(base)
            for name, index, ask in phase_a.asks(proposal):
                phase_b._with_fields(built[name]["asks"][index], fields.get(phase_b._key(task, ask["quote"])), chosen)
            arms[arm] = built
        yield folder, item, task, golds[item], arms


def _check(task, proposal_dict):
    from netzoo_agent_core.contracts.capability_check import proposal_model
    from netzoo_agent_core.interpretation.capability_check import build_capability_check

    count = sum(1 for name in proposal_dict if re.fullmatch(r"s\d+", name))
    model = proposal_model(count).model_validate(proposal_dict)
    return model, build_capability_check(task, model)[0]


def _pairs(task, model, check):
    from netzoo_agent_core.graph.router_invocation import _condition_shown
    from netzoo_agent_core.interpretation.capability_check import condition_pairs, stated_requirements

    pairs = condition_pairs(check, stated_requirements(task, model, check))
    own = condition_pairs(check, stated_requirements(task, model, check, own_sentence=True))
    return pairs, own, _condition_shown(check, pairs + own)


def _key(shown) -> str:
    return hashlib.sha256(json.dumps(shown).encode()).hexdigest()[:20]


def _ask_model(shown, llm):
    from langchain_core.messages import HumanMessage, SystemMessage
    from netzoo_agent_core.contracts.capability_check import condition_check_model
    from netzoo_agent_core.graph.capability_check_call import _CONDITION_CHECK

    schema = condition_check_model(len(shown))
    listed = "\n".join(f'{index}. Asked result: "{asked}" | Stated requirement: "{stated}" | {workflow} produces: '
                       f"{produced}" for index, (asked, stated, workflow, produced) in enumerate(shown, 1))
    adapter = llm.with_structured_output(schema, method="function_calling", include_raw=True, strict=True)
    out = adapter.invoke([SystemMessage(content=_CONDITION_CHECK), HumanMessage(content=listed)])
    parsed = out["parsed"]
    usage = getattr(out["raw"], "usage_metadata", None) or {}
    cost = usage.get("input_tokens", 0) * PRICE["in"] + usage.get("output_tokens", 0) * PRICE["out"]
    return [getattr(parsed, f"a{index}") for index in range(1, len(shown) + 1)], cost


def _answers(shown, cache):
    """The condition check's answers for one pair list: code first, the cached model answers for the rest."""
    from netzoo_agent_core.interpretation.expects import code_answer

    by_code = [code_answer(workflow, stated) for _asked, stated, workflow, _produced in shown]
    if all(by_code):
        return by_code
    asked = [pair for pair, answer in zip(shown, by_code) if answer is None]
    found = cache.get(_key(asked))
    if not found or "answers" not in found:
        return None
    model_answers = iter(found["answers"])
    return [answer or next(model_answers) for answer in by_code]


def run():
    from netzoo_agent_core.graph.capability_check_call import _own_llm
    from netzoo_agent_core.graph.required_check_budget import capability_max_tokens
    from netzoo_agent_core.interpretation.expects import code_answer

    model_name = os.environ.get("OPENROUTER_CAPABILITY_MODEL", "")
    if model_name != "openai/gpt-4o-mini-2024-07-18":
        raise RuntimeError(f"unexpected check model {model_name!r}")
    llm = _own_llm(model_name, capability_max_tokens(model_name))
    todo = {}
    for _folder, _item, task, _gold, arms in proposals():
        for proposal in arms.values():
            model, check = _check(task, proposal)
            _pairs_, _own, shown = _pairs(task, model, check)
            asked = [pair for pair in shown if code_answer(pair[2], pair[1]) is None]
            if asked:
                todo[_key(asked)] = asked
    cache = _cache()
    spent = [sum(found.get("cost", 0) for found in cache.values())]
    pending = [(key, asked) for key, asked in todo.items() if key not in cache or "answers" not in cache[key]]
    print(f"pair lists {len(todo)}, to ask {len(pending)}, spent US${spent[0]:.4f}")

    def one(job):
        key, asked = job
        with _LOCK:
            if spent[0] > CAP_USD:
                return
        try:
            answers, cost = _ask_model(asked, llm)
            found = {"answers": answers, "cost": cost}
        except Exception as error:  # noqa: BLE001 -- recorded; the rows stay unchecked, as a failed router call
            found = {"error": f"{type(error).__name__}: {error}"[:200], "cost": 0}
        with _LOCK:
            cache[key] = found
            spent[0] += found["cost"]
            CACHE.write_text(json.dumps(cache, indent=1))

    with ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(one, pending))
    print(f"done; cached {len(cache)}, spent US${spent[0]:.4f}, errors {sum('error' in v for v in cache.values())}")


def score():
    from netzoo_agent_core.capability_sheet import entry
    from netzoo_agent_core.graph.router_invocation import _not_checked
    from netzoo_agent_core.interpretation.capability_check import apply_condition_answers
    from netzoo_agent_core.interpretation.requirement_split import apply_own_sentence_answers

    cache, rows, unchecked = _cache(), [], 0
    for folder, item, task, want, arms in proposals():
        credited = {}
        for arm, proposal in arms.items():
            model, check = _check(task, proposal)
            pairs, own, shown = _pairs(task, model, check)
            if shown:
                answers = _answers(shown, cache)
                if answers is None:
                    check, unchecked = _not_checked(check, pairs + own), unchecked + 1
                else:
                    check = apply_condition_answers(check, pairs, answers[:len(pairs)])
                    check = apply_own_sentence_answers(check, own, answers[len(pairs):])
            credited[arm] = sorted({entry(key).workflow for row in check.results()
                                    if row.status in ("available", "with_step", "partial") for key in row.delivered_by})
        rows.append({"where": str(folder.relative_to(phase_a.LOGS)), "item": list(item), "gold": want["expected_call"],
                     "workflows": want["workflows"], "also": want.get("also_acceptable") or [], "credited": credited})
    (HERE / "shadow_c.json").write_text(json.dumps(rows, indent=1))
    report(rows, unchecked)


def report(rows, unchecked):
    right = lambda row, arm: bool(row["credited"][arm]) and set(row["credited"][arm]) <= (  # noqa: E731
        set(row["workflows"]) | set(row["also"]))
    do = [row for row in rows if row["gold"] == "DO"]
    decline = [row for row in rows if row["gold"] == "DECLINE"]
    lines = [f"readings {len(rows)}; gold DO {len(do)}, gold DECLINE {len(decline)}; arm checks left unchecked "
             f"(no cached answer) {unchecked}"]
    for arm in ARMS:
        up = sum(right(row, arm) and not right(row, "H") for row in do)
        down = sum(right(row, "H") and not right(row, arm) for row in do)
        lines.append(f"  {arm:20s} DO right {sum(right(row, arm) for row in do):3d} (vs H +{up} / -{down}); "
                     f"DECLINE false accepts {sum(bool(row['credited'][arm]) for row in decline)}")
    text = "\n".join(lines)
    (HERE / "SCORE.txt").write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    {"run": run, "score": score}[sys.argv[1]]()
