# Session Handoff — 2026-06-24T02:06Z (SESSION 75 CLOSE)

**Trigger:** Operator-initiated session end  
**Last commit:** pending (commit this file with the session close commit)

---

## Status

- **Phase:** 6/7 ACTIVE (dark period — NBA off-season; MLB Phase 3 in progress)
- **Tests:** 1373/1373 passing
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — NBA cron dark (off-season); MLB paper trading NOT yet active (T-182/183/184 required first)
- **Paper bets:** 158/30 resolved — G6 gate (P&L = −$248.90/24.9% drawdown; G6 positive-P&L gate FAILING; binding blocker is EXP-017 GG-004)

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| MLB C1 data source: MLB Stats API (statsapi.mlb.com) via raw HTTP requests — no pip wrapper | Official MLB source, free, unauthenticated; no new package needed beyond `requests` (now explicit in pyproject.toml); same architecture as NBA C1 (raw requests in kalshi_client.py); live API probed and response shapes confirmed before coding | DECISION_LOG.md SESSION 75 entry | EL |
| IF-C1-C2 MLB contract established: batter 24-col schema, pitcher 22-col schema, game starters gamePk dict | Three schemas required to give C2 all inputs needed for rolling batting features (batter log), SP overlay (pitcher log + game starters join), and park factor context | `mlb_ingestion.py` `_MLB_BATTER_COLUMNS` / `_MLB_PITCHER_COLUMNS` / `fetch_game_starters()` return shape | EL |
| ERA computation: total ER ÷ total IP × 9 (NOT mean of per-game ERA) | Short outings (e.g., 0.1 IP after giving up 3 ER) distort per-game ERA catastrophically; aggregate totals avoid this; matches sabermetric standard | `mlb_pitcher_stats_store.py:_era()` | EL |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| **T-181: MLB C1 data ingestion module** | ✅ COMPLETE — 3 new source files, 80 new tests, 1373/1373 total green |
| `mlb_ingestion.py` | ✅ `MLBIngestionClient` — `fetch_batter_game_log`, `fetch_pitcher_game_log`, `fetch_batter_game_logs_bulk`, `fetch_pitcher_game_logs_bulk`, `fetch_game_starters`, `fetch_completed_games`. All `(bool, DataFrame|dict)`. C6 audit trail. 0.6s throttle. Retry w/ backoff. `_team_abbr_map` injection for test isolation. `_FALLBACK_TEAM_ABBR` for offline graceful degradation. |
| `mlb_team_stats_store.py` | ✅ `MLBTeamStatsStore` — `get_opp_runs_allowed`, `get_opp_runs_scored`, `build_from_games()` classmethod, TI-01 temporal guard (`game_date < as_of_date`), cache serialization (`to_cache_dict` / `from_cache_dict`). |
| `mlb_pitcher_stats_store.py` | ✅ `MLBPitcherStatsStore` — `get_era_l5`, `get_k_per_9_l5`, `get_bb_per_9_l5` via aggregate totals (not per-game mean), `is_start==0` relief exclusion, TI-01 guard, cache serialization. |
| `c1_signal_ingestion/__init__.py` | ✅ Updated — exports `MLBIngestionClient`, `MLBTeamStatsStore`, `MLBPitcherStatsStore` |
| `kalshi_client.py` | ✅ `SERIES_MLB_PLAYER_HITS = "KXMLBHITS"` placeholder added with explicit UNCONFIRMED comment |
| `pyproject.toml` | ✅ `requests>=2.31.0,<3.0` added as explicit dependency |
| `tests/test_t181_mlb_c1.py` | ✅ 80 tests, 0 live HTTP calls, all passing. 13 test classes covering init, batter/pitcher log success/error paths, column contract, bulk concat + partial-failure propagation, game starters dict shape, completed games Final-only filter, team store rolling stats + build_from_games, pitcher ERA/K9/BB9 value verification, relief exclusion, temporal boundary, cache round-trip. |
| DECISION_LOG.md SESSION 75 entry | ✅ Written this session |
| TODO_NEXT.md T-181 → COMPLETE | ✅ Updated this session |
| MEMORY_BANK.md | ✅ Updated this session |
| PLAN.md | ✅ Updated this session |

**Test delta:** 1293 → 1373 (+80)

---

