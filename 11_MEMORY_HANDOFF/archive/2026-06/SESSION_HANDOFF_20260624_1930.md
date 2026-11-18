# Session Handoff — 2026-06-24T19:30Z

**Trigger:** Operator-initiated session end
**Last commit:** `5c233aa` (main) — pushed to GitHub + VPS

---

## Status

- **Phase:** 6/7 ACTIVE — paper trading live on VPS
- **Tests:** 1704/1704 passing
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running (PIPE-05 23:30 UTC, PIPE-05R 22:30 UTC)
- **Paper bets (NBA):** 158/30 resolved — G6 gate clock met on bet count; positive-P&L gate FAILING (−$248.90 / 24.9% drawdown); GG-004 (EXP-017 commercial validation) remains binding G6 blocker
- **Paper bets (MLB):** 0 resolved — MLB paper trading starts August 2026

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| Per-threshold MLB LR+Platt architecture: one pipeline per active threshold (t=1, t=2) instead of pooled | Pooled `class_weight='balanced'` LR + Platt calibrated to ~26% average while per-threshold base rates differ 3–4× (t=1=54.5%, t=2=18.4%). Platt scaling on pooled distribution cannot fix per-threshold systematic bias. Per-threshold ECE: t=1=0.013, t=2=0.011 vs pooled 0.1246. | DECISION_LOG.md (SESSION 81 entry: "T-187B: per-threshold MLB architecture fix") | EL |
| t=3 threshold excluded from active MLB scope | Brier delta at t=3 = +0.0002 < 0.001 gate at 3.9% base rate and AUC=0.61. Even perfect calibration cannot produce meaningful Brier improvement at this prevalence. t=3 bets would almost never fire (model predicts ~3.9% vs Kalshi ~8¢ → always negative edge). Deferred to T-187G (live SP overlay injection). | GG-042 in GOVERNANCE_GAP_LOG.md | EL |
| `threshold` added to `_NON_FEATURE_MLB` (training and inference) | Within each per-threshold pipeline, all training rows have the same threshold value — it is a degenerate constant and a corrupting feature. Must be excluded from both the training feature matrix and the inference feature vector. | DECISION_LOG.md (same entry above) | EL |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| **T-187B (continued from prior session): `scripts/train_mlb_model.py` restructure** | ✅ Per-threshold training loop for t=1 and t=2; `threshold` added to `_NON_FEATURE_MLB`; new artifact schema `{"pipelines": {1: p1, 2: p2}, "feature_names": [...18...], "col_medians": ..., "thresholds": [1, 2], "sport": "mlb"}` |
| **T-187B: `src/prediction_market_bot/run_mlb_paper_trade.py` update** | ✅ `_MODEL_THRESHOLDS = frozenset({1, 2})`; `threshold` in `_NON_FEATURE_MLB`; dispatch to `pipelines[int(mkt.threshold)].predict_proba(X)`; `threshold` param removed from `_build_mlb_feature_vector` |
| **T-187B: `tests/test_run_mlb_paper_trade.py` + `tests/test_t183_mlb_c3.py` updated** | ✅ All threshold-injection tests replaced; artifact schema assertions updated; `test_threshold_in_non_features` flipped; n_features 19→18 |
| **DECISION_LOG entry written** | ✅ Per-threshold architecture, root cause, diagnostic results, t=3 exclusion, artifact schema change, inference change, test count |
| **GG-042 registered in GOVERNANCE_GAP_LOG.md** | ✅ t=3 excluded from active MLB scope; OPEN; linked to T-187G; severity LOW (paper trading only) |
| **TODO_NEXT.md updated** | ✅ T-187B marked CODE COMPLETE → COMPLETE (post VPS shadow gate PASS) |
| **Commit + push** | ✅ `953fd20` (T-187B per-threshold code + docs) + `5c233aa` (completion marker) |
| **VPS deploy** | ✅ `git pull` to HEAD `5c233aa` on VPS |
| **VPS retrain** | ✅ `PYTHONPATH=src venv/bin/python3 scripts/train_mlb_model.py` — shadow gate PASS for both t=1 and t=2 |
| **Shadow gate verification** | ✅ t=1: ECE=0.0134, Brier delta=+0.0055; t=2: ECE=0.0106, Brier delta=+0.0022. `models/mlb_v1_model.joblib` + `models/mlb_v1_model_meta.json` saved on VPS (model version `mlb-v1-a1c25470`) |
| **MEMORY_BANK.md updated** | ✅ Last reviewed + Last major milestone updated |
| **PLAN.md updated** | ✅ Last reviewed updated |

