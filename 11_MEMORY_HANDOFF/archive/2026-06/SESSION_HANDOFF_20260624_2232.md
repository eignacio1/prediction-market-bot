# Session Handoff — 2026-06-24T22:32Z

**Trigger:** Session end — context window closing; MLB accumulation live  
**Last commit:** `42bce66` (main) — pushed to GitHub; deployed to VPS via osascript Terminal launch

---

## Status

- **Phase:** 6/7 ACTIVE — MLB paper trading LIVE as of tonight
- **Tests:** 1790/1790 passing (0 failures, 1 skipped)
- **Capital:** NO live capital — NBA paper book halted (25.12% drawdown); MLB fresh $1,000 paper book
- **VPS:** 157.230.91.33 — all crons running
- **Paper bets (MLB):** 0 open — first PIPE-05 run tonight 23:30 UTC
- **Paper bets (NBA):** 0/30 G6 gate — NBA book halted at kill switch, dark period

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| T-188: MLB dashboard must use full curses TUI (clone of `live_terminal.py` engine) | Plain-text renderer failed at any terminal width; VPS volume (~10,000 bets/day) requires background SSH thread and double-buffer draw; the NBA dashboard architecture is the proven pattern | `scripts/run_mlb_dashboard.py` (commit 42bce66); DECISION_LOG S83 T-188 entry | EL |
| MLB accumulation declared LIVE as of 2026-06-24 | All T-187 A–H complete; 5-6 weeks ahead of original August plan; sooner accumulation = sooner EXP-017 Tier 1 (n≥150) | DARK_PERIOD_PLAN.md Phase 3 row corrected; DECISION_LOG S83 MLB live entry | DS |
| pyarrow must be installed in VPS venv | PIPE-05FX parquet cache fails with `ImportError: Unable to find a usable engine` without it | VPS: `/opt/prediction-market-bot/venv/bin/pip install pyarrow` → 24.0.0; DECISION_LOG S83 | EL |
| Monte Carlo run on 2026-06-25 slate — engine hygiene verified | Pre-run sanity check on all MLB engines before first live PIPE-05 run | DECISION_LOG S83 Monte Carlo entry; `scratchpad/mlb_montecarlo.py` | EL |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| **T-188: MLB curses TUI dashboard** | ✅ `scripts/run_mlb_dashboard.py` rewritten as full curses TUI matching `live_terminal.py`. Panels: portfolio (fixed 4L), system (fixed 6L — KS + 4 PIPE timestamps), live_pos (56%), today_slate (44%), resolved, alerts, pipe_log. Background SSH ControlMaster thread. GG-034 `_pos_pnl()` helper. Commits: d0303c7, bc08721, 42bce66. |
| **MLB accumulation declared LIVE** | ✅ PIPE-05 first run tonight 23:30 UTC. DARK_PERIOD_PLAN + MEMORY_BANK + TODO_NEXT + DECISION_LOG all updated. |
| **pyarrow VPS install** | ✅ 24.0.0 installed before 22:30Z PIPE-05FX cron. |
| **Monte Carlo 2026-06-25 slate** | ✅ Engine hygiene verified: C4, calibration identity, YES-only gate, SP overlay fallback, GG-034 P&L all correct. |
| **DECISION_LOG S83 entries** | ✅ T-188, MLB live declaration, Monte Carlo entries appended. |
| **Session-end protocol** | ✅ DECISION_LOG + TODO_NEXT + PLAN + MEMORY_BANK + HANDOFF all updated. |

---

## ONE THING PENDING

**Monitor tonight's PIPE-05 run.** First live MLB paper trading run fires at 23:30 UTC. Check VPS logs:
```bash
ssh prediction-market-vps "tail -50 /opt/prediction-market-bot/logs/paper_mlb_cron.log"
```
Expected: bets placed on tonight's MLB slate (thresholds t=1 and t=2 only). Non-fatal: `game_starters_fetch_error` (VPS IP blocked by MLB Stats API — `opp_sp_is_known=0` fallback engages). Non-fatal: `kalshi_client_init_failed` (paper mode warning).

Check dashboard live:
```bash
python3 scripts/run_mlb_dashboard.py --remote root@157.230.91.33 --log-dir /opt/prediction-market-bot/logs/
```

---

## Current Paper Portfolio

### NBA Book (halted)
- Bankroll: ~$748.79 (25.12% drawdown — kill switch active)
- Open: 0
- Closed: 158 resolved | G6 gate: 0/30 (EXP-017 CONFIRMED_POSITIVE required first)

### MLB Book (fresh — first run tonight)
- Bankroll: $1,000 (fresh, separate pool)
- Open: 0 (bets fire tonight 23:30 UTC)
- Closed: 0 | EXP-017 MLB: 0/20 minimum for first run

---

## Active Cron on VPS (157.230.91.33)

```
21:00 UTC       — Health check
21:55 UTC       — PIPE-02 (run_pregame.py — NBA, dark period, no games so empty runs)
22:00 UTC       — PIPE-03 early (NBA paper bets — kill switch halted)
22:30 UTC       — PIPE-05FX (mlb_feature_refresh.py — updates feature CSV)
23:30 UTC       — PIPE-05 (run_mlb_paper_trade.py — MLB paper bets) ← FIRST RUN TONIGHT
01:25 UTC       — PIPE-02 late
01:30 UTC       — PIPE-03 late (NBA — halted)
06:00 UTC       — PIPE-03R (NBA resolve — dark period, no new closures)
06:30 UTC       — PIPE-05R (run_resolve_mlb.py — MLB resolution)
14:00 UTC Mon   — Model freshness check
14:10 UTC Mon   — PIPE-05C (run_mlb_calib_monitor.py — calibration check)
```

---

## Key Constraints to Remember

1. No live capital until G6 (**30 resolved paper bets** + positive P&L — APR-0016); NBA kill switch still active at 25.12%
2. MLB YES-only gate: `MLB_PAPER_YES_ONLY=true` — only YES-direction bets placed
3. MLB thresholds: t∈{1,2} only — t=3 excluded (GG-042, structural)
4. VPS IP blocked by MLB Stats API for schedule/roster (Fastly CDN) — non-fatal, `opp_sp_is_known=0` fallback engages
5. `exp_output/MLB/` is untracked (local only — large parquet/CSV files)
6. EXP-017 MLB: run `scripts/run_exp017_mlb.py` after ≥20 closed MLB positions

---

## ⚙️ DECISION AUDIT

Governance scan: `grep -rn "^\*\*Decisions logged:\*\* false" 02_ARCHITECTURE_DESIGN/ 08_MODEL_RISK_GOVERNANCE/ 01_SPEC/ 2>/dev/null` → CLEAN (run at session start).

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| `scripts/run_mlb_dashboard.py` (new) | n/a (not a governance doc) | T-188 S83 entry ✅ | ✅ |
| `04_EXECUTION/DARK_PERIOD_PLAN.md` (modified) | true | MLB live declaration entry ✅ | ✅ |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260624_2232.md, confirm 1790 tests. MLB PIPE-05 first run was tonight — check VPS logs and monitor accumulation."
```
