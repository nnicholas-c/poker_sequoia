# 17. The variant: three hole cards, then discard one, expose one, keep one hidden

Announced 6:00 PM. Hold'em with three hole cards. After the flop, everyone simultaneously ("secretly") discards one card and exposes one (it stays in the hand, face up); the third stays hidden. Every decision still within 1 ms or the bot folds (or checks when free, or takes the automatic choice in the new phase).

## 1. Confirm in RULES.md and sdk/ in the first five minutes

1. Order of play: is the discard/expose phase before or after the flop betting round? (Both are plausible. It changes whether flop bets are made with three cards or two.)
2. How the action is built: one action carrying three roles (discard, reveal, hide), or separate kinds? What `state.legal_actions` offers in that phase, what `min_amount` means there, and what the automatic choice `Action(first.kind, first.min_amount)` actually does (it may discard our best card). The phase handler is therefore part of v1, not v2.
3. Showdown: best five of seven using both remaining hole cards in any combination? Is the discarded card ever revealed? (Assume not: "secretly".)
4. Events: which event kinds carry the exposed cards (and whether `state.table.seats[].shown_cards` holds them during the hand). The feed must record every seat's exposed card for the current hand.
5. Does the upload test (20 hands heads-up vs check-or-fold) exercise the phase? Assume yes; a wrong or slow phase decision fails more than 10 percent of decisions.

## 2. What changes in the game

- Hands are stronger at showdown than in hold'em. Each player picks the best two of three after seeing the flop, so two pair, trips, flushes and straights are more common, and one pair with a weak kicker is a weak hand. Move every postflop value threshold up one notch: value bet two pair or better on three streets, top pair good kicker on one or two, and treat top pair weak kicker as a bluff-catcher.
- Preflop, flexibility is worth a lot. Three coordinated cards (suited and connected, for example J-T-9 with two of a suit, or A-K-Q with two suited) are premium. A high pair with a suited or connected third card is premium. A lone pair with two unrelated low cards is weaker than in hold'em. Three unrelated offsuit cards fold. More cards are dealt (24 of 52 at a full table), so draws are blocked more often; discount flush and straight draws slightly multiway.
- Information. After the flop, every opponent shows one card. That card is a known dead card for our outs, it may pair the board, and it tells us something about what the opponent kept. How much it tells depends on the opponent's exposure rule, and that rule is the biggest exploit in this variant (section 5).

## 3. Our discard and expose policy (v1, then v2)

Discard (which two to keep): for each of the three two-card keeps, compute the made-hand class on the flop with eval7 plus draw flags (flush draw, open-ended, gutshot, overcards) and look up the postflop equity table for the live opponent count; keep the pair with the highest equity. Tie-breaks: keep a made pair over a draw of equal estimated equity; keep the higher kicker; keep two suited cards on a two-tone board. Cost: three evaluations, well under 0.1 ms.

Expose (which kept card is public), v1: expose the card that connects least with the board, meaning it does not pair the board, does not share the suit of a two-tone or monotone board, and is not part of a straight draw; ties broken by the hand-seeded generator so our rule is not fixed. Hide the card that carries the strength. If both cards carry strength (two pair, set), expose the lower one.

Expose, v2 (bluff exposure, only against seats that react to exposed cards; section 5 says how to detect that): when we intend to bet as a bluff or semi-bluff, expose the scare card (the ace on an ace-high board, the suited card on a two-tone board, the straight card) and hide the blank; when we intend to value bet, expose the blank. Mix: expose the scare card with a strong hand about 30 percent of the time so the exposure is not a pure tell.

Never let exposure leak a fixed rule: never "always the higher", never "always the lower", never "always the board-pairing card". Section 5 is exactly how we punish bots that do.

## 4. Using everyone's exposed cards

- Dead cards: subtract exposed cards from our outs (a flush draw with two of its suit exposed around the table has seven outs, not nine). Up to seven known cards; the generator's postflop table assumed none, so apply the correction to the outs count before the table lookup.
- Opponent strength floor: an exposed card that pairs the board means at least a pair; an exposed overcard to the board means at least overcard equity; an exposed card of the two-tone suit raises the flush-draw probability; an exposed straight card raises the straight-draw probability. Implement as additive adjustments to the opponent's equity estimate (pairs the top card: +0.20; pairs a lower card: +0.12; suited with a two-tone board: +0.08; connected to the board: +0.05), capped so a single exposed card never moves our calling threshold by more than 0.25.
- Range narrowing with a known rule (section 5): if a seat's rule is "expose the lower card", its hidden card is at least the exposed rank, which turns an exposed king into "king or ace hidden" and a strong range; if its rule is "expose the higher card", its hidden card is at most the exposed rank, which turns an exposed seven into "at most a pair of sevens unless the board paired low", a bluffing target.
- Bluff targets: against a reactive opponent with an exposed card that missed the board, bet two thirds of the pot when our own exposed card is a scare card; against an opponent whose exposed card pairs the board, do not bluff.

## 5. The exploit specific to this variant: fingerprint every seat's exposure rule

Every showdown reveals the hidden card, and the exposed card was already public, so every showdown gives one labelled observation per seat: (exposed card, hidden card, board). After three observations a generic bot's rule is usually visible, because generic bots use a rule:

- EXPOSE_LOW: hidden rank ≥ exposed rank in all observations. Hidden card is at least the exposed rank.
- EXPOSE_HIGH: hidden ≤ exposed in all observations. Hidden card is at most the exposed rank.
- EXPOSE_KICKER: the exposed card never pairs the board while the hidden one does whenever they have a pair. Their exposed card is their kicker; an exposed card that pairs the board then means two pair or trips.
- EXPOSE_PAIR: the exposed card is the one that pairs the board. An exposed blank then means no pair.
- EXPOSE_FIRST: the exposed card is whatever position in their hand the code picked (often the first or last card as dealt). Shows up as no relation to strength: treat as random.
- EXPOSE_RANDOM: no rule found after five observations.

Counters: EXPOSE_LOW or EXPOSE_KICKER with a high exposed card: respect it; with a low exposed card and a high board: bluff it. EXPOSE_HIGH with a low exposed card: value bet thin, bluff when the board is high. EXPOSE_PAIR with an exposed blank: bet. Apply these as equity adjustments to that seat with confidence from the number of observations (weight 3 instead of 10, because the rule is deterministic in generic code and three consistent observations are strong evidence).

Detect reactive opponents (whether they use our exposed card at all): compare a seat's fold-to-bet rate when our exposed card pairs the board or is an overcard against when it is a blank. A difference above 0.25 after six observations marks it REACTIVE, and the bluff-exposure policy in section 3 v2 turns on against it. A non-reactive seat ignores exposure, so against it we always expose the blank and never spend thought on scare cards.

Also fingerprint discards indirectly: a seat that exposes a low unconnected card while betting strongly kept a strong hidden card and discarded something; a seat whose exposed card is often the only possible kicker to a board pair discards high cards (bad logic) and can be value-bet thin.

Between rounds, the hand histories give the same observations across the whole field by named opponent: count the share of each rule in the field and set the fingerprint priors from it.

## 6. Changes to the modules in 14

- `safety`: the phase handler is in v1. If the discard decision cannot be computed for any reason, fall back to: keep the two highest-ranked cards that include any pair, expose the lower of them, never the automatic choice.
- `record`: per seat add exposure observations (three slots of exposed rank, hidden rank, board-pair flags) and the REACTIVE counters; per hand add the eight exposed cards.
- `feed`: new event kinds for discard/expose; record the exposed card per seat; at showdown pair the exposed and hidden cards into the observations.
- `tables` (P2 generator): a three-card preflop table. Either the full table over three-card classes (ranks plus suit pattern) with an optimal-keep simulation, or, if time is short, a scored formula: the best two-card combination's equity from the 169 table plus bonuses (two suited: +0.015; all three suited: +0.03; three cards within a four-rank span: +0.02; a pair with a suited or connected third card: +0.02; three unrelated cards below ten: -0.03). Postflop table unchanged in shape, generated with three-card deals and best-two keeps so the opponents' strength distribution matches the variant.
- `strength`: the keep decision is the strength computation; cache it per hand after the phase.
- `baseline`: value thresholds one notch higher postflop; preflop opens expressed as percentiles of the regenerated three-card ordering, same widths as before.
- `labels`/`exploits`: the exposure labels and counters above, plus REACTIVE.
- `harness`: archetype bots must implement the phase too: a keep-two-highest-expose-lower bot, an expose-higher bot, an expose-first bot, a random-expose bot, plus the usual zoo. The eight-copies test checks our exposure carries no simple rule (a copy's fingerprint of us must come out EXPOSE_RANDOM).

## 7. Paste to Codex now (replaces P5)

```
The variant: hold'em with three hole cards; after the flop every player simultaneously discards one card, exposes one (kept, face up) and keeps one hidden. Read RULES.md and sdk/ and answer first: (1) is the discard/expose phase before or after flop betting; (2) exactly how the phase action is constructed from state.legal_actions and what the automatic choice would do; (3) showdown rules for the two remaining hole cards; (4) which event kinds and state fields carry each seat's exposed card; (5) whether the upload test exercises the phase. Then implement, in this order, against 14_ADAPTIVE_BOT_BUILD_PLAN.md and 17_VARIANT_THREE_CARD_EXPOSE.md:
a. Phase handler in v1: keep the two cards with the highest flop equity (eval7 made hand plus draw flags, postflop table lookup for the live opponent count), expose the card that connects least with the board with random tie-breaks, hide the strength. Hard fallback: keep the two highest cards including any pair, expose the lower. Never return the automatic choice in this phase.
b. Feed: record every seat's exposed card per hand from the new events; at showdown store (exposed rank, hidden rank, board-pair flags) per seat, three slots.
c. Equity: subtract exposed cards from our outs; add the opponent-strength adjustments from 17 section 4; postflop value thresholds one notch up.
d. Generator (background on the box): three-card preflop ordering (full table if it finishes in 10 minutes, else the scored formula in 17 section 6) and the postflop table regenerated with three-card deals and best-two keeps.
e. Exposure fingerprints and the REACTIVE detector from 17 section 5, with the equity adjustments they drive; the bluff-exposure policy against REACTIVE seats only.
f. Harness archetypes that implement the phase with the rules in 17 section 6; the eight-copies test must fingerprint us as EXPOSE_RANDOM.
Gates as in 14 section 8. Upload v1 with (a) and (b) by minute 20 and select it active; it then plays the practice runs.
```

## 8. Why this variant favours us

Most teams will spend their hour on the mechanics of the phase and ship a fixed rule for the exposure, because the assistant's first draft will have one. Each fixed rule is a labelled leak that every showdown confirms. A bot that reads those leaks, keeps its own exposure unreadable, and corrects its outs for the seven cards it can see is playing a different game from the one its opponents think they are in.
