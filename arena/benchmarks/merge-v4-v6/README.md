# Next-round decision

**Recommended existing version: V6 (`agent_best.py`, identical to your supplied V6).** It had the strongest fresh internal results among the original files and the custom merges, but the uncertainty intervals overlap. No merge has established a reliable improvement over it. `agent_reform_v7.py` is the best developed Team-72-inspired merged challenger, not a proven replacement. Nothing was uploaded to the tournament.

## What Team 72 does that we can adapt

Your first-1,000 download contains 1,000 scored Double G tables plus 15 filler tables. Team 72 appears in **57** of the scored tables. These observations cannot recover its hidden ranges or discard policy, establish its full-round rank, or predict a top-ten finish.

Compare the same stage: hands starting with 5–8 players. Opening rates below use only first actions in unopened, unlimped pots.

| Metric | Team 72 | Double G |
|---|---:|---:|
| Voluntary preflop participation | 28.9% (1,120/3,877) | 24.6% (16,034/65,196) |
| Preflop raise | 22.7% | 18.0% |
| Uncontested small-blind open | **93.1% (135/145)** | **46.0% (960/2,086)** |
| Button open | 67.4% (126/187) | 49.9% (1,891/3,789) |
| Cutoff open | 43.7% (146/334) | 35.6% (2,006/5,641) |
| Median opening size, all stages | 2.25 BB | 2.50 BB |
| Median flop bet when not facing a bet, all stages | 75% pot | 50% pot |

The clearest transferable hypothesis is **collect more uncontested late-position pots at a lower price**, while retaining our strong-hand and public-card checks. The larger postflop bets are an observation, not evidence that every continuation bet should become 75% pot: their cards and opponent ranges may differ.

Our latest scored sample has **0 automatic fallbacks, 0 full-house-or-better folds, and 48 first-20-hand busts out of 1,000 tables**. We scored 17.27 in this sample. Team 72 averaged 19.82 in its 57 observed tables; that conditional sample is not a full-round leaderboard comparison. The export does not identify the uploaded source, so these statistics are not attributed to either supplied file by guesswork.

Some early losses are ordinary poker outcomes: a set losing after getting all-in, kings losing to aces, or a king-high flush losing to an ace-high flush. Those examples do not justify folding every strong hand or adding blanket survival penalties. First inspect whether the decision was unreasonable using the cards visible at the time.

## The merge and reform

V6 already contains the V4 base. Its additions widen steals, tighten cold calls, lower two-pair estimates, add an early deep-stack call premium, and mix exposures.

`agent_merged_v4_v6.py` keeps V6's stealing, exposure and postflop changes, but restores V4's call ranges and removes the additional early +0.06 risk premium. Negative total chips from a category of calls and a raw bust count alone do not prove those calls had negative expected value.

`agent_reform_v7.py` builds on that merge: raises the nominal button/small-blind opening widths to 58%/65%, allows adaptive widening up to 75%, and uses 2.25 BB for ordinary late opens. It retains short-stack rules, shover precautions, calibrated preflop ordering and the mixed reveal policy. It deliberately does not jump straight to Team 72's observed 93% small-blind rate.

## Tests that decide the recommendation

Four copies of each version play full eight-seat tables. Means and confidence intervals average copies within each table. These are internal opponent pools, not a simulation of the actual field.

| Fresh comparison | Tables | Points | Paired difference, approximate 95% interval |
|---|---:|---|---|
| V6 / V4 | 64 | **13.98 / 11.02** | +2.97 [−0.24, +6.17] |
| Custom merge / V4 | 64 | 12.93 / 12.07 | +0.86 [−2.42, +4.14] |
| V6 / custom merge | 64 | 12.54 / 12.46 | +0.08 [−3.27, +3.43] |
| V6 / Team-72-inspired reform | 64 | 12.62 / 12.38 | +0.23 [−3.40, +3.87] |

The reform initially lost to V6 10–15 in 24 tables. In a separate 24-table mixed pool with nit, TAG, calling-station and loose fixtures, it averaged **19.17 versus V6's 16.46**. That mixed result is exploratory; no independence-adjusted confidence interval was computed for it. The different outcomes are why it is premature to declare the reform best.

All four versions pass the seven blocking tactical cases; two additional cases are review-only. Direct comparisons reported zero failed decisions. The merged and reform files passed the official static submission checker. A separate 20-table, eight-seat official subprocess smoke test of V6 and the reform also returned zero failed decisions for every seat. It was used to check execution health, not select the winner.

**Fast next iteration:** keep V6 as the control. Test the reform against the next real-round mistakes and an aggressive blind defender. Promote a specific change only after it improves a fresh comparison without restoring premium folds or unreasonable large commitments. A top-ten finish is the objective, not a result established by these tests.

Evidence: `practice-4/focused-analysis.json` and `v4-v6-results/`. The private download remains outside the Git repository; only aggregate findings and source versions are shared there.
