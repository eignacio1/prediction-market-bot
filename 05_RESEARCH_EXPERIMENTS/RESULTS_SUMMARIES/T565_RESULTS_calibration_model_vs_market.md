# T-565 Results — T4M-PROJ Model-vs-Market Calibration: Reproduction, Comparability, Extension

**Status:** Deliverables 1–5 complete. Pre-registration (Deliverable 1) is immutable and
unchanged since commit `5f18a54` — nothing below relabels a criterion after seeing results.
**Script:** `scripts/t565_calibration_model_vs_market.py`. **Raw output:**
`exp_output/T565_calibration_benchmark/t565_results.json` (local only, not committed — see
§6 "What was not committed").
**Pre-registration:** `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T565_PREREGISTRATION_calibration_model_vs_market.md`.

---

## Deliverable 2 — Reproduction from the LIVE ledger

**Live pull vs. mirror.** The CLAIM was computed from a local mirror,
`logs/.vps_portfolio_cache_mlb_t4.json`, `last_updated: 2026-09-21T01:57:35Z`, 2994 closed
positions. The live VPS file (`paper_portfolio_mlb_t4.json`, pulled this session as
`paper_portfolio_mlb_t4.LIVE.20260922.json`) reports `last_updated: 2026-09-22T23:58:34.168Z`
and **also 2994 closed positions** — the closed-position count matches exactly even though
the live file is ~23h newer. The mirror was not stale in a way that affected this cohort:
no closed positions were added, resolved, or altered in the T4M-PROJ epoch-12 window between
the mirror's snapshot and this pull (rejected_positions count also matches: 2000 on both).

**Per-figure reproduction (T4M-PROJ clean, logic_epoch 12 clean-epoch floor):**

| figure | claimed | reproduced (live) | verdict |
|---|---|---|---|
| clean_n | 765 | 765 | REPRODUCED (exact) |
| closed positions (source file) | 2994 | 2994 | REPRODUCED (exact) |
| logic_epoch | 12 | 12 | REPRODUCED (exact) |
| game window | 2026-07-31..2026-08-13 | 2026-07-31..2026-08-13 | REPRODUCED (exact) |
| Brier | 0.2191 | 0.21909872... → 0.2191 | REPRODUCED |
| ECE | 0.0519 | 0.05188403... → 0.0519 | REPRODUCED |
| base rate | 0.4026 | 0.40261437... → 0.4026 | REPRODUCED |
| mean model_p | 0.3976 | 0.39756159... → 0.3976 | REPRODUCED |
| skill vs climatology | +0.089 | 0.08904734... → 0.089 | REPRODUCED |
| market Brier | 0.1890 | 0.18899794... → 0.1890 | REPRODUCED |
| paired diff, bet-level | +0.0301, se 0.0053, t=5.66 | +0.03010078 → 0.0301, se 0.00531666 → 0.0053, t=5.66159 → 5.66 | REPRODUCED |
| paired diff, day-clustered | +0.0593, se 0.0207, t=2.87, 11 days | +0.05925164 → 0.0593, se 0.02066927 → 0.0207, t=2.86665 → 2.87, n_days=11 | REPRODUCED |
| P&L | +$39.73 total, +$0.052/bet, win rate 40.5% | +$39.7288 → $39.73, +0.05193307 → $0.052/bet, 0.40522876 → 40.5% | REPRODUCED |

**All 13 figures REPRODUCED, exactly and within the pre-registered rounding bands.** The
claim was not a stale-mirror artifact — the mirror and the live ledger agree on every figure
tested. Deliverable 4 proceeds as pre-registration §3 allows.

**Materiality (pre-registration §4):** day-clustered `|t|=2.87 >= 2.0` **and** `|paired
diff|=0.0301 >= 0.01`. Both conditions hold — the model-underperforms-market finding on
T4M-PROJ clean is **material** by the pre-registered standard, not just nominally
significant at the noisier bet level.

---

## Deliverable 3 — Comparability with ADR-0046

Per pre-registration §6, comparability requires clean filter, directional convention, AND
band/threshold scope to all match. They do not:

