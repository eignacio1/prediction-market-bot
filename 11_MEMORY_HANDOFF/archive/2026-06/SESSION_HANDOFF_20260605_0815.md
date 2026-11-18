# Session Handoff — 2026-06-05T08:15Z

**Trigger:** Operator-initiated session end
**Last commit:** `173b7cd` (main) — pushed to GitHub + VPS

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** 715/715 passing
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running; GHA 20:30 UTC operational (T-137 fix)
- **Paper bets:** 0 closed/resolved — G6 gate pending Finals G2 resolution (~06:00 UTC Jun 6)

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| GHA cron moved 00:30 → 20:30 UTC (T-137) | At 00:30 UTC, GAME_DATE=N+1; PIPE-02 early at 21:55 UTC reads GAME_DATE=N — different files, adj_λ cache structurally unreachable for every early cron. 20:30 UTC aligns both to GAME_DATE=N. Trade-off: late cron (01:25 UTC) loses GHA cache; acceptable for Finals (bankroll depleted by early cron). Revisit for regular season (two-runs-per-day strategy). | DECISION_LOG.md SESSION 33 / T-137; GG-015 RESOLVED in GOVERNANCE_GAP_LOG | DS |
| time.sleep(0.5) between Kalshi orders (T-136) | 25 orders in ~2s burst = ~12 req/s; GG-014 showed ~50% HTTP 429 rate. sleep(0.5) reduces to ~2 req/s, within Kalshi Basic tier (10 orders/s). Paper-safe implementation (no delay in local-only mode). Effectiveness verified after Finals G2 cron. | DECISION_LOG.md SESSION 33 / T-136; GG-014 → PARTIAL | DS |
| TSS size=0 now fires logger.error in PIPE-03 (T-134) | GG-012 and GG-013 both survived multiple cron cycles undetected because TSS=0 was treated as graceful fallback with no alert. logger.error + print ensures C7 catches silent adj_λ failures going forward. | DECISION_LOG.md (implied); GG-012/GG-013 resolution notes | DS |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| T-136 — Kalshi 429 fix | ✅ `time.sleep(0.5)` in `paper_trader.py` line 265. Deployed. GG-014 → PARTIAL. |
| T-137 — GHA cron timing fix | ✅ `tss_daily_sync.yml` cron `30 0` → `30 20`. GG-015 registered + RESOLVED. |
| T-134 — TSS size=0 monitoring | ✅ `logger.error` + `print` in `run_paper_trade.py` when `team_store is None or len==0`. |
| GG-013 status corrected | ✅ Status now cites 20:30 UTC (not 00:30 from prior session entry). |
| GG-014 status updated | ✅ Resolution + Status fields updated to PARTIAL with sleep fix detail. |
| GG-015 registered + resolved | ✅ New gap entry added to GOVERNANCE_GAP_LOG; Resolved Gaps table updated. |
| DECISION_LOG entries | ✅ T-136 and T-137 entries added. |
| TODO_NEXT.md | ✅ Header updated; T-136/T-137/T-134 closed; new SESSION 33 open items added (EXP-018, GG-014 verification, adj_λ activation check). |
| MEMORY_BANK.md | ✅ All fields updated (milestone, snapshot, cron schedule, risks, health table). |
| PLAN.md | ✅ Header `Last reviewed` updated. |
| Commit + VPS deploy | ✅ `173b7cd` pushed to GitHub; `git pull` confirmed on VPS (8 files changed). |

---

## ONE THING PENDING

**Finals G2 resolves at ~06:00 UTC Jun 6 (tonight).** After resolution:

