# 05. Variant playbook: what changes, and the first thing to change in the bot

The variant is revealed at 6:00 PM as prose plus the rule knobs (players, starting stack, blinds with an ante slot, hands per level, hand cap, up to five payouts, decision time, time bank, ICM luck correction, resampling). The engine can also represent extra hole cards, discards, exposed cards, multiple boards, a bidding or picking phase, and a card exchange phase (see 01_PLATFORM_INTEL.md, B3). The Finals use a different variant again.

## Triage in the first seven minutes

Answer these in order, out loud, with the kit open:

1. Are the hand rankings standard? (Which hand wins at showdown.) If not, the evaluator and every equity table must change before anything else.
2. How many cards do I hold, how many boards are there, and is anything face up? If the answer is not "two, one, nothing", the hand-strength layer must change.
3. Is there any decision other than fold/check/call/bet/raise (discard, bid, pick, swap)? If yes, that decision needs its own function, a legal-values check, and a safe default.
4. Betting structure: no-limit, pot-limit, capped? Read the kit's min/max raise fields; never compute them yourself.
5. Blinds, antes, levels, stack, players per table, hand cap, payouts. Copy them into constants.
6. Deadline, time bank, allowed imports, submission shape.

Then: submit a safe bot first (v1 in 03_STRATEGY_PLAYBOOK.md section 10) that handles the new decision with the simplest correct default. Only then build the real adaptation.

## Family-by-family

### F1. Hand ranking changes (flush beats full house, straight beats flush, and so on)

How it shows: prose like "a flush beats a full house". Possibly a short deck.
What breaks: the evaluator's category order, every equity table, every intuition about draws.
Adaptation: make the category order a constant list in the evaluator and swap it. Regenerate the 169 table and the postflop class-to-equity table with the new evaluator (two minutes on the build machine). Draws to the promoted category gain value; made hands of the demoted category lose value.
Default while adapting: play standard but tighten calls with the demoted hand class.

### F2. Pot-limit or capped raises

How it shows: knob or prose; the kit's max raise will be below all-in.
What breaks: shoving as a tool. Fold equity drops; stacks go in over several streets.
Adaptation: all sizes come from the kit's bounds. Push/fold logic becomes "bet the max" logic; three streets of pot-sized bets commit a stack, so plan commitment on the flop. Bluffing is cheaper to call down, so bluff less; value bet more thinly because opponents cannot shove you off hands.
Default: same ranges, sizes clamped.

### F3. Antes (per player, big-blind ante, button ante)

How it shows: the third number in each blind triple.
What breaks: pot odds preflop; steal math; the fold-bot bleeds faster.
Adaptation: include antes in the pot for every price calculation. Widen opens and steals by about 5 points, widen push/fold ranges noticeably (antes make shoving much better), defend the big blind wider. Fold-bots and nits bust earlier, so the ladder arrives sooner.

### F4. Different structure: turbo levels, deeper or shorter stacks, different table size, different hand cap

How it shows: knobs.
What breaks: stack regimes are keyed on big blinds, so mostly nothing; position buckets if the table is not 8; cap logic if the cap is not 200.
Adaptation: compute everything from big blinds and from "hands remaining to the cap". Re-bucket positions by seats before the button. With 6 players, EP disappears. With a shorter cap (say 100 hands), more tables end by ICM at the cap and survival weighs more.

### F5. Payout shape

How it shows: the payout list.
What breaks: the risk constant.
Adaptation: winner-take-most means lambda near 0.1 early and 0 late, accept flips with an edge, play for the win. Flat means lambda 0.25 to 0.35 and fold into the money. Pay-only-two means the bubble is at three left; pay five means the bubble is at six left. Set the "places paid" constant and the lambda table from it.

### F6. Board dealing pattern (five cards at once, 2-2-1, extra street, six community cards)