## ONE THING PENDING

**Known issue (KI) that must not be forgotten before MLB paper trading activates:**

`SERIES_MLB_PLAYER_HITS = "KXMLBHITS"` is a **placeholder ticker** in `kalshi_client.py:114`. It is not confirmed. A wrong ticker causes `fetch_markets()` to return empty results silently — the same failure mode as KI-019 (Polymarket NBA tag). Before MLB paper trading is activated (i.e., before T-182 → T-183 → T-184 pipeline is wired into a live PIPE-03 run), this must be verified:

```bash
# On any machine with Kalshi API access:
GET https://trading-api.kalshi.com/trade-api/v2/series
# Look for MLB player props series ticker
```

This is registered in DECISION_LOG SESSION 75 and TODO_NEXT.md T-181 complete entry.

**Next task after this commit:** T-182 (MLB C2 feature set, P0) — rolling BA/SLG/OPS (L10), SP ERA/K9/BB9 overlay (L5 starts), park factor, home/away split, rest differential. Starting pitcher overlay is MANDATORY (equivalent of T2 injury overlay for MLB).

---

## Current Paper Portfolio

- Bankroll: $751.10 (24.9% drawdown)
- Open: 0 positions, $0 deployed
- Closed/Resolved: 158 | G6 gate: 158/30 ✓ (count met; positive P&L gate FAILING; EXP-017 GG-004 is the binding blocker)

---

## Active Cron on VPS (157.230.91.33)

NBA dark period — cron is quiet. No active paper trading until T-185 (October 2026 NBA restart) or MLB Phase 3 pipeline wired. Healthcheck.sh runs per schedule; no bets being placed.

---

## Key Constraints to Remember

1. **`KXMLBHITS` is unconfirmed** — verify via `GET /series` before any MLB paper bet is placed
2. **G6 positive-P&L gate is FAILING** (−$248.90) — EXP-017 at adequate sample (ADR-0024: n≥500 or 2 sports × n≥150) is the path forward; paper trading resumption is an evidence-collection decision, not a confirmed-alpha deployment
3. **T-186 is HIGH severity before NBA 26-27 restart** — F-042 playoff TeamGameLog was NaN everywhere in v2 training data; v2b retrain required before October
4. **No live capital until G6** — ADR-0005 not finalized; EXP-017 not CONFIRMED_POSITIVE

---

## ⚙️ DECISION AUDIT

**Governance scan:** `grep -rn "^\*\*Decisions logged:\*\* false" 02_ARCHITECTURE_DESIGN/ 08_MODEL_RISK_GOVERNANCE/ 01_SPEC/` → **CLEAN**

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| `mlb_ingestion.py` | n/a (source file, not governance doc) | SESSION 75 DECISION_LOG entry written | ✅ |
| `mlb_team_stats_store.py` | n/a | SESSION 75 DECISION_LOG entry written | ✅ |
| `mlb_pitcher_stats_store.py` | n/a | SESSION 75 DECISION_LOG entry written | ✅ |

---

## Commit Message

```
[SESSION 75 CLOSE] T-181 COMPLETE: MLB C1 data ingestion module (80 tests, 1373 green)

- T-181: MLBIngestionClient (mlb_ingestion.py) — 6 public methods, C6 audit trail,
  0.6s throttle, retry/backoff, _team_abbr_map injection for test isolation
- T-181: MLBTeamStatsStore (mlb_team_stats_store.py) — get_opp_runs_allowed/scored,
  build_from_games(), TI-01 temporal guard, cache serialization
- T-181: MLBPitcherStatsStore (mlb_pitcher_stats_store.py) — ERA/K9/BB9 via aggregate
  totals (not per-game mean), relief exclusion, TI-01 guard, cache serialization
- pyproject.toml: requests>=2.31.0 added as explicit dependency
- kalshi_client.py: SERIES_MLB_PLAYER_HITS="KXMLBHITS" placeholder (UNCONFIRMED)
- DECISION_LOG: SESSION 75 DS data-source decision entry
- Tests: 1293 → 1373 (+80); 0 regressions
- Gate: Phase 3 MLB in progress — T-182 (C2 feature set) next
```

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260624_0206.md.
# T-181 is complete (MLB C1). Begin T-182 (MLB C2 feature set) — full institutional depth."
```
