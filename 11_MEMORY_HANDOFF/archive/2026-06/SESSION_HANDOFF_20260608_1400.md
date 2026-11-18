# Session Handoff — 2026-06-08T14:00Z

**Trigger:** Operator-initiated clean cutover (context approaching limit)
**Last commit:** `0394a93` (main) — pushed to GitHub. VPS HEAD: `4dd2c3d` (GG-014 503 fix).

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** 738/738 passing
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running ✅
- **Paper bets:** 35/30 resolved (G6 30-bet threshold CROSSED) — 20 open (G3, tonight)
- **Bankroll:** $958.99

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| **GHA timing gap → manual TSS cache upload** | GHA at 20:30 UTC writes cache with yesterday's date; PIPE-02 at 21:55 UTC expects today's date → `{}` cache miss. Fix: build locally, SCP to VPS. T-140 registered as ongoing monitoring. | DECISION_LOG.md SESSION 36 entry 3; T-140 | DS |
| **EXP-017 null baseline mip=0.50 was misleading** | Prior EV figures used mip=0.50. Mean model p_estimate < 0.50 → negative edge vs null. But vs actual Kalshi prices: EV=+0.1042/bet. All prior null-baseline EV figures (e.g., EXP-004 +$0.0855/bet) are NOT comparable to Part B. GG-004 OPEN until n≥66. | DECISION_LOG.md SESSION 36 entry 2; GG-004 in GOVERNANCE_GAP_LOG.md | DS |
| **HTTP 503 retry gap (T-138 extension)** | G3 portfolio: 18/20 orders HTTP 503 (not 429). 503 was not in retry tuple. Extended `_post()/_get()` to retry on `(429, 503)` with same 2s/4s/8s backoff. 738/738 tests, commit 4dd2c3d. | DECISION_LOG.md SESSION 36 entry 1; GG-014 in GOVERNANCE_GAP_LOG.md | DS |
| **G6 binding constraints clarified** | 30-bet threshold CROSSED (35 resolved). G6 is now gated on: (a) GG-004 resolved — EXP-017 Part B CONFIRMED, need ≥66 unique markets; (b) ≥5 game nights for slope regression (df≥3). Bet count is no longer binding. Regular season Week 1 may close G6 if both conditions met. | MEMORY_BANK.md Invariant 11; APR-0017 | DS |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| **G2 resolution** | 35 positions resolved, 28W/7L, +$75.67, bankroll $50.96→$958.99, 80% win rate. Pulled VPS portfolio post-resolution. |
| **GG-014 503 fix (T-138 extension)** | G3 showed 18/20 orders as HTTP 503, not 429. Extended `kalshi_client._post()/_get()` retry from `(429,)` to `(429, 503)`. Exponential backoff unchanged (2s/4s/8s). 4 new `TestTransientRetry` tests. 738/738. Commit `4dd2c3d`, deployed to VPS. T-139 registered. |
| **adj_λ cache pre-upload for G3** | GHA wrote `team_stats_cache_20260607.json` (wrong date). Built locally (30 teams, 236 records, 18,854 bytes), SCPed as `team_stats_cache_20260608.json` to VPS. T-140 registered. |
| **EXP-017 Part B (live vs actual Kalshi prices)** | First successful run: `--from-pregame logs/ --portfolio logs/paper_portfolio_vps.json`. n=33 unique markets. EV=+0.1042/bet, 81.8% win rate, mean edge vs market +0.0375. Key insight: mean edge vs null = −0.0486 (prior mip=0.50 figures were misleading). GG-004 OPEN (n=33 < 66 floor). DIRECTIONAL_POSITIVE. |
| **All governance documents updated** | DECISION_LOG.md (4 entries), GOVERNANCE_GAP_LOG.md (GG-004 + GG-014), MEMORY_BANK.md, TODO_NEXT.md (SESSION 36 completed + open items), PLAN.md. Commit `0394a93`. |

---

## ONE THING PENDING

**adj_λ fires tonight for the first time (Finals G3, 21:55 UTC).**

Cache pre-uploaded: `/root/prediction_market_bot/team_stats_cache_20260608.json` (18,854 bytes, confirmed). PIPE-02 at 21:55 UTC should log:
```
[TSS] Loaded from pre-populated cache: 30 teams (ADR-0015)
```
If it instead logs `[TSS] Built fresh: 0/30 teams loaded` or `[TSS] WARNING: 0 teams loaded`, the cache missed and adj_λ is not firing — manually re-upload.

**After G3 resolves (~06:00 UTC Jun 9):**
1. `python3.11 src/prediction_market_bot/run_resolve_local.py` — resolve 20 open positions
2. Re-run `BOT_ENV=paper python3.11 src/prediction_market_bot/run_exp017.py --from-pregame logs/ --portfolio logs/paper_portfolio_vps.json` — target n≈53

---

## Current Paper Portfolio

- **Bankroll:** $958.99
- **Open:** 20 positions (Finals G3, 2026-06-08, SAS vs NYK) — all expected to skip idempotency tonight
- **Closed:** 35 | G6 gate: 35/30 bets CROSSED; binding constraints now ≥66 unique markets (EXP-017) + ≥5 game nights

---

## Active Cron on VPS (157.230.91.33)

```
20:30 UTC  — GHA: team_stats_cache build + SCP to VPS  (check date match!)
21:00 UTC  — Health check
21:55 UTC  — PIPE-02: run_pregame.py (adj_λ ACTIVE TONIGHT — first live test ADR-0015)
22:00 UTC  — PIPE-03: run_paper_trade.py (idempotency skip expected for G3 players)
*/15 20-23 — PIPE-06: T3 momentum scan
*/15 0-3   — PIPE-06: T3 momentum scan (late games)
06:00 UTC  — PIPE-03R: run_resolve.py
```

---

## Key Constraints to Remember

1. Work wifi blocks Kalshi API — use any other network
2. No live capital until G6 (**≥66 unique resolved markets** + **≥5 game nights** + positive P&L — APR-0017)
3. G6 30-bet threshold already CROSSED (35 resolved). Binding constraints now: GG-004 (n=33<66) + game night count (need ≥5)
4. Temp filesystem `/Users/earlignacio/.claude/tmp` at 0MB — Step 1 governance scan will fail; run manually if needed

---

## ⚙️ DECISION AUDIT

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| DECISION_LOG.md | N/A (is the log) | 4 SESSION 36 entries written this session | ✅ |
| GOVERNANCE_GAP_LOG.md | N/A (gap tracker) | GG-004 + GG-014 updated | ✅ |
| MEMORY_BANK.md | N/A (memory) | Updated to SESSION 36 state | ✅ |
| TODO_NEXT.md | N/A (task list) | SESSION 36 completed + open items added | ✅ |
| PLAN.md | N/A (plan) | Phase 6 deliverable updated: 35/66 markets | ✅ |

Governance scan for `decisions_logged: false` documents: **could not run** — temp filesystem at 0MB (ENOSPC). No documents were created or substantially modified this session beyond the governance artifacts above. Item 4 (temp filesystem) remains open.

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260608_1400.md, then check VPS PIPE-02 log for adj_λ activation tonight (team_stats_cache_20260608.json). If G3 has resolved, run run_resolve_local.py and re-run EXP-017 Part B."
```
