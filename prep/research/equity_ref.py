"""Reference-table generator (run offline, output is public-knowledge data).

Computes, by Monte Carlo, the all-in equity of each of the 169 starting-hand
classes against N random opponents (N = 1 and N = 7), prints a ranking.
Pure Python, no dependencies. Not competition code: this only produces a
sanity-check table for the reference sheet.
"""
import itertools, random, sys, time
from collections import Counter

RANKS = "23456789TJQKA"
SUITS = "cdhs"
DECK = [(r, s) for r in range(13) for s in range(4)]

# ---- 5-card evaluator via rank patterns (fast enough for a reference run) ----
def eval5(cards):
    ranks = sorted((c[0] for c in cards), reverse=True)
    suits = [c[1] for c in cards]
    flush = len(set(suits)) == 1
    cnt = Counter(ranks)
    groups = sorted(cnt.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)
    uniq = sorted(cnt, reverse=True)
    straight_high = None
    if len(uniq) == 5:
        if uniq[0] - uniq[4] == 4:
            straight_high = uniq[0]
        elif uniq == [12, 3, 2, 1, 0]:
            straight_high = 3
    if straight_high is not None and flush:
        return (8, straight_high)
    if groups[0][1] == 4:
        return (7, groups[0][0], groups[1][0])
    if groups[0][1] == 3 and groups[1][1] == 2:
        return (6, groups[0][0], groups[1][0])
    if flush:
        return (5,) + tuple(ranks)
    if straight_high is not None:
        return (4, straight_high)
    if groups[0][1] == 3:
        return (3, groups[0][0]) + tuple(r for r in ranks if r != groups[0][0])
    if groups[0][1] == 2 and groups[1][1] == 2:
        kick = [r for r in ranks if cnt[r] == 1][0]
        return (2, groups[0][0], groups[1][0], kick)
    if groups[0][1] == 2:
        return (1, groups[0][0]) + tuple(r for r in ranks if r != groups[0][0])
    return (0,) + tuple(ranks)

def eval7(cards):
    best = None
    for combo in itertools.combinations(cards, 5):
        v = eval5(combo)
        if best is None or v > best:
            best = v
    return best

def hand_classes():
    out = []
    for i in range(12, -1, -1):
        for j in range(i, -1, -1):
            if i == j:
                out.append((RANKS[i] + RANKS[j], (i, 0), (j, 1)))
            else:
                out.append((RANKS[i] + RANKS[j] + "s", (i, 0), (j, 0)))
                out.append((RANKS[i] + RANKS[j] + "o", (i, 0), (j, 1)))
    return out

def equity(hole, n_opp, samples, rng):
    deck = [c for c in DECK if c not in hole]
    won = 0.0
    for _ in range(samples):
        rng.shuffle(deck)
        board = deck[:5]
        mine = eval7(list(hole) + board)
        best_opp = None
        ties = 0
        idx = 5
        for _k in range(n_opp):
            opp = deck[idx:idx + 2]
            idx += 2
            v = eval7(opp + board)
            if best_opp is None or v > best_opp:
                best_opp = v
        if mine > best_opp:
            won += 1.0
        elif mine == best_opp:
            # count how many opponents tie with the best
            idx = 5
            nt = 1
            for _k in range(n_opp):
                opp = deck[idx:idx + 2]
                idx += 2
                if eval7(opp + board) == mine:
                    nt += 1
            won += 1.0 / nt
    return won / samples

def main():
    samples = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    rng = random.Random(12345)
    t0 = time.time()
    rows = []
    for name, c1, c2 in hand_classes():
        e1 = equity((c1, c2), 1, samples, rng)
        e7 = equity((c1, c2), 7, samples, rng)
        rows.append((name, e1, e7))
    rows.sort(key=lambda r: -r[1])
    with open(sys.argv[2] if len(sys.argv) > 2 else "/home/claude/scratch/equity_ref.tsv", "w") as f:
        f.write("rank_hu\thand\tequity_vs1\tequity_vs7\trank_vs7\n")
        by7 = {r[0]: i + 1 for i, r in enumerate(sorted(rows, key=lambda r: -r[2]))}
        for i, (name, e1, e7) in enumerate(rows, 1):
            f.write(f"{i}\t{name}\t{e1:.3f}\t{e7:.3f}\t{by7[name]}\n")
    print("done in %.0fs" % (time.time() - t0))

if __name__ == "__main__":
    main()
