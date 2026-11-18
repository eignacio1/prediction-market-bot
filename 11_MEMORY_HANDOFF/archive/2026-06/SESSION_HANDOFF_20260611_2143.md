# Session Handoff — 2026-06-11T21:43Z

**Trigger:** Operator-initiated session wrap (context window approaching limit)
**Last commit:** `4d5cd43` (main) — pushed to GitHub + VPS deployed

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** 852/852 passing
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron ACTIVE (PIPE-02/03/06/07 all running)
- **Paper bets:** 114 resolved T1 | 1115+ T4 | G5 (Jun 13) bets already placed (29 open)

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| PAM archetype register wired to T1 + T4 now; full band integration (T2/T3/T5 + EnvironmentClassifier) deferred to MLB gate | Token cost of full build for NBA Finals not justified at current scope; Finals has fewest players of any sport; wiring T1+T4 as registers captures the value available now without over-engineering | DECISION_LOG.md SESSION 50 entry | DS |
| EnvironmentClassifier (elimination_flag, series_momentum, crowd_premium, role_expansion_flag → HIGH_PRESSURE / NEUTRAL / LOW_STAKES) explicitly scoped as MLB-gate deliverable, not Finals deliverable | Three-layer integration (C2 EnvironmentClassifier + C3 uncertainty multiplier + decision tree dynamic MIN_EDGE_TO_APPROVE) requires dedicated ADR; insufficient data at Finals scale to calibrate; MLB regular season volume is the right calibration surface | GG-027, T-165, DECISION_LOG.md SESSION 50 entry | DS |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| `get_archetype()` added to `QualitativeSignalStore` | ✅ Point-lookup with QTI-01 temporal guard. Returns `{prf_primary, prf_primary_name, active_modifiers, [prf_secondary/name/weight if hybrid]}` or None |
| T1 archetype register wiring (`run_paper_trade.py`) | ✅ `_pam` lookup per cohort player; `pam_archetype` in `forecast_rec`; `[PRF-X]` tag in BET print line |
| T4 archetype register wiring (`run_t4_inplay.py`) | ✅ `archetype_register` injected on `T4EventLoop`; `pam_archetype: Optional[dict] = None` on `T4RoutingResult`; best-effort lookup in `on_game_state_event`; KILL_SWITCH path intentionally excluded |
| GG-027 registered | ✅ `03_DECISIONS/GOVERNANCE_GAP_LOG.md` — T2/T3/T5 unwired + EnvironmentClassifier not built; LOW now, HIGH pre-MLB |
| T-165 registered | ✅ `04_EXECUTION/TODO_NEXT.md` item 7 — full band integration + EnvironmentClassifier ADR; MLB activation gate |
| DECISION_LOG SESSION 50 entry | ✅ Full entry with all five changes documented including design rationale for best-effort pattern and KILL_SWITCH exclusion |
| Git commit + VPS deploy | ✅ Commit `4d5cd43`; VPS fast-forward `git pull` confirmed |

---

## ONE THING PENDING

**G5 resolves Jun 13 (game_date=2026-06-13).** 29 T1 bets placed; 9/29 Kalshi demo orders failed (31% rate; GG-014 G6 gate BREACHED). T-164 throttle fix is deployed — the G6 gate confirmation requires the next actual batch run to return ≤5% failure rate. After G5, run:
1. `run_resolve_local.py` (T1 resolve from Mac — nba_api blocks VPS)
2. `run_t4_resolve_local.py` (T4 resolve)
3. `python scripts/run_exp018.py` (update EXP-018 with G5 data)

GHA resolve workflow fires automatically 05:30 UTC Jun 14.

---

## Current Paper Portfolio

- **T1 bankroll:** $285.27 (VPS; post-G4 resolve; $848.73 deployed in 29 open G5 positions)
- **T4 pool:** $1,869.68 | G5 budget ~$504.81 (× 0.27 ADR-0023)
- **Open:** 29 T1 positions (game_date=2026-06-13); T4 will generate ~1,000+ during game
- **Resolved:** 114 T1 | ~1,115+ T4
- **G6 gate progress:** T1 floor MET (114 ≥ 66); T4 floor trivially met; GG-004 OPEN (EXP-017B DIRECTIONAL_NEGATIVE vs Kalshi prices)

---

## Active Cron on VPS (157.230.91.33)

```
21:00 UTC     — Health check
21:55 UTC     — PIPE-02 inference (run_pregame.py; adj_λ ACTIVE)
22:00 UTC     — PIPE-03 early (paper bets; T3 overlay ACTIVE; in-progress guard ACTIVE)
*/15 20-23    — PIPE-06 T3 signal scan
*/15 0-3      — PIPE-06 T3 signal scan (late games)
01:25 UTC     — PIPE-02 late
01:30 UTC     — PIPE-03 late
06:00 UTC     — PIPE-03R resolve-only
23:00 UTC     — PIPE-07 T4 in-play (run_t4_live.py; EXIT_MECHANICS_ACTIVE=True)
GHA 05:30 UTC — Auto-resolve (T1 + T4; VPS_SSH_KEY; GHA runners bypass Akamai block)
GHA 20:30 UTC — TSS cache build (team_stats_cache_YYYYMMDD.json → VPS)
```

---

## Key Constraints to Remember

1. No live capital until G6 (APR-0017 four-tier evidence standard; GG-004 OPEN)
2. GHA auto-resolve is PRIMARY; Mac cron `post_game_g5_resolve.sh` is fallback + experiment runner
3. T-164 throttle fix deployed but G6 gate (≤5% order failure rate) requires next batch run to confirm
4. EXP-018 Hypothesis C: DS ruling = calibration gap (not T1 Tier 2B FAILS); G5 data will update verdict
5. Dark period begins ~Jun 22 after Finals end; next active paper window = 2026-27 regular season week 1
6. GG-027 is LOW now — do NOT wire T2/T3/T5 to PAM or build EnvironmentClassifier before MLB activation gate (T-165)

---

## ⚙️ DECISION AUDIT

**Governance scan:** CLEAN — no `decisions_logged: false` documents found.

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| `qualitative_store.py` | N/A — code file | SESSION 50 entry | ✅ |
| `run_paper_trade.py` | N/A — code file | SESSION 50 entry | ✅ |
| `run_t4_inplay.py` | N/A — code file | SESSION 50 entry | ✅ |
| `GOVERNANCE_GAP_LOG.md` | N/A | GG-027 registered | ✅ |
| `TODO_NEXT.md` | N/A | T-165 registered, SESSION 50 block | ✅ |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260611_2143.md.
# G5 (Jun 13) is next. After G5 resolves: run run_resolve_local.py, run_t4_resolve_local.py,
# then run EXP-018 update. Priority queue: T-157 (stop criterion), T-153 (fill-realism haircut),
# T-158 (dark period plan)."
```
