"""Offline research simulator for the No Limit format (NOT a competition bot).

Purpose: measure things the playbook needs numbers for, with crude archetype
bots: how often eight-player tables reach the 200-hand cap, how many survive,
how an all-in-every-hand bot and a fold-everything bot finish against a field
of tight-aggressive heuristics, and how risk-aversion settings trade off under
different payout shapes. Pure Python, standard library only.

Everything here is SYNTHETIC where the organizer has not published a value
(blind schedule after 10/20, payouts). Run from the repo root:

    python3 -I research/sng_sim.py --tables 400 --lineup shove7tag --payouts flat

This file is analysis tooling. Nothing in it is written to be submitted.
"""
from __future__ import annotations

import argparse
import itertools
import random
import sys
import time
from collections import Counter
from functools import lru_cache

# ----------------------------------------------------------------------------
# cards and a reasonably fast 7-card evaluator (rank counts + suit masks)
# ----------------------------------------------------------------------------
RANKS = "23456789TJQKA"
DECK = [(r, s) for r in range(13) for s in range(4)]  # (rank 0..12, suit 0..3)

STRAIGHT_MASKS = []
for hi in range(12, 3, -1):
    STRAIGHT_MASKS.append((hi, sum(1 << (hi - k) for k in range(5))))
WHEEL = (3, (1 << 12) | 0b1111)  # A2345

def _top_straight(mask):
    for hi, m in STRAIGHT_MASKS:
        if mask & m == m:
            return hi
    if mask & WHEEL[1] == WHEEL[1]:
        return 3
    return -1

def eval7(cards):
    """Return a comparable tuple (category, tiebreak...). Higher is better.
    Categories: 8 SF, 7 quads, 6 full house, 5 flush, 4 straight, 3 trips,
    2 two pair, 1 pair, 0 high card."""
    counts = [0] * 13
    suit_masks = [0, 0, 0, 0]
    suit_n = [0, 0, 0, 0]
    mask = 0
    for r, s in cards:
        counts[r] += 1
        suit_masks[s] |= 1 << r
        suit_n[s] += 1
        mask |= 1 << r
    # flush / straight flush
    for s in range(4):
        if suit_n[s] >= 5:
            sf = _top_straight(suit_masks[s])
            if sf >= 0:
                return (8, sf)
            fm = suit_masks[s]
            top = []
            for r in range(12, -1, -1):
                if fm >> r & 1:
                    top.append(r)
                    if len(top) == 5:
                        break
            flush = (5,) + tuple(top)
            break
    else:
        flush = None
    quads = trips = -1
    pairs = []
    for r in range(12, -1, -1):
        c = counts[r]
        if c == 4:
            quads = r
        elif c == 3:
            if trips < 0:
                trips = r
            else:
                pairs.append(r)  # second trips acts as a pair for full house
        elif c == 2:
            pairs.append(r)
    if quads >= 0:
        kick = max(r for r in range(13) if counts[r] and r != quads)
        return (7, quads, kick)
    if trips >= 0 and pairs:
        return (6, trips, pairs[0])
    if flush:
        return flush
    st = _top_straight(mask)
    if st >= 0:
        return (4, st)
    if trips >= 0:
        kick = [r for r in range(12, -1, -1) if counts[r] == 1][:2]
        return (3, trips) + tuple(kick)
    if len(pairs) >= 2:
        kick = max(r for r in range(13) if counts[r] == 1)
        return (2, pairs[0], pairs[1], kick)
    if len(pairs) == 1:
        kick = [r for r in range(12, -1, -1) if counts[r] == 1][:3]
        return (1, pairs[0]) + tuple(kick)
    top = [r for r in range(12, -1, -1) if counts[r]][:5]
    return (0,) + tuple(top)

# ----------------------------------------------------------------------------
# preflop strength: 169-class heads-up ordering (from research/equity_ref.tsv
# if present, else a built-in approximation by equity formula)
# ----------------------------------------------------------------------------
def hand_class(c1, c2):
    r1, s1 = c1
    r2, s2 = c2
    hi, lo = max(r1, r2), min(r1, r2)
    if hi == lo:
        return RANKS[hi] * 2
    return RANKS[hi] + RANKS[lo] + ("s" if s1 == s2 else "o")

def load_equity_table(path):
    eq = {}
    try:
        with open(path) as f:
            next(f)
            for line in f:
                parts = line.rstrip("\n").split("\t")
                eq[parts[1]] = (float(parts[2]), float(parts[3]))
    except OSError:
        return None
    return eq

