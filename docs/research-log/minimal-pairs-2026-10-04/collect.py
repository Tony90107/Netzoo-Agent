"""Log 340: collect the minimal-pair sessions into one readable report and a summary table.

Usage (repository root): python3 docs/research-log/minimal-pairs-2026-10-04/collect.py <tag> <repeats>
Reads .netzoo/sessions/mp-<tag>-<id>-<rep>.json (decision, reply, token use) and
.netzoo/session_meta/mp-<tag>-<id>-<rep>.json (the card the user saw), and writes
out/<tag>-report.md, out/<tag>-summary.md and out/<tag>-decisions.json. Nothing calls a model.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from netzoo_agent_core.cli import terminal_cards  # noqa: E402

terminal_cards._width = lambda: 76
PROMPTS = json.loads((HERE / "prompts.json").read_text(encoding="utf-8"))

# Word scans over the reply; each is a rough pointer for the manual read, never a verdict.
SCANS = {
    "compare_step": r"\b(compar\w*|differen\w*|paired|pre-?\s?treatment|post-?\s?treatment|before and after|change)\b",
    "causal_limit": r"\b(caus\w*|association\w*|correlat\w* (?:is|does) not)\b",
    "predictor": r"\b(predict\w*|classif\w*)\b",
    "outside_netzoo": r"\b(not a NetZoo workflow|outside NetZoo|no registered workflow|run it separately)\b",
}


def load(tag, key, rep):
    name = f"mp-{tag}-{key}-{rep}"
    session_path = ROOT / ".netzoo" / "sessions" / f"{name}.json"
    if not session_path.exists():
        return None
    session = json.loads(session_path.read_text())
    meta_path = ROOT / ".netzoo" / "session_meta" / f"{name}.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    decision = (session.get("plan") or {}).get("decision") or {}
    reply = next((m.get("content") for m in reversed(session.get("messages", []))
                  if m.get("type") in ("ai", "AIMessage") or m.get("role") == "assistant"), "")
    usage = session.get("token_usage") or {}
    cost = sum((call.get("cost_micro_usd") or 0) for call in usage.get("calls", [])) / 1e6
    return {"decision": decision, "reply": str(reply or ""), "cards": meta.get("cards") or {},
            "calls": len(usage.get("calls", [])), "cost": cost}


def shape(decision):
    rec = decision.get("advisory_recommendation") or {}
    return (decision.get("capability_match_status"),
            tuple(sorted(decision.get("hypothesis_actions") or decision.get("matched_actions") or [])),
            rec.get("action"))


def main(tag, repeats):
    lines, summary, decisions = [f"# Minimal pairs `{tag}`", ""], [], {}
    summary += [f"# Minimal pairs `{tag}` summary", "",
                "| id | rep | status | candidates | recommended | card question; understood goal | " + " | ".join(SCANS) + " | calls | $ |",
                "|---|---|---|---|---|---|" + "---|" * len(SCANS) + "---|---|"]
    modal = {}
    total = 0.0
    for key, prompt in PROMPTS.items():
        lines += [f"## {key}", "", f"> {prompt}", ""]
        shapes = Counter()
        for rep in range(1, repeats + 1):
            run = load(tag, key, rep)
            if run is None:
                lines += [f"### {key} r{rep}: missing session", ""]
                continue
            total += run["cost"]
            decision = run["decision"]
            decisions[f"{key}-{rep}"] = {"prompt": prompt, "decision": decision}
            status, candidates, recommended = shape(decision)
            shapes[(status, candidates, recommended)] += 1
            questions = [str((card.get("choices") or {}).get("question") or "")[:60]
                         for card in run["cards"].values() if card.get("choices")]
            goals = [point for card in run["cards"].values() for point in card.get("points") or []
                     if point.startswith("Understood goal")]
            questions += [goal[:90] for goal in goals]
            flags = ["y" if re.search(pattern, run["reply"], re.I) else "" for pattern in SCANS.values()]
            summary.append(f"| {key} | {rep} | {status} | {', '.join(candidates)} | {recommended or ''} | "
                           f"{'; '.join(questions)} | " + " | ".join(flags) + f" | {run['calls']} | {run['cost']:.4f} |")
            lines += [f"### {key} r{rep}", "",
                      f"- status `{status}`, candidates {list(candidates)}, recommended {recommended}",
                      f"- reason `{decision.get('reason_code') or str(decision.get('reason', ''))[:80]}`; "
                      f"calls {run['calls']}, ${run['cost']:.4f}", ""]
            for card in run["cards"].values():
                shown = terminal_cards.render_card(card, color=False)
                if card.get("choices"):
                    shown += "\n" + "\n".join(terminal_cards.render_options(card, color=False))
                lines += ["Card:", "```", shown, "```", ""]
            lines += ["Full reply:", "", "```", run["reply"], "```", ""]
        modal[key] = shapes.most_common(1)[0] if shapes else None
    summary += ["", "## Modal shape per prompt", ""]
    for key, item in modal.items():
        summary.append(f"- {key}: {item[0] if item else None} ×{item[1] if item else 0}")
    summary += ["", f"Total cost ${total:.4f}"]
    (HERE / "out" / f"{tag}-report.md").write_text("\n".join(lines), encoding="utf-8")
    (HERE / "out" / f"{tag}-summary.md").write_text("\n".join(summary), encoding="utf-8")
    (HERE / "out" / f"{tag}-decisions.json").write_text(json.dumps(decisions, ensure_ascii=False, indent=1))
    print("wrote", HERE / "out" / f"{tag}-summary.md")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]))
