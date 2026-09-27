import itertools, json, sys
sys.path.insert(0, "/Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts")
from typing import get_args
from workflow_registry import ArtifactType, Granularity, Operation, OUTPUT_CAPABILITIES
from netzoo_agent_core.contracts.outcomes import RequestedOutcome, OutcomeHypothesis, OutcomeEvidence
from netzoo_agent_core.routing.outcome_matching import match_requested_outcome, match_semantic_request
arts = sorted({c.artifact_type for c in OUTPUT_CAPABILITIES.values()} | {a for c in OUTPUT_CAPABILITIES.values() for a in c.produced_artifacts})
grans = ["aggregate", "sample_specific", "unknown"]
ops = ["infer", "analyze", "unknown"]
regsets = [[], ["tf"], ["mirna"], ["tf", "mirna"], ["unknown"]]
entsets = [[], ["gene"], ["tf", "gene"], ["mirna", "gene"], ["tf", "mirna", "gene"], ["sample"], ["gene", "sample"]]
tagsets = [[], ["aggregate_network"], ["sample_specific"]]
out = {}
ev = lambda d, v, src: OutcomeEvidence(dimension=d, value=v, source=src, text_span=("x" if src == "explicit" else None), rationale="r")
for art, g, op, regs, ents, tags in itertools.product(arts, grans, ops, regsets, entsets, tagsets):
    tgt = ["gene"] if regs and regs != ["unknown"] else []
    try:
        o = RequestedOutcome(operation=op, artifact_type=art, granularity=g, regulator_types=regs, target_types=tgt, entity_types=ents, selection_tags=tags)
    except Exception:
        continue
    m = match_requested_outcome(o)
    key = json.dumps([art, g, op, regs, ents, tags])
    row = {"base": [m.status, sorted(m.matched_actions)]}
    for mode in ("guidance", "execute"):
        for gsrc in ("explicit", "inferred"):
            evs = [ev("artifact_type", art, "explicit")]
            if g != "unknown": evs.append(ev("granularity", g, gsrc))
            if op != "unknown": evs.append(ev("operation", op, "explicit"))
            evs += [ev("regulator_type", r, "explicit") for r in regs if r != "unknown"]
            evs += [ev("target_type", t, "explicit") for t in tgt]
            evs += [ev("entity_type", e, "explicit") for e in ents]
            h = OutcomeHypothesis(outcome=o, evidence=evs, confidence=0.9)
            sm = match_semantic_request("x", [h], request_mode=mode)
            row[f"{mode}:{gsrc}"] = [sm.status, sorted(sm.matched_actions), sorted(sm.hypothesis_actions)]
    out[key] = row
json.dump(out, open(sys.argv[1], "w"))
print(len(out), "outcomes")
