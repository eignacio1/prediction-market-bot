# Session Handoff — 2026-06-24T14:45Z

**Trigger:** Operator-initiated (/session-end after T-187H complete)
**Last commit:** `6447fea` (main) — pushed to GitHub + VPS

---

## Status

- **Phase:** 6/7 ACTIVE — MLB paper trading stack fully live
- **Tests:** 1790/1790 passing (0 failures, 1 skipped)
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running (all PIPE-05 crons installed)
- **Paper bets (NBA):** 158 resolved / G6 gate (≥30 ✓; P&L gate FAILING — drawdown 24.9%)
- **Paper bets (MLB):** 0 resolved — accumulation begins August 2026

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| GG-042 status: DEFERRED — structural (t=3 excluded indefinitely) | T-187H re-evaluation after T-187G confirmed: SP coverage 99.9% (data-quality premise DISPROVED). Brier delta=+0.0002 unchanged. At 3.9% base rate, AUC=0.61 cannot produce Brier delta ≥0.001 — information-theoretic ceiling, not a fixable data problem. Only paths to activation: non-linear model or richer pitcher-batter matchup features. | `03_DECISIONS/GOVERNANCE_GAP_LOG.md` GG-042, `DECISION_LOG.md` T-187H entry | EL/DS |
| T_global calibration strategy (PIPE-05C design) | `run_mlb_calib_monitor.py` derives temperature T on combined t=1+t=2 dataset rather than per-threshold. Per-threshold datasets will be too small for robust optimization at early paper trading volumes; T_global provides statistical power. Per-threshold ECE diagnosis reuses T_global. | `scripts/run_mlb_calib_monitor.py`, `DECISION_LOG.md` T-187F entry | EL |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| **T-187E — `run_resolve_mlb.py` (PIPE-05R)** | ✅ MLB paper position resolution. `PaperTrader.settle_position()` added (sport-agnostic; stat_label="actual_hits" for MLB). `run_resolve_mlb.py`: MLB Stats API gameLog fetch, Regular→Postseason fallback, full resolve loop, C7 monitor, C6 audit. `deploy/cron.conf`: PIPE-05FX properly labeled; PIPE-05R assigned to MLB resolve at 06:30 UTC. 33 new tests (`tests/test_t187e_mlb_resolve.py`). 1704→1737. |
| **T-187F — `scripts/run_mlb_calib_monitor.py` (PIPE-05C)** | ✅ MLB calibration monitor. Reads `paper_portfolio_mlb.json`; ECE per threshold (t∈{1,2}); T_global via `minimize_scalar` on log-loss; reliability buckets; anti-predictive check. Exit 0=CALIBRATED/INSUFFICIENT, 1=MISCALIBRATED, 2=ANTI_PREDICTIVE. MIN_N_DIAGNOSE=50. Does NOT write to `calibration.py`. PIPE-05C cron Mondays 14:10 UTC. 35 new tests (`tests/test_t187f_mlb_calib_monitor.py`). 1737→1772. |
| **T-187G — Live SP overlay** | ✅ `run_mlb_paper_trade.py` modified: `_safe_int`, `_SP_OVERRIDE_FIELDS`, `_build_live_sp_override`, `_build_mlb_feature_vector(sp_override=)`. Fetches tonight's actual SPs via `MLBIngestionClient.fetch_game_starters`; overrides `opp_sp_*` fields at inference time. Falls back to historical SP stats on API failure. 18 new tests. 1772→1790. VPS deployed 7ca79b9 → 8affa0e. |
| **T-187H — t=3 shadow gate re-evaluation** | ✅ VALID NEGATIVE confirmed (governance-only, no code changes). SP coverage 99.9% (GG-042 data-quality premise DISPROVED). Brier delta=+0.0002 (FAIL — same as T-187B), ECE=0.0037 (PASS), AUC=0.6141. Score p50=0.037 (base rate); 1.9% of holdout scores exceed Kalshi market price (0.08). Structural failure: information-theoretic ceiling at 3.9% base rate. THRESHOLDS=[1,2] and _EXCLUDED_THRESHOLDS=[3] unchanged. GG-042 → DEFERRED — structural. DECISION_LOG updated. VPS deployed 6447fea. |
| **DECISION_LOG** | ✅ T-187E, T-187F, T-187G, T-187H entries all appended. |
| **GG-042 governance** | ✅ GOVERNANCE_GAP_LOG.md GG-042 status updated from OPEN to DEFERRED — structural. Resolution field updated with T-187H findings. |

