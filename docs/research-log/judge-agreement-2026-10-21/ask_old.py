"""ROUND-15: more reads of every recorded condition-check and second-opinion call with the text live sends (arm A of
ROUND-14's reask.py), so a two-read agreement rule can be simulated. Model calls: 185 per read.

Usage: python3 ask_old.py OUT.json
"""
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "usage-fields-2026-10-21"))
import reask  # noqa: E402


def main(out: str):
    reask._env()
    from netzoo_agent_core.graph.capability_check_call import _own_llm

    model = os.environ["OPENROUTER_CAPABILITY_MODEL"]
    llm = _own_llm(model, int(os.environ.get("OPENROUTER_CAPABILITY_MAX_TOKENS", "16000")))
    todo = [job for job in reask.jobs() if job["arm"] == "A"]
    with ThreadPoolExecutor(6) as pool:
        done = list(pool.map(lambda job: reask.ask_one(llm, job), todo))
    tokens = [sum(row.get("tokens", [0, 0])[i] for row in done) for i in (0, 1)]
    cost = tokens[0] * reask.PRICE["input"] + tokens[1] * reask.PRICE["output"]
    Path(out).write_text(json.dumps({"model": model, "tokens": tokens, "usd": round(cost, 4), "calls": done},
                                    indent=1, ensure_ascii=False))
    print(f"{out}: {sum(r['answers'] is not None for r in done)}/{len(done)} answered; US${cost:.4f}")


if __name__ == "__main__":
    main(sys.argv[1])
