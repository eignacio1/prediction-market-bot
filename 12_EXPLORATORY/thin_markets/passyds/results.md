# KXNFLPASSYDS (W81.3 / W82.1) — results

Operator, 2026-10-16 08:18 PT: "Beating Kalshi or institutions is a tall task - beating buddy off his phone placing parlays, that's the first step." Pre-registration: `12_EXPLORATORY/THIN_MARKET_PREREGISTRATION_2026-10-20.md`.

## W82.1 Part A — read-backs (box, 2026-10-21)
- **Red cleared.** First `passyds_install.py install` REFUSED (budget RED: the job's own `STALE ... no write found` plus `healthcheck: UNHEALTHY: 1 fault`). The healthcheck fault was a transient `[FAIL] Kalshi DEMO API unreachable (2 tries)` in the 2026-10-20 17:00Z daily run; the summary line stays UNHEALTHY until the next daily run. Re-ran the healthcheck by hand as cron does -> `[OK] Kalshi DEMO API reachable`, `=== HEALTHY: 0 faults, 0 warning(s) ===`. Install then ran: `INSTALLED: W81.3 block appended; every prior crontab line preserved`; crontab read back (`2,22,42 * * * *` line, BEGIN/END markers).
- **First runs:** 05:02Z listed=137 in_slot=0 written=0; 05:22Z listed=145 in_slot=0 written=0 (no NFL game within 30 min / 2h, as expected on a Tuesday night). Log written -> STALE cleared.
- **Budget:** `thin_capture_install.budget()` on box @ HEAD 739f5b53: `GREEN`, reasons `[]`, 77 live / 0 stale / 0 unreviewed; health `HEALTHY: 0 faults, 0 warning(s)`; silent-arm line "NFL passing-yards pre-kickoff snapshot (W81.3): no games in the last 12h, nothing expected".
- **Model landed:** PR #306 (squash 3bca010), CI test job green on head 36c7bba and on main after merge. Box HEAD contains the merge. Deploy at 05:28:27Z `deployed` (t4-mlb pmbot-web-dashboard); no MLB game live then.
- **Box dry run** (`passyds_model.model_fields`, Drake Maye 249.5 strike, event KXNFLPASSYDS-26OCT22NECHI): `model_status=ok`, `model_p=0.46049`, mu 242.28, sha256 1053c843..., features qb_shrunk 247.29, opp_dev -2.71, n_prior_starts 33, injury Active, as-of dates all before 2026-10-21.

## Part B — NOT reached in this session (no pre-kickoff window has passed)
- Snapshot rows: none yet. Time vs kickoff, fillability-floor fields and model_p are therefore unread; the cell stays NOT_IMPLEMENTED (flips to SHADOW only after the frozen artifact AND a first valid row, `promote_cell_status(..., superseding_reference="W82.1")`).
- **First game that will write:** Thu 10-22 TNF NE @ CHI, `KXNFLPASSYDS-26OCT22NECHI`, kickoff ~2026-10-23T00:15Z; pre30 slot ~23:45Z, 2h slot ~22:15Z. Read back `exp_output/PREGAME_SHADOW_PASSYDS/snap_2026-10-23.jsonl` (day file keyed on snapshot UTC date) — check `secs_to_kickoff_est` / `kickoff_source` first (window error W24), then `floor_met`, depth fields, `model_p`.

## Frozen model sanity gate (reported, not a verdict)
Train 2019–2023 REG, held out 2024–2025 (1047 QB-games, 5235 strike rows). Brier model 0.20021 vs QB-season-average baseline 0.21886 (delta -0.01864). `sanity_report.json`. No market price enters the model.