---

## ONE THING PENDING

**MLB paper trading accumulation begins when the MLB regular season resumes.** No sessions required until then unless VPS monitoring reveals a PIPE-05 cron failure. The next meaningful action is EXP-017 MLB run after ≥20 closed positions accumulate — estimated late August 2026 at current MLB game pace.

If a session fires before August: check VPS cron health (`ssh prediction-market-vps "tail -50 /opt/prediction-market-bot/logs/paper_mlb_cron.log"`) and verify PIPE-05 has been placing bets. If 0 positions after a week of MLB games, investigate `run_mlb_paper_trade.py` market-fetching or model-loading failure.

---

## Current Paper Portfolio

**NBA book:**
- Bankroll: $751.10 (24.9% drawdown — kill switch fires at 25% if further loss)
- Open: 0 positions ($0.00 deployed — dark period, NBA season over)
- Closed/Resolved: 158 | G6 gate (P&L gate FAILING — negative P&L)

**MLB book:**
- Bankroll: $1,000 (fresh book, clean baseline)
- Open: 0 positions
- Closed/Resolved: 0 (accumulation begins August 2026)

---

## Active Cron on VPS (157.230.91.33)

```
17:00 UTC      — Health check (deploy/healthcheck.sh)
17:25 UTC      — T-140 TSS cache pre-flight
17:55 UTC      — PIPE-02 inference primary (run_pregame.py)
18:00 UTC      — PIPE-03 early NBA paper bets
01:25 UTC      — PIPE-02 inference late
01:30 UTC      — PIPE-03 late NBA paper bets
06:00 UTC      — PIPE-03R NBA resolution (run_resolve.py)
20:00–23:55 UTC */15 — PIPE-06 T3 pre-tip (run_t3_pretip.py)
00:00–03:55 UTC */15 — PIPE-06 T3 (cont.)
23:00 UTC      — PIPE-07 T4 in-play (run_t4_live.py, 6h timeout)
22:30 UTC      — PIPE-05FX MLB feature refresh (--seasons 2026 only)
23:30 UTC      — PIPE-05 MLB paper bets (run_mlb_paper_trade.py)
06:30 UTC      — PIPE-05R MLB resolution (run_resolve_mlb.py)
14:00 UTC Mon  — Model freshness check
14:10 UTC Mon  — PIPE-05C MLB calibration monitor (run_mlb_calib_monitor.py)
```

---

## Key Constraints to Remember

1. **MLB Stats API VPS IP-block:** DigitalOcean IPs blocked from historical seasons (≤2025) via Fastly CDN (HTTP 406). PIPE-05FX uses `--seasons 2026` only. Annual retraining: generate full 3-season CSV locally → `scp` to VPS → run `train_mlb_model.py` locally → `scp` model artifact.
2. **t=3 structural exclusion:** `_MODEL_THRESHOLDS = frozenset({1, 2})`. t=3 markets skip with C6 log. GG-042 DEFERRED — structural. Do NOT re-evaluate unless model architecture changes (non-linear) or Kalshi market price drops to ≤5–6%.
3. **NBA book halted at drawdown:** Kill switch fires at 25% max drawdown. Current: 24.9%. Dark period — no NBA games.
4. **MLB model is frozen:** `models/mlb_v1_model.joblib` on VPS. No automated retraining (hard rule #4). Annual retrain requires full 3-season CSV locally (VPS blocked from 2024/2025 data).
5. **G6 commercial validation:** GG-004 OPEN. EXP-017 MLB needs ≥20 closed positions before first read, ≥150 for ADR-0024 Tier 1.

---

## ⚙️ DECISION AUDIT

**Governance scan result:** CLEAN — no `decisions_logged: false` documents found.

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| `03_DECISIONS/GOVERNANCE_GAP_LOG.md` | N/A (operational log) | GG-042 status update (T-187H) | ✅ |
| `04_EXECUTION/TODO_NEXT.md` | N/A | T-187E/F/G/H SESSION 82 rows | ✅ |
| `03_DECISIONS/DECISION_LOG/DECISION_LOG.md` | N/A | T-187E, F, G, H entries | ✅ |
| No new canonical docs created | — | — | ✅ |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260624_1445.md.
# All T-187 components complete. MLB paper trading fully live. Next: monitor VPS crons
# when MLB resumes in August 2026. 1790/1790 tests. VPS HEAD 6447fea."
```
