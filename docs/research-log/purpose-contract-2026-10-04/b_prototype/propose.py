"""Path (b) prototype: a model proposes the study purpose with quotes; nothing is verified here.

Usage (repository root, provider key in .env, never printed):
  set -a; . ./.env; set +a; python3 docs/research-log/purpose-contract-2026-10-04/b_prototype/propose.py <tag> <repeats>

Runs one strict structured call (gpt-4o-mini, temperature 0) per prompt of the
seen development sets (Log 340 prompts and held-out sets 1-4) and repeat, and
writes the raw proposals to b_prototype/<tag>-proposals.json. verify.py scores them.
"""
from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Literal

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from pydantic import BaseModel, ConfigDict, Field  # noqa: E402
from netzoo_agent_core.contracts import HumanMessage, SystemMessage  # noqa: E402
from netzoo_agent_core.contracts.strict_schema import strict_json_schema  # noqa: E402
from netzoo_agent_core.llm import build_llm  # noqa: E402

SETS = {
    "dev340": HERE.parent / "dev_log340.json",
    "heldout1": HERE.parent / "heldout" / "heldout.json",
    "heldout2": HERE.parent / "heldout2" / "heldout.json",
    "heldout3": HERE.parent / "heldout3" / "heldout.json",
    "heldout4": HERE.parent / "heldout4" / "heldout.json",
}


class PurposeClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")
    claim: Literal["group_difference", "individual_change", "regulator_change", "causal", "prediction"]
    text_span: str = Field(description="Exact contiguous quote from the request that states this conclusion.")


class StudyPurposeProposal(BaseModel):
    """How the request's samples relate and what it wants to conclude, as it states them."""

    model_config = ConfigDict(extra="forbid")
    design: Literal["paired", "groups", "none"]
    design_span: str = Field(description="Exact contiguous quote stating the design; empty when design is none.")
    claims: list[PurposeClaim] = Field(max_length=3)

    @classmethod
    def model_json_schema(cls, *args, **kwargs):
        return strict_json_schema(super().model_json_schema(*args, **kwargs))


SYSTEM = (
    "Return only the StudyPurposeProposal structure for the user's request. Record only what the "
    "request states; when it does not state something, use none or an empty list.\n\n"
    "design -- how the samples relate:\n"
    "- paired: the same individuals are measured under two or more conditions or time points "
    "(before/after an intervention, repeated visits, matched tissues from the same people, a time course "
    "in the same animals, a crossover, one sample split between treatments).\n"
    "- groups: different individuals are split into two or more groups (cases vs controls, genotypes, "
    "treatment arms, dose groups, strains).\n"
    "- none: no comparison structure is stated. Technical terms are not designs: paired-end reads, two omics "
    "layers from the same samples, batches, replicates, litters used only as blocks, data before and after "
    "normalization.\n\n"
    "claims -- the conclusions the request wants, most important first (at most 3):\n"
    "- group_difference: whether something differs between the groups or changes across conditions at the "
    "cohort level.\n"
    "- individual_change: which individuals (patients, animals, samples) differ or change the most.\n"
    "- regulator_change: which regulators (transcription factors, miRNAs) change or differ the most.\n"
    "- causal: to establish that one thing causes another.\n"
    "- prediction: to predict an outcome for new, unseen samples or individuals.\n"
    "A goal the request rules out ('not causal', 'prediction isn't the point') is not a claim. Describing a "
    "network, finding modules or clustering samples is no claim. Inferring or 'predicting' target genes of a "
    "regulator is network inference, not prediction. A variable such as 'cause of death' is not a causal claim.\n\n"
    "Every text_span and design_span must be copied exactly from the request, without translation."
)


def items():
    for name, path in SETS.items():
        data = json.loads(path.read_text())
        for item in data["items"]:
            yield name, item


def propose(llm, task: str) -> dict:
    adapter = llm.with_structured_output(StudyPurposeProposal, method="function_calling", include_raw=True, strict=True)
    started = time.monotonic()
    try:
        out = adapter.invoke([SystemMessage(content=SYSTEM), HumanMessage(content=task)])
    except Exception as error:  # a failed call is recorded, never retried here
        return {"error": type(error).__name__, "seconds": round(time.monotonic() - started, 2)}
    parsed = out.get("parsed")
    usage = getattr(out.get("raw"), "usage_metadata", None) or {}
    return {
        "proposal": parsed.model_dump() if parsed is not None else None,
        "parse_error": type(out.get("parsing_error")).__name__ if out.get("parsing_error") else None,
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "seconds": round(time.monotonic() - started, 2),
    }


def main(tag: str, repeats: int):
    llm = build_llm("openai/gpt-4o-mini", 0.0, max_output_tokens=400, timeout_seconds=60)
    jobs = [(name, item, rep) for rep in range(1, repeats + 1) for name, item in items()]
    with ThreadPoolExecutor(8) as pool:
        results = list(pool.map(lambda job: (job, propose(llm, job[1]["prompt"])), jobs))
    out = [{"set": name, "id": item["id"], "rep": rep, "prompt": item["prompt"], **result}
           for (name, item, rep), result in results]
    (HERE / f"{tag}-proposals.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    errors = sum(1 for row in out if row.get("error") or row.get("parse_error"))
    tokens = sum((row.get("input_tokens") or 0) + (row.get("output_tokens") or 0) for row in out)
    print(f"{len(out)} calls, {errors} errors, {tokens} tokens")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]))
