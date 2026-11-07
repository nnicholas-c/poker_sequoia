# 08. Rehearsal this afternoon (about 2 hours, finish by 2:30 PM)

The single best use of today is a timed dry run of the exact thing you will do tonight: read an unknown kit, get a legal bot submitted in 20 minutes with an AI assistant, improve it, bundle it, submit it. A public rehearsal simulator exists for exactly this (Poker Gym, MIT licensed, unaffiliated with the organizers). Use it for practice. Leave every line of code it produces at home; tonight's code is written tonight.

## Install (5 minutes)

```
git clone https://github.com/mack-dot/poker-gym.git
cd poker-gym
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m pokergym.cli run --seed 1 --verify --out runs/baseline_seed1.json
```

If `uv` is installed: `uv venv --python 3.12 .venv && source .venv/bin/activate && uv pip install -e ".[dev]"`.

## Drill 1: wire a bot into a kit you have never seen (15 minutes, both of you)

```
python drills/fake_kit/run_drill.py reference_adapter.py:Adapted    # see what PASS looks like
```

Then do it for real: start a timer, read only the interface docstring in `drills/fake_kit/fakekit.py`, copy `adapter_template.py`, fill the TODOs, run the drill until it prints PASS. Record the time. The traps in that fake kit (raise-by vs raise-to, uppercase suits, `pot` including live bets, status strings, `chips`/`wager`/`paid`) are the traps the real kit will have in some form. Do it twice if the first run takes more than 20 minutes; the second person edits the fake kit so the interface is genuinely unseen again.

## Drill 2: the sealed 60-minute rehearsal (75 minutes including postmortem)

```
python -m pokergym.arena smoke                        # 90-second end-to-end check first
python -m pokergym.arena rehearse ~/arena/r1 --seed 7 # press Enter to start the real clock
```

What it does: picks a concealed one-rule mutation (ranking swap, raise cap, antes, turbo blinds, payout shape, or board dealing pattern), creates a workspace with only what an organizer would hand over (kit modules, a template agent, a local runner, a submit script, a README), starts a real 60-minute clock with one submission per five minutes, validates each submission (size, import, interface, legality on recorded observations, full games under the 1 ms rule, errors, timing), grades against hidden opponents, and writes a postmortem with failure classes A to F.

Run it the way tonight will go: Nicholas on strategy and prompting the assistant, Kevin on the runner, validation and submission. Use Codex (or Claude) in the loop exactly as tonight. Use the prompts in 07_AI_PROMPT_PACK.md, P0 then P1 then P3, and see how long each takes with the assistant.

Competitor commands inside the workspace (Linux has no sandbox-exec; isolation is "weak" there, which is fine for practice):

```
python -I -S run_local.py my_agent.py --tables 50 --vs heuristic   # local games, latency, legality
python -I -S submit.py my_agent.py --check                         # free validation, uses no slot
python -I -S submit.py my_agent.py                                 # uses the 5-minute slot
```

Then read `results/postmortem.md`. The classes to watch for:

- A: misread the rule change (recognized late or never acted on it)
- B: implemented the rules incorrectly (legality failures)
- C: weak strategy (below the naive reference)
- D: poor experimental design (slots burnt without free checks)
- E: runtime violations (import, errors, timing)
- F: wasted development time (long silences, unused minutes before the freeze)

Whatever class you land in is the thing to fix in tonight's runbook. Most first attempts land in B or E; that is why v1 tonight is the dumbest legal bot and why it goes up at minute 18 to 20.

## Drill 3 (optional, 15 minutes): watch how a shove-bot and a fold-bot do

```
python -m pokergym.cli ladder --tables 500 --workers 4
python -m pokergym.cli run --seed 3 --bots tag,lag,shortstack,icm,adaptive,heuristic,random,call --verify
python -m pokergym.cli show runs/x.json --seat 0 --hands 0-40
```

Add a shove-bot and a call-bot to a lineup and look at the finish distributions. It builds intuition for 04_OPPONENT_FIELD_AND_COUNTERS.md: the shove-bot wins some tables outright and busts first in most; the call-bot bleeds. Watch what the ICM-aware sparring bot does near the bubble.

## What to write down after the rehearsal

1. Minutes to first legal submission. Tonight's target is 20.
2. Which interface trap cost time. Add it to the interface checklist in 01.
3. Which prompt needed rewording. Fix it in 07 before you leave.
4. The assistant's latency per prompt. Decide how many rounds of P3 you can afford in the build hour.

Leave by 2:45 PM. Friday afternoon from Berkeley to Sand Hill Road is 90 minutes with traffic, more if 880 is bad. Help desk opens 4:30.
