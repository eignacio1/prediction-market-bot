# SESSION_HANDOFF 2026-11-03T01:00Z — W97.1 (engine lane, NBA v3)
task_id: W97.1 (B-001 + B-009)
vision_pillar: DEPTH + PROOF
gap_measure: D4/D5 (NBA engine arms with rows; v3 frozen), P1
gap_delta: v3 frozen+merged 0→1 (EXP-044c, PR #391); v1, v2 rows verified 2 arms OK on 6/6 games (box read 20261103T0052Z); v3 installed 0→0 (install refused); points: engine_set measured, loses (+0.0131 Brier [+0.0106,+0.0158]), no EXP-044d
pattern_sweep: build_frozen_v3.py and study_partc_w97.py write via safe_out; study_partc_w97 first joined its csv path to HERE rather than HERE.parent (doubled dir) — fixed; freeze_v3.py, study_v3_lead60.py, factors_frame.py, study_v3.py already use safe_out
surface_delta: +1 cron line registered (nba_engine_live_v3), NOT installed; +1 silent-arm spec (additive); 0 live components added

Status: PARTIAL | B-001: v3 built+frozen+merged, NOT live (install refused; GG-1450 open) | B-009: DONE, no win — EXP-044d not frozen
Branches/PRs: #391 merged `4e5cfd65` (CI green); #395 `session/w97-1-partc-points-availability` (Part C module+study; CI result in PR)
MEASURE MOVED: NBA engine arms with rows 2 (v1, v2 — unchanged by this block, verified); v3 frozen 0→1 (source: EXP044C pre-reg, box silent_arms_read 20261103)
Operator decisions: (1) install `nba_engine_v3_cron_install` then `nba_engine_v3_cron_readback` — refused by the auto-mode classifier as a Production Deploy; permit it or run it. Recommendation: install; health is HEALTHY.
Carry-forward: v1 events 56 vs v2 77; two `Killed` lines in the readback (memory) — need a box task reading per-game rows and memory.
Details: 12_EXPLORATORY/nba_engine_v3/results_W97_1.md
