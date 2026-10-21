"""Free-model probe: schema compatibility, latency and rate limits of OpenRouter's free models (no full sessions).

Sends 10 bench requests (core-judgment items.json) to each free candidate for two reading roles, exactly as built
in production -- the capability check (function calling, strict, `proposal_model`) and the semantic interpreter
(function calling, `SemanticInterpretation`) -- and records whether the reply decodes, whether code accepts the
check's quotes (`build_capability_check`), the time, output tokens and the error kind. Only a 429 is retried (after
a wait, counted in `rate_limited`; `first_attempt_ok` is the production view, which retries nothing); every other
provider failure is a result. Only `:free` model ids are allowed: nothing is billed.

Usage: probe.py OUT.json [MODEL ...]
"""
from __future__ import annotations
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from dotenv import dotenv_values  # noqa: E402

for key, value in dotenv_values(ROOT / '.env', interpolate=False).items():
    if value is not None:
        os.environ.setdefault(key, value)

from langchain_openai import ChatOpenAI  # noqa: E402
from netzoo_agent_core.cli.bootstrap import load_project_policy  # noqa: E402
from netzoo_agent_core.contracts.capability_check import proposal_model  # noqa: E402
from netzoo_agent_core.contracts.outcomes import SemanticInterpretation  # noqa: E402
from netzoo_agent_core.graph.capability_check_call import build_capability_check_messages  # noqa: E402
from netzoo_agent_core.graph.prompts import build_graph_prompts  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import build_capability_check  # noqa: E402
from netzoo_agent_core.interpretation.semantic_repair import semantic_payload  # noqa: E402
from netzoo_agent_core.llm import build_semantic_interpreter_messages  # noqa: E402

MODELS = (
    'nvidia/nemotron-3-super-120b-a12b:free',  # today's capability-check model: the reference
    'nvidia/nemotron-3.5-super-vl:free',
    'nvidia/nemotron-3-ultra-550b-a55b:free',
    'thinkingmachines/inkling:free',
    'dots-studio/dots-3-note-preview:free',
    'google/gemma-4-31b-it:free',
)
ITEMS = ('C04', 'C07', 'C17', 'C32', 'C36', 'C39', 'C41', 'C45', 'C53', 'C58')
MAX_TOKENS = 16000  # the capability check's production cap (reasoning models spend it before the answer)
TIMEOUT = 300
RATE_LIMIT_RETRIES, RATE_LIMIT_WAIT = 3, 20  # a 429 is waited out up to 3 times; `rate_limited` counts them


def _kind(error: Exception) -> str:
    text = f'{type(error).__name__} {error}'.lower()
    for kind, marks in (('rate_limit', ('429', 'rate limit', 'ratelimit')), ('timeout', ('timeout', 'timed out')),
                        ('provider', ('502', '503', '500', 'connection', 'provider returned error', 'no endpoints')),
                        ('decode', ('validation', 'json', 'parse', 'tool_calls', 'none is not'))):
        if any(mark in text for mark in marks):
            return kind
    return 'other'


def _call(llm, schema, messages, strict):
    adapter = llm.with_structured_output(schema, method='function_calling', include_raw=True,
                                         **({'strict': True} if strict else {}))
    payload, raw = semantic_payload(adapter.invoke(messages))
    payload = payload.model_dump() if hasattr(payload, 'model_dump') else payload
    parsed = schema.model_validate(payload)
    usage = getattr(raw, 'usage_metadata', None) or {}
    finish = (getattr(raw, 'response_metadata', None) or {}).get('finish_reason')
    return parsed, usage.get('output_tokens'), finish


def probe_model(model: str, tasks: dict[str, str], semantic_prompt: str) -> list[dict]:
    if not model.endswith(':free'):
        raise ValueError(f'Not a free model id: {model}')
    llm = ChatOpenAI(model=model, temperature=0.0, api_key=os.environ['OPENROUTER_API_KEY'],
                     base_url='https://openrouter.ai/api/v1', max_tokens=MAX_TOKENS, timeout=TIMEOUT, max_retries=0)
    rows = []
    for item, task in tasks.items():
        for role in ('capability_check', 'semantic_interpreter'):
            row = {'model': model, 'item': item, 'role': role, 'rate_limited': 0}
            for attempt in range(1 + RATE_LIMIT_RETRIES):
                started = time.time()
                try:
                    if role == 'capability_check':
                        messages, count = build_capability_check_messages(task)
                        parsed, tokens, finish = _call(llm, proposal_model(count), messages, strict=True)
                        check, rejected = build_capability_check(task, parsed)
                        row.update(results=[[r.status, r.quote[:60]] for r in check.results()],
                                   rejected=len(rejected), unchecked=len(check.unchecked), goal=check.goal)
                    else:
                        messages = build_semantic_interpreter_messages(semantic_prompt, task)
                        parsed, tokens, finish = _call(llm, SemanticInterpretation, messages, strict=False)
                        row.update(request_mode=getattr(parsed, 'request_mode', None))
                    row.update(status='success', output_tokens=tokens, finish=finish, error_kind='', error='')
                except Exception as error:  # only a 429 is retried (production retries nothing): both are reported
                    row.update(status='failed', error_kind=_kind(error),
                               error=f'{type(error).__name__}: {str(error)[:300]}')
                row['seconds'] = round(time.time() - started, 1)
                if row['error_kind'] != 'rate_limit':
                    break
                row['rate_limited'] += 1
                time.sleep(RATE_LIMIT_WAIT)
            row['first_attempt_ok'] = row['status'] == 'success' and row['rate_limited'] == 0
            rows.append(row)
            print(f"{model:<45} {item} {role:<20} {row['status']:<8} {row.get('error_kind', ''):<10} "
                  f"{row['seconds']:>6}s tok={row.get('output_tokens')}", flush=True)
    return rows


def main(out: str, *models: str) -> None:
    items = {x['id']: x['prompt'] for x in json.loads(
        (ROOT / 'docs/research-log/core-judgment-2026-10-15/items.json').read_text())['items']}
    tasks = {key: items[key] for key in ITEMS}
    semantic_prompt = build_graph_prompts(load_project_policy()).semantic
    with ThreadPoolExecutor(len(models or MODELS)) as pool:  # one thread per model: each model's limit is its own
        results = list(pool.map(lambda m: probe_model(m, tasks, semantic_prompt), models or MODELS))
    rows = [row for rows in results for row in rows]
    Path(out).write_text(json.dumps({'items': list(ITEMS), 'max_tokens': MAX_TOKENS, 'timeout': TIMEOUT,
                                     'rows': rows}, ensure_ascii=False, indent=1) + '\n')


if __name__ == '__main__':
    main(sys.argv[1], *sys.argv[2:])