How it shows: prose; the kit's street names.
What breaks: street-based logic (c-bet, turn barrel), outs math.
Adaptation: write the postflop logic in terms of "cards to come" rather than street names. With all five dealt at once there is one postflop betting round and no implied odds: play made hands, fold draws (there are none). With six community cards, best five of eight changes made-hand frequencies upward: pairs are weaker, two pair is normal, flushes and straights more common. Regenerate the postflop table with the kit's dealing pattern.

### F7. Three hole cards with a discard (MIT 2026 style: discard one face up after the flop)

How it shows: three cards in hand; an explicit discard action; `discarded` and `exposed` in the replay.
What breaks: preflop ranking (which two of three), the information game (the exposed discard tells the table what you did not keep).
Adaptation:
- Preflop strength: the best of the three two-card combinations, plus a bonus because you get to choose after seeing the flop. Approximate with the maximum over the three pairs' equities plus 2 to 4 points for flexibility (connected or suited triples get more).
- Discard choice: for each of the three keep-two options evaluate made hand plus draws on the flop; keep the best; break ties by keeping the combination with the most outs. Discard the card that reveals least (prefer discarding a low off-suit card over a card that advertises a draw).
- Reading discards: an opponent who discards a high card kept something better than that high card; an opponent who discards a suited card is less likely on the flush draw. Feed the exposed card into the equity estimate as a dead card at minimum.
- Ranges are stronger than two-card hold'em (everyone effectively picks their best pair). Tighten calling standards one notch and value bet two pair or better, not one pair.

### F8. Four or more hole cards, must use exactly two (Omaha-like) or any (Pineapple-like, no discard)

How it shows: card count; prose about how many hole cards may be used.
What breaks: the evaluator (must enforce the use rule), all equity tables, hand reading.
Adaptation: evaluator enumerates legal hole-card subsets. Hand values compress; the nuts changes often; one pair and two pair are weak; wraps and nut flush draws are strong. Play tighter preflop (double-suited, connected, high pairs), avoid committing with non-nut hands multiway, and shrink bluffing to near zero. Regenerate tables; if time is short, play the heads-up percentile of the best two-card component minus a notch.

### F9. Multiple boards (double board, or Blotto-style split hands)

How it shows: `boards` has more than one entry; prose about splitting the pot.
What breaks: equity is the average over boards; scooping both is rare.
Adaptation: compute strength per board; the pot is split per board, so a hand that is the nuts on one board and air on the other has about 50 percent equity against one opponent, not 100. Favour hands with equity on both boards (pairs, overcards, suited for two flush draws). Bet sizing for value shrinks because opponents chop often. If hands are split across boards Blotto-style (assign cards to boards), assign to maximize the number of boards won with a margin, not to make one monster.

### F10. Auction or bidding for a card, or a pick phase (MIT 2024 style; the `spread`, `stakes`, `picks` frames)

How it shows: an action to bid chips or to pick among offered cards.
What breaks: a new decision with real chips at stake.
Adaptation: value of winning the bid = (equity with the extra card minus equity without) times the pot plus expected future value; bid up to that value in a second-price auction (bid your true value); in a first-price auction bid about 60 to 70 percent of it. Published experience from the 2024 MIT event found that winning the card for about 1.8 times the naive equity-based bid outperformed, because the card is worth more than its immediate equity gain (information and board coverage). Never bid more than a third of the effective stack unless the hand is already strong. Picks: pick the card that maximizes made-hand plus outs; prefer cards that block opponents' likely draws.

### F11. Exposed hole card (one of your two cards face up to the table)

How it shows: `exposed` per seat; prose.
What breaks: ranges are partially known; bluffing with an exposed low card is hopeless.
Adaptation: fold more when our exposed card is low and we face aggression (they know we have at most one good card); steal more when our exposed card is high (our range looks strong). Against opponents: compute their equity range from their exposed card; bet when their exposed card misses the board and ours connects. Treat the exposed card as a known card in every equity estimate.

### F12. Card exchange or draw (the `exchange` phase; pay to swap a card)