| dimension | ADR-0046 (n=261, derived 2026-07-16) | this task's T4M-PROJ clean cohort (n=765) | match? |
|---|---|---|---|
| filter | `raw_n`, no clean-epoch gate (explicit, disclosed choice — epoch boundaries gate the *write path*, not `model_p`) | `is_clean_for_band(logic_epoch, "T4M-PROJ")`, clean-epoch gated | **NO** |
| directional convention | `p_estimate = model_p` (YES) or `1-model_p` (NO), `outcome=1` iff WIN | raw `model_p`, `y = actual_hits >= threshold` | **NO** — not proven to be the same quantity row-for-row |
| scope | `threshold ∈ {1,2}`, all MLB, not band-scoped | band-scoped to `T4M-PROJ` specifically | **NO** |
| epoch window | derived 2026-07-16, predates epoch 12 entirely | epoch 12, 2026-07-31..08-13 | **NO** (non-overlapping in time) |
| ECE binning | 10 equal-width bins on [0,1] | 10 equal-width bins on [0,1] | YES (only matching dimension) |

**Verdict: NOT COMPARABLE.** Every dimension but ECE binning mismatches. `BRIER_BASELINE_MLB
= 0.2190` / `ECE_BASELINE_MLB = 0.0680` cannot be read as "what T4M-PROJ epoch-12 Brier/ECE
should be" — they were derived from a different, broader, differently-filtered, differently-
dated population under a different directional convention. **The fact that the reproduced
Brier (0.2191) sits almost exactly on top of the ADR-0046 baseline (0.2190) is very likely
coincidence, not corroboration** — the two numbers are not measuring the same construction,
so their near-equality has no interpretive weight on its own.

What survives: nothing about T4M-PROJ's Brier/ECE being "in line with baseline" can be
claimed on this basis. What does NOT survive: any prior or future statement treating
ADR-0046's constants as a validity check for a band-scoped, clean-epoch-gated, directional
`model_p`-vs-`y` comparison — those are two different measurements that happen to share a
name ("Brier baseline").

