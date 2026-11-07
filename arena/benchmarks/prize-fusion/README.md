# Survival + Empty Bluffer v1

File: `agent_survival_bluffer_v1.py`; ZIP contains the same source as `agent.py`. This merges the supplied NC bluffer’s prize idea into the survival-switch policy. The survival phase and more aggressive paid-place phase remain. No tournament upload was performed.

## What the prize actually rewards

The kit rules and official engine agree: Empty Bluffer requires exposing a retained 2, 3, 4 or 5, then betting/raising after selection, and winning without showdown. **A strong value hand qualifies too.** The event count is once per qualifying hand. Organizers sum raw prize counts across scored rounds, without tournament weights; this benchmark does not establish our cumulative prize standing.

Shover counts hands with an all-in bet/raise, including losing hands, but excludes all-in calls and forced blinds. Calling Station uses total calls divided by total betting decisions across scored rounds. The fusion targets Empty Bluffer while retaining ordinary shoves/calls. It does not deliberately force all-ins or unnecessary calls to maximize the other categories.

## Merge behavior

- Prefer exposing a retained 2–5 when available. Where the existing keep has no low card, consider the best qualifying alternative within 0.02 of the heuristic hand score before cashing or 0.04 afterward. These are heuristic-score budgets, not measured equity guarantees.
- Never lower the evaluator’s hand class to obtain a low card. For made hands, also preserve or improve the current evaluated hand value. Do not discard an existing draw for plain air merely to qualify.
- Preserve normal strong-value sizing. Other eligible opportunities can use a one-third-pot bet, subject to legal minimums and a cap of **6% of remaining stack before cashing**, **10% after**. The prize overlay never shoves. These caps bound the extra bet, not every later decision or the total possible hand loss.
- Before cashing, require all remaining opponents to have checked on the current street. Limit opportunities to one or two opponents; skip recognized calling stations, any all-in opponent, and hands where we already raised after the reveal. Ordinary strategy handles later streets.
- Keep the four-or-more-player survival safeguards, three-player pressure switch, heads-up pressure, and public-river/hand-class correctness fixes. The supplied NC bluffer is otherwise an older V6 policy; copying its entire file would remove those changes.

## Fresh paired comparison

256 scenarios per version, split equally across two synthetic opponent profiles. Same hero seat, table seed and seven-opponent lineup for each version. Prize counts below come from actual official-engine `prize_the_empty_bluffer` / `prize_the_shover` events, not inferred bluff attempts. Top-three/first rates use official places, including chip ranking at the cap.

| Version | Empty Bluffer awards/table | Points | Top three | First | Early bust |
|---|---:|---:|---:|---:|---:|
| Survival + Bluffer | 0.434 | 18.67 | 58.2% | 17.2% | 5.1% |
| Survival switch parent | 0.254 | 18.24 | 57.4% | 16.0% | 4.7% |
| Supplied NC bluffer | 0.723 | 16.80 | 51.2% | 15.2% | 5.1% |

Relative Empty Bluffer change versus survival parent: **+70.8%**.

Paired differences versus survival parent (approximate 95% confidence intervals):

- Empty Bluffer: +0.180 awards/table [+0.113, +0.246].
- Points: +0.430 points [-0.518, +1.377].
- Top three: +0.781 percentage points [-1.386, +2.949].
- First: +1.172 percentage points [-1.368, +3.712].
- Early bust: +0.391 percentage points [-0.375, +1.156].

Other prize metrics are diagnostic, not optimization targets:

| Version | Shover awards/table | Pooled call share |
|---|---:|---:|
| Survival + Bluffer | 6.152 | 5.70% |
| Survival switch parent | 6.039 | 5.85% |
| Supplied NC bluffer | 3.500 | 8.18% |

These are local stress tests with available policies, not a calibrated replica of the live field. Small point/top-three/win changes should not be treated as established improvements. Prize wins depend on other teams’ cumulative counts, which are not measured here. The supplied dedicated bluffer is included so the prize-versus-tournament tradeoff is visible.

## Validation and reproducibility

- All existing blocking tactical/public-river cases and the deep-JJ survival regression passed.
- Five focused test groups cover made-hand preservation, low-card exposure, legal small bets, station/all-in exclusions, no extra prize bet after an earlier post-reveal raise, stack budgets, and the paid-place transition.
- Official standalone archive validation passed. Sixteen official subprocess tables completed with zero failed decisions for all eight seats. The larger comparisons ran in-process.
- Development used 128 different paired scenarios. The same candidate was frozen before the 256 fresh scenarios; no tuning used the fresh results.
- Teammate `bots/nc_bluffer/agent.py` matches the supplied file byte for byte and is retained unchanged.
- Source and dependency hashes, seeds, per-table results, confidence intervals and prize counts are included in the JSON evidence. Call share is pooled calls/decisions, not an average of per-table ratios.

Final agent SHA-256: `2020edcd5ff36e8d68c250a443dd14c71bcdfbfaad087c7591fcb8ee031f57a0`.

Shared source: `bots/codex_survival_bluffer_v1/agent.py`. Reproduce with `python arena/prize_fusion_eval.py holdout 128`; each run writes a new folder under `arena/runs/`.
