# Semantic Contracts Integration Patches

> **Record as of 2026-06-30** — a frozen, dated record, not a living document. It is not kept in step with the system; see `00_ADMIN/DOC_REGISTRY.toml`.

**ADR-0034 / GG-051 resolution**
**Written:** 2026-06-29 SESSION 100
**Module:** `src/prediction_market_bot/c7_monitoring/semantic_contracts.py`
**Terminal windows:** Apply all three patches to integrate the module into the running system.

---

## Why This Exists

`c7_semantic_contracts.py` is the Layer 3 governance module. It declares semantic
behavioral contracts for each pipeline stage and each execution band. It does not
run on its own — it must be wired into the three call sites where violations occur:

1. **PIPE-05 / PIPE-02** — after C1 data load, before C2 evaluation (SemanticFloorGuard)
2. **T4 MLB evaluation loop** — inside `_run_cycle()`, before `evaluate_forecast()` (ContaminationGuard)
3. **C7 SystemMonitor** — `check_and_alert()` and `get_health_snapshot()` (SemanticContractMonitor)

All three patches are surgical: they add import + call site. No existing logic is removed.

---

## Patch 1 — PIPE-05: SemanticFloorGuard at C1→C2 Boundary

**File:** `src/prediction_market_bot/run_mlb_paper_trade.py`

### Step 1.1 — Add import

After the existing imports block, add:

```python
from prediction_market_bot.c7_monitoring.semantic_contracts import (
    SemanticFloorGuard,
    SemanticFloorViolation,
)
```

### Step 1.2 — Find the data load + player-match boundary

Locate the section of `run_mlb_paper_trade.py` where:
- Games are fetched from the C1 data source (ESPN or StatsAPI)
- Players are matched to live Kalshi markets

This is typically the section that populates the list/dict of players-to-evaluate.
After that list is built and before the evaluation loop begins, insert:

```python
# --- Layer 3: Semantic floor guard (GG-051 / ADR-0034) ---
# Games were fetched from C1. If matched_players == 0, the pipeline is
# semantically dark: structurally sound, operationally invisible.
# Root cause of GG-049 (T1 MLB dark June 27-28).
n_games_fetched = len(games_today)   # adjust variable name to match local context
n_matched_players = len(player_contexts)  # adjust variable name to match local context
try:
    SemanticFloorGuard.assert_floor(
        pipeline_id="PIPE-05",
        games_fetched=n_games_fetched,
        matched_players=n_matched_players,
        sport="MLB",
    )
except SemanticFloorViolation as exc:
    logger.critical("SEMANTIC FLOOR VIOLATION — halting PIPE-05: %s", exc)
    audit.log(
        component="PIPE-05",
        event_type="semantic_floor_violation",
        payload={
            "pipeline_id": "PIPE-05",
            "sport": "MLB",
            "games_fetched": n_games_fetched,
            "matched_players": n_matched_players,
            "diagnosis": exc.diagnosis,
            "action_required": (
                "Pipeline dark. Check: (1) Kalshi ticker date format "
                "(PIPE-05 GG-047 fix), (2) player name normalization, "
                "(3) all markets already settled."
            ),
        },
        severity="CRITICAL",
        session_id=session_id,
        snapshot_id=SNAPSHOT_ID,
    )
    return   # halt pipeline; do not proceed to evaluation
# --- end Layer 3 floor guard ---
```

### Step 1.3 — (Optional) Add ba_l10 range check per player

Inside the player evaluation loop (after ba_l10 is loaded from pregame context):

```python
from prediction_market_bot.c7_monitoring.semantic_contracts import (
    SemanticFloorGuard,
    BandInvariantChecker,
)

# Inside player loop, after ba_l10 is assigned:
violation = SemanticFloorGuard.check_mlb_ba_range(
    ba_l10=ba_l10,
    player_id=player_id,
    pipeline_id="PIPE-05",
)
if violation is not None:
    audit.log(
        component="PIPE-05",
        event_type="semantic_contract_breach",
        payload={"violation_id": violation.violation_id, **violation.payload},
        severity="WARNING",
        session_id=session_id,
        snapshot_id=SNAPSHOT_ID,
    )
    # Do not skip — allow evaluation to proceed with a flag logged.
    # If ba_l10=0.0, the Binomial model returns p≈0; no edge generated; C4 rejects.
```

