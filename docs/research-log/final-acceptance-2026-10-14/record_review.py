"""Record my review of one session in live/<tag>-labels-checked.json (FREEZE.md): the final labels, the
contradiction field, `right_question` for ask-class sessions, and a reason (always given, even when unchanged)."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def record(tag, code, labels=None, contradiction=None, reason="", right_question=None):
    path = HERE / "live" / f"{tag}-labels-checked.json"
    checked = json.loads(path.read_text()) if path.exists() else {}
    given = json.loads((HERE / "live" / f"{tag}-labels-A.json").read_text())[code]
    entry = {"R": labels if labels is not None else given["R"],
             "contradiction": contradiction if contradiction is not None else given.get("contradiction", "no"),
             "reason": reason, "changed": labels is not None and labels != given["R"]}
    if right_question is not None:
        entry["right_question"] = right_question
    checked[code] = entry
    path.write_text(json.dumps(checked, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    for spec in json.loads(sys.argv[2]):
        record(sys.argv[1], **spec)
    print(len(json.loads((HERE / "live" / f"{sys.argv[1]}-labels-checked.json").read_text())), "reviewed")
