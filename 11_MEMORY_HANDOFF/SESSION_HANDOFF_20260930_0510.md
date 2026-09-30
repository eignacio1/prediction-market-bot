# Session Handoff — 2026-09-30T05:10Z

<!-- session-meta
task_id: T-593
tier: STANDARD
timestamp: 2026-09-30T05:10:00Z
commit: 8554e12
one_line_summary: T-593: NFL ingestion now retains weather/QB/coach/referee + sacks/QB-hits/penalties (opt-in, allowlist); 2026 captured; no model wiring.
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
-->

**Trigger:** task complete. **Last commit:** `8554e12` on `session/20260930T050102Z-nfl-ingestion-widen` (pushed, NOT merged).

## Status
- **Tests:** 103 NFL tests pass (4 new). Full suite not run this session.
- **Capital:** none — paper only. Paper bet count not re-checked this close-out.

## Strategic Decisions This Session
| Decision | Rationale | Reference | Owner |
|---|---|---|---|
| Extended fields are opt-in (`include_extended`), core column lists untouched | `data_contracts.py` mirrors core lists and is not owned here | `T593_nfl_ingestion_widen.md` | DS |

DECISION_LOG/GGL not written (brief: 41.1 owns them) — 41.1 should log the row above.

## What changed
- `nfl_ingestion.py`: extended allowlist + `capture_extended()` (append-only, provenance manifest); tests in `tests/test_t593_nfl_extended_capture.py`.
- Live 2026 capture: 272 schedule rows, 96 team-stat rows; manifest in `exp_output/NFL/INGESTION_CAPTURE/`.
- Unrecoverable: pre-kickoff point-in-time QB/weather/referee for wks 1–3. 2014–2025 history not pulled (operator call).

## One thing pending
Merge the branch (src/ changed → PR path) and decide on a pre-kickoff recurring capture (nothing scheduled here).

## Resume
`git fetch && git log origin/session/20260930T050102Z-nfl-ingestion-widen`; read `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T593_nfl_ingestion_widen.md`.
