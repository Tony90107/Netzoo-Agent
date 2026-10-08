"""Log 385: collect each trap session into one report for labelling, plus structural counters.

Usage (any directory): python3 docs/research-log/capability-traps-2026-10-08/collect_traps.py <tag> <repeats>
Reads the arm's .netzoo/sessions/ct-<tag>-<id>-<rep>.json (decision, reply, calls) and
.netzoo/session_meta/ (the card the user saw). Writes live/<tag>-report.md (prompt, structural
fields, card, full reply per session; the family is NOT shown, so a labeller judges each reply
against its `core` alone) and live/<tag>-structure.json. Nothing calls a model.

A model-written reply is a session with a `response` call (as in Log 384's B1).
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARM = Path("/Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-trap-base")
sys.path.insert(0, str(ARM / "scripts"))
from netzoo_agent_core.cli import terminal_cards  # noqa: E402

terminal_cards._width = lambda: 76
ITEMS = {item["id"]: item for item in json.loads((HERE / "traps.json").read_text())["items"]}


def main(tag, repeats):
    lines, rows = [f"# Capability traps `{tag}`", ""], {}
    for key, item in ITEMS.items():
        for rep in range(1, repeats + 1):
            sid = f"ct-{tag}-{key}-{rep}"
            path = ARM / ".netzoo" / "sessions" / f"{sid}.json"
            if not path.exists():
                rows[sid] = {"missing": True}
                lines += [f"## {sid}", "", "MISSING SESSION", ""]
                continue
            session = json.loads(path.read_text())
            meta_path = ARM / ".netzoo" / "session_meta" / f"{sid}.json"
            meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
            decision = (session.get("plan") or {}).get("decision") or {}
            reply = next((m.get("content") for m in reversed(session.get("messages", []))
                          if m.get("type") in ("ai", "AIMessage") or m.get("role") == "assistant"), "")
            calls = (session.get("token_usage") or {}).get("calls", [])
            rec = decision.get("advisory_recommendation") or {}
            row = {
                "status": decision.get("capability_match_status"),
                "in_scope": decision.get("in_scope"),
                "intent": decision.get("intent_type"),
                "matched": decision.get("matched_actions"),
                "candidates": decision.get("hypothesis_actions"),
                "recommended": decision.get("recommended_actions"),
                "advised": rec.get("action"),
                "alternatives": decision.get("alternative_actions"),
                "artifact": (decision.get("requested_outcome") or {}).get("artifact_type"),
                "roles": [c.get("role") for c in calls],
                "model_written": any(c.get("role") == "response" for c in calls),
                "errors": [c.get("exception") for c in calls if c.get("exception")],
            }
            rows[sid] = row
            lines += [f"## {sid}", "", f"> {item['prompt']}", "",
                      f"- core: {item['core']}",
                      f"- status `{row['status']}`, in_scope {row['in_scope']}, artifact `{row['artifact']}`, "
                      f"matched {row['matched']}, candidates {row['candidates']}, recommended {row['recommended']}, "
                      f"advised {row['advised']}, model-written {row['model_written']}", ""]
            for card in (meta.get("cards") or {}).values():
                shown = terminal_cards.render_card(card, color=False)
                if card.get("choices"):
                    shown += "\n" + "\n".join(terminal_cards.render_options(card, color=False))
                lines += ["Card:", "```", shown, "```", ""]
            lines += ["Full reply:", "", "```", str(reply), "```", ""]
    (HERE / "live" / f"{tag}-report.md").write_text("\n".join(lines), encoding="utf-8")
    (HERE / "live" / f"{tag}-structure.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    print("wrote", HERE / "live" / f"{tag}-report.md")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]))
