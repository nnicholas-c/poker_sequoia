"""No Limit 2026, Bay Area variant (three hole cards, discard one / expose one after the flop).

nc_v6: open-shove the top of the range at 13-20bb (winners shove ~7% of hands at ~20bb);
v5: Team-72 shape (flat VPIP, 2.6bb opens, small 3-bets, 38%-pot flop bets, push/fold 13bb),
mixed exposure, two pair valued lower, tighter cold calls, early deep protection.
v2: calibrated 3-card percentiles, range-aware all-in calls, deep-stack-aware shover handling,
sane postflop classification (board pairs, overpairs, fake two pair), per-hand opponent counters,
c-betting from the hand history, select phase with eval7 tie-breaks.

Stateless: per-table state lives only in the memory bytes (crc-checked struct record).
Standard library + eval7.
"""

import os

os.environ.setdefault("OMP_NUM_THREADS", "1")

import gc
import random
import struct
import zlib

import eval7
import poker_agent_sdk
from poker_agent_sdk import Action, GameState

# ----------------------------------------------------------------------------------------------
# Static tables
# ----------------------------------------------------------------------------------------------
RANKS = "23456789TJQKA"
SUITS = "cdhs"
RANK_IDX = {r: i for i, r in enumerate(RANKS)}
CARD = {r + s: eval7.Card(r + s) for r in RANKS for s in SUITS}
CODE = {r + s: RANK_IDX[r] * 4 + SUITS.index(s) for r in RANKS for s in SUITS}  # 0..51
CARD_BY_CODE = {CODE[k]: CARD[k] for k in CODE}
NOCARD = 255

# 169 classes: (equity vs 1 random x1000, vs 7 random x1000, HU percentile x1000; 0 = best)
PRE = {"AA":(850,376,2),"KK":(809,336,7),"QQ":(802,289,11),"JJ":(777,258,16),"TT":(752,214,20),"99":(720,198,25),"88":(690,174,29),"AKs":(671,252,33),"AKo":(667,210,39),"AQs":(661,235,45),"77":(659,154,50),"AJs":(654,222,55),"AQo":(636,206,61),"KQs":(636,222,67),"ATs":(643,215,72),"AJo":(631,187,78),"66":(630,135,84),"KJs":(629,211,89),"ATo":(621,181,95),"KQo":(619,189,101),"A9s":(616,199,106),"KTs":(619,201,111),"QJs":(614,206,116),"55":(600,122,122),"A8s":(606,194,127),"KJo":(601,181,132),"A9o":(597,170,138),"K9s":(595,182,143),"QTs":(597,194,148),"A7s":(594,185,153),"KTo":(589,173,159),"A5s":(588,182,164),"QJo":(590,175,170),"A8o":(585,167,175),"A6s":(582,175,180),"44":(574,113,186),"JTs":(585,189,191),"A4s":(583,180,196),"K8s":(578,172,201),"Q9s":(581,180,206),"A7o":(573,158,211),"QTo":(575,165,216),"J9s":(571,174,222),"K7s":(571,164,227),"A3s":(572,172,232),"A5o":(567,155,237),"K9o":(564,153,242),"A6o":(563,151,248),"A2s":(566,169,253),"33":(548,105,258),"T9s":(557,171,263),"A4o":(557,147,268),"K8o":(547,142,273),"Q8s":(553,162,279),"K6s":(557,152,284),"J8s":(552,165,289),"JTo":(555,159,294),"Q9o":(550,152,299),"A3o":(547,140,305),"K5s":(548,148,310),"T8s":(541,157,315),"Q7s":(543,152,320),"K7o":(539,139,325),"J9o":(538,148,330),"22":(519,98,335),"A2o":(538,136,341),"K4s":(541,139,346),"98s":(530,154,351),"Q6s":(536,145,356),"T9o":(528,146,361),"J7s":(529,146,366),"K3s":(534,134,371),"Q8o":(521,134,376),"K6o":(524,127,381),"T7s":(521,143,386),"K2s":(525,128,391),"Q5s":(524,138,396),"J8o":(522,135,401),"97s":(515,143,406),"K5o":(515,121,411),"87s":(505,141,416),"Q7o":(512,123,421),"T8o":(506,127,426),"J6s":(513,134,431),"Q4s":(515,129,436),"K4o":(507,113,441),"J5s":(509,129,446),"98o":(498,124,451),"T6s":(503,128,456),"Q3s":(506,122,461),"96s":(498,131,466),"J7o":(499,118,471),"Q6o":(502,115,476),"K3o":(497,107,481),"86s":(493,129,486),"Q2s":(497,115,491),"J4s":(500,120,496),"76s":(487,128,501),"T7o":(489,114,506),"K2o":(488,101,511),"Q5o":(492,109,516),"97o":(484,112,521),"T5s":(492,119,526),"J3s":(492,113,531),"87o":(478,112,536),"95s":(486,122,541),"T4s":(488,113,546),"Q4o":(481,100,551),"65s":(474,122,556),"J6o":(477,103,561),"J2s":(484,106,566),"85s":(478,120,571),"75s":(471,117,576),"96o":(466,101,581),"Q3o":(471,93,586),"T6o":(466,97,591),"J5o":(471,99,596),"T3s":(478,106,601),"86o":(461,98,606),"Q2o":(462,88,611),"54s":(461,114,616),"T2s":(471,101,621),"64s":(459,112,626),"76o":(455,99,631),"94s":(466,106,636),"J4o":(462,90,641),"74s":(455,109,646),"84s":(461,109,651),"T5o":(455,88,656),"95o":(451,92,661),"J3o":(453,83,666),"53s":(447,106,671),"T4o":(450,83,676),"93s":(453,98,681),"65o":(439,91,686),"63s":(444,103,691),"J2o":(446,77,696),"85o":(439,89,701),"83s":(449,97,706),"75o":(433,86,711),"43s":(436,99,716),"T3o":(440,76,721),"92s":(444,90,726),"73s":(439,97,731),"54o":(424,82,736),"82s":(442,90,741),"64o":(419,79,746),"T2o":(432,70,751),"94o":(426,74,756),"52s":(428,94,761),"74o":(416,78,766),"84o":(421,78,771),"62s":(423,90,776),"42s":(418,88,781),"93o":(413,66,786),"53o":(405,72,791),"63o":(402,70,796),"83o":(406,64,801),"73o":(397,64,806),"43o":(392,66,811),"92o":(403,57,816),"32s":(401,80,821),"82o":(398,56,826),"52o":(384,60,831),"72s":(405,79,836),"62o":(380,57,841),"42o":(373,55,846),"72o":(357,48,851),"32o":(352,47,856)}

