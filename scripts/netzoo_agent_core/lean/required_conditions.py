"""R15 (2026-11-23, flag NETZOO_LEAN_CONDITION_CHECK, off by default): a DO whose request does not state a condition the
plan's contracts require becomes a question.

Why: on the 739 saved free-model conversations, 31 of the 55 errors were requests that should have been asked about and
ran instead, almost all because a required input or count was never stated (user, 2026-11-23: required conditions
must come from the user; the model must not assume them). Offline (local evaluation data, not in this repository):
684 -> 701/739, McNemar p = 0.0009; gpt-4o-mini forms 171 -> 177/209 (p = 0.18). Those banks are seen, so this is a
candidate until an unseen bank confirms it.

Who decides what: code lists the conditions from the six workflows' contracts (required_inputs, min_samples) for the
steps of the plan, never the model. Jev (closed choices, calibrated) answers only whether the request's own words
state each one: stated_has / stated_lacks / not_mentioned. Code turns DO into ASK when one is not_mentioned with
confidence >= the threshold; stated_lacks changes nothing here (other rules refuse what they can verify). A Jev
failure leaves the decision as it was.

R15b (2026-11-23, user: a missing required input must be asked about, never filled in by the model):
- SPONGE in the plan covers the motif and PPI priors only when the request asks for priors to be built (R3's
  `_BUILD_WORDS`, `prior_requested`). Otherwise the priors are still conditions: the model added SPONGE on its own
  (R015, R051: only a STRING PPI was named, and SPONGE would have replaced it). A stated lack of priors asks nothing.
- PORCUPINE as the first step also needs the networks to be TF-to-gene regulatory networks (porcupine.yaml refuses
  co-expression networks): condition `regulatory` (R050).

The cell-grouping condition is two questions (2026-11-23): whether networks per group are wanted, and whether a table
labels the cells. The first version asked both at once and read "SCORPION on all cells" as "groups wanted, no table"
(L011, F005, L155).
"""

from __future__ import annotations

import os

HAS, LACKS, NONE = "stated_has", "stated_lacks", "not_mentioned"
THRESHOLD = 0.7
JEV_MODEL = "typesafe/jev-1.13"
_INSTR = ("Judge only what the researcher's own words say. Do not assume anything the request does not say. "
          "Pick not_mentioned when the request says nothing either way.")


def enabled() -> bool:
    return os.environ.get("NETZOO_LEAN_CONDITION_CHECK", "off").strip().lower() in ("on", "1", "true")


def _tri(what: str, has: str, lacks: str, none: str = "The request does not say either way.") -> dict:
    return {"type": "choice", "instructions": f"{_INSTR} Question: {what}",
            "criteria": {HAS: has, LACKS: lacks, NONE: none}}


QUESTIONS = {
    "motif": _tri("Does the request say the researcher has a TF-motif prior (TF-to-gene motif file)?",
                  "Yes: it says they have or will provide it (for example 'motif and PPI priors ready', 'our priors').",
                  "No: it says they do not have one."),
    "ppi": _tri("Does the request say the researcher has a protein-protein interaction (PPI) prior?",
                "Yes: it says they have or will provide it (for example 'motif and PPI priors', 'a STRING network').",
                "No: it says they do not have one."),
    "gmt": _tri("Does the request say the researcher has a pathway gene-set file (GMT, for example Reactome, KEGG, "
                "Hallmark)?", "Yes: it says they have or will provide one.", "No: it says they do not have one."),
    "per_sample": _tri("Does the request say its network table holds one network per sample (sample-specific "
                       "networks)?", "Yes: one network per sample, patient or biopsy (for example LIONESS output, "
                       "one column per sample).", "No: it is a single aggregate network, or a different kind of table."),
    "regulatory": _tri("Does the request say its networks are TF-to-gene regulatory networks (for example PANDA, "
                       "LIONESS-PANDA or SCORPION output), rather than gene-gene co-expression networks?",
                       "Yes: regulatory networks linking transcription factors to target genes.",
                       "No: co-expression or gene-gene networks, or another kind of network."),
    "count": _tri("Does the request give how many samples (patients, tumours, biopsies, donors) there are?",
                  "Yes: a number of samples is given.", "No: it says the number is unknown.",
                  "No number of samples is given."),
    "groups": _tri("Does the request give how many groups (patients, donors) will each get a network?",
                   "Yes: a number of groups is given.", "No: it says the number is unknown.",
                   "No number of groups is given."),
    "raw": _tri("Does the request say the expression values are raw read counts?",
                "Yes: raw counts.", "No: it says another scale (normalized, TPM, log, intensities)."),
    "expression": _tri("Does the request say the data matrix is gene expression (RNA-seq or microarray expression)?",
                       "Yes: gene expression.",
                       "No: it says another kind of data (for example mutations, methylation)."),
    "group_wanted": {"type": "choice", "instructions": f"{_INSTR} Question: does the request ask for one network per "
                     "group of cells (per patient, donor, cell type, cluster or condition)?",
                     "criteria": {HAS: "Yes: a network for each group of cells is asked for.",
                                  LACKS: "No: one network from all the cells, or no grouping is named.",
                                  NONE: "The request does not say either way."}},
    "group_table": _tri("Does the request say a cell metadata or annotation table gives each cell's group "
                        "(patient, cell type, cluster, condition)?",
                        "Yes: such a table or column is mentioned.", "No: it says there is no such table."),
    "replicates": {"type": "choice", "instructions": f"{_INSTR} Question: if the request compares networks between "
                   "conditions, does it say each side has several donors or replicates?",
                   "criteria": {HAS: "Yes: several donors, patients or replicates on each side are stated.",
                                LACKS: "No comparison between conditions is asked for, or it says one donor per side.",
                                NONE: "A comparison is asked for, but the number of donors or replicates is not said."}},
}

