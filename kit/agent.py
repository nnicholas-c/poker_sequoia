"""Your bot. Start here, run it locally (see README.md), then improve the strategy in `act`.

Your Agent is stateless: the platform may answer any table's turn with any copy of your bot,
so nothing on `self` or in globals is remembered between calls. To remember things at a
table, return `memory` (bytes) with your action; you get it back on your next turn at that
table. It starts empty (b"") at every table and is cut beyond `state.config.memory_bytes`.
"""

import json

import poker_agent_sdk
from poker_agent_sdk import Action, GameState

# Load anything heavy (models, lookup tables) here, at import time: it happens once and every
# call shares it. If you use a model, also run one throwaway prediction here: libraries such
# as PyTorch finish setting up on first use, and a slow decision counts as a miss.


class Agent(poker_agent_sdk.Agent):
    def act(self, state: GameState, memory: bytes) -> tuple[Action, bytes]:
        """Your turn. Return within the decision limit (1 ms), or the engine applies its fallback.

        `state.events` is what happened since your last turn here; `state.can(kind)` gives
        the legal range for actions. A raise amount is your total bet for this betting
        round. Showdown cards are revealed automatically, without calling this method.
        """
        # Example memory: how many times each opponent has raised at this table.
        raises: dict[str, int] = json.loads(memory) if memory else {}
        for event in state.events:
            if event.kind == "raise" and event.seat != state.seat:
                raises[str(event.seat)] = raises.get(str(event.seat), 0) + 1
        return decide(state), json.dumps(raises).encode()


def decide(state: GameState) -> Action:
    """A placeholder that only plays legally: replace it with your strategy."""
    if state.phase != "betting":
        # A decision of the variant's own (RULES.md): its first legal action is the automatic
        # choice, which this template takes until you write a strategy for it.
        first = state.legal_actions[0]
        return Action(first.kind, first.min_amount)
    if state.can("check"):
        return Action.check()
    return Action.fold()
