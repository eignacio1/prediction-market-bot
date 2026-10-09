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

---

## NBA (EXP-038) — same procedure, different numbers (W62.3)

**Trigger.** Same cron (`49 13 * * *` UTC, `scripts/calibration_engine.py`). Looks are judged n = **150** then **400** settled *regular-season* games per cell (12 cells: moneyline/spread/game-total/team-total x T1/T2/T3). Preseason rows (`season_phase=preseason`, `excluded_from_judged_n`) never count. The regular season opens 2026-10-20, so no cell can be near 150 before ~late Dec; no NBA schedule is checked in, so cells show counts, not a projected date.

**Release behaviour (proven by `tests/test_w62_3_nba_release_rehearsal.py`).** Sealed at 149; at 150 the engine writes the frozen manifest `release_manifests/<cell>.look150.json`, `FIRST_LOOK_REPORT.md`, and the dashboard verdict. Later games never change look150. The 400 look writes its own manifest. Verdict set adds `UNRESOLVED` (EXP-038 s.5.2: CI still spans zero after n=400). The "or 2027-01-31" date trigger has no scoring rule, so it releases nothing (GG-529).

**Strategic window on release day.** As NFL: verify manifest digest + 150 games, other cells still sealed, read the REPORT without recomputing, log verdict in DECISION_LOG, plain-English result in ACTIVE_QUEUE. Cells are separate verdicts.

**Registry flip (before any of this).** From 2026-10-21 run `python3 scripts/w59_3_nba_flip_check.py` (read-only); it prints the `promote_cell_status` lines for cells holding a valid regular-season row. Then remove the preseason cron: `python3 scripts/remove_nba_preseason_cron.py` (dry run) and `--apply` only at/after 2026-10-21 10:00 UTC.
