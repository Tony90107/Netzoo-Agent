"""Synthetic only: never import or open heldout.json."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from plan import digest, jobs, write_json
from run_live import select_jobs, BOOTSTRAP, PYTHON, verify_code
from collect import collect_session, layers, sanitize
from analyze import cost, score, to_review, validate_labels, validate

class HarnessTests(unittest.TestCase):
    def test_job_plan(self):
        items = {f'i{n}': {} for n in range(120)}
        first, second = jobs(items), jobs(items)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 150)
        self.assertEqual(sum(rep == 1 for _, rep in first), 120)
        self.assertEqual(len(set(first)), 150)

    def test_explicit_selection(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 've-tag-live-a-1').mkdir()
            self.assertEqual(select_jobs([('a',1),('b',1)], [], True, root, 'tag'), [('b',1)])
            self.assertEqual(select_jobs([('a',1),('b',1)], ['b:1'], False, root, 'tag'), [('b',1)])
            with self.assertRaises(ValueError): select_jobs([('a',1)], ['a:2'], False, root, 'tag')

    def test_manifest_rejects_mutation_and_outside_files(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/'a.py').write_text('frozen')
            manifest={'base_sha':'a'*40,'files':{'a.py':digest(root/'a.py')}}
            with patch('run_live.subprocess.check_output', side_effect=['a'*40+'\n', b'a.py\0', b'']):
                self.assertEqual(verify_code(root,manifest),'a'*40)
            (root/'a.py').write_text('changed')
            with patch('run_live.subprocess.check_output', side_effect=['a'*40+'\n', b'a.py\0', b'']):
                with self.assertRaises(ValueError): verify_code(root,manifest)
            with patch('run_live.subprocess.check_output', side_effect=['a'*40+'\n', b'other.py\0']):
                with self.assertRaises(ValueError): verify_code(root,manifest)
            with patch('run_live.subprocess.check_output', side_effect=['a'*40+'\n', b'', b'unfrozen.py\0']):
                with self.assertRaises(ValueError): verify_code(root,manifest)

    def test_completeness_and_review_guards(self):
        gold={'words':'a','expect':'needs_fact','by':[],'deciding_fact':'what data'}
        items={'a':{'requirements':[gold]}}
        rows={f's{n}':{'item':'a','rep':n,'layers':[{**gold,'understood':True}],
                      'capture_verified':True,'bad_gate_candidate':True} for n in (1,2)}
        key={f'S{n}':{'session':f's{n}','gold':[gold]} for n in (1,2)}
        labels={c:{'R':['ASKED'],'contradiction':'no'} for c in key}
        checked={c:{**v,'right_question':True,'bad_gate':False,'reason':'verified deciding fact and held plan'} for c,v in labels.items()}
        validate(rows,key,labels,checked,items,repeats=1)
        with self.assertRaises(ValueError): validate(rows,key,labels,{},items,repeats=1)
        with self.assertRaises(ValueError): validate({'s1':rows['s1']},key,labels,checked,items,repeats=1)
        with self.assertRaises(ValueError): validate(rows,key,{'S1':labels['S1']},checked,items,repeats=1)
        bad={**checked,'S1':{**checked['S1'],'right_question':'true'}}
        with self.assertRaises(ValueError): validate(rows,key,labels,bad,items,repeats=1)

    def test_quotes_are_verified_and_not_background(self):
        req = [{'words':'network edges', 'expect':'supported'}]
        for check in [{'requirements':[{'quote':'network edges','kind':'background'}]},
                      {'requirements':[{'quote':'invented network edges','kind':'result'}]}]:
            self.assertFalse(layers('Give network edges', req, check)[0]['understood'])
        self.assertTrue(layers('Give network edges', req, {'requirements':[{'quote':'network edges','kind':'result'}]})[0]['understood'])

    def test_capture_complete_output_run_card_and_tamper(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d) / 've-tag-live-a-1'; folder.mkdir()
            item = {'id':'a','family':'K','form':'two_turn','prompt':'Give network edges',
                    'turns':['Give network edges', 'Use matrix.csv'],
                    'requirements':[{'words':'network edges','expect':'supported','by':['PANDA']}]}
            for n, request in enumerate(item['turns'],1):
                turn = folder / f't{n}'; turn.mkdir()
                (turn/'stdout.txt').write_text('✓ Workflow: PANDA\nNeed matrix.csv\n')
                (turn/'stderr.txt').write_text('warning visible to user\n')
                write_json(turn/'cards.json',[{'headline':'Card is preserved'}])
                session = {'messages':[{'role':'user','content':t} for t in item['turns'][:n]],
                    'plan': {'workflow':'PANDA','steps':[{'arguments':{'expression':'matrix.csv'}}],
                             'decision':{'action':'run_panda','run_verdict':{'verdict':'agrees','results':[{'quote':'network edges','status':'available'}]}}}}
                write_json(turn/'session.json', session)
                (turn/'events.jsonl').write_text(json.dumps({'event_type':'plan.created','payload':{'workflow':'PANDA','steps':[{'arguments':{'expression':'matrix.csv'}}]}})+'\n')
                write_json(turn/'manifest.json',{'turn':n,'request':request,'mode':'--session' if n==1 else '--resume','exit':0,
                    'files':{p.name:digest(p) for p in turn.iterdir()}})
            write_json(folder/'job.json',{'item':'a','rep':1,'session':folder.name,'expected_turns':2,'complete':True,'codes':[0,0]})
            row, body = collect_session(folder,item,1,{'worktree':'/candidate','sha':'abc'})
            self.assertIn('✓ Workflow: PANDA',body); self.assertIn('warning visible',body)
            self.assertIn('Card is preserved',body); self.assertIn('Give network edges',body)
            self.assertIn('matrix.csv',str(row['trace_plans']))
            self.assertTrue(row['capture_verified']); self.assertFalse(row['replayed'])
            (folder/'t2/stdout.txt').write_text('tampered')
            with self.assertRaises(ValueError): collect_session(folder,item,1,{'worktree':'/candidate','sha':'abc'})

    def test_actual_bootstrap_preserves_streams_and_card(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); module = root/'scripts/netzoo_agent_core/engine'; module.mkdir(parents=True)
            (module/'machine.py').write_text('class ConversationMachine:\n    def _reply_card(self,result,task): return {"headline":"visible card"}\n')
            (root/'scripts/netzoo_agent.py').write_text('import sys\nfrom netzoo_agent_core.engine.machine import ConversationMachine\nprint("✓ Workflow: PANDA")\nprint("stderr marker",file=sys.stderr)\nConversationMachine()._reply_card({},"q")\n')
            import os
            result = subprocess.run([PYTHON,'-c',BOOTSTRAP],cwd=root,capture_output=True,text=True,
                                    env={**os.environ,'M3_CARD_CAPTURE':str(root/'cards.json')})
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('✓ Workflow: PANDA',result.stdout); self.assertIn('stderr marker',result.stderr)
            self.assertEqual(json.loads((root/'cards.json').read_text()),[{'headline':'visible card'}])

    def test_blind_redaction(self):
        text = sanitize('secret12345 sk-or-v1-abcdefghijklmn sid /candidate hash', 'sid','/candidate','hash',['secret12345'])
        for x in ['secret12345','abcdefghijklmn','sid','/candidate','hash']: self.assertNotIn(x,text)

    def test_costs_and_primary_only_score(self):
        self.assertEqual([cost({'expect':'not_supported'},x) for x in ['NOT_GIVEN','ASKED','PARTLY','GIVEN']],[0,1,2,3])
        rows={}; key={}; labels={}; checked={}
        for n,(expect,value) in enumerate([('not_supported','NOT_GIVEN'),('supported','GIVEN'),('needs_fact','ASKED')]):
            sid=f's{n}';code=f'S{n}'
            rows[sid]={'item':sid,'rep':1,'family':'P','action':'no_tool','check_calls':[['nemotron','success']],
                       'layers':[{'expect':expect,'understood':True}], 'errors':[]}
            key[code]={'session':sid};labels[code]={'R':[value],'contradiction':'no'}
        checked['S2']={**labels['S2'],'right_question':True,'reason':'deciding fact'}
        rows['repeat']={**rows['s1'],'rep':2};key['R']={'session':'repeat'};labels['R']={'R':['NOT_GIVEN'],'contradiction':'no'}
        result=score(rows,key,labels,checked)
        self.assertEqual(result['score'],100);self.assertTrue(result['accepted'])
        self.assertEqual(result['repeat_agreement']['rate'],0)
        self.assertEqual(result['counts']['sessions'],3)
        self.assertIn('R',to_review(rows,key,labels))
        with self.assertRaises(ValueError): validate_labels(rows,key,checked)

if __name__ == '__main__': unittest.main()
