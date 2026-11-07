# V6 tournament review: the gap remains

V6 averaged **15.35 points** and finished first in **146 of 1,001 scored tables (14.6%)** in the supplied export. The filename says first-1000, but the contents contain 1,009 unique table records, including eight Double G filler appearances. All figures here exclude those filler appearances. This is the user-identified V6 round, tournament `3e3dcc02-ca4f-48c5-9acb-6c0e3a32c10e`.

The earlier recommendation selected the strongest provisional internal baseline among the supplied files. It did not demonstrate superiority over the tournament field. This result confirms that limitation.

## Where the observed leaders differ

These are the three highest averages among opponents in this export, not an independently retrieved full-round leaderboard. Each appears only at a subset of our tables, so opponent means are conditional and have much smaller samples.

| Team | Observed scored tables | Mean points | Firsts |
|---|---:|---:|---:|
| avalon | 49 | 26.12 | 22 |
| WAYS-ER TEAM | 58 | 25.52 | 20 |
| AZ | 66 | 22.73 | 23 |
| Double G / user-identified V6 | 1,001 | 15.35 | 146 |

Unopened, unlimped first actions with 5–8 players at the start of the hand:

| Team | Button raise | Small-blind raise |
|---|---:|---:|
| avalon | 37.9% | 50.5% |
| WAYS-ER TEAM | 66.5% | 90.1% |
| AZ | 56.1% | 73.8% |
| Double G | 60.2% | 61.5% |

Our button stealing is already substantial. Raising it blindly is not an explanation for the entire gap: avalon opens the button less often than us. Their other decisions, opponent mix, and cards matter. The earlier idea that all leaders share one aggression profile does not fit this sample.

A sharper structural difference is stack depth. Double G made **zero open shoves in 3,799 unopened first-action opportunities at >12–16 BB**, and zero in 3,393 at >16–20 BB. At >12–16 BB, AZ shoved 37/130 opportunities (28.5%); WAYS-ER TEAM 16/173 (9.2%); avalon 6/69 (8.7%). These observations motivate an experiment, not those exact ranges for our bot.

## The concrete decision problem

The source's shared hand classifier promotes a pocket pair above the board's paired rank but below a higher board card into class 2, the same class used for top pair. Example: **77 on T44Q** receives 53% turn equity before opponent adjustments.

A local reconstruction of an observed large turn call reproduces V6 calling and the challenger folding. This is a heuristic correction; 36% is not a computed range-equity proof. The diagnostic starts with fresh opponent memory and tests call versus fold, so it does not reproduce the full original process state. Private hand identifiers and events remain local.

The review found eight large calls across seven hands with the same pocket-pair classification pattern. Some calls can still be justified by price or opponent behavior. Their eventual losses alone do not establish the correct action.

The classification is shared with discard selection, so the challenger can also change which two cards it keeps on paired flops. That is a material scope effect, not just a turn-call adjustment.

Other focused findings:
- **Zero automatic fallback decisions** in scored own appearances.
- **30 first-20-hand busts / 1,001 tables**, about 3.0%. Blanket early survival restrictions are not the obvious first fix.
- Only **one class-5-or-better fold**: trips facing a 2,271 bet into a 100 pot with several opponents still involved. It is a review case, not a proven bad fold. No full-house-or-better fold appeared in this scan.
- **1,593 of 2,859 flop-call hands (55.7%)** later ended in a turn/river fold. This now counts the same hands, rather than comparing unrelated street denominators. It identifies a costly sequence worth reviewing; it still does not prove every initial call was wrong.

## What was built and tested

The frozen baseline is the earlier supplied `agent_v6.py`, SHA-256 `8afacbfca1ee35a5a23033db086272a9882c99d1482a63848444910acc8dcbb5`.

Three isolated experiments were tested:
1. Paired-board pocket-pair classification correction.
2. Existing late-position push ranges extended from 11 to 16 BB, only in unopened/unlimped pots and outside the exact payout bubble. No extra early-position shove range and no 20–35 BB shoves.
3. Both changes combined, saved as `agent_challenger.py` (SHA-256 `2e0080ea59d1f9f30a3e04185423650675b5c1ba3fd0bb418d953a263f4fc80e`).

| Test | Tables | V6 points | Challenger points | Challenger minus V6, approximate 95% interval |
|---|---:|---:|---:|---|
| Classification-only triage | 32 | 15.16 | 9.84 | −5.31 [−9.91, −0.72] |
| Late-push-only triage | 32 | 13.91 | 11.09 | −2.81 [−8.34, +2.72] |
| Combined triage | 32 | 10.39 | 14.61 | +4.22 [−0.78, +9.22] |
| Combined, fresh direct holdout | 128 | 12.91 | 12.09 | −0.82 [−3.32, +1.68] |
| Combined, mixed fixture pool | 96 | 17.66 | 18.80 | +1.15 [−2.90, +5.20] |

Direct comparisons use four copies of each version; mixed tables use two copies each plus nit, TAG, station, and maniac fixtures. Confidence intervals use tables as the independent unit. These fixtures are not the leaders' actual bots. Different seeds and resulting histories mean the isolated experiments do not establish a causal interaction between the two changes.

All candidates passed seven existing blocking tactical cases. Direct matches recorded zero failed decisions. The combined file passed the official static submission checker; a separate 12-table official subprocess smoke test returned zero failed decisions for all eight seats. That small smoke test validates execution only.

**Decision: keep this as an experimental challenger. Do not claim a winning reform or replace the incumbent based on these results.** The first triage gain disappeared in the fresh direct test. No tournament upload was made.

## Version identity matters

While this review ran, GitHub gained a different file named `bots/nc_v6/agent.py`, SHA-256 `85e6f38dec5c67814b71a8c0bf94dc340e81f4638d34f9fa82b2f1b8317b21e9`, in commit `1b1b831`. It is based on the supplied V5 family and adds 13–20 BB open shoves. It is **not** the frozen downloaded V6 used in the comparisons above. The hand export itself does not include the uploaded source hash. Treat the user's version attribution as the round label; do not attach these test scores to the newer nc_v6 just because the names match.

Evidence: `focused-analysis.json`, `triage.json`, `holdout.json`, `mixed.json`, and `process-check.json`. Private hand-level review data remain local.
