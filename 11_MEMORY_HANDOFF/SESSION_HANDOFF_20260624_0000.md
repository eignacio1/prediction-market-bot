# Session Handoff — 2026-06-24T00:00Z

**Trigger:** Operator-initiated session close
**Last commit:** `89d795c` (main) — pushed to GitHub + VPS deployed

---

## Status

- **Phase:** 6/7 ACTIVE — dark period (NBA Finals ended; MLB Phase 3 build in progress)
- **Tests:** 1650/1650 passing
- **Capital:** NO live capital — paper trading only (NBA book halted at drawdown kill switch)
- **VPS:** 157.230.91.33 — cron running (dark-period cadence; NBA crons active; NBA book halted at 25.12% drawdown)
- **Paper bets:** G6 gate NOT active — binding constraint is GG-004 (EXP-017 commercial validation, MLB August 2026)

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| **GG-006 CLOSED — Kalshi Participant Agreement confirms no automation restrictions** | Formally read Kalshi Member Agreement v1.54, Rule 5.13(s), Rule 5.15, Rulebook. No provisions restrict automated/algorithmic trading for retail members. Rule 5.13(s) = source agency insiders only (inapplicable). Rule 5.15 algorithm mention targets Kalshi's own affiliated market makers, NOT retail participants. Position Limits confirmed moot per DS ($1,000 fresh MLB bankroll; $500 max_single_event_exposure_usd per position). | GOVERNANCE_GAP_LOG.md GG-006, DECISION_LOG.md SESSION 80 entry | DS |
| **T-186 outcome: valid negative — deploy v2-065b9510 in October (ADR-0031 unchanged)** | F-042 (`opp_playoff_def_rating_l5_mean`) produces only Brier delta +0.000130 vs required ≥0.001 after proper data population (76/103 playoff rows non-NaN). Root cause: `nba_api.TeamGameLog` omits `PLUS_MINUS` for all season types — F-040 and F-042 were dead features (imputed 0.0) throughout EXP-005 training. Cross-reference fix correctly populates pts_allowed but insufficient playoff training sample (n=76) means F-042 cannot clear shadow gate. ADR-0031 October deployment unchanged. | DECISION_LOG.md T-186 entry SESSION 80, ADR-0031 Known Limitations | DS |
| **MLB paper book: fresh $1,000 separate pool (confirmed S80)** | Confirmed prior S74 decision. EXP-017 MLB must run on a book experimentally independent of NBA P&L history. `logs/paper_portfolio_mlb.json` to be initialized at T-187. | DECISION_LOG.md SESSION 80 entry | DS |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| **T-117 — GG-006 RESOLVED: Kalshi Participant Agreement** | ✅ Three Kalshi legal documents read via pypdf: Member Agreement v1.54, Rule 5.13(s), Rule 5.15 + Rulebook. No automation restrictions. Position Limits moot. ADR-0005 GG-006 pre-requisite satisfied. GG-006 CLOSED in GOVERNANCE_GAP_LOG.md. |
| **T-186 — F-042 playoff TeamGameLog + v2b retrain** | ✅ Root cause: `nba_api.TeamGameLog` omits `PLUS_MINUS` → pts_allowed NaN everywhere → F-040 and F-042 dead (imputed 0.0) in all EXP-005 training. Fix: `_fill_pts_allowed_via_crossref()` in `pull_playoff_teamgamelog.py` — builds `(game_date, abbr)→pts` lookup, derives `plus_minus = my_pts − opp_pts` from MATCHUP; 338/338 games populated (22 teams). v2b retrain: F-042 76/103 non-NaN (73.8%); Brier +0.000130 < 0.001 threshold → shadow gate FAIL. Valid negative — F-042 insufficient at available sample size. |
| **10 new cross-reference tests (TestPtsAllowedCrossRef)** | ✅ Covers `_parse_opponent_abbr` (5: vs./@ matchup formats, uppercase, None, empty) and `_fill_pts_allowed_via_crossref` (5: correct population, missing opponent → NaN, multiple games, empty dict, preserves original columns). Suite 1640→1650/1650. |
| **DECISION_LOG SESSION 80 entries** | ✅ T-117/GG-006 entry + T-186 entry written. |
| **T-187 REGISTERED** | ✅ `scripts/run_mlb_paper_trade.py` MLB paper trading runner (P0, before August 2026). Requires: KXMLBHIT market fetching, MLB C1/C2/C3 pipeline integration, fresh $1,000 `logs/paper_portfolio_mlb.json` book initialization, MLB cron entries in `deploy/cron.conf`. |
| **Commit + push + VPS deploy** | ✅ `89d795c` [SESSION 80 CLOSE] — HEAD confirmed on VPS 157.230.91.33. |

