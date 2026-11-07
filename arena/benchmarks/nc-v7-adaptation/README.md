# NC V7, the full V6 history, and the adapted candidate

**Main next-round candidate: `agent_nc_v7_adapted.py`. It improves the local point estimate over supplied NC V7, but has not established a top-three tournament finish.** It placed fourth in the balanced local league; its uncertainty interval overlaps the top three. Keep the original files as controls. No tournament upload was made.

## Latest V7 result received during testing

The new user-identified V7-exposed round, `547666b1-3877-4bac-9925-17e1e78134da`, contains 1,001 scored own tables. It averaged **14.60 points**, with 145 first places, 26 first-20-hand busts, and two automatic fallbacks. The export does not explain whether those two fallbacks were timeouts, illegal actions, or another runtime failure. They are separate from the observed set fold and are too few to explain the overall gap by themselves.

A fresh public-card scan found **14 zero-equity calls among 271 examined heads-up river calls**, and **7 cannot-lose folds among 576 examined heads-up river folds**. Both delivered alternatives contain the deterministic rules for these error categories.

The new shove policy is visibly active: 1,153/3,070 unopened opportunities at >12–16 BB and 1,067/3,103 at >16–20 BB became open shoves. Across all 2,788 open shoves at >12–22 BB, 483 were called (17.3%), 185 ended in a bust, and the associated hands gained 1,927.88 BB in total. Their summed per-hand ICM-equity changes were +541.29 points. These are conditional observed outcomes, not a counterfactual proof that shoving beats smaller raises. They do not support blaming every loss on the new shoves.

Ordinary late-position pressure fell: with 5–8 players, unopened button raises were **1,906/3,593 (53.0%)**, and small-blind raises **927/1,880 (49.3%)**. The earlier V6 slice had 60.2% and 61.5%. The samples and opponent pools differ, so this is a policy-direction clue rather than a controlled estimate of lost EV. The prepared V7 adaptation addresses this opening gap as well as the river mistakes.

The new 14.60 score is below the complete earlier V6 mean of 16.42. It does not establish the effect of each V7 change individually. No claim is made that the adaptation has already recovered that gap in a live round.

## Full history changes the baseline

The complete user-supplied V6 export is tournament `3e3dcc02-ca4f-48c5-9acb-6c0e3a32c10e`: **20,156 unique tables, including 156 own filler appearances and 20,000 scored own appearances**. It was read in full with valid gzip completion.

| Team | Observed scored tables | Mean points |
|---|---:|---:|
| Team 72 | 1,173 | 21.95 |
| TeamBallHog | 1,150 | 21.72 |
| WAYS-ER TEAM | 1,184 | 21.36 |
| Double G, user-identified V6 | 20,000 | **16.42** |

These opponent figures describe the subset of their tables appearing in our export. They are not an independently retrieved official full-round leaderboard. The earlier first-1,000 slice understated our mean (15.35) and gave a different ordering of opponents.

Double G finished first 3,279 times (16.4%), had zero automatic fallbacks, and busted in the first 20 hands 798 times (4.0%).

The other supplied download completed from `.crdownload` to `hands-b3ae5ccd-57bc-4690-8f4f-a082971ce5f1.jsonl.gz`. It is a separate valid export: 1,004 records, including 1,000 scored own appearances, averaging **14.86**. Its uploaded source hash is absent; do not label that result NC V7 merely because the files arrived together. Its highest observed opponent means are TS 24.26, sandylikesfrogs 22.11, and Team 72 21.31.

## The strongest actionable finding

For each relevant heads-up river decision in the full V6 history, enumerate every possible opponent hidden card while fixing their exposed card and excluding the board, our original three cards, and all public reveals. No opponent hidden cards from later showdown are used.

- **630 of 8,767 examined river calls (7.2%) had zero possible showdown equity.** They paid 407,609 chips in total. This is an observed call cost across changing blind levels, not a claimed gain in tournament points.
- **190 of 15,293 examined river folds could not lose at showdown** against any remaining hidden card. Some are certain chops; others are guaranteed wins.
- **169 large calls** had the earlier pocket-pair/paired-board classification pattern. These are review leads, not all proved wrong by the same public-card test.
- **31,586 of 57,491 flop-call hands (54.9%)** later folded on the turn or river. That is a same-hand sequence count, not proof that all those calls were wrong.
- **One full-house-or-better fold** appeared in the full history, versus none in the initial slice. This count alone does not establish it was incorrect.
- **Zero open shoves** in 76,127 unopened first-action opportunities at >12–16 BB and 65,152 at >16–20 BB. NC V7 already changes this part of the older strategy.

A typical provable error is calling with a low club flush on a four-club board when the opponent exposes a higher club. Another is folding a strong top pair when the opponent's exposed blank prevents every possible hidden card from overtaking us. Generic hand-class equity misses information that this variant explicitly provides.

## What changed in the V7-based candidate

1. Enumerates possible opponent hidden cards on heads-up rivers. Folds against a publicly certain loss; continues when no hidden card can beat us. Uses no future information.
2. For uncertain cases, caps calling equity by the uniform-hidden-card estimate; for betting decisions, blends that estimate equally with the original heuristic. Uniform hidden cards are **not** a fitted opponent betting range. This component is experimental.
3. Widens base cutoff/button/small-blind open cutoffs from 32%/44%/40% to 38%/56%/65%, and increases the adaptive steal cap to 75%.
4. Uses 2.25 BB ordinary late-position opens above 20 BB. Existing shorter-stack sizing and V7 shove logic remain.
5. Restores the no-limper guard on the any-hand foldbot steal. A player who already limped still contests the pot.

