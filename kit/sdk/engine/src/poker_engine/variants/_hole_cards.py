"""Hold'em games dealing more hole cards. Not a variant: modules whose names start with an
underscore are helpers, shipped only in the kits of the variants that import them."""

from functools import cache

from pokerkit import NoLimitTexasHoldem

from poker_engine.holdem import _CachedHoldem


@cache
def holdem_game(hole_cards: int) -> type[NoLimitTexasHoldem]:
    """Hold'em dealing this many hole cards. The hand is the best five of hole and board cards
    together, using any number of each."""
    if hole_cards == 2:
        return _CachedHoldem
    return type(f"_CachedHoldem{hole_cards}", (_CachedHoldem,), {"hole_dealing_count": hole_cards})
