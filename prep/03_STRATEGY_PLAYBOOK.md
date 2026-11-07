# 03. Strategy playbook: the bot we want to end up with by T6

This is the design to carry in your head and to feed to the AI at the event (07_AI_PROMPT_PACK.md turns it into prompts). It is written for standard no-limit hold'em at an 8-max sit-and-go with a 200-hand cap. 05_VARIANT_PLAYBOOK.md says what to change when the variant is revealed.

The ordering below is also the build order. Each layer is useful on its own and the bot should be submittable after every layer.

## 0. The shape the real interface forces (see 12_KIT_INTERFACE.md)

`act(state, memory)` returns an Action and the bytes we want back next turn. Nothing else persists: copies of the bot are forked from one import and any copy may answer any table, so `self` and globals are read-only tables built at import, and every per-table fact (hand counter, opponent counters, labels, cached numbers) lives in the memory blob. The blob is a fixed-layout `struct` record with a version byte, a length and a checksum; it is parsed inside try/except and replaced by a fresh record on any failure, because a blob that makes act raise comes back unchanged forever. Keep it under 16 KB; a few hundred bytes is enough.

`state.events` is a complete public feed since our last turn, including hands we folded early, so the tracker is fed from events, not from a kit history we have to hope for. Showdowns reveal every hole card, so the tracker also sees what opponents turned up.

eval7 is installed in the sandbox. It evaluates a 7-card hand in microseconds and makes table generation on the build box fast. The rank-count evaluator from the earlier plan is now only the exception fallback.

## 1. Non-negotiables (the layer that wins or loses by itself)

1. Never throw. `act` is wrapped so that any exception becomes check if offered, else fold, else the automatic choice `Action(first.kind, first.min_amount)`; the wrapper also returns the previous memory untouched in that case. It also catches a bad return value.
2. Never time out. Budget 0.3 ms per decision, measured on the build box under load, p99.9, with no bank: the upload test match has none and a timeout empties the table's bank anyway. No live Monte Carlo on the main path, no per-decision table building, no parsing of long event lists with string formatting.
3. Always legal. Choose only from `state.legal_actions`; clamp every `raise_to` total into [min_amount, max_amount] with integer arithmetic (floats are rounded down and can land one chip under the minimum); if raise is not offered, call if offered, else check, else fold. Check and call are never offered together, and fold is not offered when a check is free. Legal and dumb beats illegal and smart, because illegal means the fallback.
4. Only the standard library, poker_agent_sdk, poker_agent_protocol, eval7 and (at import time only) NumPy. Never import poker_engine or pokerkit, even in a helper file: `check` rejects the whole zip. No prints. No files except reading our own data files at import. No threads.
5. Deterministic given the same inputs: a `random.Random` seeded from the table id and hand number taken from the state, never from wall time, so bugs reproduce.
6. Precompute at import: the 52 eval7 Card objects, the preflop tables, the postflop tables, the position maps, the risk table. Run one throwaway decision at import so every lazy cache exists before the fork. Then `gc.disable()` (or `gc.freeze()` then disable) so the collector cannot pause a decision. The bot allocates little per decision, so this is safe. Set OMP_NUM_THREADS, MKL_NUM_THREADS and OPENBLAS_NUM_THREADS to 1 before importing NumPy.
7. All per-table state in the memory blob, nothing in globals, nothing in /tmp. A new table is recognized by `memory == b""`.
8. Cache per hand inside the blob: the hand number, the evaluated strength of my hand on the current board, the number of live players, the ICM-derived risk constant. Recompute only when the board or the stacks change.

Test this layer in isolation: run `poker-agent play` for a few hundred tables with the dumbest possible strategy (fold everything, then check-or-call everything) and confirm zero failed decisions, then `poker-agent check` and the heads-up 20-hand test against examples/check_or_fold with the bank mentally set to zero. That is the first upload, around minute 15 to 20.

## 2. Hand strength without live simulation

