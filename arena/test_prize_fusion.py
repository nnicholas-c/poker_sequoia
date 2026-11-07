"""Protect survival/correctness and verify bounded Empty Bluffer opportunities."""
import copy
import json
import unittest
from poker_agent_protocol.game import state_from_dict, is_legal
import league

class ZeroRandom:
    def random(self): return 0.0

class PrizeFusionChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bot=league.load_bot(league.ROOT/'bots/codex_survival_bluffer_v1','prize_suite')
        cls.fixture=json.loads((league.ROOT/'arena/benchmarks/prize-fusion/stab-case.json').read_text())

    def stab(self,state,station=False):
        return self.bot.empty_bluffer_stab(state_from_dict(state),station,ZeroRandom())

    def test_critical_hands_and_survival_regression(self):
        cases=json.loads((league.ROOT/'arena/critical_cases.json').read_text())['cases']
        cases+=json.loads((league.ROOT/'arena/public_river_cases.json').read_text())
        cases+=[json.loads((league.ROOT/'arena/benchmarks/survival-switch/regression-case.json').read_text())]
        for r in league.tactical_checks(self.bot,cases):
            if r['severity']=='block':self.assertTrue(r['passed'],r)

    def test_small_legal_stab_when_checked_to(self):
        state=state_from_dict(self.fixture);a=self.stab(self.fixture)
        self.assertEqual((a.kind,a.amount),('raise',40))
        self.assertTrue(is_legal(a,state.legal_actions))
        self.assertIsNone(self.stab(self.fixture,station=True))

    def test_no_stab_when_prize_impossible_or_already_eligible(self):
        s=copy.deepcopy(self.fixture);s['seats'][1][3]='all_in';s['seats'][1][1]=0
        self.assertIsNone(self.stab(s))
        s=copy.deepcopy(self.fixture);s['seats'][0][4]=['7d']
        self.assertIsNone(self.stab(s))
        s=copy.deepcopy(self.fixture);s['history'].append(['raise',0,40,[]])
        self.assertIsNone(self.stab(s))
        s=copy.deepcopy(self.fixture);s['to_call']=20
        self.assertIsNone(self.stab(s))

    def test_stack_budget_and_paid_place_transition(self):
        s=copy.deepcopy(self.fixture);s['history']=s['history'][:-1]
        self.assertIsNone(self.stab(s))
        s['players_remaining']=3
        self.assertIsNotNone(self.stab(s))
        s=copy.deepcopy(self.fixture);s['pot']=240
        self.assertIsNone(self.stab(s))  # 80 > six percent of 1000
        s['players_remaining']=3
        self.assertEqual(self.stab(s).amount,80)
        s['pot']=600
        self.assertIsNone(self.stab(s))
        s=copy.deepcopy(self.fixture);s['legal_actions']=[['check',0,0],['raise',20,40]]
        self.assertIsNone(self.stab(s))  # never use the prize overlay to shove

    def test_low_card_exposure_without_splitting_strong_hands(self):
        cases=[(['2c','2d','As'],['2h','9s','Kh'],{'2c','2d'}),
               (['Ac','Kd','2c'],['Ah','9s','6d'],{'Ac','Kd'})]
        for cards,board,expected in cases:
            with self.subTest(cards=cards):
                s=copy.deepcopy(self.fixture);s.update(cards=cards,board=board,phase='select',legal_actions=[['select',0,0]])
                a=self.bot.select(state_from_dict(s),self.bot.fresh_record())
                kept={c for i,c in enumerate(cards) if i!=a.cards[0]}
                self.assertEqual(kept,expected)
                if any(c[0] in '2345' for c in kept):self.assertIn(cards[a.cards[1]][0],'2345')

if __name__=='__main__':unittest.main()
