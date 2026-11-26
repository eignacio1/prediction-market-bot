# PREREG — NBA props demo forward test of the 14 kept leaves (W130.2, EXP-NBAPROPS-002)

**Last reviewed:** 2026-11-25. **Frozen before any order is placed.** No order, fill or settlement for this book exists when this
file is committed. Any change after the first order is a new pre-registration, not an edit. ADR-0072 is not edited; this
book runs under its addendum (ARM_ORDERS, demo only, flat stake, kelly 0).

Binds to DOCTRINE §1 / ADR-0077 (the tree picks the arm; a split is applied when tested per leaf), EXP-NBAPROPS-001 (the 14 kept
leaves), GG-527 (paper rows are not execution evidence; only demo fills are).
Purpose / measure moved: EXECUTION E1 / E2 / E3 on NBA props (0 → n once approved); D6 layers 6–7 for the NBA props cells.

## 1. What is tested
A demo forward test of the 14 (leaf, split, split_leaf) entries kept in `12_EXPLORATORY/nba_props_splits/nba_props_v2.candidate.json`
(12 RIDE, 2 FADE; 1 BH-earned). Nothing else is ordered. A prop row is eligible only if its `router_candidates["nba_props"]` record
has `prop_split_applied` true, no `prop_split_conflict`, arm RIDE or FADE, and its (leaf_id, split, split_leaf) is one of the 14.
Hypothesis closed nowhere: a leaf that loses is routed to ride / no bet in that leaf; it is not a stop.

## 2. Entry rule per leaf (from the candidate map's arm)
- RIDE: back the favourite side (mid > 0.5 → YES, mid < 0.5 → NO). FADE: back the other side. Mid == 0.5 → skip.
- The side must equal the record's `side`; a disagreement is a counted skip (`side_disagrees`).
- Band must still hold at order time: time to tip recomputed from `start_time_utc` and inside the leaf's band
  (T2 4–8 h, T3 15–60 min). Outside → skip `outside_band`. Tip already passed → skip `tip_passed`.
- Price and placement: the ADR-0072 rule, unchanged (`demo_fill_policy.decide`: book anchor, rest at the touch, skip if the
  book mid and model mid differ by more than `DEMO_FILL_MAX_MID_GAP` 0.05), 60 s cancel (`DEMO_FILL_CANCEL_AFTER_S`),
  and a cron-side `sweep_overdue` before each run because the cancel timer thread does not survive the process.
- Idempotent per (leaf, market, day): one order per leaf-split key per market per UTC day, enforced by a uuid5 client order id and a
  check of the order log. A repeat is a counted skip (`already_ordered`).
- Demo host only (production host refused), global and shadow kill switch honoured, listing and cash gates as `arm_orders`.

## 3. Stake and caps (each derived here; no real-money constant is read)
- **Flat demo stake $1.00 per order, `kelly_fraction` 0.** Layer 6 sizing is the flat stake; the Kelly-shaped figure is logged, never placed.
- **Per-event (game) cap $51.** Derivation: the 14 kept leaves matched 1,120 scored rows over 22 held-out games (RESULT.md) =
  50.9 matching rows per game, an upper bound on orders per game since one order per (leaf, market, day) only removes rows.
  Cap = ceil(50.9) × $1 stake.
- **Per-day cap $408.** Derivation: event cap × 8 games per slate (NBA regular season: ~1,230 games over ~165 days = 7.5 per day, rounded up).
- Both caps are ceilings sized to bind almost never (the GG-1935 lesson: a cap borrowed from a real-money limit starved a test of ~8,000 orders).
  They are a backstop behind the demo account's cash gate.
- **Every skip reason is a counted number** in the read: switch_off, production_host_refused, kill_switch_halted, not_a_kept_leaf, conflict,
  side_disagrees, outside_band, tip_passed, already_ordered, listing:*, demo_book_event_cap, demo_book_day_cap, cash:*, placement:* (mid gap, no book),
  submit_rejected. A read whose skip counts do not sum to the rows seen is a defect.

## 4. Settlement and voids
Each order joins to the market's settlement. **Void when the player sits** (market voided / refunded at the venue, or a 0-minute box
score on a market the venue did not settle on): the order leaves E1/E2/E3 denominators and is counted under `voided`. Partial fills
count as fills at the filled size, P&L scaled to the filled contracts. Fees: the venue's per-contract fee on every fill, deducted in E2.

## 5. Metrics (computed by the read, by leaf and pooled)
- **E1** fill rate = filled orders / submitted orders; count of filled and closed.
- **E2** P&L per filled bet after fees ($ per $1 stake).
- **E3** win rate on fills vs the would-have-won rate on non-fills (adverse selection): non-fills are scored at the order's own side and price to the market's outcome.
- Data epoch: NO-side demo fills before 2026-11-06T01:03:42Z were mirror-priced. This book starts after it, so all sides count, but the read still
  reports pre-epoch YES-only and post-epoch all sides separately.
- Treatment / control: the ADR-0072 assignment (hash share 0.5) is logged on every order; the read reports it, and no extra assignment is made.

## 6. Judged n (quant/variance.mde_clustered, games are the unit)
Inputs: per-contract net sd 0.5 (binary payout at mid-range prices; conservative), icc 0.10 (an assumption, re-estimated from the
first 100 games and the n* re-derived then, a dated edit to the READ, not to this rule), pooled across the 14 leaves.
`games_needed(sd 0.5, rows_per_game 10, icc 0.10, effect)`: effect 0.04 → 184 games; 0.02 → 734 games; 0.013 → 1,738 games.
(0.013 / 0.02 / 0.04 are the lowest, median and highest held-out means among the 14 kept leaves.)
**n\* = 734 games** with at least one filled order (effect 0.02, alpha 0.05 one-sided, power 0.80). Per leaf, n\* is far larger; **no
per-leaf verdict is issued; leaves are reported descriptively and tested only pooled** (BH not needed, one pooled test; per-leaf
tests, if any, go through `quant/multiplicity`). No score is read as a verdict below n\*.

## 7. Look date and modal outcome
- **Descriptive look: 2027-01-31** (E1 fill rate, skip counts, E3 split; E2 reported with its interval, **no verdict**, n < n\*).
- **Verdict look:** the first date with ≥ 734 games carrying a filled order, or 2027-04-15 (regular season end), whichever is first; if
  the season ends below n\*, the look is reported as underpowered with its MDE and the book carries into 2027-28.
- **Pre-registered modal outcome:** fill rate well under half (resting orders at the touch are adversely selected, per D6 arm-order
  reads); E2 interval spans zero; win rate on fills below win rate on non-fills; no leaf and no pooled verdict at the 2027-01-31 look.
  A positive pooled E2 above zero at n\* would be routed as RIDE/FADE confirmed in those leaves; negative or spanning zero is routed to
  ride / no bet in those leaves: "hypothesis closed (EXP-NBAPROPS-002, parked for R&D)", never a stop on the cell.

## 8. Future-data dependence
Nothing here is measurable until the operator approves the install by name and NBA nights with props pass. A dry run on today's slate
(orders OFF) is the only evidence available at build time.
