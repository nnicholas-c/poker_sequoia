"""No Limit 2026, Bay Area variant: three hole cards, discard one and expose one after the flop.

Stateless agent: everything per table lives in the memory bytes (a checksummed struct record).
Written during the event with an AI assistant. Standard library + eval7 only.
"""

import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import gc
import random
import struct
import zlib

import eval7
import poker_agent_sdk
from poker_agent_sdk import Action, GameState

# ----------------------------------------------------------------------------------------------
# Static tables (built at import)
# ----------------------------------------------------------------------------------------------
RANKS = "23456789TJQKA"
SUITS = "cdhs"
RANK_IDX = {r: i for i, r in enumerate(RANKS)}
CARD = {r + s: eval7.Card(r + s) for r in RANKS for s in SUITS}
CODE = {r + s: RANK_IDX[r] * 4 + SUITS.index(s) for r in RANKS for s in SUITS}  # 0..51
NOCARD = 255

# 169 two-card classes: (equity vs 1 random hand x1000, equity vs 7 random hands x1000,
# combo-weighted percentile x1000 in the heads-up ordering, 0 = best). Monte Carlo, 4000 deals.
PRE = {"AA":(850,376,2),"KK":(809,336,7),"QQ":(802,289,11),"JJ":(777,258,16),"TT":(752,214,20),"99":(720,198,25),"88":(690,174,29),"AKs":(671,252,33),"AKo":(667,210,39),"AQs":(661,235,45),"77":(659,154,50),"AJs":(654,222,55),"AQo":(636,206,61),"KQs":(636,222,67),"ATs":(643,215,72),"AJo":(631,187,78),"66":(630,135,84),"KJs":(629,211,89),"ATo":(621,181,95),"KQo":(619,189,101),"A9s":(616,199,106),"KTs":(619,201,111),"QJs":(614,206,116),"55":(600,122,122),"A8s":(606,194,127),"KJo":(601,181,132),"A9o":(597,170,138),"K9s":(595,182,143),"QTs":(597,194,148),"A7s":(594,185,153),"KTo":(589,173,159),"A5s":(588,182,164),"QJo":(590,175,170),"A8o":(585,167,175),"A6s":(582,175,180),"44":(574,113,186),"JTs":(585,189,191),"A4s":(583,180,196),"K8s":(578,172,201),"Q9s":(581,180,206),"A7o":(573,158,211),"QTo":(575,165,216),"J9s":(571,174,222),"K7s":(571,164,227),"A3s":(572,172,232),"A5o":(567,155,237),"K9o":(564,153,242),"A6o":(563,151,248),"A2s":(566,169,253),"33":(548,105,258),"T9s":(557,171,263),"A4o":(557,147,268),"K8o":(547,142,273),"Q8s":(553,162,279),"K6s":(557,152,284),"J8s":(552,165,289),"JTo":(555,159,294),"Q9o":(550,152,299),"A3o":(547,140,305),"K5s":(548,148,310),"T8s":(541,157,315),"Q7s":(543,152,320),"K7o":(539,139,325),"J9o":(538,148,330),"22":(519,98,335),"A2o":(538,136,341),"K4s":(541,139,346),"98s":(530,154,351),"Q6s":(536,145,356),"T9o":(528,146,361),"J7s":(529,146,366),"K3s":(534,134,371),"Q8o":(521,134,376),"K6o":(524,127,381),"T7s":(521,143,386),"K2s":(525,128,391),"Q5s":(524,138,396),"J8o":(522,135,401),"97s":(515,143,406),"K5o":(515,121,411),"87s":(505,141,416),"Q7o":(512,123,421),"T8o":(506,127,426),"J6s":(513,134,431),"Q4s":(515,129,436),"K4o":(507,113,441),"J5s":(509,129,446),"98o":(498,124,451),"T6s":(503,128,456),"Q3s":(506,122,461),"96s":(498,131,466),"J7o":(499,118,471),"Q6o":(502,115,476),"K3o":(497,107,481),"86s":(493,129,486),"Q2s":(497,115,491),"J4s":(500,120,496),"76s":(487,128,501),"T7o":(489,114,506),"K2o":(488,101,511),"Q5o":(492,109,516),"97o":(484,112,521),"T5s":(492,119,526),"J3s":(492,113,531),"87o":(478,112,536),"95s":(486,122,541),"T4s":(488,113,546),"Q4o":(481,100,551),"65s":(474,122,556),"J6o":(477,103,561),"J2s":(484,106,566),"85s":(478,120,571),"75s":(471,117,576),"96o":(466,101,581),"Q3o":(471,93,586),"T6o":(466,97,591),"J5o":(471,99,596),"T3s":(478,106,601),"86o":(461,98,606),"Q2o":(462,88,611),"54s":(461,114,616),"T2s":(471,101,621),"64s":(459,112,626),"76o":(455,99,631),"94s":(466,106,636),"J4o":(462,90,641),"74s":(455,109,646),"84s":(461,109,651),"T5o":(455,88,656),"95o":(451,92,661),"J3o":(453,83,666),"53s":(447,106,671),"T4o":(450,83,676),"93s":(453,98,681),"65o":(439,91,686),"63s":(444,103,691),"J2o":(446,77,696),"85o":(439,89,701),"83s":(449,97,706),"75o":(433,86,711),"43s":(436,99,716),"T3o":(440,76,721),"92s":(444,90,726),"73s":(439,97,731),"54o":(424,82,736),"82s":(442,90,741),"64o":(419,79,746),"T2o":(432,70,751),"94o":(426,74,756),"52s":(428,94,761),"74o":(416,78,766),"84o":(421,78,771),"62s":(423,90,776),"42s":(418,88,781),"93o":(413,66,786),"53o":(405,72,791),"63o":(402,70,796),"83o":(406,64,801),"73o":(397,64,806),"43o":(392,66,811),"92o":(403,57,816),"32s":(401,80,821),"82o":(398,56,826),"52o":(384,60,831),"72s":(405,79,836),"62o":(380,57,841),"42o":(373,55,846),"72o":(357,48,851),"32o":(352,47,856)}

