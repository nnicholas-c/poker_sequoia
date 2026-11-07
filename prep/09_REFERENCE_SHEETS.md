# 09. Reference sheets

Everything here is public-knowledge poker math or data you could compute from the rules of hold'em. Use it to sanity-check what the assistant produces tonight. Regenerate all tables at the event with the kit's own evaluator and the variant's deck and ranking; if the variant changes anything about hand values, the numbers below are wrong by construction.

## 1. Price to call (pot odds)

| Bet as a fraction of the pot | Equity needed to call |
|---|---|
| 1/4 | 16.7% |
| 1/3 | 20.0% |
| 1/2 | 25.0% |
| 2/3 | 28.6% |
| 3/4 | 30.0% |
| 1 (pot) | 33.3% |
| 1.5 | 37.5% |
| 2 | 40.0% |
| all-in for the rest (call equals pot) | 33.3% |

Formula: equity needed = call / (pot after your call). Antes and the blinds are in the pot. Under ICM multiply the requirement by (1 + lambda) from the risk table.

## 2. Outs to equity (two cards and one card to come)

| Outs | Flop to river (two cards) | Turn to river (one card) | Common holding |
|---|---|---|---|
| 2 | 8.4% | 4.3% | pocket pair to a set |
| 4 | 16.5% | 8.7% | gutshot |
| 6 | 24.1% | 13.0% | two overcards |
| 8 | 31.5% | 17.4% | open-ended straight draw |
| 9 | 35.0% | 19.6% | flush draw |
| 12 | 45.0% | 26.1% | flush draw plus gutshot |
| 15 | 54.1% | 32.6% | flush draw plus open-ended |

Rule of thumb: outs x 4 with two cards to come (subtract outs minus 8 when outs exceed 8), outs x 2 with one card to come.

## 3. All-in equity of the 169 starting hands (Monte Carlo, 4,000 deals per class, about 1 percent noise)

Equity vs 1 is against one random hand (heads-up). Equity vs 7 is against seven random hands (a full table all-in). "Rank vs 7" shows how the ordering changes when many players are in: suited and connected hands climb, weak offsuit aces and small pairs fall.

Percentile cutoffs by number of two-card combinations (pairs count 6, suited 4, offsuit 12; 1,326 total), heads-up ordering:

| Range | Weakest hand included | Equity vs 1 | Combos |
|---|---|---|---|
| top 5% of combos | ends at 77 | 0.659 | 68 of 1326 combos |
| top 10% of combos | ends at KQo | 0.615 | 134 of 1326 combos |
| top 15% of combos | ends at A7o | 0.601 | 200 of 1326 combos |
| top 20% of combos | ends at A4o | 0.584 | 272 of 1326 combos |
| top 25% of combos | ends at Q9s | 0.573 | 332 of 1326 combos |
| top 30% of combos | ends at A2o | 0.555 | 398 of 1326 combos |
| top 35% of combos | ends at J9o | 0.536 | 472 of 1326 combos |
| top 40% of combos | ends at Q7o | 0.522 | 532 of 1326 combos |
| top 45% of combos | ends at Q6o | 0.512 | 600 of 1326 combos |
| top 50% of combos | ends at Q4o | 0.497 | 668 of 1326 combos |
| top 60% of combos | ends at 86s | 0.466 | 798 of 1326 combos |
| top 70% of combos | ends at T5o | 0.440 | 938 of 1326 combos |

Full table (heads-up ordering):

