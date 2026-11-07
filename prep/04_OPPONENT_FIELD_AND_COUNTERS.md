# 04. The field, and how to beat each kind of bot in it

Everyone in the room gets the same 60 minutes, the same kit, and an AI assistant. That makes the field predictable in a way a human poker room never is. This sheet describes the bots we expect to meet, how to recognize each inside a 200-hand table, and what to do about it. Numbers reference the equity table in 09_REFERENCE_SHEETS.md (Monte Carlo, about 1 percent noise).

## 1. How the field evolves from T1 to T6

| Phase | What is in the field | What pays |
|---|---|---|
| T1 (end of build) | Many first-draft bots. Expect accidental fold-bots (illegal raises or timeouts that become automatic folds), a few all-in-every-hand bots, several TAG templates copied from public rehearsal simulators, a few random or always-call bots, and a handful of genuinely solid bots | Stealing blinds, value betting, never bluffing stations, not paying off shove-bots |
| T2 to T3 | Teams fix crashes and timeouts. Fold-bots mostly disappear. Shove-bots get removed by their owners once they see the result, or stay if they got lucky in T1 | Solid fundamentals, ICM discipline, exploiting whoever is still broken |
| T4 to T6 (71 percent of the score) | The strongest bots of the room, now opponent aware. Fewer free chips. More tables reach the cap with 3 to 5 survivors | Push/fold accuracy, ICM at the cap, not being exploitable (no fixed frequencies that a tracker can read), zero leaks |

Consequence: a bot tuned only to punish broken bots does well in T1 and fades. A bot that is solid first and exploitative second does well everywhere. Build the solid bot; make the exploits conditional on evidence.

## 2. Archetypes, detection, counter

### 2.1 The fold-bot (accidental or deliberate)

Where it comes from: a bot that raises illegal amounts, misreads raise-to versus raise-by, runs out of time, or crashes. The platform turns every error into "check if possible, else fold" (rule 3.7). So it checks when free and folds to any bet, and never puts chips in voluntarily.

Detection: zero voluntary chips in every opportunity (never calls a raise, never opens, never bets). After 12 such opportunities a genuine tight bot would have done this about 20 percent of the time; after 20, about 8 percent. The exploits below are graded by confidence.

Counter:
- From 8 opportunities with no voluntary action: steal its blinds with any two cards whenever the action folds to us and it is in a blind, as long as the raise is small relative to our stack. This also works against nits, so it costs nothing to be early.
- From about 20 opportunities with no voluntary action: bet every street into it with any two cards whenever we are in a pot together. It will check-fold. Do not slow play, do not check to induce; it never bets.
- Never bluff-catch against it. If it ever bets or raises, it is not a fold-bot; downgrade the label immediately.
- It bleeds blinds slowly and can outlast reckless players. In the simulations a fold-everything bot scored 10.6 points per table under flat payouts (85 percent of average) by finishing 3rd to 5th while others busted each other, and 17.1 in a zoo with a shover and a maniac. Do not let it finish above us: take its blinds every orbit so it busts before the cap.

### 2.2 The shove-bot (all-in every hand, or nearly)

Where it comes from: the two-minute strategy, and MIT Pokerbots folklore. Someone will submit it for T1.

Detection: preflop all-in on 60 percent or more of its hands after 5 hands. A deliberate one is identified in 3 hands.

What it does to a table that does not adapt (simulated, 10_RESEARCH_FINDINGS.md section 2): against seven tight-aggressive bots that keep opening and folding to it, the shove-bot won 84 percent of tables and scored 34 points per table (average is 12.5), because it pockets the blinds plus every open, and by the time someone calls with TT+ the caller is short and the shover covers it. Expect a shove-bot near the top of the T1 leaderboard if the room is naive.

Counter (measured):
- Stop feeding it. Never open-raise while it is still to act behind us; raise-folding was the biggest leak in the simulated field. Either fold, or shove first with a hand we would happily see called by a random hand.
- Threshold: hands with at least 65 to 70 percent equity against a random hand, which is 77+, AJs+, AK (65 percent) or 99+ (70 percent). Chip EV says 50 percent; ICM at a full table says this. Both 0.65 and 0.70 tested best for the adapter under flat and top-heavy payouts; 0.50 to 0.55 was worse than not adapting at all.
- Call its shove with the same set. Widen when the shove-bot is short (its all-in is cheap: under 10 big blinds call with the top 25 to 30 percent) or when we are short enough that the blinds will do the job anyway.
- Two shove-bots at the table: our hand must beat two random hands. Equity against two random hands is AA 73, KK 69, QQ 65, JJ 61, TT 58, AK 49 to 51. Call two all-ins with QQ+ early under flat payouts, JJ+ and AK under top-heavy, wider when they are short. Otherwise wait; they collide on their own.
- One adapter at the table knocks the shove-bot from 34 points to about 14 and earns 3 to 5 points more than the non-adapting bots at the same table. Seven adapters cut the shove-bot to about 1.3 points and bust it first two thirds of the time.
- If ICM luck correction is on for scoring, the shove-bot's results are replaced by its expectation and so are ours; the strategy does not change, the variance disappears.

