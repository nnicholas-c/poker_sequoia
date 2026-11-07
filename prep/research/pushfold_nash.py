"""Heads-up push/fold equilibrium (SB shoves or folds, BB calls or folds) by
fictitious play on the 169-class equity matrix. Chip EV, no antes unless given.

Research tooling (not competition code). This is also a validation of the
recipe in 09_REFERENCE_SHEETS.md section 4: the same loop with ICM-valued
outcomes instead of chips gives the tournament-correct ranges.

    python3 -I research/pushfold_nash.py research/hand_matrix.tsv
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

RANKS = "23456789TJQKA"

def combos(cls):
    return 6 if len(cls) == 2 else (4 if cls.endswith("s") else 12)

def load_matrix(path):
    eq = {}
    classes = []
    seen = set()
    with open(path) as f:
        next(f)
        for line in f:
            a, b, e, n = line.rstrip("\n").split("\t")
            e = float(e)
            eq[(a, b)] = e
            eq[(b, a)] = 1.0 - e
            for c in (a, b):
                if c not in seen:
                    seen.add(c); classes.append(c)
    return classes, eq

def solve(classes, eq, S, ante=0.0, iters=400):
    """S = effective stack in big blinds for both players (before posting).
    SB posts 0.5, BB posts 1, each posts `ante`. Returns push probs, call probs."""
    w = {c: combos(c) for c in classes}
    W = sum(w.values())
    push = {c: 0.0 for c in classes}   # average strategy (fictitious play)
    call = {c: 0.0 for c in classes}
    cur_push = {c: 1.0 for c in classes}
    cur_call = {c: 1.0 for c in classes}
    pot_pre = 1.5 + 2 * ante
    for t in range(1, iters + 1):
        # BB best response to current average push range
        tot_push = sum(w[c] * push[c] for c in classes) or 1e-9
        new_call = {}
        for h in classes:
            # EV(call) in final stack terms: 2S*eq ; EV(fold) = S - 1 - ante
            ev_call = 0.0
            for g in classes:
                if push[g] <= 0: continue
                ev_call += w[g] * push[g] * (2 * S) * eq[(h, g)]
            ev_call /= tot_push
            new_call[h] = 1.0 if ev_call > (S - 1 - ante) else 0.0
        # SB best response to current average call range
        new_push = {}
        for h in classes:
            ev = 0.0
            for g in classes:
                pc = call[g]
                ev += w[g] * ((1 - pc) * (S + 1 + ante) + pc * (2 * S) * eq[(h, g)])
            ev /= W
            new_push[h] = 1.0 if ev > (S - 0.5 - ante) else 0.0
        # fictitious play averaging
        for h in classes:
            push[h] += (new_push[h] - push[h]) / t
            call[h] += (new_call[h] - call[h]) / t
    return push, call

def pct(strat, classes):
    return 100.0 * sum(combos(c) * strat[c] for c in classes) / 1326.0

def describe(strat, classes, thresh=0.5):
    hands = [c for c in classes if strat[c] >= thresh]
    # compress: pairs, suited aces, offsuit aces, etc.
    return hands

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "research/hand_matrix.tsv"
    classes, eq = load_matrix(path)
    order = sorted(classes, key=lambda c: -eq.get((c, "72o"), 0.5))
    print("Heads-up push/fold (chip EV, no antes). Percent of combos.")
    print(f"{'stack bb':>8s} {'SB pushes':>10s} {'BB calls':>9s}  weakest pushes / weakest calls (examples)")
    for S in [3, 4, 5, 6, 7, 8, 10, 12, 15, 20, 25]:
        push, call = solve(classes, eq, S)
        p = pct(push, classes); c = pct(call, classes)
        pushes = [h for h in order if push[h] >= 0.5]
        calls = [h for h in order if call[h] >= 0.5]
        print(f"{S:8d} {p:9.1f}% {c:8.1f}%  push: ...{' '.join(pushes[-6:])} | call: ...{' '.join(calls[-6:])}")
    print()
    print("Same, with an ante of 0.1 bb per player:")
    for S in [5, 8, 10, 15]:
        push, call = solve(classes, eq, S, ante=0.1)
        print(f"{S:8d} {pct(push, classes):9.1f}% {pct(call, classes):8.1f}%")
    # full chart at 10bb
    push, call = solve(classes, eq, 10)
    print("\n10 bb SB push range (>=50% in equilibrium):")
    print(" ".join(h for h in order if push[h] >= 0.5))
    print("\n10 bb BB call range:")
    print(" ".join(h for h in order if call[h] >= 0.5))

if __name__ == "__main__":
    main()
