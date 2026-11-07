# 02. Format math: what the scoring actually rewards

Format page facts (Nov 6): 8 players, 2,000 chips, blinds 10/20 rising every 20 hands, hand cap 250, payouts 50/30/20 for three places, ICM at the cap, six rounds weighted 1 to 6 with at least 5,000 iterations each, practice runs every 10 minutes during the build, countback tiebreak. Only the blind schedule beyond 10/20 is still unknown; numbers that depend on it are labelled SYNTHETIC.

## 1. The weights

Final score = T1 + 2 T2 + 3 T3 + 4 T4 + 5 T5 + 6 T6. Weights sum to 21.

| Tournament | Weight | Share of final | Approximate start (if the build starts 6:08 PM) |
|---|---|---|---|
| T1 | 1 | 4.8% | 7:08 PM |
| T2 | 2 | 9.5% | 7:28 PM |
| T3 | 3 | 14.3% | 7:48 PM |
| T4 | 4 | 19.0% | 8:08 PM |
| T5 | 5 | 23.8% | 8:28 PM |
| T6 | 6 | 28.6% | 8:48 PM |

T4 through T6 are 71 percent of the score. The bot that is active at 8:08, 8:28 and 8:48 decides the result. T1 barely matters except as a diagnostic (health, missed decisions, how the field plays).

Submissions are one per five minutes, so there are about four usable slots between consecutive tournaments. A submission must be validated before the next tournament starts to count for it. Upload at least five minutes before a start time, or assume it lands in the one after.

## 2. Points per table

An average bot scores `payout_total / 8` points per table (if `payout_total` is 100, that is 12.5). Over six tournaments an average bot totals 12.5 x 21 = 262.5. A bot that scores 1.3 times average every tournament totals about 341. The top five of the field will likely sit somewhere in the 1.2x to 1.6x band, depending on how many broken bots are in the room.

The payout list has at most five entries, and the Getting Started page gives 50/30/20 as the default, which pays three of eight places. It also warns that a round may draw payouts per table, so the bot reads `state.config.payouts` on every table and derives "places paid" from it. The Format page shows the round defaults; copy them into 12_KIT_INTERFACE.md when you have them.

With 50/30/20, five of eight players at every table score zero. That is a strong survival incentive, but a top-heavy one: half the pool goes to the winner, so chips are worth more than under a flat table.

## 3. ICM in numbers (Malmuth-Harville, 50/30/20)

Eight players left, stacks 4000 / 3000 / 2500 / 2000 / 1500 / 1200 / 1000 / 800:

| Stack | Share of chips | ICM points | Share of pool |
|---|---|---|---|
| 4000 | 25.0% | 22.6 | 22.6% |
| 2000 | 12.5% | 13.0 | 13.0% |
| 800 | 5.0% | 5.5 | 5.5% |

Under this top-heavy table ICM is close to linear while eight are left. Eight equal stacks, 2000 each: calling an all-in for your whole stack gains 10.0 points if you win and costs 12.5 if you lose, so the break-even equity is 55.6 percent (chip EV says 50). Under the flat five-place table used in the simulations it was about 64 percent. Either way: tighter than pot odds, and the gap widens as the bubble approaches.

Bubble (4 left, 3 paid), stacks 6000 / 4000 / 3000 / 3000: the 6000 stack facing a 3000 shove needs 57 percent equity to call; the 3000 shover, if called, needed 66 percent to be right. Fold equity is everything on the bubble, and being called is a disaster for the shover.

Five left at the 200-hand cap, stacks 6000 / 4000 / 3000 / 2000 / 1000: ICM gives 31.4 / 25.1 / 20.7 / 14.9 / 7.9. The 1000 stack is "out of the money" by chip count but still collects 7.9 points at the cap, so even a short stack should not throw itself away in the last hands if it can fold to the cap; it should shove only with real fold equity or real hands.

Two left at the cap, 50/30: a 60/40 chip split is worth 42 and 38. Winning outright is 50. Heads-up late is chip EV with a modest prize for finishing.

## 4. Blind pressure and the 200-hand cap

Blinds rise every 20 hands and the cap is 250, so a table that lasts sees 13 levels. There are 16,000 chips at the table.

SYNTHETIC schedules for intuition: "eight" (10/20, 15/30, 25/50, 50/100, 75/150, 100/200, 150/300, 200/400, then flat) and "growing" (the same, continuing 300/600, 400/800, 500/1000, 600/1200, 800/1600). If the real schedule keeps growing, the big blind at hand 200 is 10 percent of all chips on the table and the last 50 hands are an all-in game.

- Eight-handed, an orbit is 8 hands, 2.5 orbits per level. Under the growing schedule a bot that only folds busts around hand 120 at a full table; under the flat-after-level-8 schedule around hand 140. Either way it outlives everyone who loses a stack early.
- Under the growing schedule, three players left at hand 180 means the average stack is 5,300 chips against a 600 or 800 big blind: 7 to 9 big blinds. The last 60 hands are push/fold, and the simulations show most capped tables end heads-up (10_RESEARCH_FINDINGS.md, 8c).
- In simulations of the real format (20-hand levels, 250 cap), 65 percent of tables of disciplined bots reached the cap under the growing schedule and 76 percent under the flat one, mostly with two survivors under the growing schedule and 2 to 4 under the flat one. Tables with a maniac or an all-in bot resolved early. Expect the ICM split to decide a large share of your points, often heads-up.
- If 2 or more survive to hand 250, points are split by ICM. The bot needs the hand number (or a count) to know how close the cap is. Within the last 15 to 20 hands, a stack that is already in the top places should refuse marginal confrontations; a short stack that is out of the money needs chips now.
- If antes appear in the blind triples, pot sizes grow and preflop ranges widen. Recompute pot odds with antes included.

## 5. How precise are the results

Each tournament is 10,000 tables. If the per-table standard deviation of points is around 12 to 15 (SYNTHETIC total of 100), the standard error of a team's average is about 0.12 to 0.15 points per tournament. Gaps between neighbouring teams on the leaderboard will usually be larger than that. The ranking measures strength against this field, not luck. There is no reason to seek variance.

The flip side: a systematic leak costs the same at every table. One missed decision per table (a timeout) is one forced fold per table, 10,000 times.

## 6. What this all implies

1. Never time out, never crash. A fold is a certainty; a brilliant decision one millisecond late is a fold.
2. Survival first until the payout table says otherwise. Avoid flips for your stack in the first 50 hands unless you are a clear favourite.
3. Steal relentlessly from bots that fold too much; most early bots will.
4. The late game is push/fold under ICM, often heads-up at the cap with blinds that dwarf the stacks. Get this part right; it decides more tables than any flop decision. Under the real format the loose opener beat the tight one by 4.5 points per table in simulation; aggression late is not optional.
5. Spend the build hour on a legal, fast, solid v1. Spend 7:08 to 8:48 on exploiting what you see in the hand logs and fixing leaks. The T6 bot is the product.
