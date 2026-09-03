# HYP-011 — Pre-registration: moneyline-first LR track (Phase 2 reroute)

**Date:** 2026-09-03 · **Window:** T-517 · **Status:** ⚪ PRE-REGISTERED, not yet run — **NO MODEL HAS BEEN FIT**
**Trigger:** APR-0033 (ACCEPTED — Option 3, 2026-09-03, `00_ADMIN/APPROVALS_REGISTER.md`) — Phase 2 reroutes to
moneyline-first now, on the same infrastructure the FALSIFIED branch would have used, while HYP-010 stays
formally INCONCLUSIVE (box 2.3, `05_RESEARCH_EXPERIMENTS/HYPOTHESES.md`, unchanged by this document).
**EXP ID reserved:** **EXP-026** (verified free: highest assigned ID in-repo is EXP-025, `04_EXECUTION/ACTIVE_QUEUE.md`
independently states "Free IDs … EXP-026+" as of this session).

---

## Why this document exists, and why it is the only thing this session produces

LL-009 (`DECISION_LOG.md`, 2026-05-29): *"confirm hypothesis with minimal experiment before building supporting
component."* Born from EXP-012/EXP-013 falsifying HYP-006/HYP-007 after ~3-5 hours of infrastructure was built
on an unconfirmed premise. HYP-010's own pre-registration (`HYP010_PHASE2_PREREGISTRATION_2026-08-15.md`)
additionally learned a second, narrower lesson worth carrying forward here: an underspecified gate can fail
(or pass) for reasons that have nothing to do with the hypothesis — five parameters had to be fixed *before*
running to close that gap (benchmark timepoint, pregame filter, independent unit, revised prior, band
labeling). This document fixes the equivalent parameters for the moneyline track **in advance**, before any
LR model is fit, so that HYP-011's eventual result cannot be explained after the fact. Per this session's task
scope: pre-registration only. No model fit, no scoring, no backtest code, this session.

---

## Data source — verified this session, not assumed

**`KXMLBGAME` is captured by the production price-archiver.** `deploy/cron.conf` (348 lines total) runs the
archiver twice daily across a midnight wrap, both blocks including `KXMLBGAME` in `--series`:

```
*/20 22-23 * * *  ... archive_market_prices.py --series KXMLBGAME KXMLBSPREAD KXMLBTOTAL KXMLBTEAMTOTAL ...
*/20 0-5   * * *  ... archive_market_prices.py --series KXMLBGAME KXMLBSPREAD KXMLBTOTAL KXMLBTEAMTOTAL ...
```
(lines 347-348 — confirmed directly, not from a stale reference)

**Volume:** 30,302 `KXMLBGAME` observations already archived as of 2026-08-15 (HYP-010's own Finding 1,
`HYP010_PHASE2_PREREGISTRATION_2026-08-15.md`, measured from `exp_output/PRICE_ARCHIVE/prices_2026-08-*.jsonl`).
This session did not independently re-count the archive (the count is sourced from that prior, already-landed
measurement, not re-verified against raw files here — `exp_output/PRICE_ARCHIVE/` is empty in this fresh
worktree, matching T-507's own note that it must be re-synced from the VPS before any archive-reading script
runs). **Whoever executes EXP-026 must re-count the current archive before scoring** — this figure is a
2026-08-15 snapshot of a continuously-growing archive, not a live number.

**Archive window / cadence:** inherited from the same cron installation Phase 0-E already registered
(`0E.4`, `MARKET_EXPANSION_ACTION_PLAN.md`) — continuous since that install, ~14 games/day cadence assumed
consistent with the totals track (not separately re-measured for moneyline specifically).

---

## Model class — fixed, no distribution fit

