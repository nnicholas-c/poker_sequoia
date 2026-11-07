"""Double G: three-card discard/reveal strategy, written during the build window.

No persistent process state: lookup objects are immutable; learning lives in memory.
"""
import gc
import itertools
import json
import random
from pathlib import Path
import struct

import eval7
from poker_agent_sdk import Agent as BaseAgent, Action, icm

NAMES = tuple(r + s for r in '23456789TJQKA' for s in 'cdhs')
CARDS = tuple(eval7.Card(c) for c in NAMES)
INDEX = {c: i for i, c in enumerate(NAMES)}
PAIRS = ((0, 1), (0, 2), (1, 2))
EVAL = eval7.evaluate
VERSION = 2
USE_REVEALS = True
SMART_SELECT = True
ROLLOUT_SELECT = True
try:
    _raw = Path(__file__).with_name("preflop.bin").read_bytes()
    assert _raw[:4] == b"RVE1" and len(_raw) == 4 + 22100 * 12
    PREFLOP = tuple(struct.iter_unpack("<fff", _raw[4:]))
except (OSError, AssertionError):
    PREFLOP = ()


def fallback(state):
    for kind in ('check', 'fold', 'call'):
        if state.can(kind):
            return Action(kind)
    first = state.legal_actions[0]
    return Action(first.kind, first.min_amount)


def raise_to(state, amount):
    legal = state.can('raise')
    if legal:
        return Action.raise_to(max(legal.min_amount, min(legal.max_amount, int(amount))))
    return Action.call() if state.can('call') else fallback(state)


