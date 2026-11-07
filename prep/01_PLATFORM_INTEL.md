# 01. Platform intel: everything we know about No Limit before the kit drops

Sources: the official rules page (pokerbot.sequoiacap.com/rules.html, fetched Nov 6), the landing page, the "Know Before You Go" email, the Loom setup video description, the public JavaScript bundle of the tournament web app (pokerbot.sequoiacap.com/tournament), the public Poker Gym rehearsal simulator (github.com/mack-dot/poker-gym), and one published competitor write-up (github.com/EthanXu07/poker-bot-overview).

Nothing here is confidential. The variant itself is the only secret and nobody outside the organizers has it.

Update, Nov 6 afternoon: the dashboard's Getting Started page (12_KIT_INTERFACE.md) is now the authority on the Agent interface, uploads (every 30 seconds, every passing upload goes live), the memory model, the time bank, libraries and the kit contents. Where a line below disagrees with 12, 12 wins.

## A. Rules digest (section numbers refer to the official rules)

| Topic | Rule | What it means for us |
|---|---|---|
| Build window | 60 minutes to build a Python bot implementing the provided Agent interface (3.3) | Speed of wiring matters more than cleverness in hour one |
| Starter kit | agent template, local simulator, ICM calculator, payout structure, blind schedule (3.3) | Read all five before typing anything |
| AI tools | Astra and Codex allowed to write, debug, refine during the build; public documentation allowed (3.4). The email adds "All AI tools are allowed" and "Using Codex is not mandatory" | Claude Code or any other assistant is fine |
| Pre-written code | The email says "Pre-written code or bots are not allowed; all code must be written during the event" | Bring knowledge and plans, not code. Prizes are subject to code review (5.4) and DQ can happen after results (6.1) |
| Submissions | the rules page says one bot every five minutes (3.5); the Getting Started page says one upload every 30 seconds and that each upload passing its test match becomes active automatically | Go by the dashboard. Uploads are cheap; a passing upload is live, so test first |
| Sandbox | no network, cannot call OpenAI or any outside service during play (3.6) | Everything the bot needs must be inside the file |
| Deadline | each decision within one millisecond; max file size 100 MB; on error or timeout the bot auto-folds, or checks if checking is available (3.7) | No live Monte Carlo. Precompute. Never throw. A timeout is a fold, and a bot that folds is an ATM for everyone else |
| State | state resets at the start of each table; opponents are anonymized (3.8) | Opponent modeling only within a table (at most 200 hands). No cross-table memory |
| Keep editing | teams may keep editing and submitting after the build phase; the active bot is frozen at the start of each scored tournament; later submissions apply to the next one (4.2) | The real build window is about 160 minutes, not 60. T6 is worth six times T1 |
| Tournaments | six scored tournaments T1 to T6; T1 starts when the build phase ends, then one every 20 minutes (4.1) | About five submission slots between consecutive tournaments |
| Tables | 10,000 eight-bot sit-and-gos per tournament, random seating each iteration (4.3) | 10,000 tables makes results precise. Skill, not luck, decides the ranking |
| Chips and blinds | 2,000 chips each; blinds start 10/20 and rise every 25 hands; a table ends when one bot has all chips or after 200 hands (4.4) | 8 blind levels max. Expect many tables to hit the cap with 2 to 5 survivors |
| Points | by finishing position; distribution varies by variant and is announced at the build phase; eliminated bots get their position's points; at the 200-hand cap, remaining points are split among survivors by ICM (4.5) | Survival and chip share both matter. Read the payout table before deciding how aggressive to be |
| Fillers | if the bot count is not divisible by 8, seats are filled with random copies of submitted bots; fillers earn no points (4.6) | You may sit with a copy of yourself |
| Score | average points per table per tournament; final = T1x1 + T2x2 + T3x3 + T4x4 + T5x5 + T6x6 (4.7) | T4 + T5 + T6 are 71 percent of the final score |
| Ties | tie-breaker challenge set by the organizer, objective and skill based (4.8) | Unknown. Do not plan for it |
| Disputes | before the next scored tournament begins; T6 within 5 minutes of results; hand logs retained (6.3) | If T1 health shows errors, say so to a Gamemaster immediately |
| Prizes | top 5 per regional get $5,000 and go to the Finals; up to 5 wildcards by score; Finals use a different variant, $100k / $50k / $25k (5.1, 5.2) | Regional target: top 5 of the Bay Area field |

## B. What the tournament web app's public client code tells us

The dashboard is a Next.js app. Its client bundle (public, no login needed to download it) contains the data schemas it expects from the server. These are not secrets, but they show what the engine can do, and that is the best available hint about what the variant could be.

### B1. Submission and health pipeline

