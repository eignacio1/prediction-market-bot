# ADR-0037 — Correction: ADR-0036 Authorized Activation of the NBA T4 Engine, Not an MLB System

**Status:** ACCEPTED — DS sign-off (Earl Ignacio, 2026-07-01 SESSION 105)
**Registered by:** EL, flagged to DS via AskUserQuestion before any code was written for T-211
**Drafted:** 2026-07-01
**Accepted:** 2026-07-01 SESSION 105
**Supersedes:** ADR-0036's "Implementation Prerequisite," "Governance Impact," and "Tasks Registered" sections (T-211 specifically). Does not touch ADR-0029 (Tier A remains frozen).
**Vacates:** T-211 as originally scoped
**New governance gaps registered:** GG-061

---

## Context

ADR-0036 (SESSION 104, 2026-06-30) authorized "Phase 8 partial activation" for paper trading: `_PHASE8_ACTIVE = True` for T4-PROJ, T4-ARITH, T4-FLOW, and T4-BLOWOUT in `t4_execution_engine.py`, ruling that GG-038 and GG-039 were not valid paper-trading blockers and that GG-040 only blocks data-deficient sub-bands. Its data-availability table described these sub-bands' inputs as "in-game batter stats (H, AB, inning, batting slot)" sourced from "ESPN scoreboard + Kalshi polling" — MLB terminology, and (per the same session's framing) MLB is the only sport currently live.

Before writing the T-211 code, the target file was read in full. `t4_execution_engine.py` is not an MLB system. It is the **NBA** T4 sub-band engine built under ADR-0029 (SESSION 66–67, 2026-06-22), months before MLB T4 existed:

- `T4GameState` carries `quarter: int` (1–4, 5+ = overtime) and `time_remaining_min` — an NBA game clock, not innings.
- Every evaluator (`T4ProjEvaluator`, `T4ArithEvaluator`, `T4FlowEvaluator`) operates on `player.pts_so_far` against `spec.stat_type` defaulting to `"pts"` — points props, not hits.
- `GamePhase` classification thresholds (NEAR_CERTAIN ≥44min, LATE ≥36min, MID ≥24min elapsed) are derived from a 48-minute NBA regulation game.
- GG-039's own resolution text (written as part of ADR-0036) names `fetch_player_points_markets()` as the price-fetch function backing the "45s polling is sufficient" ruling — that function is NBA-only.
- GG-038's resolution cites T4FastHalt as built "in `t4_live_runner.py` SESSION 71" — `t4_live_runner.py` is the sole consumer of `t4_execution_engine.py` (along with `t4_price_cache.py`), and both are NBA-only per `CLAUDE.md`'s own band description ("T4 (NBA, PIPE-07)... Code: `run_t4_live.py`, `t4_live_runner.py`, `t4_price_cache.py`").
- `run_t4_mlb_live.py` — the actual, live, currently-accumulating MLB T4 runner — does not import `t4_execution_engine`, `T4ExecutionEngine`, or any `Evaluator` class anywhere. It has its own independent, non-sub-band decision path (single flat tree; see GG-046/T-203/T-204 history). No MLB equivalent of the ADR-0029 sub-band architecture exists in this codebase.

The conflation is not superficial. Every gap ADR-0036 ruled on — GG-038, GG-039, GG-040 — was analyzed against NBA code while described in MLB terms. The ADR is internally self-consistent in its narrative but factually wrong about which system it authorizes changes to.

**The conflict is corroborated by this same session's own governance record.** SESSION 104 also produced the standing operator directive tabling all NBA engineering until ~1 month before 2026-27 tip-off (`TODO_NEXT.md`, DECISION_LOG entry 2026-07-01), which explicitly lists `t4_live_runner.py` and `t4_price_cache.py` as files to stop and confirm before touching. ADR-0036, drafted the same day, instructs a code change to the file both of those modules depend on. Neither entry cross-referenced the other.

---

## Decision

