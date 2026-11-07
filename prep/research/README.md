# research/

Offline analysis tooling used on Nov 6 to produce the numbers in 09_REFERENCE_SHEETS.md and 10_RESEARCH_FINDINGS.md. None of this is competition code, none of it is written to be submitted, and none of it should be opened at the event: tonight's code is written tonight against the real kit.

- `equity_ref.py` and `equity_ref.tsv`: 169 starting-hand classes, all-in equity versus 1 and versus 7 random hands (4,000 deals per class).
- `hand_matrix.py` and `hand_matrix.tsv`: the 169 x 169 class-vs-class all-in equity matrix (400 deals per pair).
- `pushfold_nash.py`: heads-up push/fold equilibrium by fictitious play on the matrix; chip EV; optional ante.
- `sng_sim.py`: a small eight-player sit-and-go simulator with the published format (2,000 chips, blinds up every 25 hands, 200-hand cap, ICM split at the cap) and crude archetype bots (fold-bot, shove-bot, station, random, maniac, nit, tight-aggressive, an adaptive tight-aggressive that responds to shove-bots). SYNTHETIC blind schedule and payouts.
- `sim_results*.txt`: raw output of the runs summarized in 10_RESEARCH_FINDINGS.md.

Reproduce (from the repo root; pure Python, no dependencies):

```
python3 -I research/equity_ref.py 4000 research/equity_ref.tsv
python3 -I research/hand_matrix.py 400 research/hand_matrix.tsv
python3 -I research/pushfold_nash.py research/hand_matrix.tsv
python3 -I research/sng_sim.py --tables 1500 --lineup shove7tag --payouts flat
python3 -I research/sng_sim.py --tables 1200 --lineup adapt1_65 --payouts flat
```