# equity x1000 vs an opponent holding the top 5%, 10%, 20%, 35% of hands (HU ordering)
RANGE_EQ = {"AA":(824, 847, 857, 859),"KK":(710, 727, 750, 762),"QQ":(626, 660, 707, 724),"JJ":(543, 587, 631, 676),"TT":(485, 543, 605, 638),"99":(412, 517, 563, 612),"88":(370, 480, 544, 596),"AKs":(475, 583, 667, 654),"AKo":(428, 562, 628, 657),"AQs":(400, 534, 596, 639),"77":(297, 436, 519, 557),"AJs":(361, 437, 574, 626),"AQo":(351, 486, 589, 614),"KQs":(387, 411, 481, 529),"ATs":(339, 414, 540, 588),"AJo":(330, 426, 549, 584),"66":(307, 398, 482, 533),"KJs":(389, 379, 437, 502),"ATo":(316, 376, 515, 573),"KQo":(341, 379, 450, 501),"A9s":(332, 387, 486, 546),"KTs":(354, 367, 429, 490),"QJs":(379, 376, 389, 457),"55":(287, 356, 452, 507),"A8s":(320, 386, 473, 546),"KJo":(339, 329, 404, 468),"A9o":(300, 348, 453, 518),"K9s":(322, 338, 410, 460),"QTs":(339, 344, 382, 445),"A7s":(322, 344, 449, 511),"KTo":(321, 330, 391, 458),"A5s":(318, 367, 421, 478),"QJo":(339, 329, 358, 419),"A8o":(297, 357, 439, 505),"A6s":(301, 348, 429, 481),"44":(278, 350, 438, 491),"JTs":(357, 349, 363, 408),"A4s":(302, 350, 421, 480),"K8s":(312, 328, 390, 447),"Q9s":(324, 326, 361, 422),"A7o":(301, 311, 414, 478),"QTo":(321, 309, 354, 419),"J9s":(338, 322, 347, 401),"K7s":(311, 319, 372, 433),"A3s":(293, 351, 416, 468),"A5o":(287, 326, 395, 455),"K9o":(289, 303, 376, 436),"A6o":(281, 309, 392, 450),"A2s":(292, 340, 401, 465),"33":(255, 333, 418, 467),"T9s":(336, 333, 343, 381),"A4o":(276, 318, 379, 451),"K8o":(286, 290, 363, 416),"Q8s":(310, 300, 350, 399),"K6s":(305, 314, 350, 414),"J8s":(323, 303, 334, 376),"JTo":(329, 320, 340, 384),"Q9o":(290, 293, 340, 396),"A3o":(273, 308, 374, 435),"K5s":(298, 304, 346, 408),"T8s":(327, 309, 328, 365),"Q7s":(296, 294, 343, 397),"K7o":(283, 283, 348, 400),"J9o":(309, 290, 316, 371),"22":(241, 309, 393, 437),"A2o":(260, 299, 362, 428),"K4s":(287, 293, 341, 395),"98s":(302, 347, 383, 380),"Q6s":(283, 282, 339, 392),"T9o":(304, 301, 323, 356),"J7s":(298, 295, 326, 364),"K3s":(276, 290, 329, 395),"Q8o":(276, 276, 322, 379),"K6o":(272, 271, 330, 384),"T7s":(301, 296, 319, 353),"K2s":(275, 283, 324, 385),"Q5s":(288, 279, 329, 384),"J8o":(290, 274, 308, 353),"97s":(294, 322, 339, 357),"K5o":(263, 266, 320, 374),"87s":(293, 334, 352, 357),"Q7o":(263, 259, 311, 364),"T8o":(287, 281, 308, 339),"J6s":(285, 276, 311, 356),"Q4s":(273, 274, 319, 374),"K4o":(258, 259, 310, 368),"J5s":(284, 268, 302, 350),"98o":(275, 307, 352, 352),"T6s":(290, 282, 310, 344),"Q3s":(269, 264, 309, 368),"96s":(284, 300, 320, 338),"J7o":(269, 262, 296, 334),"Q6o":(252, 251, 307, 357),"K3o":(249, 248, 303, 355),"86s":(281, 310, 334, 338),"Q2s":(267, 256, 302, 359),"J4s":(275, 262, 290, 346),"76s":(282, 324, 345, 342),"T7o":(272, 266, 291, 322),"K2o":(244, 242, 296, 349),"Q5o":(256, 249, 295, 350),"97o":(269, 291, 311, 329),"T5s":(279, 268, 296, 332),"J3s":(265, 253, 288, 338),"87o":(264, 303, 328, 331),"95s":(272, 282, 299, 327),"T4s":(270, 259, 285, 324),"Q4o":(243, 242, 288, 345),"65s":(274, 309, 328, 327),"J6o":(254, 246, 276, 326),"J2s":(265, 243, 276, 332),"85s":(273, 290, 313, 318),"75s":(268, 302, 320, 325),"96o":(255, 272, 290, 309),"Q3o":(237, 232, 279, 332),"T6o":(256, 253, 277, 311),"J5o":(248, 236, 268, 319),"T3s":(262, 251, 277, 318),"86o":(253, 282, 302, 310),"Q2o":(230, 222, 273, 326),"54s":(263, 294, 311, 311),"T2s":(258, 243, 270, 310),"64s":(258, 290, 308, 311),"76o":(255, 294, 316, 310),"94s":(258, 262, 279, 310),"J4o":(242, 230, 258, 310),"74s":(258, 283, 300, 308),"84s":(262, 276, 290, 306),"T5o":(245, 239, 264, 299),"95o":(244, 254, 269, 294),"J3o":(236, 220, 251, 304),"53s":(249, 277, 293, 300),"T4o":(240, 230, 254, 293),"93s":(250, 254, 268, 299),"65o":(246, 283, 297, 296),"63s":(246, 273, 290, 297),"J2o":(230, 213, 242, 298),"85o":(244, 263, 283, 287),"83s":(249, 258, 272, 290),"75o":(241, 274, 290, 294),"43s":(243, 268, 280, 285),"T3o":(231, 219, 246, 286),"92s":(245, 245, 261, 290),"73s":(242, 265, 280, 287),"54o":(237, 268, 282, 279),"82s":(246, 247, 263, 283),"64o":(232, 259, 280, 277),"T2o":(224, 212, 240, 277),"94o":(228, 231, 248, 276),"52s":(236, 262, 275, 279),"74o":(228, 254, 271, 272),"84o":(232, 247, 263, 272),"62s":(230, 250, 266, 272),"42s":(230, 250, 262, 268),"93o":(222, 223, 237, 266),"53o":(223, 246, 263, 262),"63o":(220, 243, 260, 262),"83o":(222, 226, 241, 258),"73o":(218, 237, 252, 253),"43o":(218, 237, 250, 248),"92o":(216, 212, 227, 256),"32s":(226, 239, 254, 258),"82o":(220, 214, 230, 251),"52o":(210, 231, 245, 243),"72s":(226, 228, 246, 252),"62o":(206, 221, 238, 238),"42o":(206, 219, 231, 231),"72o":(195, 199, 216, 220),"32o":(199, 209, 223, 221)}
RANGE_PCTS = (0.05, 0.10, 0.20, 0.35)

