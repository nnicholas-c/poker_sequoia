# Empty Bluffer primary v1

**Primary objective: maximize expected Empty Bluffer awards per scored table.** Tournament points, top-three finishes and first places are secondary diagnostics. The selected file is the best prize earner among the tested candidates, not a proven global optimum or a guaranteed prize winner.

Use `agent_empty_bluffer_primary_v1.py` or its ZIP, which contains the same source named `agent.py`. No tournament upload was performed.

## Fresh results

256 paired scenarios per version, with the same designated hero seat, table seed and seven-opponent lineup. Half use each of two synthetic opponent profiles. These are locally available policies, not the live rivals’ code. Awards are counted from actual official-engine prize events, once per qualifying hand.

| Version | Empty Bluffer awards | Awards/table | Points | Top three | First | Early bust |
|---|---:|---:|---:|---:|---:|---:|
| Empty Bluffer primary v1 | **940** | 3.672 | 10.31 | 32.4% | 9.4% | 10.5% |
| Supplied dedicated NC bluffer | **162** | 0.633 | 14.77 | 49.2% | 10.9% | 6.6% |
| Prior survival/prize fusion | **67** | 0.262 | 14.65 | 45.7% | 13.3% | 8.6% |

The selected version earned **5.80×** the dedicated bluffer’s awards. Paired gain: **3.039 awards/table**, approximate 95% interval **[2.539, 3.539]**.
Average tournament points changed by **-4.45**, interval [-7.04, -1.86]. This is a material tournament-performance sacrifice, selected deliberately because prize count is now primary.

Prize gains appeared in both profiles:
- balanced: 3.602 versus 0.648 awards/table.
- pressure: 3.742 versus 0.617 awards/table.

## What changed

- **Get to qualifying flops.** With at least 12 BB and a 2–5 among the three cards, buy inexpensive unopened flops rather than always raising and winning before selection. Preflop wins do not count for Empty Bluffer. Cheap single-raise calls are limited to 2.5 BB and 8% of stack, with an additional starting-hand score gate; all-in raisers and known shovers still to act are excluded from this extra entry rule.
- **Retain the low card more aggressively.** Choose the highest-scoring qualifying keep within 0.30 of the best heuristic score. This intentionally allows substantially more hand-strength sacrifice than the balanced fusion. It is a heuristic-score difference, not a measured 30-point equity guarantee. Do not downgrade an existing class-4-or-better hand to a lower class.
- **Pursue no-showdown wins.** With a low card exposed and no bet to call, try a qualifying bet more frequently: heads-up most aggressively, less often with two or three opponents. Reduce weak later-street attempts and attempts against recognized calling stations. Skip the extra prize bet if any opponent is all-in, since the target award requires winning without showdown.
- **Keep a betting bankroll.** Extra prize bets are normally 40% of pot for weaker hands or 60% for stronger ones, at least the legal minimum and one BB, capped at 20% of remaining stack and strictly below an all-in raise. Normal strategy may make later decisions or legitimate shoves; this is a limit on the extra prize attempt, not on total possible hand loss.
- **Retain deterministic correctness fixes.** Correct flush-card ordering, board-straight comparisons, actual kicker evaluation, and the public river-loss check are ported to the dedicated-bluffer/V6 base. The previous survival-first phase schedule is not the policy objective here.

The underlying rules require exposing a retained 2–5, betting/raising after the reveal, and winning without showdown. A value hand qualifies; a pure bluff is not required. Organizers sum raw awards across scored rounds without tournament weights. These tests do not measure rivals’ cumulative prize counts or establish an official prize ranking.

## Candidate selection and validation

Three candidates were compared against the supplied bluffer on 128 development scenarios: wider low-card retention, wider low-card opens, and cheap low-card limps. Development awards/table were 0.891, 2.930, and 4.773 respectively, versus 0.766 for the supplied bluffer. The cheap-flop candidate was selected before the 256 fresh scenarios. No changes used the fresh results. Rejected candidates are archived with the benchmark for audit/reproduction, not promoted as alternative recommendations.

- Seven existing blocking tactical cases and three public-river cases passed.
- Focused tests verify cheap qualifying entry, rejection of an expensive weak-hand chase, low-card retention, protection of a made set, and legal selections.
- Official archive validation passed; the ZIP contains exactly the tested `agent.py`.
- Sixteen official subprocess tables completed with zero failed decisions across all eight seats. Larger paired comparisons ran in-process and are not subprocess-deadline guarantees.
- Per-table results, seeds, source/dependency hashes, paired confidence intervals, Shover counts and pooled Calling Station ratios are retained in JSON. Shover and Calling Station are not the optimization target.

Agent SHA-256: `a95feff4c15af1c6ca9bf7a71c318c5d9da8811ec034b82c3519d36e7f796837`.

Shared source: `bots/codex_empty_bluffer_primary_v1/agent.py`. Reproduce the held-out comparisons with `python arena/prize_primary_eval.py holdout 128`; run `development 64` to compare archived candidates. Each run writes a new results folder under `arena/runs/`.
