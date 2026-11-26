# EXP-NFLINPLAY-001 (EXP048) — Addendum W130.1: forward capture

**Date:** 2026-11-26. **Does not edit** the sha256-pinned pre-registration; it adds what the forward capture needs. Shadow only, no orders, Kelly 0.

1. **Frozen variances.** The runner (`scripts/run_nfl_inplay_shadow.py`) pins `S2_MARGIN_PM = 3.2717` and `S2_TOTAL_PM = 3.2161` points² per minute. These come from the prereg's fit set (2026 regular season, weeks 1-6, 93 FINAL games, "v2" refit in W129.6). The values were not committed at the time; this addendum records them. They do not change during the forward look.
2. **FLOW logs the identity.** `flow_adjustment` is the identity, so T4NFL-FLOW rows carry the same `p_yes` as T4NFL-ARITH with `mode="flow_identity"`. FLOW earns no separate verdict until it is a tested split.
3. **Team totals are an unvalidated extension.** Moneyline, spread and game total use the replayed pricer. Team total has no replay: mean = points so far + ((T ± M)/2)·tau/60 + own-drive expected points; variance = (s2m + s2t)/4·tau. Rows carry `mode="team_total_ext_unvalidated"` and are judged only after their own replay-vs-forward check.
4. **Pregame line.** M and T are read from ESPN `pickcenter[0]` and cached for games starting within 4 h. A game first seen in play is logged with `line_pre_kickoff: false` and is excluded from the judged set.
5. **Market comparison.** The replay compared only moneyline. Spread, total and team-total comparisons against Kalshi mid come from this forward capture (quotes `yes_bid_dollars` / `yes_ask_dollars`, cost = half spread each way).
6. **Feed lag.** `feed_lag_s` (fetch − play wallclock) and `state_to_quote_s` are logged per row; the Kalshi 3c-move lag is read in Part B beside the replay's 120 s.
7. **Judged n.** At >= 40 games and >= 300 priceable rows per cell (same rule as H-INPLAY-NHL-1). Overtime and stale-feed states are skipped and counted.
8. **Wording.** A losing look closes this hypothesis only: "hypothesis closed (EXP-NFLINPLAY-001, parked for R&D)".
