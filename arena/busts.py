"""Print how a bot busts: python arena/busts.py HERO_FOLDER other folders... [--before 80] [--tables 40]"""
import sys, argparse
sys.path.insert(0, 'arena')
from pathlib import Path
from arena import load_agent_class, VARIANT
from poker_engine.table import SitAndGo, TableRules
from poker_engine.variant import load_variant
ap = argparse.ArgumentParser(); ap.add_argument('bots', nargs='+'); ap.add_argument('--before', type=int, default=80); ap.add_argument('--tables', type=int, default=40); ap.add_argument('--max', type=int, default=25)
args = ap.parse_args()
folders = [Path(b) for b in args.bots]
classes = [load_agent_class(f, f.name) for f in folders]
names = [f.name for f in folders]
rules = TableRules(variant=VARIANT, players=len(folders)); variant = load_variant(VARIANT)
shown = 0; total = 0
for n in range(args.tables):
    rot = n % len(folders)
    order = [(i + rot) % len(folders) for i in range(len(folders))]
    cl = [classes[i] for i in order]; nm = [names[i] for i in order]
    table = SitAndGo(rules=rules, variant=variant, table_id=f"b{n}", seed=f"busts:{n}")
    agents = [c() for c in cl]; mem = [b""] * len(cl)
    while True:
        st = table.decision()
        if st is None: break
        a, m = agents[st.seat].act(st, mem[st.seat]); mem[st.seat] = m; table.apply(a)
    hero = order.index(0)
    for e in table.log:
        if e['stacks_before'][hero] > 0 and e['stacks_after'][hero] == 0:
            total += 1
            if e['hand'] < args.before and shown < args.max:
                line = []
                for ev in e['events']:
                    k = ev['kind']
                    if k == 'board': line.append('|' + ''.join(ev['cards']))
                    elif k in ('raise','call','fold','check'): line.append(f"{nm[ev['seat']][:5]}{ev['seat']}:{k[0]}{ev.get('amount','')}")
                    elif k == 'show': line.append(f"{nm[ev['seat']][:5]}{ev['seat']}:show{''.join(ev.get('cards',[]))}")
                    elif k == 'reveal': line.append(f"{nm[ev['seat']][:5]}{ev['seat']}:rev{''.join(ev.get('cards',[]))}")
                alive = sum(1 for x in e['stacks_before'] if x > 0)
                print(f"t{n} h{e['hand']} {e['blinds'][:2]} {alive}p hero=seat{hero} {''.join(e['cards'][hero])} stack={e['stacks_before'][hero]}")
                print("   " + ' '.join(line)); shown += 1
print(f"{total} busts in {args.tables} tables")
