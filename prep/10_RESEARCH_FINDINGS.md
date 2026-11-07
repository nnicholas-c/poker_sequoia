# 10. Research findings: what the simulations and the equilibrium solves say

Everything below was measured on Nov 6 with the offline tooling in `research/` (a small pure-Python eight-player sit-and-go simulator with crude archetype bots, a Monte Carlo equity generator, and a fictitious-play push/fold solver). The simulator uses the published format (8 players, 2,000 chips, blinds up every 25 hands, 200-hand cap, ICM split at the cap) and SYNTHETIC values where the organizer has not published any: blind schedule 10/20, 15/30, 25/50, 50/100, 75/150, 100/200, 150/300, 200/400, and payouts 40/25/15/12/8 ("flat") or 60/25/10/5 ("top-heavy").

The archetype bots are deliberately simple. Treat every number as a direction and an order of magnitude, not as a forecast of tonight's field. 95 percent intervals are given where they matter. Raw output is in `research/sim_results*.txt`.

## 1. The cap is the normal ending, not the exception

| Field | Tables reaching hand 200 | Survivors at the cap (most common) |
|---|---|---|
| eight tight-aggressive heuristics | 76% | 2 (38%), 3 (34%), 4 (19%), 5 (7%) |
| one tight-aggressive among seven nits | 93% | 3 (33%), 4 (25%), 2 (18%), 5 (13%) |
| one all-in-every-hand bot plus seven tight-aggressives | 12% | 2 or 3 |
| mixed zoo (shover, fold-bot, station, random, maniac, nit, two TAGs) | 21% | 2 |

In a disciplined field most tables never produce a single winner. The ICM split at hand 200 is where most points are decided, with 2 to 4 survivors. Two consequences for the bot: (1) the hand counter and the cap logic are first-class features, not polish; (2) chips accumulated by steals convert to points at the cap only if you still have them, so the last 30 hands are about not losing stacks, except for stacks that are out of the money by chip count.

With two survivors, ICM is linear in chips, and heads-up is a near-chop under flat payouts: with 40/25 for the last two places, a 60/40 chip split is worth 34 and 31 points. Winning everything is worth 40. Heads-up play late is chip EV with a small prize for actually finishing.

## 2. The all-in-every-hand bot is lethal against a field that does not adapt

| Table | Shove-bot points per table (average bot = 12.5) | Shove-bot wins the table | TAG points |
|---|---|---|---|
| shover plus seven non-adaptive TAGs, flat payouts | 34.0 (+-0.7) | 84% | 9.4 |
| same, top-heavy payouts | 50.9 | 84% | 7.0 |
| two shovers in a mixed zoo | 13.1 each | 33% each | 13.4 |

Why it works: the non-adaptive TAGs open-raise and then fold to the shove, so the shover collects blinds plus every open, compounding at roughly 30 to 70 chips a hand early. When a TAG finally calls with TT+ it is already short, so the shover covers it and survives even when it loses the flip. By hand 40 the shover has a quarter of the chips and the table is lost.

The MIT Pokerbots story about a team that went all-in on every hand is the same phenomenon. Someone in the room will submit this for T1. If the T1 field is mostly naive, a shove-bot may top the T1 leaderboard and tempt copycats for T2.

## 3. The correct response, measured

An adaptive TAG that (a) detects a seat shoving 60 percent or more of its hands, (b) never open-raises into that seat while it is still to act, and (c) either folds or shoves first with hands whose equity against a random hand is at least T, and calls the shove with the same threshold:

| T (equity vs a random hand) | Hands in the set, roughly | One adapter among six naive TAGs, flat: adapter / shover / naive TAG points | All seven adapt, flat: adapter / shover |
|---|---|---|---|
| 0.50 | top half of hands | 11.5 / 16.9 / 11.9 | 13.3 / 7.0 |
| 0.55 | 44+, any ace, K9o+, K6s+, Q9o+, Q8s+ | 12.5 / 14.8 / 12.1 | 13.6 / 4.8 |
| 0.60 | 55+, A7o+, A4s+, KJo+, KTs+ | 13.6 / 14.0 / 12.1 | 13.9 / 2.7 |
| 0.65 | 77+, AJs+, AKo | 15.1 / 13.7 / 11.9 | 14.1 / 1.4 |
| 0.70 | 99+ | 16.8 / 19.1 / 10.7 | 14.1 / 1.2 |

Top-heavy payouts give the same ordering (0.65 and 0.70 best for the adapter).

Reading this table:

