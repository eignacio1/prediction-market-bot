# Session Handoff — 2026-06-04T13:30Z

**Trigger:** Operator-initiated session end
**Last commit:** `3abae30` (main) — PDTP Finals G1 analysis; pushed to GitHub

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** 695/695 passing (confirmed on VPS 2026-06-04)
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running; T4 PID 205448 live (SESSION 28 code deployed)
- **Paper bets:** 32/66 unique markets resolved (G6 APR-0017 statistical floor); 1/5 game nights — Finals Game 2 is next
- **G6 gate:** BLOCKED by GG-004 (EXP-017 DIRECTIONAL_NEGATIVE) — path requires T-072 model fix first

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| T4 IDEMPOTENCY interference pattern is structural, not a failure | T4 fires from tip-off (00:30 UTC) and bets on all 32 tickers within 1 hour; late T1 cron (01:30 UTC) finds most tickers locked; T1 late window collapses from ~33 MC bets to ~3 gap bets. Per-ticker idempotency is correct — do not double-bet. Pattern repeats every Finals game. Architectural note for T4 ACTIVE ADR: separate ticker namespaces would eliminate interference. | DECISION_LOG.md 2026-06-04 SESSION 29; PDTP_FINALS_G1_20260604.md | DS |
| Path to G6 requires model fix FIRST; continuing evidence on current model does not count | EXP-017 DIRECTIONAL_NEGATIVE means the commercial question is answered negatively at n=32. Accumulating more bets on the broken model does not satisfy APR-0017 Tier 0 (EXP-017 Part B CONFIRMED with positive EV). Fix model → validate → THEN accumulate ≥66 markets on FIXED model. | PDTP_FINALS_G1_20260604.md Pass 4; DECISION_LOG.md SESSION 28 | DS |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| PDTP Finals G1 document | ✅ `05_RESEARCH_EXPERIMENTS/EXPERIMENT_LOG/PDTP_FINALS_G1_20260604.md` — formal 4-pass analysis. Commit 3abae30, pushed. |
| T1 vs T4 bet count explained | ✅ 33 = MC prediction for full T1; actual G1 = ~3–6 T1 (large Kelly) + 1,414 T4 (flat $0.35/contract from $500 pool). Incorporated into PDTP. |
| VPS deploy SESSION 28 fixes | ✅ f32efa9 deployed: same-day resolve fix + T4_EXPECTED_TOTAL_EDGE=441.38. T4 old PID 154947 killed, new PID 205448 started. 695/695 tests. |
| DECISION_LOG SESSION 29 | ✅ T4 IDEMPOTENCY interference pattern logged as Notable Judgment Call. |
| TODO_NEXT.md updated | ✅ SESSION 29 COMPLETED section added; VPS deploy marked DONE. |
| MEMORY_BANK.md updated | ✅ Last reviewed + Last major milestone updated. |
| PLAN.md updated | ✅ Last reviewed header updated. |

---

## ONE THING PENDING

