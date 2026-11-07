# 19. The ultimate version: why the regress ends, and what it ends in

"If we farm, they farm, and everyone knows everyone farms." True, and it does not go on forever. Here is where it stops and what that means for the bot.

## 1. Farming is never negative; being farmable is

A correct exploit of a shover or a station is positive against that seat whether or not six other seats also exploit it. Seven farmers share one station's chips, so each gets less, but none gets less than zero. The only bots that lose to a room full of farmers are the ones with a leak to farm. So the first property of the ultimate version is not a better exploit; it is having nothing to exploit. Every advantage we take must be one that cannot be reversed if the opponent turns out to be a level-2 bot.

## 2. The prey dies fast, and then the real game starts

Shovers, stations and fold-bots bust inside the first few blind levels at any table with two or more adapters. From hand 60 or so, most tables are adapters against adapters. That game is near-equilibrium poker under ICM with a 13-level structure, often ending heads-up at the cap. Nobody out-levels anybody there; the points go to whoever makes fewer mistakes in push/fold, blind defense, bet sizing balance, and the ICM arithmetic. The second property: the baseline is solved where the game is solvable. The P2 push/fold solve with ICM for 2 to 5 players, heads-up Nash at every stack depth, minimum defense frequencies in the big blind, two sizes per spot used with both value and bluffs. If the generator is not done by minute 35, finish it between T1 and T3; it is worth more than any switch after the prey is gone.

## 3. Evidence replaces guessing

We do not need to know which level the room is at. Each seat's actions are its level, and the counters read them within 20 hands. Level 0 shows fixed sizes, automatic c-bets, exposure by rule. Level 1 shows a maniac or a nit built in reaction to an imagined field. Level 2 shows adaptation: its behaviour toward us changes with our behaviour. Our bot carries one policy per observed behaviour, not one policy per guessed level. The third property: all exploitation is conditional on evidence, with magnitude scaled by confidence, and it reverts the moment the evidence turns.

## 4. Downside-aware evidence

Not every exploit needs the same evidence. The rule: required observations grow with the cost of being wrong.

- Cheap if wrong, take it early: steals against seats that fold (cost: one small raise), floats against auto-c-bets (cost: one call), thin value bets against callers (cost: one bet called by a better hand), exposing the blank by default (cost: nothing).
- Expensive if wrong, demand more: calling a jam on the SHOVER read (cost: a stack; require four all-ins seen and the 0.65 threshold), folding a strong one-pair hand to a SIZE_TELL read (cost: a pot; require three showdowns), bluff-jamming into a STACKOFF_RULE read (cost: a stack; require four folds seen and never on a hand where we have showdown value anyway).

With this rule a level-2 opponent that tries to bait a switch (for example, folding to our first three steals to invite a wider steal and then 3-bet jamming) can win at most a small pot before the adaptation detector flips it back. Nobody can bait us for a stack with fewer than four consistent observations, and four observations of a fake tendency cost them more than they win.

## 5. The edges that do not depend on the field at all

These are worth points against every level, and they are where the hour goes before any switch:

1. Zero timeouts, zero exceptions, zero illegal actions. One timeout empties the bank; a bank-less table is a fold-bot.
2. The correct discard on every flop: three evaluations against the flop, not a heuristic. Half the room will keep "the two highest cards".
3. Seven dead cards out of our outs. Almost nobody will do this, and it changes every draw decision.
4. Opponents' exposed cards as strength floors, and their exposure rules as range bounds after two or three showdowns.
5. Our own exposure unreadable: mixed, intent-driven against readers, blank against everyone else.
6. Loose opens under a structure where blinds climb for 13 levels; measured at 4.5 points per table over a standard TAG.
7. ICM-correct all-in decisions, with a moderate risk premium early and solved ranges late.
8. Heads-up chip EV at the cap, where most capped tables end.

## 6. What "different" means tonight

Different is not a trick nobody has thought of; the room is full of people who can think of tricks. Different is doing the eight things above correctly while the field spends its hour on the mechanics of the phase, and letting evidence choose the exploits. If a trick is needed, it is the one in 18: the exposure channel is the only new information in this variant, and a bot that reads it while giving nothing back is playing with an extra card every hand after the flop.

## 7. Paste to Codex

```
Design principles that override any individual switch:
1. Nothing we do may be reversible against us by a stronger opponent. Every exploit is conditional on observed behaviour, scaled by confidence, and reverts when the adaptation detector fires. Our aggregate frequencies stay inside generic tracker thresholds (14 section 6).
2. Required evidence scales with the downside: cheap exploits (steals, floats, thin value, blank exposure) fire on 3 to 5 observations; stack-sized exploits (calling or bluffing all-in on a read, folding strong one-pair to a size read) require 4 consistent observations and the thresholds in 14 and 17.
3. The baseline is solved where solvable: ICM push/fold ranges for 2 to 5 players and heads-up Nash at every depth from the P2 solve; big-blind defense at minimum defense frequency; two sizes per spot, both used with value and with bluffs.
4. Priority of work: the eight field-independent edges in 19 section 5 before any switch beyond SHOVER, STATION, NIT and FOLDBOT.
5. Between rounds, 16 decides changes from evidence; a round with no change is acceptable.
```
