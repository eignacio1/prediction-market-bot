# T-571 Results — Ledger Integrity Audit

**Session:** `session/20260923T234404Z-ledger-integrity-audit` · **Date:** 2026-09-23 · **Tier:** STANDARD
**Deliverable:** establish whether recorded positions represent real trades.
**Scope:** read-only. No ledger row edited, excluded, or re-stamped anywhere in this session. No `clean_n` restated. No cell status, kelly_fraction, or constant changed.

---

## 0. Why this audit ran

Two independent HIGH findings from the prior wave (T-568) said the ledger misrepresents reality:
- **GG-295** — 42 NFL rows' `kalshi_threshold` backfill has no corresponding commit anywhere, falsely attributed to T-562.
- **GG-297** — 139 of 140 T4M-PROJ positions marked OPEN (dated 2026-09-22) were found `canceled`/zero-fill at Kalshi; only 1 carried a genuine fill.

T4M-PROJ's 765-row epoch-12 clean cohort is the only scorable cohort in the project, and T-565's calibration figures (the project's one demonstrated finding) are computed from it. If it contains phantoms, that finding is unsound. This session's mandate was to find out.

---

## 1. Deliverable 1 — phantom-fill test on all 765 epoch-12 T4M-PROJ closed rows

Extended GG-297's per-order Kalshi verification (`GET /portfolio/orders/{order_id}`, `authenticated=True` per T-556) from its original 140-row 2026-09-22 sample to every epoch-12 T4M-PROJ clean closed row, via `scripts/t571_verify_t4mproj_kalshi_fills.py`.

**Within T-565's exact original window (2026-07-31 → 2026-08-13, n=765):**

| Verdict | Count | % |
|---|---|---|
| FILLED | 34 | 4.4% |
| CANCELED | 0 | 0.0% |
| NOT_RETRIEVABLE | 731 | 95.6% |

**Full current ledger (905 rows, 2026-07-31 → 2026-09-22):** 35 FILLED / 139 CANCELED / 731 NOT_RETRIEVABLE. The 139 CANCELED rows are the same ones GG-297 flagged as phantom-OPEN on 2026-09-22 — they have since resolved-to-CLOSED with a recorded outcome/pnl, confirming the contamination GG-297 warned about has occurred.

**Retention boundary:** NOT_RETRIEVABLE ≠ confirmed-fake. A follow-up ticker-level crosscheck (`scripts/t571_ticker_crosscheck.py`, `GET /portfolio/orders?ticker=<ticker>`) sampled 30 of the 731 NOT_RETRIEVABLE rows (3 per affected game-date, 10 dates, 2026-07-31→2026-08-07): **30/30 show zero orders under any order_id.** This is evidence against a simple single-order-lookup retention purge and toward "never submitted" — but it is a 4.1% sample, not a census, and an unruled-out alternative (ticker-normalization mismatch between the ledger's `kalshi_ticker` field and Kalshi's own indexing) was not separately excluded. Registered as a correction to GG-300's Resolution row (2026-09-23).

**Governance record:** GG-300 (OPEN, HIGH) — "731 of 765 rows (95.6%) in the clean cohort have no independent Kalshi confirmation of ever being filled; only 34 (4.4%) are confirmed real."

---

## 2. Deliverable 2 — damage sizing: recompute T-565 with phantoms excluded

Used T-565's committed calibration script (`scripts/t565_calibration_model_vs_market.py`) **unmodified**, via a new wrapper (`scripts/t571_deliverable2_confirmed_only_recompute.py`) that imports its functions and applies them to filtered row subsets. Two variants, against the original 765-row window:

| | Original (T-565, n=765) | Variant A: exclude confirmed-CANCELED (n=765) | Variant B: confirmed-FILLED-only (n=34) |
|---|---|---|---|
| model_brier | 0.2191 | 0.2191 (identical — 0 rows excluded) | **0.2730** |
| market_brier | 0.1890 | 0.1890 | **0.1415** |
| skill vs. climatology | (positive, T-565) | (positive, unchanged) | **−0.156** |
| paired diff, bet-level | +0.0301 (t=5.66) | +0.0301 (t=5.66) | +0.1314 (t=4.92, df=33) |
| paired diff, day-clustered | +0.0593 (t=2.87, n=11) | +0.0593 (t=2.87, n=11) | +0.1115 (t=3.12, n=9) |
| win_rate | 0.405 | 0.405 | **0.176** |
| total P&L | +$39.73 | +$39.73 | **−$6.78** |

**Variant A** reproduces the original baseline exactly, because zero rows in-window are confirmed-CANCELED (all 139 CANCELED rows are from the later 2026-09-22 batch, outside this window) — expected, not new information.

**Variant B is the material finding:** on the only subset independently confirmed as real trades (n=34), the model is *worse* than the market (higher Brier), worse than a climatology baseline (negative skill), the paired-difference statistic runs in the *model's favor as an artifact of poor market calibration on this subset* rather than model skill (see caveat below), and realized P&L is negative. This is the opposite of T-565's headline.

**Caveat, stated for the record:** n=34 is small, non-randomly selected (selection is "which orders happened to retrieve cleanly," not a designed sample), and spans only 9 game-days. No statistical correction for selection bias and no power analysis were attempted — that work belongs to session "33.1"'s analysis-script territory, out of this session's scope. This is registered as a finding requiring further work, not a proven disproof of T-565.

**Governance record:** GG-301 (OPEN, HIGH) — "T4M-PROJ's calibration headline reverses sign and turns net-negative when restricted to Kalshi-confirmed-filled rows only (n=34 of 765)."

---

## 3. Deliverable 3 — NFL row provenance

**Question:** which model wrote the 20 settled + 22 open NFL rows, and is it traceable?

**Finding — MODEL provenance, resolved:** all 42 rows carry `model_identity = "EXP-027 LR (T-531, HYP-012, verdict UNDERPOWERED)"`, exactly matching `EXP027NFLForecastModel.PROVENANCE` in `nfl_exp027_adapter.py`. This is **not** `StubNFLForecastModel`, the default GG-255 warned would silently fire if nothing wired the real model in (`run_t1_nfl_game_market.py::main(model=None)`).

**Finding — RUN-EVENT provenance, resolved:** `audit_t1_nfl_game_market.jsonl` contains exactly two manual paper-trader sessions:
- `PT-T1-NFLGM-4B36EB7E`, 2026-09-15, 24 risk evals, **0 approvals, 0 positions** (consistent with GG-263's "one logged run produced zero positions").
- `PT-T1-NFLGM-22640C8C`, 2026-09-17T00:25:48–00:27:00Z (~72 seconds), 46 risk evals, **42 approved, 42 opened** — an exact match to the ledger's 42 rows.

**Finding — ACTOR provenance, NOT resolved:** the `approval_commit` field recorded on every row is a single value, `66bb0d3c6fff57b2dd75ffc2241ece102fac78f5` (2026-07-31, GG-149's T4-MLB offsetting-position commit — content unrelated to NFL). Code inspection of `logic_epoch.py` confirms this field is `CURRENT_APPROVAL_COMMIT = _BOUNDARIES[-1].commit_sha` — a static epoch-boundary marker baked into the source tree at whatever point it was last edited, **not** a live git-HEAD-at-runtime capture. It cannot identify which commit or session executed the 2026-09-17 manual run. No cron entry exists for NFL. No `DECISION_LOG.md` entry references an NFL run around that date. No artifact examined identifies who ran this, from where, or under what review.

**Disposition:** all 42 NFL rows are **QUARANTINED** from G6 evidence, calibration, and `clean_n` as a standing constraint (GG-302, OPEN, HIGH) — not because the model or the run are unknown (they are now known precisely), but because the run was manual, unlogged, unreviewed, and its human actor is unrecoverable. This is orthogonal to GG-295 (the threshold-backfill actor-provenance gap on the same 42 rows) — resolving one does not resolve or bear on the other; they are not to be conflated.

---

## 4. Deliverable 4 — evidence-base table (standing reference)

| Cohort | Rows | Verification status | Reasoning |
|---|---|---|---|
| **T4M-PROJ, epoch-12 clean** | 765 closed (905 current) | **PARTIALLY VERIFIED** — 34 (4.4%) confirmed FILLED; 731 (95.6%) NOT_RETRIEVABLE (a 4.1% ticker-crosscheck sample leans toward "never submitted," not a census); 0 confirmed-CANCELED in-window (139 CANCELED rows exist only in the later 2026-09-22 batch, now resolved-to-CLOSED) | GG-300, GG-301, GG-297. T-565's headline (positive) holds on the full/unverified-inclusive cohort; **reverses to negative on the confirmed-real 34-row subset** (GG-301) — small n, not statistically adjudicated. |
| **NFL T1 game-market** | 20 settled + 22 open | **QUARANTINED** | GG-302. Model and run-event provenance resolved (EXP-027 LR, single ~72s manual run 2026-09-17); actor/authorization provenance unrecoverable (no cron, no DECISION_LOG entry, `approval_commit` is a static epoch marker, not a runtime capture). GG-295's separate threshold-backfill actor-provenance gap remains open on the same rows. |
| **T1 MLB** | (see GG-004 / MEMORY_BANK.md for live n — not restated here) | **NOT TESTED THIS AUDIT** | Deliverable 1's phantom-fill test was scoped to T4M-PROJ only, per this session's task instruction. No Kalshi order-record verification has been applied to T1 MLB rows in this audit. Recommend the same test be run before any T1 MLB figure is used as confirmed-real evidence — this is a gap in coverage, not a clean bill of health. |
| **T2 MLB** | (see GG-004 / MEMORY_BANK.md for live n) | **NOT TESTED THIS AUDIT** | Same reasoning as T1 MLB. Additionally, GG-004's own history records T2 MLB `clean_n` has been near-zero/underpowered at various points (see GG-004, GG-124) — a separate sample-adequacy question this audit does not touch. |
| **NBA (all bands)** | — | **FROZEN / NOT APPLICABLE** | NBA is DARK per standing operator directive (tabled until ~1 month before 2026-27 season). Not part of active G6 pursuit; this audit does not score it and found no reason to change that status. |
| **`rejected_positions`** | 2,016 | **STRUCTURALLY OUT OF SCOPE (confirmed)** | GG-298. Code-level check this session confirmed `build_rows()` structurally excludes all 2,016 rows from any scored cohort (`deliverable_4_rejected_cohort: n=0`) — these are post-approval exchange-side execution failures, not risk-engine declines, and were never eligible to be scored. Independent confirmation of an existing finding, no new defect. |
| **T3 MLB, T5 (all sports)** | raw_n≈0 / never traded | **OUT OF SCOPE — no data exists to verify** | Per CLAUDE.md's live band registry: T3 `raw_n=0`, T5 never traded. Not part of this session's D1-D3 mandate and not independently re-checked here. |

**Backlog check:** searched for a gap-candidate backlog handed over by sessions "33.1" or "33.3" under those or similar identifiers (recent `SESSION_CLAIMS.md` rows, GG entries referencing those labels, open T-numbers) — none found under that name. No backlog items to clear this session.

---

## 5. Bottom line

**Does the project's one real calibration finding still stand?**

Not unconditionally. T-565's positive result (model beats market on Brier score, positive paired-difference statistics, positive P&L) is real **as computed against the full 765-row cohort as it currently exists in the ledger** — Variant A, which changes nothing, reproduces it exactly. But that cohort is now known to be 95.6% unconfirmed as real trades, and the 4.4% (n=34) that *is* independently confirmed real shows the **opposite** result: worse-than-market Brier, negative skill, and a net loss. 

The honest statement is: **the full-cohort finding stands as a description of what the ledger says; it does not yet stand as a description of what happened on the exchange.** The confirmed-real subset is too small (n=34, non-randomly selected, no bias correction attempted) to either confirm or overturn T-565's conclusion on its own — but it is large enough, and the discrepancy stark enough, that the finding cannot be called settled until either (a) the 731 NOT_RETRIEVABLE rows are resolved one way or the other, or (b) a properly-powered analysis of selection bias in "which orders retrieve cleanly" is done. Both are registered (GG-300, GG-301) as open, not deferred silently.

Repair, exclusion, or any change to what counts as the project's live cohort is the operator's decision (GG-228 applies) — this audit diagnoses only.
