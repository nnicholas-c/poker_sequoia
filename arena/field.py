#!/usr/bin/env python3
"""Field replica: one hero bot vs 7 opponents drawn each table from a pool weighted like the real
practice field (archetype census from the platform histories). Calibrate first: our old versions
should score here what they scored in practice (v1 15.45, v2 16.06, v7 14.60).

python arena/field.py bots/nc_v9 --tables 400 [--jobs 2]
"""
import argparse, math, multiprocessing as mp, random, statistics, sys, time
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from arena import load_agent_class, run_table, VARIANT  # noqa: E402
from poker_engine.table import TableRules  # noqa: E402
from poker_engine.variant import load_variant  # noqa: E402

# census of 127 teams in the practice runs: TAG 66%, LOOSE 9%, LIMPER 9%, NIT 8%, FOLDBOT 4%, MANIAC 2%, STATION 2%
POOLS = {}
POOLS["A"] = [
    ("bots/arch_tag", 0.20), ("bots/nc_v2", 0.08), ("bots/nc_v4", 0.08), ("bots/kevin1", 0.06),
    ("bots/codex_reveal_v1", 0.06), ("bots/codex_merge_v4_v6", 0.06), ("bots/nc_v6", 0.06), ("bots/codex_reform_v7", 0.04),
    ("bots/arch_loose", 0.09), ("bots/arch_limper", 0.09), ("bots/arch_nit", 0.08),
    ("kit/examples/check_or_fold", 0.04), ("bots/arch_maniac", 0.02), ("bots/arch_station", 0.02),
]
# softer: fewer of our own strong bots, more loose/limp/station/maniac (calibrated to practice scores)
POOLS["B"] = [
    ("bots/arch_tag", 0.30), ("bots/nc_v2", 0.05), ("bots/nc_v4", 0.03), ("bots/kevin1", 0.06), ("bots/codex_reveal_v1", 0.05),
    ("bots/arch_loose", 0.12), ("bots/arch_limper", 0.12), ("bots/arch_nit", 0.10),
    ("kit/examples/check_or_fold", 0.06), ("bots/arch_maniac", 0.05), ("bots/arch_station", 0.06),
]
import os as _os
POOL = POOLS[_os.environ.get("FIELD_POOL", "A")]


def worker(args):
    hero, start, n, seed = args
    classes = {p: load_agent_class(Path(p), Path(p).name) for p, _ in POOL}
    hero_cls = load_agent_class(Path(hero), "hero")
    rules = TableRules(variant=VARIANT, players=8)
    variant = load_variant(VARIANT)
    names_p = [p for p, _ in POOL]
    weights = [w for _, w in POOL]
    pts = []
    places = defaultdict(int)
    for i in range(start, start + n):
        rnd = random.Random(f"{seed}:{i}")
        opp = rnd.choices(names_p, weights, k=7)
        seat = i % 8
        folders = opp[:seat] + ["HERO"] + opp[seat:]
        cls = [hero_cls if f == "HERO" else classes[f] for f in folders]
        nm = [f"s{k}" for k in range(8)]
        stats = defaultdict(lambda: {"points": [], "places": defaultdict(int), "failed": 0, "decisions": 0, "lat": [],
                                     "exceptions": 0, "illegal": 0, "timeouts": 0, "bad_memory": 0, "errors": [],
                                     "bust_hands": [], "survived": 0})
        from history_report import Style
        stats["_style"] = defaultdict(Style)
        run_table(cls, rules, variant, f"{seed}:{i}", stats, nm, 1.0, 100.0)
        pts.append(stats[nm[seat]]["points"][0])
        for p, c in stats[nm[seat]]["places"].items():
            places[p] += c
    return pts, dict(places)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("hero"); ap.add_argument("--tables", type=int, default=400); ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--seed", default="field")
    a = ap.parse_args()
    t0 = time.time()
    per = a.tables // a.jobs
    with mp.Pool(a.jobs) as pool:
        res = pool.map(worker, [(a.hero, j * per, per, a.seed) for j in range(a.jobs)])
    pts = [p for r in res for p in r[0]]
    places = defaultdict(int)
    for r in res:
        for k, v in r[1].items():
            places[k] += v
    ci = 1.96 * statistics.pstdev(pts) / math.sqrt(len(pts))
    print(f"{a.hero}: {statistics.fmean(pts):.2f} ± {ci:.2f} pts/table over {len(pts)} tables  "
          f"1st {100 * places[1] / len(pts):.1f}%  places {dict(sorted(places.items()))}  ({time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main()