| HU rank | Hand | Equity vs 1 | Equity vs 7 | Rank vs 7 | HU rank | Hand | Equity vs 1 | Equity vs 7 | Rank vs 7 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | AA | 0.850 | 0.376 | 1 | 86 | J8o | 0.505 | 0.115 | 106 |
| 2 | KK | 0.809 | 0.336 | 2 | 87 | Q2s | 0.503 | 0.128 | 85 |
| 3 | QQ | 0.802 | 0.289 | 3 | 88 | T8o | 0.502 | 0.113 | 110 |
| 4 | JJ | 0.777 | 0.258 | 4 | 89 | Q4o | 0.497 | 0.101 | 132 |
| 5 | TT | 0.752 | 0.214 | 11 | 90 | K2o | 0.496 | 0.102 | 129 |
| 6 | 99 | 0.720 | 0.198 | 17 | 91 | J5s | 0.496 | 0.135 | 75 |
| 7 | 88 | 0.690 | 0.174 | 29 | 92 | 22 | 0.494 | 0.134 | 77 |
| 8 | AKs | 0.671 | 0.252 | 5 | 93 | Q3o | 0.491 | 0.081 | 155 |
| 9 | AKo | 0.667 | 0.210 | 13 | 94 | J4s | 0.491 | 0.132 | 81 |
| 10 | AQs | 0.661 | 0.235 | 6 | 95 | T6s | 0.491 | 0.136 | 72 |
| 11 | 77 | 0.659 | 0.150 | 50 | 96 | T7s | 0.491 | 0.146 | 56 |
| 12 | AJs | 0.654 | 0.221 | 9 | 97 | 97s | 0.491 | 0.153 | 47 |
| 13 | 66 | 0.650 | 0.158 | 42 | 98 | T5s | 0.488 | 0.118 | 102 |
| 14 | ATs | 0.643 | 0.212 | 12 | 99 | J3s | 0.488 | 0.127 | 89 |
| 15 | AJo | 0.640 | 0.184 | 21 | 100 | 98o | 0.483 | 0.125 | 91 |
| 16 | AQo | 0.636 | 0.188 | 18 | 101 | J2s | 0.477 | 0.123 | 94 |
| 17 | KJs | 0.629 | 0.222 | 8 | 102 | T7o | 0.476 | 0.115 | 108 |
| 18 | KQs | 0.626 | 0.225 | 7 | 103 | J6o | 0.473 | 0.094 | 136 |
| 19 | A9s | 0.623 | 0.183 | 22 | 104 | J5o | 0.472 | 0.081 | 154 |
| 20 | A8s | 0.616 | 0.175 | 28 | 105 | Q2o | 0.471 | 0.091 | 139 |
| 21 | KQo | 0.615 | 0.179 | 26 | 106 | 96s | 0.467 | 0.139 | 68 |
| 22 | A7s | 0.615 | 0.185 | 20 | 107 | 86s | 0.466 | 0.139 | 67 |
| 23 | 55 | 0.614 | 0.148 | 53 | 108 | J3o | 0.462 | 0.082 | 152 |
| 24 | KTs | 0.613 | 0.204 | 14 | 109 | 87s | 0.462 | 0.148 | 55 |
| 25 | ATo | 0.612 | 0.173 | 30 | 110 | 75s | 0.462 | 0.135 | 74 |
| 26 | A8o | 0.606 | 0.134 | 76 | 111 | T4s | 0.461 | 0.127 | 88 |
| 27 | A9o | 0.605 | 0.152 | 49 | 112 | 87o | 0.460 | 0.108 | 120 |
| 28 | A4s | 0.604 | 0.170 | 34 | 113 | J4o | 0.460 | 0.086 | 147 |
| 29 | A7o | 0.601 | 0.134 | 78 | 114 | T3s | 0.460 | 0.107 | 125 |
| 30 | KJo | 0.600 | 0.182 | 23 | 115 | J2o | 0.457 | 0.082 | 151 |
| 31 | A5s | 0.597 | 0.172 | 33 | 116 | 97o | 0.457 | 0.105 | 126 |
| 32 | A6s | 0.595 | 0.162 | 39 | 117 | 76s | 0.457 | 0.143 | 59 |
| 33 | K8s | 0.593 | 0.162 | 38 | 118 | T6o | 0.454 | 0.101 | 131 |
| 34 | QJs | 0.592 | 0.219 | 10 | 119 | 95s | 0.451 | 0.125 | 90 |
| 35 | KTo | 0.590 | 0.161 | 40 | 120 | T2s | 0.447 | 0.107 | 122 |
| 36 | K9s | 0.590 | 0.178 | 27 | 121 | 85s | 0.446 | 0.137 | 71 |
| 37 | QJo | 0.586 | 0.180 | 24 | 122 | T4o | 0.443 | 0.083 | 150 |
| 38 | A2s | 0.586 | 0.167 | 37 | 123 | 96o | 0.441 | 0.094 | 135 |
| 39 | A4o | 0.584 | 0.133 | 79 | 124 | T5o | 0.440 | 0.083 | 149 |
| 40 | QTs | 0.583 | 0.202 | 15 | 125 | 94s | 0.435 | 0.123 | 95 |
| 41 | A6o | 0.582 | 0.128 | 86 | 126 | 86o | 0.434 | 0.109 | 116 |
| 42 | K9o | 0.580 | 0.140 | 66 | 127 | 93s | 0.432 | 0.107 | 124 |
| 43 | QTo | 0.578 | 0.156 | 45 | 128 | 65s | 0.427 | 0.144 | 58 |
| 44 | A5o | 0.577 | 0.119 | 100 | 129 | 95o | 0.424 | 0.087 | 145 |
| 45 | JTs | 0.577 | 0.198 | 16 | 130 | T3o | 0.422 | 0.072 | 159 |
| 46 | Q9s | 0.573 | 0.179 | 25 | 131 | 84s | 0.421 | 0.117 | 104 |
| 47 | A3s | 0.570 | 0.157 | 43 | 132 | 54s | 0.419 | 0.130 | 83 |
| 48 | K7s | 0.568 | 0.161 | 41 | 133 | 75o | 0.419 | 0.091 | 138 |
| 49 | K8o | 0.561 | 0.124 | 92 | 134 | 85o | 0.419 | 0.089 | 144 |
| 50 | J9s | 0.560 | 0.173 | 31 | 135 | T2o | 0.415 | 0.071 | 162 |
| 51 | Q8s | 0.560 | 0.156 | 44 | 136 | 92s | 0.415 | 0.108 | 118 |
| 52 | 44 | 0.559 | 0.142 | 62 | 137 | 76o | 0.411 | 0.108 | 119 |
| 53 | K6s | 0.556 | 0.146 | 57 | 138 | 82s | 0.411 | 0.111 | 113 |
| 54 | JTo | 0.556 | 0.172 | 32 | 139 | 93o | 0.409 | 0.064 | 166 |
| 55 | K5s | 0.555 | 0.142 | 63 | 140 | 74s | 0.409 | 0.121 | 97 |
| 56 | A2o | 0.555 | 0.121 | 96 | 141 | 64s | 0.409 | 0.127 | 87 |
| 57 | K4s | 0.554 | 0.152 | 48 | 142 | 94o | 0.406 | 0.070 | 163 |
| 58 | Q9o | 0.552 | 0.149 | 51 | 143 | 73s | 0.403 | 0.109 | 115 |
| 59 | A3o | 0.552 | 0.116 | 105 | 144 | 65o | 0.403 | 0.102 | 130 |
| 60 | K7o | 0.546 | 0.119 | 99 | 145 | 53s | 0.401 | 0.132 | 82 |
| 61 | Q7s | 0.543 | 0.148 | 54 | 146 | 84o | 0.399 | 0.082 | 153 |
| 62 | J8s | 0.539 | 0.155 | 46 | 147 | 83s | 0.389 | 0.117 | 103 |
| 63 | K2s | 0.539 | 0.138 | 69 | 148 | 43s | 0.388 | 0.119 | 101 |
| 64 | Q6s | 0.538 | 0.143 | 60 | 149 | 92o | 0.387 | 0.075 | 158 |
| 65 | 33 | 0.537 | 0.130 | 84 | 150 | 63s | 0.386 | 0.112 | 112 |
| 66 | J9o | 0.536 | 0.140 | 64 | 151 | 74o | 0.386 | 0.085 | 148 |
| 67 | T9s | 0.534 | 0.185 | 19 | 152 | 52s | 0.385 | 0.115 | 109 |
| 68 | K6o | 0.534 | 0.113 | 111 | 153 | 83o | 0.380 | 0.071 | 161 |
| 69 | T8s | 0.533 | 0.168 | 36 | 154 | 62s | 0.379 | 0.108 | 117 |
| 70 | Q8o | 0.529 | 0.120 | 98 | 155 | 54o | 0.379 | 0.090 | 141 |
| 71 | K3s | 0.526 | 0.149 | 52 | 156 | 42s | 0.376 | 0.107 | 123 |
| 72 | J7s | 0.525 | 0.143 | 61 | 157 | 72s | 0.376 | 0.103 | 128 |
| 73 | Q5s | 0.524 | 0.137 | 70 | 158 | 43o | 0.371 | 0.087 | 146 |
| 74 | J6s | 0.522 | 0.124 | 93 | 159 | 53o | 0.369 | 0.090 | 140 |
| 75 | Q7o | 0.522 | 0.096 | 134 | 160 | 82o | 0.367 | 0.067 | 164 |
| 76 | K5o | 0.522 | 0.108 | 121 | 161 | 73o | 0.363 | 0.072 | 160 |
| 77 | K3o | 0.521 | 0.099 | 133 | 162 | 64o | 0.362 | 0.090 | 143 |
| 78 | T9o | 0.518 | 0.140 | 65 | 163 | 32s | 0.357 | 0.111 | 114 |
| 79 | 98s | 0.515 | 0.170 | 35 | 164 | 63o | 0.352 | 0.078 | 157 |
| 80 | K4o | 0.513 | 0.105 | 127 | 165 | 72o | 0.344 | 0.063 | 167 |
| 81 | Q4s | 0.513 | 0.133 | 80 | 166 | 62o | 0.337 | 0.062 | 168 |
| 82 | Q6o | 0.512 | 0.093 | 137 | 167 | 52o | 0.336 | 0.081 | 156 |
| 83 | Q5o | 0.511 | 0.090 | 142 | 168 | 42o | 0.333 | 0.067 | 165 |
| 84 | Q3s | 0.509 | 0.135 | 73 | 169 | 32o | 0.312 | 0.058 | 169 |
| 85 | J7o | 0.507 | 0.115 | 107 |  |  |  |  |  |

