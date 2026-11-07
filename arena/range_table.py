#!/usr/bin/env python3
"""Generate RANGE_EQ: equity of each of the 169 two-card classes against an opponent holding a
top-p% range (p in 5, 10, 20, 35), by Monte Carlo with eval7. Ranges follow the heads-up class
ordering in pre_table.PRE (third field = combo-weighted percentile). Output is a Python literal
to paste into agent.py.
"""

import random
import sys
from pathlib import Path

import eval7

sys.path.insert(0, str(Path(__file__).parent))
from pre_table import PRE  # noqa: E402

RANKS = "23456789TJQKA"
SUITS = "cdhs"
DECK = [eval7.Card(r + s) for r in RANKS for s in SUITS]
CARD = {str(c): c for c in DECK}


def combos(cls):
    """All concrete two-card combos of a class."""
    out = []
    if len(cls) == 2:  # pair
        r = cls[0]
        for i in range(4):
            for j in range(i + 1, 4):
                out.append((CARD[r + SUITS[i]], CARD[r + SUITS[j]]))
    else:
        a, b, kind = cls[0], cls[1], cls[2]
        for i in range(4):
            for j in range(4):
                if (kind == "s") == (i == j):
                    out.append((CARD[a + SUITS[i]], CARD[b + SUITS[j]]))
    return out


def range_combos(pct):
    out = []
    for cls, (_, _, perc) in PRE.items():
        if perc / 1000.0 <= pct:
            out.extend(combos(cls))
    return out


def equity(hero_cls, rng_combos, samples, rnd):
    hero_combos = combos(hero_cls)
    wins = 0.0
    n = 0
    for _ in range(samples):
        h = rnd.choice(hero_combos)
        v = rnd.choice(rng_combos)
        if v[0] in h or v[1] in h:
            continue
        used = set(h) | set(v)
        board = []
        while len(board) < 5:
            c = DECK[rnd.randrange(52)]
            if c not in used:
                used.add(c)
                board.append(c)
        hv = eval7.evaluate(list(h) + board)
        vv = eval7.evaluate(list(v) + board)
        if hv > vv:
            wins += 1
        elif hv == vv:
            wins += 0.5
        n += 1
    return wins / max(1, n)


def main():
    rnd = random.Random(2026)
    pcts = (0.05, 0.10, 0.20, 0.35)
    ranges = {p: range_combos(p) for p in pcts}
    samples = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    out = {}
    for cls in PRE:
        out[cls] = tuple(int(round(1000 * equity(cls, ranges[p], samples, rnd))) for p in pcts)
    print("# equity x1000 vs an opponent holding the top 5%, 10%, 20%, 35% of hands (HU ordering)")
    print("RANGE_EQ = {" + ",".join(f'"{k}":{v}' for k, v in out.items()) + "}")


if __name__ == "__main__":
    main()