- Upload: `POST /api/teams/{team}/submissions?filename=...` with the file as body. Statuses: `validating`, `ready`, `rejected`, `cancelled`. Each submission records `check_log`, `rejection_reason`, `sha256`, `size_bytes`, a queue position (`check_position`), and check attempts. Check error codes: `variant_unavailable`, `sandbox_unavailable`, `storage_unavailable`, `worker_timeout`, `worker_error`.
- There is a `cancelSubmission` call and a per-competition `submission_cooldown_seconds` (the five-minute rule).
- The team record has `active_submission_id`, and the team update endpoint accepts `active_submission_id`. That suggests you can re-activate an earlier accepted submission (a rollback) from the team page. Verify in the UI on the day; it is a lifesaver if a new bot turns out broken.
- Per-team, per-round health: `decisions`, `missed`, `restarts`, `gave_up`, `error_log`, plus `latest_decisions`, `latest_missed`, `latest_restarts` on the team view. So the platform counts missed decisions (timeouts), process restarts (crashes) and whether a bot gave up. Check this after T1 before anything else. Missed decisions are folds.
- Each account has an API key ("Your API key lets an assistant or script act as you on every team you are on: read the team and its build machine, register SSH keys and upload bots. It expires 30 days after it is made."). This is what the Codex skill uses to upload. Accounts also carry `ssh_public_keys`, `github_username`, `github_ssh_public_keys` and `starter_kit_downloaded_at`. Teams carry a `machine` (the remote build box), `openai_credits_url` and an `invite_code`.
- Participant navigation: Dashboard, Your team, Rounds, Getting started (`/competitions/{id}/start`), Format (`/competitions/{id}/format`). The Format page is where the variant, payouts and blinds will be shown.
- Announcements are polled every five minutes and shown on the dashboard. Keep the dashboard open.
- Rounds have kind `practice` or `scored`. Practice rounds carry no weight and are labelled "Counts toward: Practice only". If the organizers run a practice round during the build hour, use it as a free test against the real field.
- The leaderboard can be held back (`leaderboard_held`) and there is a `final_revealed_at` field, so expect the T6 result to be revealed with some theater.

### B2. The round rule knobs (this is the variant's shape)

A round's `rules` object can set:

| Knob | Range | Reading |
|---|---|---|
| `players` | int | table size; the rules say 8 but the engine is not hard-wired to 8 |
| `starting_stack` | int | 2,000 per the rules |
| `blinds` | list of up to 100 triples `[small, big, ante]` | the blind schedule, with an ante slot per level. Antes are possible |
| `hands_per_level` | int | 25 per the rules |
| `hand_cap` | int | 200 per the rules |
| `payouts` | list of at most 5 entries, each an int or a pair `[int, int]` | at most five paid places. Places 6 to 8 get nothing. The pair form probably means (points, number of places) or a split |
| `payout_total` | 1 to 100 | points per table, likely 100 |
| `decision_ms` | int | the 1 ms deadline is configurable |
| `time_bank_ms` | int | a time bank exists in the engine. If the Format page shows one, a few extra milliseconds on rare decisions become possible. Do not assume it |
| `icm_luck_correction` with mode `legacy` or `all_in_only` | bool + enum | the UI labels these "ICM luck correction: all-in only" and "Legacy ICM luck correction: all-in and river". Every hand record carries `icm_before` and `icm_after`. If this is on for scoring, all-in results are replaced by their equity-weighted expectation, so the all-in-every-hand bot gets exactly its EV and so do you. Ask a Gamemaster whether scored rounds use it |
| `resampling_continuations` (1 to 8) and `resampling_threshold` (2 to 9) | ints | probably "run the remaining board N times when at least K players are all in" (a run-it-twice style variance reducer). Chip EV unchanged |
| `culling` (contender places, iterations per look, max looks, confidence) | object | the server may stop simulating teams that are provably out of contention for the top places. Does not change strategy |
| `allocation_min_copies` / `allocation_max_copies` (0 to 64) | ints | how many filler copies of a bot can be seated |
| `iterations` (up to 20,000), `iterations_per_job`, `job_stagger_ms`, `worker_tables` | ints | infrastructure |

### B3. The hand-replay frame schema (what the engine can represent)

Each replay frame carries, per seat and per step:

- `boards`: a list of boards, each a list of cards. Plural. Multiple boards are representable.
- `cards`: a list of hole-card lists per seat. The count is not fixed at two.
- `exposed`: per seat, hole cards that are face up.
- `discarded`: per seat, cards that were discarded.
- `stacks`, `bets`, `statuses`, `pot`, `equities` (the engine computes live equities for display), `odds_note`.
- `spread`: a caption, a list of cards, `stakes` as `[{seat, amounts[]}]`, and `picks` as a list of booleans. This looks like a bidding or selection phase: seats put up amounts and pick cards.
- `say`: a line of commentary with a tone from `deal, post, passive, aggressive, allin, fold, hidden, show, street, result`.
- Commentary slots: `open, preflop, flop, turn, river, showdown, handoff, exchange`. An "exchange" slot means a card-exchange phase is a first-class concept.
- Hidden cards render as `??` with a `reveal_hidden` toggle, so some hands have cards hidden from spectators until the end.

