"""Three-card hold'em with a sealed flop discard and one exposed retained card."""

import random
from collections import deque
from dataclasses import replace

from poker_agent_protocol.game import Action, BlindLevel, LegalAction
from pokerkit import (
    AntePosting,
    BlindOrStraddlePosting,
    BoardDealing,
    CheckingOrCalling,
    ChipsPulling,
    CompletionBettingOrRaisingTo,
    Folding,
    HoleCardsShowingOrMucking,
    HoleDealing,
)

from poker_engine.holdem import HoldemHand
from poker_engine.variant import HandEvent, HandView
from poker_engine.variants._hole_cards import holdem_game
from poker_engine.variants._sealed import SealedLog


class FlopDiscardReveal:
    name = "flop_discard_reveal"
    title = "Bay Area"
    public_id = "bay_area"
    max_players = 10
    extension = SealedLog

    def deal(
        self, *, stacks: tuple[int, ...], blinds: BlindLevel, rng: random.Random
    ) -> "FlopDiscardRevealHand":
        return FlopDiscardRevealHand(stacks=stacks, blinds=blinds, rng=rng)


class FlopDiscardRevealHand(HoldemHand):
    game = holdem_game(3)

    def __init__(self, *, stacks: tuple[int, ...], blinds: BlindLevel, rng: random.Random) -> None:
        super().__init__(stacks=stacks, blinds=blinds, rng=rng)
        self._selecting: deque[int] = deque()
        self._selected = False
        self._choices: dict[int, tuple[int, int]] = {}
        self._discarded: list[tuple[str, ...]] = [()] * len(stacks)
        # Each player's kept and discarded cards, for the organizers' hand log only.
        self._sealed: list[HandEvent] = []
        # Calling Station: each player's calls out of all its betting actions this hand.
        self._calls = [0] * len(stacks)
        self._chances = [0] * len(stacks)
        self._early_shows: set[int] = set()
        self._deferred_show_players: set[int] = set()
        self._post_reveal_raisers: set[int] = set()

    def actor(self) -> int | None:
        state = self._state
        while True:
            if self._selecting:
                return self._selecting[0]
            if not self._selected and len(state.board_cards) == 3 and sum(state.statuses) > 1:
                self.events()
                self._selected = True
                self._selecting.extend(i for i in state.player_indices if state.statuses[i])
                return self._selecting[0]
            if state.actor_index is not None:  # Betting: nothing can be dealt or shown now.
                return state.actor_index
            if state.can_deal_hole():
                state.deal_hole()
            elif state.can_burn_card():
                state.burn_card()
            elif state.can_deal_board():
                state.deal_board()
            elif state.showdown_index is not None:
                # PokerKit requires an early internal show to advance an all-in runout.
                # Keep that operation private until the actual river showdown. Every
                # contender then shows automatically, whether all-in or not.
                if len(state.board_cards) < 5:
                    self.events()
                    self._early_shows.add(len(state.operations))
                state.show_or_muck_hole_cards(True)
            else:
                return state.actor_index

    def legal_actions(self) -> tuple[LegalAction, ...]:
        if self._selecting:
            return (LegalAction("select"),)
        return super().legal_actions()

    def apply(self, action: Action) -> None:
        if not self._selecting:
            player = self._state.actor_index
            after_reveal = self._selected and player is not None
            shove = (
                player is not None
                and action.kind == "raise"
                and action.amount == self._state.bets[player] + self._state.stacks[player]
            )
            # A call puts chips in, as the hand log's "call" event does; all in for less
            # counts too.
            call = action.kind in ("check", "call") and bool(self._state.checking_or_calling_amount)
            super().apply(action)
            if player is None:
                return
            if action.kind in ("fold", "check", "call", "raise"):
                # Every betting action is a chance, including a check or fold the table plays
                # for a failing bot. Counting both parts here keeps rounds and variants
                # without them out of the share.
                self._chances[player] += 1
                self._calls[player] += call
            if action.kind == "raise":
                if after_reveal:
                    self._post_reveal_raisers.add(player)
                if shove:
                    self.events()
                    self._events.append(HandEvent("prize_the_shover", player))
            if after_reveal and action.kind == "fold" and sum(self._state.statuses) == 1:
                winner = self._state.statuses.index(True)
                if winner in self._post_reveal_raisers and self._shown[winner][0][0] in "2345":
                    self.events()
                    self._events.append(HandEvent("prize_the_empty_bluffer", winner))
            return
        if action.kind != "select" or action.amount:
            raise ValueError("Select one discard and one different retained card to reveal.")
        indices = action.cards or (2, 0)
        if (
            len(indices) != 2
            or any(type(index) is not int or not 0 <= index < 3 for index in indices)
            or indices[0] == indices[1]
        ):
            raise ValueError("Use two distinct original card indexes from 0 to 2.")
        player = self._selecting[0]
        self._choices[player] = (indices[0], indices[1])
        self._selecting.popleft()
        # Acknowledgements disclose neither cards nor whether the choice was a fallback.
        self._events.append(HandEvent("select", player))
        if not self._selecting:
            for seat, (discard, reveal) in self._choices.items():
                hole = self._state.hole_cards[seat]
                self._shown[seat] = (repr(hole[reveal]),)
                self._discarded[seat] = (repr(hole[discard]),)
                hole.pop(discard)
                self._state.hole_card_statuses[seat].pop(discard)
                # Keep PokerKit's face-up status consistent with the public reveal.
                self._state.hole_card_statuses[seat][reveal - (discard < reveal)] = True
                self._events.append(HandEvent("reveal", seat, cards=self._shown[seat]))
                self._sealed.append(HandEvent("kept", seat, cards=tuple(map(repr, hole))))
                self._sealed.append(HandEvent("discarded", seat, cards=self._discarded[seat]))

    def sealed(self) -> tuple[HandEvent, ...]:
        # One count per player and counter, so a hand adds at most two events per player.
        counts = (
            ("prize_calling_station_chances", self._chances),
            ("prize_calling_station", self._calls),
        )
        return (
            *self._sealed,
            *(
                HandEvent(kind, player, count)
                for kind, per_player in counts
                for player, count in enumerate(per_player)
                if count
            ),
        )

    def view(self, player: int) -> HandView:
        view = super().view(player)
        return replace(
            view,
            phase="select" if self._selecting else view.phase,
            to_call=0 if self._selecting else view.to_call,
            variant={"discarded": list(self._discarded[player])},
        )

    def events(self) -> tuple[HandEvent, ...]:
        # Convert operations as in the reference, except early all-in shows. Processing
        # one at a time preserves board/show/payout order even after an automatic runout.
        operations = self._state.operations
        while self._recorded < len(operations):
            index = self._recorded
            operation = operations[index]
            if index in self._early_shows:
                assert isinstance(operation, HoleCardsShowingOrMucking)
                self._deferred_show_players.add(operation.player_index)
                self._recorded += 1
                continue
            self._record_operation(operation)
            self._recorded += 1
            if isinstance(operation, BoardDealing) and self._deferred_show_players:
                board_cards = sum(
                    len(op.cards)
                    for op in operations[: self._recorded]
                    if isinstance(op, BoardDealing)
                )
                if board_cards == 5:
                    for player in sorted(self._deferred_show_players):
                        # Final hole cards may already have been cleared by settlement.
                        kept = tuple(
                            c for c in self._dealt[player] if c not in self._discarded[player]
                        )
                        self._shown[player] = kept
                        self._events.append(HandEvent("show", player, cards=kept))
                    self._deferred_show_players.clear()
        if not self._state.status and not self._settled:
            self._settled = True
            for player, stack in enumerate(self._state.stacks):
                self._events.append(HandEvent("stack", player, stack))
        return tuple(self._events)

    def _record_operation(self, operation: object) -> None:

        match operation:
            case HoleDealing(player_index=player, cards=cards):
                self._dealt[player] += tuple(map(repr, cards))
            case AntePosting(player_index=player, amount=amount):
                self._events.append(HandEvent("ante", player, amount))
            case BlindOrStraddlePosting(player_index=player, amount=amount):
                self._events.append(HandEvent("blind", player, amount))
            case BoardDealing(cards=cards):
                self._events.append(HandEvent("board", cards=tuple(map(repr, cards))))
            case Folding(player_index=player):
                self._events.append(HandEvent("fold", player))
            case CheckingOrCalling(player_index=player, amount=amount):
                self._events.append(HandEvent("call" if amount else "check", player, amount))
            case CompletionBettingOrRaisingTo(player_index=player, amount=amount):
                self._events.append(HandEvent("raise", player, amount))
            case HoleCardsShowingOrMucking(player_index=player, hole_cards=cards) if cards:
                self._shown[player] = tuple(map(repr, cards))
                self._events.append(HandEvent("show", player, cards=self._shown[player]))
            case HoleCardsShowingOrMucking(player_index=player):
                self._events.append(HandEvent("muck", player))
            case ChipsPulling(player_index=player, amount=amount) if amount:
                self._events.append(HandEvent("win", player, amount))


VARIANT = FlopDiscardReveal
