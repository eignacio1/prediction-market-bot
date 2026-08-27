# ADR-0059 — T1 Game-Market Flat Measurement-Stake Safety Wrapper (T-497/GG-218)

**Status:** ACCEPTED. DS sign-off: operator, in-session, 2026-08-26 ("Note: I approve the
ADR - sign off confirmed."), following the same pre-granted-sign-off pattern ADR-0050 itself
used. Authorizes exactly what Section 5 below says and nothing more: zero `kelly_fraction`
change, zero cell-status promotion, zero write to the live ledger or any production pipeline.
**Date:** 2026-08-26
**Author:** Session T-497 (`t497-t1-flat-stake-wrapper` worktree)
**Registers/depends on:** `ADR-0050` (2026-07-30, ACCEPTED — the flat measurement-stake
mechanism this ADR extends). `ADR-0058` (2026-08-25, PROPOSED — confirmed all nine
`(MarketType, T1_MULTI_DAY)` game-market cells exist at `NOT_IMPLEMENTED`; explicitly deferred
designing this wrapper as out of scope, §3/§8). `ADR-0048` (2026-07-29, ACCEPTED — zeroed
`T1_MULTI_DAY.kelly_fraction` to 0.0 on GG-135's ruin geometry; unmodified by this ADR).
`T-488`/`GG-157` (2026-08-26 — synthetic per-family fill-haircut measurement this ADR's bound is
grounded in). `GG-218` (reserved for this session — used below, see Section 6).
**Scope:** `src/prediction_market_bot/c5_execution/measurement_stake.py` (new module),
`scripts/assert_ledger_invariants.py` (two new assertions), `tests/test_measurement_stake_t1.py`
(new). Does not touch `execution_bands.py`, any `kelly_fraction`, the cell registry, `risk.py`,
or the ledger. Not wired into `run_mlb_paper_trade.py` or any live pipeline — those files are
outside this session's scope fence, so this ADR authorizes a design + implementation, not an
activation.

---

## 1. Context — what ADR-0050's wrapper guarantees, and which guarantees are T4-specific

ADR-0050 introduced two things that this session's investigation (verifying `risk.py`,
`paper_trader.py`, and `run_t4_mlb_live.py` directly) found are conflated in practice but are
architecturally separable:

**(A) The core bypass** — `evaluate_forecast(fixed_stake_usd=...)` in `risk.py`. When supplied,
this routes around the `kelly_size_zero` rejection path entirely; `approved_size` is set to the
flat dollar figure directly, and every other check (edge threshold, direction consistency,
single-event cap, min-bet floor, kill switches, aggregate deployment) still runs normally. This
mechanism references no band, no sport, and no market type anywhere in its implementation. It
already works for T1 with zero code change — confirmed directly: `run_mlb_paper_trade.py`
already constructs its `RiskEngine` with `min_bet_usd=MIN_BET_PAPER=1.0`, so a $1.00 flat stake
already clears every existing gate without modification.

**(B) The safety and hygiene wrapper** — everything in `run_t4_mlb_live.py` that decides *what*
flat stake to request before calling (A): the stake/contract-cap formula
(`measurement_stake_and_stratum`), price-stratum sampling, and same-session wash-trade
suppression. This wrapper is T4-shaped by construction — it was built against T4's specific
operating cadence, and every guarantee it makes is a guarantee *about* that cadence:

| T4's wrapper assumes | T1's actual reality |
|---|---|
| 45-90s in-play polling cadence; a stale decision self-corrects within a minute | Nightly cron, 21:30 UTC once/day (`execution_bands.py::BAND_CONFIGS[T1_MULTI_DAY]`, `execution_sla_s=3600` — "execution timing immaterial at this horizon") |
| Same-day resolution — the game ends hours after entry | Multi-day horizon — a position opened tonight is not evaluated again until `apply_resolved_hits.py` finds a matching resolved outcome, whenever that is |
| An intraday exit path is live and expected (`exit_position()`, ADR-0018/0019, called from the same live loop) | No intraday exit for T1 — positions are opened once per night and left OPEN until batch resolution |
| Wash-trade suppression scoped to *one live session's* repeated evaluation of the same ticker every ~60s | T1 evaluates each market once per run; the relevant duplicate-entry risk is *cross-run* (does tonight's run re-enter a ticker still open from two nights ago), not intra-run |
| Staleness risk = ESPN/Kalshi live data going stale mid-poll (`CONTAMINATION_HALT`) | Staleness risk = pregame state going stale between data pull and market close (lineup swaps, scratches, postponement) — a different failure mode entirely, already out of scope for a sizing wrapper |
| One deep, well-attended family (KXMLBHIT props) — no fill-cost problem observed | Nine game-market cells (`ADR-0058`) with measured haircuts running 3-5x props' median, tail to ~$0.42/contract (`T-488`/`GG-157`, see Section 2) |

