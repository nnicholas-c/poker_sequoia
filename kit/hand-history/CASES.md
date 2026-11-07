# Find an example hand

Synthetic scenario collection with varying table rules, not one configured live round. Complete tables illustrate mechanics, not exhaustive outcomes or event settings.

Open `sample.jsonl` or use `read.py` to inspect the referenced table and hand. `coverage.json` contains additional locations, settings and scripted fixture expectations. Those expectations are not additional fields in a real participant download.

iteration/table/event_index/hand_index/seat are zero-based; hand is the one-based hand number.

## Tables

| Iteration / table | Scenario | Seats | Hands | Your seat | Filler |
| --- | --- | ---: | ---: | ---: | --- |
| 0 / 0 | choices and fallbacks | 8 | 10 | 1 | no |
| 1 / 0 | side pots and busts | 8 | 5 | 1 | no |
| 1 / 1 | filler seat | 8 | 5 | 7 | yes |
| 2 / 0 | flop and turn folds with prizes | 2 | 2 | 1 | no |
| 3 / 1 | preflop all in | 2 | 1 | 1 | no |
| 4 / 2 | flop all in | 2 | 1 | 0 | no |
| 5 / 3 | turn all in | 2 | 1 | 1 | no |
| 6 / 2 | river all in | 2 | 1 | 0 | no |
| 7 / 1 | short blind and one survivor | 2 | 1 | 1 | no |

## Mechanics and data cases

`selection_A_B` means discard original index A and reveal original index B. For any private-card entry, use the hand's array index rather than its one-based number.

| Case | Iteration / table | Hand | Event index, if applicable |
| --- | --- | --- | --- |
| `all_in_selection_before_river_show` | 1 / 0 | 4 | 30 |
| `ante` | 0 / 0 | 1 | 0 |
| `board_ends_with_0_cards` | 1 / 0 | 1 | — |
| `board_ends_with_3_cards` | 2 / 0 | 1 | — |
| `board_ends_with_4_cards` | 2 / 0 | 2 | — |
| `board_ends_with_5_cards` | 0 / 0 | 1 | — |
| `bust_followed_by_empty_private_cards` | 1 / 0 | 5 | — |
| `busted_seat_slots_without_stack_events` | 1 / 0 | 5 | — |
| `changing_blinds` | 0 / 0 | 3 | — |
| `flop_all_in` | 4 / 2 | 1 | 9 |
| `hand_cap_with_multiple_survivors_and_icm` | 0 / 0 | 10 | — |
| `heads_up` | 2 / 0 | whole table | — |
| `implicit_uncalled_refund` | 1 / 0 | 4 | — |
| `mandatory_showdown_reveals_every_contender` | 0 / 0 | 1 | — |
| `one_survivor_table_end` | 3 / 1 | 1 | — |
| `opponent_automatic_marker_omitted` | 0 / 0 | 3 | 10 |
| `own_automatic_check` | 0 / 0 | 1 | 40 |
| `own_automatic_fold` | 0 / 0 | 2 | 12 |
| `own_automatic_select` | 0 / 0 | 3 | 21 |
| `own_filler_seat` | 1 / 1 | whole table | — |
| `own_nondefault_selection` | 0 / 0 | 1 | 24 |
| `own_successful_selection_then_fold_with_ambiguous_discard` | 0 / 0 | 4 | 37 |
| `preflop_all_in` | 1 / 0 | 4 | 2 |
| `prize_marker_after_final_stacks` | 2 / 0 | 1 | 15 |
| `prize_the_empty_bluffer` | 2 / 0 | 1 | 15 |
| `prize_the_shover` | 1 / 0 | 4 | 3 |
| `reveal_persists_after_fold` | 0 / 0 | 4 | 37 |
| `river_all_in` | 6 / 2 | 1 | 15 |
| `selection_0_1` | 0 / 0 | 1 | 21 |
| `selection_0_2` | 0 / 0 | 1 | 22 |
| `selection_1_0` | 0 / 0 | 1 | 25 |
| `selection_1_2` | 0 / 0 | 1 | 26 |
| `selection_2_0` | 0 / 0 | 1 | 19 |
| `selection_2_1` | 0 / 0 | 1 | 20 |
| `short_all_in_call` | 1 / 0 | 4 | 4 |
| `short_blind` | 7 / 1 | 1 | 0 |
| `side_pots` | 1 / 0 | 4 | — |
| `split_pot` | 1 / 1 | 3 | — |
| `turn_all_in` | 5 / 3 | 1 | 12 |
| `varying_payouts` | 0 / 0 | whole table | — |
| `zero_own_automatic_actions` | 2 / 0 | whole table | — |

## What the file cannot tell you

- Selection indexes below are scripted fixture expectations, not fields in participant histories.
- Own private_events identify the owner's retained and discarded cards; older downloads without this field can leave them ambiguous after a fold or muck.
- Opponents' original cards and private discards are absent; only reveal/show disclosure events publish their cards.
- Automatic markers identify your fallback actions, not the failure reason; opponents' markers are omitted.
- Uncalled refunds have no event; stack differences, not event cash-flow sums, determine exact chip changes.
- A complete-pair prefix can look complete; the file format has no final table-count marker.
- These tables use different illustrative player counts, blinds, hand caps and payouts, unlike one configured live round.
- Prize markers can follow the final stack events; consume every event in a hand.