EQ = load_equity_table("/home/claude/scratch/equity_ref.tsv") or load_equity_table("research/equity_ref.tsv")
if EQ is None:
    # crude fallback: Chen-like ordering mapped to an equity-ish number
    def _fallback(cls):
        hi = RANKS.index(cls[0]); lo = RANKS.index(cls[1])
        pair = cls[0] == cls[1]
        suited = cls.endswith("s")
        base = 0.33 + 0.02 * hi + 0.01 * lo
        if pair:
            base = 0.50 + 0.027 * hi
        if suited:
            base += 0.02
        if abs(hi - lo) == 1 and not pair:
            base += 0.012
        return min(base, 0.85)
    EQ = {}
    for i in range(13):
        for j in range(i, 13):
            if i == j:
                EQ[RANKS[i] * 2] = (_fallback(RANKS[i] * 2), 0.2)
            else:
                for suf in "so":
                    cls = RANKS[j] + RANKS[i] + suf
                    EQ[cls] = (_fallback(cls), 0.15)

ORDER = sorted(EQ, key=lambda k: -EQ[k][0])
PCT = {}  # combo-weighted percentile, 0 = best
_cum = 0
for cls in ORDER:
    n = 6 if len(cls) == 2 else (4 if cls.endswith("s") else 12)
    PCT[cls] = (_cum + n / 2) / 1326.0
    _cum += n

# ----------------------------------------------------------------------------
# ICM (Malmuth-Harville) with memo over remaining-set bitmask
# ----------------------------------------------------------------------------
def icm_points(stacks, payouts):
    n = len(stacks)
    pay = list(payouts) + [0.0] * max(0, n - len(payouts))
    idx = [i for i in range(n) if stacks[i] > 0]
    total = float(sum(stacks))

    @lru_cache(maxsize=None)
    def pf(player, place, rem_mask):
        rem = [i for i in idx if rem_mask >> i & 1]
        s = sum(stacks[i] for i in rem)
        if place == 0:
            return stacks[player] / s
        p = 0.0
        for j in rem:
            if j == player:
                continue
            p += (stacks[j] / s) * pf(player, place - 1, rem_mask & ~(1 << j))
        return p

    full = 0
    for i in idx:
        full |= 1 << i
    out = [0.0] * n
    npaid = min(len(idx), len([p for p in pay if p > 0]))
    for i in idx:
        e = 0.0
        for place in range(npaid):
            e += pay[place] * pf(i, place, full)
        out[i] = e
    return out

# ----------------------------------------------------------------------------
# game state and engine
# ----------------------------------------------------------------------------
SYNTHETIC_BLINDS = [(10, 20), (15, 30), (25, 50), (50, 100), (75, 150), (100, 200), (150, 300), (200, 400)]
SCHEDULES = {
    "eight": SYNTHETIC_BLINDS,
    "growing": [(10, 20), (15, 30), (25, 50), (50, 100), (75, 150), (100, 200), (150, 300), (200, 400), (300, 600), (400, 800), (500, 1000), (600, 1200), (800, 1600)],
}

class Obs:
    __slots__ = ("seat", "hole", "board", "street", "stacks", "bets", "committed", "live", "pot",
                 "to_call", "can_check", "min_raise_to", "max_raise_to", "button", "bb", "sb",
                 "n_live", "hand_no", "raises_this_street", "aggressor", "history", "players_left")

