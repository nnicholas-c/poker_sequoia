"""Where do chips come from? Per team: net big blinds per 100 hands by how the hand was played
(preflop role x how it ended). Compares us with the best teams across one or more histories.
python arena/where_chips.py H1.gz H2.gz ... --teams "Team 72" AZ "Always Folds" "2 Curry"
"""
import argparse, collections, gzip, json, sys
sys.path.insert(0, __import__('os').path.dirname(__file__))
from history_report import load

ap = argparse.ArgumentParser(); ap.add_argument('paths', nargs='+'); ap.add_argument('--teams', nargs='*', default=[])
args = ap.parse_args()
agg = collections.defaultdict(lambda: collections.defaultdict(lambda: [0.0, 0]))
hands_n = collections.Counter()
me_name = None
for path in args.paths:
    header, tables = load(path)
    teams = {e['entry_id']: e['team_name'] for e in header['entries']}
    me = teams[header['you']]; me_name = me
    want = set(args.teams) | {me}
    for t, own in tables:
        names = [teams.get(e, '?') for e in t['seats']]
        for h in t['hands']:
            bb = h['blinds'][1]
            for s, n in enumerate(names):
                if n not in want or h['stacks_before'][s] == 0:
                    continue
                key = n if n != me else 'US'
                hands_n[key] += 1
                delta = (h['stacks_after'][s] - h['stacks_before'][s]) / bb
                street = 0; pre_raises = 0; role = 'fold/walk'; ended = 'pre'
                folded_at = None; showed = False; vol = False
                for ev in h['events']:
                    k = ev['kind']
                    if k == 'board':
                        street += 1; continue
                    if ev.get('seat') != s:
                        if k == 'raise' and street == 0: pre_raises += 1
                        continue
                    if street == 0 and k == 'raise':
                        role = 'open' if pre_raises == 0 else ('3bet+' if pre_raises == 1 else '4bet+')
                        if ev['amount'] >= 0.9 * h['stacks_before'][s]: role = 'jam'
                        pre_raises += 1; vol = True
                    elif street == 0 and k == 'call':
                        if role in ('fold/walk',):
                            role = 'limp' if pre_raises == 0 else 'call'
                        vol = True
                    elif k == 'fold':
                        folded_at = street
                    elif k == 'show':
                        showed = True
                if role == 'fold/walk' and delta != 0:
                    role = 'blinds'
                if showed: ended = 'showdown'
                elif folded_at is not None: ended = 'fold@' + 'pftr'[min(folded_at, 3)]
                elif street == 0: ended = 'won pre'
                else: ended = 'won post'
                agg[key][(role, ended)][0] += delta
                agg[key][(role, ended)][1] += 1
keys = ['US'] + [t for t in args.teams if t in agg]
cats = sorted({c for k in keys for c in agg[k]}, key=lambda c: -abs(agg['US'][c][0]))
print(f"{'role':8s} {'ended':9s} " + " ".join(f"{k[:12]:>13s}" for k in keys))
print("           (bb per 100 hands dealt; freq %)")
for c in cats:
    row = []
    for k in keys:
        tot, n = agg[k][c]
        row.append(f"{100 * tot / max(1, hands_n[k]):7.1f} {100 * n / max(1, hands_n[k]):4.1f}%")
    print(f"{c[0]:8s} {c[1]:9s} " + " ".join(f"{r:>13s}" for r in row))
print(f"{'TOTAL':18s} " + " ".join(f"{100 * sum(v[0] for v in agg[k].values()) / max(1, hands_n[k]):13.1f}" for k in keys))
