"""Parametrised opponent archetypes for the arena, modelled on the practice-run census.

Each bots/arch_*/agent.py does:  from archetypes import make_agent; Agent = make_agent(**knobs)
They reuse claude_v2's hand evaluation so the comparison is about strategy, not evaluator quality.
Internal test opponents only (not uploadable: they import a sibling module).
"""

import importlib.util
import random
import zlib
from pathlib import Path

import poker_agent_sdk
from poker_agent_sdk import Action

_spec = importlib.util.spec_from_file_location("v2_eval", Path(__file__).resolve().parents[1] / "bots" / "nc_v5" / "agent.py")
V2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(V2)


def make_agent(open_w=0.22, late_mult=1.6, pfr_frac=0.85, three_bet=0.05, call_open=0.12, bb_defend=0.35,
               cbet=0.55, bet_strong=0.60, call_need_margin=0.03, fold_to_raise_bias=0.0, limp=0.0,
               shove_bb=11, shove_w=0.25, allin_call_eq=0.55, expose="low", bluff_river=0.0,
               station=0.0, maniac=False, name="arch"):
    class Agent(poker_agent_sdk.Agent):
        def act(self, state, memory):
            try:
                return decide(state), b""
            except Exception:
                if state.phase != "betting":
                    f = state.legal_actions[0]
                    return Action(f.kind, f.min_amount), b""
                return (Action.check() if state.can("check") else Action.fold()), b""

    def decide(state):
        rnd = random.Random((zlib.crc32(state.config.table_id.encode()) * 1000003 + state.hand_number * 7919 + len(state.history)) & 0xFFFFFFFF)
        if state.phase == "select":
            cards, board = state.cards, state.board
            best = None
            for d in range(3):
                keep = [cards[i] for i in range(3) if i != d]
                a = V2.analyze(keep, board)
                v = (a["eq"], a["value"])
                if best is None or v > best[0]:
                    best = (v, d)
            d = best[1]
            keep_idx = [i for i in range(3) if i != d]
            ranks = [V2.RANK_IDX[cards[i][0]] for i in keep_idx]
            if expose == "low":
                reveal = keep_idx[0] if ranks[0] <= ranks[1] else keep_idx[1]
            elif expose == "high":
                reveal = keep_idx[0] if ranks[0] >= ranks[1] else keep_idx[1]
            else:
                reveal = rnd.choice(keep_idx)
            return Action("select", cards=(d, reveal))
        if state.phase != "betting":
            f = state.legal_actions[0]
            return Action(f.kind, f.min_amount)
        me = state.seat
        seats = state.seats
        my_total = seats[me].stack + seats[me].bet
        bb = state.blinds.big_blind or 1
        live = [s.seat for s in seats if s.status in ("active", "all_in")]
        n_opp = len(live) - 1
        to_call = state.to_call
        pot = state.pot
        can_raise = state.can("raise")
        if not state.board:
            score, bp = V2.three_card_score(state.cards)
            p = V2.score_percentile(score)
            cls = V2.cls2(state.cards[bp[0]], state.cards[bp[1]])
            eq1 = V2.PRE[cls][0] / 1000.0
            pos = V2.position_of(state, live, me)
            raises = [e for e in state.history if e.kind == "raise"]
            my_bb = my_total / bb
            if maniac:
                if can_raise:
                    return Action.raise_to(min(can_raise.max_amount, max(can_raise.min_amount, int(pot * 1.0 + to_call))) if rnd.random() < 0.7 else can_raise.max_amount)
                return Action.call() if state.can("call") else Action.check()
            if not raises:
                w = open_w * (late_mult if pos in ("co", "btn", "sb") else 1.0)
                if state.can("check"):
                    if p <= w * 0.5 and can_raise:
                        return Action.raise_to(min(can_raise.max_amount, 3 * bb))
                    return Action.check()
                if my_bb <= shove_bb:
                    if p <= shove_w * (1.4 if pos in ("btn", "sb", "co") else 1.0) and can_raise:
                        return Action.raise_to(can_raise.max_amount)
                    return Action.fold()
                if p <= w:
                    if limp and rnd.random() < limp:
                        return Action.call()
                    if rnd.random() < pfr_frac and can_raise:
                        return Action.raise_to(min(can_raise.max_amount, max(can_raise.min_amount, int(2.5 * bb))))
                    return Action.call()
                return Action.fold()
            # facing a raise
            raiser = raises[-1].seat
            all_in = seats[raiser].status == "all_in" or to_call >= 0.5 * my_total
            if all_in:
                price = to_call / (pot + to_call)
                if eq1 >= max(allin_call_eq, price + 0.12):
                    return Action.call()
                return Action.fold()
            if p <= three_bet and can_raise:
                if my_bb <= 25:
                    return Action.raise_to(can_raise.max_amount)
                return Action.raise_to(min(can_raise.max_amount, max(can_raise.min_amount, 3 * raises[-1].amount)))
            cw = call_open
            if pos == "bb" and to_call <= 2.5 * bb:
                cw = max(cw, bb_defend)
            if len(raises) >= 2:
                cw *= 0.4
            if p <= cw * (1.0 - fold_to_raise_bias) and to_call <= 0.25 * my_total:
                return Action.call()
            return Action.fold()
        # postflop
        a = V2.analyze(state.cards, state.board) if len(state.cards) == 2 else {"eq": 0.2, "cls": 0, "draw": None}
        eq = V2.multiway(a["eq"], n_opp)
        street = len(state.board)
        hist = state.history
        pre_aggr = -1
        seen_board = 0
        street_bets = 0
        for e in hist:
            if e.kind == "board":
                seen_board += 1
                street_bets = 0
            elif e.kind == "raise":
                if seen_board == 0:
                    pre_aggr = e.seat
                else:
                    street_bets += 1

        def bet(frac):
            size = max(int(pot * frac), bb)
            target = seats[me].bet + to_call + size
            if target - seats[me].bet >= 0.65 * seats[me].stack:
                target = can_raise.max_amount
            return Action.raise_to(min(can_raise.max_amount, max(can_raise.min_amount, target)))

        if to_call == 0:
            if can_raise and eq >= bet_strong:
                return bet(0.6)
            if can_raise and street == 3 and pre_aggr == me and rnd.random() < cbet:
                return bet(0.5)
            if can_raise and street == 5 and n_opp == 1 and a["cls"] == 0 and rnd.random() < bluff_river:
                return bet(0.6)
            return Action.check()
        price = to_call / (pot + to_call)
        need = price + call_need_margin - station * 0.25
        if to_call >= 0.4 * my_total:
            need = price * 1.4 + 0.05 - station * 0.2
        if can_raise and a["cls"] >= 5 and eq >= 0.72 and street_bets == 1:
            return bet(1.0)
        if eq >= need:
            return Action.call()
        return Action.fold()

    Agent.__name__ = name
    return Agent
