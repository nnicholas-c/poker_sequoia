"""Compute the 169 x 169 preflop class-vs-class all-in equity matrix by Monte Carlo.

Research tooling (not competition code). Output: research/hand_matrix.tsv with
rows "classA classB equityA samples". Uses the evaluator from sng_sim.py.

    python3 -I research/hand_matrix.py 400 research/hand_matrix.tsv
"""
import itertools, random, sys, time, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sng_sim import eval7, RANKS, DECK

def class_list():
    out = []
    for i in range(12, -1, -1):
        for j in range(i, -1, -1):
            if i == j:
                out.append(RANKS[i] * 2)
            else:
                out.append(RANKS[i] + RANKS[j] + "s")
                out.append(RANKS[i] + RANKS[j] + "o")
    return out

def representatives(cls):
    """All concrete two-card holdings of a class (as (rank,suit) tuples)."""
    r1 = RANKS.index(cls[0]); r2 = RANKS.index(cls[1])
    out = []
    if r1 == r2:
        for s1, s2 in itertools.combinations(range(4), 2):
            out.append(((r1, s1), (r2, s2)))
    elif cls.endswith("s"):
        for s in range(4):
            out.append(((r1, s), (r2, s)))
    else:
        for s1 in range(4):
            for s2 in range(4):
                if s1 != s2:
                    out.append(((r1, s1), (r2, s2)))
    return out

def main():
    samples = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    out_path = sys.argv[2] if len(sys.argv) > 2 else "research/hand_matrix.tsv"
    classes = class_list()
    reps = {c: representatives(c) for c in classes}
    rng = random.Random(2026)
    t0 = time.time()
    with open(out_path, "w") as f:
        f.write("classA\tclassB\tequityA\tsamples\n")
        for ia, a in enumerate(classes):
            for b in classes[ia:]:
                won = 0.0; n = 0
                for _ in range(samples):
                    ha = rng.choice(reps[a])
                    hb = rng.choice(reps[b])
                    if len({ha[0], ha[1], hb[0], hb[1]}) < 4:
                        continue  # card conflict; resample
                    used = {ha[0], ha[1], hb[0], hb[1]}
                    board = []
                    while len(board) < 5:
                        c = DECK[rng.randrange(52)]
                        if c not in used:
                            used.add(c); board.append(c)
                    va = eval7([ha[0], ha[1]] + board)
                    vb = eval7([hb[0], hb[1]] + board)
                    if va > vb: won += 1
                    elif va == vb: won += 0.5
                    n += 1
                eq = won / n if n else 0.5
                f.write(f"{a}\t{b}\t{eq:.4f}\t{n}\n")
            if ia % 20 == 0:
                print(f"{ia}/169 done, {time.time()-t0:.0f}s", flush=True)
    print("done", time.time() - t0)

if __name__ == "__main__":
    main()
