"""Prize-first entry/selection behavior and deterministic hand correctness."""
import copy
import json
import unittest
from poker_agent_protocol.game import state_from_dict,is_legal
import league

class PrizePrimaryChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bot=league.load_bot(league.ROOT/'bots/codex_empty_bluffer_primary_v1','primary_suite')
        cls.entry=json.loads((league.ROOT/'arena/benchmarks/prize-primary/cheap-entry-case.json').read_text())
        cls.selection=json.loads((league.ROOT/'arena/benchmarks/prize-fusion/stab-case.json').read_text())

    def test_critical_correctness(self):
        cases=json.loads((league.ROOT/'arena/critical_cases.json').read_text())['cases']
        cases+=json.loads((league.ROOT/'arena/public_river_cases.json').read_text())
        for r in league.tactical_checks(self.bot,cases):
            if r['severity']=='block':self.assertTrue(r['passed'],r)

    def test_seek_cheap_low_card_flop(self):
        state=state_from_dict(self.entry);a,_=self.bot.Agent().act(state,b'')
        self.assertEqual(a.kind,'call');self.assertTrue(is_legal(a,state.legal_actions))

    def test_do_not_chase_expensive_low_card_flop(self):
        s=copy.deepcopy(self.entry);s['pot']=230;s['to_call']=210;s['seats'][1][1:3]=[780,220]
        s['history'].append(['raise',1,220,[]]);s['legal_actions']=[['fold',0,0],['call',0,0],['raise',420,1000]]
        self.assertEqual(self.bot.Agent().act(state_from_dict(s),b'')[0].kind,'fold')

    def test_retain_low_card_but_keep_set(self):
        cases=[(['As','Kd','2c'],['Qh','7d','4s'],None,True),
               (['Ks','Kh','2c'],['Kd','Qs','5d'],{'Ks','Kh'},False)]
        for cards,board,wanted,low in cases:
            with self.subTest(cards=cards):
                s=copy.deepcopy(self.selection);s.update(cards=cards,board=board,phase='select',legal_actions=[['select',0,0]])
                state=state_from_dict(s);a=self.bot.select(state,self.bot.fresh_record())
                self.assertTrue(is_legal(a,state.legal_actions))
                kept={c for i,c in enumerate(cards) if i!=a.cards[0]}
                if wanted is not None:self.assertEqual(kept,wanted)
                if low:self.assertIn(cards[a.cards[1]][0],'2345')

if __name__=='__main__':unittest.main()
