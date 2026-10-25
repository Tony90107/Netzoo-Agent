"""ROUND-27 C1: what each piece of the user's data is, read once after a DO, and judged in code against the registry.

Declared in docs/research-log/round27-c1-2026-10-25/ROUND.md before this code. The model only reads: each piece of
data the request says the user has, as one of a closed vocabulary of contents and producers (the field-gold brief's
definitions). Code keeps a piece only when its words are in the request, and judges each credited workflow from the
registry's own `input_artifacts` and `handoff_targets`:

- rule A: the user states main data, and none of it can be given to the workflow -> ask to confirm;
- rule B: a piece the user is unsure of, whose alternatives split the workflow into takes / does not take -> ask.

Only a DO is ever changed, and only into an ASK: a new read never refuses on its own (ROUND-27 shared rule).
"""

from __future__ import annotations

import dataclasses
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

__all__ = ["CONTENTS", "DATA_ITEMS_INSTRUCTIONS", "DataItem", "DataItemsRead", "Finding", "asked_core",
           "data_item_findings", "takes", "verified_items"]

CONTENTS = ("expression", "other_omics", "coexpression_matrix", "tf_gene_prior", "mirna_prior", "protein_interactions",
            "regulator_gene_network", "gene_gene_network", "somatic_mutation", "sample_annotation", "gene_annotation",
            "other", "not_stated")
WORKFLOWS = ("PANDA", "PUMA", "LIONESS-PANDA", "LIONESS-PUMA", "LIONESS-COEXPRESSION", "LIONESS-DRAGON", "DRAGON",
             "BONOBO", "CONDOR", "COBRA", "OTTER", "GIRAFFE", "SAMBAR")
Content = Literal[CONTENTS]  # type: ignore[valid-type]
MadeBy = Literal[(*WORKFLOWS, "outside", "not_stated")]  # type: ignore[valid-type]

# The vocabulary bridge (ROUND.md section 2): main data only; priors, annotations and sample sheets are never judged.
MAIN_ARTIFACTS = {
    "expression": frozenset({"expression_matrix", "measurement_dataset"}),
    "other_omics": frozenset({"measurement_dataset"}),
    "coexpression_matrix": frozenset({"coexpression_network"}),
    "regulator_gene_network": frozenset({"regulatory_network"}),
    "somatic_mutation": frozenset({"mutation_matrix"}),
}
WORDS = {
    "expression": "a gene-by-sample expression table",
    "other_omics": "a per-sample omics measurement table",
    "coexpression_matrix": "a gene-by-gene co-expression or correlation matrix",
    "regulator_gene_network": "a regulator-to-gene network",
    "somatic_mutation": "a per-sample somatic mutation table",
}
ARTIFACT_WORDS = {
    "expression_matrix": "a gene-by-sample expression table",
    "measurement_dataset": "per-sample omics measurement tables",
    "coexpression_network": "a gene-by-gene co-expression matrix",
    "regulatory_network": "a regulator-to-gene network",
    "mutation_matrix": "a per-sample mutation table",
}

DATA_ITEMS_INSTRUCTIONS = """List each piece of data the user says they have, in the request below. Do not judge \
whether any analysis is possible; only say what each piece of data is, from the request's own words.

For each piece:
- quote: the request's exact contiguous words naming that piece of data (a file name or a description).
- content: what the data contains --
  expression: a gene-by-sample (or gene-by-cell) expression measurement table (RNA-seq, microarray, counts, TPM; raw, \
normalized or transformed).
  other_omics: another per-sample continuous omics measurement table (proteomics, methylation, metabolomics, \
copy-number values, chromatin accessibility, ...).
  coexpression_matrix: a gene-by-gene correlation or co-expression matrix (aggregate or per-sample, adjusted or not), \
whatever produced it.
  tf_gene_prior: prior TF-to-gene edges (a motif scan, ChIP-derived or curated TF-target prior).
  mirna_prior: prior miRNA-to-gene target edges.
  protein_interactions: a protein-protein or TF-TF interaction network.
  regulator_gene_network: an already-inferred regulator-to-target network, or another two-sided (bipartite) network \
given as edges or a matrix (a PANDA output, a GRN, SNP-gene eQTL edges).
  gene_gene_network: a gene-gene network that is not a co-expression or correlation matrix (e.g. a pathway graph).
  somatic_mutation: per-sample mutation calls or a mutation matrix.
  sample_annotation: clinical variables, a design or covariate matrix, group labels, survival, sample sheets.
  gene_annotation: gene lists, pathway sets (e.g. GMT), gene lengths or exon sizes.
  other: data whose kind the words state, but none of the above fits.
  not_stated: the words do not say what it contains ("my file", "the data from the core", "the output").
- made_by: a workflow name when the request says that workflow produced it; outside when the request says or \
plainly implies it is measured data, a public resource, or the output of a non-NetZoo tool or person; not_stated when \
the request does not say.
- certainty: unsure only when the user says they are not sure which of two or more contents, or which of two or more \
producers, this data is; otherwise stated. Doubts about counts, transformations, sample overlap, file format or \
anything else are not this field.
- content_alternatives / made_by_alternatives: when certainty is unsure, every content (or producer) the user gives \
as possible; otherwise empty.

Label only what the words say. Do not infer what the data must be from what an analysis would need."""


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DataItem(_Model):
    quote: str = Field(description="The request's exact words naming this piece of data.")
    content: Content = Field(description="What the data contains.")
    made_by: MadeBy = Field(description="What produced it, as the request states it.")
    certainty: Literal["stated", "unsure"] = Field(description="unsure only for a doubt about content or producer.")
    content_alternatives: list[Content] = Field(description="Contents the user gives as possible; empty if stated.")
    made_by_alternatives: list[MadeBy] = Field(description="Producers the user gives as possible; empty if stated.")