**What this table is not:** a claim that T4's wrapper is wrong for T4. It is a claim that
copying it verbatim for T1 would silently carry T4-specific assumptions — same-day resolution,
intraday self-correction, an active exit path — into an environment where none of them hold.

---

## 2. The new mechanism T4 never needed: a fill-cost (haircut) bound

`T-488`/`GG-157` (2026-08-26, synthetic measurement against the uncorrected epoch-12 ledger,
family-level nearest-in-time join — a caveat this ADR preserves, not launders) found:

| Family | Mean haircut/contract | Other stats |
|---|---|---|
| Props baseline (real, measured) | $0.0101 | median $0.0100 |
| GAME_WINNER (`mlb_moneyline`) | $0.0340 | median $0.0350 |
| GAME_TOTAL (`mlb_game_total`) | $0.0307 | p90 $0.0800, max $0.4200 |
| RUN_LINE (`mlb_run_line`) | $0.0515 | p90 $0.1500, max $0.4050 |

Game markets run 3-5x props' median haircut, with a tail reaching ~$0.42/contract. A $1.00 flat
stake sized purely on `entry_price` (ADR-0050's formula, unchanged) can fill at a materially
worse effective price than quoted mid on a thin game-market book — the stake formula itself
never sees this, because it was never designed to.

**Decision:** the new wrapper (`c5_execution/measurement_stake.py`) requires the caller to
supply a freshly measured per-contract haircut estimate at decision time and refuses the trade
(raises `MeasurementStakeRefused`, not a silent `None`) if:
- no measurement is supplied (never assume zero haircut — per CLAUDE.md's standing rule that
  depth/spread figures must be measured live, never taken from a remembered constant), or
- the measurement exceeds `T1_MAX_HAIRCUT_PER_CONTRACT_USD = 0.10`.

That bound is set at GAME_TOTAL's p90 ($0.0800), rounded up — it clears GAME_WINNER's median
comfortably and most of GAME_TOTAL's distribution, while gating out RUN_LINE's p90 ($0.15) and
both families' tail maxima. It is deliberately a binding gate for the family T-488 found worst
(RUN_LINE), not a rubber stamp. It is a ceiling on a live-measured figure, not a substitute for
measuring it — consistent with CLAUDE.md's market-depth section, which is explicit that no fixed
depth/spread number may be cited as current.

This bound is scoped to the uncorrected, synthetic T-488 measurement (D1/ADR-0055's epoch-12
ledger repair is PROPOSED, not accepted) and to T-488's family-level nearest-in-time join method,
which that task's own SUMMARY.md calls weaker than the ticker-targeted decision-time capture
GG-157 already calls for (Phase 3/4, unstaffed). Re-derive if either supersedes it.

---

## 3. Whether the multi-day horizon needs a guarantee ADR-0050 doesn't express — HARD STOP evaluated, not triggered

The task governing this session named three candidate guarantees ADR-0050 does not express: a
cross-day exposure cap, a stale-position sweep, and an exit path. Each was checked directly
against the current codebase before concluding whether this constitutes new architecture
requiring its own ADR (HARD STOP) or is already covered by T1's pre-existing, sizing-mechanism-
agnostic design:

1. **Cross-day exposure accounting.** T1's bankroll is derived directly from the ledger's
   `open_positions` list (not a `game_date`-filtered reconstruction — that pattern was T4's own,
   separate historical bug, unrelated to T1). A position that stays OPEN across many nights
   (postponed game, resolution lag) continues to reduce the bankroll figure every subsequent run
   — capital stays conservatively deducted, it does not silently vanish from exposure accounting.
   This is unaffected by whether the position was Kelly-sized or flat-staked.

2. **Cross-day duplicate entry ("wash-trade" analogue).** Verified directly in
   `run_mlb_paper_trade.py` (lines ~892-897): every nightly run builds `_open_tickers` from the
   currently loaded portfolio's open positions and skips (`[IDEMPOTENCY] SKIP ... already open`)
   any ticker already present — regardless of how many nights it has been open. This is a
   pre-existing, generic T1 mechanism, not part of ADR-0050's wrapper, and it already closes the
   cross-run analogue of T4's same-session wash-trade suppression.

3. **Exit path.** T1 has none, by design (`execution_sla_s=3600`, "execution timing immaterial
   at this horizon") — positions resolve via `apply_resolved_hits.py`'s batch, `game_date`-keyed
   settlement, not an intraday exit. This is identical for every T1 position today, prop or game
   market, Kelly-sized or flat-staked. The flat-stake wrapper does not change this surface at
   all; it was never asked to.

**Conclusion: no new guarantee is required specifically because of this wrapper.** All three
candidates are pre-existing properties of T1's whole batch architecture, equally present (and
equally already handled, per items 1-2, or equally out of scope, per item 3) for today's live
Kelly-sized `KXMLBHIT` positions. The HARD STOP condition is therefore evaluated and **not
triggered** — this ADR proceeds to authorize an implementation rather than registering a new,
unresolved decision.

**One adjacent, genuinely open observation, registered rather than fixed (Hard Rule 11):** while
item 3 confirms T1 has no exit path by design, this session found no automated alarm firing if a
position sits OPEN well past a plausible resolution window (e.g., a postponed/rescheduled game
`apply_resolved_hits.py` never finds a match for). This is an operational monitoring gap, not a
sizing-wrapper defect — it is identical in kind for props today and is not introduced or worsened
by this ADR's mechanism. See `GG-218` (Section 6) for its registration; it is explicitly not
fixed by this ADR.

---

## 4. What generalizes from ADR-0050 unchanged, verified directly this session

- `risk.py::evaluate_forecast(fixed_stake_usd=...)` — zero code change needed.
- `paper_trader.py::open_position()` — `entry_price_paid`/`price_stratum`/`contracts` are already
  generic, opt-in fields read from the caller-supplied `approval` dict
  ("None for non-T4M-PROJ callers ... absence is not an error"). Zero code change needed.
- The stake formula itself: `stake = round(min(flat_stake, max_contracts * entry_price), 4)` —
  ADR-0050 §8(B)'s deliberate choice over a `floor()`-based integer-contract formula (which
  under-stakes non-round prices). T-497 found no game-market-specific reason to diverge from this
  invariant or from ADR-0050's $1.00 / 10-contract constants, so this ADR keeps them identical.