- Adapting is worth 3 to 5 points per table for the adapter versus the naive TAGs at the same table, on a base of 12.5. Nothing else in these simulations is worth as much.
- Tighter than chip EV is right. Chip EV says call with 50 percent; ICM at a full table with flat payouts says 65 to 70 percent (77+, AK, AQs, AJs; or 99+ if you want to be strict). This is because losing a stack early is worth more than winning one, and because the shover will bust into someone else eventually.
- At T = 0.70 the shover still does well (19 points) because six naive TAGs feed it, and the adapter does best of all by outlasting them. That is the free-rider effect under flat payouts. It only works while others are naive; when the whole table adapts, the shover scores about 1.3 points and busts first 65 to 75 percent of the time.
- The single biggest leak against a shover is raise-folding. The naive TAG already called only with TT+ (about the 0.70 threshold) and still scored 9.4 because it kept opening and folding. Stop putting chips in that you will not defend.
- Against two shovers, hands must beat two random hands. Equity against two random hands: AA 73%, KK 69%, QQ 65%, JJ 61%, TT 58%, AKs 51%, AKo 49%. Call two all-ins with QQ+ early under flat payouts, JJ+ and AK under top-heavy, wider when the shovers are short or when you are.

Should we be the shover? Against a naive table, yes in chip terms; the problem is that one adapter at the table cuts the shover to about average and seven adapters bury it, and we cannot see who is at the table before sitting down. The adaptive version of the idea is safer: shove wider from late position only when the table has demonstrably stopped defending, and stop the moment anyone calls with a non-premium or shoves back. The simulator could not confirm a gain from a crude version of that rule against TAG or nit fields, because those fields defend their big blind often enough that the trigger never fired. Keep it as a T4 to T6 refinement if the hand logs show tables that fold to everything.

## 4. The fold-bot cashes

| Payouts | Fold-everything bot, points per table | Finish distribution |
|---|---|---|
| flat 40/25/15/12/8 | 10.6 (85 percent of an average bot) | 3rd 24%, 4th 32%, 5th 28%, 2nd 4% |
| top-heavy 60/25/10/5 | 5.0 | same places |

A bot that never puts in a chip outlasts everyone who busts in a confrontation and finishes 3rd to 5th most of the time under flat payouts. In a mixed zoo with a shover and a maniac it scored 17.1, above every other archetype. Lessons: never bust early for nothing, and take the fold-bot's blinds every orbit so that it does not finish above you. A broken opponent is an ATM only if you actually withdraw.

## 5. Stations, random bots and maniacs lose; nits lose slowly

| Archetype among seven TAGs, flat payouts | Points per table | Busts 6th to 8th |
|---|---|---|
| calling station (calls everything, never raises) | 0.35 | 97% |
| random legal actions | 1.8 | 90% |
| maniac (raises 55 percent of hands, bets most flops) | 8.2 (wins the table 10 percent of the time) | 65% |
| nit (half the TAG ranges, risk-averse) | 11.1 | 33% |

Value-bet the stations and the random bots; never bluff them. Let the maniac bet into strong hands. Steal from the nit.

## 6. Open wider, call all-ins tighter

Tightness sweep (same TAG, opening ranges scaled), two of each at a table, flat payouts: TAG 13.4, 30 percent looser 13.1, 50 percent tighter 12.0, half ranges 11.5. Over-tight opening costs about 2 points per table; somewhat looser than the default costs nothing measurable.

Risk-premium sweep on all-in calls (required equity = pot odds x (1 + lambda)), two of each at a table, flat payouts: lambda 1.0 scored 13.5, lambda 0.5 12.3, lambda 0.25 12.2, lambda 0 12.1 (intervals about +-0.4). Being much more careful than pot odds when calling off a stack gains about 1.3 points. The same ordering held under 60/25/10/5. So: steal with a wide range, and refuse to call all-ins without a clear edge. Those two are not in tension; they are the two halves of tournament poker.

## 7. Heads-up push/fold equilibrium (computed, chip EV, no antes)

Fictitious play on a Monte Carlo 169 x 169 class-vs-class equity matrix (400 deals per pair). Percent of two-card combinations.

| Effective stack (bb) | SB shoves | BB calls a shove |
|---|---|---|
| 3 | 78% | 92% |
| 5 | 71% | 62% |
| 7 | 66% | 48% |
| 8 | 63% | 44% |
| 10 | 60% | 37% |
| 12 | 52% | 33% |
| 15 | 45% | 27% |
| 20 | 40% | 21% |
| 25 | 36% | 17% |

With a 0.1 bb ante per player: 5 bb 75% / 68%, 10 bb 62% / 41%, 15 bb 50% / 31%. These match the published Nash charts within noise, which validates the recipe: equity matrix plus best-response iteration converges in a few hundred rounds and runs in seconds. At the event, run the same loop with the kit's ICM calculator converting chip outcomes to points, for the actual payout table and for 3 to 5 players left, and you have the real endgame ranges instead of folklore. The recipe is in 07_AI_PROMPT_PACK.md (P2 and P3) and 09_REFERENCE_SHEETS.md section 4.

