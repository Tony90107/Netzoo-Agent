"""Closed-menu phase 1: shared plumbing for the offline reading rounds (gpt-4o-mini, reading calls only).

Each read is one `read_menu` call; nothing else of the agent runs. A round writes, per read: the provider's wire
payload, the `MenuReading` code built from it, what code dropped, the `decide_menu` decision, tokens and seconds.
"""
from __future__ import annotations

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LOGS = ROOT / "docs" / "research-log"
sys.path.insert(0, str(ROOT / "scripts"))
_WORKTREES = ROOT.parent if ROOT.parent.name == ".worktrees" else ROOT.parent / ".worktrees"
DOTENV = _WORKTREES.parent / "netzoo_agent" / ".env"  # the main checkout's; worktrees carry none
MODEL = "openai/gpt-4o-mini"
PRICE = {"input": 0.15, "output": 0.60}  # USD per million tokens, gpt-4o-mini


def load_env() -> None:
    from dotenv import dotenv_values
    for key, value in dotenv_values(DOTENV, interpolate=False).items():
        if value is not None:
            os.environ.setdefault(key, value)


def build_reader_llm(max_tokens: int = 8000):
    from netzoo_agent_core.llm import build_llm, validate_router_model
    load_env()
    return build_llm(validate_router_model(MODEL), 0.0, max_output_tokens=max_tokens, timeout_seconds=150)


def usage(raw) -> dict:
    from netzoo_agent_core.llm import extract_provider_usage
    found = extract_provider_usage(raw) if raw is not None else None
    if not found:
        return {"input_tokens": 0, "output_tokens": 0, "usd": 0.0}
    usd = (found["cost_micro_usd"] / 1e6 if found.get("cost_micro_usd") is not None else
           (found["input_tokens"] * PRICE["input"] + found["output_tokens"] * PRICE["output"]) / 1e6)
    return {"input_tokens": found["input_tokens"], "output_tokens": found["output_tokens"], "usd": round(usd, 6)}


def record(item: dict, read, decision, rep: int = 0) -> dict:
    return {
        "id": item["id"], "rep": rep, "class": item.get("class"), "status": read.reading.status,
        "error": read.error, "seconds": read.seconds, **usage(read.raw),
        "kind": decision.kind, "basis": decision.basis, "workflows": decision.workflows, "partial": decision.partial,
        "questions": [q.dimension for q in decision.questions], "settled": decision.settled,
        "reasons": [r for d in decision.declined for r in d.reasons],
        "dropped": read.report.dropped, "filled": read.report.filled,
        "reading": read.reading.model_dump(mode="json", exclude_defaults=True), "payload": read.payload,
    }


def read_many(jobs, *, workers: int = 6, focus: bool = False) -> list[dict]:
    """jobs: (item, rep) pairs. Each is read once with `read_menu` and decided; with `focus`, the focused re-read of
    the candidates follows and its merged reading is decided too (recorded under `focus`)."""
    from netzoo_agent_core.graph.menu_reading_call import read_focused, read_menu
    from netzoo_agent_core.interpretation.menu_decision import decide_menu
    llm = build_reader_llm()

    def one(job):
        item, rep = job
        read = read_menu(item["prompt"], llm)
        row = record(item, read, decide_menu(read.reading, item["prompt"]), rep)
        if focus:
            focused, candidates = read_focused(item["prompt"], read.reading, llm)
            row["focus"] = {"candidates": list(candidates), "ran": focused is not None}
            if focused is not None:
                sub = record(item, focused, decide_menu(focused.reading, item["prompt"]), rep)
                row["focus"].update({k: sub[k] for k in ("status", "error", "seconds", "input_tokens",
                                                          "output_tokens", "usd", "kind", "basis", "workflows",
                                                          "partial", "questions", "settled", "reasons", "dropped",
                                                          "filled", "reading", "payload")})
        return row

    started = time.time()
    with ThreadPoolExecutor(workers) as pool:
        rows = list(pool.map(one, jobs))
    spent = sum(row["usd"] + row.get("focus", {}).get("usd", 0) for row in rows)
    failed = sum(row["status"] == "failed" for row in rows)
    print(f"{len(rows)} reads in {time.time() - started:.0f}s, failed {failed}, US${spent:.3f}")
    return rows


def write(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")


def git_head() -> str:
    import subprocess
    return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"], capture_output=True,
                          text=True).stdout.strip()
