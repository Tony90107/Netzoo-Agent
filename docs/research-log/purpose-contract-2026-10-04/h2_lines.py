"""Log 364, post hoc and report-only: H2 of Log 363 read line by line, not paragraph by paragraph.

Usage (repository root, with the (a'') commit e41b629 checked out):
  HELDOUT=heldout9/heldout.json python3 docs/research-log/purpose-contract-2026-10-04/h2_lines.py s9 3
Written after the declared check (`only_adds`) failed: it drops the "Start with" line and
normalises the tie lead, then compares whole replies. It does not replace the declared gate.
Writes live/<tag>-rec-diffs.txt (every reply (a'') changed, as a line diff) and
live/<tag>-decisions.json (the sessions, as archived for s7/s8). Nothing calls a model.
"""
import difflib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import analyze_live as A  # noqa: E402
from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.interpretation import study_purpose_notes  # noqa: E402

RECOMMEND = study_purpose_notes.recommended_actions
LEAD = re.compile(r"(?:These all fit; to choose,|Both fit; to choose,|These fit the result you described; for your question, "
                  r"start with .*?\. To choose otherwise,) tell me:")


def normalise(text):
    return LEAD.sub("<tie lead> tell me:", "\n".join(line for line in text.split("\n") if not line.startswith("Start with **")))


def main(tag, repeats):
    purposes = A.trace_purposes("cand")
    archive, diffs, equal, differ, changed = {}, [], 0, [], 0
    for item in A.ITEMS:
        for rep in range(1, repeats + 1):
            run = A.load(tag, "cand", item["id"], rep)
            if run is None:
                continue
            session = f"hp-{tag}-cand-{item['id']}-{rep}"
            traced = purposes.get(session)
            archive[f"cand-{item['id']}-{rep}"] = {"prompt": item["prompt"], "decision": run["decision"], "reply": run["reply"],
                                                   "calls": run["calls"], "cost": run["cost"], "study_purpose": str(traced)}
            decision = TaskDecision.model_validate(run["decision"])
            with_a, kind = A.render(item["prompt"], decision, True, traced)
            study_purpose_notes.recommended_actions = lambda *args, **kwargs: []
            without_a, _ = A.render(item["prompt"], decision, True, traced)
            study_purpose_notes.recommended_actions = RECOMMEND
            if kind == "response_model":
                continue
            if with_a != without_a:
                changed += 1
                diffs += [f"## {item['id']} r{rep} ({kind})", ""] + [
                    line for line in difflib.unified_diff(without_a.split("\n"), with_a.split("\n"), lineterm="", n=0)
                    if not line.startswith(("---", "+++"))] + [""]
            if normalise(with_a) == normalise(without_a):
                equal += 1
            else:
                differ.append(f"{item['id']}-{rep}")
    (HERE / "live" / f"{tag}-rec-diffs.txt").write_text("\n".join(diffs), encoding="utf-8")
    (HERE / "live" / f"{tag}-decisions.json").write_text(json.dumps(archive, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"line-level H2 (post hoc, report only): equal {equal}, differ {differ}; replies changed by (a'') {changed}")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]))
