"""Verify the frozen offline replay, schema delta, and evidence hashes. No model calls."""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
WT = HERE.parents[2]
BASE = 'cf31e7f3c6bf48f96553601eb292c66e272780f5'
sys.path.insert(0,str(WT/'scripts'))
import netzoo_agent_core.contracts as contracts  # noqa: E402


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pins(source):
    tree = ast.parse(source)
    return next(ast.literal_eval(node.value) for node in tree.body if isinstance(node,ast.Assign)
                and any(isinstance(t,ast.Name) and t.id=='SCHEMA_DIGESTS' for t in node.targets))


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def main():
    command = [sys.executable,'-I',str(HERE/'replay.py')]
    outputs = ['replay-summary.json','changed.json','core-replay.json','manifest.json']
    before = {name:sha(HERE/name) for name in outputs}
    subprocess.run(command,cwd=WT,check=True,stdout=subprocess.DEVNULL)
    after = {name:sha(HERE/name) for name in outputs}
    assert before==after, 'offline replay not reproducible'
    manifest = json.loads((HERE/'manifest.json').read_text())
    for group in ('input_sha256','source_sha256'):
        for path,expected in manifest[group].items():
            assert sha(Path(path))==expected,path
    summary = json.loads((HERE/'replay-summary.json').read_text())
    assert summary['counts']['readings']==summary['counts']['core_replayed']==979
    assert not summary['skipped']
    rows = json.loads((HERE/'core-replay.json').read_text())
    assert all(r['before']==r['after'] for r in rows if r['gold'])
    changes = json.loads((HERE/'changed.json').read_text())
    changed_calls = [r for r in changes if r['before_core']['kind']!=r['after_core']['kind']]
    assert len(changed_calls)==2
    for row in changed_calls:
        assert (row['before_core']['kind'],row['after_core']['kind'])==('DO','ASK')
        assert row['after_authority']=={'action':'no_tool','should_execute':False,'execution_requested':False}
        assert row['after_view']['kind']=='ask_facts'
    original = subprocess.check_output(['git','show',BASE+':tests/test_contracts_package.py'],cwd=WT,text=True)
    baseline = pins(original)
    current = pins((WT/'tests/test_contracts_package.py').read_text())
    schema_changes = {}
    for name,expected in baseline.items():
        schema = getattr(contracts,name).model_json_schema()
        actual = digest(schema)
        assert actual==current[name],name
        if expected==actual:
            continue
        assert name=='TaskDecision'
        schema['$defs']['FactConflict']['properties']['reason']['enum'].remove('count_reading_precedence')
        assert digest(schema)==expected,'Unexpected additional schema change'
        schema_changes[name]={'before':expected,'after':actual,'only_delta':
            'FactConflict.reason adds count_reading_precedence (code-owned provenance)'}
    (HERE/'schema-change.json').write_text(json.dumps(schema_changes,indent=2)+'\n')
    result = {'status':'passed','frozen_replay_identical':True,'source_and_input_hashes_verified':True,
              'gold_baseline_core_kind_unchanged':189,'schema_only_expected_enum_changed':True,
              'changed_asks_hold_execution':2,'output_sha256':after,'verify_script_sha256':sha(Path(__file__))}
    (HERE/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':
    main()
