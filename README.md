# poker_sequoia — No Limit 2026 (Bay Area) bot

Team: Nicholas + Kevin + Claude. Everything we build lives here; we iterate by running our
bots against each other in the arena and promote the winner to the active upload.

Variant (announced 6 PM): hold'em with **three** hole cards; after the flop every live player
discards one card face down and exposes one retained card; the third stays hidden; showdown
uses the two retained cards + board. Mystery prizes: Empty Bluffer, the Shover, Calling Station.

## Layout

| path | what |
| --- | --- |
| `bots/<name>/agent.py` | one folder per bot version (upload `agent.py` directly, or `poker-agent pack`) |
| `arena/arena.py` | in-process tournament runner: any mix of bot folders, latency, bust hands, points ± CI |
| `arena/pre_table.py` | generator for the 169-class preflop equity table embedded in the bots |
| `kit/` | the organizers' starter kit (SDK, engine, rules, examples, hand-history reader) |
| `prep/` | strategy research, build plan, format math, exploit notes (read `prep/README.md`) |

## Setup

```bash
python3.12 -m venv venv && source venv/bin/activate
pip install -r kit/requirements.txt eval7 numpy
pip install -e kit/sdk/agent-protocol -e kit/sdk/agent-sdk -e kit/sdk/engine
```

## Daily loop

For quick shared competitions, see [the internal league](arena/LEAGUE.md). It discovers
`bots/*/agent.py`, blocks known tactical failures, freezes source and assets by hash,
and plays balanced eight-seat pairings. New versions go in new folders.

```bash
python arena/league.py --tables 24
# Compare only the changed version, without rerunning every unchanged pair:
python arena/league.py --focus nc_v2 --tables 24
```

Reports and frozen snapshots stay in ignored `arena/runs/`. Short matches guide the
next fix; they do not automatically promote or upload a bot.

```bash
# legality + size check exactly as the upload does it
poker-agent check bots/nc_v1/agent.py

# upload-test conditions: heads-up vs check_or_fold, 1 ms per decision, no time bank
python arena/arena.py bots/nc_v1 kit/examples/check_or_fold --players 2 --tables 300 --bank 0 --hand-cap 20

# full table: four copies of A vs four of B (seats rotate every table)
python arena/arena.py bots/A bots/A bots/A bots/A bots/B bots/B bots/B bots/B --tables 400

# mixed field with fallbacks (teams whose bots crash are played as check_or_fold)
python arena/arena.py bots/A bots/B bots/C --fill kit/examples/check_or_fold --tables 400

# the organizers' runner (sandboxed subprocesses, hand histories)
poker-agent play bots/A bots/B kit/examples/check_or_fold --tables 50
```

Points are the table payouts (50/30/20 by default); 100 points per table split over 8 seats, so
12.5 is par. `bust@` is the median hand a bot busted on (251 = survived to the cap).

## Rules of the road for bots

* Stateless: no globals that change between calls; everything per table goes in the memory bytes
  (we use a crc-checked struct record, fresh record on any parse failure).
* 1 ms per decision, 100 ms bank per table that never refills. Keep p99.9 well under 1 ms.
* Never import `poker_engine` or `pokerkit` in `agent.py`; `poker-agent check` rejects them.
* A `raise_to` outside `[min_amount, max_amount]` is a failed decision (platform plays check/fold).
* Select phase: `Action("select", cards=(discard_index, reveal_index))`, indices into `state.cards`.
