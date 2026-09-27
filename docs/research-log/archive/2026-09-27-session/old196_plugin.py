import sys
sys.path.insert(0, "/Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts")
import netzoo_agent_core.graph.semantic_attempts as sa
import netzoo_agent_core.interpretation.request_integrity as ri
sa.supplied_pairs = lambda issues, proposal: None
ri.granularity_mentions = lambda task: ()
