"""Log 320: collect each local TEST_PROMPTS session into one readable report.

Usage (repository root): python3 docs/research-log/test10-2026-10-03/collect.py <tag>
Reads .netzoo/sessions/t10-<tag>-<id>.json (decision, reply, token use) and
.netzoo/session_meta/t10-<tag>-<id>.json (the card the user saw), and writes
out/<tag>-report.md plus out/<tag>-decisions.json. Nothing calls a model.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from netzoo_agent_core.cli import terminal_cards  # noqa: E402

terminal_cards._width = lambda: 76
PROMPTS = json.loads((HERE / "prompts.json").read_text(encoding="utf-8"))


def main(tag):
    lines, decisions = [f"# TEST_PROMPTS local run `{tag}`", ""], {}
    for key, prompt in PROMPTS.items():
        session = json.loads((ROOT / ".netzoo" / "sessions" / f"t10-{tag}-{key}.json").read_text())
        meta = json.loads((ROOT / ".netzoo" / "session_meta" / f"t10-{tag}-{key}.json").read_text())
        decision = (session.get("plan") or {}).get("decision") or {}
        decisions[key] = {"prompt": prompt, "decision": decision}
        reply = next((m.get("content") for m in reversed(session.get("messages", []))
                      if m.get("type") in ("ai", "AIMessage") or m.get("role") == "assistant"), "")
        usage = session.get("token_usage") or {}
        cost = sum((call.get("cost_micro_usd") or 0) for call in usage.get("calls", [])) / 1e6
        rec = (decision.get("advisory_recommendation") or {})
        lines += [f"## {key}", "", f"> {prompt}", "",
                  f"- status `{decision.get('capability_match_status')}`, matched {decision.get('matched_actions')}, "
                  f"candidates {decision.get('hypothesis_actions')}, recommended {rec.get('action')} "
                  f"{[(c.get('axis'), c.get('value')) for c in rec.get('conditions', [])]}",
                  f"- reason `{decision.get('reason_code') or decision.get('reason', '')[:80]}`; "
                  f"calls {len(usage.get('calls', []))}, tokens {usage.get('total_tokens')}, ${cost:.4f}", ""]
        for card in (meta.get("cards") or {}).values():
            shown = terminal_cards.render_card(card, color=False)
            if card.get("choices"):
                shown += "\n" + "\n".join(terminal_cards.render_options(card, color=False))
            lines += ["Card:", "```", shown, "```", ""]
        lines += ["Full reply:", "", "```", str(reply), "```", ""]
    (HERE / "out" / f"{tag}-report.md").write_text("\n".join(lines), encoding="utf-8")
    (HERE / "out" / f"{tag}-decisions.json").write_text(json.dumps(decisions, ensure_ascii=False, indent=1))
    print("wrote", HERE / "out" / f"{tag}-report.md")


if __name__ == "__main__":
    main(sys.argv[1])
