# 07. Prompt pack: what to paste into Codex (or Claude Code) at the event

All code is written at the event, by you and the assistant, against the real kit. These prompts carry the design so the assistant does not have to rediscover it. Fill the `<<...>>` slots by pasting kit files or variant text. Ask for a plan before code when the task is bigger than one file. Ask for tests with every piece. Keep every prompt's acceptance criteria; if the assistant cannot meet them, it has not finished.

The kit ships AGENTS.md and CLAUDE.md with its own rules for assistants. Use the kit folder as the assistant's working directory so it reads them, and paste the constraints block below once anyway; it adds what the kit's file does not say about our design.

Constraints block (paste once at the top of the session):

```
We are building a poker bot for the No Limit tournament. Hard constraints:
- Interface: class Agent(poker_agent_sdk.Agent) with act(self, state, memory) -> (Action, bytes). Actions are Action.fold(), Action.check(), Action.call(), Action.raise_to(total) with total = whole bet for the current round, plus any kinds the variant adds. Choose only from state.legal_actions; state.can(kind) gives min_amount and max_amount. A raise_to outside [min, max] is a failed decision (not clamped). Floats are rounded down; use integers. Check and call are never offered together; fold is not offered when a check is free. When neither check nor fold is offered, Action(first.kind, first.min_amount) with first = state.legal_actions[0] is the safe automatic choice.
- State: nothing persists between calls except the memory bytes we return. Copies of the bot are forked from one import; self and globals must be treated as read-only tables built at import. All per-table state lives in memory (b"" on a new table, truncated at state.config.memory_bytes, 64 KB default; keep it under 16 KB). Parse it defensively and start fresh on any error. No files, no /tmp between tables, no threads, no network, no prints.
- Time: state.config.decision_ms per decision (1 ms default) with a per-table bank of state.config.time_bank_ms (100 ms default) that does not refill and is emptied by a timeout. The upload test match has no bank: 20 hands heads-up vs a check-or-fold bot, rejected if more than 10% of decisions fail. Budget p99.9 under 0.3 ms with no bank. Precompute at import and run one throwaway decision at import.
- Libraries: standard library, poker_agent_sdk, poker_agent_protocol, eval7, NumPy at import time only. Never import poker_engine or pokerkit anywhere in the upload. Set OMP_NUM_THREADS, MKL_NUM_THREADS, OPENBLAS_NUM_THREADS to 1 before importing NumPy.
- Events: state.events is the complete public feed since our last turn (kinds: hand, ante, blind, fold, check, call, raise, board, show, win, stack, plus variant kinds). All showdown hands are revealed. Seats are anonymized per table; carrying anything between tables is against the rules.
- Scoring: 8-player sit-and-go, read state.config for starting_stack, blinds schedule, hands_per_level, hand_cap and payouts (payouts may differ per table; never hard-code them). ICM split among survivors at the cap. Six rounds weighted 1 to 6.
- Upload: agent.py alone or a zip from `poker-agent pack`, 1 MB of code in agent.py, data files next to it. Prefer boring, verified code. Keep strategy in plain functions of plain inputs so the kit-facing layer stays thin. Produce tests with every piece.
```

## P0. Kit reconnaissance (first prompt after the drop)

```
Here is the starter kit: agent.py, examples/, sdk/ (protocol, engine, ICM calculator, poker-agent command), requirements.txt, RULES.md, hand-history/, README.md, AGENTS.md.

<<run from the kit folder so the assistant can read the files; paste RULES.md and the variant announcement text in full>>

Do not write the bot yet. Produce:
1. The exact State and Action API as implemented in sdk/ (field names, types, units): hand fields, table seats and statuses, tournament fields, config fields, events and their kinds, legal_actions entries, any variant phases and action kinds from RULES.md and how to construct them.
2. How the template agent.py uses memory; the memory_bytes default; what happens on a new table.
3. The ICM calculator's signature, units and measured runtime for 8 stacks with the configured payouts.
4. The exact payouts, blinds schedule, hands_per_level, hand_cap, decision_ms and time_bank_ms from the kit's defaults, and whether RULES.md says a round may change them.
5. How `poker-agent play` and `poker-agent check` and `poker-agent pack` work, with the command lines for an 8-seat local game (repeat folders) and for the heads-up 20-hand test against examples/check_or_fold.
6. A list of ambiguities with the one-line experiment that resolves each.
7. A latency harness: time act with time.perf_counter_ns over at least 5,000 realistic states including memory parsing, report p50, p99, p99.9 and max, and the import time of agent.py in a fresh `python -I -S` interpreter.
```