---

## Patch 2 — T4 MLB: ContaminationGuard in `_run_cycle()`

**File:** `src/prediction_market_bot/run_t4_mlb_live.py`

### Step 2.1 — Add import

```python
from prediction_market_bot.c7_monitoring.semantic_contracts import (
    ContaminationGuard,
    T4CorrDownwardViolation,
)
```

### Step 2.2 — Find the inner evaluation loop

Inside `_run_cycle()`, locate the inner loop over player/market combinations.
The critical section is the logic that currently reads:

```python
pm = live_prices.get(ticker)
if pm is None or not getattr(pm, "has_live_quotes", False):
    continue
mip = getattr(pm, "mid_price", 0.0)
if mip <= 0.0 or mip >= 1.0:
    continue
```

These are the existing guards. Immediately AFTER the existing `mip` guard, add:

```python
# --- Layer 3: ContaminationGuard (GG-051 / ADR-0034) ---
# Verifies data window coherence before evaluate_forecast() fires.
# Guards that already exist above (has_live_quotes, mip range) are
# necessary but not sufficient — they do not check game/player state.
player_in_live_game = player_id in active_player_ids  # set of player_ids in live boxscore
game_in_progress = (
    live_states.get(game_id, {}).get("status") == "STATUS_IN_PROGRESS"
    if hasattr(live_states.get(game_id, {}), "get")
    else getattr(live_states.get(game_id), "status", "") == "STATUS_IN_PROGRESS"
)
guard = ContaminationGuard(
    ticker=ticker,
    player_id=player_id,
    has_live_quotes=getattr(pm, "has_live_quotes", False),
    mip=mip,
    player_in_live_game=player_in_live_game,
    game_in_progress=game_in_progress,
    # T4-ARITH coherence check (pass if available):
    h_needed=h_needed if "h_needed" in dir() else None,
    ab_remaining=ab_remaining if "ab_remaining" in dir() else None,
    cycle_id=cycle_id,
    audit=audit,
    session_id=session_id,
    snapshot_id=SNAPSHOT_ID,
)
if not guard.is_clean():
    # contamination_halt already logged to C6 by guard
    continue
# --- end Layer 3 ContaminationGuard ---
```

**Note on `active_player_ids`:** This set should be assembled at the top of `_run_cycle()` from the live boxscore data (ESPN `athletes` array). If it's not currently assembled as a set, add:

```python
# Assemble set of player IDs in live game (for ContaminationGuard)
active_player_ids: set = set()
for game_state in live_states.values():
    athletes = getattr(game_state, "athletes", []) or []
    for a in athletes:
        pid = getattr(a, "athlete_id", None) or getattr(a, "id", None)
        if pid is not None:
            active_player_ids.add(int(pid) if isinstance(pid, str) and pid.isdigit() else pid)
```

### Step 2.3 — T4-CORR downward violation handling (when T4-CORR sub-band is activated)

If/when T4-CORR is activated (currently frozen per ADR-0029 Tier A), add this to the
correlation overlay section:

```python
try:
    corr_guard = ContaminationGuard(
        ticker=ticker,
        player_id=player_id,
        has_live_quotes=True,    # already verified above
        mip=mip,                 # already verified above
        player_in_live_game=True,  # already verified above
        game_in_progress=True,   # already verified above
        original_size=original_size_usd,
        adjusted_size=corr_adjusted_size_usd,
        cycle_id=cycle_id,
        audit=audit,
        session_id=session_id,
        snapshot_id=SNAPSHOT_ID,
    )
    # is_clean() raises T4CorrDownwardViolation if adjusted > original
    corr_guard.is_clean()
except T4CorrDownwardViolation as exc:
    logger.critical("T4-CORR DOWNWARD VIOLATION — triggering kill switch: %s", exc)
    audit.log(
        component="C7-SEMANTIC",
        event_type="semantic_corr_downward_violation",
        payload={
            "market_id": exc.market_id,
            "original_size": exc.original_size,
            "adjusted_size": exc.adjusted_size,
            "adr_ref": "ADR-0029 Principle 6",
        },
        severity="CRITICAL",
        session_id=session_id,
        snapshot_id=SNAPSHOT_ID,
    )
    # ADR-0029 Principle 6 breach — halt T4 band immediately
    fast_halt.halt(reason="T4CorrDownwardViolation_ADR0029_P6")
    break
```