# Equity of the three-card hand score (section below) against random three-card hands, by
# score percentile bin; filled in by the generator when available. Fallback: linear.
SCORE_QUANTILES = None  # sorted list of 201 score values at percentiles 0..100 step 0.5


def cls2(a, b):
    """Two card strings -> 169-class key."""
    ra, rb = RANK_IDX[a[0]], RANK_IDX[b[0]]
    if ra == rb:
        return a[0] * 2
    hi, lo = (a, b) if ra > rb else (b, a)
    return hi[0] + lo[0] + ("s" if a[1] == b[1] else "o")


def pre_equity(cls, n_opp):
    e1, e7, _ = PRE[cls]
    if n_opp <= 1:
        return e1 / 1000.0
    if n_opp >= 7:
        return e7 / 1000.0
    return (e1 + (e7 - e1) * (n_opp - 1) / 6.0) / 1000.0


def three_card_score(cards):
    """Strength of a three-card holding before the flop: best two-card class equity plus
    bonuses for the flexibility the third card brings. Returns (score, best_pair_index)."""
    best = -1.0
    best_pair = (0, 1)
    pairs = ((0, 1), (0, 2), (1, 2))
    eqs = []
    for i, j in pairs:
        e = PRE[cls2(cards[i], cards[j])][0] / 1000.0
        eqs.append(e)
        if e > best:
            best, best_pair = e, (i, j)
    ranks = sorted(RANK_IDX[c[0]] for c in cards)
    suits = [c[1] for c in cards]
    bonus = 0.0
    nsuit = max(suits.count(s) for s in "cdhs")
    if nsuit == 3:
        bonus += 0.025
    elif nsuit == 2:
        bonus += 0.012
    span = ranks[2] - ranks[0]
    if span <= 2:
        bonus += 0.02
    elif span <= 4:
        bonus += 0.012
    if ranks[0] == ranks[1] or ranks[1] == ranks[2]:  # a pair
        bonus += 0.015
        if ranks[0] == ranks[1] == ranks[2]:
            bonus -= 0.02  # trips preflop: one card is wasted
    # second-best pair also decent -> more playable
    eqs.sort(reverse=True)
    bonus += 0.25 * max(0.0, eqs[1] - 0.45)
    return best + bonus, best_pair


def score_percentile(score):
    """Fraction of random three-card hands that score at least this (0 = best)."""
    q = SCORE_QUANTILES
    if q is None:
        # Fallback: map the heads-up class percentile by the best pair equity
        # (roughly linear between 0.36 and 0.90).
        return max(0.0, min(1.0, (0.86 - score) / 0.50))
    lo, hi = 0, len(q) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if q[mid] < score:
            lo = mid + 1
        else:
            hi = mid
    return 1.0 - lo / (len(q) - 1)


# ----------------------------------------------------------------------------------------------
# Memory record
# ----------------------------------------------------------------------------------------------
NSEATS = 10
NC = 20  # counters per seat
(HANDS, VPIP, PFR, LIMP, ALLIN_PRE, FTO_CH, FTO, THREEBET, PBETS, PCALLS, PFOLDS, CBET_CH, CBET,
 SHOWDOWNS, BLUFFS, EXP_LOW, EXP_HIGH, EXP_PAIRB, SHORT_CH, SHORT_FOLD) = range(NC)
REC_VERSION = 3
# header: version u8, hand_no u16, button u8, street u8, pre_raises u8, aggressor i8,
# raised_mask u16, river_bettors u16, flags u8, nraisers_street u8, board 5xu8,
# exposed 10xu8, last_stacks 10xu16, my_bank_uses u8, pad u8, counters 200xu16, crc u32
REC = struct.Struct("<BHBBBbHHBB5B10B10HBB200HI")
REC_SIZE = REC.size


def fresh_record():
    return {
        "hand": 0, "button": 0, "street": 0, "pre_raises": 0, "aggressor": -1,
        "raised_mask": 0, "river_bettors": 0, "flags": 0, "nraisers_street": 0,
        "board": [NOCARD] * 5, "exposed": [NOCARD] * NSEATS, "stacks": [0] * NSEATS,
        "bank_uses": 0, "counters": [[0] * NC for _ in range(NSEATS)],
    }


