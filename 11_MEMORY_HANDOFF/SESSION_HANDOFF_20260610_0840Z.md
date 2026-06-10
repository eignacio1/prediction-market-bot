# Session Handoff — 2026-06-10T08:40Z

**Trigger:** Session end — G4 readiness complete, all systems automatic
**Last commit:** `0644d04` (main) — pushed to GitHub + VPS deployed

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** 817/817 passing (no new tests this session — GHA workflow is YAML only)
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running (PIPE-02/03/07 all active, HEAD `0644d04`)
- **Paper bets:** 82 T1 resolved bets (82/66 floor ✓) — game nights 3/5; G4 = tonight

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| GHA runners as primary post-game resolve path | nba_api 403-blocked on VPS (Akamai WAF on DigitalOcean IPs); Mac cron requires Mac to be on. GHA runners are not blocked. `VPS_SSH_KEY` secret already existed (tss_daily_sync.yml). SSH key written to `~/.ssh/id_ed25519_droplet` to match hardcoded path in both resolve scripts — no source changes required. Mac `post_game_g4_resolve.sh` remains as fallback + experiment runner (EXP-017/018 rerun is in Mac script, not GHA workflow). Race condition safe: both scripts idempotent (0 open positions → clean exit). | DECISION_LOG.md SESSION 44 entry; `.github/workflows/post_game_resolve.yml` | DS (Earl) |
| T4 `current_daily_loss` stale-date reset | `current_daily_loss=$157.89` carried forward from G3 in `paper_portfolio_t4.json`. Without date-check reset at game-loop entry, first G4 bet would immediately breach the 15% drawdown kill switch and halt T4 for the entire game. Fix: `run_t4_live.py:438` — if `portfolio_data.get("daily_loss_date") != today_str`, reset `current_daily_loss=0.0` before entering the loop. | DECISION_LOG.md SESSION 44 entry; `src/prediction_market_bot/run_t4_live.py:438` | DS (Earl) |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| Session-start protocol (Steps 1–3 + Q1–Q6) | ✅ Complete — governance scan clean; stub scan CLEAN; 4 OPEN governance gaps reviewed; Q6 surfaced T4 stale-date bug as critical pre-G4 find |
| T4 stale daily-loss kill switch bug | ✅ Fixed — `run_t4_live.py:438` date-check reset. Commit `a300a51`. Deployed VPS. |
| GHA post-game resolve workflow | ✅ Created `.github/workflows/post_game_resolve.yml` — 05:30 UTC schedule + workflow_dispatch. SSH to VPS via `VPS_SSH_KEY`. Resolves T1 (`run_resolve_local.py`) then T4 (`run_t4_resolve_local.py`). Verified workflow_dispatch run 27253281067 (35s, all green — T1 81,610 bytes pulled/0 open; T4 1,123,127 bytes pulled/0 open). Commit `aa263fb`. Deployed VPS. |
| DECISION_LOG updated | ✅ Both SESSION 44 entries written (stale-date fix + GHA resolve architecture) |
| MEMORY_BANK updated | ✅ Header, Last major milestone, VPS section all reflect SESSION 44 state |
| Final governance commit | ✅ `0644d04` — DECISION_LOG + MEMORY_BANK + TODO_NEXT + PLAN + SESSION_HANDOFF |

---

## ONE THING PENDING

**G4 resolves automatically tonight.** Game 4 tips ~00:30 UTC Jun 11 (5:30 PM PDT Jun 10). System runs:
- **PIPE-02** at 21:30 UTC (pregame TSS cache + adj_λ)
- **PIPE-03** at 22:00 UTC (T1 paper bets)
- **PIPE-07** at 23:00 UTC (T4 live paper trading, runs until ~04:00 UTC)
- **GHA post_game_resolve.yml** at 05:30 UTC Jun 11 (T1+T4 resolve — PRIMARY)
- **Mac post_game_g4_resolve.sh** at 06:00 UTC Jun 11 (`0 23 10 6 *` cron — FALLBACK + EXP-017/018 rerun)

No operator action needed during the game. First post-game task:

