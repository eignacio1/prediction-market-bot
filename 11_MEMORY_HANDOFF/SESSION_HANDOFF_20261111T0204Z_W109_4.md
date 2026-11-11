# SESSION HANDOFF - W109.4 (B-064) props net of costs

vision_pillar: PROOF
gap_measure: P2 (verdicts issued) / prop families measured net
gap_delta: prop families measured net 0 of 3 sports (108.3) -> 3 of 3 sports, 25 of 25 series costed; 22 testable sport x band cells, 0 net-positive after Holm/BH (source: 12_EXPLORATORY/quant_w108_props/net_results.json, 2026-11-11)
surface_delta: none (read-only research; no live component)
pattern_sweep: batch /markets/candlesticks returns empty for pre-cutoff settled markets (use /historical/markets/{ticker}/candlesticks). Same call remains in 12_EXPLORATORY/quant_w108_props/fetch_candles.py.txt (108.3, superseded) and 12_EXPLORATORY/quant_w109_props/fetch_markets.py (another block's file; NOT edited - owner should check it for settled markets older than the live cutoff). Not yet registered as a GG number.

Status: PARTIAL. PR #472 merged (CI green), squash 6a56768.
Result: NBA/NFL props NOT shown mispriced after costs; NHL underpowered. No pre-registration written.
Limits: ~3-5% sample; no tip-off in API so leads are hours before close (5/8/12h), not T-60/30/5 min; NHL FIRSTGOAL has almost no early quotes.
Cost-per-family table for 109.3: RESULT.md (W109.4 section). Operator decisions: none.
