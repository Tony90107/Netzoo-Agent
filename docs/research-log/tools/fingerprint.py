"""Offline prompt/schema fingerprint, the same value evaluate_routing writes to reports.

Usage: python docs/research-log/tools/fingerprint.py

Prints the first 12 hex digits of `prompt_schema_sha256` for the legacy and the
claims contract. Research-log entries quote these (for example legacy
`1f68bfde4081`, claims `348a144cd9b4`) to show a change left every provider
prompt and schema untouched.
"""
import sys

from traces import ROOT

sys.path.insert(0, str(ROOT / "scripts"))

import evaluate_routing as ev  # noqa: E402
from netzoo_agent_core.contracts.semantic_claims import SemanticClaimRepair, SemanticClaims  # noqa: E402

policy = ev.ProjectPolicyLoader(ROOT).load()
prompts = ev.build_graph_prompts(policy)
tags = {tag for spec in policy.workflows.values() for tag in spec.output_capability.selection_tags}
reviewer = [str(m.content) for m in ev.build_semantic_reviewer_messages(prompts.semantic, "<evaluation prompt>", None, ())]
result = {}
for contract in ("legacy", "claims"):
    if contract == "legacy":
        schemas = [s.model_json_schema() for s in (ev.SemanticInterpretation, ev.SemanticReview, ev.SemanticPatch, ev.SemanticDiscriminator, ev.IntentDecision)]
        claim = None
    else:
        schemas = [s.model_json_schema() for s in (SemanticClaims, SemanticClaims, SemanticClaimRepair, ev.IntentDecision)]
        claim = [str(m.content) for m in ev.claim_messages("<evaluation prompt>", selection_tags=tags)]
    result[contract] = ev._fingerprint({
        "semantic": prompts.semantic, "intent": prompts.intent, "reviewer": reviewer,
        "schemas": schemas, "claim_messages": claim,
    })[:12]
print(result)
