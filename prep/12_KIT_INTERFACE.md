# 12. The real interface: what the Getting Started page says, and what it changes

Source: the dashboard's Getting Started page (text captured Nov 6, 1 PM). This is authoritative where it overlaps with earlier guesses in 01 and 03. Read this before the runbook and the prompts.

## 0. The Format page (pasted Nov 6, 2 PM; this is the round default, and state.config is the truth per table)

- Players 8, starting stack 2,000, starting blinds 10/20, blinds increase every 20 hands, hand cap 250. A table ends when one bot holds every chip or at the cap. The blind schedule beyond 10/20 arrives with the kit.
- Default payouts 50 / 30 / 20 for places 1 to 3; places 4 to 8 get 0. At the cap, survivors split the remaining points by ICM on their stacks.
- Six scored rounds, 20 minutes apart from the end of the build, weights 1 to 6. Each round runs at least 5,000 iterations; every bot plays one table per iteration; round score is average points per table; final score is the weighted sum (the last round is 6 of 21 units). Results normally arrive in the following 20-minute window, with a compute gap after the last round.
- Practice runs: about 1,000 iterations every 10 minutes during the build phase, never counted. This is a free look at the live field before T1. Upload v1 by minute 15 and read the practice results and hand histories from minute 25 onward.
- Activation: the Format page says "Select a ready upload as your active bot. An upload alone does not activate it", while the Getting Started page says each passing upload becomes active automatically. Treat it as manual: after every upload, open the team page and confirm which upload is active. Each round freezes a snapshot of the active bot at its start; a team without an active bot forfeits that round.
- Fairness: seats randomized each iteration; fillers never score for their teams; when several bots bust in the same hand, the one with more chips at the start of the hand places higher; memory starts empty at every table; seats are anonymized.
- Tiebreak is countback, not a challenge: equal totals are ordered by the share of tables each team won in every scored round, weighted and summed, then second places, and so on. First places matter beyond their points.
- Regionals at Harvard/MIT, Stanford (this one) and CMU; five teams from each plus five wildcards go to the Finals, same format, different variant.
- The build box for this team is poker-production-team-114 (ssh ubuntu@44.211.129.102), first login already done on Nov 6 at 1:47 PM.

## 1. The Agent

```
class Agent(poker_agent_sdk.Agent):
    def act(self, state, memory):
        return action, memory_bytes
```