**T-211 as scoped in ADR-0036 is vacated.** `_PHASE8_ACTIVE` in `t4_execution_engine.py` must not be set to `True` under ADR-0036's authorization. Doing so would activate the dormant NBA in-play engine — a live-trading-logic change to a tabled component, justified by an ADR whose stated rationale (MLB data availability) does not describe the code it targets. That NBA engine is currently a practical no-op only because NBA is off-season (0 active games); it is not an intentional or reviewed activation, and would become live the moment any NBA market existed, contrary to the tabling directive.

**No MLB sub-band system exists to activate instead.** GG-040's ruling that "T4-PROJ, T4-ARITH, T4-FLOW, T4-BLOWOUT are unblocked because ESPN + Kalshi polling data is sufficient" may well be *true as an abstract data-availability claim about MLB* — but there is no MLB code implementing those sub-bands for that ruling to attach to. Building one is a new architecture effort (new evaluator classes, wiring into `run_t4_mlb_live.py`, its own test suite, its own Phase 8 activation gate), not a flag flip, and is not authorized by this ADR. It is out of scope here and is not decided one way or the other by this correction — it would require its own ADR if pursued.

**GG-038 and GG-039's rulings are corrected to reflect that they describe the NBA runner.** The underlying technical claims (T4FastHalt exists in `t4_live_runner.py`; 45s polling feeds `fetch_player_points_markets()`) are accurate — but as statements about the NBA system, not as paper-trading exemptions applicable to any currently-active MLB work. Both gaps revert to their pre-ADR-0036 OPEN status with this correction noted.

**GG-040 is corrected to remove the false "PARTIALLY RESOLVED" status.** The sub-band data-sufficiency table in ADR-0036 was written against NBA field names it mislabeled as MLB; it does not describe any real MLB sub-band data check. GG-040 reverts to OPEN, unresolved, with a note that the true MLB-equivalent question (does ESPN + Kalshi polling suffice for hypothetical MLB batter/inning/flow sub-bands) has never actually been analyzed against MLB code — only asserted using MLB vocabulary layered over NBA logic.

---

## Why this happened (for the record, not as blame)

ADR-0036 was drafted in response to a legitimate strategic question — "are GG-038/039/040 real paper-trading blockers?" — and answered it by reading ADR-0029's sub-band architecture and `t4_execution_engine.py`'s code. At the time of drafting, MLB was the only sport under active discussion in the session, and the ADR's author described the data sources in the vocabulary of the system being discussed (MLB) rather than the system actually being read (NBA, per ADR-0029's original scope). No step in the ADR drafting or acceptance process included a check of the form "does this file's code actually reference the sport this ADR claims to be about" before authorizing a change to it.

---

## Governance Impact

1. **GG-061 (new)** — Process gap: ADR drafting did not verify that the target file/system matched the sport domain the ADR's rationale described, before authorizing a runtime flag change to it. Registered below.
2. **GG-038** — Reverts to OPEN, no paper-trading exemption. The exemption described a real fact (T4FastHalt exists) about the NBA runner; it does not apply to any current MLB work because there is no MLB system it would gate.
3. **GG-039** — Reverts to OPEN, no paper-trading exemption, same reasoning.
4. **GG-040** — Reverts to OPEN, "PARTIALLY RESOLVED" status removed. The sub-band data-sufficiency table was written against mislabeled NBA fields.
5. **T-211** — Vacated. Not reassigned. If a real MLB sub-band system is later desired, it requires a new task registered against a new ADR, scoped to code that actually exists.

---

## Tasks Registered

- **T-214**: Update `04_EXECUTION/TODO_NEXT.md` and `03_DECISIONS/GOVERNANCE_GAP_LOG.md` to reflect this correction (T-211 vacated, GG-038/039/040 reverted, GG-061 registered). Completed as part of this ADR's acceptance — see commit history.

No new build work is authorized or required by this ADR. It is a correction of an authorization error, not a design change.

---

## DS Sign-Off

DS sign-off (Earl Ignacio, 2026-07-01 SESSION 105) — confirmed via explicit choice to halt T-211 and correct ADR-0036 rather than proceed against the NBA engine or build a new MLB sub-band system.