Acceptance: you can answer every line of the checklist in 12_KIT_INTERFACE.md from the output, and the kit's own template runs through the harness.

## P1. The safe baseline (v1, target: uploaded by minute 20)

```
Write v1 of agent.py against the API you summarized. Requirements:
- act wrapped so that any exception returns check if offered, else fold if offered, else Action(first.kind, first.min_amount), together with the memory bytes unchanged.
- One function `choose(kind, total)` that returns a legal Action: raise_to only if offered and with total clamped to [min_amount, max_amount] as an int; otherwise call if offered, else check, else fold, else the automatic choice.
- Memory record: struct-packed, version byte + payload + 16-bit checksum. Fields for v1: hand number seen, my seat, a per-seat all-in-preflop counter and hands-observed counter (8 x 2 x uint16). Parse inside try/except; on failure or b"" start fresh. Update counters from state.events each turn.
- Import-time setup: the 52 eval7 Card objects cached by string; the 169-class preflop table with this ordering <<paste the ranking from 09_REFERENCE_SHEETS.md, or the regenerated one if P2 is done>>; one throwaway act on a synthetic state; then gc.disable().
- Strategy, deliberately simple:
  - Position from distance to state.button among active seats.
  - Preflop: open the top 12% from early seats, 16% middle, 25% cutoff, 40% button, 35% small blind; raise_to 2.5 big blinds (2.2 from button and cutoff). With 12 big blinds or fewer, raise_to max_amount instead with the same ranges plus 10 points. Facing a raise: call with the top 10% when to_call is at most 15% of our stack, raise_to max with the top 4%, otherwise fold. Big blind: call a min-raise with the top 40%. Never open-raise if a seat with all-in-preflop rate >= 60% over 4+ hands is still to act unless our equity vs a random hand is >= 0.65, in which case raise_to max.
  - Postflop: eval7 made-hand class. Bet 60% of the pot with top pair or better when checked to; call bets when the equity estimate (top pair 55%, two pair 75%, trips+ 90%, strong draw 35% with two cards to come, 18% with one) beats pot odds; fold otherwise.
  - Any variant phase or action kind: <<the safe default you chose in triage>>.
- A random.Random seeded from (state.config.table_id, state.tournament.hand_number).
Then: poker-agent check agent.py; poker-agent play with 8 seats (our bot repeated with the examples) for 300 tables; the heads-up 20-hand game against examples/check_or_fold; the latency harness. Report failed decisions, p50/p99/p99.9/max latency, import time, and points per table.
```

Acceptance: 0 failed decisions, p99.9 under 0.3 ms, import under 2 seconds, check passes.

## P2. Table generation (runs on the build box with eval7 and the kit's engine, not inside the bot)

```
Write a standalone generator script using eval7 (and the kit's engine only if the variant changes dealing or rankings) to produce data files loaded by agent.py at import:
1. PREFLOP: for each of the 169 hand classes (use the variant's hole-card count if different; for 3 cards define the class as the best two-card class plus a suited/connected flag), all-in equity against 1, 2, 3, 5 and 7 random opponents, and its rank in the heads-up ordering. 20,000 deals per class.
2. POSTFLOP: for street in (flop, turn), for each made-hand class in <<list from 03 section 4>> crossed with draw flags (none, gutshot, open-ended, flush draw, combo) and for 1, 2, 3 live opponents: average equity against random live hands. 300,000 deals total, bucketing on the fly.
3. MATRIX: the 169 x 169 class-vs-class all-in equity matrix (500 deals per pair, use symmetry), saved for the solver, not loaded by the bot.
4. PUSHFOLD: using MATRIX and the kit's ICM calculator with the payouts from state.config defaults, solve by fictitious play (caller best-responds to the average shoving range, shover best-responds to the average calling range, average the strategies, 300 rounds) the shove-or-fold and call-or-fold ranges for: heads-up at 3, 5, 7, 10, 12, 15, 20 bb; and with 3, 4 and 5 players left and the others assumed to fold, the small blind vs big blind and the button vs both blinds spots at 5, 7, 10 and 15 bb, with chip outcomes converted to points through ICM for representative stack configurations (equal; shover short; caller short). Emit as sets of class indices keyed by (players left, position, stack bucket).
Emit compact Python literals (tuples of ints scaled by 1000) into a data module or a .json next to agent.py, with a header giving the generation parameters. Time-box the script with a wall-clock budget argument and emit what it has when the budget expires.
```

