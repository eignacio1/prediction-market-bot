# Session Handoff — 2026-06-24T23:00Z (SESSION 85)

**Trigger:** Session S85 — context window limit; compaction triggered mid-session-end; S86 completing the protocol and beginning T-190 build
**Last commit:** `aab7337` (main) — pushed to GitHub + VPS deployed

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** 1819/1819 passing (1 skip, 0 fail) — UNCHANGED from S84; S85 made no code changes
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — MLB cron PAUSED (all 4 MLB lines commented out, commit `aab7337`)
- **NBA cron:** ACTIVE (dark period, 0 bets expected — NBA off-season)
- **Paper bets:** 0/30 MLB resolved — G6 floor (MLB accumulation PAUSED until T-190 complete)
- **MLB portfolio:** $1,000.00 bankroll, 0 open, 0 closed — fresh start, NOT accumulating

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| **CLAUDE.md T4 line corrected** | `CLAUDE.md:53` said "T4/T5: In-play — future; post-G6." This was factually wrong and caused every session to conclude MLB T4 didn't need to be built. Fixed to 4-line accurate status: (1) NBA T4 PIPE-07 deployed; (2) MLB T4 NOT built; (3) ADR-0029 Tier A `t4_execution_engine.py` Phase 8 BLOCKED; (4) T5 not built. | DECISION_LOG.md [SESSION 85] | DS |
| **MLB cron PAUSED** | MLB arm has 3 missing components (pregame context, T3, T4). Running T1-only on an arm designed for T1+T3+T4 is structurally incomplete. All 4 MLB cron lines commented out with reason in `deploy/cron.conf`. Re-enable gate: T-190 Steps 1–3 complete and tested on VPS. | DECISION_LOG.md [SESSION 85] | DS |
| **T-190 registered — MLB arm completion in 3-step sequence** | Sequence fixed by dependency: pregame must exist before T3/T4 can run. Step 1: `run_mlb_pregame.py`. Step 2: `run_t3_mlb_pretip.py`. Step 3: `run_t4_mlb_live.py`. All 3 required before any MLB cron re-enabled. | DECISION_LOG.md [SESSION 85] | EL |
| **Accountability finding** | Asked "are we clean, green, on auto for MLB?" — answered yes without flagging MLB T4 as unbuilt. Root cause: CLAUDE.md documentation error. Now fixed. Standing rule: readiness verdict requires explicit band-by-band audit. | DECISION_LOG.md [SESSION 85] | DS |

---

## What Happened This Session

### Audit finding — MLB arm incomplete

**Monte Carlo simulation for June 26 slate (15 games):**
- ~1,231 quoted KXMLBHIT markets across 647 total
- Combined threshold: VIG_MEAN (0.1186) + MIN_EDGE (0.04) = 0.1586 above market mid
- Only ~0.2% of quoted markets clear → ~3.4 bets/night
- This is T1 only. T4 (which provides ~1,000 evals/game) is NOT built for MLB.

**Root cause trace:**
- `CLAUDE.md:53` read "T4/T5: In-play — future; post-G6"
- Every session loaded that line and concluded T4 was a future concern
- "MLB T4 not built" looked like the expected state, not a gap
- Fixed by rewriting CLAUDE.md with 4-line accurate T4 status

**Commits this session:** Only `aab7337` — CLAUDE.md T4 fix + MLB cron pause. No code changes.

---

## What Did NOT Change

- All 1819 tests: unchanged
- NBA paper trading (PIPE-03): unchanged — dark period
- NBA portfolio: halted at 25.12% drawdown kill switch
- Model artifacts: unchanged
- GG-004 (no demonstrated alpha): still OPEN

---

## Open Governance Gaps (OPEN as of S85)

- **GG-004 / T-177**: No demonstrated alpha vs Kalshi — requires MLB accumulation (EXP-017 n≥20 closed positions). MLB accumulation PAUSED until T-190 complete.
- **GG-042**: t=3 shadow gate DEFERRED — structural ceiling; indefinitely deferred
- All other gaps unchanged from S84 (see GOVERNANCE_GAP_LOG.md)

---

## One-Thing-Pending