**LR per ADR-0004** (production model class: LR + Platt scaling). Moneyline is a binary target (which team
wins) — unlike the totals track, it needs no distribution fit (Poisson/NB) at all; this is the entire premise
of the "Note on model class" that triggered this reroute. **No LR model has been trained or fit this
session** — ADR-0004's production class exists for player-prop targets today, not team-win targets, so a
moneyline-specific LR classifier is itself unbuilt. Fixing the model *class* in advance (LR, not a new
distribution family) is what this pre-registration authorizes; fitting it is explicitly out of scope for T-517
and belongs to whichever task executes EXP-026.

**Minimal feature set (LL-009 — no new C2 build for the confirming run):** team-level rolling features already
available from `MLBTeamStatsStore` (the same store HYP-010's totals track used, `get_opp_runs_scored` /
`get_opp_runs_allowed`) plus home/away and rest-day indicators already computed elsewhere in the pipeline. No
new ingestion, no new C2 matrix, for the minimal confirming experiment. A richer feature set is deferred to
Phase 2 box 2.7 (`MARKET_EXPANSION_ACTION_PLAN.md`), and only if this experiment PASSes.

---

## H0 / H1

**H0 (Null):** an LR model fit on `MLBTeamStatsStore`'s existing rolling series (no new C2 build) produces
**P&L per bet ≤ 0, net of fill cost,** over the selected subset where `|model_p − mkt_p| > 0.010`, scored
against archived `KXMLBGAME` closing pregame prices.

**H1 (Alternative):** P&L per bet > 0 on that subset, net of fill cost, with `clean_n ≥ n*` where `n*` is
derived live from the realized mean/sd via `scripts/run_power_calc.py` (APR-0024: `n* = ((z_α + z_β) · σ / μ)²`,
one-sided α=.05, default power=.95).

---

## Test method — fixed in advance

- **Benchmark timepoint:** the closing pregame snapshot — the last archived `KXMLBGAME` quote available under
  the same TI-01-safe `as_of_date` cutoff mechanism the production LR pipeline already uses for T1 forecasts
  (no new cutoff invented; reuses existing infrastructure per LL-009).
- **Independent unit:** the **game**. Unlike the totals track (up to 12 lines per game, requiring a per-game
  averaging step — HYP-010 amendment (c)), moneyline carries exactly one market per game-event, so row-level
  and game-level qualifying-bet counts are identical by construction. No averaging step is needed; this is a
  genuine simplification versus the totals track, not an oversight.
- **Selected-subset rule (numeric, fixed):** `|model_p − mkt_p| > 0.010` — the same threshold HYP-010 used,
  "the same instrument every other band is already gated on" (HYP010 prereg, Finding 4).

---

## Primary metric — P&L/bet, NET of fill cost (T-507)

**Primary gate:** `P&L/bet > 0 AND clean_n ≥ n*`, one-sided α=.05, **computed net of fill cost.** If
`clean_n < n*` the verdict is INCONCLUSIVE — EXTEND ARCHIVE, explicitly not FALSIFIED.

**Why net-of-fill is a hard requirement, not a refinement:** T-507 (`DECISION_LOG.md`, 2026-08-31) re-ran
T-488/GG-157's fill-haircut measurement against the repaired epoch-12 ledger and found the haircut consumed
**~65% of gross edge** on T4M-PROJ — mean P&L/bet **$0.0540 gross → $0.0191 net** ((0.0540−0.0191)/0.0540 =
64.6%). A gate scored gross-of-fill on this magnitude of haircut is not measuring a smaller version of the
same quantity — it can show a comfortably positive PASS on a result that nets to a materially thinner or even
negative one. **HYP-011 must be scored using the same fill-haircut methodology T-507/GG-157 established
(`scripts/gg157_fill_haircut_analysis.py` / `scripts/t507_gg157_haircut_rerun.py`), applied to this
experiment's own fills — not reported gross.** A result reported only gross-of-fill does not satisfy this
pre-registration's primary gate and must not be treated as a PASS or FALSIFIED verdict; it is not scored.

**Secondary (descriptive, not a gate):** Brier vs. market-implied probability, paired per-game. Reported with
CI and measured power; never used as a gate, per the same reasoning HYP-010's own Finding 3 established
(Brier is underpowered by roughly an order of magnitude relative to the P&L/bet metric at realistic archive
sizes).