Acceptance: agent.py loads the files at import in under 2 seconds, the preflop ordering matches the known order to within noise (AA, KK, QQ, JJ, TT, AKs, 99, AQs, AKo at the top), and the heads-up chip-EV solve at 10 bb gives about 60 percent shoving and 37 percent calling (09_REFERENCE_SHEETS.md 4a). If the ICM version is not finished by minute 35, ship the chip-EV ranges with the lambda premium and finish the ICM ranges between T1 and T3.

Note: 14_ADAPTIVE_BOT_BUILD_PLAN.md is the specification; P1 to P4 below are the prompts that walk through its modules. Paste the relevant section of 14 into each prompt.

## P3. The strategy core (v2)

```
Replace v1's strategy with the full design. Keep the wrapper, choose(), the memory record and the import-time setup; extend the memory record for the new counters.
Design:
<<paste 11_DECISION_CARD.md, then 03_STRATEGY_PLAYBOOK.md sections 2 to 7, then the variant deltas from 05>>
Specifics:
- Position buckets from distance to the button among seats with status active or all_in, so they work for any number of live players.
- Effective stack in big blinds = min(my stack + my bet, largest stack + bet among live opponents) / big blind, with antes included in the pot.
- Three stack regimes: deep (>25bb), medium (12 to 25bb), short (<=12bb push/fold), with all ranges as constants in one dictionary.
- Postflop: eval7 made-hand class, draw flags, board texture, equity estimate from the POSTFLOP table shaded by the opponent-aggression factor.
- Bet sizes: third, two thirds, pot, all-in; raise_to max when the planned bet exceeds 60% of the effective stack. All totals as ints through choose().
- Risk: lambda from a table indexed by (players left, places paid from state.config.payouts, my stack rank); required equity = pot-odds equity x (1 + lambda); lambda = 0 heads-up. Opening ranges are not tightened by lambda; only all-in calls and commitments are.
- Cap logic from state.tournament.hand_number and state.config.hand_cap: in the last 20 hands, a stack in a paid position by chip count declines marginal all-ins; a stack outside the paid places takes high-fold-equity spots.
- Shove-bot response: a seat with all-in-preflop rate >= 60% over 4+ hands is a SHOVER. While a SHOVER is still to act, never open-raise; fold, or raise_to max with hands whose equity vs a random hand is >= 0.65 (77+, AJs+, AK). Call a SHOVER's all-in with the same set; vs two all-ins require QQ+. Widen when the SHOVER's stack is under 10 bb.
- Never raise-fold: a preflop raise must be one we are prepared to call a shove with when a SHOVER or a frequent 3-bettor is behind; otherwise fold preflop.
Produce unit tests for: choose() on every combination of offered actions, the memory record round trip and its rejection of corrupt bytes, position buckets at 8, 5, 3 and 2 players, effective stack with all-in seats, the eval7 class against a rank-count fallback on 50,000 random 7-card hands, and the preflop decision for 20 scripted states.
Then run the paired evaluation against v1 in the same seats for 1,000 tables and report the mean difference in points per table with a 95% interval, plus the latency harness with the machine loaded (run two evaluations in parallel).
```

Acceptance: evaluator agrees with the fallback 100 percent on category; paired difference positive with interval excluding zero; p99.9 under 0.3 ms; zero failed decisions; memory under 2 KB.

## P4. Opponent tracker and exploits (v3)

```
Extend the memory record and the event parser with the per-seat counters and labels from this design:
<<paste 03 section 7 and 04 section 2>>
Requirements:
- Counters update from state.events every turn, including hands we folded; opportunities are counted only when the seat actually had the choice.
- Showdown observations from show events: count river bets that showed worse than one pair (bluffs) and the percentile of hands shown after a preflop raise.
- Every rate smoothed toward a prior with weight 10.
- Labels: FOLDBOT, SHOVER, MANIAC, STATION, NIT, TAG, UNKNOWN with the triggers in the design; relabel every hand; FOLDBOT requires zero voluntary actions, not low VPIP.
- Adjustments as multiplicative changes to range widths and equity thresholds, all constants in one dictionary.
- Table-level stats: fold-to-steal rate and 3-bet rate.
Add sparring bots to the local harness if P6 has not yet: shove-bot, fold-bot (returns an out-of-range raise every time so the fallback fires), station, maniac, random, nit. Run the paired evaluation of v3 vs v2 against (a) the kit's examples, (b) a lineup with two fold-bots and one shove-bot, (c) eight copies of v3. Report memory size per turn.
```

