# Handoff W123.3 — H3 news latency (B-063). 2026-11-20
Rules read: first line of COMMON_RULES_W123.md "# Wave 123 common rules".
vision_pillar: PROOF — H3 verdict per event type; minutes-to-reprice distribution (median 0, p90 0 on every type).
Result: 12_EXPLORATORY/edge_location/h3_news/RESULT.md (+ results.json, PREREG.md frozen d698f99 before any price read, run_h3.py).
- NOT SUPPORTED (n>=30): NBA injury ruled-out / day-to-day / other, starter-set change. Still to come at +5 min 0.3-0.5c vs 1.9c cost.
- UNDERPOWERED: NBA lineup confirmation (n 6; needs 30, ~early Jan 2027 at current yield or denser Muse snapshots near tip); NFL inactives (n 14; needs 30, ~2 more full slates 11-29 / 12-06).
- Registry: H-EDGE-3 row in HYPOTHESIS_DOCTRINE.md updated (own row only).
directive_conflicts: none found in files touched.
pattern_sweep: n/a (analysis only). surface_delta: 0 (no cron, service or install). Read-only calls to Kalshi public trades from the laptop; no box task needed.
Data note: Muse snapshots (1.5MB) committed under h3_news/data; trade-print cache (30MB) is gitignored and re-fetches.
For the window:
- Pre-registered window ends at +30 min, which drops 54 of 60 NBA confirmations (Muse stamps ~30 min before tip). A snapshot near tip-60 would fix the yield.
- Muse has no NFL injury-report family; NFL injury news is a data limit.
- Next supportable test: same news on NBA prop / team-total markets (H1 overlap); needs its own pre-registration.
- Branch w123-3-h3-news in worktree PM-worktrees/w123-3; the untracked edge_location/ stub I made in the main tree was moved there.
PR: w123-3-h3-news (a .py under 12_EXPLORATORY needs green CI before merge).