Preflop: the 169 starting-hand classes. For each class store (a) equity against 1 to 7 random opponents and (b) its rank in the heads-up ordering (a percentile from 0 for AA to 1 for 72o). 09_REFERENCE_SHEETS.md has a reference table; regenerate at the event with eval7 and the variant's deck and ranking so that any change is baked in. With eval7 on the build box this takes seconds, and the output is pasted into the bot as a literal or saved as a data file next to agent.py.

Postflop: eval7 evaluates the 7-card hand exactly in a few microseconds and gives the made-hand class. Add draw detection (flush draw, open-ended, gutshot, combo, overcards) and a board texture summary (paired, monotone, two-tone, connected, high card). Map (street, made-hand class, draw flags, number of live opponents) to an equity estimate through a small table generated at the event by a Monte Carlo against random hands, then shade it down for opponents who have shown aggression (see section 7). This is coarse and it is enough: the mistakes it makes are a few percent of equity; a timeout costs 100 percent.

Optional refinement, behind a time check and only when `state.time_bank_ms` is full and the decision is all-in sized: eval7's Monte Carlo against a range for about 100 to 200 iterations. Measure it on the build box first; if its p99 is above 0.4 ms, leave it out. The tables carry the bot; the refinement is a T4 to T6 luxury.

Keep a small rank-only fallback (pair, two pair, and so on by rank counting) in case the eval7 path has a bug: the wrapper falls back to it on exception.

## 3. Preflop

Inputs: my hand class, position bucket, effective stack in big blinds (the smaller of my stack and the largest stack still to act or already in), number of live players at the table, action so far this hand (limpers, raisers, raise size, all-ins), and the opponent labels from section 7.

Position buckets for 8-max: EP (first two seats after the blinds), MP (next two), CO, BTN, SB, BB. As players bust, re-bucket by seats-before-the-button so a 5-handed table maps to MP/CO/BTN/SB/BB.

Stack regimes by effective big blinds:

- Deep (over 25 bb): raise or fold. Open 2.5 bb early, 2.2 to 2.3 bb from CO/BTN, 3 bb from SB. Never open-limp. Isolate limpers with a raise of 3 bb plus 1 bb per limper. Three-bet with the top 4 to 5 percent for value and a few suited connectors or suited aces as bluffs only against opponents who fold to 3-bets; call 3-bets with the next 5 percent when in position and the raise is not more than a third of the effective stack; fold the rest. Four-bet or shove only with QQ+ and AK against unknowns.
- Medium (12 to 25 bb): still raise or fold, open 2 to 2.2 bb. Facing an open, either re-shove or fold; re-shove the top 8 to 12 percent depending on the opener's label and ICM. Facing a 3-bet after opening, shove with the top 7 percent or fold.
- Short (12 bb or fewer): push or fold. Shove ranges by position as a fraction of the 169 ordering (SYNTHETIC anchors for 10 bb without antes: EP about 12 to 15 percent, MP about 18 percent, CO about 25 percent, BTN about 35 percent, SB about 45 percent when it folds to you; widen with antes, narrow with ICM pressure and callers behind who are loose). Calling a shove needs more than pot odds under ICM: use the risk-adjusted threshold from section 6.
- Under 5 bb: shove any two from the button or small blind when folded to; from earlier seats shove the top 40 percent; call shoves with the top 50 percent heads-up for your stack.

Opening ranges (percent of the 169 ordering) at a full table, SYNTHETIC anchors: EP 11 to 13, MP 14 to 17, CO 22 to 27, BTN 38 to 45, SB 32 to 40. Against a table whose blinds fold too much (section 7), add 10 to 20 points to CO/BTN/SB.

Big blind defence: against a min-raise with no callers, call with about the top 45 percent and 3-bet the top 6; against 2.5 bb raises call with the top 30 percent. Fold more when the raiser is a nit, call more when the raiser is a maniac (their range is wide, your pairs and aces are ahead).