# three_card_score values at percentiles 0, 0.5, 1, ... 100 (from 40k random three-card hands)
SCORE_QUANTILES = (0.397,0.413,0.421,0.426,0.431,0.439,0.445,0.448,0.451,0.451,0.455,0.456,0.461,0.463,0.465,0.466,0.467,0.468,0.472,0.473,0.474,0.478,0.478,0.479,0.482,0.484,0.484,0.487,0.489,0.490,0.491,0.496,0.497,0.498,0.500,0.501,0.502,0.504,0.505,0.506,0.507,0.510,0.510,0.512,0.514,0.515,0.517,0.518,0.520,0.522,0.522,0.524,0.525,0.526,0.527,0.528,0.529,0.530,0.532,0.534,0.534,0.536,0.537,0.539,0.541,0.542,0.543,0.544,0.546,0.547,0.549,0.550,0.551,0.553,0.555,0.556,0.558,0.559,0.560,0.562,0.563,0.564,0.565,0.566,0.568,0.569,0.570,0.572,0.573,0.575,0.576,0.578,0.579,0.580,0.581,0.582,0.583,0.585,0.586,0.588,0.589,0.590,0.592,0.594,0.595,0.596,0.597,0.598,0.600,0.601,0.601,0.603,0.603,0.605,0.606,0.607,0.609,0.610,0.612,0.613,0.614,0.615,0.616,0.618,0.619,0.621,0.622,0.623,0.624,0.625,0.625,0.627,0.628,0.629,0.631,0.631,0.634,0.635,0.637,0.639,0.641,0.642,0.643,0.645,0.646,0.648,0.650,0.652,0.653,0.655,0.656,0.658,0.659,0.660,0.662,0.663,0.665,0.666,0.667,0.670,0.672,0.674,0.677,0.678,0.681,0.683,0.686,0.688,0.690,0.693,0.695,0.697,0.700,0.703,0.705,0.708,0.712,0.715,0.717,0.722,0.728,0.734,0.737,0.747,0.751,0.767,0.774,0.788,0.795,0.813,0.822,0.833,0.840,0.848,0.857,0.867,0.882,0.893,0.903,0.916,0.965)


def cls2(a, b):
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


def range_equity(cls, width):
    """Equity of a two-card class vs one opponent holding the top `width` fraction of hands."""
    if width >= 0.99:
        return PRE[cls][0] / 1000.0
    row = RANGE_EQ[cls]
    if width <= RANGE_PCTS[0]:
        return row[0] / 1000.0
    for i in range(1, len(RANGE_PCTS)):
        if width <= RANGE_PCTS[i]:
            lo, hi = RANGE_PCTS[i - 1], RANGE_PCTS[i]
            t = (width - lo) / (hi - lo)
            return (row[i - 1] + (row[i] - row[i - 1]) * t) / 1000.0
    # between 35% and random
    t = (width - 0.35) / 0.65
    return (row[3] + (PRE[cls][0] - row[3]) * t) / 1000.0


def three_card_score(cards):
    best = -1.0
    best_pair = (0, 1)
    eqs = []
    for i, j in ((0, 1), (0, 2), (1, 2)):
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
    if ranks[0] == ranks[1] or ranks[1] == ranks[2]:
        bonus += 0.015
        if ranks[0] == ranks[1] == ranks[2]:
            bonus -= 0.02
    eqs.sort(reverse=True)
    bonus += 0.25 * max(0.0, eqs[1] - 0.45)
    return best + bonus, best_pair


def score_percentile(score):
    """Fraction of random three-card hands at least this strong (0 = best)."""
    q = SCORE_QUANTILES
    lo, hi = 0, len(q) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if q[mid] < score:
            lo = mid + 1
        else:
            hi = mid
    return max(0.0, 1.0 - lo / (len(q) - 1))


# ----------------------------------------------------------------------------------------------
# Memory record
# ----------------------------------------------------------------------------------------------
NSEATS = 10
NC = 20
(HANDS, VPIP, PFR, LIMP, ALLIN_PRE, FTO_CH, FTO, THREEBET, PBETS, PCALLS, PFOLDS, CBET_CH, CBET,
 SHOWDOWNS, BLUFFS, EXP_LOW, EXP_HIGH, EXP_PAIRB, RRAISE, WINS_NOSD) = range(NC)
REC_VERSION = 4
# version u8, hand_no u16, street u8, pre_raises u8, aggressor i8, masks 6 x u16
# (vpip, pfr, allin, ftoch, limp, river_bettors), flags u8, nraisers_street u8,
# board 5 x u8, exposed 10 x u8, stacks 10 x u16, counters 200 x u16, crc u32
REC = struct.Struct("<BHBBb6HBB5B10B10H200HI")
REC_SIZE = REC.size
F_STREET_BET = 1
F_CBET_PENDING = 2


def fresh_record():
    return {
        "hand": 0, "street": 0, "pre_raises": 0, "aggressor": -1,
        "m_vpip": 0, "m_pfr": 0, "m_allin": 0, "m_ftoch": 0, "m_limp": 0, "m_river": 0,
        "flags": 0, "nraisers_street": 0,
        "board": [NOCARD] * 5, "exposed": [NOCARD] * NSEATS, "stacks": [0] * NSEATS,
        "counters": [[0] * NC for _ in range(NSEATS)],
    }