**Finals Game 2 MC verify + T1 cron fires at 22:00 UTC Jun 5 (2:55 PM PDT).** After PIPE-02 at 21:55 UTC generates `pregame_20260605.json`, run:

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
BOT_ENV=paper PYTHONPATH=src python3 scripts/run_monte_carlo.py --label pre-g2
```

VPS pregame file will be at `/opt/prediction-market-bot/data/pregame_20260605.json` — pull it locally first:
```bash
scp root@157.230.91.33:/opt/prediction-market-bot/data/pregame_20260605.json data/
```

Also decide on portfolio reset before G2 cron. Current portfolio: $1,404.80 total (T1 bankroll ~$904.80 + T4 pool $500 pool_isolated). Last session decided to reset to $1,500 before G2 for clean signal — confirm before 22:00 UTC Jun 5.

---

## Current Paper Portfolio

- **T1 Bankroll:** ~$904.80 (started $1,000, P&L −$95.20 from G1)
- **T4 Pool:** $500 pool_isolated — tracks separately
- **Total system bankroll:** $1,404.80
- **Open positions:** 0
- **Resolved:** 1,417 (32 unique markets for EXP-017)
- **G6 gate progress:** 32/66 unique markets | 1/5 game nights | EXP-017 DIRECTIONAL_NEGATIVE (GG-004 OPEN — requires model fix before accumulation counts)

---

## Active Cron on VPS (157.230.91.33)

```
21:00 UTC  — Health check
21:55 UTC  — PIPE-02 inference (run_pregame.py) ← generates pregame_20260605.json
22:00 UTC  — PIPE-03 early (paper bets, 7pm ET games)
01:30 UTC  — PIPE-03 late (paper bets, 9pm+ ET games)
06:00 UTC  — PIPE-03R resolve-only (403-blocked on VPS; T-109 local procedure covers this)
14:00 UTC Mon — Model freshness check
```

**T4 live process:** PID 205448 on VPS, watching for Finals Game 2 ESPN game ID. Will auto-activate at tip-off.

**Finals Game 2:** Jun 5 PDT tip-off ~8:30 PM ET / 00:30 UTC Jun 6.

---

## Key Constraints to Remember

1. **stats.nba.com 403 blocks VPS** — resolution must always run locally via `run_resolve_local.py`
2. **No live capital until G6** — APR-0017 four-tier gate; GG-004 OPEN (DIRECTIONAL_NEGATIVE); T-072 required first
3. **EXP-017 verdict is DIRECTIONAL_NEGATIVE** — path to G6 = fix model (T-072: add F-040 opponent features, retrain) → EXP-017 v2 (positive EV) → accumulate ≥66 markets on FIXED model
4. **T4_BAND_WEIGHT is STUB** — GG-011 blocks T4 ACTIVE; new ADR required for high-throughput per-evaluation sizing
5. **T4 IDEMPOTENCY interference** — T4 pre-empts late T1 cron; T1 early cron (~22:00 UTC) is the de facto T1 window; late cron fills gaps only
6. **MC verify BEFORE G2 cron** — must run after PIPE-02 at 21:55 UTC Jun 5 (not before; stale pregame gives wrong bets)

---

## Open Priority Queue

| Priority | Task | Notes |
|----------|------|-------|
| **BEFORE G2 CRON (21:55 UTC Jun 5)** | MC verify with G2 pregame | Pull pregame from VPS after 21:55 UTC; run MC; check expected bet count |
| **BEFORE G2 CRON** | Portfolio reset decision | Reset to $1,500 ($1,000 T1 + $500 T4)? Current: $1,404.80. Recommend reset. |
| HIGH — before G6 | T-131 fee-adjusted edge ADR | GG-009: taker fee absent from MIN_EDGE gate; write ADR before G6 EXP-017 re-run |
| HIGH — before G6 | T-072 opponent features + retrain | F-040 opp_def_rating_l10_mean to C2; new ADR per ADR-0004; EXP-017 v2 on corrected model |
| MEDIUM | KI-027 Kalshi HTTP 503/429 | Rate errors in second PIPE-03 window; investigate retry/backoff |
| LOW now / HIGH before T4 ACTIVE | GG-011 T4_BAND_WEIGHT ADR | Per-evaluation sizing architecture incompatible with high-throughput T4 |
| LOW — before any edit | T-132 CHANGE_CONTROL.md governance debt | decisions_logged: false — extract decisions before editing |

---

## ⚙️ DECISION AUDIT

**Governance scan:** CLEAN — no `decisions_logged: false` documents found.

| Document | Decisions logged | Status |
|----------|-----------------|--------|
| PDTP_FINALS_G1_20260604.md | N/A — analysis document, not a spec | ✅ |
| DECISION_LOG.md | ACTIVE | ✅ SESSION 29 entry added |
| TODO_NEXT.md | ACTIVE | ✅ SESSION 29 section added |
| MEMORY_BANK.md | ACTIVE | ✅ Updated |
| PLAN.md | ACTIVE | ✅ Updated |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260604_1330.md.
# Priority 1: Finals Game 2 MC verify — run AFTER PIPE-02 at 21:55 UTC Jun 5 (2:55 PM PDT):
#   scp root@157.230.91.33:/opt/prediction-market-bot/data/pregame_20260605.json data/
#   BOT_ENV=paper PYTHONPATH=src python3 scripts/run_monte_carlo.py --label pre-g2
# Priority 2: Portfolio reset decision before 22:00 UTC Jun 5 cron.
# Priority 3: T-072 dark period plan — add F-040 opp_def_rating_l10_mean to C2 and retrain per T-072.
# GG-004 is OPEN — EXP-017 DIRECTIONAL_NEGATIVE — path to G6 requires model fix first."
```
