import sys
sys.path.insert(0, "/Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent/scripts")
import importlib
for name in ("routing.named_labels", "routing.method_rejections", "interpretation.extraction", "handoff", "interpretation.concept_answers"):
    importlib.import_module("netzoo_agent_core." + name).without_path_tokens = lambda text, root=None: text
