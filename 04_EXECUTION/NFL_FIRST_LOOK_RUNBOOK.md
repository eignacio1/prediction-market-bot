# NFL first-look runbook (EXP-037) — one page

**Trigger.** Cron `49 13 * * *` UTC runs `scripts/calibration_engine.py` on the VPS (W58.3-CALIBRATION block). A cell unseals on the first run in which its judged n (settled NFL games) is >= 60. Projected: **2026-11-02 13:49 UTC** (all 12 cells at 15/60 on 2026-10-09; the 60th game lands on the 11-01 Sunday slate + 1 day settle lag). The date assumes 100% coverage: one missed game per cell moves it to ~11-09. Nothing for the operator to run.

**Outputs (VPS `/opt/prediction-market-bot/exp_output/CALIBRATION/`).**
- `engine_<UTC>.json` — every cell, daily; scores exist only on released cells.
- `release_manifests/<cell>.look60.json` — the frozen 60 games + sha256 digest; written once, never overwritten.
- `FIRST_LOOK_REPORT.md` — the readable report, released cells only (added W61.2).
- Live `/project` page (dashboard tunnel) → Calibration section: status JUDGED, Brier model/market, delta vs market with CI, and the verdict word. Within ~1 min of the run; the static Visual Dashboard.html only updates at session-end.

**Verdict lines (plain English).**
- **RULED_OUT** — model is measurably worse than the market (delta-Brier CI entirely below zero). Stop; this market type is not an edge.
- **SHADOW** — no proven difference (CI spans zero), or better but not profitable after fees. Keep logging; nothing changes.
- **CANDIDATE-PENDING-CAPACITY** — model beats the market with CI above zero and positive expected net under both fee cases. Still $0 stake: capacity and operator decision come first.
- A "model worse than climatology" flag is a separate model-failure note, not a decision rule.
- No verdict ever changes a cell's registry status or sizing (kelly stays 0.0, ADR-0048).

**Allowed after a look.** Read it; record it; add a dated addendum for FUTURE (not-yet-judged) data. **Not allowed:** relabel or reselect cells/games, change any model or parameter, change the bootstrap seed/B, edit the pre-registration, re-run with a different ordering, or score any still-sealed cell. A change needs a new dated pre-registration covering only data not yet judged.

**Strategic window on release day.** Verify the manifest (digest, 60 games) and that other cells stayed sealed; read the REPORT without recomputing; log the verdict in DECISION_LOG; write the plain-English result into ACTIVE_QUEUE for the operator; separate cells are separate verdicts (do not pool). Second look is n=150, same procedure.