---

## ONE THING PENDING

**T-187E — MLB resolve script.** The MLB paper portfolio (`logs/paper_portfolio_mlb.json`) has no resolve pipeline yet. PIPE-05 will start placing bets once MLB season is active in August 2026, but there is no `run_mlb_resolve.py` to settle outcomes. This is the next P0 task for the MLB paper trading stack.

Current state: `paper_portfolio_mlb.json` exists on VPS with $1,000 bankroll, 0 open positions, 0 closed positions. PIPE-05 cron fires at 23:30 UTC. The model is live. The runner is live. Resolve is the gap.

---

## Current Paper Portfolio

**NBA book:**
- Bankroll: $751.10 (24.9% drawdown)
- Open: 0 bets ($0.00 deployed)
- Closed/Resolved: 158 | G6 gate: 158/30 on bet count; P&L gate FAILING

**MLB book:**
- Bankroll: $1,000.00 (fresh pool)
- Open: 0 bets
- Closed/Resolved: 0 | MLB paper trading starts August 2026

---

## Active Cron on VPS (157.230.91.33)

```
21:00 UTC  — Health check
21:30 UTC  — PIPE-02 NBA inference (run_pregame.py)
22:00 UTC  — PIPE-03 NBA early (paper bets, 7pm ET games)
22:30 UTC  — PIPE-05R MLB daily feature refresh (generate_mlb_features.py --seasons 2026)
23:30 UTC  — PIPE-05 MLB paper bets (run_mlb_paper_trade.py)
01:30 UTC  — PIPE-03 NBA late (paper bets, 9pm+ ET games)
06:00 UTC  — PIPE-03R NBA resolve-only (run_resolve.py)
14:00 UTC Mon — Model freshness check
```

---

## Key Constraints to Remember

1. **MLB Stats API IP-blocking**: VPS (DigitalOcean) blocked from historical seasons (2024/2025) via HTTP 406 (Fastly CDN). Season 2026 accessible. Full feature matrix must be generated locally → scp to VPS. PIPE-05R uses `--seasons 2026` only. Annual retraining: local full generation + scp.
2. **t=3 excluded from active MLB model scope**: GG-042 OPEN. t=3 bets will be gate-filtered by `_MODEL_THRESHOLDS = frozenset({1, 2})`. T-187G deferred.
3. **No live capital until G6** — GG-004 (EXP-017 commercial validation) is the binding blocker. MLB paper trading starts August 2026.
4. **NBA dark period**: NBA is OFF-SEASON until October 2026. NBA crons run but find no games — no bets fire. Normal.
5. **Work wifi blocks Kalshi API** — use any other network for live testing.

---

## ⚙️ DECISION AUDIT

Governance scan: `grep -rn "^\*\*Decisions logged:\*\* false" 02_ARCHITECTURE_DESIGN/ 08_MODEL_RISK_GOVERNANCE/ 01_SPEC/` → **CLEAN** (no matches)

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| `scripts/train_mlb_model.py` | N/A (code, not a strategy doc) | SESSION 81 DECISION_LOG entry covers architecture decision | ✅ |
| `src/prediction_market_bot/run_mlb_paper_trade.py` | N/A (code) | Covered by DECISION_LOG entry | ✅ |
| `03_DECISIONS/GOVERNANCE_GAP_LOG.md` | N/A (gap log) | GG-042 registered | ✅ |

---

## Remaining T-187 Tasks

| Task | Description | Priority |
|------|-------------|----------|
| T-187E | MLB resolve script (`run_mlb_resolve.py`) — settle MLB paper positions against actuals | P0 |
| T-187F | MLB calibration monitor — `CALIBRATION_TEMPERATURE["mlb"]` derivation pipeline once paper bets accumulate (deferred to dark period Phase 3, August+) | LOW |
| T-187G | Live SP overlay injection for t=3 reconsideration (GG-042) — t=3 exclusion holds until live SP ERA data improves AUC beyond ~0.65 | LOW |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260624_1930.md, then continue with T-187E (MLB resolve script). 1704/1704 tests passing."
```
