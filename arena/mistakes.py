"""Flag unreasonable decisions of the hero (bots/claude_v2): folds of strong hands, big calls with weak hands.
python arena/mistakes.py bots/claude_v2 opp folders... --tables 40"""
import sys, argparse, importlib.util
sys.path.insert(0, 'arena')
from pathlib import Path
from arena import load_agent_class, VARIANT
from poker_engine.table import SitAndGo, TableRules
from poker_engine.variant import load_variant
ap = argparse.ArgumentParser(); ap.add_argument('bots', nargs='+'); ap.add_argument('--tables', type=int, default=40)
args = ap.parse_args()
folders = [Path(b) for b in args.bots]
spec = importlib.util.spec_from_file_location("hero_mod", folders[0] / "agent.py"); H = importlib.util.module_from_spec(spec); spec.loader.exec_module(H)
classes = [H.Agent] + [load_agent_class(f, f.name) for f in folders[1:]]
names = [f.name for f in folders]
rules = TableRules(variant=VARIANT, players=len(folders)); variant = load_variant(VARIANT)
flags = []
for n in range(args.tables):
    rot = n % len(folders); order = [(i + rot) % len(folders) for i in range(len(folders))]
    cl = [classes[i] for i in order]; nm = [names[i] for i in order]
    table = SitAndGo(rules=rules, variant=variant, table_id=f"m{n}", seed=f"mist:{n}")
    agents = [c() for c in cl]; mem = [b""] * len(cl); hero = order.index(0)
    while True:
        st = table.decision()
        if st is None: break
        a, m = agents[st.seat].act(st, mem[st.seat])
        if st.seat == hero and st.phase == "betting":
            my_total = st.seats[hero].stack + st.seats[hero].bet
            if st.board and len(st.cards) == 2:
                an = H.analyze(st.cards, st.board)
                if a.kind == "fold" and an["cls"] >= 4:
                    flags.append(f"t{n} h{st.hand_number} FOLD strong cls={an['cls']} {st.cards} board={st.board} to_call={st.to_call} pot={st.pot} stack={my_total}")
                if a.kind in ("call",) and st.to_call >= 0.4 * my_total and an["cls"] <= 1 and not an["draw"]:
                    flags.append(f"t{n} h{st.hand_number} BIGCALL weak cls={an['cls']} {st.cards} board={st.board} to_call={st.to_call} pot={st.pot} stack={my_total}")
            elif not st.board:
                p = H.score_percentile(H.three_card_score(st.cards)[0])
                if a.kind == "fold" and p <= 0.03:
                    import traceback
                    rec = H.unpack_record(mem[hero]); H.feed(rec, st)
                    try:
                        live=[s.seat for s in st.seats if s.status in ("active","all_in")]
                        print("   pos", H.position_of(st, live, st.seat), "button", st.button, "seat", st.seat, "live", live, "can", [(x.kind) for x in st.legal_actions], "bb", st.blinds.big_blind, "stacks", [(s.seat,s.stack+s.bet,s.status) for s in st.seats])
                        print("   replay decide ->", H.decide(st, rec))
                    except Exception:
                        traceback.print_exc()
                    flags.append(f"t{n} h{st.hand_number} FOLD premium p={p:.3f} {st.cards} to_call={st.to_call} pot={st.pot} stack={my_total} hist={[(e.kind,e.seat,e.amount) for e in st.history if e.kind in ('raise','call')]}")
        mem[st.seat] = m; table.apply(a)
for f in flags[:40]: print(f)
print(len(flags), "flags")
