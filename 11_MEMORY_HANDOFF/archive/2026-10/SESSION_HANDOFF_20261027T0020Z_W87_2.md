<!-- session-meta
task_id: T-1173
tier: STANDARD
timestamp: 2026-10-27T00:25:00Z
commit: 360881a
one_line_summary: W87.2 PARTIAL: exposure gate fed by every order book and consulted on submit_order, LOG-ONLY on box; enforce flip pending.
gg_touched: GG-1082, GG-441
adr_touched: none
plan_deliverable_moved: no
vision_pillar: PLUMBING
gap_measure: PLUMBING (GG-1082/GG-441 kill-switch coverage of order-capable books)
gap_delta: books feeding gate 1 -> 2 live on box (MLB_T1, SHADOW; exposure_gate_state.json @ 2026-10-27T00:17Z); T4 pending restart
pattern_sweep: grepped submit_order/open_position/maybe_place callers: 3 PaperTrader paths, 5 shadow runners, 1 canary; all fed or noted
surface_delta: 0
-->

# Session Handoff — W87.2 (2026-10-27T00:25Z)

## Strategic Decisions
| Decision | Note |
|---|---|
| Gate ships LOG-ONLY; enforce via separate PR | per block spec |
| t4-mlb restart skipped (`skip_live_game`) | deploy log 00:13Z |

## State
PR #334 merged (360881a), CI green. Box state file shows MLB_T1 and SHADOW feeding, no breaches. `GATE_MODE="log"` (env `EXPOSURE_GATE_MODE`); `exposure_gate_logonly.jsonl` not yet created (no order since deploy). t4-mlb still runs old code, so MLB_T4 has no writer until restart.

## Pending (one thing)
Restart t4-mlb after games end; read the log after one full game day; flip to enforce in a separate PR; read back on box; then close GG-1082/GG-441.

## Assumptions to register
SHADOW uses a nominal $1000 denominator and open stake only; cancelled shadow orders count as open; Kalshi settled-status strings unverified; dashboard test order-dependent flake; local py3.9 lacks tomllib.

## Pattern sweep
Callers: run_paper_trade (frozen NBA, reported not summed), run_t4_mlb_live (feeds after restart), run_mlb_paper_trade (feeds), five shadow runners (feed), w65_2_cancel_canary (unmapped band, refused in enforce).

Not run this session: full CLAUDE.md Steps 1-4 and Q1-Q7.

Resume: `scripts/session_end_timer.sh` then read this file.
