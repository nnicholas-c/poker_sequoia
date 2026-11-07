# 15. Final audit: what 14 covers, and seven additions in order of value per minute

Audit done at 5:55 PM against the question "is this the most comprehensive adaptive, exploitative strategy against AI-written bots, including bots built from the same advice". The answer is that 14 covers the structure (baseline, tracker, labels, switches, anti-adaptive layer, late game, gates) and the limit is build time, not ideas. The additions below are ordered by points per minute of implementation; take them in order, each only after the previous upload passed its gates.

## A. Range-aware equity (biggest remaining leak; about 10 minutes in the P2 generator plus a lookup key)

14 estimates postflop equity against random hands and shades it by aggression. Against a seat whose preflop raise rate is 12 percent, our top pair is far weaker than the random-hand table says, and against a 45 percent raiser far stronger. Add to the P2 generator a second POSTFLOP table keyed by the opponent's preflop range width bucket (top 10, 20, 35, 50, 100 percent of the regenerated ordering) and use the seat's smoothed PFR (if it raised) or VPIP (if it called) to pick the bucket. Multiway: use the tightest live opponent's bucket. This replaces the aggression shading, which stays as the fallback for seats with no data.

## B. A time-bank budget for exact ICM at the decisions that matter (5 minutes)

The bank is 100 ms per table and does not refill, and an overrun inside the bank is not a timeout. Allow at most three decisions per table to run the kit's ICM calculator exactly, each capped at 8 ms by a perf_counter check, only when all three hold: the decision is all-in sized, four or fewer players are live, and `state.time_bank_ms` is above 50. Gate the whole feature on `state.config.time_bank_ms > 0` so the upload test match (no bank) never sees it. Track the count in the memory record. Everywhere else the lambda table stays.

## C. Three more labels the research found and 14 lacks (5 minutes each)

- JAM_CALLER: showed a hand outside the top 25 percent after calling an all-in preflop, or called two or more all-ins in 20 hands. Counter: never bluff-jam it; jam value wider into it (top 20 percent at 12 to 20 bb); let it call off against our premiums.
- OVERBLUFFER: bluffs_shown / showdowns at or above 0.4 with three or more showdowns. Counter: call its river bets with any pair; raise its turn bets with good pair.
- DONKER: bets into the preflop aggressor on 25 percent or more of flops (GPT-4's measured postflop habit) and shows weak hands doing it. Counter: raise its donk bets with good pair or better, call with draws, fold air.

## D. Our image as the table sees it (second-order play; 10 minutes)

Keep our own last-20-hands VPIP, PFR and postflop aggression in the record, computed the way a generic tracker would. When our recent PFR exceeds 0.35 (a steal burst against nits), expect the adaptive seats to label us MANIAC and call lighter: for the next 15 hands bet only for value against them and let them pay off. When our recent VPIP is under 0.15 (a card-dead stretch), expect them to label us NIT and steal more: defend the blind wider and 3-bet their steals with the top 8 percent. This is the cyclical version of 14 section 6, and it is what a bot built from the same advice as ours cannot see coming, because it reads our stats, not our intent.

## E. Use the practice runs as an A/B lab, not only as a telescope (0 minutes of code)

Practice runs are 1,000 tables every 10 minutes. v1 is active from minute 20; switch the active bot to v2 at minute 45 to 50 and compare the two practice averages at minute 60. Same field, same hour, a thousand tables each: that is a cleaner comparison than any local lineup. Between rounds, the same trick works only when a round is not about to start; the snapshot rule makes the active bot at each start the one that counts, so never leave an experimental bot active within five minutes of a round start.

## F. Heads-up specifics (5 minutes)

Most capped tables end heads-up under the real format. Two more switches: if the opponent folds its big blind to our min-raise 60 percent or more over 6 chances, min-raise every button; if it 3-bet jams our opens 30 percent or more over 6 chances, open smaller with the top 60 percent and call its jams with the solved heads-up calling range at the current stack depth. If it limps its button, raise every limp with the top 70 percent.

## G. Thresholds from the field, not from a prior (between rounds; 5 minutes with the streaming reader)

After each round, compute per-opponent-name VPIP, PFR, fold-to-open, all-in rate and postflop call rate from the hand history, and set the label thresholds at population quantiles: NIT at the 20th percentile of VPIP, MANIAC at the 85th percentile of PFR, STATION at the 85th percentile of postflop call rate. Labels then separate this field rather than a textbook one, and the priors in 14 section 4 become the field medians.

## Things checked and left as they are

- The one-shown-bluff rule in 14 section 6 is cheap only if the bluff is a min-bet on the river against a NO_BLUFF or AUTO_CBET seat that folds often; keep it that way, once per table, never when a call would hurt.
- The adaptation detector needs five chances in both windows, so it fires around hand 60 at the earliest. That is acceptable; most adaptive bots need as long to start adapting.
- Seat indices are stable within a table and anonymized across tables (Format page). Confirm in P0 that the index in events matches the index in `state.table.seats`.
- Label thresholds should scale with the player count as the table shrinks (a 25 percent VPIP is tight 3-handed). Simplest: evaluate NIT and MANIAC only against the expected VPIP for the live count (8: 0.20, 6: 0.25, 4: 0.33, 3: 0.40, 2: 0.60).
- Nothing in the plan assumes a schedule, payout table, cap or deck; everything reads `state.config` and the regenerated tables.
- Over-building is the real risk. The order in 14 section 1 and the gates in section 8 are the protection; an upload that fails a gate is not an upload.
