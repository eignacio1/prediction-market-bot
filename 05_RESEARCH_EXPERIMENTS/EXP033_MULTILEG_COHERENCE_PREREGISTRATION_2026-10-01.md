# EXP-033 — Multi-leg coherence of Kalshi sports books: PRE-REGISTRATION

**Registered:** 2026-10-01 (UTC), before any coherence statistic (sum, monotonicity, dutch-book margin, placebo, p-value) has been computed on any set.
**Status: FROZEN on push.** Any change after this commit is an *amendment*, appended below with a date and reason; the original text stays intact. Nothing here may be edited to suit a result.

Coherence is arithmetic. No model is built, fit or tuned. No order is placed (demo or production), no pool, ledger, sizing, stake or `kelly_fraction` is touched. Data: `exp_output/PRICE_ARCHIVE` (read-only) and public unauthenticated Kalshi GET metadata.

## What was known when this was written (D1)
Structure only: which markets belong to which leg set, and how many runs each set has quotes in. Grouping is read from Kalshi's own metadata (event `mutually_exclusive`, market `strike_type`/`floor_strike`, team/player uuid in `custom_strike`), not from ticker strings; the event-ticker suffix is used only as a join key and is verified against event `sub_title` (0 mismatches across 1,039 game keys) and team uuids. All 84,786 archived tickers map to metadata. Every settled mutually-exclusive set (MLB GAME 780, F3 757, F5 756, F7 760, NFL GAME 48) had exactly one YES. Frozen grouping: `exp_output/EXP-033-MULTILEG-COHERENCE/d1_grouping.json`, sha256 `223b7e3dad6cfa94411a57ee2fcea6a3f8c71eb11db92306ff56de4e457b06bb`. No settlement-vs-quote comparison and no price comparison across legs was made.

## Relation types (what is and is not tested)
- **Complementary** (event `mutually_exclusive=true`): MLB GAME (2 legs), F3/F5/F7 (3 legs incl. TIE), NFL GAME (2 legs). MLB sets are exhaustive (verified above). NFL GAME is treated as **non-exhaustive** (ties are possible; 48 settled sets is too few to rule them out), so only the buy-all-NO direction is tested for NFL.
- **Nested** (sub ⊆ super, so P(sub) ≤ P(super)): within-event ladders (strike_type `greater`, same team/player, rising `floor_strike`; **all pairs i<j**, not only adjacent) for TOTAL, F5TOTAL, TEAMTOTAL, SPREAD, F5SPREAD, HIT and the NFL equivalents; cross-family edges SPREAD⊆GAME, F5SPREAD⊆F5 (matched by team uuid, TIE leg excluded), TEAMTOTAL⊆TOTAL and F5TOTAL⊆TOTAL (matched on equal floor). Unmatched floors are excluded and counted.
- **Related** (same game, no arithmetic constraint): counted in the distribution, **not tested**. Also untested: mutual exclusion of opposite-team SPREAD legs.
- **Implication validity gate:** an edge family is dropped, and reported as dropped, if any settled instance has sub=yes and super=no. Exhaustiveness gate for complementary families: dropped if any settled set does not have exactly one YES (NFL excepted, already non-exhaustive).

## Observation, quote-time window
An observation is a (set, run_ts). **Window rule:** every leg must carry the **identical** `run_ts`, status `active`, and an executable quote; legs from different runs are never combined (except in the placebo below, on purpose). `run_ts` is a run-level stamp: intra-run skew between legs is unknown and is a disclosed limit, not corrected. Duplicate (ticker, run_ts) rows: first kept, count reported. Executable quote = `yes_ask` and `no_ask` both parse and lie in (0, 1) — a leg with ask 0 or 1.0 (no real offer) makes the observation untestable (counted, not imputed). MLB families share run_ts; NFL families are on their own cadence; MLB and NFL are never mixed.