class Table:
    def __init__(self, bots, payouts, seed, blinds=SYNTHETIC_BLINDS, hands_per_level=25, cap=200, start=2000):
        self.bots = bots
        self.n = len(bots)
        self.payouts = payouts
        self.rng = random.Random(seed)
        self.blinds = blinds
        self.hpl = hands_per_level
        self.cap = cap
        self.stacks = [start] * self.n
        self.button = self.rng.randrange(self.n)
        self.finish = [None] * self.n  # finishing place (1 = winner)
        self.hand_no = 0
        self.busted_order = []
        for i, b in enumerate(bots):
            b.reset(i, self.n, self.rng.randrange(1 << 30))

    def alive(self):
        return [i for i in range(self.n) if self.stacks[i] > 0]

    def next_alive(self, seat):
        s = seat
        for _ in range(self.n):
            s = (s + 1) % self.n
            if self.stacks[s] > 0:
                return s
        return seat

    def level(self):
        lv = min(self.hand_no // self.hpl, len(self.blinds) - 1)
        return self.blinds[lv]

    def run(self):
        while len(self.alive()) > 1 and self.hand_no < self.cap:
            self.play_hand()
            self.hand_no += 1
        alive = self.alive()
        points = [0.0] * self.n
        pay = list(self.payouts) + [0.0] * self.n
        # busted players get their place points
        places_taken = 0
        # finishing places assigned at bust time from the bottom
        for i in range(self.n):
            if self.finish[i] is not None:
                points[i] = pay[self.finish[i] - 1]
        if len(alive) == 1:
            points[alive[0]] = pay[0]
            self.finish[alive[0]] = 1
        else:
            # ICM over remaining places 1..len(alive)
            rem_pay = pay[:len(alive)]
            sub = [self.stacks[i] for i in alive]
            eq = icm_points(sub, rem_pay)
            for k, i in enumerate(alive):
                points[i] = eq[k]
                self.finish[i] = 0  # 0 marks "survived to cap"
        return points, len(alive), self.hand_no

    def bust(self, seat):
        # place = number of players still with chips + 1 (ties resolved arbitrarily by order)
        alive_before = len(self.alive()) + 1
        self.finish[seat] = alive_before
        self.busted_order.append(seat)

    def play_hand(self):
        alive = self.alive()
        n_live = len(alive)
        sb_amt, bb_amt = self.level()
        self.button = self.next_alive(self.button)
        if n_live == 2:
            sb_seat = self.button
            bb_seat = self.next_alive(sb_seat)
        else:
            sb_seat = self.next_alive(self.button)
            bb_seat = self.next_alive(sb_seat)
        deck = DECK[:]
        self.rng.shuffle(deck)
        hole = {}
        k = 0
        for s in alive:
            hole[s] = (deck[k], deck[k + 1]); k += 2
        board_cards = deck[k:k + 5]
        committed = [0] * self.n   # total this hand
        bets = [0] * self.n        # this street
        folded = set(i for i in range(self.n) if self.stacks[i] <= 0)
        allin = set()
        def post(seat, amt):
            a = min(amt, self.stacks[seat])
            self.stacks[seat] -= a
            bets[seat] += a
            committed[seat] += a
            if self.stacks[seat] == 0:
                allin.add(seat)
        post(sb_seat, sb_amt)
        post(bb_seat, bb_amt)
        history = []
        pot_before_streets = 0

        def live_players():
            return [i for i in alive if i not in folded]

        def betting_round(street, first_to_act, board):
            nonlocal bets
            current_bet = max(bets) if street == 0 else 0
            last_raise = bb_amt if street == 0 else bb_amt
            raises = 0
            aggressor = bb_seat if street == 0 else None
            acted = set()
            order = []
            s = first_to_act
            for _ in range(self.n):
                if s in alive and s not in folded:
                    order.append(s)
                s = (s + 1) % self.n
            # queue of players who still need to act
            pending = [s for s in order if s not in allin]
            i = 0
            guard = 0
            while pending:
                guard += 1
                if guard > 500:
                    break
                seat = pending.pop(0)
                if seat in folded or seat in allin:
                    continue
                lp = live_players()
                if len(lp) == 1:
                    return
                to_call = current_bet - bets[seat]
                can_check = to_call == 0
                pot = pot_before_streets + sum(bets)
                others_live = [p for p in lp if p != seat and p not in allin]
                max_raise_to = bets[seat] + self.stacks[seat]
                min_raise_to = current_bet + max(last_raise, bb_amt)
                # cannot raise if no one can respond (all others all-in) -- simplify: allowed but pointless
                can_raise = max_raise_to > current_bet and (len(others_live) > 0 or current_bet == 0)
                if min_raise_to > max_raise_to:
                    min_raise_to = max_raise_to
                o = Obs()
                o.seat = seat; o.hole = hole[seat]; o.board = board; o.street = street
                o.stacks = self.stacks; o.bets = bets; o.committed = committed
                o.live = lp; o.pot = pot; o.to_call = to_call; o.can_check = can_check
                o.min_raise_to = min_raise_to if can_raise else None
                o.max_raise_to = max_raise_to if can_raise else None
                o.button = self.button; o.bb = bb_amt; o.sb = sb_amt; o.n_live = len(lp)
                o.hand_no = self.hand_no; o.raises_this_street = raises; o.aggressor = aggressor
                o.history = history; o.players_left = n_live
                try:
                    act = self.bots[seat].act(o)
                except Exception:
                    act = ("check",) if can_check else ("fold",)
                kind = act[0]
                # legalize
                if kind == "raise":
                    if not can_raise:
                        kind = "call" if to_call > 0 else "check"
                    else:
                        amt = int(act[1])
                        amt = max(min_raise_to, min(max_raise_to, amt))
                        if amt <= current_bet:
                            kind = "call" if to_call > 0 else "check"
                if kind == "check" and not can_check:
                    kind = "fold"
                if kind == "call" and to_call == 0:
                    kind = "check"
                if kind == "fold":
                    folded.add(seat)
                    history.append((street, seat, "fold", 0))
                elif kind == "check":
                    history.append((street, seat, "check", 0))
                elif kind == "call":
                    post(seat, to_call)
                    history.append((street, seat, "call", to_call))
                elif kind == "raise":
                    inc = amt - current_bet
                    post(seat, amt - bets[seat])
                    if bets[seat] > current_bet:
                        if bets[seat] - current_bet >= max(last_raise, bb_amt):
                            last_raise = bets[seat] - current_bet
                        current_bet = bets[seat]
                        raises += 1
                        aggressor = seat
                        history.append((street, seat, "raise", current_bet))
                        # everyone else live and not all-in must act again
                        pending = [p for p in order if p != seat and p not in folded and p not in allin]
                    else:
                        history.append((street, seat, "call", bets[seat]))
                acted.add(seat)
            return

        # preflop
        first = self.next_alive(bb_seat) if n_live > 2 else self.button  # HU: button (SB) acts first preflop
        betting_round(0, first, [])
        pot_before_streets += sum(bets); bets = [0] * self.n
        streets = [(1, 3), (2, 4), (3, 5)]
        for street, ncards in streets:
            lp = live_players()
            if len(lp) <= 1:
                break
            if len([p for p in lp if p not in allin]) >= 2:
                board = board_cards[:ncards]
                first_post = self.next_alive(self.button)
                while first_post in folded:
                    first_post = self.next_alive(first_post)
                betting_round(street, first_post, board)
                pot_before_streets += sum(bets); bets = [0] * self.n
        # showdown / award
        lp = live_players()
        total_pot = sum(committed)
        if len(lp) == 1:
            self.stacks[lp[0]] += total_pot
        else:
            # side pots by contribution levels
            board = board_cards[:5]
            ranks = {p: eval7(list(hole[p]) + board) for p in lp}
            levels = sorted(set(committed[p] for p in lp))
            prev = 0
            remaining = total_pot
            for lvl in levels:
                contributors = [i for i in range(self.n) if committed[i] >= lvl]
                portion = sum(min(committed[i], lvl) - min(committed[i], prev) for i in range(self.n))
                eligible = [p for p in lp if committed[p] >= lvl]
                best = max(ranks[p] for p in eligible)
                winners = [p for p in eligible if ranks[p] == best]
                share = portion // len(winners)
                for w in winners:
                    self.stacks[w] += share
                self.stacks[winners[0]] += portion - share * len(winners)
                remaining -= portion
                prev = lvl
            if remaining:
                self.stacks[lp[0]] += remaining  # rounding leftovers
        # busts (players with 0 chips who were alive): assign places; ties by committed stack size
        busted = [s for s in alive if self.stacks[s] == 0]
        busted.sort(key=lambda s: committed[s])  # smaller stack busts "first" (worse place)
        k = len(self.alive())
        for idx, s in enumerate(busted):
            self.finish[s] = k + len(busted) - idx
            self.busted_order.append(s)
        for b in self.bots:
            hook = getattr(b, "on_hand_end", None)
            if hook:
                try:
                    hook(history, alive)
                except Exception:
                    pass

# ----------------------------------------------------------------------------
# archetype bots (crude on purpose; research only)
# ----------------------------------------------------------------------------
class FoldBot:
    name = "fold"
    def reset(self, seat, n, seed): pass
    def act(self, o):
        return ("check",) if o.can_check else ("fold",)

class ShoveBot:
    name = "shove"
    def reset(self, seat, n, seed): pass
    def act(self, o):
        if o.max_raise_to is not None:
            return ("raise", o.max_raise_to)
        return ("call",) if o.to_call > 0 else ("check",)

class CallBot:
    name = "station"
    def reset(self, seat, n, seed): pass
    def act(self, o):
        return ("call",) if o.to_call > 0 else ("check",)

class RandomBot:
    name = "random"
    def reset(self, seat, n, seed): self.rng = random.Random(seed)
    def act(self, o):
        r = self.rng.random()
        if o.max_raise_to is not None and r < 0.25:
            lo, hi = o.min_raise_to, o.max_raise_to
            return ("raise", self.rng.randint(lo, hi))
        if r < 0.55:
            return ("call",) if o.to_call > 0 else ("check",)
        if o.can_check:
            return ("check",)
        return ("fold",) if r < 0.85 else ("call",)

def made_class(hole, board):
    """0 air,1 weak pair,2 top pair/overpair,3 two pair+,4 nuts-class; plus draw flag."""
    if not board:
        return 0, False
    v = eval7(list(hole) + board)
    cat = v[0]
    hr = {hole[0][0], hole[1][0]}
    br = [c[0] for c in board]
    top = max(br)
    draw = False
    if len(board) < 5:
        suits = Counter(c[1] for c in list(hole) + board)
        if max(suits.values()) == 4:
            draw = True
        mask = 0
        for c in list(hole) + board:
            mask |= 1 << c[0]
        # open-ended-ish: four consecutive ranks present
        for hi in range(12, 2, -1):
            m = sum(1 << (hi - k) for k in range(4))
            if mask & m == m:
                draw = True
                break
    if cat >= 4:
        return 4, draw
    if cat == 3 or cat == 2:
        return 3, draw
    if cat == 1:
        pr = v[1]
        if pr in hr and (pr >= top or hole[0][0] == hole[1][0]):
            return 2, draw
        if pr in hr:
            return 1, draw
        return 0, draw  # board pair only
    return 0, draw

class TagBot:
    """Position chart + pot odds + push/fold. `tight` scales ranges; `icm_lambda` is risk premium on all-in calls."""
    name = "tag"
    def __init__(self, tight=1.0, icm_lambda=0.25, aggression=1.0, name=None):
        self.tight = tight; self.lam = icm_lambda; self.aggr = aggression
        if name: self.name = name
    def reset(self, seat, n, seed):
        self.rng = random.Random(seed)
    def position(self, o):
        # seats before button among live players: 0 = button
        lp = o.live
        order = []
        s = o.button
        for _ in range(8):
            if s in lp:
                order.append(s)
            s = (s - 1) % len(o.stacks)
        # order[0]=button, order[1]=cutoff, ... ; blinds are after button
        try:
            d = order.index(o.seat)
        except ValueError:
            d = 0
        n = len(lp)
        if n == 2:
            return "btn" if o.seat == o.button else "bb"
        # distance from button going backwards: 0 btn, 1 co, 2 hj, ...; blinds are the last two
        if d == n - 1:
            return "sb"
        if d == n - 2:
            return "bb"
        if d == 0: return "btn"
        if d == 1: return "co"
        if d <= 3: return "mp"
        return "ep"
    def act(self, o):
        cls = hand_class(*o.hole)
        p = PCT[cls]
        my = o.stacks[o.seat] + o.bets[o.seat]
        bb = o.bb
        eff_bb = my / bb
        if o.street == 0:
            return self.preflop(o, p, eff_bb)
        return self.postflop(o, eff_bb)
    def preflop(self, o, p, eff_bb):
        pos = self.position(o)
        widths = {"ep": 0.12, "mp": 0.16, "co": 0.25, "btn": 0.40, "sb": 0.35, "bb": 0.0}
        w = widths[pos] / self.tight
        raised = o.raises_this_street
        facing_allin = o.to_call >= 0.5 * (o.stacks[o.seat] + o.bets[o.seat]) and o.to_call > 0
        if raised == 0 or (raised == 1 and pos == "bb" and o.can_check and False):
            # unopened (or just blinds)
            if o.can_check:  # we are BB and everyone limped/folded
                return ("raise", o.min_raise_to) if (o.max_raise_to and p < 0.15) else ("check",)
            if eff_bb <= 12:
                if p < min(0.9, w * 1.8) and o.max_raise_to:
                    return ("raise", o.max_raise_to)
                return ("fold",)
            if p < w and o.max_raise_to:
                size = int(2.5 * o.bb) if pos in ("ep", "mp") else int(2.3 * o.bb)
                if pos == "sb": size = 3 * o.bb
                return ("raise", max(o.min_raise_to, min(o.max_raise_to, size)))
            return ("fold",)
        # facing a raise
        pot_after = o.pot + o.to_call
        need = o.to_call / pot_after if pot_after else 1
        if facing_allin:
            # call all-in: equity vs random ~ EQ[cls][0]; require need*(1+lambda) with multiway tightening
            eq = EQ[cls][0]
            nraisers = sum(1 for h in o.history if h[0] == 0 and h[2] == "raise")
            if nraisers >= 2: eq -= 0.08
            lam = 0.0 if o.players_left == 2 else self.lam
            return ("call",) if eq >= min(0.95, need * (1 + lam) + 0.1) else ("fold",)
        if p < 0.04 and o.max_raise_to:
            target = 3 * (o.to_call + o.bets[o.seat])
            if eff_bb <= 25: target = o.max_raise_to
            return ("raise", max(o.min_raise_to, min(o.max_raise_to, target)))
        if eff_bb <= 15:
            if p < 0.08 and o.max_raise_to:
                return ("raise", o.max_raise_to)
            return ("fold",)
        if p < 0.12 and o.to_call <= 0.15 * (o.stacks[o.seat] + o.bets[o.seat]):
            return ("call",)
        if pos == "bb" and raised == 1 and o.to_call <= 1.5 * o.bb and p < 0.40:
            return ("call",)
        return ("fold",)
    def postflop(self, o, eff_bb):
        mc, draw = made_class(o.hole, o.board)
        n_opp = o.n_live - 1
        est = {0: 0.15, 1: 0.35, 2: 0.55, 3: 0.75, 4: 0.90}[mc]
        if n_opp >= 2: est -= 0.08 * (n_opp - 1)
        if draw: est += 0.18 if o.street < 3 else 0.0
        pot = o.pot
        if o.can_check:
            if mc >= 2 or (draw and self.rng.random() < 0.5 * self.aggr) or (mc == 0 and o.aggressor == o.seat and self.rng.random() < 0.45 * self.aggr and n_opp == 1):
                size = int(0.6 * pot)
                if o.max_raise_to is None:
                    return ("check",)
                target = o.bets[o.seat] + o.to_call + size
                if target > 0.6 * (o.stacks[o.seat] + o.bets[o.seat]):
                    target = o.max_raise_to
                return ("raise", max(o.min_raise_to, min(o.max_raise_to, target)))
            return ("check",)
        need = o.to_call / (o.pot + o.to_call)
        big = o.to_call >= 0.4 * (o.stacks[o.seat] + o.bets[o.seat])
        lam = 0.0 if o.players_left == 2 else self.lam
        if big:
            return ("call",) if est >= need * (1 + lam) + 0.08 else ("fold",)
        if mc >= 3 and o.max_raise_to:
            target = o.bets[o.seat] + o.to_call + int(1.0 * (o.pot + o.to_call))
            if target > 0.6 * (o.stacks[o.seat] + o.bets[o.seat]): target = o.max_raise_to
            return ("raise", max(o.min_raise_to, min(o.max_raise_to, target)))
        if est >= need + 0.03:
            return ("call",)
        return ("fold",)

class ManiacBot(TagBot):
    name = "maniac"
    def __init__(self):
        super().__init__(tight=0.4, icm_lambda=0.0, aggression=2.0, name="maniac")
    def preflop(self, o, p, eff_bb):
        if o.max_raise_to and p < 0.55 and o.raises_this_street <= 1:
            target = int(2.5 * o.bb) if o.raises_this_street == 0 else 3 * (o.to_call + o.bets[o.seat])
            return ("raise", max(o.min_raise_to, min(o.max_raise_to, target)))
        return super().preflop(o, p, eff_bb)

class NitBot(TagBot):
    name = "nit"
    def __init__(self):
        super().__init__(tight=2.2, icm_lambda=0.5, aggression=0.6, name="nit")

class AdaptiveTag(TagBot):
    """TagBot that detects a preflop shove-bot (full hand histories) and responds with
    an equity threshold T against it: shove into it / call its shove with eq >= T."""
    def __init__(self, T=0.6, name=None, **kw):
        super().__init__(name=name or f"adapt{int(T*100)}", **kw)
        self.T = T
    def reset(self, seat, n, seed):
        super().reset(seat, n, seed)
        self.seen = [0] * n; self.shoves = [0] * n
    def on_hand_end(self, history, alive):
        for s in alive:
            self.seen[s] += 1
        for street, seat, kind, amt in history:
            if street == 0 and kind == "raise":
                self.shoves[seat] += 1  # counted as shove if raise was all-in; approximated below
    def shover_seats(self, o):
        out = []
        for s in o.live:
            if s != o.seat and self.seen[s] >= 4 and self.shoves[s] >= 0.6 * self.seen[s]:
                out.append(s)
        return out
    def preflop(self, o, p, eff_bb):
        shovers = self.shover_seats(o)
        if shovers:
            cls = hand_class(*o.hole)
            eq = EQ[cls][0]
            acted = {h[1] for h in o.history if h[0] == 0}
            shoved_now = [h for h in o.history if h[0] == 0 and h[2] == "raise" and h[1] in shovers]
            if shoved_now:
                # facing the shove-bot's raise (treat as all-in)
                return ("call",) if eq >= self.T else ("fold",)
            still_to_act = [s for s in shovers if s not in acted]
            if still_to_act:
                if eq >= self.T and o.max_raise_to:
                    return ("raise", o.max_raise_to)
                return ("check",) if o.can_check else ("fold",)
        return super().preflop(o, p, eff_bb)

class StealerTag(AdaptiveTag):
    """AdaptiveTag that also measures how often the table folds to raises and,
    when the table is passive, widens late-position steals (shoves when <= 20bb,
    raises when deeper). Research probe for the 'table naivety index'."""
    def __init__(self, width=0.5, name=None, **kw):
        super().__init__(name=name or f"steal{int(width*100)}", **kw)
        self.width = width
    def reset(self, seat, n, seed):
        super().reset(seat, n, seed)
        self.raises_seen = 0; self.raises_folded = 0
    def on_hand_end(self, history, alive):
        super().on_hand_end(history, alive)
        pre = [h for h in history if h[0] == 0]
        # first raise of the hand: did everyone else fold?
        for i, h in enumerate(pre):
            if h[2] == "raise":
                rest = pre[i+1:]
                self.raises_seen += 1
                if all(x[2] == "fold" for x in rest):
                    self.raises_folded += 1
                break
    def preflop(self, o, p, eff_bb):
        if self.shover_seats(o):
            return super().preflop(o, p, eff_bb)
        passive = self.raises_seen >= 8 and self.raises_folded / self.raises_seen >= 0.80
        pos = self.position(o)
        if passive and o.raises_this_street == 0 and pos in ("co", "btn", "sb") and o.max_raise_to and not o.can_check:
            if p < self.width:
                if eff_bb <= 20:
                    return ("raise", o.max_raise_to)
                size = int(2.3 * o.bb)
                return ("raise", max(o.min_raise_to, min(o.max_raise_to, size)))
        return super().preflop(o, p, eff_bb)

LINEUPS = {
    "tag8": lambda: [TagBot(name="tag") for _ in range(8)],
    "shove7tag": lambda: [ShoveBot()] + [TagBot(name="tag") for _ in range(7)],
    "fold7tag": lambda: [FoldBot()] + [TagBot(name="tag") for _ in range(7)],
    "station7tag": lambda: [CallBot()] + [TagBot(name="tag") for _ in range(7)],
    "random7tag": lambda: [RandomBot()] + [TagBot(name="tag") for _ in range(7)],
    "maniac7tag": lambda: [ManiacBot()] + [TagBot(name="tag") for _ in range(7)],
    "nit7tag": lambda: [NitBot()] + [TagBot(name="tag") for _ in range(7)],
    "mixed": lambda: [ShoveBot(), FoldBot(), CallBot(), RandomBot(), ManiacBot(), NitBot(), TagBot(name="tag"), TagBot(name="tag")],
    "lambda": lambda: [TagBot(icm_lambda=0.0, name="lam0"), TagBot(icm_lambda=0.0, name="lam0"),
                       TagBot(icm_lambda=0.25, name="lam25"), TagBot(icm_lambda=0.25, name="lam25"),
                       TagBot(icm_lambda=0.5, name="lam50"), TagBot(icm_lambda=0.5, name="lam50"),
                       TagBot(icm_lambda=1.0, name="lam100"), TagBot(icm_lambda=1.0, name="lam100")],
    "tightness": lambda: [TagBot(tight=0.7, name="loose"), TagBot(tight=0.7, name="loose"),
                          TagBot(tight=1.0, name="tag"), TagBot(tight=1.0, name="tag"),
                          TagBot(tight=1.5, name="tight"), TagBot(tight=1.5, name="tight"),
                          TagBot(tight=2.2, name="nit"), TagBot(tight=2.2, name="nit")],
    **{f"adapt1_{t}": (lambda t=t: [ShoveBot(), AdaptiveTag(T=t/100)] + [TagBot(name="tag") for _ in range(6)]) for t in (50,55,60,65,70)},
    **{f"adapt7_{t}": (lambda t=t: [ShoveBot()] + [AdaptiveTag(T=t/100) for _ in range(7)]) for t in (50,55,60,65,70)},
    **{f"steal1_{w}": (lambda w=w: [StealerTag(width=w/100)] + [TagBot(name="tag") for _ in range(7)]) for w in (30,50,70,100)},
    **{f"steal4_{w}": (lambda w=w: [StealerTag(width=w/100) for _ in range(4)] + [TagBot(name="tag") for _ in range(4)]) for w in (50,100)},
    **{f"stealnit_{w}": (lambda w=w: [StealerTag(width=w/100)] + [NitBot() for _ in range(7)]) for w in (0,40,70,100)},
    "tagnit": lambda: [TagBot(name="tag")] + [NitBot() for _ in range(7)],
    "mixed_two_shovers": lambda: [ShoveBot(), ShoveBot(), FoldBot(), CallBot(), NitBot(), TagBot(name="tag"), TagBot(name="tag"), TagBot(name="tag")],
}
PAYOUTS = {
    "flat": [40, 25, 15, 12, 8],
    "topheavy": [60, 25, 10, 5],
    "wta": [100],
    "three": [50, 30, 20],
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tables", type=int, default=200)
    ap.add_argument("--lineup", default="tag8")
    ap.add_argument("--payouts", default="flat")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--hpl", type=int, default=25)
    ap.add_argument("--cap", type=int, default=200)
    ap.add_argument("--schedule", default="eight")
    args = ap.parse_args()
    pay = PAYOUTS[args.payouts]
    rng = random.Random(args.seed)
    t0 = time.time()
    agg = {}
    cap_hits = 0; survivors_hist = Counter(); hands_hist = []
    for t in range(args.tables):
        bots = LINEUPS[args.lineup]()
        rng.shuffle(bots)
        table = Table(bots, pay, seed=rng.randrange(1 << 30), blinds=SCHEDULES[args.schedule], hands_per_level=args.hpl, cap=args.cap)
        points, nsurv, nhands = table.run()
        if nhands >= table.cap and nsurv > 1:
            cap_hits += 1
            survivors_hist[nsurv] += 1
        hands_hist.append(nhands)
        for i, b in enumerate(bots):
            a = agg.setdefault(b.name, {"pts": 0.0, "n": 0, "places": Counter(), "sq": 0.0})
            a["pts"] += points[i]; a["sq"] += points[i] ** 2; a["n"] += 1
            a["places"][table.finish[i]] += 1
    el = time.time() - t0
    print(f"lineup={args.lineup} payouts={args.payouts} tables={args.tables} hpl={args.hpl} cap={args.cap} schedule={args.schedule} time={el:.0f}s")
    print(f"tables reaching the cap: {100*cap_hits/args.tables:.1f}%  survivors at cap: {dict(sorted(survivors_hist.items()))}")
    hs = sorted(hands_hist)
    print(f"hands per table: median {hs[len(hs)//2]}, p10 {hs[len(hs)//10]}, p90 {hs[9*len(hs)//10]}")
    print(f"{'bot':10s} {'pts/table':>9s} {'+-95%':>6s} {'1st%':>5s} {'cap%':>5s} {'6-8th%':>6s}  places(1st..8th, 0=survived to cap)")
    for name, a in sorted(agg.items(), key=lambda kv: -kv[1]["pts"] / kv[1]["n"]):
        n = a["n"]; mean = a["pts"] / n
        sd = (a["sq"] / n - mean ** 2) ** 0.5
        ci = 1.96 * sd / n ** 0.5
        pl = a["places"]
        first = 100 * pl[1] / n; cap = 100 * pl[0] / n; low = 100 * (pl[6] + pl[7] + pl[8]) / n
        dist = " ".join(f"{k}:{100*pl[k]/n:.0f}" for k in [1, 2, 3, 4, 5, 6, 7, 8, 0] if pl[k])
        print(f"{name:10s} {mean:9.2f} {ci:6.2f} {first:5.1f} {cap:5.1f} {low:6.1f}  {dist}")

if __name__ == "__main__":
    main()
