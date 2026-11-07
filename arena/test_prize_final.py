"""Final prize-source correctness and verified short-stack entry behavior."""
import copy
import json
import unittest
from poker_agent_protocol.game import state_from_dict
import league

class PrizeFinalChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.final=league.load_bot(league.ROOT/'bots/codex_empty_bluffer_final','prize_final_suite')
        cls.previous=league.load_bot(league.ROOT/'bots/codex_empty_bluffer_primary_v1','prize_previous_suite')
        cls.entry=json.loads((league.ROOT/'arena/benchmarks/prize-primary/cheap-entry-case.json').read_text())

    def test_critical_hands(self):
        cases=json.loads((league.ROOT/'arena/critical_cases.json').read_text())['cases']
        cases+=json.loads((league.ROOT/'arena/public_river_cases.json').read_text())
        for r in league.tactical_checks(self.final,cases):
            if r['severity']=='block':self.assertTrue(r['passed'],r)

    def test_qualifying_entry_depths(self):
        for bb,old,new in [(6,'fold','fold'),(10,'fold','call'),(16,'call','call')]:
            with self.subTest(stack_bb=bb):
                s=copy.deepcopy(self.entry);s['seats'][0][1]=20*bb-10;state=state_from_dict(s)
                self.assertEqual(self.previous.Agent().act(state,b'')[0].kind,old)
                self.assertEqual(self.final.Agent().act(state,b'')[0].kind,new)

if __name__=='__main__':unittest.main()
