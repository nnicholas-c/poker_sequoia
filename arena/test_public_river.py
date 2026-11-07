import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'arena'))
import league
import archetypes
from poker_agent_protocol.game import state_from_dict

class PublicRiverTests(unittest.TestCase):
    def test_provable_outcomes(self):
        cases = json.loads((ROOT / 'arena/public_river_cases.json').read_text())
        for name in ('codex_nc_v7_adapted', 'codex_merge_river_guard'):
            module = league.load_bot(ROOT / 'bots' / name, 'test_' + name)
            for result in league.tactical_checks(module, cases):
                with self.subTest(bot=name, case=result['case']):
                    self.assertTrue(result['passed'], result)

    def test_small_blind_position_survives_folds(self):
        cases = json.loads((ROOT / 'arena/critical_cases.json').read_text())['cases']
        state = copy.deepcopy(next(c['state'] for c in cases if c['id'] == 'small-blind-premium-after-folds'))
        state['cards'] = ['As', 'Jd', '2c']
        # This hand belongs in the fixture's late range, outside its early range.
        agent = archetypes.make_agent(open_w=.17, late_mult=1.7)()
        action, _ = agent.act(state_from_dict(state), b'')
        self.assertEqual(action.kind, 'raise')

if __name__ == '__main__':
    unittest.main()
