"""Small invariants that protect shared comparisons, not bot strategy tests."""
import json
import tempfile
import unittest
from pathlib import Path

import league


class LeagueChecks(unittest.TestCase):
    def test_frozen_assets_survive_live_edits(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory);live=base/'live';live.mkdir()
            (live/'agent.py').write_text('class Agent: pass\n')
            (live/'lookup.bin').write_bytes(b'first table')
            frozen=base/'frozen';manifest=league.snapshot(live,frozen)
            (live/'lookup.bin').write_bytes(b'replacement table')
            self.assertEqual((frozen/'lookup.bin').read_bytes(),b'first table')
            self.assertEqual(manifest['files'],league.fingerprints(frozen))
            self.assertNotEqual(manifest['files'],league.fingerprints(live))

    def test_silent_fallback_is_rejected(self):
        cases=json.loads((league.ROOT/'arena/critical_cases.json').read_text())['cases']
        case=next(c for c in cases if c['id']=='monster-570')
        bot=league.load_bot(league.ROOT/'bots/claude_v1','known_bad')
        result=league.tactical_checks(bot,[case])[0]
        self.assertFalse(result['passed'])
        self.assertEqual(result['action'],'fold')
        self.assertTrue(any('TypeError' in x for x in result['swallowed_exceptions']))

    def test_current_bot_handles_nuts_and_known_defeat(self):
        cases=json.loads((league.ROOT/'arena/critical_cases.json').read_text())['cases']
        cases=[c for c in cases if c['id'] in ('monster-570','exposed-card-defeat')]
        bot=league.load_bot(league.ROOT/'bots/kevin1','known_good')
        for result in league.tactical_checks(bot,cases):
            self.assertTrue(result['passed'],result)


if __name__=='__main__':unittest.main()
