# 11. Decision card: the shape of `act()` on one page

Carry this into the room. It is the order of checks the bot runs on every decision, from the wrapper down. Each line names the inputs it needs so the kit-recon (P0) can confirm they exist.

```
act(state, memory)
  wrap everything in try/except -> on any failure return (CHECK if offered, else FOLD if offered,
     else Action(first.kind, first.min_amount)) together with the memory bytes unchanged
  start the clock (perf_counter)

  0. parse memory (struct record: version, length, checksum) -> fresh record if b"" or corrupt
     parse state: my seat, hole cards, board, phase, legal_actions, seats (stack, bet, status),
     pot, to_call, button, hand_number, hand_cap, blinds, payouts, players_remaining
     fold state.events into the record: per-seat counters, hand counter, showdown observations
     if state.phase is not "betting": the variant handler, else the automatic choice

  1. table facts (cached per hand):
       players_left, places_paid, my_stack_rank, eff_bb, hands_to_cap
       lambda = RISK[players_left][places_paid][my_stack_rank]  (0 heads-up)
       shovers = seats with all-in rate >= 60% over >= 4 hands
       foldbots = seats with zero voluntary actions over >= 8 opportunities
       table_fold_to_steal, table_3bet_rate

  2. hand strength (cached per street):
       preflop: class index -> (percentile, eq_vs_1 .. eq_vs_7)
       postflop: made-hand class + draw flags + texture -> equity estimate, shaded by
                 opponents' aggression; count live opponents

  3. PREFLOP
       a. facing an all-in (or a raise from a SHOVER):
            need = pot odds * (1 + lambda); if two all-ins: equity vs 2 random
            SHOVER: call iff eq_vs_1 >= 0.65 (0.70 if flat payouts and 6+ left); QQ+ vs two
            else: call iff equity vs the raiser's estimated range >= need; never raise
       b. a SHOVER still to act behind me: FOLD, or SHOVE first iff eq_vs_1 >= 0.65
       c. unopened pot:
            eff_bb <= 12 -> push/fold table by position (widen vs FOLDBOT blinds, with antes)
            eff_bb <= 5  -> shove any two from BTN/SB; top 40% elsewhere
            else -> open iff percentile <= OPEN[position] * steal_multiplier(table_fold_to_steal)
                    size 2.5bb early, 2.2 to 2.3bb CO/BTN, 3bb SB; isolate limpers 3bb + 1 per limper
       d. facing an open (not all-in):
            3-bet/shove top 4% (shove when eff_bb <= 25); re-shove top 8 to 12% when 12 to 25bb
            call top 10% in position if call <= 15% of stack and not a NIT's raise
            BB: call min-raise with top 45%, 2.5bb raise with top 30%; wider vs MANIAC
            everything else FOLD (never raise-fold)
       e. BB option when everyone limped: raise top 15%, else CHECK

  4. POSTFLOP
       classify: air / weak draw / strong draw / weak pair / good pair / two pair+ / nuts
       opponents: labels (STATION, NIT, MANIAC, FOLDBOT, TAG), live count, aggressor
       a. checked to me:
            vs FOLDBOT: bet 60% any two
            aggressor & dry board & <= 2 opps: c-bet 60% with weak pair+ or strong draw;
              with air iff opp fold-to-cbet >= 55% and not STATION (mix 60%)
            good pair+ : bet 60 to 75% (75 to 100% vs STATION); multiway: good pair+ only
            else CHECK
       b. facing a bet:
            price = to_call / (pot + to_call); all-in-sized -> price * (1 + lambda)
            nuts/two pair+ : raise (pot-sized or shove if > 60% of stack), CALL if raise illegal
            good pair: CALL; fold to second barrel from NIT; call down vs MANIAC/random
            strong draw: CALL iff equity >= price (+implied only if opp has chips); raise vs folders
            weak pair / air: FOLD (call small bets only vs MANIAC with decent equity)
       c. river: value bet good pair+ vs callers; check marginal vs aggressive; fold weak to big bets
          from passive opponents; never bluff STATION

  5. CAP (hands_to_cap <= 20; the cap is 250 and levels are 20 hands, read both from state.config):
       in a paid place by chips: decline marginal all-ins (lambda x 1.5)
       outside the paid places: take high-fold-equity shoves; never fold into zero
       heads-up: chip EV, lambda = 0

  6. choose(kind, total): raise_to only if offered, total = int clamped to [min_amount, max_amount];
     else call if offered, else check, else fold, else the automatic choice
  7. pack the record back into bytes (under 16 KB; a few hundred bytes in practice) and return (action, bytes)
  if elapsed > 0.5 ms at any checkpoint: skip optional refinements and return the current best
```

Constants live in one dictionary: OPEN ranges by position, push/fold widths by position and stack, RISK table, SHOVER threshold, label triggers, bet sizes. Tuning between tournaments edits that dictionary only.

The Getting Started page confirms the kit provides: hand_number, hand_cap, hands_until_next_level, blind_level and blinds, players_remaining and bust_order, every seat's stack, bet and status, the button, this hand's history, the full public event feed since our last turn (including showdown cards), legal_actions with min_amount and max_amount, payouts and the rest of config. Still confirm in P0: the exact field names in sdk/, any variant phase and action kind, and how the memory example in the template serializes.
