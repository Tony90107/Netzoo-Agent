"""Log 410 pre-measure: the reply resolver's decision on follow-up replies, one checkout at a time.

Usage (repository root, provider key in the environment):
  REPLAY_CODE_ROOT=<checkout> python docs/research-log/follow-up-conditions-2026-10-12/resolver_ab.py <out.json> [calls]

Each reply is resolved `calls` times (default 3) against a trusted context like the one the CLI builds
after a guidance turn, with the checkout's prompt, schema and validation (gpt-4o-mini, the router model).
Written before the live round; the bank is not a held-out set.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

CODE_ROOT = Path(os.environ.get("REPLAY_CODE_ROOT") or Path(__file__).resolve().parents[3])
sys.path.insert(0, str(CODE_ROOT / "scripts"))

from netzoo_agent_core.cli.reply_resolution import _validated_resolution, build_reply_resolution_messages  # noqa: E402
from netzoo_agent_core.contracts import FollowUpContext, ReplyIntentDecision  # noqa: E402
from netzoo_agent_core.llm import build_llm, structured_result_payload, validate_router_model  # noqa: E402

QUESTION = ("Enter a follow-up question, provide inputs only if you want to execute the complete recommended "
            "pipeline, or describe another NetZoo goal.")
CONTEXTS = {
    "C1": ("We want per-sample TF-gene networks from expression, motifs and PPI of 50 samples.", ["run_lioness_panda", "run_panda"]),
    "C2": ("We have a TF-gene network and want its modules.", ["run_condor"]),
    "C3": ("We want a TF-gene network from expression, motifs and PPI of 40 samples.", ["run_panda", "run_otter", "run_giraffe"]),
    "C4": ("We want a network linking expression and methylation in 60 samples.", ["run_dragon"]),
    "C5": ("We want one gene co-expression network across our 120 samples.", ["run_lioness_coexpression"]),
}
BANK = [
    ("condition", "C1", "Those samples are 50 spatial spots from one tissue section, and neighbouring spots should share information."),
    ("condition", "C2", "But TFs need to be allowed in more than one module."),
    ("condition", "C3", "Actually our data are 40 single nuclei, not bulk samples."),
    ("condition", "C3", "Our regulators include miRNAs too, from predicted binding sites."),
    ("condition", "C4", "We also have copy number, and all three layers must be modelled in one network."),
    ("condition", "C5", "Actually we need one for each sample."),
    ("condition", "C1", "The samples come from two time points of the same 25 patients."),
    ("condition", "C3", "We only have expression, no motif prior."),
    ("condition", "C4", "The methylation was measured on a different set of samples."),
    ("condition", "C2", "The network is gene-gene co-expression, not TF-gene."),
    ("acknowledgement", "C1", "ok thanks"),
    ("acknowledgement", "C2", "sounds good"),
    ("acknowledgement", "C3", "hmm"),
    ("acknowledgement", "C4", "interesting"),
    ("acknowledgement", "C5", "great, that helps"),
    ("new_goal", "C1", "Separately, we have somatic mutations for 200 tumors and want patient subtypes."),
    ("new_goal", "C5", "Now I want to find communities in a bipartite TF-gene network."),
    ("new_goal", "C3", "Different question: can you predict drug response from expression?"),
    ("question", "C1", "How long would that take for 50 samples?"),
    ("question", "C2", "What does the core score mean?"),
    ("question", "C4", "Does it give p-values for the edges?"),
    ("accept", "C1", "Yes, let's plan LIONESS-PANDA."),
    ("accept", "C2", "Go with CONDOR."),
    ("navigation", "C3", "back"),
]


def main() -> None:
    out, calls = Path(sys.argv[1]), int(sys.argv[2]) if len(sys.argv) > 2 else 3
    llm = build_llm(validate_router_model(os.environ.get("NETZOO_ROUTER_MODEL", "openai/gpt-4o-mini")), 0.0,
                    max_output_tokens=256).with_structured_output(
        ReplyIntentDecision, method="function_calling", include_raw=True)
    rows = []
    for family, ctx_key, reply in BANK:
        goal, candidates = CONTEXTS[ctx_key]
        context = FollowUpContext(prior_user_goal=goal, prompt_kind="recommended_workflow", prompt_question=QUESTION,
                                  candidate_actions=candidates, continuation_action=candidates[0])
        for _ in range(calls):
            try:
                payload, _raw = structured_result_payload(llm.invoke(build_reply_resolution_messages(context, reply)))
                decision = ReplyIntentDecision.model_validate(payload)
                resolution = _validated_resolution(decision, context, reply)
                rows.append({"family": family, "reply": reply, "kind": decision.kind,
                             "confidence": decision.confidence, "resolved": resolution.kind,
                             "task": resolution.resolved_task})
            except Exception as error:  # noqa: BLE001 - recorded, not hidden
                rows.append({"family": family, "reply": reply, "error": f"{type(error).__name__}: {error}"[:200]})
    out.write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    print(f"{len(rows)} rows -> {out}")


if __name__ == "__main__":
    main()