def pack_record(r):
    flat = []
    for row in r["counters"]:
        flat.extend(min(65535, max(0, int(v))) for v in row)
    body = REC.pack(
        REC_VERSION, r["hand"] & 0xFFFF, r["button"] & 0xFF, r["street"] & 0xFF,
        min(255, r["pre_raises"]), max(-128, min(127, r["aggressor"])),
        r["raised_mask"] & 0xFFFF, r["river_bettors"] & 0xFFFF, r["flags"] & 0xFF,
        min(255, r["nraisers_street"]), *r["board"], *r["exposed"],
        *[min(65535, max(0, int(s))) for s in r["stacks"]], min(255, r["bank_uses"]), 0,
        *flat, 0,
    )
    crc = zlib.crc32(body[:-4]) & 0xFFFFFFFF
    return body[:-4] + struct.pack("<I", crc)


def unpack_record(memory):
    if not memory or len(memory) != REC_SIZE:
        return fresh_record()
    if zlib.crc32(memory[:-4]) & 0xFFFFFFFF != struct.unpack("<I", memory[-4:])[0]:
        return fresh_record()
    v = REC.unpack(memory)
    if v[0] != REC_VERSION:
        return fresh_record()
    counters = [list(v[37 + i * NC: 37 + (i + 1) * NC]) for i in range(NSEATS)]
    return {
        "hand": v[1], "button": v[2], "street": v[3], "pre_raises": v[4], "aggressor": v[5],
        "raised_mask": v[6], "river_bettors": v[7], "flags": v[8], "nraisers_street": v[9],
        "board": list(v[10:15]), "exposed": list(v[15:25]), "stacks": list(v[25:35]),
        "bank_uses": v[35], "counters": counters,
    }


# ----------------------------------------------------------------------------------------------
# Event feed -> counters
# ----------------------------------------------------------------------------------------------
PRIOR_W = 10.0


def rate(count, chances, prior):
    return (count + prior * PRIOR_W) / (chances + PRIOR_W)


