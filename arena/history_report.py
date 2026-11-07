#!/usr/bin/env python3
"""Report on a platform hand history (hands-*.jsonl.gz): how we did, the field leaderboard
seen from our tables, every opponent's style fingerprint, and how we busted.

    python arena/history_report.py path/to/hands.jsonl.gz [--top 25] [--busts 12] [--team NAME]

Standard library only. Writes nothing; prints a report.
"""

import argparse
import collections
import gzip
import json
import statistics
from pathlib import Path

RANKS = "23456789TJQKA"


def load(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        lines = f.read().splitlines()
    header = json.loads(lines[0])
    tables = []
    for i in range(1, len(lines) - 1, 2):
        table = json.loads(lines[i])
        own = json.loads(lines[i + 1])["you"]
        tables.append((table, own))
    return header, tables


def places_from_table(table):
    """Finishing place per seat (1 = winner), ties share."""
    hands = table["hands"]
    n = len(table["seats"])
    bust_hand = {}
    for h in hands:
        for s, (b, a) in enumerate(zip(h["stacks_before"], h["stacks_after"])):
            if b > 0 and a == 0:
                bust_hand[s] = (h["hand"], b)
    final = hands[-1]["stacks_after"]
    # survivors ranked by final stack; busted ranked by (bust hand desc, stack before desc)
    order = []
    for s in range(n):
        if s in bust_hand:
            order.append((0, bust_hand[s][0], bust_hand[s][1], s))
        else:
            order.append((1, final[s], 0, s))
    order.sort(reverse=True)
    place = {}
    for i, (_, _, _, s) in enumerate(order):
        place[s] = i + 1
    return place, bust_hand, len(hands)


def icm_points(table):
    """Points per seat from the engine's own equity_after of the last hand (handles the cap and ties)."""
    last = table["hands"][-1]
    return last.get("equity_after") or [0.0] * len(table["seats"])


class Style:
    __slots__ = ("hands", "vpip", "pfr", "limp", "allin_pre", "fto_ch", "fto", "threebet", "pbets", "pcalls",
                 "pfolds", "pchecks", "cbet_ch", "cbet", "showdowns", "bluff_shows", "exp_low", "exp_high",
                 "exp_pairb", "exp_total", "wins_no_sd", "points", "tables", "places", "bust_hands", "auto")

    def __init__(self):
        for k in self.__slots__:
            setattr(self, k, 0)
        self.points = []
        self.places = collections.Counter()
        self.bust_hands = []


def analyze_table(table, own, styles, teams):
    seats = table["seats"]
    n = len(seats)
    names = [teams.get(e, e[:8]) for e in seats]
    place, bust_hand, nhands = places_from_table(table)
    pts = icm_points(table)
    for s in range(n):
        st = styles[names[s]]
        st.tables += 1
        st.points.append(pts[s])
        st.places[place[s]] += 1
        st.bust_hands.append(bust_hand[s][0] if s in bust_hand else nhands + 1)
    for h in table["hands"]:
        board = []
        street = 0
        pre_raises = 0
        aggressor = None
        acted_vpip = set()
        acted_pfr = set()
        fto_seen = set()
        allin_seen = set()
        street_bet = False
        cbet_pending = False
        exposed = {}
        river_bettors = set()
        folded = set()
        in_hand = [s for s in range(n) if h["stacks_before"][s] > 0]
        for s in in_hand:
            styles[names[s]].hands += 1
        shown = {}
        for ev in h["events"]:
            k = ev["kind"]
            s = ev.get("seat")
            if k == "board":
                board += ev["cards"]
                street += 1
                street_bet = False
                if street == 1 and aggressor is not None:
                    styles[names[aggressor]].cbet_ch += 1
                    cbet_pending = True
                continue
            if s is None:
                continue
            st = styles[names[s]]
            if k == "raise":
                if street == 0:
                    if s not in acted_vpip:
                        st.vpip += 1
                        acted_vpip.add(s)
                    if s not in acted_pfr:
                        st.pfr += 1
                        acted_pfr.add(s)
                    if pre_raises >= 1 and s not in fto_seen:
                        st.fto_ch += 1
                        fto_seen.add(s)
                        st.threebet += 1
                    pre_raises += 1
                    aggressor = s
                    if ev["amount"] >= 0.9 * h["stacks_before"][s] and s not in allin_seen:
                        st.allin_pre += 1
                        allin_seen.add(s)
                else:
                    st.pbets += 1
                    if street == 1 and cbet_pending and s == aggressor and not street_bet:
                        st.cbet += 1
                        cbet_pending = False
                    if street == 3:
                        river_bettors.add(s)
                    street_bet = True
            elif k == "call":
                if street == 0:
                    if s not in acted_vpip:
                        st.vpip += 1
                        acted_vpip.add(s)
                    if pre_raises == 0:
                        st.limp += 1
                    elif s not in fto_seen:
                        st.fto_ch += 1
                        fto_seen.add(s)
                else:
                    st.pcalls += 1
            elif k == "check":
                if street >= 1:
                    st.pchecks += 1
                if street == 1 and cbet_pending and s == aggressor:
                    cbet_pending = False
            elif k == "fold":
                folded.add(s)
                if street == 0:
                    if pre_raises >= 1 and s not in fto_seen:
                        st.fto_ch += 1
                        st.fto += 1
                        fto_seen.add(s)
                else:
                    if street_bet:
                        st.pfolds += 1
            elif k == "reveal":
                c = ev["cards"][0]
                exposed[s] = c
                st.exp_total += 1
                if c[0] in [b[0] for b in board[:3]]:
                    st.exp_pairb += 1
            elif k == "show":
                cards = ev.get("cards", [])
                if len(cards) == 2:
                    st.showdowns += 1
                    shown[s] = cards
                    e = exposed.get(s)
                    if e in cards:
                        hidden = cards[0] if cards[1] == e else cards[1]
                        if RANKS.index(hidden[0]) > RANKS.index(e[0]):
                            st.exp_low += 1
                        elif RANKS.index(hidden[0]) < RANKS.index(e[0]):
                            st.exp_high += 1
            elif k == "win":
                if not shown and s is not None:
                    st.wins_no_sd += 1
    # automatic (platform-played) actions for us
    styles[teams.get(seats[own["seat"]], "?")].auto += len(own["automatic"])


def pct(a, b):
    return 100.0 * a / b if b else 0.0


def profile_team(tables, teams, T):
    """Sizing and position profile of one team (open size, 3-bet size, bet sizes, VPIP by position)."""
    opens, threebets, shove_bb = [], [], []
    bet_fracs = collections.defaultdict(list)
    pos_vpip, pos_hands = collections.Counter(), collections.Counter()
    cold_calls = limps = 0
    for table, own in tables:
        names = [teams.get(e, "?") for e in table["seats"]]
        if T not in names:
            continue
        s = names.index(T)
        for h in table["hands"]:
            if h["stacks_before"][s] == 0:
                continue
            bb = h["blinds"][1]
            street = pot = pre_raises = 0
            bets_street = 0
            contrib = [0] * len(names)
            n_alive = sum(1 for x in h["stacks_before"] if x > 0)
            k = h["button"]
            order = []
            for _ in range(len(names)):
                k = (k - 1) % len(names)
                if h["stacks_before"][k] > 0:
                    order.append(k)
            d = order.index(s) if s in order else -1
            pos = "sb" if d == len(order) - 1 else "bb" if d == len(order) - 2 else "btn" if d == 0 else "co" if d == 1 else "mp" if d <= 3 else "ep"
            if n_alive >= 5:
                pos_hands[pos] += 1
            vp = False
            for ev in h["events"]:
                kind = ev["kind"]
                seat = ev.get("seat")
                if kind == "board":
                    street += 1
                    bets_street = 0
                    continue
                if kind in ("blind", "ante"):
                    contrib[seat] += ev["amount"]
                    pot += ev["amount"]
                    continue
                if kind == "raise":
                    amt = ev["amount"]
                    add = amt - contrib[seat]
                    if seat == s:
                        if street == 0:
                            vp = True
                            (opens if pre_raises == 0 else threebets).append(amt / bb)
                            if amt >= 0.9 * h["stacks_before"][s]:
                                shove_bb.append(h["stacks_before"][s] / bb)
                        elif bets_street == 0 and pot:
                            bet_fracs[street].append(add / pot)
                    if street == 0:
                        pre_raises += 1
                    bets_street += 1
                    pot += add
                    contrib[seat] = amt
                elif kind == "call":
                    amt = ev["amount"]
                    add = amt - contrib[seat]
                    if seat == s and street == 0:
                        vp = True
                        if pre_raises == 0:
                            limps += 1
                        else:
                            cold_calls += 1
                    pot += add
                    contrib[seat] = amt
            if vp and n_alive >= 5:
                pos_vpip[pos] += 1
    med = lambda v: round(statistics.median(v), 2) if v else None
    print(f"\nPROFILE {T}: open {med(opens)}bb (n={len(opens)}), 3-bet {med(threebets)}bb (n={len(threebets)}), "
          f"shove at median {med(shove_bb)}bb (n={len(shove_bb)}), cold-calls {cold_calls}, limps {limps}")
    print("  bet size / pot by street:", {st: (med(v), len(v)) for st, v in sorted(bet_fracs.items())})
    print("  VPIP by position (5+ handed):", {p: f"{pct(pos_vpip[p], pos_hands[p]):.0f}%" for p in ("ep", "mp", "co", "btn", "sb", "bb") if pos_hands[p]})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", type=Path)
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--busts", type=int, default=10, help="how many of our busts to print")
    ap.add_argument("--min-tables", type=int, default=5)
    ap.add_argument("--losses", type=int, default=12, help="biggest chip losses in the first 40 hands to print")
    ap.add_argument("--profile", default=None, help="print sizing/position profile of this team")
    args = ap.parse_args()
    header, tables = load(args.path)
    teams = {e["entry_id"]: e["team_name"] for e in header["entries"]}
    me = teams[header["you"]]
    styles = collections.defaultdict(Style)
    for table, own in tables:
        analyze_table(table, own, styles, teams)

    mine = styles[me]
    n = len(mine.points)
    print(f"tournament {header['tournament_id'][:8]}  teams {len(teams)}  our tables {n}  we are '{me}'")
    print(f"\nOUR RESULT: {statistics.fmean(mine.points):.2f} pts/table (par 12.5)  "
          f"places {dict(sorted(mine.places.items()))}  median bust hand {statistics.median(mine.bust_hands):.0f}  "
          f"automatic actions {mine.auto}")
    print(f"  style: VPIP {pct(mine.vpip, mine.hands):.0f}% PFR {pct(mine.pfr, mine.hands):.0f}% "
          f"3bet {pct(mine.threebet, mine.fto_ch):.0f}% fold-to-raise {pct(mine.fto, mine.fto_ch):.0f}% "
          f"allin-pre {pct(mine.allin_pre, mine.hands):.1f}% cbet {pct(mine.cbet, mine.cbet_ch):.0f}% "
          f"postflop bet/call/fold {mine.pbets}/{mine.pcalls}/{mine.pfolds}  showdowns {mine.showdowns}  "
          f"expose low/high {mine.exp_low}/{mine.exp_high}")

    print(f"\nFIELD LEADERBOARD (from our tables; teams with >= {args.min_tables} tables)")
    rows = [(statistics.fmean(s.points), name, s) for name, s in styles.items() if len(s.points) >= args.min_tables]
    rows.sort(reverse=True)
    print(f"{'#':>3s} {'team':28s} {'pts':>6s} {'tbl':>4s} {'1st%':>5s} {'VPIP':>5s} {'PFR':>5s} {'3b%':>4s} {'FtR%':>5s} "
          f"{'AI%':>5s} {'limp%':>5s} {'cbet%':>5s} {'call%':>5s} {'fold%':>5s} {'SD':>4s} {'expL/H':>7s} {'bust@':>6s}")
    rank = {name: i + 1 for i, (_, name, _) in enumerate(rows)}
    for i, (mean, name, s) in enumerate(rows[: args.top] + [r for r in rows[args.top:] if r[1] == me]):
        pc = s.pcalls + s.pfolds + s.pbets
        print(f"{rank[name]:3d} {name[:28]:28s} {mean:6.2f} {len(s.points):4d} {pct(s.places[1], len(s.points)):5.1f} "
              f"{pct(s.vpip, s.hands):5.1f} {pct(s.pfr, s.hands):5.1f} {pct(s.threebet, s.fto_ch):4.0f} {pct(s.fto, s.fto_ch):5.1f} "
              f"{pct(s.allin_pre, s.hands):5.1f} {pct(s.limp, s.hands):5.1f} {pct(s.cbet, s.cbet_ch):5.0f} "
              f"{pct(s.pcalls, pc):5.0f} {pct(s.pfolds, pc):5.0f} {s.showdowns:4d} {s.exp_low:3d}/{s.exp_high:<3d} "
              f"{statistics.median(s.bust_hands):6.0f}{'  <-- us' if name == me else ''}")
    print(f"\nour rank: {rank.get(me)} of {len(rows)}")

    # archetype census
    print("\nARCHETYPES (teams with >= 20 hands)")
    census = collections.Counter()
    examples = collections.defaultdict(list)
    for name, s in styles.items():
        if s.hands < 20:
            continue
        v = pct(s.vpip, s.hands)
        p = pct(s.pfr, s.hands)
        ai = pct(s.allin_pre, s.hands)
        pc = s.pcalls + s.pfolds + s.pbets
        calls = pct(s.pcalls, pc)
        if v <= 2:
            a = "FOLDBOT"
        elif ai >= 40:
            a = "SHOVER"
        elif p >= 45:
            a = "MANIAC"
        elif v <= 14:
            a = "NIT"
        elif pct(s.limp, s.hands) >= 12:
            a = "LIMPER"
        elif pc >= 20 and calls >= 55:
            a = "STATION"
        elif v >= 35:
            a = "LOOSE"
        else:
            a = "TAG"
        census[a] += 1
        examples[a].append((statistics.fmean(s.points) if s.points else 0, name))
    for a, c in census.most_common():
        ex = sorted(examples[a], reverse=True)
        avg = statistics.fmean(x[0] for x in ex)
        print(f"  {a:8s} {c:3d} teams  avg {avg:5.2f} pts   best: {', '.join(f'{n_}({p_:.1f})' for p_, n_ in ex[:4])}")

    # biggest early losses: where the stack goes before the blinds matter
    print(f"\nOUR BIGGEST EARLY LOSSES (hands 1-40, top {args.losses})")
    losses = []
    for table, own in tables:
        seat = own["seat"]
        names = [teams.get(e, "?") for e in table["seats"]]
        for h in table["hands"]:
            if h["hand"] <= 40:
                loss = h["stacks_before"][seat] - h["stacks_after"][seat]
                if loss >= 600:
                    losses.append((loss, table["table"], h, seat, names, own["cards"][h["hand"] - 1] if h["hand"] - 1 < len(own["cards"]) else []))
    losses.sort(key=lambda x: -x[0])
    for loss, tb, h, seat, names, cards in losses[: args.losses]:
        line = []
        for ev in h["events"]:
            k = ev["kind"]
            tag = "US" if ev.get("seat") == seat else (names[ev["seat"]][:5] if ev.get("seat") is not None else "")
            if k == "board":
                line.append("|" + "".join(ev["cards"]))
            elif k in ("raise", "call", "fold", "check"):
                line.append(f"{tag}:{k[0]}{ev.get('amount', '')}")
            elif k == "show":
                line.append(f"{tag}:show{''.join(ev.get('cards', []))}")
            elif k == "reveal":
                line.append(f"{tag}:rev{''.join(ev.get('cards', []))}")
        print(f"  -{loss} t{tb} h{h['hand']} {h['blinds'][:2]} us={''.join(cards)}")
        print("     " + " ".join(line))
    if args.profile:
        profile_team(tables, teams, args.profile)

    # how we busted
    print(f"\nOUR BUSTS (first {args.busts})")
    shown = 0
    for table, own in tables:
        if shown >= args.busts:
            break
        seat = own["seat"]
        names = [teams.get(e, "?") for e in table["seats"]]
        for h in table["hands"]:
            if h["stacks_before"][seat] > 0 and h["stacks_after"][seat] == 0:
                cards = own["cards"][h["hand"] - 1] if h["hand"] - 1 < len(own["cards"]) else []
                line = []
                for ev in h["events"]:
                    k = ev["kind"]
                    if k == "board":
                        line.append("|" + "".join(ev["cards"]))
                    elif k in ("raise", "call", "fold", "check"):
                        line.append(f"{names[ev['seat']][:6]}{ev['seat']}:{k[0]}{ev.get('amount', '')}")
                    elif k == "show":
                        line.append(f"{names[ev['seat']][:6]}{ev['seat']}:show{''.join(ev.get('cards', []))}")
                    elif k == "reveal":
                        line.append(f"{names[ev['seat']][:6]}{ev['seat']}:rev{''.join(ev.get('cards', []))}")
                alive = sum(1 for x in h["stacks_before"] if x > 0)
                print(f"  t{table['table']} h{h['hand']} {h['blinds'][:2]} {alive}p seat{seat} us={''.join(cards)} stack={h['stacks_before'][seat]}")
                print("     " + " ".join(line))
                shown += 1
                break


if __name__ == "__main__":
    main()
