# 14. Build plan for the adaptive bot (what Codex implements once the variant is announced)

This is the specification. It is written so that Codex can implement it module by module against the real kit without rediscovering the design. It assumes the interface in 12_KIT_INTERFACE.md, the strategy in 03, the archetypes and counters in 04 and 13, the numbers in 10, and the variant triage in 05. Where the variant changes something, section 9 says which modules absorb it.

The idea in one sentence: play a loose, position-aware, ICM-aware baseline that no tracker can label as anything but "solid", learn every seat's tendencies from the event feed inside the table, and turn on targeted exploits only where the evidence says so, with the size of each exploit scaled by how much evidence there is; and when a seat starts adapting to us, switch that seat back to the baseline and exploit its adaptation instead.

## 1. Modules and build order

| Order | Module | What it holds | Minute target |
|---|---|---|---|
| 1 | `safety` | The wrapper, `choose()`, the automatic choice for unknown phases, gc.disable, import-time warmup | 7 to 15 |
| 2 | `record` | The memory blob: struct layout, pack/unpack, checksum, fresh-record constructor | 7 to 15 |
| 3 | `feed` | Event parser: turns `state.events` since our last turn into per-seat counter updates and hand bookkeeping | 15 to 25 |
| 4 | `tables` | Import-time data: 52 eval7 cards, 169-class preflop table, postflop class table, push/fold ranges, risk table (from the P2 generator) | 20 to 35 (generator runs in the background on the box) |
| 5 | `strength` | Preflop class lookup; postflop made-hand class, draws, texture, equity estimate | 25 to 35 |
| 6 | `baseline` | The decision pipeline from 11_DECISION_CARD.md with loose ranges, stack regimes, push/fold, ICM lambda, cap logic | 25 to 45 |
| 7 | `labels` | Smoothed rates, labels, confidence weights, adaptation detector | 35 to 50 |
| 8 | `exploits` | The switch table: multipliers applied to baseline constants per seat and per table | 40 to 55, then between rounds |
| 9 | `harness` | Archetype bots, paired evaluation, no-bank latency check, pack and upload | from minute 10 in parallel |

v1 = modules 1, 2, 3 (counters only), a static preflop table and a rank-count postflop fallback, uploaded by minute 20. v2 = everything through module 6 plus the SHOVER switch, uploaded by minute 50. v3+ = labels and exploits tuned from the practice runs and the round hand histories.

## 2. `record`: the memory blob

Fixed layout, little-endian `struct`, one record per table. Version byte first so a later upload can read an older blob or discard it.

Header (16 bytes): version u8, flags u8, hand_number u16, my_seat u8, players_at_start u8, last_board_len u8, reserved u8, checksum u32, table_rng_seed u32.

Per seat, 8 slots of 44 bytes (seat index as given by the kit; unused slots zero):

- hands_dealt u16 (hands in which this seat had cards)
- vpip u16, pfr u16, limp u16, three_bet u16, fold_to_open_chance u16, fold_to_open u16, fold_to_3bet_chance u16, fold_to_3bet u16
- allin_pre u16, open_sizes_sum u16 (in tenths of a big blind, capped) and open_count u8 (to detect fixed sizing)
- cbet_chance u8, cbet u8, turn_barrel_chance u8, turn_barrel u8, fold_to_cbet_chance u8, fold_to_cbet u8
- post_bets_raises u16, post_calls u16, post_folds_to_bet u16
- showdowns u8, bluffs_shown u8 (river aggression shown with worse than one pair), big_bet_strong u8, big_bet_weak u8, small_bet_strong u8, small_bet_weak u8
- short_handed_folds_btn u8, short_handed_chance_btn u8
- adapt_window_recent u8 x 2 and adapt_window_early u8 x 2 (fold-to-our-steal and 3-bet-vs-us in two windows; section 6)
- last_label u8

