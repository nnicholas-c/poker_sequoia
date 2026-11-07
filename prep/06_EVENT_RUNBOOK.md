# 06. Event runbook: 4:30 PM to 9:00 PM, minute by minute

Two people, two laptops, one remote build machine, one dashboard. Roles below are a default; swap if one of you is faster at a step.

- Nicholas (N): strategy owner. Reads the variant, decides lambda and ranges, drives the strategy prompts, reads hand logs between tournaments.
- Kevin (K): pipeline owner. Reads the kit interface, owns the local simulator and the latency harness, owns bundling and submission, watches health and announcements.

Golden rules: a legal bot on the server beats a brilliant bot on the laptop. Uploads are allowed every 30 seconds, but every upload that passes its test match becomes the active bot immediately, so an upload is a release, not an experiment. Upload at least five minutes before each round start so the test match finishes. Never upload anything that has not run a few hundred local tables and the heads-up check_or_fold game with zero failed decisions. Only one person uploads.

## 4:30 to 5:00 PM: arrive, help desk

- Check in with government ID. Both names must be on the attendee list.
- Verify on both laptops: dashboard sign-in works, the team shows both members, the build box answers `ssh ubuntu@<address>` (or shows its opening time), the SSH alias `no-limit-2026-build` works for the Codex app, `codex login status` on the box is signed in, and the platform API key is created and saved somewhere safe (it uploads bots). Run the setup skill again after the announcement to pull the kit onto the box.
- Verify Codex and any other assistant are signed in and have credits. Verify a plain terminal with Python 3.12 works offline on each laptop.
- Ask the help desk two questions: whether the kit's local simulator is the same engine as the server, and whether scored rounds use ICM luck correction. Write down the answers.
- Check the Getting Started and Format pages for anything new. Download the kit the moment it appears.

## 5:00 to 6:00 PM: dinner, networking

- Eat. Talk to the Citadel Securities and OpenAI people (they are there to recruit; a 30-second intro each is worth doing). Collect swag.
- At 5:40 sit down together, open this kit's 05_VARIANT_PLAYBOOK.md triage list and 07_AI_PROMPT_PACK.md P0 and P1, and be ready to paste.
- Charge everything.

## 6:00 to 6:08 PM: kickoff and variant reveal

- One person transcribes the variant prose word for word into a text file the moment it appears (Format page or screen). The other opens the kit.
- Do not start coding during the talk. Listen for: payouts, blind schedule, antes, time bank, anything about luck correction or practice rounds, and the exact start time of the build phase.

## Build phase, T = 0 to 60 (times from the official start)

### T+0 to T+7: read, do not type (both)

- K: open agent.py, examples/, sdk/, RULES.md, README.md and AGENTS.md. Confirm the facts in 12_KIT_INTERFACE.md against the shipped code (field names, event kinds, any variant phase and action kind, payouts and blinds in the defaults, memory_bytes, decision_ms, time_bank_ms) and note every difference. Install the venv on the box, run `poker-agent check agent.py` and `poker-agent play` on the template.
- N: read the variant prose twice and run the triage in 05_VARIANT_PLAYBOOK.md. Write down the payout table, places paid, and the lambda choice. Identify every new decision type.
- Both: 60 seconds to agree on what v1 is. v1 is always: the safety wrapper, legal-action clamp, a normal position chart, pot-odds postflop, no raise-folding, and a correct default for any variant-specific decision.

### T+7 to T+18: v1 (K pipeline, N bot)

- K: set up the one-command local evaluation (8 seats by repeating folders, N tables, --seed), the latency harness (p50, p99, p99.9, max, import time, no-bank mode), the heads-up check_or_fold game, and the one-command pack plus upload. The build box is the machine to time on; it matches production.
- N: prompt P1 (safe baseline). Paste the kit's template and the interface checklist into the prompt. Review the output for the non-negotiables (03_STRATEGY_PLAYBOOK.md section 1).
- Both at T+15: run v1 through K's pipeline. Zero failed decisions over 300 tables and in the heads-up test, p99.9 under 0.3 ms with no bank, or it is not v1.

### T+18 to T+20: upload v1

- K uploads the packed zip. Watch the test match pass, then select the upload as the active bot on the team page (the Format page says an upload alone does not activate it; the Getting Started page says it does; check either way). If rejected, read the validation log on the team page, fix, upload again (30-second cooldown). Do not touch strategy until v1 is active on the server. From now on it plays in the practice runs that happen every 10 minutes.

### T+20 to T+45: v2 (the real bot)

