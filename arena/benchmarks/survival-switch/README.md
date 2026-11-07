# Survival switch v1

File: `agent_survival_switch_v1.py`. ZIP: `agent_survival_switch_v1.zip` (contains only `agent.py`).

This implements the requested two-stage strategy. It is a candidate for the next submission, not a guarantee of a live leaderboard improvement. No tournament upload was made.

## Behavior

- Before the paid places are secured (four or more players for 50/30/20 payouts), use tighter reraise/rejam ranges and ordinary raises instead of unopened 23–30 BB jams. Keep short-stack shoves, normal open ranges and blind steals.
- With more than 12 BB, control pot size with one-pair-strength hands; avoid automatically converting a large value bet into a stack commitment. Require more evidence to pay large reraises and repeated barrels. The extra requirement applies to both normal and large-call branches.
- After an opponent reraises our postflop raise and barrels again, cap fragile-hand equity conservatively when a call costs at least 20% of the remaining stack-plus-bet. This is an explicit heuristic range adjustment, not solved equity; stronger combo draws are exempt and recognized maniacs receive a looser threshold.
- At three players remaining, the survival restrictions turn off: lower risk premium, 12% wider opening thresholds, original aggressive postflop strategy and 30 BB opening-shove schedule. Heads-up uses zero risk premium and 20% wider opening thresholds. This switch follows total players remaining, not the number of opponents who have not folded in the current hand.
- Keep the supplied final file’s public-river loss check and straight, flush and kicker corrections. Strong made-hand protections and ordinary short-stack play pass the existing critical cases.

## Fresh comparison

384 paired table scenarios per version: 192 in each of two synthetic opponent profiles. Every scenario has one designated hero seat against seven opponents; all versions use the same seat, seed and lineup. These are available local policies, not the tournament rivals’ actual code. Top-three and first-place rates use official placing, including chip-ranked finishes at the hand cap. Points use the official payout/ICM scoring.

| Version | Points | Top three | First | Bust by hand 20 |
|---|---:|---:|---:|---:|
| Survival switch v1 | 16.28 | 50.3% | 15.4% | 4.9% |
| Supplied GTO final | 16.17 | 49.2% | 14.8% | 8.9% |
| Original supplied GTO | 15.89 | 46.9% | 16.9% | 10.4% |
| Earlier V6 reference | 17.68 | 55.5% | 15.9% | 4.2% |

Paired differences versus supplied GTO final (approximate 95% intervals; uncertainty is across independent table scenarios):

- Points: +0.10 points, interval [-1.99, +2.20].
- Top three: +1.04 percentage points, interval [-4.32, +6.40].
- First: +0.52 percentage points, interval [-4.22, +5.26].
- Early bust: -3.91 percentage points, interval [-6.22, -1.60].

The behavioral switch is verified, but a more aggressive strategy after cashing does not itself prove more wins. Read first-place results separately from top-three gains. V6 is included as a reference rather than hiding a stronger older policy. The profiles are stress tests, not a calibrated forecast of the current live field.

## Selection and validation

Development used 160 paired scenarios. A 16 BB pre-cash opening-jam cutoff increased top-three finishes but reduced firsts; a 22 BB cutoff retained more profitable mid-stack pressure and improved development points/top-three results. The latter was selected before the 384 fresh scenarios; no settings were changed using those results. Development results retain both variants and exact hashes.

- All seven existing blocking tactical cases and three public-river cases passed.
- A reconstructed 200-BB JJ loss now folds to the turn shove after a flop reraise; the unchanged supplied final calls. Reconstruction uses only information available at the decision, with no opponent hidden cards or future river. Prior-table opponent labels are not reconstructed.
- The four-to-three-player transition and an alternative two-paid-place configuration are tested.
- Final source passed the official archive check. Sixteen official subprocess tables completed with zero failed decisions across all eight seats. Larger comparisons ran in-process; those timing conditions are not a subprocess deadline guarantee.
- An initial subprocess smoke attempt incorrectly included arena-only fixture folders; their shared imports failed, so that attempt was discarded and replaced with standalone opponents. It is not used for scoring or validation claims.

Exact agent SHA-256: `da078c6e7117daa922affbad3f4df7d9886cdab42be2a62f22da54f16fbe91e8`.

Shared repository sources: `bots/codex_survival_switch_v1/agent.py` and unchanged parent `bots/gto_final_reference/agent.py`. Reproduce fresh comparisons with `python arena/survival_switch_eval.py holdout 192`; results write to a new folder under `arena/runs/`. Current bot hashes and shared dependency hashes are saved in the evidence.
