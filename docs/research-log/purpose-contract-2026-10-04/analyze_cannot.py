"""Log 365 gates: "cannot" cells (one result for all the samples, asked about individuals).

Usage (repository root):
  live round:  HELDOUT=heldout10/heldout.json python3 docs/research-log/purpose-contract-2026-10-04/analyze_cannot.py live <tag> <repeats>
  seen data:   python3 docs/research-log/purpose-contract-2026-10-04/analyze_cannot.py seen
For each candidate session: the decision and reply it saved and the study purpose
its trace recorded; the reply re-rendered offline with the Log 365 cells and
without them (the cells Log 365 adds removed from CLAIM_SUPPORT), and the card.
`seen` replays the archived s7/s8/s9 candidate decisions instead (design data,
already read). Writes live/<tag>-cannot-analysis.txt. Nothing calls a model.
"""
import ast
import glob
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import analyze_live as A  # noqa: E402
from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.interpretation import study_purpose_notes  # noqa: E402
from netzoo_agent_core.routing.study_purpose import StudyPurpose  # noqa: E402
from workflow_registry import ACTION_DEFINITIONS, CLAIM_SUPPORT  # noqa: E402

# The cells Log 365 adds: every "cannot" cell, and the restored multi-omic cells.
ADDED = {key for key, cell in CLAIM_SUPPORT.items()
         if cell.level == "cannot" or key[0] in {"run_dragon", "run_lioness_dragon"}}
WITHOUT = {key: cell for key, cell in CLAIM_SUPPORT.items() if key not in ADDED}
TIE_LEAD = re.compile(r"^(?:These all fit; to choose,|Both fit; to choose,|These fit the result you described, "
                      r"but (?!none can ).*? cannot show .*?; to choose,) tell me:")
ADDED_LINE = re.compile(r'^(?:|For your question \(".*|- \*\*.*|Note: .*)$')


def name(action):
    return ACTION_DEFINITIONS[action].workflow


def lines_only_add(base, cand):
    """Declared H2 (Log 365): every line of `base` is in `cand`, in order, unchanged except a tie lead
    rewritten as declared; every other line of `cand` is a purpose-paragraph line (its header, a
    workflow line, a Note line) or blank. Returns (ok, reason)."""
    base_lines = [TIE_LEAD.sub("<tie lead> tell me:", line) for line in base.split("\n")]
    cand_lines = [TIE_LEAD.sub("<tie lead> tell me:", line) for line in cand.split("\n")]
    position = 0
    for line in base_lines:
        while position < len(cand_lines) and cand_lines[position] != line:
            if not ADDED_LINE.match(cand_lines[position]):
                return False, f"undeclared added line: {cand_lines[position][:120]!r}"
            position += 1
        if position == len(cand_lines):
            return False, f"base line missing or changed: {line[:120]!r}"
        position += 1
    extra = [line for line in cand_lines[position:] if not ADDED_LINE.match(line)]
    return (not extra), (f"undeclared added line: {extra[0][:120]!r}" if extra else "")


def render_pair(task, decision, traced):
    with_c, kind = A.render(task, decision, True, traced)
    study_purpose_notes.CLAIM_SUPPORT = WITHOUT
    try:
        without_c, _ = A.render(task, decision, True, traced)
    finally:
        study_purpose_notes.CLAIM_SUPPORT = CLAIM_SUPPORT
    return with_c, without_c, kind


def purpose_of(traced):
    return (StudyPurpose(traced.get("design"), traced.get("design_quote") or "",
                         tuple(tuple(claim) for claim in traced.get("claims") or ())) if traced else StudyPurpose())


def score(trials, out_name):
    """trials: dicts with key, item, decision, traced, reply (None for seen data), roles."""
    counts, c1_bad, c3_bad, c2_bad, h2_fail, lines, mentioned_bad = Counter(), [], [], [], [], [], []
    for trial in trials:
        item, decision, traced = trial["item"], trial["decision"], trial["traced"]
        with_c, without_c, kind = render_pair(item["prompt"], decision, traced)
        cannot = study_purpose_notes.cannot_cells(decision, purpose_of(traced))
        shown = [action for action, _ in cannot] if re.search(r"\b(?:does|do) not answer this:", with_c or "") else []
        acceptable = set(item["acceptable_candidates"])
        counts["trials"] += 1
        if kind == "response_model":
            counts["response_model"] += 1
            continue
        if trial["reply"] is not None and with_c != trial["reply"]:
            h2_fail.append(f"{trial['key']}: live reply differs from its offline render ({kind})")
        else:
            ok, reason = lines_only_add(without_c, with_c)
            counts["h2_ok"] += ok
            counts["h2_changed"] += ok and with_c != without_c
            if not ok:
                h2_fail.append(f"{trial['key']}: {reason} ({kind})")
        if not shown:
            counts["cells_not_shown"] += bool(cannot)  # e.g. a reply kind the purpose layer leaves alone
            continue
        counts["noted_trials"] += 1
        flagged = {name(action) for action in shown}
        instead = {name(action) for _, cell in cannot for action in cell.instead}
        # The card steers to the per-sample workflows only when no listed workflow answers.
        steered = len(cannot) == len(study_purpose_notes.claim_cells(decision, purpose_of(traced)))
        counts["steered_trials"] += steered
        if flagged & acceptable:
            c1_bad.append(f"{trial['key']}: flagged {sorted(flagged & acceptable)} is acceptable {sorted(acceptable)}")
        if not instead <= acceptable:
            (c3_bad if steered else mentioned_bad).append(
                f"{trial['key']}: instead {sorted(instead - acceptable)} not in {sorted(acceptable)}")
        if item.get("is_control") or item["claim_kind"] == "none":
            c2_bad.append(f"{trial['key']} ({item['claim_kind']})")
        lines.append(f"- {trial['key']}: [{item['comparison_design']}/{item['claim_kind']}] {kind} "
                     f"candidates {[name(a) for a in dict.fromkeys(decision.hypothesis_actions or decision.matched_actions)]} "
                     f"| cannot {sorted(flagged)} | instead {sorted(instead)}{' (next steps)' if steered else ''} "
                     f"| acceptable {sorted(acceptable)}")
    noted = counts["noted_trials"]
    summary = [
        f"trials {counts['trials']}, response_model {counts['response_model']}, noted {noted}, "
        f"cannot cells not shown {counts['cells_not_shown']}",
        f"C1 flagged workflow outside acceptable: {noted - len(c1_bad)}/{noted}; failures {c1_bad}",
        f"C2 notes on controls / claim none (gate 0): {c2_bad}",
        f"C3 per-sample next steps (no listed workflow answers) within acceptable: "
        f"{counts['steered_trials'] - len(c3_bad)}/{counts['steered_trials']}; failures {c3_bad}",
        f"report: per-sample workflows named beside others that answer, outside acceptable: "
        f"{len(mentioned_bad)}/{noted - counts['steered_trials']} {mentioned_bad}",
        f"H2 lines_only_add: ok {counts['h2_ok']} (changed {counts['h2_changed']}); failures {h2_fail}",
    ]
    (HERE / "live" / out_name).write_text("\n".join(summary + [""] + lines) + "\n", encoding="utf-8")
    print("\n".join(summary))