**After G4 resolves (post 06:00 UTC Jun 11):** Check `paper_portfolio.json` and `paper_portfolio_t4.json` on VPS for resolved positions. Run EXP-018 DS decision (Hypothesis C: injury-filter view vs. overall — G4 data expands n). Note if EXP-017 Part B crosses APR-0017 significance threshold. T-152/T-153 (EXP-019B/C empirical) become eligible after G4+G5 trajectory/spread data collected.

---

## Current Paper Portfolio

- **T1 Bankroll:** $876.83 (12.3% drawdown) — 0 open positions (all G3 resolved)
- **T4 Pool:** $1,539.42 — 0 open positions (all G3 resolved); pool_isolated=True
- **Resolved:** 82 T1 bets (G1+G2+G3), 1,330 T4 bets (G1+G2+G3)
- **G6 gate:** 82/66 bets ✓; 3/5 game nights — need G4 (tonight) + G5 (~Jun 12)

---

## Active Cron on VPS (157.230.91.33)

```
21:00 UTC        — Health check (PIPE-01)
21:25 UTC        — TSS cache pre-check (run_t140_check.py)
21:30 UTC        — PIPE-02 pregame inference (run_pregame.py + adj_λ)
22:00 UTC        — PIPE-03 early (T1 paper bets)
01:30 UTC        — PIPE-03 late (T1 paper bets, 9pm+ ET games)
06:00 UTC        — PIPE-03R resolve-only (VPS-only; finds 0 positions after GHA resolves first)
23:00 UTC        — PIPE-07 T4 live paper trading (run_t4_live.py, 6h timeout)
14:00 UTC Mon    — Model freshness check
```

**GitHub Actions (runs on GHA, not VPS):**
```
05:30 UTC daily  — post_game_resolve.yml (T1+T4 resolve — PRIMARY path)
20:30 UTC daily  — tss_daily_sync.yml (TSS cache build + upload to VPS)
```

---

## Key Constraints to Remember

1. Work wifi blocks Kalshi API — use any other network
2. No live capital until G6 — APR-0017: ≥66 resolved bets ✓ (82 now) + ≥5 game nights (3/5) + EXP-017 CONFIRMED + ADR-0005
3. nba_api is 403-blocked on VPS (Akamai WAF). Resolve path must use GHA or local Mac. VPS PIPE-03R finds 0 positions because GHA resolves first at 05:30 UTC.
4. T-155 / ADR amendment: formalize APR-0017 per-bucket evidence floor separation before G6 can be called (GG-018 RESOLVED but amendment still needed)

---

## ⚙️ DECISION AUDIT

Governance scan: clean — no `decisions_logged: false` documents found.

| Document | Decisions logged | DECISION_LOG entries written | Status |
|----------|-----------------|------------------------------|--------|
| `.github/workflows/post_game_resolve.yml` | N/A (not a strategy doc) | SESSION 44 GHA resolve entry | ✅ |
| `src/prediction_market_bot/run_t4_live.py` | N/A (code) | SESSION 44 stale-date fix entry | ✅ |
| `MEMORY_BANK.md` | N/A (index) | — | ✅ |
| `TODO_NEXT.md` | N/A (task list) | — | ✅ |

---

## Pending Tasks (Carry-Forward)

| Task | Priority | Notes |
|------|----------|-------|
| T-151: Verify Kalshi fee 0.07 against actual receipts | LOW — post-G6 | GG-020 open; 2 sources support 0.07; T-151 gated on live receipts |
| T-152: EXP-019B empirical (trajectory data) | MEDIUM — after G4+G5 | Requires `logs/t4_position_trajectories.jsonl` ≥3 game nights |
| T-153: EXP-019C spread model | MEDIUM — after G4+G5 | Requires `logs/spread_observations.jsonl` ≥3 game nights |
| T-154: Extract decisions from CHANGE_CONTROL.md | LOW | Governance debt; carry forward |
| T-155: APR-0017 per-bucket evidence floor amendment | HIGH — before G6 | Formalize GG-018 resolution as ADR amendment |
| EXP-018 DS decision post-G4 | HIGH — after G4 resolves | Hypothesis C: injury-filter view governs per SESSION 43 ruling; G4 data expands n and clarifies YES/NO asymmetry |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260610_0840Z.md. G4 game tonight (Jun 10 PDT, tips 5:30 PM PDT). Check if post-game resolve ran automatically — look at VPS paper_portfolio.json resolved count and GHA Actions run history for post_game_resolve.yml."
```