Acceptance: v3 beats v2 clearly on lineup (b), is not worse on (a) with the interval, shows no pathology on (c) (no label other than TAG/UNKNOWN on a copy of itself after 50 hands), memory under 4 KB.

## P5. Variant adaptation (as soon as triage is done; may precede P3)

```
RULES.md says:
<<paste RULES.md and the announcement text>>
List every assumption in the current bot that the variant breaks, in order of damage. For each: the change, the test that proves it, and a safe default to use if the change is not done in time. Then implement the changes in that order. Pay particular attention to: new phases and action kinds (how to construct them from state.legal_actions, what the automatic choice is), hand ranking order, hole-card count and which cards may be used, number of boards, pot-limit bounds, antes in pot odds, hand cap, table size, payouts, and anything that alters what the events carry.
After implementing, regenerate PREFLOP and POSTFLOP with the variant's evaluator and deck (rerun P2), run poker-agent check, and run 300 local tables plus the heads-up check_or_fold game.
```

Acceptance: a written list of broken assumptions with status; zero failed decisions in the variant's local play; regenerated tables loaded.

## P6. Sparring bots and the paired harness

```
Write a local evaluation harness around poker-agent play (or the sdk engine directly if play's JSON is enough):
- Seats our bot among a lineup of folders; runs N tables; reports points per table with a 95% interval, finish distribution, first-place rate, bust-by-level histogram, failed decisions, and latency percentiles from the harness in P0.
- Paired mode: two versions of our bot in the same seats with the same --seed, mean difference with interval.
- Lineups: the kit's examples; archetype folders we write (shove-bot, fold-bot that returns an out-of-range raise, station, maniac, random, nit, a fixed-range TAG); self (eight copies).
- A no-bank mode: wrap act and count any decision over decision_ms as failed, to approximate the upload test and the production bank running dry.
```

Acceptance: 1,000 tables in under a few minutes on the build box; results reproducible from a seed.

## P7. Pack, validate, upload

```
Produce the upload: a bot directory holding agent.py and its data files only, packed with `poker-agent pack DIR OUT.zip`. Then:
1. Import agent.py in a fresh `python -I -S` interpreter from a virtualenv with only requirements.txt installed; time the import.
2. poker-agent check on the zip.
3. The heads-up 20-hand game against examples/check_or_fold in no-bank mode, and 300 eight-seat tables; require zero failed decisions.
4. Print the sha256 and size so we can confirm them on the team page after upload.
Do not upload unless all four pass. Remember that a passing upload becomes the active bot immediately.
```

Acceptance: all four pass; the team page shows the upload as ready and active with the matching size.

## P8. Between rounds: read the evidence

```
Here is our team page health (decisions, missed, restarts, error reports) and the hand-history subset for the last round, read with the kit's streaming reader:
<<paste health; point the assistant at the downloaded .jsonl.gz>>
Report: (1) any missed decisions, restarts, memory-cut notes or tracebacks and their likely cause; (2) how many of our tables reached the cap and with how many survivors; (3) our finish distribution and bust hands (aggressor or caller, hand class, position, blind level); (4) the archetype mix across named opponents (shove rate, VPIP, fold-to-raise, station behaviour) with rough frequencies; (5) the three highest-value changes for the next round with the risk of each; (6) which of those are safe to ship in 10 minutes with the paired harness as the gate.
```

Acceptance: a short list you can act on in the 20-minute gap.

## How to drive the assistant well in a 60-minute window

- Model choice: credits are not a constraint, so use the strongest model for anything that involves design or judgment (P0, P3, P4, P5, P8) and the fastest one for mechanical work (P1 skeleton, P6, P7, quick fixes). In Codex that is Astra for the first group and Sol for the second. Claude Code is allowed too ("All AI tools are allowed"); run one assistant per person so you are not waiting on the same queue, and give the same constraints block to both.
- Work in the kit folder so the assistant reads AGENTS.md. Paste files, do not describe them.
- Ask for the plan first on P3 and P5, then say "go". Thirty seconds of plan saves ten minutes of rewrite.
- Insist on the acceptance criteria. "Done" means the harness says so.
- Keep two terminals: one running the assistant, one running the harness. The harness is the referee.
- When the assistant proposes live Monte Carlo on the main path, per-call NumPy, Numba, threads, caching to /tmp between tables, globals that carry state, or anything that touches the network, say no and point at the constraints block.
- When an upload is rejected, paste the validation log from the team page into the assistant. Do not paraphrase errors.
