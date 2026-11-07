# Shared competition results — November 6

Sources are frozen and identified by hashes in the JSON reports. Recheck hashes before applying a result to a newer version. These are direct official-engine internal matches on Python 3.12, not official tournament rounds or subprocess deadline tests.

| Pair | Tables | Points per seat, averaged within tables | Paired difference, approximate 95% CI |
|---|---:|---|---|
| Claude v2 / Codex reveal v1 | 24 | 15.42 / 9.58 | +5.83 [+1.39, +10.27] |
| Claude v2 / Kevin 1 | 24 | 15.42 / 9.58 | +5.83 [−0.17, +11.84] — initially inconclusive |
| Codex reveal v1 / Kevin 1 | 24 | 12.60 / 12.40 | +0.21 [−5.91, +6.32] — inconclusive |
| Claude v2 / Kevin 1, fresh seed | 64 | **16.84 / 8.16** | **+8.67 [+5.57, +11.78]** |

All matches returned zero failed decisions. Claude v1 was excluded because it failed the critical hand cases and its strategy silently raised a TypeError. Claude v2, Kevin 1 and Codex reveal v1 passed all blocking tactical checks.

**Current internal lead: Claude v2.** Use that exact version as the next challenger baseline. This does not establish superiority against the unknown tournament field. Keep the next iteration short: inspect a few early busts or public-card contradictions, make one change, then compare only that changed version.

Raw per-pair scores, compute latency, street-action counts, sample sizes, seeds and bot-folder hashes are in `2026-11-06-initial.json` and `2026-11-06-confirm.json`. Private incident histories are intentionally kept in ignored local run folders.
