"""Log 191 replay: every recorded trial's name lookups and match, old (identity) vs new."""
import json, glob, os, sys, importlib
root = sys.argv[1]; sys.path.insert(0, root + "/scripts")
P = "/private/tmp/claude-501/-Users-chenzhonghan-Documents-LLM-AGENT/8f6660b9-a748-4022-87ea-7496f85a5ff5/scratchpad"
from netzoo_agent_core.contracts import TaskDecision
from netzoo_agent_core.routing import path_tokens
from netzoo_agent_core.routing.named_labels import named_registered_action, solely_named_run_action
from netzoo_agent_core.interpretation.extraction import _needs_lioness_mode_choice
from netzoo_agent_core.routing.method_rejections import rejected_methods_for
from netzoo_agent_core.routing.outcome_matching import match_semantic_request
MODS = [importlib.import_module("netzoo_agent_core." + n) for n in ("routing.named_labels", "routing.method_rejections", "interpretation.extraction", "handoff", "interpretation.concept_answers")]
real = path_tokens.without_path_tokens
rows = []
for f in sorted(glob.glob(P + "/trace*.json")) + sorted(glob.glob(root + "/docs/research-log/live-semantic-trace-*.json")):
    try: d = json.load(open(f))
    except Exception: continue
    for i, r in enumerate(d.get("results", [])):
        t = r.get("_trace") or {}
        task = t.get("prompt") or r.get("prompt")
        if not task: continue
        dec = None
        if t.get("decision"):
            try: dec = TaskDecision.model_validate(t["decision"])
            except Exception: dec = None
        rows.append((f"{os.path.basename(f)}#{r.get('id')}#{i}", task, dec))
corpus = json.load(open(root + "/tests/routing_scenarios.json"))
corpus = corpus if isinstance(corpus, list) else corpus.get("cases") or corpus.get("scenarios")
for c in corpus: rows.append(("corpus#" + c["id"], c["prompt"], None))

def run():
    out = {}
    for key, task, dec in rows:
        item = {"named": named_registered_action(task), "sole": solely_named_run_action(task), "lioness_choice": _needs_lioness_mode_choice(task)}
        if dec is not None and dec.outcome_hypotheses:
            hyps = [h.model_copy(deep=True) for h in dec.outcome_hypotheses]
            mode = (t := dec.model_dump().get("requested_outcome")) and "guidance" if not dec.should_execute else "execute"
            m = match_semantic_request(task, hyps, request_mode=mode)
            item["match"] = [m.status, m.match_basis, m.matched_actions, m.hypothesis_actions, [x.action for x in m.rejected_methods]]
        out[key] = item
    return out
new = run()
for m in MODS: m.without_path_tokens = lambda text, root=None: text
old = run()
for m in MODS: m.without_path_tokens = real
changed = {k: (old[k], new[k]) for k in new if old[k] != new[k]}
print("rows", len(rows), "changed", len(changed))
for k, (o, n) in sorted(changed.items()):
    diff = {f: (o.get(f), n.get(f)) for f in n if o.get(f) != n.get(f)}
    print(k, "|", json.dumps(diff))
json.dump({k: {"old": o, "new": n} for k, (o, n) in changed.items()}, open(sys.argv[2], "w"), indent=1)