## Tests and cost model
Position = set of (side, ask) legs; margin per $1 guaranteed payoff = guaranteed minimum payoff − Σ ask paid − Σ fees. **Fee:** `0.07·p·(1−p)` per contract at the price paid (ADR-0016, `paper_trader.py:505`; cited as the in-repo model, **not a verified venue constant**). Prices rounded to 4 dp; violation = margin > 0 strictly.
1. **Sum coherence (complementary).** BUY-ALL-YES: payoff 1, margin = 1 − Σ yes_ask − Σ fee (exhaustive sets only). BUY-ALL-NO: payoff n−1, margin = (n−1) − Σ no_ask − Σ fee (all complementary sets). Descriptive only: overround Σ yes_mid − 1.
2. **Monotonicity (nested), every edge (sub, super).** Buy YES(super) + NO(sub): payoff 1, margin = 1 − yes_ask(super) − no_ask(sub) − fees. Descriptive only: mid(sub) > mid(super).
3. **Dutch-book margin** = the margins above, which already include the cost of crossing every leg (asks are the crossing cost) and the fee. **Cost source:** the observed ask side plus ADR-0016. 44.1's execution-cost surface (GG-325/T-603) had **not landed** at registration, so it is not used. **Sensitivity:** substitute `mid ± H_family` (EXP-031's per-family median half-spread at the first-seen snapshot) for the ask, same fee. Reported alongside; the verdict uses the ask-side margin.
Three tiers per cell: (i) gross (margin before fees, ask side); (ii) net (margin > 0 after fees); (iii) net **and** persistent (net > 0 for ≥2 consecutive runs of that set in the sport's run sequence) **and** Holm-significant against the placebo.

## Null: chance violations from snapshot timing and stale quotes
**Timing-shift placebo.** For each real observation, rebuild the same set with each leg's quote taken independently from that ticker's immediately previous or next archived run (fair coin per leg); drop the placebo if any leg lacks that run. This deliberately desynchronises quotes by one run and measures the net-violation rate that non-simultaneity alone produces. **Test per cell:** paired by observation, clustered by **game key**; statistic = Σ over games of (real − placebo) net-violation indicators; one-sided sign-flip test over games, 10,000 flips, seed 20261001. A cell with real ≤ placebo is by construction not distinguishable from timing.
**Multiple testing:** Holm–Bonferroni at family-wise α = 0.05 over **all cells with ≥1 testable observation in D1**, where a cell = (family or edge-family) × relation × direction. The denominator is fixed by D1 and is not reduced for cells that show nothing.
**Uncertainty:** 95% game-cluster bootstrap (2,000 resamples, seed 20261001) on net-violation rate and median positive margin.

## Labels (each cell gets exactly one, in order)
1. **INCONCLUSIVE** — fewer than 30 distinct games with a testable observation.
2. **DROPPED (invalid relation)** — failed a validity gate.
3. **NO NET VIOLATION** — no observation with margin > 0 after cost.
4. **NOT DISTINGUISHABLE FROM TIMING/COST** — net violations exist but the cell fails persistence or Holm.
5. **SURVIVES** — tier (iii).
If nothing is SURVIVES, the report says so in the first line.

## D4 capacity (surviving cells only)
Per surviving cell: leg count; `top_of_book_contracts` per leg side as recorded in `depth_*.jsonl` (the side semantics will be stated from the archiver source in the write-up, not assumed here) **only where a depth row exists for that ticker at the identical run_ts** (EXP-031's depth is SAMPLE ONLY — absent depth is reported as unknown, never imputed); executable size = min over legs; **all-or-nothing** requirement stated: an unhedged partial fill loses its cost, so an n-leg set needs n simultaneous fills. No size is recommended.

## Interpretation limits (binding on the write-up)
- ~2 months MLB, ~4 weeks NFL, archive cadence 20 min; a 20-minute snapshot cannot see a violation that closes in seconds, nor prove one existed at an executable instant.
- Settlement wording differences (suspended/shortened games, voids) between legs of a cross-family edge are assumed away except via the settled-instance gate.
- "Multi-leg structures price more loosely than single legs" is answered only by whether any cell reaches SURVIVES; an arbitrage margin and EXP-031's calibration gap are not put on one scale.
- Nothing here authorises a parlay arm, a position, or any sizing.

## Frozen
Grouping file hash, relation definitions, window rule, quote validity, fee model, tiers, placebo construction, seeds, flip/bootstrap counts, Holm denominator, n threshold, labels.

## Amendments
(none)
