"""Verify audit reproducibility and source/data integrity; offline, no production imports."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
WT = HERE.parents[2]
rebuilt = Path(sys.argv[1]).resolve()
command = [sys.executable, '-I', str(HERE/'audit.py'), '--rebuilt', str(rebuilt)]
names = ['inventory.json', 'records.json', 'summary.json', 'manifest.json',
         'rebuilt-metrics.json', 'supplemental-veto.json', 'AUDIT.md']
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
subprocess.run(command, cwd=WT, check=True, stdout=subprocess.DEVNULL)
before = {name: sha(HERE/name) for name in names}
subprocess.run(command, cwd=WT, check=True, stdout=subprocess.DEVNULL)
after = {name: sha(HERE/name) for name in names}
assert before == after, 'Repeated generation differs'
m = json.loads((HERE/'manifest.json').read_text())
for path, meta in m['inputs'].items():
    assert sha(Path(path)) == meta['sha256'], path
for path, digest in m['source_files'].items():
    assert sha(Path(path)) == digest, path
assert sha(HERE/'audit.py') == m['audit_script_sha256']
assert not m['missing_source_references']
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=WT, text=True).strip() == m['code_head']
tracked = subprocess.check_output(['git', 'status', '--short', '--untracked-files=no'], cwd=WT, text=True)
assert not tracked.strip(), tracked
rs = json.loads((HERE/'records.json').read_text())
s = json.loads((HERE/'summary.json').read_text())
assert len(rs) == 999 == len({r['record_id'] for r in rs})
assert len({r['content_key'] for r in rs}) == 979
assert sum(bool(r['gold']) for r in rs) == 189
assert len({r['gold']['id'] for r in rs if r['gold']}) == 189
assert sum(not r['notes']['task_quotes_all_matched'] for r in rs) == 6
for category, row in s['all_events'].items():
    eligible = [r for r in rs if r['signals'][category]['eligible']]
    assert row['eligible'] == len(eligible)
    assert row['flagged'] == sum(r['signals'][category]['flagged'] for r in eligible)
    assert row['gold_eligible']['n'] == row['gold_flagged']['n'] + row['gold_unflagged']['n']
    assert row['gold_eligible']['wrong'] == row['gold_flagged']['wrong'] + row['gold_unflagged']['wrong']
    for r in eligible:
        assert not r['signals'][category]['flagged'] or r['signals'][category]['details']
assert len(json.loads((HERE/'supplemental-veto.json').read_text())) == 19
result = {'status': 'passed', 'code_head': m['code_head'],
    'repeated_generation_identical': True, 'output_sha256': after,
    'input_files_unchanged': len(m['inputs']), 'source_files_unchanged': len(m['source_files']),
    'source_references_resolved': True, 'tracked_tree_unchanged': True,
    'count_and_gold_integrity': True, 'no_production_tests_run': True,
    'command': command, 'verify_script_sha256': sha(Path(__file__))}
(HERE/'verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('output_sha256','command')}, ensure_ascii=False))
