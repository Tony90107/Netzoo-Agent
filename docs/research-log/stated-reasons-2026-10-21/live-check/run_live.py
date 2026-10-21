"""ROUND-20 live check (Claude, 2026-10-21): J20, C57, C51, C44, C32 and C07 -- each gave a false reason in ROUND-19's
replay -- read live once each with gpt-4o-mini. Copied from named-limits-2026-10-21/live-check/run_live.py; only this
note, the tag and the prior cost differ.

One bounded live CLI smoke. Observes the existing CLI; does not replace any model or routing function."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request

HERE = Path(__file__).resolve().parent
WT = HERE.parents[3]
DOTENV = WT.parents[1]/'netzoo_agent/.env'
HARNESS = WT/'docs/research-log/closed-menu-hybrid-2026-10-19/h4/run_live.py'
MODELS = {'openai/gpt-4o-mini','openai/gpt-4o-mini-2024-07-18'}
TAG = 'statedReasons20261021'


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint():
    head = subprocess.check_output(['git','rev-parse','HEAD'],cwd=WT,text=True).strip()
    files = subprocess.check_output(['git','ls-files','-z','--','scripts','workflows','prompts','AGENTS.md'],cwd=WT).decode().split('\0')
    return {'head':head,'files':{name:sha(WT/name) for name in files if name and (WT/name).is_file()}}


def main():
    if (HERE/'round.json').exists():
        raise RuntimeError('This live round already started; never rerun implicitly.')
    sys.path.insert(0,str(HARNESS.parent))
    spec = importlib.util.spec_from_file_location('existing_h4_live',HARNESS)
    live = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(live)
    env = live.environment(DOTENV)
    config = {k:env.get(k,default) for k,default in {
        'OPENROUTER_MODEL':'openai/gpt-4o-mini','OPENROUTER_ROUTER_MODEL':'openai/gpt-4o-mini',
        'OPENROUTER_SEMANTIC_MODEL':'openai/gpt-4o-mini',
        'OPENROUTER_CAPABILITY_MODEL':''}.items()}
    if set(config.values())-MODELS or config['OPENROUTER_CAPABILITY_MODEL'] != 'openai/gpt-4o-mini-2024-07-18' \
            or not env.get('OPENROUTER_API_KEY'):
        raise RuntimeError('Unexpected model configuration or missing credential')
    with urllib.request.urlopen('https://openrouter.ai/api/v1/models',timeout=20) as response:
        metadata = json.load(response)
    prices = {m['id']:m['pricing'] for m in metadata['data'] if m['id'] in MODELS}
    if set(prices)!=MODELS:
        raise RuntimeError('Could not verify model rates')
    raw = json.loads((HERE/'items.json').read_text())['items']
    turns = sum(len(x.get('turns') or [x.get('prompt')]) for x in raw)
    maximum_rate = max(float(v.get(k,0)) for v in prices.values() for k in ('prompt','completion'))
    conservative_estimate = turns*60_000*maximum_rate
    prior_cost = 0.257  # judgment-live attempts 01-08, the ROUND-17 and ROUND-18 checks
    if len(raw)>6 or turns>7 or prior_cost+conservative_estimate>0.50:
        raise RuntimeError('Live smoke exceeds session/token/cost envelope')
    stamp = datetime.now(timezone.utc).isoformat()
    pricing = {model:{'input_micro_usd_per_million':round(float(p['prompt'])*1e12),
                      'output_micro_usd_per_million':round(float(p['completion'])*1e12),
                      'effective_at':stamp} for model,p in prices.items()}
    env.update({'NETZOO_MAX_TASK_TOKENS':'30000','OPENROUTER_CAPABILITY_EXTRA_TOKENS':'30000',
                'NETZOO_MODEL_PRICING_JSON':json.dumps(pricing),'PYTHONUNBUFFERED':'1'})
    frozen = fingerprint()
    write(HERE/'round.json',{'started_utc':stamp,'code':frozen,'dataset_sha256':sha(HERE/'items.json'),
        'harness':str(HARNESS),'harness_sha256':sha(HARNESS),'config':config,
        'price_source':'https://openrouter.ai/api/v1/models','provider_prices':prices,
        'price_catalog':pricing,'turns':turns,'sessions':len(raw),'max_workers':2,'budget_usd':0.50,
        'estimated_token_envelope_usd':conservative_estimate,'prior_attempt_cost_usd':prior_cost,'actual_execution_authorized':False})
    output = HERE/'live'
    output.mkdir(exist_ok=False)
    def job(item):
        if fingerprint()!=frozen:
            raise RuntimeError('Runtime code changed')
        sid = live.session_id(TAG,item['id'],1)
        result = live.run_job(TAG,item['id'],1,item,WT,output,{**env,'NETZOO_PROFILE':sid},600)
        if fingerprint()!=frozen:
            raise RuntimeError('Runtime code changed during live job')
        return result
    results = []
    sid,codes = job(raw[0])
    results.append({'id':raw[0]['id'],'session':sid,'codes':codes})
    write(HERE/'jobs.json',results)
    print(json.dumps(results[-1]),flush=True)
    if any(c != 0 for c in codes):
        raise RuntimeError('Pilot failed; remaining sessions were not started')
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {pool.submit(job,item):item['id'] for item in raw[1:]}
        for future in as_completed(futures):
            key = futures[future]
            try:
                sid,codes = future.result()
                row = {'id':key,'session':sid,'codes':codes}
            except Exception as exc:
                row = {'id':key,'error_type':type(exc).__name__,'error':str(exc)}
            results.append(row)
            write(HERE/'jobs.json',results)
            print(json.dumps(row),flush=True)
    write(HERE/'finished.json',{'finished_utc':datetime.now(timezone.utc).isoformat(),
          'runtime_code_unchanged':fingerprint()==frozen,'sessions':len(results)})


if __name__=='__main__':
    main()
