# 18. The exposure game, bluffing with cards, and what the mystery prizes do to the field

Confirmed sequence: flop dealt, then everyone simultaneously picks discard / reveal / hide, then flop betting with every exposed card visible. Mystery prizes announced: Empty Bluffer (most pots won without showdown while exposing a 2 through 5), the Shover (most all-ins), Calling Station (highest call percentage).

## 1. What the prizes do to the room

The Shover prize buys all-in bots. The Calling Station prize buys bots that call everything. Both are the archetypes our switches are built to farm (04, 13, 14). Teams that have given up on the top five by T4 will switch to prize chasing, so expect more shovers and stations in T5 and T6, not fewer. Keep the SHOVER and STATION switches strong all night, and expect tables with two or three shovers: QQ+ against two all-ins, wait for the collisions, never try to out-shove.

Empty Bluffer rewards winning without showdown with a low card exposed. That is close to good poker (aggression that gets folds) with one cost: keeping a 2 to 5 as one of the two cards. We take it only when it is free (section 4). We never shove or call for a prize. The regional is decided by points; the prizes decide who gives us theirs.

## 2. The exposure game: what our exposed card does to each kind of opponent

Three kinds of opponent, by what they do with exposed cards:

- Non-reactive: ignores exposed cards entirely. Most first-draft bots. Against them exposure does not matter for their decisions; expose the blank and keep the strength hidden so nothing is given away to the few who do read.
- Naive reader: treats an exposed card at face value. Exposed ace or board-pairing card means strong; exposed low blank means weak. Against them: when bluffing, expose the scare card; when value betting, expose the blank so they call.
- Rule-assuming reader: assumes we expose by a rule, usually the one its own code uses, which in generic code is "expose the lower card". Under that assumption our exposed card X implies our hidden card is at least X, so an exposed high card maximizes our perceived strength and an exposed low card says nothing. Same policy as against the naive reader: scare card out when we want folds, blank out when we want calls.

So one policy serves both reactive kinds: scare card exposed when we intend to bet without a hand, blank exposed when we intend to bet with one, mixed 30 percent the other way so our exposure never becomes a pure tell for a bot that correlates our exposure with our showdowns. Against non-reactive seats always the blank. Against unknown seats, the blank (v1).

Scare card means: an ace or king on a board without one; a card that pairs the board's top card; a card of the suit on a two-tone or monotone board; a card inside the straight window of a connected board.

## 3. Bluffing with cards

Exposure is truthful; the lie is what we hide. We can only represent what we actually hold a piece of.

- Flush representation: on a two-tone board, keep and expose our card of that suit when the other kept card is the real strength or when we have nothing and want to barrel; bet the flop; if the third suit card arrives, bet big on the turn. Against reactive seats this folds out one-pair hands; against auto-c-bet TAGs that give up on the turn it works regardless of exposure.
- Overcard representation: hold an ace with a blank on a king-high board; expose the ace; bet. The hidden card could be anything, which is the point.
- Board-pair representation: on a paired board, if we hold a card of that rank and a weak one, exposing the pair card announces trips; bet for folds against readers, check for value against stations (they call anyway, and the ace is better kept hidden there).
- Value disguise: with two pair or a set where one card is a blank, expose the blank. With a strong hand where both kept cards connect (two pair with both ranks on board), expose the lower one.
- Never: expose the scare card and check. That wastes the representation and teaches a tracker that our scare exposure means weakness.

Semi-bluffs beat pure bluffs here as everywhere: expose the draw card, bet with real outs, and win either way often enough.

## 4. Empty Bluffer for free

Only when it costs nothing:

- When the two best keeps are equal in equity and one of them includes a 2 through 5, keep that one.
- When both kept cards are blanks and one is a 2 through 5, expose the low one.
- Our aggression is unchanged: c-bets, steals and value bets happen for points. The low exposed card rides along.

Never keep a 2 through 5 over a better card for the prize. Never bet without equity for the prize. If by T4 the leaderboard says we are out of the top five with no realistic path back, a prize mode flag may be turned on between rounds: it widens the "keep the low card" tie-break and raises the bluff frequency against non-reactive folders. It is a flag in the constants dictionary, off by default, decided by the two of you on evidence, never by the bot.

## 5. Learning every opponent's reveal rule fast

From 17 section 5, with two additions:

- The practice runs during the build hour give showdowns by named opponent before T1. Tabulate (exposed rank, hidden rank, does exposed pair the board, does hidden pair the board) per name and classify each as EXPOSE_LOW, EXPOSE_HIGH, EXPOSE_KICKER, EXPOSE_PAIR, EXPOSE_FIRST or EXPOSE_RANDOM. The share of each rule in the field becomes the prior for the in-table fingerprint, which then needs two consistent observations instead of three.
- A seat whose exposure carries a rule is almost always non-reactive too (the same first draft that exposes by rule does not read exposures). A seat whose exposure looks random is more likely to be a bot that thought about it, and more likely REACTIVE. Use that as the prior for REACTIVE until the conditional fold-to-bet test (17 section 5) has its six observations.

## 6. Second-order: they know others use AI

Three levels will be in the room and our tracker separates them within 20 hands, so we do not have to guess which one dominates:

- Level 0 builds the generic bot (13 section 1). Our exploits are for them.
- Level 1 reasons "everyone will be a generic nit" and builds a maniac, or reasons "everyone will be a maniac" and builds a nit that calls down. Both are archetypes with switches (MANIAC, NIT, STATION).
- Level 2 builds what we built: a tracker with switches. Against them, 14 section 6 and 15 item D: stay under their triggers, detect their adaptation, exploit the adaptation, and keep our exposure unreadable so the one new information channel in this variant gives them nothing about us while giving us everything about the level 0 bots.

What makes us different in ways that score: a correct discard every flop (three evaluations, not a heuristic), seven dead cards subtracted from our outs, opponents' exposed cards as strength floors, fingerprinted exposure rules turned into range bounds, mixed exposure of our own, ICM-correct jams in a 13-level structure, and switches that fire on evidence instead of assumptions. None of that is a first draft.

## 7. Paste to Codex (adds to 17 section 7)

```
Additions for the exposure game and the mystery prizes:
1. Exposure policy: against seats not labelled REACTIVE, always expose the kept card that connects least with the board (blank). Against REACTIVE seats: if we intend to bet without a made hand or strong draw, expose the scare card (ace or king on a board without one, a card pairing the board's top card, the two-tone suit card, a straight-window card) with probability 0.7, else the blank; if we intend to value bet, expose the blank with probability 0.7, else the scare card. Decide the intent from the same pipeline that will make the flop decision, before the phase action is returned. Never expose a scare card and then check.
2. Free Empty Bluffer: equal-equity keep ties go to the keep containing a 2 to 5; blank-vs-blank exposure ties go to the 2 to 5. No other change. A constants flag PRIZE_MODE (default off) widens that tie-break and raises bluff frequency against non-reactive folders; do not implement its effects until told.
3. Fingerprint priors: read exposure rules by named opponent from the practice-run hand histories and set the rule priors; a seat with a rule is prior non-reactive, a seat without a rule is prior REACTIVE.
4. Expect multiple shovers and stations per table because of the Shover and Calling Station prizes: two all-ins require QQ+, three require KK+; never bluff a STATION; value bet it with top pair good kicker or better on three streets.
5. Harness: add a prize-chasing shover (all-in 100 percent), a prize-chasing station (calls 100 percent, never raises), and a naive-reader bot (folds to bets when our exposed card is a scare card, calls otherwise) to the archetype zoo, and confirm each switch gains against its target.
```
