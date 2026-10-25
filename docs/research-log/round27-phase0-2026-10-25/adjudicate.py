"""ROUND-27 phase 0: apply the content brief's own definition of `certainty` to the labeller's 53 `unsure` units.

Rule (CONTENT-SPOT-CHECK.md): a unit is unsure for C1 only when the alternatives the user gives for it map to
different `content` or different `made_by` values. Other doubts about the data (counts, transforms, sample overlap,
file format, single-cell vs bulk) keep `certainty_c1 = stated` and are left to the existing typed fields.
Writes content-labels-adjudicated.json (original labels kept, `certainty_c1` and `c1_note` added).
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
# (id, n): why the alternatives differ in content or origin -- decided by reading each prompt (CONTENT-SPOT-CHECK.md)
C1_UNSURE = {
    ("C06", 2): "TF prior vs RNA-binding-protein lists: tf_gene_prior vs other",
    ("C20", 0): "expression vs somatic mutation calls",
    ("C21", 0): "PANDA TF-gene network vs gene-gene co-expression network",
    ("C39", 3): "miRNA vs piRNA target prior: mirna_prior vs other",
    ("C44", 2): "full correlation matrix vs LIONESS co-expression edge-by-sample table (made_by differs)",
    ("C56", 0): "somatic vs germline calls: somatic_mutation vs other",
    ("H13", 0): "TF-gene network vs gene-gene co-expression network",
    ("H25", 0): "somatic vs germline calls",
    ("J34", 0): "somatic vs germline calls",
    ("J36", 1): "miRNA vs piRNA target predictions",
    ("L05", 0): "somatic vs germline calls",
    ("L22", 0): "TF-gene network vs gene-gene correlation edges",
    ("M06", 0): "somatic vs germline calls",
    ("Q35", 0): "somatic mutation counts vs copy-number log2 ratios",
}


def main() -> None:
    data = json.loads((HERE / "content-labels.json").read_text())
    unsure = {(u["id"], u["n"]) for u in data["units"] if u["certainty"] == "unsure"}
    assert set(C1_UNSURE) <= unsure, sorted(set(C1_UNSURE) - unsure)
    for u in data["units"]:
        key = (u["id"], u["n"])
        u["certainty_c1"] = "unsure" if key in C1_UNSURE else "stated"
        u["c1_note"] = C1_UNSURE.get(key, "doubt is not about content or origin" if key in unsure else "")
    data["adjudication_note"] = __doc__.strip()
    (HERE / "content-labels-adjudicated.json").write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
    print(f"unsure: labeller {len(unsure)}, for C1 {len(C1_UNSURE)}")


if __name__ == "__main__":
    main()