---

## ONE THING PENDING

**T-187 — `scripts/run_mlb_paper_trade.py`** is the only P0 item remaining before MLB paper trading activates in August 2026.

Required:
1. `KXMLBHIT` market fetching — `kalshi_client.py` already has `get_mlb_player_hit_markets()` stub (confirmed ticker `KXMLBHIT`); wire into MLB paper runner
2. MLB C1/C2/C3 pipeline integration — all three pipeline modules exist; MLB forecaster `predict_proba()` uses `sport="mlb"` artifact schema
3. Initialize `logs/paper_portfolio_mlb.json` with fresh $1,000 book (same structure as NBA book)
4. Add MLB cron entries to `deploy/cron.conf` — distinct windows from NBA crons (MLB games start ~18:00 ET / ~22:00 UTC)

Read `deploy/cron.conf` and `scripts/run_paper_trade.py` before writing T-187 to understand the NBA runner pattern.

---

## Current Paper Portfolio

- **NBA book:** bankroll ~$751 (halted at drawdown kill switch; 25.12% > 20%; PIPE-03 refuses new bets)
- **MLB book:** `logs/paper_portfolio_mlb.json` NOT YET INITIALIZED — created at T-187
- **Open bets:** 0 (NBA dark period; no live NBA games)
- **G6 gate:** NOT counting — binding constraint is GG-004 (EXP-017 MLB commercial validation, target August–September 2026)

---

## Active Cron on VPS (157.230.91.33)

```
21:00 UTC  — Health check
21:30 UTC  — PIPE-02 inference (run_pregame.py) — runs but no active NBA games
22:00 UTC  — PIPE-03 early (paper bets) — halted at kill switch
01:30 UTC  — PIPE-03 late (paper bets) — halted at kill switch
06:00 UTC  — PIPE-03R resolve-only (run_resolve.py)
14:00 UTC Mon — Model freshness check
```

MLB crons: NOT YET ADDED — needed at T-187.

---

## Key Constraints to Remember

1. Work wifi blocks Kalshi API — use any other network
2. No live capital until G6 (GG-004 resolved + APR-0017 tiers met + ADR-0005 accepted)
3. NBA book halted at 25.12% drawdown — kill switch fires before any new NBA bets
4. `arb/` folder = REFERENCE ONLY (hard rule 1)
5. BOT_C4_ACTIVE must NOT be set during any offline script or training run
6. F-040 (`opp_def_rating_l10_mean`) is ALSO dead in v1/v2 models — both opponent defensive features were imputed 0.0 throughout EXP-005 training. This is a known limitation of all current models.

---

## ⚙️ DECISION AUDIT

**Governance scan:** CLEAN — `grep -rn "^\*\*Decisions logged:\*\* false"` returned no matches.

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| GOVERNANCE_GAP_LOG.md (GG-006 updated) | N/A — gap log, not a strategy doc | GG-006 closure logged in DECISION_LOG S80 | ✅ |
| scripts/pull_playoff_teamgamelog.py (new) | N/A — implementation | T-186 entry in DECISION_LOG S80 | ✅ |
| scripts/train_model_v2b.py (new) | N/A — implementation | T-186 entry in DECISION_LOG S80 | ✅ |
| data/playoff_teamgamelog_cache.json (new) | N/A — data artifact | Covered by T-186 DECISION_LOG entry | ✅ |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260624_0000.md. Next task is T-187: MLB paper trading runner. Read deploy/cron.conf and scripts/run_paper_trade.py first to understand the NBA runner pattern."
```

---

## Q6 Standing Concerns (Carry Forward)

1. **GG-004 (OPEN) — commercial validation**: No demonstrated alpha vs Kalshi market prices. EXP-017 MLB targets August–September 2026 paper trading accumulation (n≥20 to start; n≥150 for Tier 1). The NBA edge is anti-predictive (T-177 ANTI-PREDICTIVE, p=0.0505 at n=114). System is operating in a negative-P&L state. This is the binding G6 blocker.

2. **F-040 dead in all models**: `opp_def_rating_l10_mean` (regular season opponent defensive rating) has been imputed 0.0 in every model since EXP-005. Same root cause as F-042 (PLUS_MINUS absent from `nba_api.TeamGameLog`). No fix is possible without re-building the regular-season training pipeline with cross-reference approach. Deferred — impact is symmetric across training and inference (the model learned without this feature; inference without it is consistent).

3. **GG-020 (OPEN)** — Kalshi fee rate 0.07 vs 0.06 for sports markets. Unverifiable without live transaction receipts. Conservative direction (over-deduct fees). Remains open post-G6.
