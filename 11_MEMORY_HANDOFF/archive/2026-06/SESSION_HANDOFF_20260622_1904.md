# Session Handoff — 2026-06-22T19:04Z

**Trigger:** Operator-initiated (`/session-end`)
**Last commit:** `3067944` (main) — pushed to GitHub + deployed to VPS

---

## Status

- **Phase:** 6/7 ACTIVE (dark period Phase 1, June 13–30)
- **Tests:** 1280/1280 passing (unchanged this session — governance-only)
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron INACTIVE (dark period; no NBA games until October 2026)
- **Paper bets:** 158/30 resolved — G6 gate (count exceeded; G6 binding blocker is GG-004, not count)

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| **ADR-0028 ACCEPTED** — Segmented per-band promotion thresholds. G6 is T1-only (6 conditions). T4 Tier 2 + T-AGG moved to T4 Activation Gate (Phase 8). Mods 5 (fill-realism) and 9 (YES-only gate) apply at G6. | T4 strategies are BLOCKED in BAND_REGISTRY (Phase 8+). G6 is a T1 live capital gate; requiring T4 evidence for G6 would block live capital indefinitely. | `03_DECISIONS/ADR-0028_segmented-band-promotion-thresholds.md` — ACCEPTED | DS (Earl Ignacio) |
| **T-127/KI-023 window confirmed closed — GG-041 registered** — No live KXNBAPTS orderbook depth data was captured during the 2026 NBA Finals window. Script ran pre-game (2026-06-02, all zeros). All markets finalized 2026-06-14. Deferred to 2026-27 regular season Day 1 (Phase 4, October 2026). | Finals window was the only active KXNBAPTS opportunity before October 2026. ADR-0005 `max_order_pct_of_depth` hard limit has no empirical basis until Phase 4. | `03_DECISIONS/GOVERNANCE_GAP_LOG.md` — GG-041 OPEN; `04_EXECUTION/TODO_NEXT.md` T-127 row updated | DS |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| ADR-0028 sign-off | ✅ ACCEPTED — all 14 checklist items [x], sign-off block populated (Earl Ignacio 2026-06-22) |
| GG-022 RESOLVED | ✅ Status updated in GOVERNANCE_GAP_LOG; fill-realism mandate in ADR-0028 Mod 5 is the resolution artifact |
| DECISION_LOG ADR index (line 46) | ✅ ADR-0028 DRAFT → **ACCEPTED — DS sign-off Earl Ignacio 2026-06-22 SESSION 72** |
| DECISION_LOG SESSION 72 entry | ✅ Added: ADR-0028 acceptance + T-127/KI-023 window miss + GG-041 registration |
| GG-041 registered | ✅ GOVERNANCE_GAP_LOG: KI-023 data collection miss; LOW severity; deferred Phase 4 |
| TODO_NEXT T-148 | ✅ 🔄 PENDING → ✅ DONE (SESSION 72) |
| TODO_NEXT T-127 | ✅ Updated to reflect DEFERRED / Phase 4 October 2026 / GG-041 |
| MEMORY_BANK + PLAN + TODO_NEXT headers | ✅ All updated to SESSION 72 |
| Git commit `3067944` | ✅ Pushed to origin; deployed to VPS (fast-forward) |

---

## ONE THING PENDING

**The dark period work queue is fully up-to-date. The next session should open with the dark period Phase 2 (July 2026) plan.**

Phase 2 starts July 1. Priority order:
1. **T-072** (P0) — Model retrain with playoff-context features (`playoff_round_multiplier`, playoff-opponent defensive stats, within-series momentum). Deadline 2026-10-15. See DECISION_LOG S69 entry for the three authorized feature additions.
2. **T-073** (P1) — DS-04 injury source selection (required before T2 activation).
3. **T-077** (P1) — Polymarket operator KYC (operator action).
4. **ADR-0005 draft** (P2) — Live capital framework. NOTE: `max_order_pct_of_depth` must be labeled PROVISIONAL (no empirical basis until GG-041 resolved Oct 2026).

No code is in-flight. No experiments are running. Clean slate for Phase 2.

---

## Current Paper Portfolio

- Bankroll: **$751.10** (24.9% drawdown; kill switch halted at this level)
- Open: 0 positions ($0.00 deployed)
- Closed/Resolved: 158 | G6 gate: 158/30 (count exceeded; binding G6 blocker = GG-004)
- G6 P&L baseline: **−$248.90** (−24.9% headline, −$212.25/−21.2% clean-only per SNAP-2026-06-16-001)

---

## Active Cron on VPS (157.230.91.33)

```
DARK PERIOD (June 13 – October 2026) — no NBA crons active
Run T-177 monitor manually when needed:
  ssh prediction-market-vps "cd /opt/prediction-market-bot && venv/bin/python3 scripts/run_t177_edge_monitor.py"
```

---

## Key Constraints to Remember

1. **GG-004 is the binding G6 blocker** — EXP-017 CONFIRMED_POSITIVE at ADR-0024 adequate sample (n≥500, ≥15 opponents, OR ≥2 sports × n≥150). No commercial validation yet.
2. **T-072 deadline 2026-10-15** — model must retrain before 2026-27 season tip-off.
3. **GG-041** — ADR-0005 `max_order_pct_of_depth` must stay PROVISIONAL until Phase 4 Day 1 data.
4. **T4 BLOCKED** — All T4 execution paths gated on `_PHASE8_ACTIVE=False`. Phase 8 requires GG-038/039/040 resolution ADRs + activation ADR.
5. Work wifi blocks Kalshi API — use any other network.
6. No live capital until G6 (**30 resolved paper bets + positive P&L + EXP-017 confirmed + ADR-0005 accepted** — APR-0016/APR-0017).

---

## ⚙️ DECISION AUDIT

Governance scan result: **CLEAN** — no `decisions_logged: false` documents found.

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| `ADR-0028_segmented-band-promotion-thresholds.md` | N/A (ADR, not PDTP doc) | SESSION 72 entry written | ✅ |
| `GOVERNANCE_GAP_LOG.md` | N/A (registry, not PDTP doc) | GG-041 + GG-022 updated | ✅ |

---

## Open Governance Gaps (OPEN status)

| Gap | Severity | Blocker for |
|-----|----------|-------------|
| GG-004 | HIGH | G6 — EXP-017 CONFIRMED_POSITIVE required |
| GG-020 | LOW now | ADR-0005 (fee receipt verification post-G6) |
| GG-027 | LOW now | T2/T3/T5 activation (PAM wiring) |
| GG-037 alpha half | HIGH | G6 — alpha vs Kalshi not demonstrated |
| GG-038 | Phase 8 | T4 kill switch ≤5s |
| GG-039 | Phase 8 | T4 price cache |
| GG-040 | Phase 8 | T4 real-time data sources |
| GG-041 | LOW | ADR-0005 `max_order_pct_of_depth` limit empirical basis |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260622_1904.md, confirm 1280 tests"
```
