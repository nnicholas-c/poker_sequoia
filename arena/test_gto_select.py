"""Targeted regressions for the experimental discard patch, not promotion evidence."""
import json
import unittest
from poker_agent_protocol.game import state_from_dict
import league

class SelectionChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bot = league.load_bot(league.ROOT/'bots/codex_gto_refined', 'gto_select_test')
        cls.template = json.loads((league.ROOT/'arena/critical_cases.json').read_text())['cases'][-1]['state']

    def test_pairs_and_draws(self):
        cases = [
            ('9d 9h 2d', '7d 5d Qh', {'9d','9h'}),
            ('Ts Qc 9s', '7h 4c 8s', {'Ts','9s'}),
            ('3s 5d 3d', 'Ad Kc 2d', {'5d','3d'}),
        ]
        for cards, board, expected in cases:
            with self.subTest(cards=cards, board=board):
                state = dict(self.template, cards=cards.split(), board=board.split(),
                             phase='select', legal_actions=[['select',0,0]])
                action = self.bot.select(state_from_dict(state), self.bot.fresh_record())
                kept = {c for i,c in enumerate(cards.split()) if i != action.cards[0]}
                self.assertEqual(kept, expected)

if __name__ == '__main__': unittest.main()
