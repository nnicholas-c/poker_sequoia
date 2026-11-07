"""Critical hands, exact cash transition, and a large-pot regression."""
import copy
import json
import unittest
from poker_agent_protocol.game import state_from_dict
import league

class SurvivalChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bot = league.load_bot(league.ROOT/'bots/codex_survival_switch_v1', 'survival_suite')
        cls.cases = json.loads((league.ROOT/'arena/critical_cases.json').read_text())['cases']
        cls.public = json.loads((league.ROOT/'arena/public_river_cases.json').read_text())

    def test_critical_hands(self):
        for r in league.tactical_checks(self.bot, self.cases + self.public):
            if r['severity']=='block': self.assertTrue(r['passed'], r)

    def test_cash_boundary_includes_folded_players(self):
        state=copy.deepcopy(self.cases[0]['state'])
        state['config']['payouts']=[50,30,20]
        # Keep all seats constant: players remaining, not active opponents in
        # this hand, controls the transition.
        for remaining,expected in [(8,True),(4,True),(3,False),(2,False)]:
            state['players_remaining']=remaining
            self.assertEqual(self.bot.survival_mode(state_from_dict(state)),expected)
        state['config']['payouts']=[70,30]
        state['players_remaining']=3
        self.assertTrue(self.bot.survival_mode(state_from_dict(state)))

    def test_deep_pair_after_reraise_and_barrel(self):
        case=json.loads((league.ROOT/'arena/benchmarks/survival-switch/regression-case.json').read_text())
        state=state_from_dict(case['state'])
        parent=league.load_bot(league.ROOT/'bots/gto_final_reference','survival_parent_test')
        self.assertEqual(parent.Agent().act(state,b'')[0].kind,'call')
        self.assertEqual(self.bot.Agent().act(state,b'')[0].kind,'fold')

if __name__=='__main__':unittest.main()