class DataItemsRead(_Model):
    items: list[DataItem] = Field(description="Each piece of data the user says they have.")


@dataclasses.dataclass(frozen=True)
class Finding:
    rule: str  # "A" or "B"
    workflow: str
    quote: str
    question: str
    contract_quote: str = ""


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold()).strip()


def verified_items(task: str, read: DataItemsRead | None) -> list[DataItem]:
    """The read's items whose words are in the request (ROUND.md section 1); the rest are dropped."""
    if read is None:
        return []
    request = _norm(task)
    return [item for item in read.items if item.quote.strip() and _norm(item.quote) in request]


def _capability(workflow: str):
    from workflow_registry import ACTION_DEFINITIONS

    from ..method_names import registered_workflows
    action = registered_workflows().get(workflow)
    return action, ACTION_DEFINITIONS[action].output_capability if action else None


def takes(workflow: str, content: str, made_by: str) -> bool | None:
    """Whether data of this content, made by this producer, can be given to the workflow; None when it is not main
    data (never judged)."""
    if content not in MAIN_ARTIFACTS:
        return None
    action, capability = _capability(workflow)
    if capability is None:
        return None
    if not MAIN_ARTIFACTS[content] & set(capability.input_artifacts):
        return False
    if made_by in ("outside", "not_stated"):
        return True
    _, producer = _capability(made_by)
    return producer is not None and action in producer.handoff_targets


def _accepted_words(workflow: str) -> str:
    _, capability = _capability(workflow)
    words = sorted({ARTIFACT_WORDS[a] for a in capability.input_artifacts if a in ARTIFACT_WORDS})
    return " or ".join(words)


def _refusal_clause(workflow: str, content: str) -> str:
    """The contract's own words when its request-level input check refuses this content (`refuses_input:<kind>`)."""
    from .contract_veto import _input_check
    try:
        return _input_check(workflow, f"refuses_input:{content}", whole=True)
    except (KeyError, AttributeError):
        return ""


def data_item_findings(task: str, read: DataItemsRead | None, workflows) -> list[Finding]:
    """Rules A and B for each credited workflow (ROUND.md section 2); empty when nothing applies."""
    items = verified_items(task, read)
    found: list[Finding] = []
    for workflow in workflows:
        if _capability(workflow)[1] is None:
            continue
        stated = [(item, takes(workflow, item.content, item.made_by)) for item in items if item.certainty == "stated"]
        main = [(item, verdict) for item, verdict in stated if verdict is not None]
        if main and not any(verdict for _, verdict in main):
            item = main[0][0]
            found.append(Finding(
                "A", workflow, item.quote,
                f"Is that data {WORDS[item.content]}"
                + (f" made by {item.made_by}" if item.made_by not in ("outside", "not_stated") else "")
                + f"? {workflow} takes {_accepted_words(workflow)} as its input.",
                _refusal_clause(workflow, item.content)))
            continue
        for item in items:
            if item.certainty != "unsure":
                continue
            contents = list(dict.fromkeys(item.content_alternatives)) or [item.content]
            makers = list(dict.fromkeys(item.made_by_alternatives)) or [item.made_by]
            if len(contents) * len(makers) < 2:
                continue  # unsure with fewer than two alternatives judges nothing (ROUND.md section 1)
            verdicts = {takes(workflow, c, m) for c in contents for m in makers}
            if True in verdicts and False in verdicts:
                options = (contents if len(contents) > 1 else makers)
                spoken = [WORDS.get(o, o.replace("_", " ")) if len(contents) > 1 else f"made by {o}" for o in options]
                found.append(Finding(
                    "B", workflow, item.quote,
                    f"Is that data {' or '.join(spoken)}? "
                    f"{workflow} takes {_accepted_words(workflow)} as its input."))
                break
    return found


def asked_core(core, findings: list[Finding]):
    """The live DO turned into an ASK with code's questions; anything else, or no finding, as it came."""
    from ..contracts.core_decision import CoreDecision, FactQuestion
    if core.kind != "DO" or not findings:
        return core
    seen: dict[str, Finding] = {}
    for finding in findings:
        seen.setdefault(finding.question, finding)
    facts = [FactQuestion(question=f.question, user_quote=f.quote, workflows=[f.workflow],
                          contract_quote=f.contract_quote) for f in seen.values()]
    evidence = {**core.evidence, "data_items": [dataclasses.asdict(f) for f in findings]}
    return CoreDecision(kind="ASK", basis="data_item_fact", workflows=list(core.workflows), facts=facts,
                        declined=list(core.declined), evidence=evidence)