Per-hand scratch (32 bytes): my cached strength class, cached equity (u16 in thousandths), cached lambda (u16), live-player count, street, aggressor seat, whether we open-raised this hand, whether we c-bet, number of raises this street.

Total under 400 bytes. `unpack` validates version, length and checksum and raises on mismatch; the wrapper catches it and starts a fresh record. `pack` recomputes the checksum. Every counter saturates at its type's max instead of wrapping.

## 3. `feed`: from events to counters

Process `state.events` in order. Maintain a small per-hand state machine inside the scratch area: current hand number (from `hand` events), street (from `board` events), who has raised this street, who was the first raiser preflop, who is the preflop aggressor, whether a flop bet by the aggressor has happened (c-bet), whether the flop was checked through.

Per event kind:

- `hand`: close the previous hand (resolve per-hand flags into counters: who had the chance to c-bet and did or not, who faced a c-bet and folded or not, who had the chance to fold to an open), then open the new one; hands_dealt += 1 for every seat with status active at the start.
- `ante`, `blind`: record who posted; not voluntary.
- `fold`: if preflop and facing a raise, fold_to_open += 1 (chance counted when the raise was made); if facing a 3-bet after opening, fold_to_3bet; postflop facing a bet, post_folds_to_bet; if the folder was in the big blind facing a late-position open, that is a fold to a steal.
- `check`: nothing, except it ends a c-bet chance without a c-bet for the aggressor.
- `call` (preflop, no prior raise): limp += 1 and vpip += 1. `call` facing a raise: vpip += 1 (preflop) or post_calls += 1 (postflop).
- `raise` preflop: vpip += 1, pfr += 1; first raise of the hand records the size in tenths of a big blind into open_sizes_sum / open_count; a raise over a raise is a 3-bet (three_bet += 1) and gives every earlier raiser a fold_to_3bet_chance; if the total equals the raiser's stack plus bet, allin_pre += 1. Every seat still to act after a raise gets a fold_to_open_chance.
- `raise` postflop: post_bets_raises += 1; if the raiser is the preflop aggressor and this is the first flop action by them, cbet += 1 (chance was counted at flop deal); on the turn, turn_barrel likewise. Record size relative to the pot at that moment (the pot is reconstructable from blinds, calls and raises in the feed; keep a running pot in scratch).
- `board`: street += 1; at the flop, give the preflop aggressor a cbet_chance and every other live seat a fold_to_cbet_chance when the aggressor bets.
- `show`: for each shown seat, evaluate the shown hand on the full board with eval7 and pair it with the largest bet that seat made on the river (from scratch): big (over 0.7 pot) and strong (two pair or better) → big_bet_strong, big and weak (one pair or worse) → big_bet_weak, likewise small. If the seat bet the river and shows worse than one pair, bluffs_shown += 1. showdowns += 1.
- `win`, `stack`: bookkeeping only (stack at hand end feeds the bust detector; the kit's seats list already carries stacks).
- Unknown kinds: ignore.

Everything the feed needs that the kit also provides directly (stacks, statuses, button) is read from `state` rather than reconstructed.

## 4. `labels`: rates, confidence and labels

Every rate is smoothed: rate = (count + prior_rate x W) / (chances + W) with W = 10. Confidence c = chances / (chances + W), between 0 and 1; it scales every exploit (section 5), so a seat seen for 5 hands gets a third of the adjustment a seat seen for 40 hands gets.

Priors (population guesses for an AI-written field; replace from the practice runs at minute 30): VPIP 0.20, PFR 0.14, limp 0.03, fold-to-open 0.75, fold-to-3bet 0.70, c-bet 0.70, turn barrel 0.40, fold-to-cbet 0.55, postflop aggression share 0.35, all-in preflop 0.02.

Labels, evaluated every hand from smoothed rates, with the minimum chances in brackets; a seat can carry more than one tag:

- SHOVER: allin_pre rate ≥ 0.60 [4 hands].
- FOLDBOT: vpip = 0 with hands_dealt ≥ 12 and fold_to_open = fold_to_open_chance ≥ 6; or any fold when a check was free. Hard flag, not a rate.
- NIT: vpip ≤ 0.15 [20 hands] or fold-to-steal ≥ 0.75 [5 chances].
- LIMPER: limp rate ≥ 0.10 [15 hands].
- MANIAC: pfr ≥ 0.40 [10 hands].
- STATION: post_calls / (post_calls + post_folds_to_bet) ≥ 0.65 [8 chances] and post_bets_raises small relative to calls.
- AUTO_CBET: cbet ≥ 0.80 [4 chances] and turn_barrel ≤ 0.40 [3 chances].
- SIZE_TELL: showdowns ≥ 3 and big_bet_weak = 0 and big_bet_strong ≥ 2.
- NO_BLUFF: showdowns ≥ 3 and bluffs_shown = 0.
- STACKOFF_RULE: fold_to_3bet ≥ 0.85 [4 chances] and no observed call of an all-in.
- FIXED_SIZE: open_count ≥ 5 and all opens within 0.2 bb of the mean.
- SHORT_PASSIVE: with 3 or fewer live, short_handed_folds_btn / chance ≥ 0.60 [4 chances].
- ADAPTIVE: section 6.
- TAG: none of the above after 20 hands.
- UNKNOWN: fewer than 8 hands.

Table-level: fold_to_steal_table (blinds folding to late opens), threebet_table, cap_distance = hand_cap - hand_number, live count, places paid (from the number of nonzero payouts), my stack rank.

## 5. `exploits`: the switch table

Each switch produces multipliers or offsets on the baseline constants. Applied value = base x (1 + c x (m - 1)) for multipliers and base + c x delta for offsets, where c is the seat's confidence. Switches are cumulative but capped: total steal width never above 0.60 of hands, total bluff frequency never above 0.35 on any street, calling thresholds never below pot odds.

| Label on a seat | Where it applies | Adjustment at full confidence |
|---|---|---|
| NIT or FOLDBOT in the blinds | Our open from CO, BTN, SB when the action folds to us | Steal width x 1.8 (cap 0.60); size 2.0 bb instead of 2.3 |
| NIT opened | Our 3-bet range | Value 3-bet top 6 percent plus bluff 3-bets with suited aces and suited connectors (about 5 percent) when its fold-to-3bet ≥ 0.65; fold to its 4-bet without QQ+/AK |
| FOLDBOT in a pot with us | Postflop | Bet 60 percent on every street with any two; never call its bet (downgrade the label if it ever bets) |
| SHOVER still to act | Preflop | No open-raises; fold, or raise_to max with equity ≥ 0.65 vs random (0.60 when the SHOVER has under 10 bb) |
| SHOVER has jammed | Preflop call | Call with equity ≥ 0.65 vs random; two jams: QQ+ |
| MANIAC | Preflop and postflop | Value 3-bet top 15 percent, call its opens with top 25 percent in position; call down with good pair; bluff frequency 0 against it |
| STATION | Postflop | Value bet good pair or better on all streets, sizes 0.75 to 1.0 pot; bluff frequency 0; fold to its raises without two pair+ |
| LIMPER limped | Preflop | Isolate to 4 bb plus 1 per limper with top 35 percent from CO/BTN/SB; c-bet 70 percent |
| AUTO_CBET is the aggressor | Flop and turn vs its c-bet | Float in position with any pair, draw or two overcards; bet 0.66 pot when it checks the turn; from the blinds check-raise dry flops with the top of our range and once per 10 hands with air |
| SIZE_TELL or NO_BLUFF | Facing its bets | Fold one pair to its bets ≥ 0.7 pot on turn and river; fold all but two pair+ to its raises; call its bets < 0.4 pot with any pair |
| STACKOFF_RULE opened | Preflop, 12 to 25 bb effective | Re-jam with top 25 percent (top 35 percent when it covers us by less than 2x); on the bubble as the covering stack, jam top 40 percent over its opens |
| SHORT_PASSIVE, 3 or fewer left | Button and small blind | Raise or jam 80 percent of buttons; attack its blind every orbit |
| Timeout tell (fold to a min-bet with a strong price, or checks on boards it used to bet) | Multiway pots and flops | Min-bet and min-raise it; never give a free card when a small bet forces a decision |
| Table fold_to_steal_table ≥ 0.70 [8 chances] | CO, BTN, SB opens | Steal width x 1.5 regardless of seat labels |
| Table threebet_table ≥ 0.12 | Our opens | Open 10 percent tighter from early seats; 4-bet jam top 5 percent instead of calling 3-bets |

Baseline constants these multiply (loose by design, from 10 section 8c): open widths EP 0.15, MP 0.20, CO 0.32, BTN 0.48, SB 0.42; BB defense vs min-raise 0.45, vs 2.5x 0.32; 3-bet value 0.05; c-bet 0.60 dry / 0.35 wet; risk lambda table by (players left, places paid, stack rank) with 0.5 as the typical value and 0 heads-up; push/fold from the P2 solve.

## 6. Countering the teams who asked the same question (the adaptive opponents)

Three layers.

1. Do not trip their switches. Our aggregate stats stay inside the generic tracker's thresholds while our conditional play is exploitative: preflop raise rate under 0.30 at a full table (the loose baseline sits at about 0.26 before steal multipliers; the multipliers only fire against seats that fold, so the raise rate rises only where it is not punished), big-blind defense at least 0.40, c-bet 0.60 not 1.0, postflop aggression factor under 2.5, two bet sizes per situation from the hand-seeded generator, one shown bluff per table (a cheap river bet with air against a NO_BLUFF seat that folds, once; or a shown semi-bluff that got called). Short-handed we exceed these on purpose.

2. Detect adaptation. For each seat keep two windows of its behaviour toward us specifically: the first 15 hands we interacted and the most recent 15. Two rates: fold-to-our-steal and 3-bet-or-raise-vs-our-opens. If the recent rate moved against us by more than 0.30 (it stopped folding, or started re-raising) with at least 5 chances in each window, tag it ADAPTIVE. Also tag ADAPTIVE any seat whose VPIP against us differs from its VPIP against the table by more than 0.20.

3. Exploit the adaptation. Against an ADAPTIVE seat, turn its switches off (back to baseline) and add two counters: if it now 3-bets our steals light, 4-bet jam with the top 8 percent and call its 3-bets in position with the next 8 percent instead of folding; if it now calls our c-bets, c-bet only with equity and check-raise its stabs with two pair or better. Keep ADAPTIVE for the rest of the table; a bot that adapts once will adapt again.

What a copy of our own bot does to us: it steals when we fold too much (we do not), floats automatic c-bets (ours are not automatic), folds to our big bets if our sizes leak (two sizes per spot, both used with value and with bluffs). Eight copies at a table must look like eight TAGs to each other; the harness checks that no copy labels another as anything but TAG or UNKNOWN after 50 hands (section 8).

## 7. The late game under the real format

Blinds rise every 20 hands to level 13 at the 250-hand cap. The simulations under a growing schedule show most capped tables ending heads-up and the loose opener scoring 18.5 points per table against 14.0 for a standard TAG. So:

- Stack regimes by effective big blinds decide everything from about hand 100 onward: over 25 bb normal play, 12 to 25 bb raise-or-jam, 12 bb or under push/fold from the solved ranges, 5 bb or under any two from the button and small blind.
- Three or fewer left: button raise or jam rate 70 to 80 percent against anyone not labelled MANIAC; attack SHORT_PASSIVE every orbit.
- Heads-up: chip EV (lambda 0); the countback tiebreak rewards first places, so at equal totals we want wins, and the solved heads-up push/fold ranges from P2 are the policy.
- Bubble (4 left, 3 paid): as the covering stack, jam into STACKOFF_RULE and ICM-tight seats; as a short stack, jam first rather than call; as a medium stack facing a bigger jammer, fold everything but the top 8 percent.
- Cap logic: with 20 hands or fewer to the cap, a stack in a paid position by chip count declines marginal all-ins (lambda x 1.5); a stack outside the paid places takes high-fold-equity jams; nobody folds into zero. Read hand_cap and hand_number from the state; never assume 250.

## 8. `harness`: tests and acceptance

Archetype bots to write for local play (each a tiny agent folder): shove-bot; fold-bot that returns an out-of-range raise every turn (so the server's fallback plays); station; maniac; random; nit; limper (limps 30 percent, folds to raises); auto-cbet TAG with a fixed 0.66 pot size and no turn barrel; size-tell TAG (bets 0.4 pot with one pair, 0.9 pot with two pair+, never bluffs); stack-off-rule TAG (folds to any bet over 40 percent of stack without QQ+/AK); our own bot x 8.

Acceptance before each upload:

- Zero failed decisions over 300 eight-seat tables and the heads-up check_or_fold game in no-bank mode; p99.9 under 0.3 ms; import under 2 seconds; memory record under 2 KB; `poker-agent check` passes on the packed zip.
- Paired against the previous upload, same seats and seeds, 1,000 tables: mean difference positive with the 95 percent interval excluding zero against (a) the kit's examples lineup and (b) the archetype zoo; not negative beyond the interval against (c) eight copies of ourselves.
- Each switch, tested alone against its target archetype among seven TAG-style bots: positive difference with interval excluding zero; against seven copies of ourselves: no label other than TAG or UNKNOWN assigned to any copy after 50 hands, and no switch firing on a copy.
- Latency under load: two evaluations running in parallel on the box while the harness times act.

Between rounds, the same gates apply, plus: priors in section 4 re-estimated from the round's hand history (archetype mix by named opponent), and the switch thresholds loosened or tightened to match.

## 9. Where the variant lands

- Hand rankings, deck, hole-card count, boards: `strength` and `tables` (regenerate with the P2 generator against the kit's engine). The baseline ranges are expressed as percentiles of the regenerated ordering, so they survive a ranking change; re-tune the multipliers only if the practice runs say so.
- New phases or action kinds (discard, bid, pick, exchange): `safety` handles the automatic choice on day one; a variant handler module implements the decision from 05_VARIANT_PLAYBOOK.md (F7, F10, F12) and `feed` learns the new event kinds (ignore unknown kinds until then).
- Betting structure (pot-limit, caps): `choose()` already uses the kit's bounds; the baseline's "jam" becomes "bet the max" automatically; bluff frequencies drop one notch under pot-limit.
- Antes, blinds, table size, payouts, cap: read from `state.config` every table; nothing in the plan assumes the defaults.
- Information changes (exposed cards, fewer fields): `feed` and `strength` take the extra public cards as known cards; `labels` degrade to what is observable.

## 10. Minute-by-minute mapping to the runbook

- 0 to 7: triage (05) and interface confirmation (12). Decide the variant's safe default.
- 7 to 15: modules 1, 2, 3 (counters only), static preflop table, rank-count postflop. P1.
- 15 to 20: upload v1, select it active. It plays the practice runs from now on.
- 20 to 35: P2 generator in the background (tables, matrix, push/fold with ICM); modules 5 and 6; harness archetypes.
- 30: read practice results and hand histories; set priors and thresholds.
- 35 to 50: modules 7 and 8 with the SHOVER, NIT, FOLDBOT, STATION and AUTO_CBET switches first; paired evaluation; upload v2 by 50 and select it active.
- 50 to 60: fixes only. Final build-hour upload by 55.
- Between rounds: health first, then the hand history, then one change set gated by the harness, uploaded by minute 15 of the gap and selected active.
