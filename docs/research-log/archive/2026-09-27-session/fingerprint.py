"""Offline prompt/schema fingerprint, same dict as evaluate_routing's metadata."""
import sys
from pathlib import Path
root = Path(sys.argv[1]); sys.path.insert(0, str(root / "scripts"))
import evaluate_routing as ev
from netzoo_agent_core.contracts.semantic_claims import SemanticClaims, SemanticClaimRepair
policy = ev.ProjectPolicyLoader(root).load()
prompts = ev.build_graph_prompts(policy)
out = {}
for contract in ("legacy", "claims"):
    schemas = (SemanticClaims, SemanticClaims, SemanticClaimRepair) if contract == "claims" else (ev.SemanticInterpretation, ev.SemanticReview, ev.SemanticPatch)
    value = {
        "semantic": prompts.semantic, "intent": prompts.intent,
        "reviewer": [str(m.content) for m in ev.build_semantic_reviewer_messages(prompts.semantic, "<evaluation prompt>", None, ())],
        "schemas": [s.model_json_schema() for s in (*schemas, ev.SemanticDiscriminator, ev.IntentDecision)] if contract == "legacy" else [s.model_json_schema() for s in (*schemas, ev.IntentDecision)],
        "claim_messages": [str(m.content) for m in ev.claim_messages("<evaluation prompt>", selection_tags={t for spec in policy.workflows.values() for t in spec.output_capability.selection_tags})] if contract == "claims" else None,
    }
    out[contract] = ev._fingerprint(value)[:12]
print(out)
