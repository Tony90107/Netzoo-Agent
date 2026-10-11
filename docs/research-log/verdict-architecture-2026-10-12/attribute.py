"""Log 409: which part of the pipeline made each executability misjudgment (no model calls).

Usage (repository root): python docs/research-log/verdict-architecture-2026-10-12/attribute.py

Reads every labelled normal-operation round (n11, b12, m13, r14, x15; s11 is the simulated outage and is
reported apart) with its final labels (resolved/checked over labeller A) and, per (session, gold requirement),
puts each misjudged or unclear outcome under the component whose verdict the reply carried:

- the check's verdict for that requirement (`layers[].checked`: available/with_step/partial/not_available,
  `unconfirmed`, or None when the check read no result there), and
- routing's offer (`candidates`, `status`).

Contradictions are split into the code-detected kind (understanding paragraph credits one workflow, the body
selects another or none) and the rest.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOG = HERE.parent
ROUNDS = {
    "n11": "requirement-verdicts-2026-10-10", "s11": "requirement-verdicts-2026-10-10",
    "b12": "checked-no-result-2026-10-11", "m13": "checked-match-2026-10-11",
    "r14": "reread-2026-10-11", "x15": "executability-score-2026-10-11",
}
SETS = {"n11": "requirement-verdicts-2026-10-10/heldout11.json", "s11": "requirement-verdicts-2026-10-10/heldout11.json",
        "b12": "checked-no-result-2026-10-11/heldout12.json", "m13": "checked-match-2026-10-11/heldout13.json",
        "r14": "reread-2026-10-11/heldout14.json", "x15": "executability-score-2026-10-11/heldout15.json"}
# Arms whose code is the live code or one rule away from it (Log 405 onward).
RECENT = {("m13", "cand"), ("r14", "base"), ("r14", "cand"), ("x15", "live")}
SAYS_GIVEN = {"GIVEN", "GIVEN_WITH_STEP", "GIVEN_IF_INPUT"}
UNCLEAR = {"UNCONFIRMED", "ASKED", "OMITTED"}
CREDITED = {"available", "with_step", "partial"}


def final_labels(tag: str, folder: str) -> dict:
    live = LOG / folder / "live"
    key = json.loads((live / f"{tag}-blind-key.json").read_text())
    a = json.loads((live / f"{tag}-labels-A.json").read_text())
    over = {}
    for name in ("labels-resolved", "labels-checked"):
        path = live / f"{tag}-{name}.json"
        if path.exists():
            over.update(json.loads(path.read_text()))
    b_path = live / f"{tag}-labels-B.json"
    b = json.loads(b_path.read_text()) if b_path.exists() else {}
    labels = {}
    for code, sid in key.items():
        label = over.get(code) or a[code]
        if code not in over and b and b.get(code, {}).get("R") != a[code].get("R"):
            raise ValueError(f"{tag} {code}: labellers disagree and no resolution")
        labels[sid] = label
    return labels


def offered(row) -> bool:
    return bool(row.get("candidates")) and row.get("status") != "unsupported"


def source(row, layer, label) -> str:
    verdict = layer.get("checked")
    negative = layer["expect"] == "not_supported"
    if verdict in CREDITED:
        return "check credited it" if negative else "check credited it, reply did not"
    if verdict == "not_available":
        return "check refused it, reply offered a workflow" if negative else "check refused it"
    if verdict == "unconfirmed":
        return "check unconfirmed (backup/failed)"
    if row.get("errors") or row.get("reply_kind") == "unresolved":
        return "routing failed, check read no result"
    return ("check read no result there; routing's offer stood" if offered(row)
            else "check read no result there; nothing offered")


def main() -> None:
    out = []

    def say(text=""):
        out.append(text)
        print(text)

    tables = {"all normal rounds": lambda tag, arm: tag != "s11", "recent arms (Log 405 on)": lambda t, a: (t, a) in RECENT,
              "s11 outage": lambda tag, arm: tag == "s11"}
    rows_by_round = {}
    for tag, folder in ROUNDS.items():
        rows = json.loads((LOG / folder / "live" / f"{tag}-structure.json").read_text())
        labels = final_labels(tag, folder)
        items = {item["id"]: item for item in json.loads((LOG / SETS[tag]).read_text())["items"]}
        rows_by_round[tag] = (rows, labels, items)
    for title, keep in tables.items():
        n = Counter()
        causes = defaultdict(Counter)
        examples = defaultdict(list)
        contra = Counter()
        route = Counter()
        for tag, (rows, labels, items) in rows_by_round.items():
            for sid, row in rows.items():
                if row.get("missing") or not keep(tag, row["arm"]) or sid not in labels:
                    continue
                label = labels[sid]
                n["sessions"] += 1
                if str(label.get("contradiction", "no")).startswith("yes"):
                    contra["code: understanding vs body" if row.get("conflicts") or row.get("contradictions")
                           else "other"] += 1
                gold = items[row["item"]]["requirements"]
                for index, (layer, given) in enumerate(zip(row["layers"], label.get("R") or [])):
                    negative = layer["expect"] == "not_supported"
                    n["neg" if negative else "pos"] += 1
                    if negative and (given in SAYS_GIVEN or given == "PARTLY"):
                        kind = "FALSE ACCEPT"
                    elif not negative and given == "NOT_GIVEN":
                        kind = "FALSE REFUSAL"
                    elif negative and given in UNCLEAR:
                        kind = "neg unclear"
                    elif not negative and (given in UNCLEAR or given == "PARTLY"):
                        kind = "pos unclear"
                    else:
                        if not negative:
                            by = {"run_" + name.lower().replace("-", "_") for name in gold[index].get("by", [])}
                            cands = set(row.get("candidates") or [])
                            route["right workflow offered" if by & cands else
                                  "said doable, no gold workflow offered"] += 1
                        continue
                    cause = source(row, layer, given)
                    causes[kind][cause] += 1
                    examples[(kind, cause)].append(f"{tag}-{row['arm']}-{row['item']}-{row['rep']}")
        say(f"## {title}: {n['sessions']} sessions, {n['neg']} negative and {n['pos']} positive requirements")
        for kind in ("FALSE ACCEPT", "FALSE REFUSAL", "neg unclear", "pos unclear"):
            total = sum(causes[kind].values())
            say(f"{kind}: {total}")
            for cause, count in causes[kind].most_common():
                shown = sorted(set(e.rsplit("-", 1)[0] for e in examples[(kind, cause)]))
                say(f"    {count:3d}  {cause}   e.g. {', '.join(shown[:6])}")
        say(f"contradiction sessions: {dict(contra)}")
        say(f"positives said doable: {dict(route)}")
        say()
    (HERE / "attribution.txt").write_text("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