Limpers: an opponent who limps is weak or broken. Raise them; if they call and check the flop, bet.

Two rules the simulations made non-negotiable (10_RESEARCH_FINDINGS.md):

- Never open-raise and fold. If a seat that shoves most hands is still to act behind us, we either fold now or we shove first with a hand we would call its shove with. Raise-folding into a shover was the single largest leak in the simulated field, worth more than the calling threshold itself.
- Opening ranges should be loose, never tight. Under the real format (20-hand levels, 250-hand cap) a bot with ranges 30 percent wider than the TAG default scored 18.5 points per table against the TAG's 14.0, and the nit scored 7.6 (10_RESEARCH_FINDINGS.md, 8c). The risk premium belongs on all-in calls, not on opens. Widen further as the blinds climb and as the table folds.

## 4. Postflop

Classify my hand after each board change into: air, weak draw, strong draw (8+ outs), weak pair (bottom or middle, or top pair with a bad kicker on a wet board), good pair (top pair good kicker or overpair), two pair or better, nuts-class (set, straight, flush, full house). Classify the board as dry or wet.

As the preflop aggressor against one or two opponents: continuation-bet about 60 percent of the pot on dry boards with any hand that has at least a weak pair or a strong draw, and with air on dry boards against opponents who fold to c-bets at 55 percent or more. Check air on wet boards or against stations. On the turn, continue with good pair or better and with strong draws; give up with air unless the opponent folded to the last two barrels.

Facing a bet: compute pot odds. Call with any hand whose equity estimate beats the price plus a margin that grows with ICM pressure (section 6) and shrinks against maniacs. Raise with two pair or better and with the nuts-class; raise strong draws only against opponents who fold to raises. Fold weak pairs to a second barrel from a non-maniac. Never bluff-raise a station.

Value betting: against stations bet bigger (75 percent to full pot) with good pair or better on all three streets. Against nits, bet smaller and give up faster.

River: bet good pair or better for value against anyone who calls too much; check behind marginal hands against aggressive opponents and call their bets with good pair when the price is right; fold weak pairs to large river bets from passive opponents (a passive bot that suddenly bets large has it).

Bet sizing: three sizes only (a third, two thirds, full pot) plus all-in, always clamped to legal bounds. Shove when the planned bet is more than 60 percent of the effective stack; do not leave a tiny stack behind.

Multiway (three or more live opponents): tighten everything one notch; do not bluff; value-bet only good pair or better and prefer check-call with top pair weak kicker.

## 5. Short-handed and heads-up

With 4 or fewer left, position buckets compress and ranges open up; most pots are preflop confrontations by then because the blinds are large. Heads-up, play chip EV (ICM is linear in chips when 2 players split 2 payouts). Heads-up push/fold at 10 bb or less: the button shoves roughly the top 55 to 60 percent; the defender calls with roughly the top 35 to 40 percent. Deeper than 15 bb heads-up: raise the top 70 percent from the button to 2 bb, call with the top 40 percent of the remaining hands, c-bet most dry boards.

## 6. ICM and the 200-hand cap

The cap is the normal ending. In simulated fields of disciplined bots, 75 to 93 percent of tables reached hand 200 with 2 to 4 survivors, and only tables with a maniac or a shove-bot resolved early (10_RESEARCH_FINDINGS.md, section 1). Most of the points at most tables are therefore handed out by the ICM split, which means the hand counter, the survivors' stack ranking and the payout table drive the last third of every table. Build this in v2.

The kit ships an ICM calculator. Use it, but not on every decision; eight-player Malmuth-Harville in pure Python can exceed a millisecond. Pattern:

- At the first decision of each hand, compute the current ICM value of my stack and cache it.
- For the two or three all-in-sized decisions per hand (call a shove, shove, call a big bet), compute ICM for the win and lose outcomes (two more calls), and decide by ICM EV versus the fold value. Guard this with a time check; if the clock is past 0.5 ms, fall back to the chip-EV decision with a risk premium.
- Risk premium fallback: required equity = pot_odds_equity x (1 + lambda), where lambda is 0 heads-up, about 0.1 to 0.15 when the payout table is top-heavy, about 0.2 to 0.35 when it is flat or when exactly one more bust-out puts everyone into the points, and higher for a stack that is already comfortably in the points at a table with a shorter stack about to be blinded out. The bot reads lambda from a small table indexed by (players left, places paid, my stack rank).

Ladder logic: when a stack shorter than mine is about to be blinded out (its stack is under 3 big blinds), avoid any confrontation that could bust me in the meantime; two or three folds buy a guaranteed place. Conversely, when I am that short stack, shove first rather than being blinded out, because folding into zero points is never right.

The cap: track the hand number (from the kit if provided, else count new-hand hooks). In the last 20 hands, a stack in a paid position by chip count should decline marginal all-ins (its ICM share at the cap is nearly locked); a stack out of the paid places by chip count should take aggressive, high-fold-equity spots because its ICM at the cap is small. Nobody should "wait for the cap" by folding everything: the blinds at level 8 destroy a passive stack in two orbits.

## 7. Opponent modeling within a table

State per opponent seat, kept as small integer counters in the memory blob and updated from `state.events` on every turn (the feed covers everything since our last turn, including hands we were not in): hands observed, voluntary-put-in-pot count, preflop raise count, three-bet count, folds to preflop raise when given the chance, c-bet fold count, bets and raises versus calls postflop (aggression), preflop all-in count, whether the seat has ever put chips in voluntarily, and showdown observations (every showdown reveals all hole cards, so count how often a seat showed air after betting the river, and how strong its preflop raising hands were).

Every rate is smoothed toward a population prior with a weight of about 10 hands, so the first few observations move the estimate but do not dominate it. Labels and the behaviour change they trigger:

| Label | Trigger (after smoothing) | Our adjustment |
|---|---|---|
| FOLDBOT | no voluntary chips ever in 12 or more hands and folds to every raise, or folds when a check was free | Raise any two when it is in the blinds and everyone else folded; bet every street into it; never bluff-catch, it never bets |
| SHOVER | preflop all-in on 60 percent or more of its hands over 4 or more hands | Never open-raise while it is still to act. Fold, or shove first with 77+, AJs+, AK (equity 65 percent or more against a random hand); call its shove with the same set; QQ+ when two shovers are in. Widen when the shover is short (its all-in is cheap) or when we are short. Measured worth: 3 to 5 points per table over a non-adapting bot at the same table |
| MANIAC | raises 50 percent or more of hands preflop or bets two thirds of postflop opportunities | Widen value ranges: 3-bet and call with the top 15 to 20 percent; call down with good pair; do not bluff it |
| STATION | calls 70 percent or more of bets postflop and rarely raises | Value bet thinner and bigger; never bluff; fold to its rare raises without two pair or better |
| NIT | VPIP under 12 percent after 20 or more hands | Steal its blinds every orbit; fold to its 3-bets without QQ+/AK; c-bet it with air on dry boards |
| TAG/LAG | the normal middle | Default strategy |
| UNKNOWN | fewer than about 8 hands | Default strategy with the prior |

Two field-wide stats also matter: how often the table folds to a steal from CO/BTN/SB, and how often the table 3-bets. A table that folds 80 percent of the time to steals gets stolen from with 50 percent of hands.

Folded hands stay hidden, but every showdown is fully revealed. That is enough for a bluff-frequency estimate per seat (river bets that showed worse than a pair) and for a preflop raising-range estimate (the percentile of the hands a seat showed after raising preflop). Both need only a few bytes per seat in the blob.

## 8. Randomization

Few bots will adapt to us within 200 hands, so determinism costs little and helps debugging. Keep two mixed decisions only: c-bet bluff frequency on dry boards (about 60 percent) and the choice to 3-bet versus call with the bottom of the value range (about 30 percent 3-bet). Use the per-table seeded generator.