Put together with MIT Pokerbots history (2021 Blotto Hold'em: six cards split across three boards; 2024 Auction Hold'em: bid for a third hole card after the flop; 2026: three hole cards, discard one face up after the flop), the engine was clearly built so the variant can involve extra hole cards, discards, exposed cards, multiple boards, bidding, or exchanges. See 05_VARIANT_PLAYBOOK.md for what each does to strategy.

### B4. Variant object

A variant is `{id: slug, title, rules: text}` and is fetched from `/api/competitions/{id}/variant` once revealed. So the reveal will be prose plus the knob values above. Read the prose twice. Prose is where the twist lives.

## C. The starter kit: what to pin down in the first seven minutes

The rules promise an agent template, a local simulator, an ICM calculator, a payout structure and a blind schedule. Everything else is unknown until the drop. The Poker Gym authors list the five things that always differ between kits, and they are right:

1. Card spelling: `"As"` vs `"AS"` vs `"10h"` vs integers vs tuples.
2. Raise semantics: raise-to (total) vs raise-by (increment) vs "amount to add to the pot".
3. Whether `stack` includes the chips already bet this street or this hand.
4. How folded or busted players appear (status strings, booleans, or absence from the list).
5. Whether the action history has streets, and whether it exists at all.

Add these:

6. Deadline semantics: is import time counted, is the first `act` call counted, wall clock or CPU time, is there a time bank.
7. Allowed imports: standard library only? Is `numpy` present in the sandbox? Assume no.
8. Submission shape: one `.py` file or a zip; the entry point name; whether the kit ships a local checker. Run the checker on the kit's own template first.
9. What the bot sees: hand number, blind level, number of players left, stacks of everyone, the button, who is all in, showdown cards. Hand number and stacks are needed for the ICM layer. If showdown cards are not visible, the bluff detector has no data.
10. What the ICM calculator takes and returns (stacks + payouts, presumably), and how fast it is. Eight-player Malmuth-Harville in pure Python can exceed 1 ms if called every decision. Cache it per hand.
11. The payout table and the full blind schedule. Copy both into the bot as constants after confirming they match the Format page.
12. Any variant-specific action (discard, bid, pick, exchange) and its legal values.

## D. Field intel: who else is building

- At least one competitor (EthanXu07) has published a write-up of a bot built ahead of the event: a decision-tree model with evolution-tuned thresholds, precomputed equity tables keyed by hand class and opponent count, within-table opponent modeling (VPIP, PFR, aggression, fold-to-bet, showdown bluffs), ICM-aware risk aversion that goes to zero heads-up, around 0.05 ms per decision, one 165 KB standard-library file. Whether that team follows the email's rule is their business. The point for us is that the top of the field will look like this by T6: tight-aggressive, ICM aware, opponent aware, fast.
- Poker Gym (mack-dot) is public and includes sparring bots named `tag`, `lag`, `shortstack`, `icm`, `adaptive`, a bundler that produces a single file, and a 60-minute runbook whose first instruction is "submit `tag` wrapped by the adapter". Expect several teams to submit a TAG-style bot inside 25 minutes.
- Most teams will use Codex with default prompting. Expect the default output: a tight-ish opening chart, pot-odds calls postflop, fixed bet sizes, and bugs in raise semantics or all-in handling that turn into automatic folds. Early tournaments will contain accidental fold-bots. By T4 to T6 most of those are fixed.
- The MIT Pokerbots community lore includes a team that went all-in on every single hand. Someone will try it here for T1 because it takes two minutes to write. Against correct callers it loses chips on average; against ICM-tight tables it wins blinds for a while. 04_OPPONENT_FIELD_AND_COUNTERS.md covers the response.

## E. Logistics facts from the email

- Register at pokerbot.sequoiacap.com/tournament with the application email (Nicholas: nchen06@berkeley.edu, Kevin: kwang3170@berkeley.edu). Claim OpenAI credits after registering. Set up the remote computer from the landing page. "Use Sol for set-up to conserve credits" (Sol is GPT-6.1 Sol, the cheaper and faster coding model; Astra is GPT-6 Astra, the flagship. The rules name both as the permitted OpenAI tools).
- Loom setup guide (https://www.loom.com/share/5e9d1c77a8814954937b01c9ced04204): sign in, find Getting Started, claim credits on platform.openai.com and create an API key (30-day expiry in the example), open the Codex app, paste the key, download the skill, connect through Codex Desktop Settings > Connections > NoLimitBuild. A practice site exists at practice.pokerbot.sequoiacap.com/tournament.
- Reply to the email to confirm set up and to reserve the shuttle back to Berkeley (Sather Gate).
- Help desk opens 4:30 PM. Check-in and dinner 5:00 to 6:00 (outside, bring a jacket). Kickoff and variant reveal at 6:00 sharp. Sequoia HQ, 2800 Sand Hill Road, Suite 101, Menlo Park. Government ID required.