def seen():
    trials = []
    for tag, heldout in (("s7", "heldout7"), ("s8", "heldout8"), ("s9", "heldout9")):
        items = {item["id"]: item for item in json.loads((HERE / heldout / "heldout.json").read_text())["items"]}
        for key, value in json.loads((HERE / "live" / f"{tag}-decisions.json").read_text()).items():
            if not key.startswith("cand-"):
                continue
            traced = value.get("study_purpose")
            traced = ast.literal_eval(traced) if isinstance(traced, str) else traced
            trials.append({"key": f"{tag}-{key[5:]}", "item": items[key[5:].rsplit("-", 1)[0]],
                           "decision": TaskDecision.model_validate(value["decision"]), "traced": traced, "reply": None})
    score(trials, "seen-cannot-analysis.txt")


def live(tag, repeats):
    purposes = A.trace_purposes("cand")
    roles_before = set()
    for old in ("s7", "s8", "s9"):
        for path in glob.glob(str(A.ROOT / ".netzoo" / "sessions" / f"hp-{old}-cand-*.json")):
            roles_before |= {call["role"] for call in (json.loads(Path(path).read_text()).get("token_usage") or {}).get("calls", [])}
    trials, missing, new_roles = [], 0, set()
    for item in A.ITEMS:
        for rep in range(1, repeats + 1):
            run = A.load(tag, "cand", item["id"], rep)
            if run is None:
                missing += 1
                continue
            new_roles |= run["roles"] - roles_before
            trials.append({"key": f"{item['id']}-{rep}", "item": item, "reply": run["reply"],
                           "decision": TaskDecision.model_validate(run["decision"]),
                           "traced": purposes.get(f"hp-{tag}-cand-{item['id']}-{rep}")})
    print(f"missing {missing}; H3 roles beyond s7-s9 candidate arms (gate none): {sorted(new_roles)}")
    score(trials, f"{tag}-cannot-analysis.txt")


def selftest():
    """Log 364's lesson: check the measuring function on the declared output shapes before freezing."""
    base = ("Several fit:\n\nFor your question (\"q\"):\n- **A** — gives it.\nNote: n.\n\n"
            "These all fit; to choose, tell me: (1) x?\n\nNo files were inspected.")
    line = "- **B** — does not answer this: it gives one network from all the samples, so ..."
    cases = {
        "a cannot line inside the paragraph": (base.replace("gives it.\n", f"gives it.\n{line}\n"), True),
        "a new paragraph first": (f"For your question (\"q\"):\n{line}\n\n{base}", True),
        "the declared tie lead": (base.replace("These all fit; to choose,",
                                               "These fit the result you described, but **B** cannot show which "
                                               "individuals change or stand out; to choose,"), True),
        "unchanged": (base, True),
        "a changed word": (base.replace("gives it.", "gives that."), False),
        "a removed line": (base.replace("Note: n.\n", ""), False),
        "reordered lines": (base.replace("- **A** — gives it.\nNote: n.", "Note: n.\n- **A** — gives it."), False),
        "an undeclared added line": (base.replace("Several fit:", "Several fit:\nStart with **A**."), False),
        "the gap lead is not the cannot lead": (base.replace("These all fit; to choose,",
                                                             "These fit the result you described, but none can "
                                                             "show that one thing causes another; to choose,"), False),
    }
    results = [f"{'ok  ' if lines_only_add(base, cand)[0] == expected else 'FAIL'} {label}: expected {expected}"
               for label, (cand, expected) in cases.items()]
    print("\n".join(results))
    return all(line.startswith("ok") for line in results)


if __name__ == "__main__":
    if sys.argv[1] == "selftest":
        sys.exit(0 if selftest() else 1)
    if sys.argv[1] == "seen":
        seen()
    else:
        live(sys.argv[2], int(sys.argv[3]))