Anchors worth memorizing: any pocket pair is at least about 50 percent against one random hand (22 is 50.3 in exact tables); AKo is about 65 percent against a random hand and about 21 percent against seven; 72o is 34 percent heads-up and 6 percent against seven. Against one random shove, half of all hands are favourites; under ICM at a full table you still fold most of them.

## 4. Push/fold: computed heads-up equilibrium and multiway anchors

### 4a. Heads-up equilibrium (computed Nov 6: fictitious play on a Monte Carlo 169 x 169 equity matrix; chip EV; no antes)

Percent of two-card combinations. SB shoves or folds; BB calls or folds.

| Effective stack (bb) | SB shoves | BB calls |
|---|---|---|
| 3 | 78% | 92% |
| 4 | 74% | 73% |
| 5 | 71% | 62% |
| 6 | 69% | 54% |
| 7 | 66% | 48% |
| 8 | 63% | 44% |
| 10 | 60% | 37% |
| 12 | 52% | 33% |
| 15 | 45% | 27% |
| 20 | 40% | 21% |
| 25 | 36% | 17% |

With a 0.1 bb ante per player: 5 bb 75% / 68%, 8 bb 68% / 48%, 10 bb 62% / 41%, 15 bb 50% / 31%.

At 10 bb the BB calling set is roughly any pair, any ace, K5o+ and K2s+, Q8o+ and Q7s+, J8o+ and J8s+, T9s. The SB shoving set is 60 percent of hands: every pair, every ace, every suited king and queen, most suited connectors and one-gappers, offsuit down to about K2o, Q7o, J7o, T7o.