The minimal alternative, `agent_merge_river_guard.py`, applies only the guaranteed heads-up river outcome rules to the older V4/V6 merge. It does not use the uniform-equity blend or the new opening widths.

The earlier blanket paired-board reclassification was not copied into these candidates: its scoring gain had not held up. V7's existing imperfect hand-class model remains in other situations.

## Against every available opponent

The first pass tested supplied V7 against all ten other viable standalone repo bots, 24 tables per pairing. V7 led on point estimate in seven pairings; most intervals overlap. Two legacy bots, nc_v1 and nc_v2, failed the existing tactical checks and were excluded from performance rankings.

Mixed tests also include all six fixture policies: nit, TAG, station, maniac, loose, and limper. A position error in those fixtures was corrected: folded players must still count when identifying preflop position. All new mixed results use that correction. It has a regression test.

The final balanced league used **18 policies, 288 eight-seat tables, and exactly 128 appearances per policy**, with eight distinct policies per table:

| Rank by point estimate | Policy | Mean points | Approximate 95% interval |
|---|---|---:|---|
| 1 | Original V4/V6 merge | 17.73 | 14.39–21.08 |
| 2 | nc_v3 | 17.42 | 14.09–20.75 |
| 3 | Downloaded original V6 | 17.19 | 13.77–20.60 |
| **4** | **V7-based adaptation** | **16.95** | **13.49–20.41** |
| 5 | Prior steal reform | 16.72 | 13.23–20.20 |
| 10 | Supplied nc_v7 | 14.77 | 11.80–17.73 |

This is a local point-estimate ranking, not a statistically established ordering. The minimal merge/river-guard alternative was built afterward and is not included in this ranking; its separate tests are below. The original top merge was not modified.

The actual competitors' source code is unavailable. Neither histories nor simplified fixtures reproduce their private ranges, discard policy, opponent adaptation, or response to our changed strategy. We cannot claim that 21 points in this local pool would mean 21 points against the real field. The six fixtures are also weaker than most surviving repo versions, and many repo versions share the same underlying model.

## Fresh tests and failed experiments

Mixed candidate/control comparisons use two copies each plus four opponents balanced across all sixteen other available policies. Differences average the two copies within each table before calculating uncertainty. Direct comparisons use four copies each.

| Test | Tables | Candidate | Control | Candidate minus control, approx. 95% interval |
|---|---:|---:|---:|---|
| Public-river model only, development | 64 | 12.50 | 15.08 | −2.58 [−7.69, +2.53] |
| Wider/smaller steals only, development | 64 | 14.22 | 15.47 | −1.25 [−6.22, +3.72] |
| Combined V7 adaptation, development | 64 | 17.34 | 12.27 | +5.08 [+0.36, +9.79] |
| **Combined, fresh mixed holdout** | **192** | **16.33** | **14.01** | **+2.32 [−0.55, +5.19]** |
| Combined, fresh direct V7 comparison | 96 | 12.63 | 12.37 | +0.26 [−2.13, +2.65] |
| Guaranteed river rules on V7 only | 96 | 15.36 | 14.48 | +0.89 [−3.18, +4.95] |
| Minimal merge/river guard, mixed vs V7 | 192 | 16.46 | 14.87 | +1.59 [−1.22, +4.40] |
| Minimal merge/river guard vs its parent | 96 | 12.08 | 12.92 | −0.83 [−3.57, +1.90] |

Both alternatives have positive mixed-field point estimates against V7, but neither establishes a reliable scoring improvement. The development gain shrank on fresh tables. No rank was obtained by rerunning seeds until the candidate appeared in the top three.

## Validation and files

Both delivered candidates pass the seven existing blocking tactical cases plus three public-river regression cases: a guaranteed royal-flush win, a guaranteed royal-flush loss, and a certain board chop. Supplied V7 incorrectly calls in the guaranteed-loss case. Both pass the official static submission checker.

The V7 adaptation passed a 32-table official subprocess check with zero failed decisions on all eight seats; the minimal alternative passed a separate 16-table check with the same result. No promotion was inferred from these short runtime checks. Direct strategy benchmarks also reported no failed decisions. Tests cover observable failures; they do not prove every possible internal path is exception-free.

Source identities:
- Supplied NC V7: `5a120a45d98f97d31d726c066e1d5d3c500584a8df681f1d77a2f9f71819e0ef`
- V7 adaptation: `418902a7a99d1da027bcc541d01fc66424ef3e38c9dea11e753d452d8deddb35`
- Minimal merge/river guard: `df6580d139d44d292bbf1a90766dcde1be3d8aabee75ec3cdc1b8253dd66ea29`

Raw JSON evidence accompanies this report. Full/private hand histories and individual private examples remain local. The repo also includes the reusable balanced field league, public-river history checker, and regression tests.

**Recommendation:** use the V7 adaptation as the next controlled candidate if moving beyond supplied V7. The guaranteed river corrections address demonstrated mistakes; the wider opens and equity blend remain experimental. A top-three finish has not been achieved or verified by this work.

A newer teammate `nc_v8` arrived during this work (commit e3e8065). It was not part of the earlier 18-policy league; its separate direct comparison is recorded in `nc8-comparison.json`.

Against that newer nc_v8 in 64 fresh direct tables, the adaptation scored **13.52 versus 11.48**, difference +2.03 with approximate 95% interval [-1.12, +5.18]. This comparison is also inconclusive; both had zero failed decisions.