**Build T-190 Step 1: `src/prediction_market_bot/run_mlb_pregame.py`** — the pregame context file generator. This is the prerequisite for both T3 and T4. Without it, neither PIPE-06 nor PIPE-07 MLB can run. NBA analog: `run_pregame.py` → `pregame_YYYYMMDD.json`.

---

## T-190 Build Spec (for next session)

### Step 1: `src/prediction_market_bot/run_mlb_pregame.py`
- Generates `logs/pregame_mlb_YYYYMMDD.json`
- Maps MLB players → T1 model forecasts → KXMLBHIT market tickers
- Reads: `exp_output/MLB/mlb_feature_matrix.csv`, `models/mlb_v1_model.joblib`
- NBA analog: `run_pregame.py` (reads `exp_output/nba_feature_matrix.csv` + `models/prod_model.joblib` → `pregame_YYYYMMDD.json`)
- Schedule: run at 22:00 UTC (1 hour before first MLB game window)
- Needs tests

### Step 2: `src/prediction_market_bot/run_t3_mlb_pretip.py` (PIPE-06 MLB)
- Reads `logs/pregame_mlb_YYYYMMDD.json`
- Polls Kalshi KXMLBHIT prices every 15 min before first pitch
- Computes CONFIRM/FADE/NEUTRAL per player
- Writes `logs/t3_mlb_YYYYMMDD_HHMM.json`
- cron: `*/15 20-23 * * *` and `*/15 0-3 * * *`
- NBA analog: `run_t3_pretip.py`
- Needs tests

### Step 3: `src/prediction_market_bot/run_t4_mlb_live.py` (PIPE-07 MLB)
- 45-second continuous evaluation loop during live MLB games
- ESPN MLB scoreboard: `site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard`
- Reads `logs/pregame_mlb_YYYYMMDD.json`
- Evaluates KXMLBHIT markets against live batter hit count
- Isolated portfolio: `logs/paper_portfolio_mlb_t4.json`
- Budget: pool × T4_BAND_WEIGHT=0.27 (ADR-0023)
- File-based kill switch: `logs/t4_mlb_kill_switch.flag`
- cron: `0 23 * * * timeout 21600`
- NBA analog: `run_t4_live.py` (+ `t4_live_runner.py`, `t4_price_cache.py`)
- Generates ~1,000 evaluations/game (CLAUDE.md Hard Rule 9)
- Needs tests

### After all 3 complete
1. Uncomment the 4 paused MLB cron lines in `deploy/cron.conf`
2. Deploy crontab to VPS
3. MLB accumulation restarts with $1,000 fresh bankroll

---

## Commit Message

```
[SESSION 85 CLOSE] MLB arm audit — CLAUDE.md T4 corrected, MLB cron paused, T-190 registered

- CLAUDE.md:53: "T4/T5: future/post-G6" corrected to 4-line accurate status
  (NBA T4 PIPE-07 deployed, MLB T4 NOT built, ADR-0029 Tier A Phase 8 BLOCKED, T5 not built)
- deploy/cron.conf: all 4 MLB cron lines commented out (PIPE-05, PIPE-05R, PIPE-05FX, PIPE-05C)
- T-190 registered: 3-step MLB arm build sequence (pregame → T3 → T4)
- Session governance: DECISION_LOG.md 4 entries, TODO_NEXT.md SESSION 85 block,
  MEMORY_BANK.md updated, PLAN.md updated
- Tests: 1819/1819 (no code changes this session)

Co-Authored-By: Claude Sonnet 4.6 (1M context) <noreply@anthropic.com>
```

---

## Resume Command for Next Session

```
NEXT SESSION PRIMER:
S85 CLOSED. T-190 is the ONLY task. MLB accumulation is PAUSED until all 3 MLB arm
components are built, tested, and deployed: (1) run_mlb_pregame.py → pregame_mlb_YYYYMMDD.json;
(2) run_t3_mlb_pretip.py (PIPE-06 MLB); (3) run_t4_mlb_live.py (PIPE-07 MLB, 45s loop,
~1000 evals/game). Build in sequence. NBA analog files for reference: run_pregame.py,
run_t3_pretip.py, run_t4_live.py. After all 3 complete: uncomment 4 MLB cron lines in
deploy/cron.conf, deploy to VPS, confirm MLB accumulation restarts.
```