### 2.3 The maniac (raises or bets most hands, not always all-in)

Detection: preflop raise rate 50 percent or more over 10 hands, or bets two thirds of its postflop opportunities.

Counter: widen value. Three-bet or call with the top 15 to 20 percent preflop; call down with top pair or better; do not bluff it; let it bet into our strong hands rather than betting first. Under ICM, still avoid stacking off with one pair against a maniac that covers us unless the payout table is top-heavy.

### 2.4 The station (calls too much, rarely raises)

Detection: calls 70 percent or more of bets postflop, raise rate near zero.

Counter: value bet thinner and bigger, three streets with top pair good kicker or better. Never bluff. Fold to its rare raises without two pair or better. Preflop, isolate its limps with a raise and bet the flop. Simulated, a pure station among seven TAGs scored 0.35 points per table and busted 8th 83 percent of the time; a random bot scored 1.8. They are the chips everyone else is fighting over, so be in the pot with them when you have something.

### 2.5 The nit (tight, mostly folds)

Detection: VPIP under 12 percent after 20 hands, folds to steals at 80 percent or more.

Counter: steal its blinds every time; fold to its 3-bets without QQ+ or AK; c-bet it on dry boards with air; give up when it continues past the flop. It will finish in the points often at loose tables because it never busts early, so take its blinds relentlessly to shrink it before the cap.

### 2.6 The TAG template (copied from a public simulator or a sensible first prompt)

Detection: VPIP 15 to 25 percent, raise-first-in from late position, folds to 3-bets often, c-bets often, gives up on the turn.

Counter: default strategy. Steal when it is in the blinds and the table folds a lot. Float or raise its c-bets rarely; it folds to turn aggression more than it should, so bet the turn with equity when it checks.

### 2.7 The random bot

Detection: raise sizes all over the place, calls and raises with no relation to pot size, folds at odd times.

Counter: its bets carry no information. Value bet every street with any pair or better. Call down with medium strength when the price is right. Treat its all-ins as a random hand and call with the ICM-adjusted threshold. It busts fast on its own; do not do anything fancy.

### 2.8 The ICM-aware TAG (what the top of the room becomes by T6)

Detection: tight early, steals late, re-shoves correctly, folds to our shoves when it should, exploits our folds.

Counter: do not leak. Avoid fixed patterns it can read in 50 hands (always c-betting, always folding the big blind to a 3x raise). Play the push/fold game accurately. Our edge against this bot is small; the edge comes from the rest of the table.

## 3. Things we can learn from a table in 10 hands

- Fold-to-steal rate of the blinds. If the two players in the blinds have folded to the last four steals, steal with 50 percent of hands from the button.
- Limpers. Anyone who open-limps is weak or broken; isolate.
- Shove frequency. One shove-bot changes the whole table: tighten, let it run into other people.
- Table aggression. A table where every pot has a raise and a 3-bet is one to play tight and value heavy; a table of checks and calls is one to bet into.

## 4. Self-play sanity

Fillers are copies of submitted bots, which can include ours. Also, by T4 to T6 several bots will resemble ours. Check in the local evaluation that eight copies of our bot do not create pathologies: no infinite steal wars, no two copies ending every hand all-in preflop, no detector misfiring on a copy of itself as a fold-bot (a tight bot that defends its blind against a steal is not a fold-bot; the detector requires zero voluntary action, not low VPIP).

## 5. What to look at in the hand histories between rounds

After each round the team page offers the round's hand history as gzipped JSON lines with opponents named, our cards in every hand, and other players' cards whenever they were public (every showdown reveals all hands). The kit ships a streaming reader. Download the subset, run P8, and spend five minutes per round on:

1. Our health: `missed` and `restarts` must be zero. Anything else is bug-fixing before strategy.
2. Finish distribution: how often 1st, how often 6th to 8th. Too many early busts means too loose or too much flipping; too few firsts means too passive late.
3. Hands where we busted: were we the aggressor with a marginal hand, or did we call a shove too wide?
4. How often the table hit the cap and how many survived. If most tables hit the cap with 4 to 5 survivors, the cap logic and ICM share are worth more work than the flop game.
5. Count the archetypes we met, by named team: shove rate, VPIP, fold-to-raise, calling frequency. Names are useless inside a table (seats are anonymized and cross-table memory is banned), but the mix tells us how aggressive to make the detector thresholds. If fold-bots or shove-bots are common, loosen the exploit triggers; if they are gone by T3, tighten them back so the detectors do not misfire on solid bots.