---

## Patch 3 — C7 SystemMonitor Integration

**File:** `src/prediction_market_bot/c7_monitoring/monitor.py`

### Step 3.1 — Add import

At the top of monitor.py, after the existing imports:

```python
from prediction_market_bot.c7_monitoring.semantic_contracts import (
    SemanticContractMonitor,
    SemanticHealthState,
)
```

### Step 3.2 — Add SemanticContractMonitor to SystemMonitor.__init__

Inside `SystemMonitor.__init__()`, after the existing instance variable initializations:

```python
# Layer 3: Semantic contract monitor (ADR-0034 / GG-051)
self._semantic = SemanticContractMonitor(
    logger=self._logger,
    session_id=session_id,
    snapshot_id=snapshot_id or "SNAPSHOT-UNKNOWN",
)
```

### Step 3.3 — Expose semantic_monitor property

Add a property to SystemMonitor so pipeline components can record violations:

```python
@property
def semantic_monitor(self) -> SemanticContractMonitor:
    """Layer 3 semantic contract monitor. Callers record violations here."""
    return self._semantic
```

### Step 3.4 — Add semantic health to get_health_snapshot()

Inside `get_health_snapshot()` (or `get_drift_snapshot()` if that's the C8 feed method),
add the semantic health state to the returned dict/dataclass.

If `get_health_snapshot()` returns a dict:

```python
def get_health_snapshot(self) -> dict:
    snap = self.get_drift_snapshot()
    semantic_state = self._semantic.get_health_state()
    return {
        # ... existing fields ...
        "semantic_contract_status": {
            "n_floor_violations_session": semantic_state.n_floor_violations_session,
            "n_contamination_halts_session": semantic_state.n_contamination_halts_session,
            "n_band_invariant_breaches_session": semantic_state.n_band_invariant_breaches_session,
            "n_corr_downward_violations_session": semantic_state.n_corr_downward_violations_session,
            "is_semantically_dark": semantic_state.is_semantically_dark,
            "last_floor_violation_ts": semantic_state.last_floor_violation_ts,
            "last_contamination_halt_ts": semantic_state.last_contamination_halt_ts,
            "last_breach_band": semantic_state.last_breach_band,
            "computed_at": semantic_state.computed_at,
        },
    }
```

If `get_health_snapshot()` returns a dataclass, add these fields to the dataclass
definition and populate them in the same pattern.

### Step 3.5 — Periodic health snapshot emission

Inside `check_and_alert()`, add a call to emit a periodic semantic summary.
This is optional (the per-violation C6 events are sufficient for audit trail)
but provides a session-level trend view for C8:

```python
# At the end of check_and_alert(), after existing shadow model logic:

# Emit semantic health snapshot every 10 check_and_alert() calls (sampled)
if not hasattr(self, "_semantic_snapshot_counter"):
    self._semantic_snapshot_counter = 0
self._semantic_snapshot_counter += 1
if self._semantic_snapshot_counter % 10 == 0:
    self._semantic.emit_health_snapshot(session_id=sid)
```

---

## Patch 4 — PIPE-05 violation recording (connects SemanticFloorGuard to SemanticContractMonitor)

After catching `SemanticFloorViolation` in Patch 1, record it on the monitor:

```python
except SemanticFloorViolation as exc:
    logger.critical("SEMANTIC FLOOR VIOLATION — halting PIPE-05: %s", exc)
    # Record on C7 monitor for health snapshot
    if monitor is not None:
        monitor.semantic_monitor.record_floor_violation(exc)
    # ... rest of halt logic ...
```

After catching a contamination halt (inside `_run_cycle()`) for session tracking:

```python
if not guard.is_clean():
    # ContaminationGuard already logged to C6; update session counter
    if monitor is not None:
        monitor.semantic_monitor.record_contamination_halt(ticker=ticker, reason="contamination_halt")
    continue
```

---

## Patch 5 — `__init__.py` export (optional but recommended)

**File:** `src/prediction_market_bot/c7_monitoring/__init__.py`

Add the public API exports:

```python
from prediction_market_bot.c7_monitoring.semantic_contracts import (
    SemanticFloorViolation,
    SemanticFloorGuard,
    ContaminationGuard,
    BandInvariantChecker,
    SemanticContractMonitor,
    SemanticHealthState,
    T4CorrDownwardViolation,
    ContractViolation,
    ContractType,
)

__all__ = [
    # existing exports ...
    "SemanticFloorViolation",
    "SemanticFloorGuard",
    "ContaminationGuard",
    "BandInvariantChecker",
    "SemanticContractMonitor",
    "SemanticHealthState",
    "T4CorrDownwardViolation",
    "ContractViolation",
    "ContractType",
]
```

---

## Test coverage requirements

Add tests to the test suite for:

1. **SemanticFloorGuard.assert_floor():**
   - games_fetched=0 → no raise (idle pipeline is not a violation)
   - games_fetched=5, matched_players=0 → raises SemanticFloorViolation
   - games_fetched=5, matched_players=3 → no raise
   - games_fetched=5, matched_players=1, min_match_rate=0.5 → raises (1/5=20% < 50%)

2. **ContaminationGuard.is_clean():**
   - has_live_quotes=False → returns False
   - mip=0.0 → returns False
   - mip=1.0 → returns False
   - player_not_in_live_game → returns False
   - game_not_in_progress → returns False
   - elapsed_min >= game_regulation_min → returns False
   - h_needed=3, ab_remaining=2 → returns False (impossible)
   - ab_remaining=0, h_needed=1 → returns False
   - all clean → returns True
   - original_size=10.0, adjusted_size=12.0 → raises T4CorrDownwardViolation

3. **BandInvariantChecker checks:**
   - threshold=0 → ContractViolation (below min)
   - threshold=4 → ContractViolation (above max)
   - threshold=2 → None (clean)
   - ba_l10=0.0 → ContractViolation
   - ba_l10=0.30 → None (clean)
   - score_diff=65 → ContractViolation
   - score_diff=42 → None (clean)

4. **SemanticContractMonitor:**
   - record_floor_violation() increments counter + sets is_semantically_dark
   - record_contamination_halt() increments counter
   - get_health_state() returns copy (not reference)
   - record_corr_downward_violation() emits CRITICAL C6 event

---

## Deployment sequence

1. Run existing test suite (must be green before patch)
2. Apply Patch 5 (`__init__.py`) — no behavior change
3. Apply Patch 3 (monitor.py) — extends C7 with semantic monitor
4. Apply Patch 1 (PIPE-05) — wires floor guard into T1 MLB pipeline
5. Apply Patch 2 (T4 MLB) — wires contamination guard into T4 evaluation loop
6. Write new tests per requirements above
7. Run full test suite
8. Deploy to VPS
9. Verify: next T1 MLB cron run should emit `semantic_floor_violation` at CRITICAL
   if 0 matched; should not emit if healthy. Check audit.jsonl.

---

## Expected behavior in production

**Healthy run (T1 MLB, morning cron):**
- `SemanticFloorGuard.assert_floor()` passes silently (no C6 event for clean)
- No `semantic_floor_violation` in audit.jsonl
- Health snapshot shows `n_floor_violations_session=0`, `is_semantically_dark=False`

**Dark pipeline (GG-049 pattern replay):**
- `SemanticFloorGuard.assert_floor()` raises SemanticFloorViolation
- `semantic_floor_violation` CRITICAL event in audit.jsonl within 1 second of data load
- Pipeline halts before evaluation loop
- Health snapshot shows `n_floor_violations_session=1`, `is_semantically_dark=True`
- Step 4 (operational heartbeat) confirms 0 bets — consistent with Layer 3 alert
- Operator sees both signals before next session

**T4 contamination (stale price window):**
- ContaminationGuard.is_clean() returns False for that one evaluation
- `contamination_halt` WARNING in audit.jsonl for that ticker
- Evaluation skipped; cycle continues to next player/market
- Health snapshot shows `n_contamination_halts_session` incrementing

**T4-CORR downward violation (ADR-0029 Principle 6):**
- ContaminationGuard raises T4CorrDownwardViolation
- T4 fast_halt triggered
- `semantic_corr_downward_violation` CRITICAL in audit.jsonl
- C7 system kill switch cascade (T4FastHalt → SystemMonitor.trigger_kill_switch())
