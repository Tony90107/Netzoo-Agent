"""Reading-only check of how one checkout's capability reading types group_membership for "subtypes" requests
(h5 Q26, h2 J22, h4 M45), read REPS times by one model exactly as `request_capability_check` asks it. No decision.

Usage: python3 read_groups.py SCRIPTS_DIR MODEL OUT.json
"""
import json
import sys
from pathlib import Path

SCRIPTS, MODEL, OUT = sys.argv[1:4]
sys.path.insert(0, SCRIPTS)
HERE = Path(__file__).resolve().parent
LOGS = HERE.parent
from dotenv import load_dotenv  # noqa: E402

load_dotenv(HERE.parents[4] / "netzoo_agent/.env")
from netzoo_agent_core.graph.capability_check_call import _own_llm, build_capability_check_messages  # noqa: E402
from netzoo_agent_core.contracts.capability_check import proposal_model  # noqa: E402

ITEMS = {"Q26": "heldout-h5-2026-10-21/items.json", "J22": "closed-menu-options-first-2026-10-18/h2/items.json",
         "M45": "closed-menu-hybrid-2026-10-19/h4/items.json"}
REPS = 3

llm = _own_llm(MODEL, 8000)
rows = []
for item, path in ITEMS.items():
    prompt = next(x["prompt"] for x in json.loads((LOGS / path).read_text())["items"] if x["id"] == item)
    messages, count = build_capability_check_messages(prompt)
    schema = proposal_model(count)
    for rep in range(REPS):
        try:
            got = llm.with_structured_output(schema, method="function_calling", include_raw=True,
                                             strict=True).invoke(messages)
            parsed = got.get("parsed")
            payload = parsed.model_dump() if parsed is not None else {}
            error = None if parsed is not None else str(got.get("parsing_error"))[:200]
            usage = (got.get("raw").usage_metadata or {}) if got.get("raw") is not None else {}
        except Exception as exc:  # noqa: BLE001 -- recorded
            payload, error, usage = {}, f"{type(exc).__name__}: {exc}"[:200], {}
        groups = [a["group_membership"] for key, part in payload.items() if key[:1] == "s" and key[1:].isdigit()
                  for a in (part or {}).get("asks") or []]
        rows.append({"item": item, "rep": rep, "groups": groups, "error": error, "usage": usage})
        print(item, rep, groups, error or "", flush=True)
Path(OUT).write_text(json.dumps({"scripts": SCRIPTS, "model": MODEL, "rows": rows}, indent=1) + "\n")
