
## T-1050 · W83.1 · Weekly NFL source capture (STANDARD)
- The bot now saves five Sharp Football NFL tables (coverage, defensive tendencies, both line stats, offensive personnel) every Tuesday and Wednesday night. Each save is dated, so we keep the history the website itself throws away.
- First backfill is in: 32 teams per table, through Week 6.
- Muse card accuracy: all 22 rows we could compare matched the source. Pro Football Reference blocks automated fetches, and NGS only works in a browser, so neither is captured.
- The 82.3 re-test was not run. There is no 2026 per-game coverage data yet, so only descriptive numbers were reported.
- Two low-severity gaps were logged: GG-1000 (the PFR block) and GG-1001 (a new cron shows RED until its first write).
- Nothing needed from you.
