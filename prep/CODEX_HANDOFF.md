# Handoff to Codex (or Claude Code): setup now, build at 6 PM

Paste the block in section 1 as the first message to Codex, with this folder as its working directory. Sections 2 to 4 are what it will do and in what order; read them once so you can tell when it is off track.

## 1. First message to Codex (paste verbatim)

```
You are helping Team Nicholas + Kevin prepare for the No Limit poker-bot tournament (Sequoia, Citadel Securities, OpenAI), Bay Area regional, tonight 5 to 9 PM PT, Sequoia HQ Menlo Park. This folder is our prep kit. Read README.md first, then 12_KIT_INTERFACE.md (section 0 has the Format page facts: 8 players, 2,000 chips, blinds 10/20 rising every 20 hands, 250-hand cap, payouts 50/30/20, practice runs every 10 minutes during the build, countback tiebreak), 13_EXPLOIT_THE_AI_FIELD.md, 06_EVENT_RUNBOOK.md, 07_AI_PROMPT_PACK.md, 11_DECISION_CARD.md, 03_STRATEGY_PLAYBOOK.md, 04_OPPONENT_FIELD_AND_COUNTERS.md, 05_VARIANT_PLAYBOOK.md and 10_RESEARCH_FINDINGS.md. The rest is reference. We are not building a generic bot: 13 describes the generic bot every other team's assistant will produce and how we exploit it; our bot must implement those switches and stay inside the bounds in its section 4.

Hard rule from the organizers: all bot code must be written during the event. Until the variant is announced at 6:00 PM PT, do NOT write any bot code, tables, generators, harnesses or helpers. Right now your job is setup, reading, and planning.

Do these now, in order, and report after each:
1. Download the organizers' setup skill from https://pokerbot.sequoiacap.com/tournament/no-limit-2026-setup/SKILL.md (save it under ~/.agents/skills/no-limit-2026-setup/SKILL.md, or ~/.claude/skills/... if you are Claude Code) and follow it. It needs a platform API key: ask me for it, do not guess. It registers my SSH key, writes the SSH alias no-limit-2026-build, connects the Codex app, and later puts the kit on the build box. Choose the remote build box, not local-only.
2. Confirm the build box: `ssh no-limit-2026-build` should either give a shell as ubuntu or print the opening time (UTC) and disconnect; both mean the key works. If "Address not available yet", say so and move on. If codex is installed on the box, run `codex login status` there and tell me whether I need to do `codex login --device-auth` myself (I will do that step; you do not sign in for me).
3. Using the API access the skill gives you, pull everything readable about the competition (id 5f8be52b-8038-4c43-a0fa-971abcacec1b, team id bef5bc9d-5d26-4237-8c39-31c01f153f69, build box poker-production-team-114 at 44.211.129.102): team record, competition details, variant (empty until 6 PM), rounds, announcements. The Format page facts are already in 12_KIT_INTERFACE.md section 0; confirm them against the API and note any difference in dashboard/SUMMARY.md.
4. Prepare the local machine: Python 3.12 available, `python3.12 -m venv` works, git and OpenSSH work, outbound port 22 works on this network. Do not pip install anything yet (the kit's requirements.txt pins exact versions and we install into a fresh venv at 6 PM).
5. Write BUILD_HOUR_BRIEF.md in this folder: one page, in build order, of what we will do from the announcement onward, taken from 06_EVENT_RUNBOOK.md and 07_AI_PROMPT_PACK.md, with the constraints block from 07 copied verbatim at the top, the exploit switch table from 13_EXPLOIT_THE_AI_FIELD.md section 3 and the self-limits from its section 4, a checklist of the facts to confirm in the first seven minutes from 12_KIT_INTERFACE.md, and the variant triage from 05_VARIANT_PLAYBOOK.md. Include the practice-run reading points (minute 30 and minute 45) and the rule that an upload must be selected as active on the team page.
6. Read 14_ADAPTIVE_BOT_BUILD_PLAN.md twice, then 15_FINAL_AUDIT_ADDENDA.md (seven additions in order of value per minute; take them in order after the base plan, each only after the previous upload passed its gates). It is the specification you will implement tonight, module by module, in the order of its section 1, with the memory layout in section 2, the event parser in section 3, the labels in section 4, the switch table in section 5, the anti-adaptive layer in section 6, the late game in section 7, the harness gates in section 8 and the variant hooks in section 9. Repeat its section 1 table back to me with your estimate of minutes per module.
7. Read 16_ROUND_LOOP.md: the between-rounds protocol you will run after every practice run and every scored round (health, read the round, one gated change set, upload, activate, ledger). Create LEDGER.md now with a header.
8. Stop and wait. At 6:00 PM I will paste the variant announcement and tell you to run the setup skill again to pull the kit onto the build box. From then on we follow the runbook: P0 reconnaissance, then v1 by minute 20, and the kit folder becomes your working directory.

Constraints for everything you write tonight (repeat them back to me now so I know you have them):
- Interface: class Agent(poker_agent_sdk.Agent) with act(self, state, memory) -> (Action, bytes). Choose only from state.legal_actions; raise_to totals are ints clamped into [min_amount, max_amount]; when neither check nor fold is offered use Action(first.kind, first.min_amount).
- Nothing persists between calls except the memory bytes; all per-table state goes in a small checksummed struct record parsed defensively; globals are read-only tables built at import; no files, no threads, no network, no prints.
- 1 ms per decision, 100 ms per-table bank that does not refill and is emptied by a timeout; the upload test has no bank. Budget p99.9 under 0.3 ms. Precompute at import, run one throwaway decision at import, gc.disable() after setup.
- Libraries: standard library, poker_agent_sdk, poker_agent_protocol, eval7, NumPy at import only. Never import poker_engine or pokerkit in anything that goes into the upload.
- Read payouts, blinds, hand cap and time bank from state.config every table.
- Uploads every 30 seconds and every passing upload goes live: nothing is uploaded that has not passed poker-agent check, 300 local tables, and the heads-up check_or_fold game with zero failed decisions.
```

