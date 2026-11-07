#!/usr/bin/env python3
"""In-process arena: pit any set of bot folders against each other under the real engine.

Faster than `poker-agent play` (no subprocesses) and reports what the CLI does not:
per-bot decision latency (p50/p99/max), failed decisions, the hand each bot busted on,
and points with 95% confidence intervals. Seats are rotated every table so no bot gets a
positional edge; use --fixed to keep the given order.

Usage (from the repo root, with the kit venv active):

    python arena/arena.py bots/claude_v1 bots/claude_v1 kit/examples/check_or_fold ... --tables 200
    python arena/arena.py bots/A bots/B --fill kit/examples/check_or_fold --tables 400   # pad to 8 seats
    python arena/arena.py bots/A bots/B --players 2 --tables 1000 --decision-ms 1 --bank 0  # upload test

Bots are loaded in-process; they must be stateless (a fresh Agent per seat, memory bytes only).
"""

from __future__ import annotations

import argparse
import importlib.util
import math
import os
import random
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")

from poker_agent_protocol.game import Action  # noqa: E402
from poker_engine.scoring import table_places, table_points  # noqa: E402
from poker_engine.table import SitAndGo, TableRules  # noqa: E402
from poker_engine.variant import load_variant  # noqa: E402

VARIANT = "flop_discard_reveal"


