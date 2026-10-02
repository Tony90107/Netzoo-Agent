"""Hash of the condition recommender's model-visible messages and schema (as Log 304's `dd5f012d0be4`).

Usage (repository root): python docs/research-log/cohort-witness-2026-10-02/condition_prompt_hash.py
Three candidate sets: BONOBO vs LIONESS-COEXPRESSION (cohort_size), PANDA/OTTER/GIRAFFE, PANDA/PUMA.
"""
import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from evaluate_routing import ProjectPolicyLoader  # noqa: E402
from netzoo_agent_core.graph.condition_recommender import _candidate_facts, _condition_schema, condition_options  # noqa: E402
from netzoo_agent_core.llm import build_selection_condition_messages  # noqa: E402

context = SimpleNamespace(project_policy=ProjectPolicyLoader(ROOT).load())
digest = hashlib.sha256()
for candidates in (["run_lioness_coexpression", "run_bonobo"], ["run_panda", "run_otter", "run_giraffe"], ["run_panda", "run_puma"]):
    options = condition_options(candidates)
    messages = build_selection_condition_messages(
        "Which tool? Advice only.", [(o.condition, o.label) for o in options], _candidate_facts(candidates, context))
    digest.update(json.dumps([str(m.content) for m in messages], ensure_ascii=False).encode())
    digest.update(json.dumps(_condition_schema(options).model_json_schema(), sort_keys=True).encode())
print(digest.hexdigest()[:12])