The 10 bb BB calling set from the solve is roughly: any pair, any ace, K5o+/K2s+, Q8o+/Q7s+, J8o+/J8s+, T9s. The 10 bb SB shoving set covers 60 percent of hands and includes every pair, every ace, every suited king and queen, most suited connectors and one-gappers, and offsuit hands down to about K2o, Q7o, J7o, T7o.

## 8b. The same runs under the dashboard's default payouts, 50/30/20 (three of eight paid)

After the Getting Started page named 50/30/20 as the default, the key lineups were re-run with it (1,200 tables each). The ordering of every conclusion survived; the magnitudes moved a little.

| Result | 40/25/15/12/8 (five paid) | 50/30/20 (three paid) |
|---|---|---|
| Tables reaching the cap, eight TAGs | 76% | 77% (2 to 4 survivors) |
| Shove-bot vs seven naive TAGs | 34.0 pts, wins 84% | 40.9 pts, wins 81% |
| One adapter among six naive TAGs, best T | 0.65 to 0.70: 15.1 to 16.8 vs TAG 11 to 12 | 0.65 to 0.70: 15.7 to 17.9 vs TAG 9.6 to 11.0 |
| All seven adapt at 0.65: shover | 1.4 | 1.4 (busts first 66%) |
| Fold-everything bot vs seven TAGs | 10.6 | 6.3 (3rd to 5th, but 4th and 5th pay nothing now) |
| Fold-everything bot in the mixed zoo | 17.1 | 18.1 (the best score at the table) |
| Station / random vs seven TAGs | 0.35 / 1.8 | 0.14 / 4.2 |
| Risk premium on all-in calls, lambda 1.0 vs 0 | 13.5 vs 12.1 | 13.1 vs 11.6 |
| Opening tightness: loose / TAG / tight / nit | 13.1 / 13.4 / 12.0 / 11.5 | 13.7 / 13.2 / 12.3 / 10.8 |

Two things worth noting for 50/30/20. First, ICM is closer to linear with eight left (02_FORMAT_MATH.md section 3), so the measured benefit of the all-in risk premium is less about the payout curve and more about not gambling on crude equity estimates; keep lambda, but let the solved ICM ranges from P2 drive the late game. Second, the fold-bot's absolute score halves because 4th and 5th pay nothing, yet in a wild table it still outscores every other archetype. Do not bust early for nothing.

## 8c. The real format: 20-hand levels, 250-hand cap, 50/30/20 (1,000 tables per lineup)

The Format page fixed the level length at 20 hands and the cap at 250. The blind schedule beyond 10/20 is still unknown, so two SYNTHETIC schedules were run: "eight" (the eight-level ladder above, then flat at 200/400) and "growing" (continuing to 800/1600 by level 13).

| Result | growing schedule | eight-level flat schedule |
|---|---|---|
| Tables reaching the cap, eight TAGs | 65% (two survivors 94% of the time) | 76% (2 to 4 survivors) |
| Median hands per table, eight TAGs | 250 | 250 |
| Shove-bot vs seven naive TAGs | 40.2 pts, wins 80% | 40.4 pts, wins 80% |
| One adapter (T = 0.65) among six naive TAGs | adapter 16.4, shover 18.2, TAG 10.9 | similar |
| All seven adapt at 0.65: shover | 1.4 (busts first 64%) | similar |
| Fold-everything bot vs seven TAGs | 4.6 | similar |
| Risk premium on all-in calls: lambda 0 / 0.25 / 0.5 / 1.0 | 11.4 / 12.2 / 13.5 / 13.0 | |
| Opening tightness: loose / TAG / tight / nit | 18.5 / 14.0 / 9.9 / 7.6 | |

The last row is the headline. With blinds that keep climbing for 13 levels, the loose opener (ranges 30 percent wider than the TAG default) scored 18.5 points per table against 14.0 for the TAG, 9.9 for a bot with ranges 50 percent tighter, and 7.6 for the nit; it also won 19 percent of tables outright against 8 percent. Blinds that large relative to stacks make every uncontested pot worth a real fraction of a stack, and a bot that folds its way to the cap arrives there with nothing. Under the real format, "open wide, call all-ins carefully" is worth several points per table, not one.

A moderate risk premium on all-in calls (lambda about 0.5) beat both no premium and a very large one. The shove-bot and fold-bot conclusions are unchanged.

## 8. What this changes in the playbook

1. Build the cap logic and the ICM-at-cap awareness in v2, not v4. Most tables end there.
2. The shover response is the highest-value exploit: detect in 3 to 5 hands, never raise-fold into it, fold or shove first with 77+/AK/AQs/AJs, call its shove with the same set, QQ+ against two shovers. Widen when the shover is short.
3. Opening ranges stay normal or slightly loose; all-in calls carry a real risk premium. Steal, do not gamble.
4. Take the fold-bot's and the nit's blinds every orbit. They cash by default; make them pay for it.
5. Value-bet the stations and random bots relentlessly and never bluff them.
6. Heads-up late is chip EV; three- to five-handed near the cap is where ICM does the most work.