How it shows: an exchange action, maybe with a chip cost.
What breaks: a new decision; opponents' ranges improve after exchanging.
Adaptation: exchange when expected equity gain times the pot exceeds the cost; keep pairs and strong draws; swap the dead card. Note who exchanged and how many: a player who stands pat usually has a made hand. Regenerate tables assuming one exchange for everyone if the exchange is free.

### F13. Short deck (no 2 to 5)

How it shows: prose; 36-card deck; often flush beats full house and A-6-7-8-9 is a straight.
What breaks: every equity number; pairs are weaker, straights are far more common, flushes rarer.
Adaptation: regenerate all tables with the kit's deck and ranking. Open-ended straight draws have 16 outs of 32 unseen cards; play draws aggressively, play one pair carefully.

### F14. Run-it-twice style resampling

How it shows: `resampling_continuations` and `resampling_threshold`.
What breaks: nothing in strategy. Chip EV is unchanged; variance falls.
Adaptation: none. Slightly less reason to avoid flips, but the ICM asymmetry remains.

### F15. Decision time and time bank

How it shows: `decision_ms`, `time_bank_ms`.
What breaks: the budget.
Adaptation: if `decision_ms` is larger than 1, allow a bounded Monte Carlo refinement for all-in decisions behind a hard time check at 40 percent of the budget. If there is a time bank, spend it only on all-in decisions and never let the bank fall below two decisions' worth. If `decision_ms` is smaller than 1, strip the ICM calls and the full evaluator and run from tables alone.

### F16. ICM luck correction (scored by equity on all-ins, maybe on the river)

How it shows: a round-level flag; ask a Gamemaster.
What breaks: nothing in strategy; everything in variance.
Adaptation: pure EV play. Shove-bots get their negative EV every time. Our thin value and correct calls are credited at their expectation. Do not gamble for position: a lucky double-up is not credited, only its expectation.

### F17. Position-dependent blinds, straddles, dead button rules

How it shows: prose; blind triples that differ by seat; a mandatory straddle.
What breaks: position math and pot odds.
Adaptation: read who posted what from the kit each hand rather than assuming; a straddle makes the effective big blind the straddle; pot odds for the blinds improve.

### F18. Bounties or elimination bonuses

How it shows: prose ("earn X points for eliminating a player").
What breaks: ICM risk aversion partially reverses.
Adaptation: calling a short stack's shove becomes more attractive by the bounty's value; shoving into a big stack does not. Compute the bounty in points and add it to the win branch of the all-in evaluation. Avoid being the short stack that everyone wants to call.

### F19. Hi-lo split, wild cards, lowball components

How it shows: prose about splitting between best high and best low, or a joker.
What breaks: the evaluator and the entire value scale.
Adaptation: write a second evaluator for the low hand (and a wild-card expansion for jokers); equity = share of the pot from both halves; favour hands that can scoop (A-2 with suited high cards in hi-lo). If this is the variant, spend the first 20 minutes on the evaluator and accept a simple strategy; most of the room will have a broken evaluator and a broken evaluator means illegal or absurd actions.

### F20. Less information (no stacks, no history, no hand number)

How it shows: fields missing from the observation.
What breaks: ICM, tracker, cap logic.
Adaptation: count hands ourselves from new-hand hooks; infer stacks from our own and the pot if given; degrade the tracker to what is observable (our own pots only); fall back to the static lambda table.

## Which assumptions to re-check for every variant

- Does "all-in" still mean the kit's maximum raise field? Read it from the kit.
- Does the minimum raise follow standard rules? Read it from the kit.
- Are blinds still posted by the two seats after the button when heads-up? Read it from the replay of one local hand.
- Does the hand number come from the kit? If not, count.
- Does the kit's ICM calculator take the payouts in the same order as the Format page? Test once with a two-player case.
- Does the local simulator in the kit implement the variant exactly as the server does? The kit is the closest thing we have to the server; trust it over our intuition, but spot-check one hand by hand.
