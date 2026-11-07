# GTO comparison: prioritize first places

**Recommendation: use [`bots/gto_supplied/agent.py`](../../../bots/gto_supplied/agent.py), byte-for-byte identical to the supplied GTO.** Preserve its betting strategy for the next iteration. The tested merges fix specific mistakes but did not improve first-place results on fresh seeds, so they remain experimental.

## Fresh comparisons

Each mixed table contains two copies of A, two of B, and four balanced background opponents from the viable local bots and six fixtures. Direct matches contain four copies of each. “First” uses the official engine placement, including shared firsts and chip-ranked results at the hand cap. Copies are averaged within each table before computing approximate 95% confidence intervals.

| Comparison A / B | Tables | First A / B | Points A / B | First-rate difference A−B, percentage points (95% CI) |
|---|---:|---:|---:|---:|
| Supplied GTO / previous NC V7 adaptation | 256 mixed | **17.0% / 13.5%** | 14.71 / 14.55 | +3.52 [−1.26, +8.29] |
| Refined discard + river merge / supplied GTO | 512 mixed | 15.1% / **16.8%** | 15.05 / 15.65 | −1.66 [−5.12, +1.80] |
| River-only patch / supplied GTO | 384 mixed | 15.1% / **17.3%** | 14.80 / 16.25 | −2.21 [−6.24, +1.81] |
| Supplied GTO / teammate NC V9 | 96 direct | **13.5% / 11.5%** | 14.14 / 10.86 | +2.08 [−2.93, +7.09] |

Every first-place difference interval includes zero. These are useful direction-of-travel results, not proof that GTO is superior or will reach the tournament's top three. The field consists of available local policies, not the actual leading teams' unavailable code. Results from different pairings are not a single common leaderboard. No supplied hand-history file has been independently attributed to this exact GTO hash, so the claimed live improvement is user-reported; comparisons above are internal simulations.

## What to retain and why

- **Larger value bets and postflop pressure.** GTO uses bigger value sizing, including pot/1.5-pot bets for strong later-street hands, heads-up flop pressure, second barrels and semi-bluff raises. These are plausible mechanisms for building a winning stack. The whole policy tested well; these experiments do not isolate the causal benefit of each feature.
- **Normal opening sizes.** The active code opens around 2.5 BB, with some shallower 2.3 BB sizes. The historical 9 BB header is not the active strategy. Avoid importing that separate version's sizing.
- **Existing conservative preflop corrections.** GTO already uses `PRE - .07` and all-in `range_equity - .06`, versus NC V7's positive offsets. Applying the feedback's proposed discount again would double-count it. Retain positional/mid-stack aggression instead of widening every shove.
- **Existing postflop recalibration and stronger multiway reduction.** Several feedback changes are already present. Do not replace all estimates with random-opponent equities: opponents who bet have different ranges, and class estimates interact with all action thresholds.

## Feedback validation and rejected changes

Independent 12,000-runout comparisons confirmed the important discard defect: with `9d 9h 2d` on `7d 5d Qh`, the original heuristic chooses the bare flush draw over 99. Keeping 99 gained roughly **14.6–17.8 percentage points** of showdown equity under two opponent selection models, rather than the feedback's claimed 30 points. Four other named examples also supported preserving the made hand. See `discard-verification.json` for exact model-dependent results.

A blanket reduction in draw values caused a new error: `Ts Qc 9s` on `7h 4c 8s` dropped the open-ended straight draw for overcards, losing about **21.4 points** of sampled equity. This broad merge had an attractive 64-table development result, but that result was insufficient to justify promotion.

The refined experiment only revisits a leading unpaired draw when another keep has a real pair with at most one higher board rank. It preserves 99 in the first example, keeps the straight draw in the second, and preserves a flush draw over a weak pair facing multiple overcards. On 1,200 fresh random flops it changed only three selections; estimated overall equity gain was +0.036 percentage points, CI [−0.007, +0.080]. Its tournament first-place result still did not improve.

Exact river guards address the earlier histories' demonstrable calls with no possible winning/tied runout and folds when no loss was possible. The guards use public information only and require heads-up river play. They pass targeted guaranteed-win, guaranteed-loss and chop cases, but neither the river-only patch nor the refined merge demonstrated a first-place gain. They are saved for future testing, not silently included in the recommended file.

The feedback's referenced generator scripts and reference-table path were not present in the shared repository. Kevin's agent does contain a 22,100-row table, but its header describes flop-only estimates and its generation/range assumptions were not verified. Supplied GTO still uses a 169-class two-card table with offsets; it is not a validated three-card lookup or a solved equilibrium strategy. The shared NC V8 also differs from the 9 BB version described in the feedback.

## Validation and audit

- Original GTO and both retained experimental files passed all seven existing blocking tactical cases. Patched files also passed the three public-river cases.
- Official subprocess smoke: 24 eight-seat tables, two copies each of GTO, both retained experiments and the previous NC V7 adaptation; **zero failed decisions** across all eight seats. Static agent checks passed.
- Larger comparisons use direct in-process execution for speed. Timing figures from those runs are not subprocess-deadline guarantees.
- JSON results retain per-table lineups, placements, points, seeds, approximate table-clustered confidence intervals and source manifests. `candidate-manifest.json` adds exact refined/GTO/river/NC V9 source hashes; `sources.json` records the background policy files.
- The exploratory 192-table `gto-vs-codex_nc_v7_adapted-holdout.json` allowed the previous adaptation into the background pool as well. It is **superseded by the clean 256-table final comparison**, which excludes both compared policies from background selection. It is not used in the recommendation.
- The shared league now reports first-place rates and paired first-place differences, as well as payout points. Its tests also use the teammate's current NC bot names.
- Experimental files are explicitly labeled. No live tournament submission was made.

Recommended source SHA-256: `1d388d34699a5a93874534b3d61a74f1fffa9376b42ebf2b57edd2f8f01b5e06`.