- K: prompt P2 (tables and the push/fold solve) on the build box in the background with eval7: preflop, postflop, the equity matrix and the ICM push/fold ranges. Target: tables by T+30 as data files next to agent.py. Then prompt P6 (sparring bots and the paired harness): shove-bot, fold-bot, station, maniac, random, nit, and self.
- N: prompt P3 (strategy core, with 11_DECISION_CARD.md pasted in) with the variant deltas from 05; the SHOVER detector and the cap logic are part of P3. Then P4 (the other labels and exploits). Keep the strategy in plain functions of plain inputs so the interface layer stays thin.
- N at T+30 and T+45: read the practice-run results and hand histories on the team page (1,000 tables every 10 minutes). Count fold-bots, shove-bots, nits, stations and maniacs by named opponent; note how many tables reached the cap. Set the exploit switch thresholds in 13_EXPLOIT_THE_AI_FIELD.md from the real mix.
- Both at T+40: evaluate v2 against v1, paired, same seats, at least 1,000 tables. Promote only if the difference is positive with the 95 percent interval excluding zero. Check latency under load. Check the eight-copies self-play sanity.

### T+45 to T+50: submit v2

- Pack with poker-agent pack, run check, smoke test 300 tables and the heads-up game in no-bank mode, upload, then select it as active on the team page. Verify the size matches.

### T+50 to T+60: freeze

- Fix only bugs found by the harness. No new features. Final upload by T+55 at the latest. Confirm the team page shows the intended upload as active and the size matches. Then stop.

## T1 to T6 (about 7:08 PM to 8:48 PM)

Each round starts 20 minutes after the previous one and snapshots the active bot at its start. Uploads are every 30 seconds, so the limit is testing, not slots. Rhythm for each 20-minute gap:

1. Minute 0 to 5 (K): team page first. Missed decisions, restarts, memory-cut notes and tracebacks must all be absent. If not, nothing else matters; find the cause, fix, upload. Then standings: our average points, our finish distribution.
2. Minute 0 to 8 (N): download the round's hand-history subset and run P8 with the kit's streaming reader: how many tables reached the cap, how we busted, the archetype mix across named opponents, whether steals got through, whether we paid off shoves. Write three bullet findings.
3. Minute 8 to 14 (both): one change set, driven by the findings, in priority: fix leaks that lose points at every table, then exploit the archetypes actually present, then ICM and cap tuning. Evaluate paired against the current active bot.
4. Minute 14 to 15: upload if better. Never upload after minute 15 of a gap; the test match must pass before the snapshot, and a bot that is still validating at the start is not the active one.
5. Keep the dashboard announcements visible. Watch for practice rounds and use them.

Plan for the content of each submission (adjust to evidence):

- For T2: fix anything T1 revealed; the remaining opponent labels (FOLDBOT, STATION, NIT, MANIAC) and their exploits on if those archetypes are present in numbers; re-check the SHOVER response against what the logs show.
- For T3: ICM-valued push/fold ranges from the P2 solve (or the ICM calculator on all-in decisions); cap behaviour checked against how many tables actually reached hand 200.
- For T4: heads-up and short-handed polish; re-check self-play; tighten exploit triggers if broken bots have disappeared; steal-widening against tables that fold to everything, if the logs show such tables.
- For T5: only evidence-based tuning. The T5 and T6 bots should be nearly identical.
- For T6: no change unless T5 health shows a problem. Confirm the active upload at 8:40 PM and leave it.

## Disputes and the end

- Raise any dispute with a Gamemaster before the next tournament starts; for T6 within five minutes of the results. Hand logs are retained.
- Tie-breaker: announced by the organizer, skill based. Nothing to prepare.
- Shuttle back to Berkeley (Sather Gate) if reserved by email.
- Top 5 go to the Finals on Nov 15 (12:00 to 8:00 PM, San Francisco) with a different variant. Everything in this kit applies again; the field will be stronger and the variant stranger.

## If something goes wrong

- Dashboard down or submission endpoint failing: tell the help desk immediately; the technical lead decides on delays (rule 6.2). Keep working locally.
- Build machine unreachable: everything also runs on a laptop; Python 3.12 and the kit are enough. Only the submission needs the network.
- An upload rejected close to a round start: the previous active upload stays active. Do not panic-upload a second untested file. If a new upload passed but health shows it is worse, re-select the previous upload on the team page.
- The bot shows missed decisions in T1: most likely cause is a cold first call (run a throwaway decision at import), second is GC pauses (gc.disable after setup), third is the ICM calculator or a Monte Carlo on the main path (cache per hand, remove the refinement), fourth is memory parsing that grew (keep the record small). A timeout empties the table's bank, so one slow decision becomes several failed ones; find the spike.
- The variant breaks an assumption nobody anticipated: submit the dumbest legal bot that handles the new decision with a safe default, then think. A legal bot that folds a lot scores more than a brilliant bot that is auto-folded on every decision.