## 2. What Codex does before 6 PM (and what you do yourself)

Codex: downloads and runs the setup skill, registers your SSH key, writes the SSH alias, connects the Codex app to the box, pulls the dashboard data it can reach, writes dashboard/SUMMARY.md and BUILD_HOUR_BRIEF.md.

You, by hand, because an assistant should not do these for you:
- Give Codex the platform API key when it asks (Settings > API keys on the dashboard). Do not paste it into any file in this folder.
- `codex login --device-auth` on the build box (open the printed address, enter the code, sign in with the team's ChatGPT account). One sign-in per box; the last one wins, so agree with Kevin whose account it is.
- Kevin repeats the SSH-key step from his own laptop with his own key (five keys per account; each member adds their own under Account settings > SSH keys).
- Reply to the organizers' email to confirm setup and reserve the shuttle.
- If Codex cannot fetch the Format page through the API, open it in the browser where you are signed in, select all, and paste the text to Codex (and to me, if you want the kit updated).

## 3. What Codex does at 6 PM

1. You paste the variant announcement text and RULES.md. Codex runs the setup skill again to put the kit on the build box, and clones or copies it locally too.
2. Codex switches its working directory to the kit folder (so it reads the kit's AGENTS.md) and runs P0 from 07_AI_PROMPT_PACK.md.
3. The runbook in 06_EVENT_RUNBOOK.md takes over: v1 uploaded by minute 20, v2 by minute 45 to 50, then one upload per 20-minute gap between rounds, each gated by the harness.
4. Between rounds: download the round's hand-history subset from the team page and run P8.

## 4. Reading the dashboard pages

The organizers' setup skill is built around the platform API key ("read the team and its build machine, register SSH keys and upload bots"). The competition's public JavaScript names these endpoints, which the skill will document properly: `/api/competitions/{id}`, `/api/competitions/{id}/variant`, `/api/teams/{id}`, `/api/teams/{id}/submissions`, rounds and announcements under the competition. Codex should try those first with the key. Anything that turns out to be browser-only, you paste. Do not give any assistant your dashboard password or sign-in code.
