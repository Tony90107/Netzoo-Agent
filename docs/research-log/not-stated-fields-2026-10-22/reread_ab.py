"""Reading-only A/B (no decision): the capability reading of a few items, with one checkout's prompt and schema, read
REPS times by gpt-4o-mini-2024-07-18 exactly as `request_capability_check` asks it; prints each ask's
group_membership and input_network. Run once per checkout (old base ba7d828d, new 557bd5b1).

Usage: python3 reread_ab.py SCRIPTS_DIR OUT.json
"""
import json
import sys
from pathlib import Path

SCRIPTS, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, SCRIPTS)
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from dotenv import load_dotenv  # noqa: E402

load_dotenv(HERE.parents[4] / "netzoo_agent/.env")
from run_live import LOGS, SETS  # noqa: E402
from netzoo_agent_core.graph.capability_check_call import _own_llm, build_capability_check_messages  # noqa: E402
from netzoo_agent_core.contracts.capability_check import proposal_model  # noqa: E402

PICK = {"h5": ["Q26", "Q13", "Q06"], "h2": ["J22", "J40"], "h4": ["M45"], "h1": ["H37"], "h3": ["L35"]}
REPS = 3
MODEL = "openai/gpt-4o-mini-2024-07-18"

llm = _own_llm(MODEL, 8000)
rows = []
for name, ids in PICK.items():
    found = {x["id"]: x for x in json.loads((LOGS / SETS[name]).read_text())["items"]}
    for item in ids:
        messages, count = build_capability_check_messages(found[item]["prompt"])
        schema = proposal_model(count)
        for rep in range(REPS):
            try:
                got = llm.with_structured_output(schema, method="function_calling", include_raw=True,
                                                 strict=True).invoke(messages)
                parsed = got.get("parsed")
                payload = parsed.model_dump() if parsed is not None else {}
                usage = (got.get("raw").usage_metadata or {}) if got.get("raw") is not None else {}
            except Exception as error:  # noqa: BLE001 -- recorded
                payload, usage = {"error": f"{type(error).__name__}: {error}"[:200]}, {}
            asks = [a for key, part in payload.items() if key[:1] == "s" and key[1:].isdigit()
                    for a in (part or {}).get("asks") or []]
            rows.append({"item": item, "rep": rep, "fields": [(a["group_membership"], a["input_network"],
                                                               a["quote"][:70]) for a in asks],
                         "error": payload.get("error"), "usage": usage})
            print(item, rep, [(f[0], f[1]) for f in rows[-1]["fields"]], rows[-1]["error"] or "", flush=True)
Path(OUT).write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n")
