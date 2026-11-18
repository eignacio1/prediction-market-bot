# W57.2 handoff
Status: DONE | code PR #170 merged (bec2a75), CI success, Deploy success (t4-mlb restart not_needed) | docs commit follows on main.
Result: MLB settle built + run once on VPS (128 settled rows, T2/T3 only; T1 0), cron 11:41 UTC armed, GG-472 and GG-477 RESOLVED (GG-477 on n=1 clean night), GG-482 confirmed healthy.
Operator decide: (1) settlement source is cache scores, not Kalshi settlement (GG-440) - want a cross-check? (2) T1 cells settle 0 - check after next 11:41 run.
Details: 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W57_2_mlb_settle_results.md