def pack_record(r):
    flat = []
    for row in r["counters"]:
        flat.extend(v if v < 65535 else 65535 for v in row)
    body = REC.pack(
        REC_VERSION, r["hand"] & 0xFFFF, r["street"] & 0xFF, min(255, r["pre_raises"]),
        max(-128, min(127, r["aggressor"])),
        r["m_vpip"] & 0xFFFF, r["m_pfr"] & 0xFFFF, r["m_allin"] & 0xFFFF, r["m_ftoch"] & 0xFFFF,
        r["m_limp"] & 0xFFFF, r["m_river"] & 0xFFFF, r["flags"] & 0xFF, min(255, r["nraisers_street"]),
        *r["board"], *r["exposed"], *[min(65535, max(0, int(s))) for s in r["stacks"]], *flat, 0,
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
    off = 13
    board = list(v[off:off + 5]); off += 5
    exposed = list(v[off:off + 10]); off += 10
    stacks = list(v[off:off + 10]); off += 10
    counters = [list(v[off + i * NC: off + (i + 1) * NC]) for i in range(NSEATS)]
    return {
        "hand": v[1], "street": v[2], "pre_raises": v[3], "aggressor": v[4],
        "m_vpip": v[5], "m_pfr": v[6], "m_allin": v[7], "m_ftoch": v[8], "m_limp": v[9], "m_river": v[10],
        "flags": v[11], "nraisers_street": v[12],
        "board": board, "exposed": exposed, "stacks": stacks, "counters": counters,
    }


# ----------------------------------------------------------------------------------------------
# Event feed -> per-seat counters (per hand, not per event)
# ----------------------------------------------------------------------------------------------
PRIOR_W = 8.0


def rate(count, chances, prior):
    return (count + prior * PRIOR_W) / (chances + PRIOR_W)


def feed(rec, state):
    counters = rec["counters"]
    seats_now = state.seats
    nseats = min(len(seats_now), NSEATS)
    board_cards = rec["board"]
    for ev in state.events:
        k = ev.kind
        s = ev.seat
        if k == "hand":
            rec["hand"] = ev.amount
            rec["street"] = 0
            rec["pre_raises"] = 0
            rec["aggressor"] = -1
            rec["m_vpip"] = rec["m_pfr"] = rec["m_allin"] = rec["m_ftoch"] = rec["m_limp"] = rec["m_river"] = 0
            rec["flags"] = 0
            rec["nraisers_street"] = 0
            for i in range(5):
                board_cards[i] = NOCARD
            for i in range(NSEATS):
                rec["exposed"][i] = NOCARD
            if ev.amount == state.hand_number:
                # hand-start stacks for this hand: stack + bet is exact before the flop
                for i in range(nseats):
                    st = seats_now[i]
                    rec["stacks"][i] = st.stack + st.bet
            for i in range(nseats):
                if rec["stacks"][i] > 0:
                    counters[i][HANDS] += 1
            continue
        if s is None:
            if k == "board":
                n = sum(1 for c in board_cards if c != NOCARD)
                for c in ev.cards:
                    if n < 5:
                        board_cards[n] = CODE.get(c, NOCARD)
                        n += 1
                rec["street"] = 1 if n <= 3 else (2 if n == 4 else 3)
                rec["nraisers_street"] = 0
                rec["flags"] &= ~F_STREET_BET
                if n == 3 and rec["aggressor"] >= 0:
                    counters[rec["aggressor"]][CBET_CH] += 1
                    rec["flags"] |= F_CBET_PENDING
            continue
        if s >= NSEATS:
            continue
        c = counters[s]
        st = rec["street"]
        bit = 1 << s
        if k == "raise":
            if st == 0:
                if not rec["m_vpip"] & bit:
                    c[VPIP] += 1
                    rec["m_vpip"] |= bit
                if not rec["m_pfr"] & bit:
                    c[PFR] += 1
                    rec["m_pfr"] |= bit
                if rec["pre_raises"] >= 1 and not rec["m_ftoch"] & bit:
                    c[FTO_CH] += 1
                    c[THREEBET] += 1
                    rec["m_ftoch"] |= bit
                rec["pre_raises"] += 1
                rec["aggressor"] = s
                sb = rec["stacks"][s]
                if sb > 0 and ev.amount >= 0.9 * sb and not rec["m_allin"] & bit:
                    c[ALLIN_PRE] += 1
                    rec["m_allin"] |= bit
            else:
                c[PBETS] += 1
                if rec["flags"] & F_STREET_BET:
                    c[RRAISE] += 1
                if st == 1 and (rec["flags"] & F_CBET_PENDING) and s == rec["aggressor"] and not rec["flags"] & F_STREET_BET:
                    c[CBET] += 1
                    rec["flags"] &= ~F_CBET_PENDING
                if st == 3:
                    rec["m_river"] |= bit
                rec["flags"] |= F_STREET_BET
                rec["nraisers_street"] += 1
        elif k == "call":
            if st == 0:
                if not rec["m_vpip"] & bit:
                    c[VPIP] += 1
                    rec["m_vpip"] |= bit
                if rec["pre_raises"] == 0:
                    if not rec["m_limp"] & bit:
                        c[LIMP] += 1
                        rec["m_limp"] |= bit
                elif not rec["m_ftoch"] & bit:
                    c[FTO_CH] += 1
                    rec["m_ftoch"] |= bit
            else:
                c[PCALLS] += 1
        elif k == "check":
            if st == 1 and (rec["flags"] & F_CBET_PENDING) and s == rec["aggressor"]:
                rec["flags"] &= ~F_CBET_PENDING
        elif k == "fold":
            if st == 0:
                if rec["pre_raises"] >= 1 and not rec["m_ftoch"] & bit:
                    c[FTO_CH] += 1
                    c[FTO] += 1
                    rec["m_ftoch"] |= bit
            elif rec["flags"] & F_STREET_BET:
                c[PFOLDS] += 1
        elif k == "reveal":
            if ev.cards:
                code = CODE.get(ev.cards[0], NOCARD)
                rec["exposed"][s] = code
                if code != NOCARD and any(rc != NOCARD and rc // 4 == code // 4 for rc in board_cards[:3]):
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
                if rec["m_river"] & bit:
                    full = [CARD_BY_CODE[x] for x in codes if x != NOCARD] + [CARD_BY_CODE[b] for b in board_cards if b != NOCARD]
                    if len(full) >= 5 and (eval7.evaluate(full) >> 24) == 0:
                        c[BLUFFS] += 1
        elif k == "win":
            if rec["street"] >= 1 and not any(seats_now[i].shown_cards for i in range(nseats) if i != s) and ev.amount:
                c[WINS_NOSD] += 1
        elif k == "stack":
            rec["stacks"][s] = ev.amount


# ----------------------------------------------------------------------------------------------
# Labels
# ----------------------------------------------------------------------------------------------
def labels_for(c):
    out = set()
    hands = c[HANDS]
    if hands >= 4 and c[ALLIN_PRE] >= 0.5 * hands and c[ALLIN_PRE] >= 3:
        out.add("SHOVER")
    if hands >= 6 and c[VPIP] <= 0.02 * hands and c[FTO] >= 3:
        out.add("FOLDBOT")
    vp = rate(c[VPIP], hands, 0.25)
    if hands >= 15 and vp <= 0.14:
        out.add("NIT")
    if hands >= 12 and rate(c[LIMP], hands, 0.02) >= 0.10:
        out.add("LIMPER")
    if hands >= 8 and rate(c[PFR], hands, 0.18) >= 0.42:
        out.add("MANIAC")
    pc = c[PCALLS] + c[PFOLDS]
    if pc >= 6 and c[PCALLS] / pc >= 0.65:
        out.add("STATION")
    if pc >= 6 and c[PFOLDS] / pc >= 0.75:
        out.add("FOLDER")
    if c[CBET_CH] >= 4 and c[CBET] / c[CBET_CH] >= 0.75:
        out.add("AUTO_CBET")
    if c[SHOWDOWNS] >= 4 and c[BLUFFS] == 0:
        out.add("NO_BLUFF")
    if c[SHOWDOWNS] >= 3 and c[BLUFFS] / c[SHOWDOWNS] >= 0.4:
        out.add("OVERBLUFF")
    if c[EXP_LOW] + c[EXP_HIGH] >= 2:
        if c[EXP_HIGH] == 0:
            out.add("EXPOSE_LOW")
        elif c[EXP_LOW] == 0:
            out.add("EXPOSE_HIGH")
    return out


# ----------------------------------------------------------------------------------------------
# Hand strength
# ----------------------------------------------------------------------------------------------
def has_straight(mask):
    lowmask = ((mask >> 12) & 1) | (mask << 1)
    for start in range(0, 10):
        w = 0b11111 << start
        if lowmask & w == w:
            return True
    return False


def straight_outs(mask):
    lowmask = ((mask >> 12) & 1) | (mask << 1)
    outs = 0
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


# class -> equity vs one opponent (who keeps best 2 of 3), by street
# 0 air, 1 weak pair, 2 top pair, 3 overpair/TPTK, 4 two pair, 5 set/trips, 6 straight, 7 flush, 8 FH+
EQ_F = (0.21, 0.40, 0.54, 0.61, 0.66, 0.82, 0.86, 0.90, 0.95)
EQ_T = (0.15, 0.36, 0.53, 0.60, 0.66, 0.84, 0.89, 0.92, 0.96)
EQ_R = (0.08, 0.30, 0.50, 0.58, 0.64, 0.84, 0.90, 0.93, 0.97)
DRAW_EQ = {"gut": (0.15, 0.08), "oesd": (0.27, 0.15), "fd": (0.31, 0.17), "fd_oesd": (0.44, 0.27),
           "fd_gut": (0.37, 0.22), "over2": (0.09, 0.04), "over1": (0.04, 0.02)}


def analyze(hole, board, dead_codes=()):
    """hole: 2 card strings, board: 3-5 card strings -> dict(cls, draw, eq, value)."""
    hc = [CARD[c] for c in hole]
    bc = [CARD[c] for c in board]
    value = eval7.evaluate(hc + bc)
    cat = value >> 24
    hr = [RANK_IDX[c[0]] for c in hole]
    br = [RANK_IDX[c[0]] for c in board]
    btop = max(br)
    bcount = {}
    for r in br:
        bcount[r] = bcount.get(r, 0) + 1
    board_pairs = sum(1 for v in bcount.values() if v >= 2)
    board_trips = any(v >= 3 for v in bcount.values())
    pocket = hr[0] == hr[1]
    hits = [r for r in hr if r in bcount]  # hole ranks matching the board
    street = len(board)
    bsuits = {}
    for c in board:
        bsuits[c[1]] = bsuits.get(c[1], 0) + 1
    if cat >= 6:
        cls = 8
        if board_trips and not pocket and not hits:
            cls = 4  # board trips + our pair... actually full house with board trips, weak
    elif cat == 5:
        cls = 7
        suit = max(bsuits, key=bsuits.get)
        ours = [c for c in hole if c[1] == suit]
        if bsuits[suit] >= 4 and (not ours or RANK_IDX[ours[0][0]] < RANK_IDX["T"]):
            cls = 4  # one-card low flush on a four-flush board
        elif bsuits[suit] >= 4 and RANK_IDX[max(ours, key=lambda c: RANK_IDX[c[0]])[0]] < RANK_IDX["K"]:
            cls = 6
    elif cat == 4:
        cls = 6
        bmask = 0
        for r in br:
            bmask |= 1 << r
        if street == 5 and has_straight(bmask):
            cls = 2  # straight on the board; we have at best a tie
    elif cat == 3:
        if pocket and hr[0] in bcount:
            cls = 5  # set
        elif hits and bcount.get(hits[0], 0) >= 2:
            cls = 5 if max(hr) >= RANK_IDX["T"] or pocket else 4  # trips, kicker matters
        else:
            cls = 0 if not hits else 1  # board trips
    elif cat == 2:
        if pocket:
            # pocket pair + board pair
            cls = 3 if hr[0] > btop else (1 if hr[0] < max(k for k, v in bcount.items() if v >= 2) else 2)
            if hr[0] > btop:
                cls = 3
        elif len(hits) == 2:
            cls = 4  # both hole cards pair the board
        elif len(hits) == 1 and board_pairs >= 1:
            cls = 2 if hits[0] == btop else 1  # one pair of ours + board pair
        else:
            cls = 0 if max(hr) < btop else 1  # two pair on the board, we play kicker
    elif cat == 1:
        if pocket:
            cls = 3 if hr[0] > btop else 1
        elif hits:
            top = hits[0] == btop
            kicker = max(hr)
            cls = (3 if kicker >= RANK_IDX["Q"] and top else 2 if top else 1)
        else:
            cls = 0  # board pair only
    else:
        cls = 0
    table = EQ_F if street == 3 else (EQ_T if street == 4 else EQ_R)
    eq = table[cls]
    if cls == 0:
        eq += 0.02 * (max(hr) >= RANK_IDX["Q"]) + 0.02 * (min(hr) > btop)
    draw = None
    if street < 5:
        suits = dict(bsuits)
        for c in hole:
            suits[c[1]] = suits.get(c[1], 0) + 1
        fsuit = None
        for s_, n_ in suits.items():
            if n_ == 4 and any(h[1] == s_ for h in hole):
                fsuit = s_
        fd = fsuit is not None and sum(1 for h in hole if h[1] == fsuit) >= 1
        mask = 0
        for r in hr + br:
            mask |= 1 << r
        bmask = 0
        for r in br:
            bmask |= 1 << r
        so = 0
        if not has_straight(mask):
            so = straight_outs(mask)
            if straight_outs(bmask) >= so:
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
        elif cls == 0 and max(hr) > btop:
            draw = "over1"
        if draw and cls <= 3:
            add = DRAW_EQ[draw][0 if street == 3 else 1]
            if fd:
                dead = sum(1 for dc in dead_codes if dc != NOCARD and SUITS[dc % 4] == fsuit)
                add -= 0.035 * dead
                if sum(1 for h in hole if h[1] == fsuit) == 1 and RANK_IDX[[h for h in hole if h[1] == fsuit][0][0]] < RANK_IDX["J"]:
                    add -= 0.06  # one-card low flush draw
            eq = min(0.95, eq + max(0.0, add) * (1.0 if cls == 0 else 0.6))
    return {"cls": cls, "draw": draw, "eq": eq, "value": value}


def multiway(eq, n_opp):
    if n_opp <= 1:
        return eq
    return eq ** (1.0 + 0.55 * (n_opp - 1))


# ----------------------------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------------------------
def choose(state, kind, total=0):
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
    if "check" in kinds:
        return Action.check()
    if "fold" in kinds:
        return Action.fold()
    if la:
        return Action(la[0].kind, la[0].min_amount)
    return Action.fold()


def position_of(state, live, seat):
    n = len(live)
    total = len(state.seats)
    order = []
    s = state.button
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


# tuning knobs (arena variants override these)
K = {"open_mult": 1.0, "lam": 0.40, "cbet_dry": 0.6, "cbet_rand": 0.35, "strong": 0.54, "call_margin": 0.03,
     "three_bet": 0.05, "steal_cap": 0.60, "shove_w_mult": 1.0, "bluff_river": 0.18, "raise_bluff": 0.10,
     "reveal_mix": 0.25, "unknown_expose_w": 0.35, "cold_call": 0.09, "push_bb": 13, "midshove_bb": 20, "midshove_w": 0.8}

OPEN_W = {"ep": 0.21, "mp": 0.25, "co": 0.32, "btn": 0.44, "sb": 0.40, "bb": 0.0}
PUSH_W = {"ep": 0.14, "mp": 0.19, "co": 0.26, "btn": 0.36, "sb": 0.45, "bb": 0.0}


def rng_for(state):
    return random.Random((zlib.crc32(state.config.table_id.encode()) * 1000003 + state.hand_number * 7919 + len(state.history)) & 0xFFFFFFFF)


def shove_range_width(stack_bb, n_prior_raises, label):
    """How wide an opponent's all-in range is, as a fraction of hands (1.0 = any two)."""
    if "SHOVER" in label:
        return 1.0
    if n_prior_raises == 0:
        w = 0.55 if stack_bb <= 7 else 0.38 if stack_bb <= 12 else 0.24 if stack_bb <= 20 else 0.14
    elif n_prior_raises == 1:
        w = 0.24 if stack_bb <= 14 else 0.14 if stack_bb <= 25 else 0.08
    else:
        w = 0.06 if stack_bb <= 30 else 0.03
    if "MANIAC" in label:
        w = min(1.0, w * 1.7)
    if "NIT" in label:
        w *= 0.6
    return w


# ----------------------------------------------------------------------------------------------
# Agent
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
    # everyone dealt in (positions), and everyone still contesting the pot (equity)
    live = [s.seat for s in seats if s.status != "busted"]
    opp_live = [s for s in live if s != me]
    active = [s.seat for s in seats if s.status in ("active", "all_in") and s.seat != me]
    n_opp = max(1, len(active))
    counters = rec["counters"]
    labels = {s: labels_for(counters[s]) if s < NSEATS else set() for s in opp_live}
    rnd = rng_for(state)
    # risk premium (ICM-ish)
    paid = sum(1 for p in state.config.payouts if p > 0)
    players_left = state.players_remaining
    hands_to_cap = state.config.hand_cap - state.hand_number
    alive = sorted((s.stack + s.bet for s in seats if s.status != "busted"), reverse=True)
    my_rank = alive.index(my_total) + 1 if my_total in alive else len(alive)
    if players_left <= 2:
        lam = 0.0
    else:
        lam = K["lam"]
        if players_left == paid + 1:
            lam += 0.30
        if hands_to_cap <= 25 and my_rank <= paid:
            lam += 0.30
        if my_rank == 1 and players_left >= 4:
            lam += 0.10
        # a fold-bot or nit at the table will outlast loose busts: survive it
        if any(("FOLDBOT" in labels[s] or "NIT" in labels[s]) for s in opp_live) and state.hand_number < 110:
            lam += 0.15
        lam = min(lam, 0.65)
    if len(state.board) == 0:
        return preflop(state, rec, labels, live, n_opp, my_total, lam, rnd)
    return postflop(state, rec, labels, live, n_opp, my_total, lam, rnd)


def preflop(state, rec, labels, live, n_opp, my_total, lam, rnd):
    me = state.seat
    bb = state.blinds.big_blind or 1
    cards = state.cards
    score, best_pair = three_card_score(cards)
    p = score_percentile(score)
    best_cls = cls2(cards[best_pair[0]], cards[best_pair[1]])
    eq1 = PRE[best_cls][0] / 1000.0 + 0.025
    pos = position_of(state, live, me)
    pot = state.pot
    to_call = state.to_call
    can_raise = state.can("raise")
    seats = state.seats
    opp_stacks = [seats[s].stack + seats[s].bet for s in live if s != me and seats[s].status != "folded"] or [my_total]
    eff = min(my_total, max(opp_stacks) if opp_stacks else my_total) / bb
    my_bb = my_total / bb
    hist = state.history
    raises = [e for e in hist if e.kind == "raise"]
    nraises = len(raises)
    limpers = sum(1 for e in hist if e.kind == "call") if nraises == 0 else 0
    raiser = raises[-1].seat if raises else None
    raiser_total = (seats[raiser].stack + seats[raiser].bet) if raiser is not None else 0
    acted = {e.seat for e in hist if e.kind in ("fold", "call", "raise", "check")}
    shovers_behind = [s for s in live if s != me and "SHOVER" in labels.get(s, ()) and s not in acted and seats[s].status == "active"]
    # opponents with money in this pot who have not folded (for multiway all-in equity)
    in_pot = [s for s in live if s != me and seats[s].bet > 0 and seats[s].status in ("active", "all_in")]
    # risk premium scales with how much of our stack the call puts at risk
    lam = lam * min(1.0, 2.0 * to_call / my_total) if my_total else lam
    # table fold-to-raise rate -> steal more when it is high
    tot_ch = sum(rec["counters"][s][FTO_CH] for s in live if s != me and s < NSEATS)
    tot_f = sum(rec["counters"][s][FTO] for s in live if s != me and s < NSEATS)
    table_fold = rate(tot_f, tot_ch, 0.75)
    steal_mult = 1.0
    if tot_ch >= 10 and table_fold >= 0.85:
        steal_mult = 1.35
    if n_opp >= 2:
        blind_seats = [s for s in live if s != me and position_of(state, live, s) in ("sb", "bb")]
        if blind_seats and all(("NIT" in labels[s] or "FOLDBOT" in labels[s]) for s in blind_seats):
            steal_mult = max(steal_mult, 1.6)

    if nraises == 0:
        if state.can("check"):
            # big blind, everyone limped or folded
            if p <= 0.14 and can_raise:
                return choose(state, "raise", bb * (3 + limpers))
            return choose(state, "check")
        if shovers_behind:
            thr = 0.62 + 0.15 * min(1.0, max(0.0, (eff - 10) / 40.0))
            if eq1 >= thr and can_raise:
                return choose(state, "raise", can_raise.max_amount)
            return choose(state, "fold")
        behind = [s for s in live if s != me and s not in acted and seats[s].status == "active"]
        if behind and can_raise and all("FOLDBOT" in labels.get(s, ()) for s in behind):
            return choose(state, "raise", can_raise.min_amount)  # everyone left folds to any raise
        width = min(K["steal_cap"], OPEN_W[pos] * steal_mult * K["open_mult"])
        if my_bb <= 5.5:
            if pos in ("btn", "sb", "co") or p <= 0.45:
                return choose(state, "raise", can_raise.max_amount if can_raise else 0)
            return choose(state, "fold")
        if my_bb <= K["push_bb"]:
            w = PUSH_W[pos] * steal_mult * K["shove_w_mult"]
            if p <= w and can_raise:
                return choose(state, "raise", can_raise.max_amount)
            return choose(state, "fold")
        if limpers:
            if p <= width * 0.8 and can_raise:
                return choose(state, "raise", bb * (3 + limpers))
            if p <= width * 1.15 and pos in ("btn", "sb", "co") and to_call <= bb:
                return choose(state, "call")
            return choose(state, "fold")
        if p <= width and can_raise:
            if my_bb <= K["midshove_bb"] and p <= PUSH_W[pos] * K["midshove_w"] * steal_mult:
                return choose(state, "raise", can_raise.max_amount)  # the field folds to raises ~80%: take it now
            if my_bb <= 20:
                size = int(2.2 * bb)
            elif pos == "sb":
                size = 3 * bb
            else:
                size = int(2.6 * bb)
            return choose(state, "raise", size)
        return choose(state, "fold")

    # facing a raise
    price = to_call / (pot + to_call) if (pot + to_call) > 0 else 1.0
    opened_by_me = any(e.kind == "raise" and e.seat == me for e in hist)
    raiser_label = labels.get(raiser, set()) if raiser is not None else set()
    facing_allin = raiser is not None and (seats[raiser].status == "all_in" or to_call >= 0.5 * my_total)
    if facing_allin or "SHOVER" in raiser_label:
        # equity vs the raiser's range, discounted for extra players in the pot
        prior = nraises - 1
        width = shove_range_width(raiser_total / bb, prior, raiser_label)
        eq = range_equity(best_cls, width) + 0.02
        others = [s for s in in_pot if s != raiser]
        if others:
            # each extra player with chips committed: assume a medium range
            eq *= (pre_equity(best_cls, 1 + len(others)) / pre_equity(best_cls, 1)) ** 0.9
            eq -= 0.02 * len(others)
        need = price * (1.0 + lam) + 0.05
        if eff > 40 and prior >= 1:
            need += 0.05  # deep 3-bet/4-bet jams in this field are KK+ far too often
        if state.hand_number <= 40 and my_bb >= 60:
            need += 0.06  # no early deep flips
        if "SHOVER" in raiser_label:
            # a shover will shove again: wait for a real hand when deep
            thr = 0.62 + 0.15 * min(1.0, max(0.0, (eff - 10) / 40.0))
            if others:
                thr += 0.08
            ok = eq1 >= thr and eq >= need
        else:
            ok = eq >= need
        if my_bb <= 6 and state.players_remaining > 2 and eq >= need - 0.06:
            ok = True
        if not ok:
            return choose(state, "fold")
        if state.can("call") and (to_call >= 0.5 * my_total or seats[raiser].status == "all_in"):
            return choose(state, "call")
        return choose(state, "raise", can_raise.max_amount if can_raise else 0)
    if opened_by_me:
        # we opened, someone 3-bet (not all-in)
        if p <= 0.045 and can_raise:
            if eff <= 45:
                return choose(state, "raise", can_raise.max_amount)
            if p <= 0.012:
                return choose(state, "raise", int(2.6 * raises[-1].amount))
            return choose(state, "call")  # QQ/AK: see a flop deep rather than stack off
        if p <= 0.10 and to_call <= 0.14 * my_total and eff > 25:
            return choose(state, "call")
        if p <= 0.06 and eff <= 45 and can_raise:
            return choose(state, "raise", can_raise.max_amount)
        return choose(state, "fold")
    if nraises >= 2:
        if p <= (0.03 if eff <= 50 else 0.012) and can_raise:
            return choose(state, "raise", can_raise.max_amount)
        if p <= 0.06 and to_call <= 0.1 * my_total:
            return choose(state, "call")
        return choose(state, "fold")
    # facing a single open
    maniac = "MANIAC" in raiser_label
    nit = "NIT" in raiser_label
    v3 = K["three_bet"] * (1.6 if maniac else 1.0) * (0.6 if nit else 1.0)
    if p <= v3 and can_raise:
        if eff <= 25:
            return choose(state, "raise", can_raise.max_amount)
        return choose(state, "raise", int(2.4 * raises[-1].amount) + (bb if pos in ("sb", "bb") else 0))
    if my_bb <= 15:
        w = 0.10 if not maniac else 0.17
        if p <= w and can_raise:
            return choose(state, "raise", can_raise.max_amount)
        return choose(state, "fold")
    call_w = K["cold_call"] * (1.5 if maniac else 1.0) * (0.6 if nit else 1.0)
    if pos == "bb":
        if to_call <= 1.5 * bb:
            call_w = max(call_w, 0.38)
        elif to_call <= 2.5 * bb:
            call_w = max(call_w, 0.27)
        else:
            call_w = max(call_w, 0.16)
    elif pos in ("btn", "co"):
        call_w = max(call_w, 0.14)
    if p <= call_w and to_call <= 0.2 * my_total:
        return choose(state, "call")
    return choose(state, "fold")


def select(state, rec):
    cards = state.cards
    board = state.board
    if len(cards) != 3:
        return Action("select", cards=(2, 0))
    best = None
    for discard in range(3):
        keep = [cards[i] for i in range(3) if i != discard]
        a = analyze(keep, board)
        val = (a["eq"], a["value"])
        if best is None or val > best[0]:
            best = (val, discard, keep)
    _, discard, keep = best
    keep_idx = [i for i in range(3) if i != discard]
    br = [RANK_IDX[c[0]] for c in board]
    btop = max(br)
    suits = {}
    for c in board:
        suits[c[1]] = suits.get(c[1], 0) + 1
    two_tone = max(suits.values()) >= 2
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
        if r not in br and min(abs(r - b) for b in br) <= 2:
            sc += 1.0
        if r >= RANK_IDX["Q"]:
            sc += 0.6  # keep high cards hidden: they are what opponents fear least when shown low
        if r <= RANK_IDX["5"]:
            sc -= 0.3
        sc += rnd.random() * 0.3
        scores.append((sc, i))
    scores.sort()
    reveal = scores[0][1]
    if len(scores) > 1 and rnd.random() < K["reveal_mix"]:
        reveal = scores[1][1]
    return Action("select", cards=(discard, reveal))


def postflop(state, rec, labels, live, n_opp, my_total, lam, rnd):
    me = state.seat
    seats = state.seats
    cards = state.cards
    board = state.board
    pot = state.pot
    to_call = state.to_call
    can_raise = state.can("raise")
    bb = state.blinds.big_blind or 1
    if len(cards) != 2:
        return choose(state, "check") if to_call == 0 else choose(state, "fold")
    dead = [rec["exposed"][s] for s in live if s != me and s < NSEATS]
    a = analyze(cards, board, dead)
    eq1 = a["eq"]
    cls = a["cls"]
    br = [RANK_IDX[c[0]] for c in board]
    btop = max(br)
    bsuits = {}
    for c in board:
        bsuits[c[1]] = bsuits.get(c[1], 0) + 1
    # exposed cards: threat (their shown card connects) and information (expose-low players)
    threat = 0.0
    for s in live:
        if s == me or s >= NSEATS or seats[s].status == "folded":
            continue
        ec = rec["exposed"][s]
        if ec == NOCARD:
            continue
        er, es = ec // 4, SUITS[ec % 4]
        lab = labels.get(s, set())
        if er == btop:
            threat += 0.14
        elif er in br:
            threat += 0.07
        elif er > btop:
            threat += 0.03
        if bsuits.get(es, 0) >= 2 and len(board) < 5:
            threat += 0.04
        # expose-low players (most of the field) show their weaker card: hidden >= shown
        low_w = 1.0 if "EXPOSE_LOW" in lab else (0.0 if "EXPOSE_HIGH" in lab else K["unknown_expose_w"])
        if low_w and er >= RANK_IDX["T"]:
            if er == RANK_IDX["A"]:
                threat += 0.30 * low_w  # hidden >= A: pocket aces
            elif er >= RANK_IDX["Q"]:
                threat += 0.16 * low_w  # KK/AK-type holdings
            else:
                threat += 0.07 * low_w
        if "EXPOSE_HIGH" in lab and er <= RANK_IDX["9"] and er not in br:
            threat -= 0.08
    if cls <= 3:
        eq1 = max(0.03, eq1 - min(0.22, threat))
    eq = multiway(eq1, n_opp)
    street = len(board)
    # this hand's history: preflop aggressor and bets on this street
    hist = state.history
    pre_aggr = -1
    street_bets = 0
    last_bettor = -1
    seen_board = 0
    for e in hist:
        if e.kind == "board":
            seen_board += 1
            street_bets = 0
            continue
        if e.kind == "raise":
            if seen_board == 0:
                pre_aggr = e.seat
            else:
                street_bets += 1
                last_bettor = e.seat
    aggressor = pre_aggr == me
    # streets on which an opponent bet or raised this hand (multi-street aggression tell)
    opp_aggr_streets = 0
    seen_board = 0
    street_had = False
    for e in hist:
        if e.kind == "board":
            if street_had:
                opp_aggr_streets += 1
            street_had = False
            seen_board += 1
        elif e.kind == "raise" and seen_board >= 1 and e.seat != me:
            street_had = True
    if street_had:
        opp_aggr_streets += 1
    # scary boards: four to a straight or four to a flush
    bmask = 0
    for r in br:
        bmask |= 1 << r
    four_flush = max(bsuits.values()) >= 4
    four_straight = straight_outs(bmask) >= 1 and len(set(br)) >= 4 and not has_straight(bmask)
    scary = four_flush or four_straight
    if scary and cls <= 4:
        eq1 = max(0.03, eq1 - 0.15)
        eq = multiway(eq1, n_opp)
    opp_labels = set()
    for s in live:
        if s != me and seats[s].status != "folded":
            opp_labels |= labels.get(s, set())
    station = "STATION" in opp_labels
    folder = "FOLDER" in opp_labels and n_opp == 1
    foldbot = n_opp == 1 and "FOLDBOT" in opp_labels
    nobluff = "NO_BLUFF" in opp_labels
    bettor_label = labels.get(last_bettor, set()) if last_bettor >= 0 else set()
    ranks_sorted = sorted(br)
    dry = len(set(br)) == len(br) and max(bsuits.values()) <= 2 and (
        ranks_sorted[-1] - ranks_sorted[0] >= 5 or (len(board) == 3 and ranks_sorted[1] - ranks_sorted[0] >= 2 and ranks_sorted[2] - ranks_sorted[1] >= 2))

    def bet(frac):
        size = max(int(pot * frac), bb)
        target = seats[me].bet + to_call + size
        if (target - seats[me].bet) >= 0.62 * seats[me].stack:
            if scary and cls <= 4 and street >= 4:
                return choose(state, "call") if to_call else choose(state, "check")
            target = can_raise.max_amount if can_raise else target
        return choose(state, "raise", target)

    if to_call == 0:
        if (foldbot or folder) and can_raise:
            return bet(0.5)
        strong = K["strong"] if not station else K["strong"] - 0.06
        if eq >= strong and can_raise:
            if cls >= 4:
                return bet(0.85 if station else 0.7)
            return bet(0.75 if station else (0.45 if street == 3 else 0.6))
        if can_raise and not station and n_opp <= 2:
            if street == 3 and aggressor:
                if eq1 >= 0.30 or (dry and rnd.random() < K["cbet_dry"]) or (n_opp == 1 and rnd.random() < K["cbet_rand"]):
                    return bet(0.4)
            if street == 4 and aggressor and street_bets == 0 and a["draw"] in ("fd", "oesd", "fd_oesd", "fd_gut") and n_opp == 1:
                return bet(0.55)
            if street == 5 and n_opp == 1 and cls == 0 and not nobluff and rnd.random() < K["bluff_river"] and "STATION" not in opp_labels:
                return bet(0.6)  # occasional river bluff heads-up
        return choose(state, "check")

    # facing a bet
    price = to_call / (pot + to_call)
    big = to_call >= 0.4 * my_total
    small = to_call <= 0.4 * (pot - to_call)  # bet of at most 40% of the pot before it
    need = price + K["call_margin"] + (0.0 if street == 3 else 0.02 if street == 4 else 0.05)
    if street_bets >= 2:
        need += 0.10  # raised, not just bet
    if nobluff and cls <= 3:
        need += 0.08
    if opp_aggr_streets >= 2 and cls <= 3 and not small:
        need += 0.10
    if cls <= 1 and not small and street >= 4 and a["draw"] is None:
        need += 0.10  # weak pair facing a real bet on turn/river
    if "MANIAC" in bettor_label or "OVERBLUFF" in bettor_label or "AUTO_CBET" in bettor_label and street == 3:
        need -= 0.06
    if big:
        need = price * (1.0 + lam * min(1.0, 2.0 * to_call / my_total)) + 0.04 + (0.08 if street_bets >= 2 and cls <= 4 else 0.0)
        if opp_aggr_streets >= 2 and cls <= 3:
            need += 0.12  # bet/raised on two streets already: one pair is rarely good
        if "MANIAC" in bettor_label or "OVERBLUFF" in bettor_label:
            need -= 0.07
        if eq >= need:
            if can_raise and cls >= 5 and eq >= 0.72:
                return choose(state, "raise", can_raise.max_amount)
            return choose(state, "call")
        return choose(state, "fold")
    # raise for value with strong hands (not into a re-raise unless very strong)
    if can_raise and ((cls >= 5 and eq >= 0.72 and street_bets == 1) or (cls >= 7 and eq >= 0.80)):
        return bet(1.0)
    if can_raise and cls == 4 and eq >= 0.68 and street_bets == 1 and street <= 4 and rnd.random() < 0.5:
        return bet(0.9)
    # draws: implied odds when stacks are deep
    if a["draw"] in ("fd", "oesd", "fd_oesd", "fd_gut") and street < 5 and to_call <= 0.15 * my_total:
        need -= 0.05
    if small and street < 5 and (cls >= 1 or a["draw"] is not None):
        need -= 0.04
    if eq >= need:
        return choose(state, "call")
    # occasional raise-bluff vs a lone small flop bet on a dry board
    if can_raise and street == 3 and n_opp == 1 and small and dry and cls == 0 and not station and rnd.random() < K["raise_bluff"]:
        return bet(1.0)
    return choose(state, "fold")


def _warmup():
    try:
        three_card_score(("As", "Kd", "7c"))
        analyze(("As", "Kd"), ("Ah", "7c", "2d"))
        analyze(("9s", "8s"), ("7s", "6d", "2s", "Kh"))
        analyze(("9s", "8s"), ("7s", "6d", "2s", "Kh", "2c"))
        unpack_record(pack_record(fresh_record()))
        range_equity("AKs", 0.12)
    except Exception:
        pass


_warmup()
gc.collect()
gc.freeze()
gc.disable()
