# Final Empty Bluffer tuning

**Decision: promote the 8 BB cheap-flop version.**

Final deliverable: `agent_empty_bluffer_final.py`. The primary objective remains official Empty Bluffer awards per table. This is the best-supported choice among the versions tested here, not a guarantee of the live prize or a global optimum. No tournament upload was made.

## Development pass

120 paired scenarios across balanced, aggressive and call-heavy synthetic profiles compared four changes with the current version: smaller bets; inexpensive low-card entry down to 8 BB instead of 12; wider low-card retention; and a combined higher-volume policy. Awards/table were:

| Candidate | Awards/table |
|---|---:|
| current | 3.975 |
| small_bets | 3.600 |
| short_stack | 4.225 |
| wide_keep | 3.850 |
| volume | 3.542 |

Only the short-stack entry change improved the pooled development estimate. It was frozen before the fresh comparison; no parameter changes used the fresh results. The promotion rule was also saved before that comparison: positive lower bound for the pooled paired approximate 95% gain interval, no lower award point estimate in any profile, all blocking checks passed, and zero observed failures.

## Fresh validation

384 scenarios per version: 128 in each profile. Same designated hero seat, table seed and seven-opponent lineup per paired comparison. Prize counts come from actual official-engine events, once per qualifying hand. These profiles contain available local policies; they do not reconstruct competitors’ current code.

| Version | Empty Bluffer awards | Awards/table | Points | Top three | Early bust |
|---|---:|---:|---:|---:|---:|
| 8 BB candidate | 1420 | 3.698 | 12.53 | 37.5% | 12.0% |
| Current prize-primary v1 | 1366 | 3.557 | 13.23 | 39.6% | 12.2% |
| Original dedicated bluffer | 282 | 0.734 | 18.44 | 57.3% | 5.7% |

Candidate minus current: **+0.141 awards/table**, approximate 95% interval **[+0.022, +0.259]**.

| Profile | Candidate awards/table | Current awards/table |
|---|---:|---:|
| balanced | 3.766 | 3.539 |
| pressure | 3.781 | 3.680 |
| call_heavy | 3.547 | 3.453 |

Promotion checks:
- positive_paired_interval: PASS.
- nonnegative_in_every_profile: PASS.
- blocking_checks: PASS.
- no_holdout_failures: PASS.
- no_subprocess_failures: PASS.

## Final policy and practical limits

The only strategy difference from prize-primary v1 is lowering the inexpensive qualifying-flop entry threshold from 12 BB to 8 BB. Bet sizes, low-card retention budget, large-hand protection and the public-river check are unchanged.

It retains the prize-first strategy: seek inexpensive flops with a 2–5, retain/expose the qualifying low card more often, and pursue wins without showdown. Tournament points and survival remain secondary. It does not optimize Shover or Calling Station or certify the current cumulative prize standings.

- All challenger sources passed the existing seven blocking tactical cases and three public-river cases.
- A targeted test confirms that the candidate calls the qualifying 10 BB opportunity where current v1 folds; both fold the 6 BB case and call the 16 BB case.
- Sixteen official subprocess tables included both current and candidate versions; all eight seats had zero failed decisions. The larger performance comparison ran in-process.
- Rejected variants, exact sources, seeds, per-table outcomes, source/dependency hashes, the predeclared gate and the gate decision are retained for audit.

Final source SHA-256: `ef58de32d61dc1dd33460938d768bbeeeaf23ac4454cc6e6dd2a51893430b678`.

Shared source: `bots/codex_empty_bluffer_final/agent.py`. Reproduce the fresh comparison with `python arena/prize_final_eval.py holdout 128`; development uses `development 40`. Each run writes to a new folder under `arena/runs/`.