---

## Verdict states — exactly three, matching this plan's existing convention

- **PASS** — P&L/bet > 0, net of fill cost, at `clean_n ≥ n*`.
- **FALSIFIED** — P&L/bet ≤ 0, net of fill cost, at `clean_n ≥ n*`.
- **INCONCLUSIVE — EXTEND ARCHIVE** — `clean_n < n*`. Explicitly not FALSIFIED.

No other verdict state is defined. A result reported gross-of-fill only (see above) is not any of these three
— it is not scored at all.

---

## Pre-registered effect band

**Expectation: P&L/bet (net of fill cost) in the range +0.003 to +0.015.** Set *tighter* than HYP-010's
totals-track band (+0.005 to +0.025), not equal to it, for a stated reason: CLAUDE.md's own "Market
efficiency gradient" section frames game-market expansion (moneyline, spread, totals) as movement toward the
*most*-attended, most efficiently-priced end of the board — the opposite end from the thin-liquidity props
cell (`KXMLBHIT`) where the strategy is designed to work — and names moneyline specifically as flagship,
highest-attention inventory. If totals (a secondary game market) is expected to produce thinner edge than
props, moneyline should be expected to produce thinner edge still, not equal edge. This has not been measured
this session (no half-spread pull was run against `KXMLBGAME`, unlike HYP-010's Finding 2 for `KXMLBTOTAL`) —
it is a reasoned prior, not a measurement, and should be corrected against a real half-spread pull before the
experiment executes if that turns out to change the picture materially.

**Suspect threshold: a result above +0.020 (net of fill cost) should be treated as suspect and audited for
leakage before being believed, not celebrated** — set below HYP-010's +0.03 threshold for the same
tighter-band reasoning above.

---

## Consequences (fixed in advance, per LL-009's own lesson — do not decide these after seeing a result)

- **If PASS:** Phase 2 box 2.6 clears; box 2.7 (additional feature/build work) is authorized, scoped by
  whatever this run's own results indicate is needed — not decided here.
- **If FALSIFIED:** the moneyline-first track itself is falsified. This is a different event from HYP-010's
  own verdict (which remains INCONCLUSIVE, untouched) — a FALSIFIED HYP-011 would leave Phase 2 without a
  currently-defined next reroute target in this plan; that gap, if it occurs, is a new decision for the
  operator, not resolved in advance here.
- **If INCONCLUSIVE:** continue archiving `KXMLBGAME`; re-run at `n*`. Cadence and time-to-`n*` not yet
  projected for this market (no equivalent of HYP-010's Finding 4 table has been run for moneyline this
  session) — that projection belongs to whoever executes EXP-026, using the actual measured effect size
  and variance from this archive, not assumed in advance.

---

## Band / cell scope (GG-172 discipline — do not assume T4)

This model, as specified, is pregame and rolling-stat-driven (no live in-game state) — it is a **T1 signal**,
analogous to HYP-010 amendment (e)'s finding for the totals track. A PASS on EXP-026 is evidence for the cell
`(mlb_moneyline, T1_MULTI_DAY)` specifically (`c5_execution/market_type_registry.py`) — **it is not evidence
for, and does not touch, any `T4M-*` cell**, and activation of any cell still requires its own ADR per
ADR-0058's process. This document does not initiate that.

---

## What this document does NOT do

- Does not fit, train, or score any model. No code has been run against `KXMLBGAME` data this session.
- Does not touch `kelly_fraction`, any cell status, or the price-archive cron.
- Does not relabel HYP-010's box 2.3 verdict (`HYPOTHESES.md`) — that remains INCONCLUSIVE — EXTEND ARCHIVE,
  both the Poisson (T-487/EXP-022) and NB (T-500/EXP-025) runs, unchanged.
- Does not assign a session/task to actually execute EXP-026 — that is separate, future work.
