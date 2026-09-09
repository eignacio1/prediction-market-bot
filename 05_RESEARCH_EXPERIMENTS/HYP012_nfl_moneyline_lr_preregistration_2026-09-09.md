# HYP-012 — Pre-registration: NFL moneyline-LR test (per-cell discovery, first NFL cell)

**Date:** 2026-09-09 · **Window:** T-531 · **Status:** ⚪ PRE-REGISTERED, not yet run — **NO MODEL HAS BEEN FIT**
**Trigger:** Session task assignment (governance-protocol NFL moneyline LR experiment), STANDARD tier.
**ID reroute:** originally task-assigned `EXP-026`/`HYP-011` — both already canonically registered to a
pre-existing MLB moneyline experiment (`HYP011_moneyline_lr_preregistration_2026-09-03.md`, T-517/APR-0033).
Rerouted to **EXP-027**/**HYP-012** before any pre-registration content was written; GG-258 (OPEN, LOW)
documents the collision and root cause; `DECISION_LOG.md` 2026-09-09 (T-531) is the authoritative record.
Verified free by direct grep of this file and a repo-wide search, cross-checked against live `origin/main`
`SESSION_CLAIMS.md`.

---

## Why this document exists, and why it is the only thing this session produces before fitting

LL-009 (`DECISION_LOG.md`, 2026-05-29): *"confirm hypothesis with minimal experiment before building
supporting component."* Per Hard Rule 7 / this task's own hard rule: fitting before pushing this document
voids the experiment. This document fixes every parameter an NFL moneyline LR result could otherwise be
explained by after the fact — feature set, split rule, fill-cost convention, effect-size band, and `n*` —
before a single row is scored. **Per this session's explicit per-cell discovery doctrine: this result, however
it lands, is evidence about the cell `(nfl_moneyline, T1_MULTI_DAY)` only — it is not a verdict on NFL as a
sport, on any other market family, or on any other execution band, and must never be cited as one.**

---

## Data source — verified this session, live, not assumed

**Schedule (`NFLIngestionClient.fetch_schedule()`):** 7,548 total rows spanning seasons 1999–2026.
Per-season row counts confirmed directly: 2020=269, 2021=285, 2022=284, 2023=285, **2024=285**, **2025=285**,
2026=272. **2025 is fully completed** — `home_score` non-null = 285/285 (all games final). **2026 is fully
scheduled through week 18 but zero games have been played** — `home_score` non-null = 0, consistent with the
2026-09-10 season-opener framing. Confirmed columns: `game_id, season, game_type, week, gameday, home_team,
away_team, home_score, away_score, home_rest, away_rest` (the column is `game_type`, not `season_type`).

**Team efficiency stats (`NFLTeamStatsStore`, `c1_signal_ingestion/nfl_team_stats_store.py`, landed T-526/T-529,
per GG-253's explicit "recency-weighted" requirement):** already implements exponential-decay recency-weighted
`off_epa` / `def_epa_allowed` per team — `get_off_epa(team_abbr, as_of_date, window=DEFAULT_WINDOW,
min_periods=MIN_PERIODS, decay=DEFAULT_DECAY)` and `get_def_epa_allowed(...)` with the identical signature.
Constants confirmed by direct read: `DEFAULT_WINDOW=8`, `DEFAULT_DECAY=0.85` (half-life ≈4.27 games),
`MIN_PERIODS=3`. `fetch_team_stats(season=2025)` returns 570 rows (285 games × 2 teams, fully available);
`fetch_team_stats(season=2026)` returns 0 rows (confirmed cold-start/404-as-empty-DataFrame case, consistent
with the season not having started). No new C2 build needed for the efficiency features — this store already
exists and already implements the recency-weighting this task's brief asks for.

**`KXNFLGAME` price archive (VPS, `exp_output/PRICE_ARCHIVE/prices_2026-09-*.jsonl`, read-only measurement):**
daily `KXNFL` row counts: 09-01 through 09-04 = **0**; 09-05 = 827; 09-06 = 18,194; 09-07 = 9,924; 09-08 = 9,924.
**NFL price archiving began exactly 2026-09-05 — no historical closing-line data exists for any NFL season
prior to 2026.** This is a genuine, real constraint (not a design choice) that shapes the split rule below:
market-baseline comparison is only possible prospectively, against the 2026 season as it resolves, never
retrospectively against the 2015–2025 training/backtest window. `exp_output/PRICE_ARCHIVE/` is gitignored
(VPS/worktree-local only).

**`KXNFLGAME` microstructure, measured live (2026-09-06/07/08, n=2,944 active rows, 32 distinct
`event_ticker`s):** median `half_spread` = **0.005**, mean ≈ **0.00743**, min/max = 0.005/0.02, median
`yes_mid` = **0.5**. Schema confirmed: `run_ts, series_ticker, ticker, event_ticker, status, yes_bid, yes_ask,
no_bid, no_ask, last_price, previous_price, volume, volume_24h, open_interest, liquidity, close_time,
expiration_time, yes_mid, half_spread`.

---

## Model class — fixed, no distribution fit

**LR per ADR-0004** (production model class: LR + Platt scaling). Moneyline is a binary target (which team
wins) — no distribution fit needed, same reasoning as HYP-011's identical note for MLB. **No LR model has
been trained or fit this session.**

---

## Exact feature set — fixed in advance

Per game, from the home team's perspective (label = 1 if home team wins):

1. `off_epa_home` — `NFLTeamStatsStore.get_off_epa(home_team, as_of_date=gameday, window=8, min_periods=3, decay=0.85)`
2. `def_epa_allowed_home` — `get_def_epa_allowed(home_team, ...)`, same parameters
3. `off_epa_away` — `get_off_epa(away_team, ...)`, same parameters
4. `def_epa_allowed_away` — `get_def_epa_allowed(away_team, ...)`, same parameters
5. `home_rest` — from `fetch_schedule()`, days of rest for the home team
6. `away_rest` — from `fetch_schedule()`, days of rest for the away team
7. Home-field indicator is implicit in the home/away-split feature construction above (features 1–4 are
   computed separately for home vs. away, not pooled) — no separate dummy needed.

**Strength-of-schedule (SOS):** deferred, **not** in the fixed feature set above. Per this task's own
instruction ("if cheap, don't block on it"), SOS will be evaluated for cheap inclusion during the Deliverable
2 feature-build step, using only data already present in `NFLTeamStatsStore`/`fetch_schedule()` — no new
ingestion. That determination (included or excluded) will be made and committed as part of Deliverable 2,
**before any model is fit**, and is therefore a feature-availability decision, not a post-hoc parameter change.
If SOS is added, this document is not retroactively edited — the Deliverable 2 commit records the final
feature set actually used.

All features use `as_of_date` strictly before each game's kickoff (`gameday`), reusing the existing production
TI-01-safe cutoff mechanism (no new leakage-prevention code invented for this task).

---

## Train / test split rule — fixed in advance

Three-part split, driven directly by the data-availability findings above (not a preference):

1. **TRAIN: seasons 2015–2024** (10 completed seasons). Model fit on this window only.
2. **HELD-OUT BACKTEST: season 2025** (fully completed, 285/285 games with final scores). Strictly
   out-of-sample — the model is never fit on any 2025 game. **No market-baseline comparison is possible for
   this window** — no `KXNFLGAME` archive exists for 2025 (price archiving began 2026-09-05). Accuracy,
   calibration curve, and Brier score are reported against actual outcomes only for this window.
3. **PROSPECTIVE OUT-OF-SAMPLE TEST, WITH CLOSING-LINE COMPARISON: live 2026 season.** As 2026 games resolve,
   score the model (fit only on 2015–2024 data, never refit) against archived `KXNFLGAME` closing prices.
   This is the only window where performance vs. the market's closing-line implied probability can be
   reported, and it satisfies "strictly out-of-sample" most strongly (the games are in the future relative to
   training data by a full season or more).

**Explicit, provable leakage check (Deliverable 3 will run and report this, not merely assert it):**
- Assert every training-set game's `gameday` < 2025-01-01 (no 2025 or 2026 game contributes to the fit).
- Assert every `as_of_date` used to compute a test-set game's features is strictly before that game's own
  `gameday` (no same-day or future information).
- Assert the training `game_id` set and the test `game_id` set (2025 backtest ∪ 2026 prospective) are disjoint
  — zero intersection, checked directly, not assumed.
- Assert `NFLTeamStatsStore`'s recency window for any test-set feature draws only on games with `gameday`
  strictly before the test game's own `gameday`, regardless of season boundary (a Week-1 2026 game's rolling
  window correctly reaches back into late-2025 games only, never into any 2026 game already played that week
  or later).

---

## Fill-cost convention — defined independently this session, grounded in measured data

T-507's MLB fill-haircut methodology (`scripts/gg157_fill_haircut_analysis.py` / `t507_gg157_haircut_rerun.py`)
is an empirically-fitted haircut model calibrated specifically to `KXMLBHIT` player-prop fills (mean P&L/bet
$0.0540 gross → $0.0191 net in its most recent, T-507, re-run) — no equivalent empirical fill-haircut study
exists for NFL game markets, and building one is out of this task's scope fence. For NFL moneyline, net-of-
fill-cost P&L is instead computed using the **standard pay-the-ask/pay-the-bid convention** for a two-sided
quoted market: a YES bet is filled at `yes_ask` (not `yes_mid`), a NO bet at `no_ask` (not `no_mid`) — i.e.
net P&L per bet = gross P&L computed at the mid, minus that bet's own `half_spread`. This is grounded in this
session's own measured `KXNFLGAME` microstructure (median `half_spread`=0.005, mean≈0.00743), not fabricated,
and is a strictly more conservative (harsher) haircut than assuming a fill at the mid. **This convention is
fixed before any fitting and will not be revised after seeing results.**

---

## Primary gate — fixed in advance

**P&L/bet > 0, net of fill cost (convention above), AND `clean_n ≥ n*`, one-sided α=.05, computed against the
2026 prospective window only** (the only window with an archived closing price to compare against). If
`clean_n < n*` the verdict is **UNDERPOWERED**, explicitly *not* a directional PASS/FALSIFIED — per this
task's explicit hard rule, an underpowered result must be reported as UNDERPOWERED and must not be forced into
a directional verdict.

**Pre-registered expectation:** **P&L/bet (net of fill cost) in the range +0.003 to +0.015** — reused from
MLB HYP-011's band, additionally grounded here by NFL's own measured `KXNFLGAME` half-spread (0.005–0.0074)
being the same order of magnitude as MLB's moneyline microstructure that motivated that band. Moneyline sits
at the most-attended, most efficiently-priced end of the board (CLAUDE.md § "Market efficiency gradient"), so
thinner edge than a props-style market is the expectation, not a disappointment. A result above **+0.020
(net)** should be treated as **suspect and audited for leakage before being believed**, not celebrated.

**Falsification condition:** P&L/bet ≤ 0, net of fill cost, at `clean_n ≥ n*`.

---

## `n*` — worked arithmetic (APR-0024), shown per task instruction

Formula (confirmed exactly matching both this task's brief and `scripts/run_power_calc.py`'s own
implementation): **`n* = ((z_α + z_β) · σ / δ)² = k · σ² / δ²`**, one-sided α=.05, power=.95 ⇒
`z_α = z_β = 1.645`, `z_α + z_β = 3.290`, `k = 3.290² = 10.824`.

**σ (illustrative, pre-registered now):** for a $1-payoff binary contract priced `p`, net P&L per bet is
`(1−p)` w.p. `p_true` or `−p` w.p. `(1−p_true)`; under a well-calibrated null this gives `Var(PnL) = p(1−p)`,
maximized at `p=0.5` ⇒ `σ = 0.50`. This is a conservative (maximal-variance) bound, additionally grounded by
this session's own measurement of median `yes_mid = 0.5` across live `KXNFLGAME` rows.

**δ (illustrative, pre-registered now):** the pre-registered expectation band, +0.003 to +0.015 (above).

```
n* = 10.824 × 0.50² / δ²

δ = 0.003:  n* = 10.824 × 0.25 / 0.000009   = 2.706 / 0.000009   ≈ 300,667
δ = 0.015:  n* = 10.824 × 0.25 / 0.000225   = 2.706 / 0.000225   ≈ 12,027
```

Both figures vastly exceed any realistic per-season clean-bet count (285 games/season before the
`|model_p − mkt_p| > 0.010` selection filter reduces it further), and the 2026 season has just started with a
price archive only five days old as of this writing. **This session pre-registers the expectation, in
advance, that the primary gate will resolve UNDERPOWERED, not that this is a discovered excuse after running
the numbers.** The actual gate `n*` will be re-derived live from the realized 2026-window mean/sd via
`scripts/run_power_calc.py` (APR-0024) at scoring time, exactly as HYP-011 (MLB) pre-registers — the σ/δ
figures above are the pre-registration-time illustrative calculation this task's brief explicitly requires,
not a substitute for the live re-derivation.

---

## Secondary (descriptive, **not** a gate)

Calibration curve + Brier score, reported for **both** the 2025 held-out backtest (vs. actual outcomes only —
no market baseline available) and the 2026 prospective window (vs. actual outcomes **and** vs. the archived
closing-line implied probability, explicitly, not vs. a coin flip). Never scored as a gate — Brier is
underpowered relative to P&L/bet at any realistic archive size, same reasoning as HYP-010/HYP-011's identical
note.

---

## Consequences

| Verdict | Consequence |
|---|---|
| PASS (confirmed) | Evidence for cell `(nfl_moneyline, T1_MULTI_DAY)` specifically — not for NFL as a sport, not for any other market family or band. Cell activation still requires its own ADR. |
| FALSIFIED | The `(nfl_moneyline, T1_MULTI_DAY)` cell specifically is falsified. Per per-cell discovery doctrine, **this result must never be cited as a reason to deprioritize NFL, any other NFL market family, or any other sport.** |
| UNDERPOWERED (expected, given the price archive is 5 days old) | Continue archiving `KXNFLGAME` through the 2026 season; re-run at `n*` once reached. No directional verdict is claimed. |

---

## Explicit DO NOTs (restated from task scope, binding on this experiment)

Never change a pre-registered parameter after seeing results. Never relabel a pre-registered verdict after
seeing it. Never recommend against NFL, any other sport, or any other market family from this result. Never
wire into live/paper execution. Never touch `kelly_fraction`. Never place or settle any position.

---

**Status:** ⚪ PRE-REGISTERED (2026-09-09, T-531) — **no model fit, no scoring, no backtest code run this
session before this document was pushed (LL-009 / this task's hard rule: fitting before pushing voids the
experiment).**

**Experiment ID:** EXP-027 (verified free this session; see GG-258 / `DECISION_LOG.md` 2026-09-09).
