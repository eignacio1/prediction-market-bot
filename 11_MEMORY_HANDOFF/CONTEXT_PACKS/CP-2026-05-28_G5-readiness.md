# Context Pack — CP-2026-05-28_G5-readiness

**Created:** 2026-05-28  
**Purpose:** Seamless session handoff at Phase 5 / G5 gate readiness. Covers the full Phase 5 build + EXP-004 results. Read this if MEMORY_BANK.md is not enough context.  
**Replaces:** CP-2026-05-28_G4-gate-readiness.md (now superseded)

---

## One-Paragraph State

Phase 5 (Operational Readiness) is 95% complete. All tasks T-049–T-055 are done: C7 monitoring, C8 dashboard, kill switch drill (APR-0013, 0.340ms), ST-001–004 sensitivity tests (all PASS), MODEL_CARD.md at 10/10, CAPACITY_PLANNING.md stub. The only remaining item is EXP-004 Part B — a live market check against Kalshi prices — which requires mobile hotspot connectivity (Kalshi's CloudFront WAF blocks all WiFi ISP networks by IP/ASN; mobile hotspot works). EXP-004 Part A ran successfully: HYP-003 is SUPPORTED (EV +$0.0855/bet, 59% win rate, 2,481 bets on 3,254 TEST rows). G5 gate (APR-0007) is ready to close once Part B runs on hotspot.

---

## Session Activity (2026-05-28, this context window)

### What Was Done

**1. DS-02-B-001 Root Cause Confirmed**
- Previous diagnosis: TLS fingerprint block (Homebrew Python 3.11 fix)
- New diagnosis: IP/ASN-based block. Homebrew Python 3.11 (OpenSSL 3.6.2) confirmed working on mobile hotspot in prior session. Same Python fails on home WiFi and work WiFi — both blocked identically. Root cause: Kalshi CloudFront WAF filters by ISP IP range/ASN, not TLS fingerprint.
- No code fix exists. Mobile hotspot or datacenter VPS (Phase 6+) are the only solutions.

**2. EXP-004 Refactored for Offline Resilience**
- `run_exp004.py` updated: DS-02 connectivity is now optional
- If DS-02 offline: Part A runs using `MEASURED_VIG_20260528 = 0.01` (measured from 37 KXNBAPTS markets, OKC-SAS game, mobile hotspot session)
- Part B skipped gracefully with clear note when offline
- Constant `MEASURED_VIG_20260528` documented in code as the source of truth

**3. EXP-004 Executed (Part A)**
- Command: `VENUE_API_KEY=$(grep VENUE_API_KEY .env | cut -d= -f2) PYTHONPATH=src /usr/local/bin/python3.11 src/prediction_market_bot/run_exp004.py`
- Session: `EXP-004-2A47C378` | Run at: `2026-05-28T18:29:37Z`
- Output: `exp_output/EXP-004/EXP-004_results.json`

**4. EXP-004 Part A Results**

| Metric | Value |
|--------|-------|
| TEST rows | 3,254 (2023-24 full season) |
| Brier (model) | 0.2416 |
| Brier (null) | 0.2500 |
| Brier improvement | **+0.0084** |
| ECE | 0.0247 |
| AUC-ROC | 0.6062 |
| Vig applied | 0.0100 (MEASURED_VIG_20260528) |
| YES bets | 1,380 |
| NO bets | 1,101 |
| Total bets | 2,481 / 3,254 (76.1%) |
| Win rate | **59.0%** |
| Total P&L (flat $1) | **+$212.10** |
| EV per bet | **+$0.0855** |
| **HYP-003 (Part A)** | **SUPPORTED** |

*Caveat: market_implied_prob=0.50 is the null assumption. Real Kalshi prices will differ. Part B will quantify edge against actual mid-prices.*

**5. Documentation Updated**
- `05_RESEARCH_EXPERIMENTS/EXPERIMENT_LOG/EXP-004_edge-vs-vig.md` — CREATED
- `05_RESEARCH_EXPERIMENTS/HYPOTHESES.md` — HYP-003 status: BLOCKED → 🟡 SUPPORTED (Part A)
- `08_MODEL_RISK_GOVERNANCE/PERFORMANCE_METRICS.md` — EXP-004 section added
- `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/RESULTS_INDEX.md` — EXP-004 row updated
- `00_ADMIN/APPROVALS_REGISTER.md` — APR-0007 updated to 95% ready
- `04_EXECUTION/TODO_NEXT.md` — T-052 updated; DS-02-B-001 detail corrected
- `04_EXECUTION/RID_LOG.md` — DS-02-B-001 root cause corrected (IP/ASN, not TLS fingerprint)
- `11_MEMORY_HANDOFF/MEMORY_BANK.md` — state snapshot updated

**6. sklearn Deprecation Fix**
- `run_exp004.py`: removed `penalty="l2"` from `LogisticRegression` (deprecated in sklearn 1.8; default is l2 so no behavioral change)

---

## What Remains for G5 Gate Closure

### Single blocking item:
**EXP-004 Part B** — live market alignment against Kalshi prices for today's game.

**How to run (on mobile hotspot):**
```bash
VENUE_API_KEY=$(grep VENUE_API_KEY .env | cut -d= -f2) \
PYTHONPATH=src /usr/local/bin/python3.11 \
    src/prediction_market_bot/run_exp004.py
```
Part B runs automatically when DS-02 is online. No code changes needed.

**After Part B:**
1. Update `HYPOTHESES.md` HYP-003 → 🟢 CONFIRMED (or note if Part B changes the picture)
2. Update `RID_LOG.md` DS-02-B-001 → RESOLVED
3. Update `APPROVALS_REGISTER.md` APR-0007 → ACCEPTED (sign G5 gate)
4. Commit everything

### Low-priority pending:
- T-056 (this context pack — now complete ✅)
- Model data refresh: retrain on 2024-25 and 2025-26 data for production realism (pre-G6 item)

---

## VPS Decision

**Not needed for Phase 5.** Mobile hotspot resolves the immediate blocker.

**Needed for Phase 6** (paper trading) when:
- Scheduled pre-game runs (cron ~90 min before tip-off)
- Uptime independent of laptop
- Stable datacenter IP (clean ASN passes CloudFront WAF)

Do not provision until Phase 6 infrastructure planning.

---

## Key File Locations

| What | Where |
|------|-------|
| Kalshi client | `src/prediction_market_bot/c5_execution/kalshi_client.py` |
| EXP-004 runner | `src/prediction_market_bot/run_exp004.py` |
| EXP-004 results | `exp_output/EXP-004/EXP-004_results.json` |
| Sensitivity test results | `exp_output/SENSITIVITY_TESTS/sensitivity_test_results.json` |
| Feature matrix CSV | `exp_output/EXP-001/EXP-001_feature_matrix.csv` |
| API key | `.env` (gitignored; VENUE_API_KEY=...) |
| Kill switch drill log | `logs/drill_audit.jsonl` |

## Python Environments

| Environment | Python | OpenSSL | Use for |
|-------------|--------|---------|---------|
| `.venv` | 3.9.6 | LibreSSL 2.8.3 | All non-Kalshi work: tests, experiments, scripts |
| `/usr/local/bin/python3.11` | 3.11.15 | OpenSSL 3.6.2 | Kalshi API calls only (hotspot required) |
| `.venv311` | 3.11.x | OpenSSL 3.6.2 | Has numpy install issue — avoid; use global Homebrew instead |

**Run commands:**
- Tests: `PYTHONPATH=src .venv/bin/python3 -m pytest tests/ -q`
- EXP-004: `VENUE_API_KEY=$(grep VENUE_API_KEY .env | cut -d= -f2) PYTHONPATH=src /usr/local/bin/python3.11 src/prediction_market_bot/run_exp004.py`
- Sensitivity tests: `PYTHONPATH=src .venv/bin/python3 src/prediction_market_bot/run_sensitivity_tests.py`

---

## Security Constraints (always in effect)

1. NFR-05: Zero hardcoded secrets. `.env` is gitignored, never committed.
2. No real capital until G6 Release Gate (APR-0008, ADR-0005 accepted).
3. `BOT_C4_ACTIVE` must NOT be set in ENV-01/ENV-02 — all C4 calls will REJECT.
4. Kill switch must halt ≤60 seconds (tested: 0.340ms). No bypass path.
5. `arb/` folder = REFERENCE ONLY. No incorporation until APR-0010 granted.
6. Old key `80742ef7-b0ce-45fd-b9b6-34e71950ed0d` is COMPROMISED — never use.
7. Active key stored ONLY in `.env`. Never type in chat or commit to VCS.