def pair_strength(a, b):
    """Smooth preflop ordering only, not a claim of measured equity."""
    x, y = sorted((a // 4 + 2, b // 4 + 2), reverse=True)
    if x == y:
        return .50 + .027 * (x - 2)
    value = .30 + .024 * (x - 2) + .012 * (y - 2)
    value += .025 if a % 4 == b % 4 else 0
    value += .022 if x - y == 1 else .010 if x - y == 2 else 0
    value -= .025 if x - y > 5 and x < 14 else 0
    return value


def pre_strength(hole):
    scores = sorted((pair_strength(hole[i], hole[j]) for i, j in itertools.combinations(range(len(hole)), 2)), reverse=True)
    if len(scores) == 1:
        return scores[0]
    # The third card provides an option after seeing the flop, not a third showdown card.
    return scores[0] + .10 * max(0, scores[1] - .44)


def flop_quality(hole, board):
    cards = hole + board
    rank = EVAL([CARDS[c] for c in cards])
    category = rank >> 24
    suits = [0, 0, 0, 0]
    mask = 0
    for c in cards:
        suits[c % 4] += 1
        mask |= 1 << (c // 4)
    flush_draw = max(suits) == 4 and any(suits[c % 4] == 4 for c in hole)
    straight_draw = 0
    for high in range(4, 13):
        straight_draw = max(straight_draw, ((mask >> (high - 4)) & 31).bit_count())
    straight_draw = max(straight_draw, (mask & ((1 << 12) | 15)).bit_count())
    # Category dominates ordinary high cards; strong draws can outrank a weak pair.
    value = category * 1.0 + ((rank & 0xffffff) / 0x1000000) * .3
    if category < 4:
        value += .82 if flush_draw else 0
        value += .38 if straight_draw >= 4 else 0
    top = max(c // 4 for c in board)
    value += .08 * sum(c // 4 > top for c in hole)
    return value


def choose_cards(state):
    if not SMART_SELECT or len(state.cards) != 3:
        return Action('select', cards=(2, 0))
    hole = [INDEX[c] for c in state.cards]
    board = [INDEX[c] for c in state.board]
    quality = [flop_quality([hole[i], hole[j]], board) for i, j in PAIRS]
    best = max(range(3), key=lambda i: quality[i])
    if ROLLOUT_SELECT:
        # Common runouts compare all three retained pairs on identical deals.
        # Opponents choose using the flop only; never let them see the runout.
        known = set(hole + board)
        for seat in state.seats:
            known.update(INDEX[c] for c in seat.shown_cards)
        deck = [c for c in range(52) if c not in known]
        rng = random.Random(sum((c+1)*53**k for k,c in enumerate(hole+board)))
        pairs = [[CARDS[hole[i]], CARDS[hole[j]]] for i,j in PAIRS]
        flop = [CARDS[c] for c in board]
        opponents = min(2, sum(s.seat != state.seat and s.status in ('active','all_in') for s in state.seats))
        scores = [0.0]*3
        trials = 16
        for trial in range(trials):
            deal = rng.sample(deck, 2+3*opponents)
            full = flop + [CARDS[c] for c in deal[:2]]
            rival = -1
            rival_ties = 0
            for seat in range(opponents):
                triple = [CARDS[c] for c in deal[2+3*seat:5+3*seat]]
                a,b,c=triple
                ab=EVAL([a,b]+flop);ac=EVAL([a,c]+flop);bc=EVAL([b,c]+flop)
                if ab>=ac and ab>=bc: held=[a,b]
                elif ac>=bc: held=[a,c]
                else: held=[b,c]
                rank = EVAL(held+full)
                if rank>rival: rival,rival_ties=rank,1
                elif rank==rival: rival_ties+=1
            for k,pair in enumerate(pairs):
                rank=EVAL(pair+full)
                scores[k]+=1 if rank>rival else 1/(rival_ties+1) if rank==rival else 0
        best=max(range(3),key=lambda k:scores[k]+.10*quality[k])
    i, j = PAIRS[best]
    discard = 3 - i - j
    # Conceal a board-pairing or draw-critical card. Mix equivalent exposures without
    # encoding hand strength into a deterministic high/low exposure convention.
    board_ranks = {c // 4 for c in board}
    suit_counts = [sum(c % 4 == suit for c in board) for suit in range(4)]
    def information(index):
        c = hole[index]
        return 3 * (c // 4 in board_ranks) + 2 * (suit_counts[c % 4] >= 2) + (c // 4) / 20
    reveal = i if information(i) < information(j) else j
    seed = sum((c + 1) * (53 ** k) for k, c in enumerate(hole + board)) + state.hand_number * 997
    if seed % 4 == 0:
        reveal = j if reveal == i else i
    return Action('select', cards=(discard, reveal))


def update_tracker(state, memory):
    try:
        record = json.loads(memory)
        version, hand, postflop, shoved, raised, stacks, bets, counts = record
        if version != VERSION or len(stacks)!=10 or len(bets)!=10 or len(counts)!=40:
            raise ValueError('memory')
        if not all(type(x) is int for x in stacks+bets+counts):
            raise ValueError('memory values')
    except (ValueError, TypeError, UnicodeError):
        hand, postflop, shoved, raised = 0, 0, 0, 0
        stacks = [state.config.starting_stack if i<state.config.players else 0 for i in range(10)]
        bets, counts = [0]*10, [0]*40
    # events is the complete feed since the last successful reply, including hands
    # we folded. A failed reply keeps both old memory and the unacknowledged feed.
    for event in state.events:
        if event.kind == 'hand':
            hand=event.amount;postflop=shoved=raised=0;bets=[0]*10
            for i in range(10):
                if stacks[i]>0: counts[4*i]=min(60000,counts[4*i]+1)
            continue
        if event.kind == 'board':
            postflop=1;bets=[0]*10
            continue
        seat=event.seat
        if seat is None or not 0<=seat<10: continue
        base=4*seat
        if event.kind=='stack': stacks[seat]=event.amount
        elif event.kind=='ante': stacks[seat]=max(0,stacks[seat]-event.amount)
        elif event.kind in ('blind','call'):
            stacks[seat]=max(0,stacks[seat]-event.amount);bets[seat]+=event.amount
        elif event.kind=='raise':
            stacks[seat]=max(0,stacks[seat]-max(0,event.amount-bets[seat]));bets[seat]=event.amount
            if not postflop and not (raised>>seat)&1:
                counts[base+2]=min(60000,counts[base+2]+1);raised|=1<<seat
            if not postflop and stacks[seat]==0 and not (shoved>>seat)&1:
                counts[base+3]=min(60000,counts[base+3]+1);shoved|=1<<seat
        elif event.kind=='fold': counts[base+1]=min(60000,counts[base+1]+1)
    packed=json.dumps([VERSION,hand,postflop,shoved,raised,stacks,bets,counts],separators=(',',':')).encode()
    return counts,packed[:state.config.memory_bytes]


def risk_margin(state, me, cost, opponents):
    if state.players_remaining <= 2:
        return 0.0
    paid = sum(p > 0 for p in state.config.payouts)
    payout_total = max(1, sum(state.config.payouts))
    flatness = 1 - state.config.payouts[0] / payout_total
    fraction = cost / max(1, me.stack)
    margin = .035 * flatness * min(1, fraction * 2)
    if state.players_remaining == paid + 1 and fraction > .5:
        smaller = sum(0 < s.stack < me.stack * .6 for s in state.seats if s.seat != me.seat)
        margin += .055 + .025 * min(2, smaller)
    return margin


def icm_call_threshold(state, me, opponent, cost, pot):
    """Exact ICM branch values for an isolated all-in call, before ties.

    Other stack configurations retain the conservative fallback; this is not
    a multiway side-pot solver or an assertion of game-theoretic equilibrium.
    """
    stacks = [s.stack for s in state.seats]
    hero, villain = state.seat, opponent.seat
    refund = max(0, state.pot-pot)
    stacks[villain] += refund
    folded=stacks.copy(); folded[villain]+=pot
    won=stacks.copy(); won[hero]+=pot
    lost=stacks.copy(); lost[hero]-=cost; lost[villain]+=pot+cost
    vf=icm(folded,state.config.payouts)[hero]
    vw=icm(won,state.config.payouts)[hero]
    vl=icm(lost,state.config.payouts)[hero]
    if lost[hero] == 0:
        # Eliminated players receive their finishing-place payout. The SDK's
        # ICM helper returns only surviving equity, so add this separately.
        survivors=sum(x>0 for x in lost)
        vl=state.config.payouts[survivors] if survivors<len(state.config.payouts) else 0.0
    return (vf-vl)/max(1e-9,vw-vl)


def equity(state, opponents):
    """Small fixed joint sample, conditioned on every public exposed/dead card.

    Opponent retention and betting selection are modeled conservatively, not as
    an exact posterior. No shared mutable RNG or hidden simulator information.
    """
    hole = [INDEX[c] for c in state.cards]
    board = [INDEX[c] for c in state.board]
    known = set(hole + board)
    for c in state.variant.get('discarded', ()):
        known.add(INDEX[c])
    for s in state.seats:
        for c in s.shown_cards:
            known.add(INDEX[c])
    deck = [c for c in range(52) if c not in known]
    exposed = [[INDEX[c] for c in s.shown_cards] if USE_REVEALS else [] for s in opponents]
    if not USE_REVEALS:
        # A diagnostic ablation ignores public information, while still keeping
        # our own discarded card out of the deck.
        known = set(hole + board + [INDEX[c] for c in state.variant.get('discarded', ())])
        deck = [c for c in range(52) if c not in known]
    raises = {e.seat for e in state.history if e.kind == 'raise'}
    seed = 1469598103934665603
    for c in hole + board + sorted(known):
        seed = ((seed ^ (c + 1)) * 1099511628211) & 0xffffffffffffffff
    seed ^= state.hand_number * 97 + state.seat
    rng = random.Random(seed)
    samples = 24 if len(opponents) <= 2 else 16
    missing_board = 5 - len(board)
    needed = missing_board + sum(max(0, 2 - len(x)) for x in exposed)
    total = 0.0
    hero_cards = [CARDS[c] for c in hole]
    if not missing_board and len(opponents)==1 and len(exposed[0])==1:
        final_board=[CARDS[c] for c in board]
        mine=EVAL(hero_cards+final_board)
        wins=0.0
        for card in deck:
            rank=EVAL([CARDS[exposed[0][0]],CARDS[card]]+final_board)
            wins+=1 if mine>rank else .5 if mine==rank else 0
        return max(0.0, wins/len(deck)-(.07 if state.to_call else .025))
    for trial in range(samples):
        drawn = rng.sample(deck, needed)
        final_board = [CARDS[c] for c in board + drawn[:missing_board]]
        mine = EVAL(hero_cards + final_board)
        best, ties = mine, 1
        offset = missing_board
        for shown in exposed:
            n = max(0, 2 - len(shown))
            their = shown + drawn[offset:offset+n]
            offset += n
            rank = EVAL([CARDS[c] for c in their] + final_board)
            if rank > best:
                best, ties = rank, 1
            elif rank == best:
                ties += 1
        if mine == best:
            total += 1 / ties
    estimate = total / samples
    # Public exposure is exact information; the unknown card is not uniform
    # after a strategic retention and a large bet. Avoid calling on raw equity.
    if state.to_call:
        estimate -= .035 + .025 * min(2, len(raises))
    else:
        estimate -= .025
    return max(0.0, min(1.0, estimate))


def decide(state, counts):
    if state.phase == 'select':
        return choose_cards(state)
    if state.phase != 'betting':
        return fallback(state)
    me = next(s for s in state.seats if s.seat == state.seat)
    opponents = [s for s in state.seats if s.seat != state.seat and s.status in ('active', 'all_in')]
    if not opponents:
        return fallback(state)
    call = min(state.to_call, me.stack)
    bb = max(1, state.blinds.big_blind)
    effective = min(me.stack + me.bet, max(s.stack + s.bet for s in opponents))
    eff_bb = effective / bb
    # Discount uncallable excess in a covering opponent's current wager.
    excess = sum(max(0, s.bet - (me.bet + me.stack)) for s in opponents)
    pot = max(1, state.pot - excess)
    price = call / (pot + call)
    margin = risk_margin(state, me, call, opponents)
    if call and len(opponents)==1 and state.players_remaining<=5 and (call==me.stack or opponents[0].stack==0):
        price=max(price,icm_call_threshold(state,me,opponents[0],call,pot))
        margin=0
    if not state.board:
        hole = [INDEX[c] for c in state.cards]
        strength = pre_strength(hole)
        lookup = None
        if len(hole)==3 and PREFLOP:
            a,b,c=sorted(hole)
            lookup=PREFLOP[c*(c-1)*(c-2)//6+b*(b-1)//2+a]
        live = sorted(s.seat for s in state.seats if s.status != 'busted')
        after_button = sorted(live, key=lambda s: (s - state.button - 1) % state.config.players)
        sb, big = (state.button, after_button[0]) if len(live) == 2 else after_button[:2]
        if me.seat == state.button: position = 'btn'
        elif me.seat == sb: position = 'sb'
        elif me.seat == big: position = 'bb'
        else:
            before = sorted(live, key=lambda s: (state.button - s) % state.config.players)
            position = 'co' if before.index(me.seat) == 1 else 'early'
        raises = [e for e in state.history if e.kind == 'raise']
        shovers = [s for s in opponents if counts[s.seat*4] >= 4 and counts[s.seat*4+3] >= .6 * counts[s.seat*4]]
        if not raises:
            cutoff = {'btn':.56, 'sb':.56, 'co':.59, 'early':.63, 'bb':.58}[position]
            if len(live) <= 3: cutoff -= .035
            if shovers: cutoff += .04
            open_hand = strength >= cutoff
            if lookup:
                width={'btn':.48,'sb':.45,'co':.31,'early':.20,'bb':.30}[position]
                if len(live)<=3:width+=.12
                if shovers:width*=.65
                open_hand=lookup[2]<=width
            if open_hand:
                if eff_bb <= 9:
                    return raise_to(state, me.bet + me.stack)
                limpers = sum(e.kind == 'call' for e in state.history)
                return raise_to(state, bb * (2.2 + .7 * limpers))
            return fallback(state)
        aggressor = raises[-1].seat
        wide = any(s.seat == aggressor for s in shovers)
        heavy = call >= .30 * max(1, me.stack) or max(s.bet for s in opponents) >= 8 * bb
        if heavy:
            # Three-card random opposition is stronger than two random cards.
            # This smooth fallback will be evaluated against actual variant bots.
            e = lookup[0 if wide else 1] if lookup else max(.05, min(.9, strength - (.12 if wide else .20)))
            contesting=sum(s.bet>=max(bb,me.bet+call) or s.status=='all_in' for s in opponents)
            if contesting>1:e=e**(1+.65*(contesting-1))
            if e > price + margin + (.02 if wide else .045):
                return Action.call() if state.can('call') else fallback(state)
            return fallback(state)
        if strength >= .76 and state.can('raise'):
            return raise_to(state, me.bet + me.stack if eff_bb <= 18 else 3 * max(s.bet for s in opponents))
        required = .60 if position == 'bb' else .64
        if len(live) <= 3: required -= .04
        if wide: required -= .035
        if strength >= required and call <= .20 * me.stack and price < .38:
            return Action.call() if state.can('call') else fallback(state)
        return fallback(state)
    e = equity(state, opponents)
    if not call:
        threshold = .57 if len(opponents) == 1 else .53 if len(opponents) == 2 else .48
        if e >= threshold:
            size = .65 if e >= .72 else .40
            return raise_to(state, me.bet + max(bb, int(pot * size)))
        # Small, infrequent probes only in heads-up pots after the opponent checks.
        seed = sum(INDEX[c] for c in state.cards) + state.hand_number
        checks = sum(ev.kind == 'check' for ev in state.history)
        if len(opponents) == 1 and e > .30 and checks and seed % 7 == 0:
            return raise_to(state, me.bet + max(bb, pot // 3))
        return fallback(state)
    if e >= max(.79, price + margin + .25) and state.can('raise'):
        return raise_to(state, me.bet + call + max(bb, int((pot + call) * .8)))
    # Additional margin controls small-sample equity uncertainty and multiway
    # range selection; do not use raw sampled equity as an exact probability.
    if e >= price + margin + .045:
        return Action.call() if state.can('call') else fallback(state)
    return fallback(state)


class Agent(BaseAgent):
    def act(self, state, memory):
        try:
            counts, packed = update_tracker(state, memory)
            action = decide(state, counts)
            return action, packed
        except Exception:
            return fallback(state), b''


# Eager evaluator warm-up; no per-table state is retained here.
EVAL(list(CARDS[:7]))
gc.disable()
