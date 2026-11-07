# No Limit (Sequoia x Citadel Securities x OpenAI), Bay Area Regional, Nov 6 2026

Prep kit for Nicholas and Kevin (team of two, Bay Area regional). Built overnight on Nov 6 from the official rules, the tournament web app's public client code, the setup email and video, the public Poker Gym rehearsal simulator, one competitor's published write-up, MIT Pokerbots history, and a set of offline simulations and equilibrium solves run for this kit (10_RESEARCH_FINDINGS.md, `research/`).

## Why this repo holds a plan and not a bot

The Know Before You Go email says: "Pre-written code or bots are not allowed; all code must be written during the event." The official rules add that prizes and advancement are subject to code review (5.4) and that disqualification can happen after results are announced (6.1). So the bot gets written tonight, with Codex or Claude, in the room. What can legitimately be prepared is everything else, and that is what this kit is: the platform facts, the format math, the strategy design, the counter-strategies for the bots you will actually meet, a playbook for every variant family the engine can express, a minute-by-minute runbook, and the prompts that turn the design into code fast. With AI tools allowed and sixty minutes on the clock, the team with the clearest spec and the best test discipline wins the build hour; the team that keeps iterating until T6 wins the night.

## Giving it to Codex

Unzip this folder, open Codex (or Claude Code) with the folder as its working directory, and paste the first block of CODEX_HANDOFF.md. It sets up the build box and the dashboard access now and holds off on bot code until the 6 PM announcement, as the rules require.

## Read in this order

| File | What it gives you | When |
|---|---|---|
| 00_LOGISTICS_CHECKLIST.md | Registration, credits, remote machine, API key, what to bring, timeline | This morning |
| 08_REHEARSAL_TODAY.md | A two-hour timed dry run with the public Poker Gym arena | This afternoon |
| 01_PLATFORM_INTEL.md | Rules digest, what the web app's schemas reveal (variant knobs, frame schema, health metrics, rollback), kit checklist, field intel | Before you leave |
| 02_FORMAT_MATH.md | Weights (T4 to T6 are 71 percent), ICM in numbers, blind pressure, why luck is not a factor | Before you leave |
| 03_STRATEGY_PLAYBOOK.md | The bot design, in build order: safety layer, hand strength without live simulation, preflop by stack regime, postflop, ICM and the cap, opponent modeling | Before you leave, again at 5:40 PM |
| 04_OPPONENT_FIELD_AND_COUNTERS.md | How the field evolves from T1 to T6; fold-bots, shove-bots, maniacs, stations, nits, TAG templates, random bots; detection and counters | Before you leave |
| 05_VARIANT_PLAYBOOK.md | Triage procedure and twenty variant families with the first thing to change for each | At 6:00 PM with the reveal |
| 06_EVENT_RUNBOOK.md | 4:30 to 9:00 PM minute by minute, roles, submission rhythm between tournaments, failure handling | At the venue |
| 07_AI_PROMPT_PACK.md | Eight prompts (P0 recon to P8 post-tournament analysis) with acceptance criteria | At the venue |
| 09_REFERENCE_SHEETS.md | Pot odds, outs, the 169-hand equity table (computed), the computed heads-up push/fold equilibrium, multiway equities, ICM intuitions, the pure-Python 1 ms toolbox, legality traps | Any time |
| 10_RESEARCH_FINDINGS.md | Measured: how often tables hit the cap, what a shove-bot does to a naive table and the response that beats it, what fold-bots and stations score, open wide but call all-ins tight, the Nash push/fold table | Before you leave |
| 12_KIT_INTERFACE.md | The real Agent interface from the dashboard's Getting Started page: act(state, memory), the memory blob, events, time bank, eval7 and the other libraries, uploads every 30 seconds, hand histories, build box | Before you leave, again at 5:40 PM |
| 14_ADAPTIVE_BOT_BUILD_PLAN.md | The specification Codex builds from at 6 PM: modules in order, the memory record layout, the event parser, labels with confidence weights, the exploit switch table, the anti-adaptive layer, the late game, harness gates, variant hooks | Give to Codex now |
| 16_ROUND_LOOP.md | The between-rounds adaptation loop, run six times: health, read the round's hand history, one gated change set, upload, activate, ledger | Give to Codex now; run after every round |
| 15_FINAL_AUDIT_ADDENDA.md | The final audit of 14: range-aware equity, a time-bank budget for exact ICM, three more labels, image management, practice-run A/B, heads-up switches, field-derived thresholds | Give to Codex with 14 |
| 13_EXPLOIT_THE_AI_FIELD.md | What a model like me builds for the other teams, stage by stage; the tells it leaves in the event feed; the counter for each; how not to be the thing we exploit; the meta across six rounds | Before you leave, and paste section 6 to Codex |
| 11_DECISION_CARD.md | The order of checks inside `act()` on one page, to hand to the assistant with P3 | At the venue |
| research/ | The offline tooling behind 09 and 10 (equity tables, equity matrix, push/fold solver, sit-and-go simulator). Not for the event | Reference only |

## The whole thing in twelve lines

1. The bot that is active at 8:08, 8:28 and 8:48 PM decides the result. Keep submitting after the build hour.
2. A timeout or an exception is a fold, thousands of times, and a timeout also empties the table's time bank. Safety layer first, precompute at import, run a throwaway decision at import, no live Monte Carlo, disable GC.
3. Upload a dumb legal bot by minute 20 (uploads are every 30 seconds, and every passing upload goes live). Then build the real one. All per-table state lives in the memory bytes; nothing survives in globals.
4. Levels are 20 hands and the cap is 250, so a table that lasts sees 13 blind levels and most capped tables end heads-up. The ICM split at the cap is where a large share of the points are. Hand counter and cap logic go in v2.
5. Read payouts from state.config every table; the default is 50/30/20, which pays three of eight. Open loose and put the risk premium on all-in calls: under the real format the loose opener scored 18.5 points per table against 14.0 for a standard TAG and 7.6 for a nit.
6. Someone will submit an all-in-every-hand bot. Against a naive table it wins 84 percent of tables. The response worth 3 to 5 points per table: never raise-fold into it, fold or shove first with 77+/AJs+/AK, call its shove with the same set, QQ+ against two shovers.
7. The field is AI-written and predictable: fixed sizes that encode strength, automatic c-bets, equity-vs-random calls, hard stack-off rules, nits, limp-folders, timeout fold-bots, short-handed passivity. 13_EXPLOIT_THE_AI_FIELD.md has the tell, the switch and the counter for each. Practice runs every 10 minutes during the build show the real mix before T1.
8. The late game is push/fold. The computed heads-up equilibrium is in 09; at the event, run the same solve with the kit's ICM calculator for the real payouts.
9. Model opponents inside each table with smoothed stats and labels; adjust ranges, never bluff stations, bet every street into fold-bots.
10. The engine supports extra hole cards, discards, exposed cards, multiple boards, bidding and exchanges. Read the variant prose twice and run the triage before typing.
11. Promote a new version only when a paired local evaluation says it is better with the interval excluding zero, and health shows zero missed decisions.
12. Freeze at 8:40 PM and confirm the active submission on the team page.

## Putting this on GitHub

The session that built this kit could not create a repository on your account (no token with repo-creation rights). The folder is already a git repository with history. Create an empty private repo named `nolimit-prep` on github.com (no README), then:

```
cd nolimit-prep
git remote add origin git@github.com:nnicholas-c/nolimit-prep.git
git push -u origin main
```

Or tell Claude the repo name once it exists and it will push.
