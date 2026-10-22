"""h6 sealing check (ROUND.md): counts, ids, language and quote validity only -- never prints a prompt, gold or label.

Usage: python3 check_format.py
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent


def items(name: str):
    path = HERE / name
    return json.loads(path.read_text())["items"] if path.exists() else None


def main():
    for name in ("items-author.json", "items.json"):
        found = items(name)
        if found is None:
            print(f"{name}: missing")
            continue
        ids = [item["id"] for item in found]
        print(f"{name}: {len(found)} items; ids R01-R48 exactly: {ids == [f'R{i:02d}' for i in range(1, 49)]}; "
              f"classes {dict(Counter(item['class'] for item in found))}; "
              f"forms per class {dict(Counter((item['class'], item['form']) for item in found))}; "
              f"non-ASCII prompts {sum(not item['prompt'].isascii() for item in found)}")
    prompts = {item["id"]: item["prompt"] for item in (items("items.json") or [])}
    labels = items("fields.json")
    if labels is None:
        print("fields.json: missing")
        return
    links = Counter()
    bad = 0
    for item in labels:
        prompt = prompts.get(item["id"], "")
        for field in ("results", "settings", "has", "lacks", "source"):
            for link in item.get(field, []):
                links[field] += 1
                bad += any(link.get(key) and link[key] not in prompt for key in ("quote", "result_quote"))
    print(f"fields.json: {len(labels)} items, ids match items.json: {sorted(i['id'] for i in labels) == sorted(prompts)}; "
          f"links {dict(links)}; quotes not in their prompt: {bad}")


if __name__ == "__main__":
    main()