- The LOW (<$0.10) / MID ($0.10-$0.70) / HIGH (>$0.70) price-stratum boundaries — generic
  price buckets, not a T4-specific concept.

---

## 5. What this ADR authorizes

1. `src/prediction_market_bot/c5_execution/measurement_stake.py` — a new, standalone module
   implementing `t1_measurement_stake_and_stratum(entry_price, measured_haircut_usd_per_contract)`
   per Sections 2 and 4 above, scoped to the nine ADR-0058 `MarketType` values
   (`T1_GAME_MARKET_TYPES`). Not imported by any live pipeline.
2. Two new ledger-invariant assertions in `scripts/assert_ledger_invariants.py`
   (`assert_I2_t1_measurement_stake`, `assert_J2_t1_contracts_cap`) — the T1-scoped equivalents of
   `assert_I_adr0050_stake`/`assert_J_contracts_cap`, closing the `NO_FORMULA` gap T-466 flagged
   for T1 on those two assertions. Scoped by `market_type` membership rather than a floor epoch,
   since the mechanism has no live epoch yet.
3. `tests/test_measurement_stake_t1.py` — unit coverage of the stake formula, the fill-cost bound
   (including T-488's own measured figures as literal test fixtures — RUN_LINE's tail refused,
   GAME_WINNER's median cleared), and a synthetic dry-run proof that a fabricated T1 game-market
   record passes both new assertions while a `KXMLBHIT` prop record under the same band correctly
   continues to report `NO_FORMULA` (unaffected).

**Not authorized:** any `kelly_fraction` change, any cell promotion above `NOT_IMPLEMENTED`, any
edit to `run_mlb_paper_trade.py` or any production pipeline, any live or paper bet.

---

## 6. GG-218 registration

`GG-218` (reserved for this session) is used, not returned unused, for the operational-monitoring
observation in Section 3's closing paragraph: **T1 has no automated alarm for a position that
stays OPEN materially past a plausible resolution window (e.g., a postponed/rescheduled game
`apply_resolved_hits.py` never finds a matching outcome for).** Register as OPEN, LOW severity
(pre-existing, sizing-mechanism-agnostic, applies identically to today's live prop positions;
not introduced or worsened by this ADR). See `GOVERNANCE_GAP_LOG.md` GG-218 for the full entry.

---

## 7. Sign-off

**Status:** ACCEPTED. DS sign-off: operator, in-session, 2026-08-26 — explicit pre-authorization
("Note: I approve the ADR - sign off confirmed.") received before this ADR was drafted, applied
here per the same pattern ADR-0050 itself used. This ADR authorizes exactly Section 5's three
deliverables. It does not authorize activation, cell promotion, or any nonzero `kelly_fraction` —
those remain independently gated exactly as ADR-0058 §5 already states.
