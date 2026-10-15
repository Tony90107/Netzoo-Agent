"""Synthetic checks of the core-judgment scoring; never reads items.json or live outputs."""
import unittest
from analyze import outcome, needs_field

def item(cls, workflows=('PANDA',)): return {'class': cls, 'workflows': list(workflows)}
def label(decision, workflows=(), **extra): return {'decision': decision, 'workflows': list(workflows), **extra}

class Outcomes(unittest.TestCase):
    def test_do(self):
        self.assertEqual(outcome(item('do'), label('DOES', ['PANDA'])), ('correct', 0))
        self.assertEqual(outcome(item('do'), label('DOES', ['PUMA'])), ('wrong_workflow', 2))
        self.assertEqual(outcome(item('do', ['PANDA', 'LIONESS-PANDA']), label('OPTIONS', ['PANDA', 'LIONESS-PANDA'])), ('correct', 0))
        self.assertEqual(outcome(item('do'), label('OPTIONS', ['PANDA', 'PUMA'])), ('needless_choice', 1))
        self.assertEqual(outcome(item('do'), label('ASKS')), ('needless_ask', 1))
        self.assertEqual(outcome(item('do'), label('DECLINES')), ('false_refusal', 2))
        self.assertEqual(outcome(item('do', ['LIONESS-PANDA']), label('DOES', ['lioness panda'])), ('correct', 0))

    def test_dont(self):
        self.assertEqual(outcome(item('dont'), label('DECLINES', ['OTTER'])), ('correct', 0))
        self.assertEqual(outcome(item('dont'), label('OPTIONS', ['PANDA', 'PUMA'])), ('false_accept', 3))
        self.assertEqual(outcome(item('dont'), label('PARTLY', ['PANDA'])), ('partly_accept', 2))
        self.assertEqual(outcome(item('dont'), label('ASKS')), ('undecided', 1))

    def test_ask_and_vague(self):
        self.assertEqual(outcome(item('ask'), label('ASKS', core_question=True)), ('correct', 0))
        self.assertEqual(outcome(item('ask'), label('ASKS', core_question=False)), ('wrong_question', 1))
        self.assertEqual(outcome(item('ask'), label('DOES', ['PANDA'], states_condition=True)), ('committed_stating_condition', 1))
        self.assertEqual(outcome(item('ask'), label('DECLINES')), ('refused_without_asking', 2))
        checkable = {**item('ask'), 'file_checkable': True}
        self.assertEqual(outcome(checkable, label('DOES', ['PANDA'], states_condition=True)), ('correct', 0))
        self.assertEqual(outcome(checkable, label('DOES', ['PANDA'], states_condition=False)), ('committed_without_asking', 2))
        self.assertEqual(outcome(item('vague'), label('OPTIONS', ['PANDA', 'PUMA'], core_question=True)), ('correct', 0))
        self.assertEqual(outcome(item('vague'), label('DOES', ['PANDA'], states_condition=True)), ('committed_without_asking', 2))

    def test_adjudication_fields(self):
        self.assertEqual(needs_field(item('ask'), label('ASKS')), 'core_question')
        self.assertEqual(needs_field(item('vague'), label('OPTIONS')), 'core_question')
        self.assertEqual(needs_field(item('ask'), label('DOES')), 'states_condition')
        self.assertIsNone(needs_field(item('vague'), label('DOES')))
        self.assertIsNone(needs_field(item('do'), label('ASKS')))




class CoreScoring(unittest.TestCase):
    def test_core_outcomes(self):
        from score_core import outcome as core
        do, dont, ask, vague = (item(c) for c in ('do', 'dont', 'ask', 'vague'))
        self.assertEqual(core(do, {'kind': 'DO', 'workflows': ['PANDA']}), ('correct', 0))
        self.assertEqual(core(do, {'kind': 'DO', 'workflows': ['PANDA', 'OTTER']}), ('extra_options', 1))
        self.assertEqual(core(do, {'kind': 'CLARIFY'}), ('needless_question', 1))
        self.assertEqual(core(dont, {'kind': 'DO', 'workflows': ['PANDA']}), ('false_accept', 3))
        self.assertEqual(core(dont, {'kind': 'DO', 'workflows': ['PANDA'], 'partial': True}), ('partly_accept', 2))
        self.assertEqual(core(ask, {'kind': 'ASK'}, True), ('correct', 0))
        self.assertEqual(core(ask, {'kind': 'ASK'}, False), ('wrong_fact', 1))
        self.assertEqual(core(ask, {'kind': 'CLARIFY'}), ('wrong_question_kind', 1))
        self.assertEqual(core(vague, {'kind': 'CLARIFY'}), ('correct', 0))
        self.assertEqual(core(vague, {'kind': 'DO', 'workflows': ['PANDA']}), ('committed_without_asking', 2))

    def test_a_file_checkable_ask_settled_by_the_input_check_is_correct(self):
        from score_core import outcome as core
        checkable = {**item('ask'), 'file_checkable': True}
        settled = {'kind': 'DO', 'workflows': ['OTTER'], 'facts': [{'settled_by_input_check': True}]}
        self.assertEqual(core(checkable, settled, True), ('correct', 0))
        self.assertEqual(core(checkable, settled, False), ('committed_without_asking', 2))
        self.assertEqual(core(item('ask'), settled, True), ('committed_without_asking', 2))

    def test_bench_excludes_the_seen_items(self):
        from plan import DEV, jobs
        self.assertEqual([k for k, _ in jobs({k: {} for k in ('C01', 'C04', 'C05')})], ['C04'])
        self.assertEqual(DEV, {'C01', 'C02', 'C03', 'C05'})

if __name__ == '__main__': unittest.main()
