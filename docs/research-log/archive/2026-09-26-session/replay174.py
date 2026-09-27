import json, sys
root=sys.argv[1]; S=sys.argv[2]; sys.path.insert(0, root+"/scripts")
from types import SimpleNamespace
from netzoo_agent_core.contracts import LLMUsage
from netzoo_agent_core.contracts.outcomes import CapabilityMatch, OutcomeHypothesis, SemanticInterpretation
from netzoo_agent_core.graph.discriminator import invoke_semantic_discriminator
from netzoo_agent_core.pricing import PriceCatalog
class Rec:
    def append(self,*a,**k): pass
r=json.load(open(f"{S}/trace_log172_live.json"))
for i in (6,7):
    t=r["results"][i]["_trace"]; d=t["decision"]
    disc=[c for c in t["calls"] if c["schema"]=="SemanticDiscriminator"][0]["parsed"]
    ctx=SimpleNamespace(semantic_discriminator=SimpleNamespace(invoke=lambda m, p=disc: {"parsed": p, "raw": object()}),
        semantic_claims=False, semantic_model_name="fixture", router_max_tokens=200, task_token_budget=10_000,
        recorder=Rec(), price_catalog=PriceCatalog())
    interp=SemanticInterpretation(request_mode="guidance", semantic_goal="g",
        outcome_hypotheses=[OutcomeHypothesis.model_validate(h) for h in d["outcome_hypotheses"]])
    match=CapabilityMatch(status="ambiguous", hypothesis_actions=["run_lioness_coexpression","run_cobra"])
    _, narrowed, _, _ = invoke_semantic_discriminator(ctx, {"run_id": "x"}, t["prompt"], interp, match, LLMUsage(), [])
    print(("new" if "wt174" in root else "old"), "trial", i, "discriminator tags", disc.get("selection_tags"), "->", narrowed.status, narrowed.matched_actions or narrowed.hypothesis_actions)
