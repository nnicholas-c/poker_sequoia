# 16. The round loop: reason and adapt six times tonight

Two adaptation loops run tonight. Inside a table the bot adapts on its own (14, sections 3 to 6). Across rounds the bot cannot learn (memory starts empty, seats are anonymized), so the second loop is ours: read what happened, decide one change set, gate it, upload, activate, before the next snapshot. This page is that loop. Run it after every practice run during the build hour and after every scored round. Time budget per round: 15 minutes from results to active upload; results arrive in the 20-minute window after a round starts, so start the loop the moment the team page shows them.

## 0. Keep a ledger

`LEDGER.md` in the bot folder, one block per upload: upload id, time, what changed (constants and switches), the local paired result that gated it, and after the round, the round's average points, finish distribution, missed decisions, and what the hand history said. Every change tonight is traceable to evidence in the ledger. Codex appends; nobody edits history.

## 1. Health (2 minutes, Kevin)

Team page: decisions, missed decisions, restarts, error reports, memory-cut notes. Any nonzero missed or restart count is the only item on the agenda until it is zero. Typical causes in order: a cold path on the first call of a copy, a GC pause, an ICM or Monte Carlo path that ran long, a memory record that grew past 16 KB, an exception on an event kind we did not expect. The fix ships alone, with no strategy change in the same upload.

## 2. Read the round (6 minutes, Nicholas, with Codex and the kit's streaming reader)

Download the hand-history subset. Compute and write into the ledger:

- Ours: average points, finish distribution (1st to 8th and survived-to-cap), bust hands by cause (called a jam, jammed and got called, lost a big pot postflop, blinded out), share of tables that reached the cap and with how many survivors, steal attempts and success rate, 3-bet success rate, c-bet success rate, how often we were the first to bust, how often we finished 4th.
- Field, by named opponent: VPIP, PFR, limp rate, fold-to-open, fold-to-3-bet, all-in-preflop rate, postflop call rate, c-bet rate, number of showdown bluffs, average open size and its spread, short-handed button fold rate. Then the distribution of each stat across the field (median, 20th and 85th percentiles) and the count of each archetype by 14's label rules.
- Exploit hit rates: for each switch, how often it fired per table and the average points at tables where it fired against tables where it did not (the harness can tag this in local play; in the round, approximate from the labels the opponents' stats would have earned).

## 3. Decide one change set (4 minutes, both)

Pick from this list, top to bottom, the first that the evidence supports. One change set per round; two only if the first is a pure bug fix.

1. Missed decisions or restarts: fix, nothing else.
2. We bust first or finish 4th far more than average: tighten all-in calls (raise lambda one notch, require one more notch of equity against jams), stop raise-folding, check that the SHOVER switch fires fast enough; do not touch opens.
3. We reach the cap with the short stack too often: open wider late (the loose opener's edge in 10 section 8c), jam more at 12 bb and under, attack SHORT_PASSIVE and NIT blinds harder.
4. Steals fail more than 40 percent of the time: the field defends; cut steal multipliers by a third, add light 3-bets only against seats whose fold-to-3-bet is high, raise the 4-bet jam range.
5. Archetype counts shifted (fold-bots gone, nits fewer, maniacs more): re-fit the label thresholds to the field quantiles (15, item G) and the priors to the field medians; loosen or tighten each switch to match.
6. A switch fires often and loses: lower its multiplier or raise its evidence requirement; a switch never fires: lower its minimum sample if the archetype exists in the field, otherwise leave it.
7. Many tables end heads-up at the cap and we lose them: heads-up switches from 15, item F, and the solved push/fold ranges at the real stack depths.
8. Nothing above applies: ship nothing. A round with no change is a good round.

## 4. Gate and ship (3 minutes, Kevin)

Paired local evaluation against the active upload, same seats and seeds, 1,000 tables, archetype zoo plus eight copies: positive with the interval excluding zero, zero failed decisions, p99.9 under 0.3 ms with no bank, record under 2 KB. Pack, check, upload, then select the upload as active on the team page and confirm it there. Never within five minutes of a round start. Write the ledger block.

## 5. What changes from round to round (the expected arc)

- After the build-hour practice runs: priors and thresholds from the live field; the SHOVER, NIT, FOLDBOT and STATION switches tuned; v2 active for T1.
- After T1: health, then whatever item 2 or 3 says; the field still has broken bots, so switches stay loose.
- After T2: range-aware equity (15, item A) if the generator finished; AUTO_CBET and SIZE_TELL switches tuned from showdown data, which only becomes plentiful now.
- After T3: late-game work, since 71 percent of the score is still ahead: heads-up switches, cap logic checked against the real cap frequency, the time-bank budget for exact ICM (15, item B).
- After T4: tighten exploit triggers if the broken bots are gone; image management (15, item D) if adaptive opponents are visible in the data (seats whose fold-to-steal against us dropped over the table).
- After T5: only fixes with evidence. The T6 bot is the T5 bot unless health says otherwise; confirm it is active at 8:40 PM.

## 6. Reasoning rules that hold all night

- Points per table, not chips, is the objective; a change that wins more chips but busts more often is a bad change under 50/30/20.
- One change set per round, gated, logged. Two untested changes in one upload cannot be debugged in a 20-minute window.
- Evidence beats theory: a switch that the hand history says loses is turned off even if the design says it should win.
- The last round is worth six of the twenty-one units; never risk it on an unproven upload.
- When in doubt between two changes, ship the one that reduces our bust-early rate.
