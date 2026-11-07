# Shared competition results — November 6

Sources are frozen and identified by hashes in the JSON reports. Recheck hashes before applying a result to a newer version. These are direct official-engine internal matches on Python 3.12, not official tournament rounds or subprocess deadline tests.

| Pair | Tables | Points per seat, averaged within tables | Paired difference, approximate 95% CI |
|---|---:|---|---|
| Claude v2 / Codex reveal v1 | 24 | 15.42 / 9.58 | +5.83 [+1.39, +10.27] |
| Claude v2 / Kevin 1 | 24 | 15.42 / 9.58 | +5.83 [−0.17, +11.84] — initially inconclusive |
| Codex reveal v1 / Kevin 1 | 24 | 12.60 / 12.40 | +0.21 [−5.91, +6.32] — inconclusive |
| Claude v2 / Kevin 1, fresh seed | 64 | **16.84 / 8.16** | **+8.67 [+5.57, +11.78]** |

All matches returned zero failed decisions. Claude v1 was excluded because it failed the critical hand cases and its strategy silently raised a TypeError. Claude v2, Kevin 1 and Codex reveal v1 passed all blocking tactical checks.

Claude v2 led the initial pool, but Claude v3 arrived while this was running. A focused regression for the known position bug demonstrates that **v2 folds pocket kings in an unopened small blind after the others fold; v3 continues**. The final gate set therefore blocks v2 as well as v1. This is a definite mistake, even though v2 scored well in the broader sample.

| Newly arrived version | Tables | Points | Paired difference, approximate 95% CI |
|---|---:|---|---|
| Claude v3 / Claude v2 | 24 | 11.77 / 13.23 | −1.46 [−7.16, +4.25] — inconclusive |
| Claude v3 / Kevin 1 | 24 | 18.54 / 6.46 | +12.08 [+7.29, +16.87] |

**Next internal baseline: Claude v3**, which passes the expanded tactical gate. Its short match does not establish a scoring improvement over v2, but it repairs a demonstrated premium-hand fold. This is an internal testing choice, not a tournament upload or a claim about the unknown field. Keep the next iteration short: inspect a few early busts or public-card contradictions, make one change, then compare only that changed version.

Raw per-pair scores, compute latency, street-action counts, sample sizes, seeds and bot-folder hashes are in the adjacent JSON files. The v3 matches used the earlier gate set; `2026-11-06-critical-gates.json` records the expanded nine-case check. Private incident histories are intentionally kept in ignored local run folders.
