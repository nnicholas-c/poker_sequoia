# Shared internal league

Put every new version in `bots/<owner>_<version>/agent.py`, with its required local assets beside it. Keep old versions immutable. Pull teammates' changes before starting a comparison. The league discovers these folders automatically; no registration service or tournament API key is needed.

The repository's `arch_*` folders are shared arena helper opponents, not standalone contenders; they are excluded here. Use the existing `arena/arena.py` for mixed-field checks with those helpers. The team's `arena/mistakes.py` and `arena/busts.py` complement the small incident samples from the league.

```sh
git pull --ff-only
# Use the project's Python 3.12 virtualenv.
python arena/league.py --checks-only
python arena/league.py --tables 24

# The fast iteration path: only the changed bot plays the other selected versions.
python arena/league.py --bots claude_v2 kevin1 codex_reveal_v1 --focus claude_v2 --tables 24
```

The loop is **one demonstrated mistake → one new version → focused checks → short internal match**. Fix monster folds, public-card contradictions, silent exceptions and avoidable large commitments first. Ordinary losing hands and early busts are review leads, not automatic bugs.

`critical_cases.json` contains seven blocking tactical cases: a straight flush, four quad hands, the river where the lone opponent's exposed card proves a better hand, and pocket kings in an unopened small blind after the other players fold. The team policy for the river case is to fold instead of accidentally value-raising a dead hand; this is not a claim that every intentional zero-equity bluff is impossible. A cheap set and a weak-two-pair bubble commitment are review-only cases. These reconstruct decision-time information with fresh prior memory. No future hidden cards are supplied.

Every bot runs its real `Agent.act()` wrapper. A separate traced call reports swallowed strategy exceptions; its slower timing and action are not used to grade deadline-sensitive choices. Failed blocking checks exclude a bot from matches and remain visible in the report. Custom strategy exceptions intentionally handled inside a strategy function may require reviewing the trace. The checks are focused regressions, not exhaustive proof of correctness.

Each pairing plays eight-seat tables with four copies per version, shuffled seats and fresh table memory. Points are averaged across a version's four copies **inside each table** before estimating uncertainty. Match seeds are reproducible; the default seed is fresh. Avoid tuning to a fixed seed. `--focus` avoids rerunning unchanged pairs.

Reports go to ignored `arena/runs/<run-id>/`: `SUMMARY.md`, `report.json`, the exact frozen bot folders, and `incidents.jsonl`. All bot-folder files are hashed, including lookup tables. A live file edit during the run does not change the snapshot; the report flags changed sources. Results must be identified by hashes, not just “latest.” Check console progress after each pairing. A failing focused candidate exits with status 2.

The match reports strategy outcomes, failed replies, street actions, direct computation latency and early busts. It retains only a few failed states and early busts with the bot's last decision states, so the next review stays small. Runs remain local because they can contain private cards. Publish selected summary metrics with the candidate commit rather than committing all histories.

**A short-match winner is a lead, not an automatic champion.** Overlapping/zero-crossing intervals are inconclusive. Confidence intervals are approximate, with no multiple-comparison correction. Before replacing the agreed champion, repeat only the promising challenger on a fresh seed, include a mixed table in the existing arena, and run the organizers' subprocess checker. Direct matches do not enforce transport deadlines or prove protection from swallowed exceptions outside the tactical cases. In-process modules share a Python process; process tests remain the release authority.

The league never edits bot source, updates a champion, pushes a commit, trains shared cross-table memory, or uploads to the tournament. Each human/assistant iterates its own version from the small incident list. Kevin remains the tournament release owner. Bot improvement here means code/policy iteration; match results do not automatically train neural-network weights.

Useful final checks with the existing tools:

```sh
poker-agent check bots/YOUR_VERSION/agent.py
python arena/arena.py bots/YOUR_VERSION bots/CHAMPION --fill kit/examples/check_or_fold --tables 40
# Real subprocesses; repeat the folders to get a 4-vs-4 full table.
poker-agent play bots/YOUR_VERSION bots/YOUR_VERSION bots/YOUR_VERSION bots/YOUR_VERSION bots/CHAMPION bots/CHAMPION bots/CHAMPION bots/CHAMPION --tables 20
```

The folder `codex_reveal_v1` is an archived experimental baseline, not a recommended champion: it lost a larger comparison to repaired Claude v1. Keeping it in the internal pool makes regressions and relative improvements measurable without claiming it is the best bot.