**Supplementary check — does ADR-0046 reproduce from a fresh pull of its own source file?**
Not pre-registered as a numeric-tolerance test (§3 exempts cross-n comparisons from tolerance
scoring), but directly useful and in scope: `paper_portfolio_mlb.json` — ADR-0046's literal
source — was pulled live this session
(`paper_portfolio_mlb.LIVE.20260922.json`, `last_updated: 2026-08-06T00:05:01.517Z`, 468
closed positions, vs. ADR-0046's 2026-07-16 pull of n=261). Re-running ADR-0046's own filter
(`duplicate_of` excluded, `outcome ∈ {WIN,LOSS}`, `model_p` present, `threshold ∈ {1,2}`) on
this later snapshot:

| | ADR-0046 (2026-07-16) | this pull (2026-08-06 snapshot) |
|---|---|---|
| n | 261 | 468 |
| Brier | 0.2190 | 0.2200 |
| ECE | 0.0680 | 0.0832 |
| mean_p | 0.5660 | 0.5637 |
| mean_actual | 0.4981 | 0.4808 |

n grows as expected (three more weeks of T1/T2 accumulated between the two pulls — not a
discrepancy, just more data). Brier is close (+0.0010). **ECE has drifted materially: 0.0680
→ 0.0832, a +0.0152 absolute / +22% relative increase** on the same methodology applied to a
larger, later sample of the same source. This is a finding, not a fix: ADR-0046's ECE
baseline was a point-in-time estimate at n=261 and does not hold steady as more data accrues
under the identical construction — logged below as a gap candidate for 31.2, not corrected
here (ADR-0046's constants are explicitly out of scope to change, per task DO NOT).

---

## Deliverable 4 — Extension

### Per-cell table (MIN_N=30, game-day clustering, both sports attempted)

| cell | clean_n | status | model Brier | market Brier | paired diff | day-clustered t | span |
|---|---|---|---|---|---|---|---|
| T4M-PROJ | 765 | COMPUTED | 0.2191 | 0.1890 | +0.0301 | 2.87 (df=10) | 2026-07-31..08-13 |
| T1 (MLB) | **0** | OMITTED_BELOW_MIN_N | — | — | — | — | — |
| T2 (MLB) | 0 | OMITTED_BELOW_MIN_N | — | — | — | — | — |

**T1's clean_n=0 is a structural finding, not a data gap.** `logic_epoch.clean_epoch_floor_for_band("T1")
= 10` under the current codebase (`CURRENT_LOGIC_EPOCH = 12`), but every T1 row in the only
available T1 portfolio file (`paper_portfolio_mlb.json`, 466 T1 rows, `last_updated:
2026-08-06`) is stamped `logic_epoch ∈ {1,2,3,6,7,8}` — the file simply stopped accumulating
before epoch 10 was ever reached. **There is currently no way to compute a clean T1 Brier/ECE
comparison at all from the data this session can access — not because T1 lacks volume, but
because the only T1 ledger available predates its own current clean-epoch floor entirely.**
This is consistent with, and substantially strengthens, gap candidate (e) below (T1 possible
pipeline silence since 2026-08-06): it is not merely "not investigated further" as originally
framed — it is now confirmed that T1's ledger has not advanced past epoch 8 while
`CURRENT_LOGIC_EPOCH` has reached 12 elsewhere.

T2 clean_n=0 for the same reason (raw_n=2 total, both pre-epoch-10 by the same token).

**MLB rows excluded from the table (band absent, not band-mismatched):**
- 365 T4-file closed positions, `logic_epoch ∈ {1,2,3}`, dated 2026-06-30..2026-07-07 —
  earliest T4 MLB era, predates the `band` field's introduction to the schema. Cannot be
  assigned a band without inventing one; excluded, not zero-filled.

**NBA — excluded from the primary table, documented separately (not computed):**
`paper_portfolio.json` (`last_updated: 2026-06-17`, 158 closed positions) has **no `band`
field on any row** (all `None`) and uses **`actual_pts`, not `actual_hits`**, as its outcome
field. Neither condition can be satisfied without deviating from the pre-registered
construction (§2: `y = actual_hits >= kalshi_threshold`, clean filter requires a `band`
argument). Applying the pre-registered method verbatim to NBA is not possible with the data
in hand. No substitute NBA figure is reported — computing one would require redefining `y`
and inventing a band label, both of which the pre-registration and the task's DO NOTs
("DO NOT manufacture a ... cohort member") rule out. NBA is also independently known to be
dark/frozen since 2026-06 ([[project_nba_deferred]]), consistent with this file's staleness.

**`paper_portfolio_t4.json`** (3MB, `last_updated: 2026-06-17`, seen in the VPS `ls` listing)
was **not pulled or examined** — its purpose relative to `paper_portfolio_mlb_t4.json` is
unclear (possibly a pre-MLB-split NBA T4 file, given the matching 2026-06-17 timestamp shared
with the NBA file above) and pursuing it was judged out of the task's stated scope (MLB T4 /
T1 / T2, NBA, per the CLAIM and the explicit portfolio files named in the task). Flagged here
as seen-but-not-pursued, not silently skipped.

### `rejected_positions` cohort

**Result: UNSCORABLE. n=0, and this is a substantive finding, not a null result.**

All 2000 `rejected_positions` rows (T4 MLB file) lack `actual_hits`, `outcome`, and `pnl`
entirely — `build_rows()` correctly excludes them (missing required fields), which is why the
pre-registered "run the same paired comparison" cannot literally be executed. Three
independent checks confirm this is not a transient gap:

1. **Every one of the 2000 rows carries the identical `kalshi_order_status`**: `"failed:
   HTTP 404: {\"error\":{\"code\":\"insufficient_shard_balance\",...}}"`. These are exchange-side
   order-submission failures (the bot's Kalshi account lacked collateral at order time) on
   positions that had **already passed C4 risk approval** (each carries `approval_commit`,
   `gross_edge`, `fee_net_edge`) — not risk-engine declines. The task's framing of
   `rejected_positions` as "evaluations the risk engine refused" does not match what this
   cohort actually is.
2. **All 2000 rows share a single `game_date`: 2026-09-20.** This is a one-day, one-cause
   execution-failure event, not a distributed sample spanning the epoch-12 window or any
   comparable span to the 765-row primary cohort.
3. **Zero ticker overlap with the only available outcome-resolution source** —
   `t4_mlb_outcome_store.jsonl` (T-421's decoupled outcome store, pulled live this session,
   2021 resolved tickers, covering 2026-07-02..2026-08-03) — because that store's coverage
   ends seven weeks before `rejected_positions`' single game-date of 2026-09-20. Building new
   outcome resolution for 2026-09-20 (live ESPN/MLB API calls) would be required to score this
   cohort at all, and is out of scope for this read-only analysis task.

**No same-sign-vs-different-sign comparison can be reported** — there is no scored
`rejected_positions` result to compare a sign against. The pre-registered holdout framing
(§8: "not a true holdout... does not establish out-of-sample generalization") is moot here
for a different reason than anticipated: the cohort cannot be scored at all under current
data, not merely that its selection isn't random. This project currently has **no scorable
non-approved cohort** for this purpose.

---

## Gap candidates for 31.2 (not registered by this session — 31.2 owns GG/DECISION_LOG this wave)

1. `rejected_positions` naming/framing mismatch: these 2000 rows are exchange-side
   `insufficient_shard_balance` order-submission failures on already-risk-approved positions,
   concentrated on a single game-date (2026-09-20) — not risk-engine declines, and not usable
   as a holdout-style cohort under any task framing that assumes distributed, risk-refused
   samples.
2. **T1 MLB's ledger (`paper_portfolio_mlb.json`) has not advanced past `logic_epoch=8` since
   `last_updated: 2026-08-06`, while `CURRENT_LOGIC_EPOCH` has since reached 12 — T1's own
   clean-epoch floor (10) now exceeds every row's stamped epoch, making T1 clean_n
   structurally 0 with currently-available data.** Possible T1-pipeline-silence signal; not
   investigated further here (scope fence — read-only analysis, no pipeline diagnosis).
3. The 365 pre-band-era T4 MLB closed rows (`logic_epoch ∈ {1,2,3}`, 2026-06-30..07-07) are
   invisible to any per-band analysis due to a schema-versioning gap (no `band` field at all
   in that era).
4. 12 of those 365 rows show an anomalous pattern: `kalshi_order_id: null`,
   `kalshi_order_status: "failed: HTTP 410"`, yet `status: "CLOSED"` with a real resolved
   `outcome`/`pnl` as if the order had actually filled. 353/365 are ordinary
   submitted-and-resolved trades; these 12 are the exception, not representative — worth
   checking whether a failed submission was mistakenly treated as filled.
5. ADR-0046's ECE baseline (0.0680, n=261, 2026-07-16) does not hold steady under its own
   exact methodology re-applied to a later snapshot of its own source file: n=468 (2026-08-06)
   gives ECE=0.0832 (+22% relative), while Brier stays close (0.2190→0.2200). If ADR-0046's
   constants are ever leaned on again as a live reference rather than a historical snapshot,
   this drift should be accounted for.
6. `paper_portfolio_t4.json` (VPS, 3MB, `last_updated: 2026-06-17`) — purpose relative to
   `paper_portfolio_mlb_t4.json` unclear; not examined this session.
7. (Carried from a prior window, restated for completeness) `MEMORY_BANK.md` contains a
   single line of ~5159 characters — a formatting/hygiene issue noted but not fixed here
   (out of this session's scope fence).

---

## What was not committed

The pulled VPS snapshots and generated result files remain local/uncommitted, consistent with
the SCOPE FENCE's "read-only pulls from the VPS" — these are large (multi-MB) point-in-time
mirrors, not source-of-truth artifacts this repo should track:
`exp_output/T565_calibration_benchmark/paper_portfolio_mlb_t4.LIVE.20260922.json`,
`paper_portfolio_mlb.LIVE.20260922.json`, `paper_portfolio_nba.LIVE.20260922.json`,
`t4_mlb_outcome_store.LIVE.20260922.jsonl`, and `t565_results.json` (the script's own JSON
output, regenerable by re-running `scripts/t565_calibration_model_vs_market.py` against fresh
pulls placed at the same paths). Only the analysis script and this write-up are committed.

## What was NOT checked

- `paper_portfolio_t4.json` (see gap candidate 6) — not pulled or examined.
- No new outcome-resolution infrastructure was built to score `rejected_positions` for
  2026-09-20 — out of scope for a read-only analysis task.
- NBA was not scored under any construction, pre-registered or substitute (see Deliverable 4).
- The 12 anomalous HTTP-410-yet-resolved rows (gap candidate 4) were not traced further into
  `paper_trader.py`'s resolution logic — flagged, not diagnosed.
