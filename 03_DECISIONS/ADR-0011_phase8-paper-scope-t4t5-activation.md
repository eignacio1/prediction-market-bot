# ADR-0011 — Phase 8 Paper Prototype: T4/T5 Activation Scope

**Status:** ACCEPTED — 2026-06-02
**Decision makers:** DS (Earl Ignacio)
**Supersedes:** —
**Superseded by:** ADR-0012 (Phase 8 production-grade infra — when written)
**Related:** ADR-0006 (risk framework), ADR-0010 (band Kelly hierarchy), ADR-0009 (shadow model)
**Motivation:** Activate T4/T5 paper prototype before NBA Finals G2 (Jun 5, 2026) to generate empirical in-play evidence before the dark period.

---

## Context

ADR-0010 authorized code changes for T4/T5 Kelly fractions and established the Phase 8 gate. The operator's strategic goal is to see the bot "at optimum" (T1+T4+T5 active) during the NBA Finals window before the NBA dark period (~Jun 22 – Oct 2026). This requires activating T4/T5 at paper scale on VPS 157.230.91.33 before Finals G2.

Three blockers existed for Phase 8 production activation:
1. DS-02 real-time game state feed (source not selected — latency + cost ADR)
2. Kill switch redesign (<5s SLA — NFR-03 supersession ADR)
3. Phase 8 infrastructure ADR (VPS hardware, process isolation, monitoring)

This ADR resolves blocker 3 for **paper prototype scope only**. Blockers 1 and 2 are explicitly deferred as SKELETON components. Production-grade activation (live capital, <5s SLA) requires a superseding ADR that addresses all three blockers.

---

## Decision

**Activate T4/T5 as a paper prototype for the Finals window, with the following explicit scope boundaries:**

### 1. DS-02: NBA Stats API polling (NOT real-time)

**Selected:** `nba_api.live.nba.endpoints.boxscore` CDN polling at 45-second intervals.

**Rationale:**
- NBA Stats CDN updates every ~30s; 45s polling interval gives 1-2 update lag
- Zero cost (public CDN); no API key required
- Acceptable for paper trading where execution fidelity is not the test — decision architecture is
- Data structure verified: `game.period`, `game.gameClock` (ISO 8601), `game.homeTeam/awayTeam.players[].statistics.points`

**Explicit NOT in scope for this ADR:**
- Real-time WebSocket stream (e.g., SportsData.io, ESPN)
- Sub-30s latency guarantee
- Retry backoff / dead-letter queue for failed polls
- Rate-limit management beyond nba_api defaults

This DS-02 implementation is a PAPER-ONLY component. It is not suitable for live capital execution. The production DS-02 decision (real-time vs. polling, vendor selection, latency SLA) is deferred to the Phase 8 production ADR.

### 2. Kill switch: file-based flag (NOT C7 integrated)

**Selected:** File flag at `logs/t4_kill_switch.flag`.
- Arm: `touch logs/t4_kill_switch.flag`
- Disarm: `rm logs/t4_kill_switch.flag`
- Response time: <1ms (stat call)

**Rationale:**
- Sufficient for paper prototype: operator can arm in <2s from terminal
- Does not require C7 MonitorAgent integration or new process architecture
- File stat is the fastest possible check that survives process restarts
- NFR-03 (≤60s kill switch) is satisfied at paper scale (operator can arm manually in <60s)

**Explicit NOT in scope for this ADR:**
- C7 MonitorAgent in-memory state integration (<5s SLA)
- Automated kill on drawdown detection from T4/T5 loop
- Cross-process kill coordination

NFR-03 gap: at paper scale, operator manual intervention satisfies the 60s SLA. At live capital scale, the automated sub-60s kill requirement requires C7 integration — this is a Phase 8 production ADR blocker and must be addressed before T4/T5 can handle live capital.

### 3. Infrastructure: single-process polling on existing VPS

**Selected:** Run T4 polling loop in a separate terminal/screen session on VPS 157.230.91.33. No new process isolation, no systemd service, no hardware changes.

**Activation procedure:**
```bash
# On VPS 157.230.91.33
screen -S t4_loop   # or tmux
cd /opt/prediction-market-bot
source .env
BOT_ENV=paper PYTHONPATH=src python3 \
    src/prediction_market_bot/c1_signal_ingestion/ds02_nba_live.py \
    --game-id <GAME_ID> \
    --cohort-ids <IDS...> \
    --poll-sec 45

# Separate terminal for T4 event loop (when wired)
# Kill switch: touch logs/t4_kill_switch.flag
```

**Rationale:**
- Paper prototype requires zero infrastructure investment beyond existing VPS
- Single-process is sufficient; no concurrent paper bets can cause financial harm
- Systemd service + process monitoring is production infrastructure — deferred

### 4. Capital exposure: paper only

