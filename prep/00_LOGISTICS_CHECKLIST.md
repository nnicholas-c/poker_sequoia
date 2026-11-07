# 00. Logistics checklist for Friday, Nov 6

## Before you leave Berkeley (do these in the morning)

- [ ] Register the team at pokerbot.sequoiacap.com/tournament. Sign in with the application email (Nicholas: nchen06@berkeley.edu; Kevin: kwang3170@berkeley.edu). Both of you must register; teams are locked. Pick the team name together.
- [ ] Claim the OpenAI credits from the Getting Started page after registering. On platform.openai.com create an API key (the setup video's example expires in 30 days). Credits are not a constraint for us, so model choice is about speed and quality only (see 07).
- [ ] Build box. Each of you: `ssh-keygen -t ed25519` (Enter at every prompt), copy `~/.ssh/id_ed25519.pub`, add it under your name > Account settings > SSH keys (live in 30 seconds). Then Your team > Build box tab > copy the `ssh ubuntu@<address>` command and try it; before the opening time it prints the opening time and disconnects, which still proves the key works. Add the alias to `~/.ssh/config` (Host no-limit-2026-build, HostName <address>, User ubuntu, IdentityFile ~/.ssh/id_ed25519, IdentitiesOnly yes, ServerAliveInterval 30). Or let a terminal agent do all of it with the setup skill: `curl -fsSL --create-dirs -o ~/.claude/skills/no-limit-2026-setup/SKILL.md https://pokerbot.sequoiacap.com/tournament/no-limit-2026-setup/SKILL.md` then `/no-limit-2026-setup` in Claude Code (or `~/.agents/skills/...` and `$no-limit-2026-setup` in Codex) with an API key from Settings > API keys. Run it again after the announcement to put the kit on the box. Loom walkthrough: https://www.loom.com/share/5e9d1c77a8814954937b01c9ced04204. The email says to use "Sol" for setup to conserve credits. Sol is GPT-6.1 Sol, OpenAI's faster coding model; Astra is GPT-6 Astra, the flagship. With credits not a constraint, use Astra for every design-heavy prompt (P0, P3, P4, P5) and Sol only where latency matters more than reasoning (quick fixes, packaging, P7). Keep Claude Code as the second assistant so the two of you never wait on one queue.
- [ ] Codex on the box: `ssh` in, `codex login --device-auth`, open the printed address in your browser, enter the code, sign in with the team's ChatGPT account; `codex login status` confirms. One sign-in per box, last one wins. Codex app: Settings > Connections > add no-limit-2026-build with project folder ~/work. Without the app: `tmux new-session -A -s no-limit-2026` then `codex` in ~/work. If `codex: command not found`, the box is still installing: `cloud-init status --wait`.
- [ ] Create the platform API key from the dashboard settings ("API keys"). It lets a script or assistant read the team, register SSH keys and upload bots. It expires in 30 days. Save it in a password manager, not in a file that could end up inside a submission (rule 8.4 forbids credentials in submissions).
- [ ] Reply to the Know Before You Go email: confirm set up, and reserve two shuttle seats back to Berkeley (Sather Gate).
- [ ] Sign in to the practice site (practice.pokerbot.sequoiacap.com/tournament) if it is open to you and look at the Getting Started and Format pages. Check whether a practice variant or a sample kit is available there; if so, read the agent template now.
- [ ] Both laptops: Python 3.12 installed and working offline, `venv`, git, OpenSSH, a terminal, the Codex app signed in, Claude Code signed in (all AI tools are allowed), this kit downloaded for offline reading. Outbound port 22 must work on the venue network; test the hotspot as the fallback.
- [ ] Run the rehearsal in 08_REHEARSAL_TODAY.md (about two hours). Leave the rehearsal code at home.
- [ ] Phone hotspot tested as a backup network. Venue wifi with a hundred people uploading is a risk.

## What to bring

- [ ] Government-issued ID (or a photo of it) for security check-in
- [ ] Fully charged laptop plus power bank plus charger (outlets are limited)
- [ ] A light jacket (dinner is outside)
- [ ] Earbuds (the room will be loud during the build)
- [ ] A printed or offline copy of 06_EVENT_RUNBOOK.md and 07_AI_PROMPT_PACK.md
- [ ] Water, a snack for 7:30 PM

## Timeline

| Time | What |
|---|---|
| 2:45 PM | Leave Berkeley. Friday traffic to Sand Hill Road is 90 minutes or more |
| 4:30 PM | Help desk opens. Arrive by now. Sequoia HQ, 2800 Sand Hill Road, Suite 101, Menlo Park. Rideshare destination "Sequoia Capital" |
| 4:30 to 5:00 | Verify dashboard, build machine, API key, Codex connection on both laptops. Ask the two questions in 06 |
| 5:00 to 6:00 | Check-in, dinner, meet the Citadel Securities and OpenAI representatives |
| 6:00 | Kickoff and variant reveal. Build phase starts right after |
| about 7:08 | T1 starts (end of build). Then T2 7:28, T3 7:48, T4 8:08, T5 8:28, T6 8:48, all approximate |
| 9:00 | Event ends. Shuttles to Berkeley and Stanford |

## Rules to remember in one breath

Written at the event, Python, `act(state, memory)` returning an Action and bytes, one millisecond per decision with a 100 ms per-table bank that does not refill, no network, one upload per 30 seconds and every passing upload goes live, state only in the memory bytes, six rounds weighted 1 to 6, thousands of eight-bot sit-and-gos each, 2,000 chips, blinds up every 25 hands, 200-hand cap with ICM split, payouts read from state.config (50/30/20 by default, three places), top five teams in the room go to the Finals for the $100k variant.