- One method. It receives the state and the `memory` bytes returned on our previous turn at this table, and returns an Action and the bytes to get back next time.
- Betting actions: `Action.fold()`, `Action.check()`, `Action.call()`, `Action.raise_to(total)` where total is the whole bet for the current betting round (raise-to semantics, settled).
- `state.can(kind)` returns that kind's legal action with `min_amount` and `max_amount`, or None. `state.legal_actions` is the list. In reference hold'em `state.phase` is "betting"; a variant may add phases and action kinds, and "its rules describe how to build them". Where neither check nor fold is offered, `Action(first.kind, first.min_amount)` with `first = state.legal_actions[0]` is the automatic choice. That line is the safe default for any variant phase we do not understand yet.
- Only offered kinds are legal. A `raise_to` total outside min to max is not clamped; it is a failed decision (fallback) even when the fallback would have the same effect. Check and call are never offered together. No fold is offered when checking is free. Integers pass unchanged; floats (NumPy's too) are rounded down, so a computed size can land one chip under the minimum. Use integer arithmetic and `max(min_amount, min(max_amount, total))` on every raise.
- Showdowns never call act. Everyone who reaches showdown reveals all hole cards, losers included; mucking is not allowed. The `show` events arrive on our next turn.

## 2. State

- `state.events`: everything public at the table since our last turn (first turn: since the table started). Kinds in reference hold'em: hand (amount = hand number), ante, blind, fold, check, call (chips added), raise (the raiser's total for the round), board (newly dealt cards), show (revealed cards), win (chips awarded, several per hand possible), stack (seat's stack when the hand ends). Each event has kind, seat (None for hand and board), amount, cards. Variants can add kinds; ignore unknown ones. This is a complete action feed, including everything that happened after we folded, so full opponent tracking is possible from events alone.
- The hand: seat, cards, board, pot, to_call, legal_actions, history (this hand), phase. Cards are strings like "As", "Td". `state.variant` holds any public variant state.
- The table: seats, each with seat, stack, bet, status (active, folded, all_in, busted), shown_cards; and button. Seat numbers are anonymized per table.
- The tournament: blind_level, blinds, hands_until_next_level, hand_number, players_remaining, bust_order.
- `state.config`: table_id, seat, variant id, players, starting_stack, blinds schedule, hands_per_level, hand_cap, payouts, decision_ms, time_bank_ms, memory_bytes. The page warns that a round may draw payouts per table, so the bot reads `state.config.payouts` every table and never hard-codes the payout table. The page's example default is 50/30/20, which for an 8-player table means only three places pay.

## 3. Memory is the only state

- `self` and module globals cannot be relied on between calls. Each team runs as a pool of identical copies and any copy may answer any table. Production imports agent.py once, forks every copy from that process, then each copy constructs Agent(). Threads started at import do not survive the fork.
- Per-table state travels in `memory`: starts as b"" at every table, truncated at `state.config.memory_bytes` (64 KB default), and "up to about 16 KB costs nothing measurable" because it travels inside the decision time.
- After a timeout, exception or crash, the previous memory is kept and that turn's events are delivered again. After an illegal action, the memory returned with it is stored. Memory that makes act raise comes back unchanged on every later turn, so a corrupt blob can poison a whole table.
- Carrying information between tables breaks the rules. Files between tables and computing between decisions are forbidden too.

Design consequence: the opponent tracker, the hand counter, the labels, the cached ICM number, everything per table, is a small fixed-layout binary record (`struct`) with a version byte, a length and a checksum. Parse it inside try/except; on any failure start from a fresh record for this table rather than raising. Keep it under 16 KB; a few hundred bytes is plenty (8 seats times a dozen 16-bit counters is under 200 bytes).

## 4. Time

- `state.config.decision_ms` per decision (1 ms default) plus a small delivery allowance. Overruns draw on a per-table bank of `state.config.time_bank_ms` (100 ms default); `state.time_bank_ms` shows what remains. A timeout empties the bank; the next table starts with a full one.
- The bank does not refill within a table. 200 hands times a 1 ms overrun is twice the bank, so it is for rare spikes, not for routine use. Budget p99.9 well under 1 ms.
- The upload test match has no bank: up to 20 hands heads-up against a check-or-fold bot, 1 ms per decision, in the competition's variant. Rejected if the bot does not start within the startup allowance, crashes or stalls, or fails more than 10 percent of its decisions. Local `play` always gives a 100 ms bank, so a bot can pass locally and fail the upload.
- Importing has its own startup allowance; a cold first call inside act can exhaust the bank. Load everything at import and run one throwaway act-equivalent there so lazily built caches exist before the fork.

## 5. Libraries and sandbox

- Python 3.12, the standard library, poker_agent_sdk, poker_agent_protocol, and exactly the packages in requirements.txt: NumPy, SciPy, pandas, scikit-learn, PyTorch (CPU), LightGBM, XGBoost, ONNX Runtime, Numba, eval7. poker_engine and pokerkit exist only locally; `check` rejects any .py in the zip that imports them.
- eval7 is the important one: a C hand evaluator with range and Monte Carlo helpers. Exact made-hand evaluation becomes a few microseconds, and tables can be generated on the build box at millions of deals a minute. Cache the 52 `eval7.Card` objects at import; building them per call is the slow part.
- No network, no GPU. The bot directory is read-only and not executable (no compiled extensions of our own). /tmp is a 64 MB scratch shared by the copies. OpenMP, MKL and OpenBLAS are limited to one thread; set OMP_NUM_THREADS, MKL_NUM_THREADS and OPENBLAS_NUM_THREADS to 1 in agent.py before importing NumPy or PyTorch so local timings match; ONNX Runtime needs `intra_op_num_threads = 1`, Numba needs NUMBA_NUM_THREADS=1 before import.
- What this means for the design: keep NumPy to import-time table building; per-call NumPy operations cost microseconds each and add nothing over tuple lookups. Numba's JIT compile at import is a startup-allowance risk and the read-only directory blocks its on-disk cache; skip it. A tiny LightGBM or Torch model is possible but a lookup table does the same job a hundred times faster; consider a model only for T4 to T6 if the hand histories justify it.

## 6. Uploads and rounds

- Upload agent.py alone, or a zip with agent.py at its root plus the files it reads. `poker-agent pack DIR OUT.zip` zips reproducibly (drops hidden files and __pycache__, refuses symlinked files) and runs `check`; DIR holds only the bot, not the kit root. Limits: 50 MB upload, 200 MB unpacked, 1,000 entries, 1 MB of code in agent.py, paths up to 512 characters and 16 levels. Tables beyond 1 MB go in data files next to agent.py and are read at import.
- One upload every 30 seconds (not five minutes; the rules page is out of date on this).
- Each upload that passes its test match becomes active automatically unless the competition is frozen or has ended. An earlier upload can be chosen on the team page. Each round snapshots the active bot when it starts; a team without an active bot forfeits that round with zero points. During a freeze, uploads and active-bot changes are refused.
- Consequence: never upload an experiment to "see if it passes". Passing makes it live. Verify locally, upload, and keep the previous upload's id handy to re-select if health goes bad.
- The team page shows each round's decisions, missed decisions, restarts and the latest error reports: tracebacks, why a copy was killed, and a note when memory was cut. It never shows prints.
- A copy that crashes, stalls, or breaks the protocol is killed and restarted on its next request; copies have a limited number of starts per round, and once every copy is given up on, the bot plays the fallback for the rest of the round on that machine. An exception inside act fails only that decision.

## 7. Hand histories

When a round completes, the team page and the round page offer the hand history: every table our bot played, as gzipped JSON lines, with opponents named, our cards in every hand, other players' cards when public, and the actions played for our failed decisions. Full set or a smaller subset. The kit's hand-history/ folder has a sample and a streaming reader.

Use between rounds: count how many tables reached the cap, our finish distribution, our bust hands, and the archetype mix by named opponent (which teams shove every hand, which fold everything). Names are not available inside a table (seats are anonymized) and cross-table memory is banned, so this informs the detector thresholds and the ranges, never a per-team lookup.

## 8. Starter kit contents

agent.py (a template that plays legally, with a memory example), examples/check_or_fold and examples/min_raiser, sdk/ (protocol, engine with local simulator, ICM calculator, the poker-agent command), requirements.txt (exact versions on the competition machines), RULES.md (the announced variant), hand-history/ (sample and streaming reader), README.md, AGENTS.md and CLAUDE.md (instructions for coding assistants; use the kit folder as the assistant's working directory). Available when the variant is announced.

Local commands:

```
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e ./sdk/agent-protocol -e ./sdk/engine -e ./sdk/agent-sdk
poker-agent check agent.py
poker-agent play . examples/check_or_fold examples/min_raiser --tables 200
```

`play` seats 2 to 10 folders (repeat folders to fill 8), runs each folder as two processes, prints stderr tails, and reports average points, finishing places and failed decisions per seat as JSON. `--seed` replays the same randomness. Changes under sdk/ affect only local play. Test in a virtualenv with nothing else installed, since `check` only catches the two local-only packages.

## 9. Build box and setup skill

An EC2 Ubuntu box similar to the tournament runtime, per team, with SSH per member key (ed25519, RSA or ECDSA; five keys per account; live within 30 seconds), `~/work` as the working folder, `codex login --device-auth` for Codex, tmux for a terminal session, and an SSH alias `no-limit-2026-build` that the Codex app needs. The setup skill is one file at https://pokerbot.sequoiacap.com/tournament/no-limit-2026-setup/SKILL.md; a terminal agent (Codex, Claude Code) downloads and follows it with an API key from Settings, and running it again after the announcement puts the kit on the machine. The page says to run setup on a smaller model to save credits; credits are not a constraint for us, so that advice only matters for speed. "Address not available yet" means the fleet has not started; "Build starts ..." means the box is closed until then.

## 10. What this changes in the earlier files

- 03 and 11: all per-table state lives in the memory blob; the tracker reads `state.events`, not a kit-provided history; made-hand evaluation uses eval7; the ICM calculator from sdk/ is available but still time it.
- 06: uploads every 30 seconds, the upload test match conditions, and the "passing makes it active" rule change the submission rhythm; the EC2 box is where to benchmark.
- 07: prompts rewritten against the real signatures.
- 02 and 04: with a 50/30/20 default, only three of eight places pay; the simulations were re-run for that shape (10, section 9).
- 01 section B remains useful for the round-rule knobs and the frame schema; its guesses about the Agent interface are superseded by this file.