T4/T5 activates in `BOT_ENV=paper` mode exclusively. No live capital until:
- G6 gate formally cleared (30 resolved paper bets with positive P&L)
- Phase 8 production ADR signed (all three blockers resolved)
- ADR-0005 (live capital authorization) accepted

RESERVE_MANDATE_PCT = 0.40 (from ADR-0010): ≥40% bankroll uncommitted after T1 batch. Warning-only at paper scale — logged to C6 but does not halt execution.

### 5. EXP-018 and EXP-019 gate for T4/T5 ACTIVE (live capital)

Before T4/T5 can be designated ACTIVE (live capital) rather than SKELETON:
- **EXP-018:** Calibrate T4_MIN_DELTA_P by game phase. Current 0.08 is phase-appropriate only for late Q4 (min 44+); too lenient for Q4 entry (min 40-42 noise floor 2σ = 0.10-0.15). Phase-dependent thresholds required (tentative: 0.10 for min 36-40, 0.08 for 40-44, 0.05 for 44+).
- **EXP-019:** Validate T5 certainty thresholds against live paper data. Current 0.85/0.15 are Poisson-grounded but unvalidated against actual late-game market behavior.
- **T-128:** DS-02 ADR requiring live pace data and real-time feed selection.

---

## Options Considered

| Option | Description | Decision |
|--------|-------------|----------|
| **A — Paper prototype (chosen)** | NBA Stats API polling, file kill switch, existing VPS, paper capital | ACCEPTED |
| B — Full Phase 8 production build | Real-time stream, C7-integrated kill switch, systemd service, process isolation | Rejected — 2-3 day build; Finals G2 deadline is Jun 5; paper prototype provides the evidence needed |
| C — Defer T4/T5 to dark period | No in-play activation until 2026-10 season open | Rejected — misses the strategic goal of seeing the bot "at optimum" in the Finals window before dark period |
| D — Synthetic demo only | Run T4 demo with synthetic events; no live DS-02 | Rejected — no empirical evidence; defeats the purpose |

---

## Consequences

**Positive:**
- T4/T5 paper prototype active before Finals G2 (Jun 5)
- Empirical evidence on in-play decision architecture before dark period
- EXP-018/EXP-019 data collection begins immediately
- Zero additional infrastructure cost

**Negative / Trade-offs:**
- 30-60s data lag: T4 signals are delayed by poll cadence + CDN update latency. Paper bets will not reflect real-time market prices. This is acceptable for paper validation; not acceptable for live capital execution.
- No automated kill: operator must manually arm kill switch. Acceptable at paper scale; not acceptable at live capital scale.
- No process isolation: T4 polling loop crash requires manual restart. No financial harm at paper scale.
- T4 Kelly = 0.20 is aggressive for a first activation. Reserve mandate (40% bankroll) mitigates this by capping T1 deployment.

**Neutral:**
- This ADR does not change the G6 gate criteria (paper bets from T1 only count toward the 30-bet floor; T4/T5 paper bets provide architecture validation but are not counted separately in G6).
- ADR-0010 Kelly fractions and thresholds apply as specified.

---

## Scope Boundary (explicit)

| Component | This ADR (paper scope) | Phase 8 production ADR (future) |
|-----------|----------------------|--------------------------------|
| DS-02 | NBA Stats API polling, 45s interval | Real-time stream, <30s SLA, vendor ADR |
| Kill switch | File flag, operator-manual | C7 MonitorAgent in-memory, <5s automated |
| Infrastructure | screen/tmux session, existing VPS | systemd service, process isolation, monitoring |
| Capital | Paper only (BOT_ENV=paper) | Live capital after ADR-0005 |
| EXP gate | EXP-018/EXP-019 data collection begins | EXP-018/EXP-019 completed and thresholds calibrated |

---

## Implementation

| Task | Description | Status |
|------|-------------|--------|
| T-129 | Path B Poisson CDF fix in run_paper_trade.py | Done — Session 14 |
| DS-02 adapter | ds02_nba_live.py in c1_signal_ingestion | Done — Session 14 |
| Kill switch | File-based flag in run_t4_inplay._kill_switch_armed | Done — Session 14 |
| ADR-0011 | This ADR | Done — Session 14 |
| Paper portfolio reset | Reset paper_portfolio.json to $1,000 on VPS | Pending — Session 14 |
| VPS deploy | git push + VPS git pull + verify | Pending — Session 14 |
| EXP-018 | T4_MIN_DELTA_P calibration by game phase | Dark period |
| EXP-019 | T5 certainty threshold validation | Dark period |
| T-128 | DS-02 production ADR (real-time stream) | Dark period |

---

## DS sign-off

**Earl Ignacio — ACCEPTED**
**Date: 2026-06-02**

This ADR authorizes T4/T5 activation at paper prototype scope for the NBA Finals window. It does NOT authorize live capital. The paper prototype framing (30-60s lag, file kill switch, no process isolation) is an explicit design choice for speed-to-evidence, not an architectural compromise of the production system.