def feed(rec, state):
    """Fold state.events into the record. Events are delivered once each (redelivered only
    after a failed decision, when the memory is also the old one), so counting is exact."""
    counters = rec["counters"]
    seats_now = state.seats
    nseats = min(len(seats_now), NSEATS)
    board_cards = rec["board"]
    for ev in state.events:
        k = ev.kind
        s = ev.seat
        if k == "hand":
            # close the previous hand: c-bet chance resolution is done at flop time
            rec["hand"] = ev.amount
            rec["button"] = state.button if ev.amount == state.hand_number else rec["button"]
            rec["street"] = 0
            rec["pre_raises"] = 0
            rec["aggressor"] = -1
            rec["raised_mask"] = 0
            rec["river_bettors"] = 0
            rec["flags"] = 0
            rec["nraisers_street"] = 0
            for i in range(5):
                board_cards[i] = NOCARD
            for i in range(NSEATS):
                rec["exposed"][i] = NOCARD
            for i in range(nseats):
                if seats_now[i].status != "busted" and rec["stacks"][i] > 0 or seats_now[i].stack > 0:
                    counters[i][HANDS] += 1
            continue
        if s is None:
            if k == "board":
                n = sum(1 for c in board_cards if c != NOCARD)
                for c in ev.cards:
                    if n < 5:
                        board_cards[n] = CODE.get(c, NOCARD)
                        n += 1
                rec["street"] = 1 if n == 3 else (2 if n == 4 else 3)
                rec["nraisers_street"] = 0
                rec["flags"] &= ~1  # street has no bet yet
                if n == 3 and rec["aggressor"] >= 0:
                    counters[rec["aggressor"]][CBET_CH] += 1
                    rec["flags"] |= 2  # c-bet pending
            continue
        if s >= NSEATS:
            continue
        c = counters[s]
        st = rec["street"]
        if k == "raise":
            if st == 0:
                c[VPIP] += 1
                c[PFR] += 1
                if rec["pre_raises"] >= 1:
                    c[THREEBET] += 1
                    c[FTO_CH] += 1  # acted facing a raise (did not fold)
                rec["pre_raises"] += 1
                rec["aggressor"] = s
                rec["raised_mask"] |= 1 << s
                stack_before = rec["stacks"][s]
                if stack_before > 0 and ev.amount >= 0.9 * stack_before:
                    c[ALLIN_PRE] += 1
            else:
                c[PBETS] += 1
                if st == 1 and (rec["flags"] & 2) and s == rec["aggressor"] and rec["nraisers_street"] == 0:
                    c[CBET] += 1
                if st == 3:
                    rec["river_bettors"] |= 1 << s
                rec["flags"] |= 1
                rec["nraisers_street"] += 1
            if rec["flags"] & 2 and st == 1 and s != rec["aggressor"]:
                pass
        elif k == "call":
            if st == 0:
                c[VPIP] += 1
                if rec["pre_raises"] == 0:
                    c[LIMP] += 1
                else:
                    c[FTO_CH] += 1
            else:
                c[PCALLS] += 1
        elif k == "check":
            if st == 1 and (rec["flags"] & 2) and s == rec["aggressor"] and rec["nraisers_street"] == 0:
                rec["flags"] &= ~2  # aggressor declined to c-bet
        elif k == "fold":
            if st == 0:
                if rec["pre_raises"] >= 1:
                    c[FTO_CH] += 1
                    c[FTO] += 1
            else:
                if rec["flags"] & 1:
                    c[PFOLDS] += 1
        elif k == "reveal":
            if ev.cards:
                rec["exposed"][s] = CODE.get(ev.cards[0], NOCARD)
                if any(rc != NOCARD and rc // 4 == CODE.get(ev.cards[0], NOCARD) // 4 for rc in board_cards[:3]):
                    c[EXP_PAIRB] += 1
        elif k == "show":
            if len(ev.cards) == 2:
                c[SHOWDOWNS] += 1
                exp = rec["exposed"][s]
                codes = [CODE.get(x, NOCARD) for x in ev.cards]
                if exp != NOCARD and exp in codes:
                    hidden = codes[0] if codes[1] == exp else codes[1]
                    if hidden // 4 > exp // 4:
                        c[EXP_LOW] += 1
                    elif hidden // 4 < exp // 4:
                        c[EXP_HIGH] += 1
                if rec["river_bettors"] >> s & 1:
                    full = [CARD[x] for x in ev.cards] + [CARD_BY_CODE[b] for b in board_cards if b != NOCARD]
                    if len(full) >= 5 and (eval7.evaluate(full) >> 24) == 0:
                        c[BLUFFS] += 1
        elif k == "stack":
            rec["stacks"][s] = ev.amount
    # refresh stacks from the live view
    for i in range(nseats):
        rec["stacks"][i] = seats_now[i].stack + seats_now[i].bet
    rec["button"] = state.button


CARD_BY_CODE = {CODE[k]: CARD[k] for k in CODE}
NAME_BY_CODE = {CODE[k]: k for k in CODE}


# ----------------------------------------------------------------------------------------------
# Labels
# ----------------------------------------------------------------------------------------------
def labels_for(c):
    """Return a set of labels for one seat's counters."""
    out = set()
    hands = c[HANDS]
    if hands >= 4 and c[ALLIN_PRE] >= 0.6 * hands and c[ALLIN_PRE] >= 3:
        out.add("SHOVER")
    if hands >= 12 and c[VPIP] == 0 and c[FTO] >= 6:
        out.add("FOLDBOT")
    vp = rate(c[VPIP], hands, 0.22)
    if hands >= 20 and vp <= 0.15:
        out.add("NIT")
    if hands >= 15 and rate(c[LIMP], hands, 0.03) >= 0.10:
        out.add("LIMPER")
    if hands >= 10 and rate(c[PFR], hands, 0.14) >= 0.40:
        out.add("MANIAC")
    pc = c[PCALLS] + c[PFOLDS]
    if pc >= 8 and c[PCALLS] / pc >= 0.65 and c[PBETS] <= 0.5 * c[PCALLS]:
        out.add("STATION")
    if c[CBET_CH] >= 4 and c[CBET] / c[CBET_CH] >= 0.8:
        out.add("AUTO_CBET")
    if c[SHOWDOWNS] >= 3 and c[BLUFFS] == 0:
        out.add("NO_BLUFF")
    if c[SHOWDOWNS] >= 3 and c[BLUFFS] / c[SHOWDOWNS] >= 0.4:
        out.add("OVERBLUFF")
    if c[EXP_LOW] + c[EXP_HIGH] >= 2:
        if c[EXP_HIGH] == 0:
            out.add("EXPOSE_LOW")   # hidden >= exposed
        elif c[EXP_LOW] == 0:
            out.add("EXPOSE_HIGH")  # hidden <= exposed
    return out


# ----------------------------------------------------------------------------------------------
# Hand strength
# ----------------------------------------------------------------------------------------------
def straight_outs(mask):
    """Number of distinct ranks that would complete a straight given a rank bitmask."""
    outs = 0
    full = mask | ((mask >> 12) & 1)  # ace low: bit 13 -> treat as rank -1 by shifting below
    # windows: ranks r..r+4 for r in -1..8 (wheel uses ace as low)
    lowmask = ((mask >> 12) & 1) | (mask << 1)  # shift so that index 0 = ace-low, 1 = deuce ...
    for r in range(13):
        if lowmask >> r & 1:
            continue
        test = lowmask | (1 << r)
        for start in range(0, 10):
            w = 0b11111 << start
            if test & w == w:
                outs += 1
                break
    return outs


def has_straight(mask):
    lowmask = ((mask >> 12) & 1) | (mask << 1)
    for start in range(0, 10):
        w = 0b11111 << start
        if lowmask & w == w:
            return True
    return False


EQ_TABLE = {
    # (street_group, class): equity vs one random opponent in this variant (opponents keep best 2 of 3)
    # classes: 0 air, 1 weak pair (bottom/middle or board pair with kicker), 2 top pair/overpair,
    # 3 two pair, 4 trips, 5 straight, 6 flush, 7 full house+
    ("f", 0): 0.17, ("f", 1): 0.38, ("f", 2): 0.56, ("f", 3): 0.74, ("f", 4): 0.84, ("f", 5): 0.88, ("f", 6): 0.91, ("f", 7): 0.96,
    ("t", 0): 0.12, ("t", 1): 0.34, ("t", 2): 0.55, ("t", 3): 0.74, ("t", 4): 0.85, ("t", 5): 0.90, ("t", 6): 0.93, ("t", 7): 0.97,
    ("r", 0): 0.08, ("r", 1): 0.28, ("r", 2): 0.52, ("r", 3): 0.73, ("r", 4): 0.85, ("r", 5): 0.90, ("r", 6): 0.94, ("r", 7): 0.98,
}
DRAW_EQ = {  # added equity for draws (flop, turn)
    "gut": (0.14, 0.08), "oesd": (0.26, 0.15), "fd": (0.30, 0.17), "fd_oesd": (0.42, 0.26), "fd_gut": (0.36, 0.22),
    "over2": (0.08, 0.04),
}


def analyze(hole, board, dead_codes=()):
    """hole: 2 card strings; board: 3..5 card strings. Returns dict with class, draw, equity vs 1."""
    hc = [CARD[c] for c in hole]
    bc = [CARD[c] for c in board]
    v = eval7.evaluate(hc + bc)
    cat = v >> 24
    hr = [RANK_IDX[c[0]] for c in hole]
    br = [RANK_IDX[c[0]] for c in board]
    btop = max(br)
    street = len(board)
    sg = "f" if street == 3 else ("t" if street == 4 else "r")
    # classify
    if cat >= 6:
        cls = 7
    elif cat == 5:
        cls = 6
    elif cat == 4:
        cls = 5
    elif cat == 3:
        cls = 4
    elif cat == 2:
        # two pair: if both pairs on board, we have only kicker
        board_pairs = len(br) - len(set(br))
        cls = 3 if board_pairs < 2 else (1 if max(hr) > btop else 0)
    elif cat == 1:
        if hr[0] == hr[1]:
            cls = 2 if hr[0] > btop else 1
        elif hr[0] in br or hr[1] in br:
            pr = hr[0] if hr[0] in br else hr[1]
            cls = 2 if pr == btop else 1
        else:
            cls = 0  # pair is on the board
    else:
        cls = 0
    eq = EQ_TABLE[(sg, cls)]
    # draws
    draw = None
    if street < 5:
        suits = {}
        for c in hole + list(board):
            suits[c[1]] = suits.get(c[1], 0) + 1
        fd = any(n == 4 and any(h[1] == s for h in hole) for s, n in suits.items())
        mask = 0
        for r in hr + br:
            mask |= 1 << r
        bmask = 0
        for r in br:
            bmask |= 1 << r
        so = 0
        if not has_straight(mask):
            so = straight_outs(mask)
            if straight_outs(bmask) >= so:  # the board alone has the draw; worthless
                so = 0
        if fd and so >= 2:
            draw = "fd_oesd"
        elif fd and so == 1:
            draw = "fd_gut"
        elif fd:
            draw = "fd"
        elif so >= 2:
            draw = "oesd"
        elif so == 1:
            draw = "gut"
        elif cls == 0 and min(hr) > btop:
            draw = "over2"
        if draw and cls <= 2:
            add = DRAW_EQ[draw][0 if street == 3 else 1]
            # dead outs: exposed cards of our flush suit reduce the flush draw
            if fd:
                suit = next(s for s, n in suits.items() if n == 4 and any(h[1] == s for h in hole))
                dead = sum(1 for dc in dead_codes if dc != NOCARD and SUITS[dc % 4] == suit)
                add -= 0.035 * dead
            eq = min(0.95, eq + max(0.0, add) * (1.0 if cls == 0 else 0.6))
    return {"cls": cls, "draw": draw, "eq": eq, "cat": cat}


def multiway(eq, n_opp):
    if n_opp <= 1:
        return eq
    return eq ** (1.0 + 0.6 * (n_opp - 1))


# ----------------------------------------------------------------------------------------------
# Decision helpers
# ----------------------------------------------------------------------------------------------
def choose(state, kind, total=0):
    """Return a legal action close to the intent."""
    la = state.legal_actions
    kinds = {a.kind: a for a in la}
    if kind == "raise" and "raise" in kinds:
        r = kinds["raise"]
        amt = int(total)
        if amt < r.min_amount:
            amt = r.min_amount
        if amt > r.max_amount:
            amt = r.max_amount
        return Action.raise_to(amt)
    if kind in ("raise", "call") and "call" in kinds:
        return Action.call()
    if kind in ("raise", "call", "check") and "check" in kinds:
        return Action.check()
    if "check" in kinds:
        return Action.check()
    if "fold" in kinds:
        return Action.fold()
    if la:
        return Action(la[0].kind, la[0].min_amount)
    return Action.fold()


def position(state, live_seats):
    """0 = button, 1 = cutoff, ... ; blinds are the last two (or SB last when heads-up)."""
    n = len(live_seats)
    order = []
    s = state.button
    total = len(state.seats)
    for _ in range(total):
        if s in live_seats:
            order.append(s)
        s = (s - 1) % total
    try:
        d = order.index(state.seat)
    except ValueError:
        d = 0
    if n == 2:
        return "sb" if state.seat == state.button else "bb"
    if d == n - 1:
        return "sb"
    if d == n - 2:
        return "bb"
    if d == 0:
        return "btn"
    if d == 1:
        return "co"
    if d <= 3:
        return "mp"
    return "ep"


OPEN_W = {"ep": 0.15, "mp": 0.20, "co": 0.32, "btn": 0.48, "sb": 0.42, "bb": 0.0}
PUSH_W = {"ep": 0.14, "mp": 0.19, "co": 0.27, "btn": 0.38, "sb": 0.48, "bb": 0.0}


def rng_for(state):
    return random.Random((zlib.crc32(state.config.table_id.encode()) * 1000003 + state.hand_number * 7919 + len(state.history)) & 0xFFFFFFFF)


# ----------------------------------------------------------------------------------------------
# The agent
# ----------------------------------------------------------------------------------------------
class Agent(poker_agent_sdk.Agent):
    def act(self, state: GameState, memory: bytes) -> tuple[Action, bytes]:
        try:
            rec = unpack_record(memory)
        except Exception:
            rec = fresh_record()
        try:
            feed(rec, state)
        except Exception:
            pass
        try:
            action = decide(state, rec)
        except Exception:
            action = choose(state, "check")
        try:
            out = pack_record(rec)
        except Exception:
            out = memory
        return action, out


def decide(state, rec):
    if state.phase == "select":
        return select(state, rec)
    if state.phase != "betting":
        first = state.legal_actions[0]
        return Action(first.kind, first.min_amount)
    me = state.seat
    seats = state.seats
    my = seats[me]
    my_total = my.stack + my.bet
    bb = state.blinds.big_blind or 1
    live = [s.seat for s in seats if s.status in ("active", "all_in")]
    opp_live = [s for s in live if s != me]
    n_opp = len(opp_live)
    counters = rec["counters"]
    labels = {s: labels_for(counters[s]) for s in opp_live}
    pot = state.pot
    to_call = state.to_call
    can_raise = state.can("raise")
    rnd = rng_for(state)
    # ICM-ish risk premium
    paid = sum(1 for p in state.config.payouts if p > 0)
    players_left = state.players_remaining
    hands_to_cap = state.config.hand_cap - state.hand_number
    stacks_sorted = sorted((s.stack + s.bet for s in seats if s.status != "busted"), reverse=True)
    my_rank = stacks_sorted.index(my_total) + 1 if my_total in stacks_sorted else len(stacks_sorted)
    if players_left <= 2:
        lam = 0.0
    else:
        lam = 0.45
        if players_left == paid + 1:
            lam += 0.3
        if hands_to_cap <= 20 and my_rank <= paid:
            lam += 0.3
        if my_rank == 1 and players_left >= 4:
            lam += 0.1
    big_call = to_call >= 0.4 * my_total if my_total else True
    if len(state.board) == 0:
        return preflop(state, rec, labels, live, n_opp, my_total, bb, lam, rnd)
    return postflop(state, rec, labels, live, n_opp, my_total, bb, lam, rnd)


def preflop(state, rec, labels, live, n_opp, my_total, bb, lam, rnd):
    me = state.seat
    cards = state.cards
    score, best_pair = three_card_score(cards)
    p = score_percentile(score)
    best_cls = cls2(cards[best_pair[0]], cards[best_pair[1]])
    eq1 = PRE[best_cls][0] / 1000.0 + 0.03  # flexibility of the third card
    pos = position(state, live)
    pot = state.pot
    to_call = state.to_call
    can_raise = state.can("raise")
    seats = state.seats
    # effective stack in bb against the biggest live opponent
    opp_stacks = [seats[s].stack + seats[s].bet for s in live if s != me]
    eff = min(my_total, max(opp_stacks) if opp_stacks else my_total) / bb
    hist = state.history
    raises = [e for e in hist if e.kind == "raise"]
    nraises = len(raises)
    limpers = sum(1 for e in hist if e.kind == "call" and nraises == 0)
    raiser = raises[-1].seat if raises else None
    raiser_total = (seats[raiser].stack + seats[raiser].bet) if raiser is not None else 0
    shovers = [s for s in live if s != me and "SHOVER" in labels[s]]
    acted = {e.seat for e in hist if e.kind in ("fold", "call", "raise", "check")}
    shovers_behind = [s for s in shovers if s not in acted and seats[s].status == "active"]
    facing_allin = raiser is not None and (seats[raiser].status == "all_in" or to_call >= 0.5 * my_total)
    # table fold-to-open rate (how often raises get folded to)
    tot_ch = sum(rec["counters"][s][FTO_CH] for s in live if s != me)
    tot_f = sum(rec["counters"][s][FTO] for s in live if s != me)
    table_fold = rate(tot_f, tot_ch, 0.7)
    steal_mult = 1.0
    if tot_ch >= 8 and table_fold >= 0.8:
        steal_mult = 1.4
    blinds_fold = all(("NIT" in labels[s] or "FOLDBOT" in labels[s]) for s in live if s != me and position_of(state, live, s) in ("sb", "bb")) if n_opp >= 2 else False
    if blinds_fold:
        steal_mult = max(steal_mult, 1.6)

    if nraises == 0:
        # unopened pot (maybe limpers)
        if state.can("check"):  # we are the big blind with limpers or walk
            if p <= 0.15 and can_raise:
                return choose(state, "raise", bb * (3 + limpers))
            return choose(state, "check")
        if shovers_behind:
            if eq1 >= 0.65 and can_raise:
                return choose(state, "raise", can_raise.max_amount)
            return choose(state, "fold")
        width = OPEN_W[pos] * steal_mult
        if pos in ("co", "btn", "sb"):
            width = min(0.62, width)
        if eff <= 5:
            if pos in ("btn", "sb", "co") or p <= 0.45:
                return choose(state, "raise", can_raise.max_amount if can_raise else 0)
            return choose(state, "fold")
        if eff <= 11:
            w = PUSH_W[pos] * steal_mult
            if p <= w and can_raise:
                return choose(state, "raise", can_raise.max_amount)
            return choose(state, "fold")
        if limpers:
            if p <= width * 0.8 and can_raise:
                return choose(state, "raise", bb * (3 + limpers))
            if p <= width * 1.1 and pos in ("btn", "sb", "bb") and to_call <= bb:
                return choose(state, "call")
            return choose(state, "fold")
        if p <= width and can_raise:
            if eff <= 18:
                size = 2 * bb
            elif pos in ("co", "btn"):
                size = int(2.3 * bb)
            elif pos == "sb":
                size = 3 * bb
            else:
                size = int(2.5 * bb)
            return choose(state, "raise", size)
        return choose(state, "fold")

    # facing at least one raise
    price = to_call / (pot + to_call) if (pot + to_call) > 0 else 1.0
    opened_by_me = any(e.kind == "raise" and e.seat == me for e in hist)
    callers_of_shove = sum(1 for e in hist if e.kind == "call" and e.amount >= 0.5 * my_total)
    if facing_allin or (raiser is not None and "SHOVER" in labels[raiser]):
        n_allin = sum(1 for s in live if s != me and seats[s].status == "all_in") + (0 if seats[raiser].status == "all_in" else 1)
        if raiser is not None and "SHOVER" in labels[raiser]:
            thr = 0.65 if raiser_total >= 10 * bb else 0.58
            if n_allin >= 2 or callers_of_shove >= 1:
                thr = 0.73  # QQ+ territory against two
            if eq1 >= thr:
                if state.can("call"):
                    return choose(state, "call")
                return choose(state, "raise", can_raise.max_amount if can_raise else 0)
            return choose(state, "fold")
        eq = pre_equity(best_cls, max(1, n_allin)) + 0.02
        need = price * (1.0 + lam) + 0.06
        if eff <= 6 and state.players_remaining > 2:
            need -= 0.06  # we are nearly blinded out anyway
        if eq >= need:
            return choose(state, "call")
        return choose(state, "fold")
    # normal raise(s)
    if opened_by_me:
        # facing a 3-bet after our open
        if p <= 0.06 and can_raise:
            return choose(state, "raise", can_raise.max_amount if eff <= 40 else 3 * raises[-1].amount)
        if p <= 0.10 and to_call <= 0.12 * my_total and eff > 25:
            return choose(state, "call")
        return choose(state, "fold")
    if nraises >= 2:
        if p <= 0.035 and can_raise:
            return choose(state, "raise", can_raise.max_amount)
        return choose(state, "fold")
    # facing a single open
    maniac = raiser is not None and "MANIAC" in labels[raiser]
    nit = raiser is not None and "NIT" in labels[raiser]
    v3 = 0.045 * (1.6 if maniac else 1.0) * (0.7 if nit else 1.0)
    if p <= v3 and can_raise:
        if eff <= 25:
            return choose(state, "raise", can_raise.max_amount)
        return choose(state, "raise", 3 * raises[-1].amount)
    if eff <= 15:
        if p <= (0.10 if not maniac else 0.16) and can_raise:
            return choose(state, "raise", can_raise.max_amount)
        return choose(state, "fold")
    call_w = 0.12 * (1.6 if maniac else 1.0) * (0.6 if nit else 1.0)
    if pos == "bb":
        if to_call <= 1.5 * bb:
            call_w = max(call_w, 0.42)
        elif to_call <= 2.5 * bb:
            call_w = max(call_w, 0.30)
        else:
            call_w = max(call_w, 0.18)
    if p <= call_w and to_call <= 0.18 * my_total:
        return choose(state, "call")
    return choose(state, "fold")


def position_of(state, live, seat):
    n = len(live)
    order = []
    s = state.button
    total = len(state.seats)
    for _ in range(total):
        if s in live:
            order.append(s)
        s = (s - 1) % total
    try:
        d = order.index(seat)
    except ValueError:
        return "ep"
    if n == 2:
        return "sb" if seat == state.button else "bb"
    if d == n - 1:
        return "sb"
    if d == n - 2:
        return "bb"
    if d == 0:
        return "btn"
    if d == 1:
        return "co"
    if d <= 3:
        return "mp"
    return "ep"


def select(state, rec):
    """Choose which card to discard and which kept card to expose."""
    cards = state.cards
    board = state.board
    if len(cards) != 3:
        return Action("select", cards=(2, 0))
    me = state.seat
    live = [s.seat for s in state.seats if s.status in ("active", "all_in")]
    n_opp = max(1, len(live) - 1)
    best = None
    for discard in range(3):
        keep = [cards[i] for i in range(3) if i != discard]
        a = analyze(keep, board)
        eq = a["eq"]
        # small kicker preference
        kick = max(RANK_IDX[c[0]] for c in keep) / 1000.0
        val = eq + kick
        if best is None or val > best[0]:
            best = (val, discard, keep, a)
    _, discard, keep, a = best
    keep_idx = [i for i in range(3) if i != discard]
    # exposure: show the card that connects least with the board
    br = [RANK_IDX[c[0]] for c in board]
    btop = max(br)
    suits = {}
    for c in board:
        suits[c[1]] = suits.get(c[1], 0) + 1
    two_tone = max(suits.values()) >= 2
    has_ak = btop >= RANK_IDX["K"]
    rnd = rng_for(state)
    scores = []
    for i in keep_idx:
        c = cards[i]
        r = RANK_IDX[c[0]]
        sc = 0.0
        if r == btop:
            sc += 3
        elif r in br:
            sc += 2
        if two_tone and suits.get(c[1], 0) >= 2:
            sc += 1.5
        if min(abs(r - b) for b in br) <= 2 and r not in br:
            sc += 1.0
        if r >= RANK_IDX["K"] and not has_ak:
            sc += 1.0
        if r <= RANK_IDX["5"]:
            sc -= 0.3  # free Empty Bluffer tie-break
        sc += rnd.random() * 0.2
        scores.append((sc, i))
    scores.sort()
    reveal = scores[0][1]
    return Action("select", cards=(discard, reveal))


def postflop(state, rec, labels, live, n_opp, my_total, bb, lam, rnd):
    me = state.seat
    seats = state.seats
    cards = state.cards
    board = state.board
    pot = state.pot
    to_call = state.to_call
    can_raise = state.can("raise")
    if len(cards) != 2:
        # should not happen after selection; play safe
        return choose(state, "check") if to_call == 0 else choose(state, "fold")
    dead = [rec["exposed"][s] for s in live if s != me and s < NSEATS]
    a = analyze(cards, board, dead)
    eq1 = a["eq"]
    cls = a["cls"]
    # opponents' exposed cards as strength floors
    br = [RANK_IDX[c[0]] for c in board]
    btop = max(br)
    suits = {}
    for c in board:
        suits[c[1]] = suits.get(c[1], 0) + 1
    threat = 0.0
    for s in live:
        if s == me or s >= NSEATS:
            continue
        ec = rec["exposed"][s]
        if ec == NOCARD:
            continue
        er, es = ec // 4, SUITS[ec % 4]
        if er == btop:
            threat += 0.15
        elif er in br:
            threat += 0.08
        elif er > btop:
            threat += 0.03
        if suits.get(es, 0) >= 2 and len(board) < 5:
            threat += 0.04
        lab = labels.get(s, set())
        if "EXPOSE_HIGH" in lab and er <= RANK_IDX["9"] and er not in br:
            threat -= 0.08  # its hidden card is at most this rank
        if "EXPOSE_LOW" in lab and er >= RANK_IDX["T"]:
            threat += 0.05
    if cls <= 2:
        eq1 = max(0.02, eq1 - min(0.25, threat))
    eq = multiway(eq1, n_opp)
    street = len(board)
    aggressor = rec["aggressor"] == me
    # opponent labels in the pot
    opp_labels = set()
    for s in live:
        if s != me:
            opp_labels |= labels.get(s, set())
    station = "STATION" in opp_labels
    foldbot = n_opp == 1 and "FOLDBOT" in opp_labels
    nobluff = "NO_BLUFF" in opp_labels
    dry = len(set(br)) == len(br) and max(suits.values()) <= 2 and (max(br) - min(br) >= 5 or len(board) == 3 and sorted(br)[1] - sorted(br)[0] >= 2 and sorted(br)[2] - sorted(br)[1] >= 2)
    stack_frac = lambda amt: amt / my_total if my_total else 1.0

    def bet(frac):
        size = int(pot * frac)
        target = seats[me].bet + to_call + size
        if target - seats[me].bet >= 0.6 * (seats[me].stack):
            target = can_raise.max_amount if can_raise else target
        return choose(state, "raise", target)

    if to_call == 0:
        if foldbot and can_raise:
            return bet(0.6)
        strong = 0.60
        if station:
            strong = 0.52
        if eq >= strong and can_raise:
            return bet(0.8 if station else 0.62)
        if street == 3 and aggressor and n_opp == 1 and can_raise and not station:
            # continuation bet: with equity, or with air on dry boards sometimes
            if eq1 >= 0.30 or (dry and rnd.random() < 0.55):
                return bet(0.55)
        if street == 4 and aggressor and n_opp == 1 and can_raise and not station and a["draw"] in ("fd", "oesd", "fd_oesd", "fd_gut"):
            return bet(0.55)
        return choose(state, "check")
    # facing a bet
    price = to_call / (pot + to_call)
    big = to_call >= 0.4 * my_total
    if big:
        need = price * (1.0 + lam) + 0.05
        if nobluff:
            need += 0.05
        if "MANIAC" in opp_labels or "OVERBLUFF" in opp_labels:
            need -= 0.07
        return choose(state, "call") if eq >= need else choose(state, "fold")
    if cls >= 3 and can_raise and eq >= 0.70:
        return bet(1.0)
    need = price + 0.04
    if nobluff and to_call >= 0.7 * (pot - to_call) and cls <= 2:
        need += 0.12  # a big bet from a bot that never bluffs
    if "MANIAC" in opp_labels or "OVERBLUFF" in opp_labels:
        need -= 0.06
    # draws need the odds; river has none
    if eq >= need:
        return choose(state, "call")
    return choose(state, "fold")


# Warm up at import and stop the collector from pausing a decision later.
def _warmup():
    try:
        three_card_score(("As", "Kd", "7c"))
        analyze(("As", "Kd"), ("Ah", "7c", "2d"))
        analyze(("9s", "8s"), ("7s", "6d", "2s", "Kh"))
        pack_record(fresh_record())
        unpack_record(pack_record(fresh_record()))
    except Exception:
        pass


_warmup()
gc.collect()
gc.freeze()
gc.disable()
