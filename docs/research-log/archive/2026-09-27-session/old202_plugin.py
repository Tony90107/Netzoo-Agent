import sys
sys.path.insert(0, "/Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts")
import netzoo_agent_core.routing.capability_compatibility as cc
orig = cc._supported_entities
def old(artifact_type, capability, granularity="unknown"):
    result = orig(artifact_type, capability, granularity)
    if artifact_type == "community_assignment":
        result = result - ({"tf", "mirna"} - capability.entity_types)
    return result
cc._supported_entities = old