These apply directly when two players are left, and as the "folded to the small blind" case with more players if ICM is ignored. ICM with 3 or more players left makes both sides tighter; the caller tightens more than the shover.

### 4b. Multiway anchors (approximate, from published Nash work; derive the real ones at the event)

Shoving when folded to you, 10 bb, no antes, as a share of combinations: early about 12 to 15 percent, middle about 18, cutoff about 25, button about 35, small blind as in 4a. At 7 bb the button shoves about 50 percent and the small blind about 65. At 5 bb or less, button and small blind shove nearly everything. At 15 bb early position is about 8 to 10 percent and the rest is raise/fold territory. Calling a shove under ICM with others still to bust: subtract 10 to 15 points from the heads-up calling percentages.

### 4c. Equity against several random hands (Monte Carlo, 20,000 deals each)

| Hand | vs 1 | vs 2 | vs 3 |
|---|---|---|---|
| AA | 85.5% | 73.4% | 63.7% |
| KK | 82.9% | 68.8% | 58.6% |
| QQ | 79.6% | 64.5% | 53.6% |
| JJ | 77.9% | 61.2% | 49.1% |
| TT | 75.7% | 57.5% | 45.2% |
| 99 | 71.9% | 52.8% | 40.9% |
| 88 | 69.4% | 49.7% | 37.6% |
| 77 | 66.4% | 46.7% | 34.5% |
| AKs | 66.8% | 50.9% | 41.2% |
| AKo | 64.9% | 48.7% | 38.7% |
| AQs | 65.7% | 48.7% | 39.9% |
| AJs | 65.9% | 48.6% | 38.6% |
| KQs | 63.6% | 47.4% | 37.5% |
| 66 | 63.7% | 43.1% | 31.7% |
| JTs | 58.0% | 41.8% | 34.4% |
| 22 | 50.6% | 30.7% | 21.8% |

Against two all-in random hands you need a third of the pot in chip EV, which almost any pair clears; under ICM early at a full table the right call is QQ+ (see 10_RESEARCH_FINDINGS.md section 3).

### 4d. How to derive the real numbers at the event