def load_agent_class(folder: Path, tag: str):
    path = folder / "agent.py"
    if not path.exists():
        raise SystemExit(f"{folder}: no agent.py")
    spec = importlib.util.spec_from_file_location(f"bot_{tag}_{abs(hash(str(folder))) % 10**6}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(folder))
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path.pop(0)
    if not hasattr(mod, "Agent"):
        raise SystemExit(f"{folder}: agent.py defines no Agent class")
    return mod.Agent


def run_table(agent_classes, rules: TableRules, variant, seed: str, stats, names, decision_ms, bank_ms):
    table = SitAndGo(rules=rules, variant=variant, table_id=f"arena-{seed}", seed=seed)
    agents = [cls() for cls in agent_classes]
    memories = [b""] * len(agents)
    failures = [0] * len(agents)
    decisions = [0] * len(agents)
    bank = [float(bank_ms)] * len(agents)
    while True:
        state = table.decision()
        if state is None:
            break
        seat = state.seat
        decisions[seat] += 1
        t0 = time.perf_counter_ns()
        try:
            action, memory = agents[seat].act(state, memories[seat])
            answered = True
        except Exception as exc:  # noqa: BLE001
            action, memory, answered = None, memories[seat], False
            stats[names[seat]]["exceptions"] += 1
            if stats[names[seat]]["exceptions"] <= 3:
                stats[names[seat]]["errors"].append(repr(exc)[:200])
        dt_ms = (time.perf_counter_ns() - t0) / 1e6
        stats[names[seat]]["lat"].append(dt_ms)
        over = max(0.0, dt_ms - decision_ms)
        if over > 0:
            if bank[seat] >= over:
                bank[seat] -= over
            else:
                bank[seat] = 0.0
                answered = False  # timeout: memory unchanged, events redelivered
                stats[names[seat]]["timeouts"] += 1
        if answered:
            if not isinstance(memory, (bytes, bytearray)) or len(memory) > rules.memory_bytes:
                memory = memories[seat]
                stats[names[seat]]["bad_memory"] += 1
            memories[seat] = bytes(memory)
            ok = table.apply(action, answered=True)
            if not ok:
                failures[seat] += 1
                stats[names[seat]]["illegal"] += 1
                if stats[names[seat]]["illegal"] <= 3:
                    stats[names[seat]]["errors"].append(
                        f"illegal {action!r} at hand {state.hand_number} phase {state.phase} legal={[(a.kind, a.min_amount, a.max_amount) for a in state.legal_actions]}"
                    )
        else:
            failures[seat] += 1
            table.apply(None, answered=False)
    result = table.result(tuple(failures), tuple(decisions))
    points = table_points(result, table.payouts)
    places = table_places(result)
    # hand each seat busted on (None if survived)
    bust_hand = {}
    for entry in table.log:
        for seat, (before, after) in enumerate(zip(entry["stacks_before"], entry["stacks_after"])):
            if before > 0 and after == 0:
                bust_hand[seat] = entry["hand"]
    for seat, name in enumerate(names):
        s = stats[name]
        s["points"].append(points[seat])
        s["places"][places[seat]] += 1
        s["failed"] += failures[seat]
        s["decisions"] += decisions[seat]
        s["bust_hands"].append(bust_hand.get(seat, result.hands_played + 1))
        s["survived"] += 0 if seat in bust_hand else 1
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bots", nargs="+", help="bot folders (each with agent.py); repeat for several seats")
    ap.add_argument("--fill", help="bot folder used to pad the table up to --players seats")
    ap.add_argument("--players", type=int, default=8)
    ap.add_argument("--tables", type=int, default=100)
    ap.add_argument("--seed", default="arena")
    ap.add_argument("--decision-ms", type=float, default=1.0)
    ap.add_argument("--bank", type=float, default=100.0, help="time bank ms (0 = upload test conditions)")
    ap.add_argument("--hand-cap", type=int, default=250)
    ap.add_argument("--fixed", action="store_true", help="do not rotate seats between tables")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    folders = [Path(b) for b in args.bots]
    if args.fill:
        while len(folders) < args.players:
            folders.append(Path(args.fill))
    if len(folders) != args.players:
        raise SystemExit(f"{len(folders)} bots given but --players is {args.players} (use --fill to pad)")

    # one name per seat; duplicates of the same folder are numbered
    counts = defaultdict(int)
    names = []
    classes = []
    cache = {}
    for f in folders:
        key = str(f.resolve())
        if key not in cache:
            cache[key] = load_agent_class(f, f.name)
        counts[key] += 1
        names.append(f"{f.name}#{counts[key]}" if folders.count(f) > 1 else f.name)
        classes.append(cache[key])

    rules = TableRules(variant=VARIANT, players=args.players, hand_cap=args.hand_cap,
                       decision_ms=max(1, int(math.ceil(args.decision_ms))), time_bank_ms=int(args.bank))
    variant = load_variant(VARIANT)
    stats = defaultdict(lambda: {"points": [], "places": defaultdict(int), "failed": 0, "decisions": 0,
                                 "lat": [], "exceptions": 0, "illegal": 0, "timeouts": 0, "bad_memory": 0,
                                 "errors": [], "bust_hands": [], "survived": 0})
    t0 = time.time()
    order = list(range(args.players))
    for n in range(args.tables):
        if not args.fixed:
            rot = n % args.players
            order = [(i + rot) % args.players for i in range(args.players)]
        seat_classes = [classes[i] for i in order]
        seat_names = [names[i] for i in order]
        run_table(seat_classes, rules, variant, f"{args.seed}:{n}", stats, seat_names, args.decision_ms, args.bank)
        if not args.quiet and (n + 1) % max(1, args.tables // 10) == 0:
            print(f"  {n + 1}/{args.tables} tables, {time.time() - t0:.1f}s", file=sys.stderr)
    elapsed = time.time() - t0

    print(f"\n{args.tables} tables x {args.players} seats, variant {VARIANT}, {elapsed:.1f}s "
          f"({args.tables / max(elapsed, 1e-9):.1f} tables/s)\n")
    rows = []
    for name in dict.fromkeys(names):
        s = stats[name]
        pts = s["points"]
        mean = statistics.fmean(pts)
        ci = 1.96 * (statistics.pstdev(pts) / math.sqrt(len(pts))) if len(pts) > 1 else 0.0
        lat = sorted(s["lat"])
        quant = tuple(lat[min(len(lat) - 1, int(p * len(lat)))] if lat else 0.0 for p in (0.5, 0.99, 0.999, 1.0))
        places = " ".join(f"{p}:{s['places'][p]}" for p in sorted(s["places"]))
        bh = s["bust_hands"]
        rows.append((mean, name, ci, s, quant, places, bh))
    rows.sort(key=lambda r: -r[0])
    print(f"{'bot':24s} {'pts':>6s} {'±95%':>5s} {'1st%':>5s} {'top3%':>5s} {'fail':>5s} {'p50ms':>6s} {'p99ms':>6s} {'p999':>6s} {'max':>6s} {'bust@':>6s}  places")
    for mean, name, ci, s, quant, places, bh in rows:
        n = len(s["points"])
        first = s["places"][1] / n * 100
        top3 = sum(s["places"][p] for p in (1, 2, 3)) / n * 100
        print(f"{name:24s} {mean:6.2f} {ci:5.2f} {first:5.1f} {top3:5.1f} {s['failed']:5d} {quant[0]:6.3f} {quant[1]:6.3f} {quant[2]:6.3f} {quant[3]:6.3f} {statistics.median(bh):6.0f}  {places}")
    for name in dict.fromkeys(names):
        s = stats[name]
        if s["errors"]:
            print(f"\n{name}: {s['exceptions']} exceptions, {s['illegal']} illegal, {s['timeouts']} timeouts, {s['bad_memory']} bad memory")
            for e in s["errors"][:6]:
                print("   ", e)


if __name__ == "__main__":
    main()