1. Run `run_resolve_local.py` on local machine (VPS blocked for nba_api resolution) — pulls `paper_portfolio.json` from VPS, resolves 25 G3 positions, pushes back.
2. Run EXP-018 analysis on G3 positions: baseline Poisson vs. real Kalshi prices (all 25 positions use unadjusted λ — GG-013 was unresolved during G3 cron run).
3. Check `kalshi_order_status` breakdown in resolved portfolio — was sleep(0.5) fix effective? Target: ≤5% HTTP 429 rate. Note: the sleep fix was deployed AFTER G3 cron; G3 positions will still show the old 429 rate. **First effectiveness test is Finals G3 cron (Jun 8 22:00 UTC).**
4. Update MEMORY_BANK + TODO_NEXT with G3 resolution results.

**For Finals G3 (Jun 8):** Verify GHA cache fires at 20:30 UTC Jun 8 → `team_stats_cache_20260608.json` on VPS → PIPE-03 log shows `adj_λ` values ≠ raw pts_l10_mean. This is the first end-to-end live test of ADR-0015.

---

## Current Paper Portfolio

- Bankroll: $256.34 (25 open positions, $743.66 deployed)
- Open: 25 positions, all `game_date: "2026-06-05"` (Finals Game 2 local; tips 00:30 UTC Jun 6)
  - 13 with `kalshi_order_status: resting` (Kalshi order placed successfully)
  - 12 with `kalshi_order_status: failed: HTTP 429` (local position recorded; paper P&L unaffected)
- Closed/Resolved: 0 | G6 evidence: 0 resolved bets
- Kill switch state: drawdown = 0% (realized_loss=0; no closed positions)

---

## Active Cron on VPS (157.230.91.33)

```
20:30 UTC  — GHA TSS cache build (GitHub Actions → SCP to VPS; T-137 fix)
21:00 UTC  — Health check
21:55 UTC  — PIPE-02 early inference (run_pregame.py)
22:00 UTC  — PIPE-03 early (paper bets, 7pm ET games)
01:25 UTC  — PIPE-02 late inference
01:30 UTC  — PIPE-03 late (paper bets, 9pm+ ET games)
06:00 UTC  — PIPE-03R resolve-only (run_resolve.py — VPS blocked, use run_resolve_local.py)
```

---

## Key Constraints to Remember

1. VPS (DigitalOcean) is blocked by Akamai from stats.nba.com — use ESPN scoreboard API (already in build_tss_cache.py)
2. Game resolution MUST run from local machine via `run_resolve_local.py` (VPS nba_api blocked)
3. adj_λ (ADR-0015) has NEVER been applied to any live bet — first live application is Finals G3 (Jun 8)
4. GG-014 sleep(0.5) fix applies to FUTURE cron runs; G3 positions (already placed) will still show 429 failures
5. No live capital until G6 (APR-0017: ≥66 resolved bets + ≥5 game nights + EXP-017 Part B confirmed)
6. NAMING: "Finals Game N" = NBA game. "Gate G6" = live capital gate. Never abbreviate both as G-N in same context.

---

## ⚙️ DECISION AUDIT

**Governance scan:** CLEAN — no `decisions_logged: false` documents found.

| Document | Decisions logged | DECISION_LOG entries | Status |
|----------|-----------------|---------------------|--------|
| GOVERNANCE_GAP_LOG.md | N/A (register, not spec doc) | GG-015 registered; GG-013/GG-014 updated | ✅ |
| DECISION_LOG.md | N/A (is the log) | T-136, T-137 entries added | ✅ |
| tss_daily_sync.yml | N/A (code artifact) | DECISION_LOG T-137 covers rationale | ✅ |
| paper_trader.py | N/A (code artifact) | DECISION_LOG T-136 covers rationale | ✅ |
| run_paper_trade.py | N/A (code artifact) | GG-012/GG-013 resolution notes cover intent | ✅ |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Read 11_MEMORY_HANDOFF/MEMORY_BANK.md + this handoff file
# Immediate: check if Finals G2 has resolved (game tips 00:30 UTC Jun 6)
# If resolved: run run_resolve_local.py, then EXP-018 analysis
# If not yet: wait for game to complete, then run resolution
```
