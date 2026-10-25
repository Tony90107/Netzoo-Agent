"""h10 sealing check (ROUND-27 phase 0): counts and format only -- never a prompt, reason, deciding fact or label.

Usage: python3 check_format.py [items.json] [--fields]
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
WORKFLOWS = {"PANDA", "PUMA", "LIONESS-PANDA", "LIONESS-PUMA", "LIONESS-COEXPRESSION", "LIONESS-DRAGON", "DRAGON",
             "BONOBO", "CONDOR", "COBRA", "OTTER", "GIRAFFE", "SAMBAR"}
CONTENT = {"expression", "other_omics", "coexpression_matrix", "tf_gene_prior", "mirna_prior", "protein_interactions",
           "regulator_gene_network", "gene_gene_network", "somatic_mutation", "sample_annotation", "gene_annotation",
           "other", "not_stated"}
QUOTE = re.compile(r"([\w.-]+\.(?:yaml|py)): \"(.+?)\"(?=\s*(?:;|$|,|\n| [\w.-]+\.(?:yaml|py):))", re.S)


def sources(name: str) -> str:
    path = ROOT / "workflows" / name if name.endswith(".yaml") else ROOT / "scripts" / name
    return path.read_text() if path.exists() else ""


def items(name: str) -> None:
    single = json.loads((HERE / name).read_text())["single"]
    print(f"{name}: {len(single)} items")
    print("category x sub:", dict(sorted(Counter((i["category"], i["sub"]) for i in single).items())))
    print("category x expected_call:", dict(sorted(Counter((i["category"], i["expected_call"]) for i in single).items())))
    print("expected_call:", dict(Counter(i["expected_call"] for i in single)))
    print("uncertainty:", dict(Counter(i.get("uncertainty") for i in single)))
    ids = [i["id"] for i in single]
    print("ids Y01-Y48:", sorted(ids) == [f"Y{n:02d}" for n in range(1, 49)])
    print("non-ASCII prompts:", [i["id"] for i in single if not i["prompt"].isascii()] or "none",
          "| unknown workflow names:", [i["id"] for i in single if not set(i.get("workflows", [])) <= WORKFLOWS] or "none")
    missing = sorted({i["id"] for i in single for source, quote in QUOTE.findall(i.get("evidence", "") or "")
                      if " ".join(quote.split()) not in " ".join(sources(source).split())})
    print("evidence quotes not found verbatim:", missing or "none")
    named = Counter(w for i in single for w in WORKFLOWS if re.search(rf"(?<![\w-]){re.escape(w)}(?![\w-])", i["prompt"]))
    listed = Counter(w for i in single for w in set(i.get("workflows", [])))
    print("workflows (listed in gold / named in a prompt):", {w: (listed[w], named[w]) for w in sorted(WORKFLOWS)})


def fields() -> None:
    prompts = {i["id"]: i["prompt"] for i in json.loads((HERE / "items.json").read_text())["single"]}
    labels = json.loads((HERE / "fields.json").read_text())["items"]
    print(f"fields.json: {len(labels)} items; ids match items.json: {sorted(l['id'] for l in labels) == sorted(prompts)}")
    counts = Counter()
    bad_quotes = set()
    for label in labels:
        for kind in ("results", "settings", "has", "lacks", "source"):
            for unit in label.get(kind, []):
                counts[kind] += 1
                if unit.get("quote") and unit["quote"] not in prompts.get(label["id"], ""):
                    bad_quotes.add(label["id"])
    print("units:", dict(counts))
    has = [u for l in labels for u in l.get("has", [])]
    print("has content:", dict(Counter(u.get("content") for u in has)))
    print("has certainty:", dict(Counter(u.get("certainty") for u in has)))
    print("unknown content values:", sum(u.get("content") not in CONTENT for u in has),
          "| items with a quote not in the prompt:", len(bad_quotes))


if __name__ == "__main__":
    if "--fields" in sys.argv:
        fields()
    else:
        items(next((a for a in sys.argv[1:] if not a.startswith("--")), "items.json"))