## 9. Things not to do

- No live Monte Carlo on the main path. The bounded eval7 refinement of section 2 only behind a time check, only with a full bank, only for all-in decisions, and only if measured on the build box first.
- No per-call NumPy, no Numba, no model inference unless a measured p99 says it fits. Import-time use of NumPy for building tables is fine.
- No stdout, no stdin, no files after import, no threads, nothing in /tmp between tables.
- No reliance on opponent names (anonymized inside a table) or on anything from a previous table. The named hand histories are for analysis between rounds, not for lookups inside the bot.
- No "all-in every hand" as the main strategy. Against callers who use pot odds it bleeds chips, and under ICM luck correction it gets exactly its negative EV with no variance to hide behind. It is a fine thing to build as a sparring partner, not as a submission.
- No fancy bluffs multiway. No slow-playing. No limping.

## 10. Second-order ideas for T4 to T6 (only with evidence from the hand logs)

- Table naivety index. Track how often our raises and shoves get through without a call across the table, and how often anyone's all-in gets called. A table that has not called a shove in 20 hands and folds to 90 percent of late-position raises is a table to steal from with 40 to 50 percent of hands from the cutoff, button and small blind, shoving when under 20 big blinds. Downgrade instantly when someone calls light or re-shoves. The simulations show the upside is large against a naive table (the shove-bot's 34 points) and the downside is one stack; graded widening keeps the downside bounded.
- Bet-size tells. Many first-draft bots size bets by hand strength (bigger with better). If the kit shows showdown cards, record each opponent's bet-size-to-pot ratio at showdown and the strength shown; after 6 to 8 observations with a clear pattern, fold medium hands to its big bets and call its small bets lighter.
- Pressure creates error opportunities. Every decision an opponent faces is a chance for its bug or timeout to fire and turn into a fold. Small raises and probing bets against suspected fragile bots are cheap ways to create those decisions. Do not do this against solid bots; it just builds pots.
- Fold-equity bookkeeping per opponent. Steal success rate per seat, 3-bet frequency per seat. Steal more from seats that fold, stop stealing from seats that 3-bet, and re-shove the top 10 percent against serial 3-bettors when 12 to 25 big blinds deep.
- The spectator "say" field. If the kit lets a bot attach a short message to an action, it is for the replay screens and has no effect on the score. One static string, never computed.
- ICM luck correction, if on. Scored outcomes of all-ins are replaced by their equity-weighted expectation. Nothing in the decision rules changes; what changes is that the leaderboard will reflect decision quality faster, so small edges in all-in thresholds show up even in a single tournament.

## 11. The iteration plan across T1 to T6

Practice runs of about 1,000 tables happen every 10 minutes during the build hour and do not count. The first upload is in them from minute 15 to 20, and their results and hand histories show the real field before T1. Read them at minute 30 and minute 45 and set the exploit switches (13_EXPLOIT_THE_AI_FIELD.md) from what is actually there.

- v1 (minute 15 to 20): sections 1, 2 (preflop table only), a normal position chart, pot-odds postflop with a rank-count evaluator, the no-raise-fold rule. Submit.
- v2 (minute 40 to 50): full evaluator, postflop classes, stack regimes, push/fold, the lambda table, the hand counter and cap logic, and the SHOVER detector with its response (shove-bots will be in T1 and the response is the most valuable exploit measured). Submit if it beats v1 in a paired local evaluation with the confidence interval excluding zero.
- v3 (between T1 and T3): the remaining opponent labels and exploits, tuned from what the T1 hand logs and health page show about the field (how many fold-bots, stations, nits).
- v4 (between T3 and T5): ICM calculator integration for all-in decisions (or the solved push/fold ranges from the P2 loop), heads-up polish, steal-widening against tables that fold too much.
- v5 (for T6): only fixes with evidence. Freeze by 8:40 PM and verify the active submission on the team page.