ASK_TEXT = {
    "motif": "a TF-motif prior for your organism (do you have one?)",
    "ppi": "a protein-protein interaction prior (do you have one?)",
    "gmt": "PORCUPINE needs a pathway gene-set file (GMT); do you have one?",
    "per_sample": "PORCUPINE reads sample-specific networks; does your table hold one network per sample?",
    "regulatory": "PORCUPINE reads TF-to-gene regulatory networks, not co-expression networks; which kind are yours?",
    "count": "how many samples you have (the workflow has a minimum)",
    "groups": "how many patients or groups will each get a network (PORCUPINE needs at least 8)",
    "raw": "SNAIL takes raw counts; are your expression values raw counts?",
    "expression": "whether the matrix is gene expression",
    "group_table": "which table labels each cell's group (for one network per group)",
    "replicates": "how many donors or replicates each side of the comparison has",
}


def sponge_asked(task: str, steps: list[str]) -> bool:
    """SPONGE is in the plan because the request asks for priors to be built (R15b), not because the model added it."""
    from ..prior_request import prior_requested
    from .request_facts import _BUILD_WORDS

    return "SPONGE-PRIORS" in steps and bool(_BUILD_WORDS.search(task) or prior_requested(task))


def conditions(task: str, raw: dict, steps: list[str]) -> list[str]:
    """The questions a DO plan's contracts need answered from the request (code, not the model)."""
    from . import _found, prep_steps

    need, nets = [], [s for s in steps if s not in prep_steps()]
    if not sponge_asked(task, steps) and any(s in steps for s in ("PANDA", "LIONESS-PANDA", "SCORPION")):
        need += ["motif", "ppi"]
    if "PORCUPINE" in steps:
        need.append("gmt")
        if nets and nets[0] == "PORCUPINE":
            need += ["per_sample", "regulatory"]
    count = raw.get("sample_count")
    if not (isinstance(count, int) and _found(task, raw.get("sample_count_quote", ""))):
        if "SCORPION" in steps and "PORCUPINE" in steps:
            need.append("groups")
        elif "LIONESS-PANDA" in steps or "PORCUPINE" in steps:
            need.append("count")
    if "NORMALIZE-EXPRESSION" in steps:
        need.append("raw")
    if nets and nets[0] in ("PANDA", "LIONESS-PANDA"):
        need.append("expression")
    if "SCORPION" in steps:
        need += ["group_wanted", "group_table", "replicates"]
    return need


def missing(answers: dict, threshold: float = THRESHOLD) -> list[str]:
    """Conditions the request leaves unstated, from Jev's answers ({name: {choice, confidence}})."""
    def unstated(name):
        a = answers.get(name) or {}
        return a.get("choice") == NONE and (a.get("confidence") or 0) >= threshold

    out = [name for name in answers if name not in ("group_wanted", "group_table") and unstated(name)]
    wanted = answers.get("group_wanted") or {}
    if wanted.get("choice") == HAS and (wanted.get("confidence") or 0) >= threshold and unstated("group_table"):
        out.append("group_table")
    return out


def question_text(names: list[str], steps: list[str] = ()) -> str:
    lines = [f"- {ASK_TEXT[n]}" for n in names]
    if "SPONGE-PRIORS" in steps and {"motif", "ppi"} & set(names):
        lines.append("- (If you have no priors, SPONGE can build human motif and PPI priors; say so and it will.)")
    return "Before anything runs, please tell me:\n" + "\n".join(lines)


def check(task: str, raw: dict, decided, *, threshold: float = THRESHOLD, timeout: float = 30):
    """R15 on a decision: returns (decision, record). The decision changes only from DO to ASK."""
    from ..jev_client import decide as jev

    if decided.kind != "DO" or not (need := conditions(task, raw, list(decided.steps))):
        return decided, None
    try:
        out = jev(f"Researcher's request:\n{task}", {name: QUESTIONS[name] for name in need}, timeout=timeout)
        answers = {n: {"choice": a.get("choice"), "confidence": a.get("confidence")}
                   for n, a in (out.get("answers") or {}).items()}
    except Exception as error:  # Jev down or no key: the decision stands
        return decided, {"model": JEV_MODEL, "error": repr(error)[:200], "cost_usd": 0.0}
    record = {"model": JEV_MODEL, "answers": answers, "cost_usd": float((out.get("usage") or {}).get("cost") or 0)}
    if gaps := missing(answers, threshold):
        decided.kind = "ASK"
        decided.question = decided.reply = question_text(gaps, list(decided.steps))
        decided.notes = []
        decided.rules.append(f"R15: not stated in the request: {', '.join(gaps)}")
    return decided, record
