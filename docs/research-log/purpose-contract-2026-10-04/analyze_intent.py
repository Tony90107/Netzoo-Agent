"""Log 370 gates: on a tie with a verified question, lead with what fits it, every candidate kept.

Usage (repository root):
  live round:  HELDOUT=heldout13/heldout.json python3 docs/research-log/purpose-contract-2026-10-04/analyze_intent.py live <tag> <repeats>
  seen data:   python3 docs/research-log/purpose-contract-2026-10-04/analyze_intent.py seen
Each trial's reply and card are rendered offline with the change and without it
(`intent_shortlist.intent_reply` patched to return nothing). Writes
live/<tag>-intent-analysis.txt. Nothing calls a model.
"""
import ast
import glob
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import analyze_cannot as C  # noqa: E402
import analyze_live as A  # noqa: E402
from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.interpretation import intent_shortlist as I  # noqa: E402
from workflow_registry import ACTION_DEFINITIONS  # noqa: E402

LEAD = "these fit best, and here is why:"


def name(action):
    return ACTION_DEFINITIONS[action].workflow


def render_pair(task, decision, traced):
    with_c, kind, card_with = C._render(task, decision, traced)
    original = I.intent_reply
    I.intent_reply = lambda *args, **kwargs: None
    try:
        without_c, _, card_without = C._render(task, decision, traced)
    finally:
        I.intent_reply = original
    return with_c, without_c, kind, card_with, card_without


def _option_keys(card):
    return [o.key for o in card.choices.options] if card is not None and not isinstance(card, str) and card.choices else []


def score(trials, out_name):
    counts, lines = Counter(), []
    s1_bad, s2, s3_bad, s4_bad, u1_bad, h2_bad, k1_bad = [], Counter(), [], [], [], [], []
    for trial in trials:
        item, decision, traced = trial["item"], trial["decision"], trial["traced"]
        with_c, without_c, kind, card_with, card_without = render_pair(item["prompt"], decision, traced)
        counts["trials"] += 1
        if kind == "response_model":
            counts["response_model"] += 1
            continue
        if trial["reply"] is not None and with_c != trial["reply"]:
            h2_bad.append(f"{trial['key']}: live reply differs from its offline render ({kind})")
        # K1: the card keeps every option and step it had.
        if sorted(_option_keys(card_with)) != sorted(_option_keys(card_without)):
            k1_bad.append(f"{trial['key']}: options {_option_keys(card_without)} -> {_option_keys(card_with)}")
        fired = LEAD in (with_c or "")
        if not fired:
            if with_c != without_c:
                u1_bad.append(f"{trial['key']}: changed without a shortlist ({kind})")
            continue
        counts["fired"] += 1
        purpose = C.purpose_of(traced)
        recommended, others = I.intent_shortlist(decision, purpose, item["prompt"])
        names = {name(r.action) for r in recommended}
        acceptable = set(item["acceptable_candidates"])
        label = set(item.get("recommended_subset") or [])
        counts["chars_without"] += len(without_c)
        counts["chars_with"] += len(with_c)
        if not names <= acceptable:
            s1_bad.append(f"{trial['key']}: {sorted(names - acceptable)} not in {sorted(acceptable)}")
        if label:
            s2["labelled"] += 1
            s2["exact" if names == label else "overlap" if names & label else "disjoint"] += 1
        if item.get("is_control") or item["claim_kind"] in {"none", "causal", "prediction"}:
            s3_bad.append(f"{trial['key']} ({item['claim_kind']})")
        missing = [name(a) for a in dict.fromkeys(decision.hypothesis_actions)
                   if a in ACTION_DEFINITIONS and f"**{name(a)}**" not in with_c]
        if missing:
            s4_bad.append(f"{trial['key']}: {missing}")
        lines.append(f"- {trial['key']}: [{item['comparison_design']}/{item['claim_kind']}] candidates "
                     f"{[name(a) for a in dict.fromkeys(decision.hypothesis_actions)]} | recommended {sorted(names)} "
                     f"| acceptable {sorted(acceptable)}" + (f" | label {sorted(label)}" if label else ""))
    fired = counts["fired"]
    summary = [
        f"trials {counts['trials']}, response_model {counts['response_model']}, shortlist fired {fired}",
        f"S1 recommended within acceptable: {fired - len(s1_bad)}/{fired}; failures {s1_bad}",
        f"S2 against recommended_subset (labelled trials): {dict(s2)}",
        f"S3 shortlists on controls / causal / prediction (gate 0): {s3_bad}",
        f"S4 candidates missing from the reply (gate 0): {s4_bad}",
        f"U1 replies changed without a shortlist (gate 0): {u1_bad}",
        f"K1 cards that lost or gained an option (gate 0): {k1_bad}",
        f"H2 live reply equals its offline render: failures {h2_bad}",
        f"report: reply length with/without on fired trials {counts['chars_with']}/{counts['chars_without']}",
    ]
    (HERE / "live" / out_name).write_text("\n".join(summary + [""] + lines) + "\n", encoding="utf-8")
    print("\n".join(summary))


def seen():
    trials = []
    for tag, heldout in (("s7", "heldout7"), ("s8", "heldout8"), ("s9", "heldout9"), ("s10", "heldout10"),
                         ("s12", "heldout12")):
        items = {item["id"]: item for item in json.loads((HERE / heldout / "heldout.json").read_text())["items"]}
        for key, value in json.loads((HERE / "live" / f"{tag}-decisions.json").read_text()).items():
            if not key.startswith("cand-"):
                continue
            traced = value.get("study_purpose")
            traced = ast.literal_eval(traced) if isinstance(traced, str) else traced
            trials.append({"key": f"{tag}-{key[5:]}", "item": items[key[5:].rsplit("-", 1)[0]],
                           "decision": TaskDecision.model_validate(value["decision"]), "traced": traced, "reply": None})
    score(trials, "seen-intent-analysis.txt")


def live(tag, repeats):
    purposes = A.trace_purposes("cand")
    roles_before = set()
    for old in ("s7", "s8", "s9", "s10", "s12"):
        for path in glob.glob(str(A.ROOT / ".netzoo" / "sessions" / f"hp-{old}-cand-*.json")):
            roles_before |= {c["role"] for c in (json.loads(Path(path).read_text()).get("token_usage") or {}).get("calls", [])}
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
    print(f"missing {missing}; H3 roles beyond s7-s12 candidate arms (gate none): {sorted(new_roles)}")
    score(trials, f"{tag}-intent-analysis.txt")


if __name__ == "__main__":
    if sys.argv[1] == "seen":
        seen()
    else:
        live(sys.argv[2], int(sys.argv[3]))
