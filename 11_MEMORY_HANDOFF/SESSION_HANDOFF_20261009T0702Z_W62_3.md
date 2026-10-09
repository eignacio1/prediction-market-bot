# Session handoff: W62.3

Status: DONE | main @ 06d0b0c | PR #196 (Part A) + #200 (Part B), CI green, merged | GG-527 RESOLVED (gate proven in running t4-mlb after the single authorized restart); T1 MLB 85/485 orders filled, fills -$1.50/bet vs non-fills +$0.03/bet, both CIs span zero (GG-536); NBA flip check = not ready (0 rows), cron-removal script ready and untested live by design, NBA first-look release works with no src change | Operator decisions: (1) GG-536, what the T1 book may claim given only 17.5% of its orders fill; (2) run `python3 scripts/remove_nba_preseason_cron.py --apply` on the VPS at/after 2026-10-21 10:00 UTC (dry-run first); (3) from 2026-10-21 run `scripts/w59_3_nba_flip_check.py`.

Deploy decisions: PR #196 t4-mlb restart `not_needed`; PR #200 tests/docs only. Real sidecar `logs/t1_mlb_fill_status.jsonl` written on VPS (485 rows). Details: `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W62_3_gate_t1_fills_nba_results.md`.
