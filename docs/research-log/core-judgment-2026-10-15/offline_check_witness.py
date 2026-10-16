"""Phase 2 step 1b: the capability check's own reading (with UnknownAbout `other`) as R1's second reader.

Re-reads the dev requests of `offline_fact_compare.py` with the check's model and this checkout's proposal schema,
keeps `uncertain_quotes`, and re-applies R1-R6 to the fact agent's recorded proposals (live/f2) with them.

Usage: offline_check_witness.py IN_TAG OUT_TAG
"""
from __future__ import annotations
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import offline_fact_compare as base
from plan import HERE, write_json

from netzoo_agent_core.contracts.fact_check import FactProposal, FactProposals
from netzoo_agent_core.graph.capability_check_call import build_capability_check_messages
from netzoo_agent_core.contracts.capability_check import CapabilityCheck, proposal_model
from netzoo_agent_core.interpretation.capability_check import stated_quotes, uncertain_quotes
from netzoo_agent_core.interpretation.fact_check import kept_facts
from netzoo_agent_core.interpretation.semantic_repair import semantic_payload
from netzoo_agent_core.llm import build_llm, validate_router_model
from netzoo_agent_core.policy import ProjectPolicyLoader


_BEFORE_R7 = {'about': 'user_data', 'alternatives': []}
"""Phase 5c added `about` and `alternatives`; the phase 2 recordings predate them (every fact read as user_data)."""


def _from_fact(f):
    """A kept FactQuestion back to the agent's proposal (f2 stored the kept facts, not the raw ones)."""
    def split(outcome):
        kind, _, name = outcome.partition(':')
        return kind, name
    yes, yes_name = split(f['if_yes'])
    no, no_name = split(f['if_no'])
    return FactProposal(user_quote=f['user_quote'], uncertainty=f['uncertainty'], workflow=f['workflows'][0],
                        contract_quote=f['contract_quote'], question=f['question'], yes_outcome=yes,
                        yes_workflow=yes_name, no_outcome=no, no_workflow=no_name, **_BEFORE_R7)


def proposals_of(r):
    found = [_from_fact(f) for f in r.get('asked', []) + r.get('said', [])]
    for x in r.get('rejected', []):
        p = x['proposal']
        found.append(FactProposal(**{**_BEFORE_R7, **p}) if 'yes_outcome' in p else _from_fact(p))
    return FactProposals(facts=found[:3])


def read(llm, task):
    messages, count = build_capability_check_messages(task)
    schema = proposal_model(count)
    adapter = llm.with_structured_output(schema, method="function_calling", include_raw=True, strict=True)
    payload, _raw = semantic_payload(adapter.invoke(messages))
    return schema.model_validate(payload.model_dump() if hasattr(payload, 'model_dump') else payload)


def main(in_tag, out_tag):
    policy = ProjectPolicyLoader(HERE.parents[2]).load()
    model = os.environ['OPENROUTER_CAPABILITY_MODEL']
    llm = build_llm(validate_router_model(model), 0.0,
                    max_output_tokens=int(os.environ.get('OPENROUTER_CAPABILITY_MAX_TOKENS', '9000')))
    items = {i['id']: i for i in base.dev_items()}
    rows = json.loads((HERE / 'live' / in_tag / 'fact-compare.json').read_text())
    needed = sorted({r['item'] for r in rows if r.get('status') == 'checked'})

    def witness(item_id):
        task = items[item_id]['prompt']
        started = time.time()
        for attempt in (1, 2):
            try:
                proposal = read(llm, task)
                return item_id, {'uncertain': uncertain_quotes(task, proposal), 'stated': stated_quotes(task, proposal),
                                 'seconds': round(time.time() - started)}
            except Exception as error:  # an undecodable reply is asked once more, as live
                last = f'{type(error).__name__}: {str(error)[:200]}'
        return item_id, {'failed': last}

    saved = HERE / 'live' / out_tag / 'witness.json'
    if saved.exists():  # re-score: the witnesses were read already
        witnesses = {r['item']: r['witness'] for r in json.loads(saved.read_text())}
    else:
        with ThreadPoolExecutor(6) as pool:
            witnesses = dict(pool.map(witness, needed))
    out = []
    for r in rows:
        if r.get('status') != 'checked':
            continue
        w = witnesses[r['item']]
        decision = base.recorded_decision(r['item'])
        # A run's recorded decision carries no capability_check (it is checked in shadow); live, the fact agent is
        # given the turn's check either way (`apply_fact_check`).
        check = decision.capability_check or CapabilityCheck()
        if 'failed' not in w:
            decision = decision.model_copy(update={'capability_check': check.model_copy(update={
                'uncertain_quotes': w['uncertain'], 'stated_quotes': w['stated']})})
        proposals = proposals_of(r)
        kept = kept_facts(items[r['item']]['prompt'], proposals, decision, policy)
        out.append({**{k: r[k] for k in ('item', 'family', 'model', 'gold_fact')}, 'witness': w,
                    'asked': [f.model_dump() for f in kept.accepted if not f.settled_by_input_check],
                    'said': [f.model_dump() for f in kept.accepted if f.settled_by_input_check],
                    'rejected': [x.rule for x in kept.rejected]})
    dest = HERE / 'live' / out_tag
    dest.mkdir(parents=True, exist_ok=True)
    write_json(dest / 'witness.json', out, exclusive=False)
    print('check failures:', sum('failed' in w for w in witnesses.values()), '/', len(witnesses))


if __name__ == '__main__':
    main(*sys.argv[1:3])