For a candidate shoving range R and calling range C, EV(shove) = P(fold) x (blinds + antes) + P(call) x (equity(R vs C) x pot - risk), with equity from the generator's class-vs-class matrix and the chip outcomes converted to points by the kit's ICM calculator. Iterate: best-response C to R, best-response R to C, average the strategies (fictitious play). It converges in a few hundred rounds and runs in seconds for two players; for 3 to 5 players left, solve the folded-to-SB, folded-to-button and under-the-gun shove spots separately with the other players assumed to fold or call with a fixed tight range. That is a ten-minute job for the assistant on the build machine and worth more than any flop heuristic.

## 5. ICM intuitions

- Chips you win are worth less than chips you lose, except heads-up where points are linear in chips.
- The bubble factor (ICM loss if you lose divided by ICM gain if you win) is 1 heads-up, 1.2 to 1.5 for a mid stack on the bubble, 2 or more for a comfortable stack facing a stack that covers it on the bubble. Required equity = BF / (1 + BF): 1.5 means 60 percent, 2 means 67 percent.
- Short stacks should shove before they are blinded under 5 big blinds; folding into zero points is never right.
- Big stacks should attack medium stacks (who have the most to lose) and avoid the short stacks' shoves without premium hands.
- At the 200-hand cap the points are split by ICM. A stack in a paying position by chips in the last 20 hands should not flip; a stack out of the points should.
- The ladder: when someone shorter than you is about to be blinded out, fold marginal spots for two or three hands.

## 6. Pure-Python toolbox for the 1 ms budget

- Exact 7-card evaluation: build at import a dictionary from a 5-card key to one of 7,462 rank classes (the Cactus Kev prime-product trick: each card is a prime by rank; a 5-card hand's product is unique for rank patterns, with a flush flag from suit bits), then take the best of the 21 five-card subsets. Pure Python cost: roughly 20 to 60 microseconds per 7-card hand. Build time at import: under a second if generated by enumeration of the 7,462 classes rather than all 2.6 million 5-card hands. Cache the board's partial evaluation per street.
- Rank-count fallback: count ranks and suits; detect quads, trips, pairs, flush by suit count 5+, straight by a 13-bit mask with the wheel case. Tens of microseconds, no tables, no bugs worth mentioning. Use it to validate the fast evaluator and as the exception fallback.
- Preflop: a 13x13 lookup (rank1, rank2, suited) to the 169-class index; everything else is table lookups by that index.
- Time guard: `t0 = time.perf_counter()` at entry; any optional refinement checks `perf_counter() - t0 < 0.0004` before starting.
- `gc.disable()` after import-time setup. Python's cyclic collector can pause for more than a millisecond when many objects were just created; the bot allocates little per decision, so disabling it is safe for a 200-hand table.
- Avoid: string formatting in the hot path, regex, `itertools.combinations` of the deck per decision, `sorted` on big lists, `copy.deepcopy`, logging, `random.choices` with weights (precompute cumulative thresholds).
- Startup: measure `python -I -S -c "import bot"` wall time. Keep it under two seconds in case import time is counted by the server's first-decision clock.
- Memory: a 100 MB limit is generous; a few hundred kilobytes of tables is all we need. Do not ship a 130 MB two-plus-two evaluator table.

## 7. Legality traps that turn into automatic folds

- Raise-to versus raise-by. The single most common bug. Test one hand by hand.
- Minimum raise equals the size of the last raise (not the last bet), and at least one big blind. An all-in for less than a full raise does not reopen the action for players who already acted.
- Facing an all-in that covers you, your only options are call or fold; "raise" is illegal.
- When nobody has bet on this street, "call" may be illegal and "check" is right; when someone has bet, "check" is illegal.
- A bet larger than your stack is a raise-to your stack; sizes must be integers in the kit's units.
- Big blind option: when everyone limps, the big blind may check or raise, not call.
- Heads-up, the button posts the small blind and acts first preflop, last postflop.
- Side pots: your effective stack against each opponent is the smaller of the two stacks; do not compute pot odds with chips you cannot win.
- Antes count in the pot for odds but are not part of "to call".
- Variant actions (discard, bid, pick, exchange) have their own legal sets. The default must be legal in every state.

## 8. Common first-draft bugs seen in bot competitions

- Monte Carlo in the decision loop, works on the laptop, times out on the server.
- Reading opponents' hole cards from a debug field that the server does not populate.
- Position computed from seat index instead of distance to the button.
- Treating folded players as live when counting opponents.
- Pot odds computed without antes or without the opponent's bet.
- Equity table indexed by card rank 0 to 12 in one place and 2 to 14 in another.
- State carried across tables through module-level variables.
- A `print` for debugging left in the submission, corrupting the protocol.
- The bot's own big blind counted as "to call" when the option to check exists.
