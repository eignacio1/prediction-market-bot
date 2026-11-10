# SESSION HANDOFF — W106.4 (B-018, MLB engine step 2: lineup-aware game model)

Status: DONE | B-018: step 2 delivered (ticket state is the strategic window's to set; ROLLING_BACKLOG.json not edited) | code: PR #449 merged (squash 8bab993), CI green on head 2ebece4 | results: docs-only push.

One-line result: lineup awareness moves the model a little against a constant (2024→2025 n=2,430: total +0.0024 Brier [+0.0008,+0.0041], run line +0.0028 [+0.0017,+0.0039], moneyline +0.0016 [+0.0000,+0.0032]) but does NOT beat Kalshi's closing line (2026, moneyline n=753: model−market Brier −0.0075 [−0.0121,−0.0029]; blend w=0.00 [0,0.30]; total rung n=735: −0.0031 [−0.0075,+0.0011], blend CV gain negative). The market is the bar; w≈0 is the result.

```
vision_pillar: DEPTH
gap_measure: D4 (MLB) - factor classes built point-in-time, scored held out vs naive and vs market
gap_delta: MLB factor classes point-in-time 0 -> 4 (starter, bullpen, lineup-vs-handedness, park); held-out vs naive: yes; vs market: yes (moneyline, total rung), run line vs market not scored. Source: 12_EXPLORATORY/mlb_engine/RESULT_W106_4.md, RESULTS_W106_4*.json
pattern_sweep: first CI run failed on new exploratory drivers writing without safe_out (test_exploratory_isolation); fixed in both new drivers; other exploratory scripts already route writes through _fence.safe_out.
surface_delta: none (no cron, service or workflow added; shadow research code only)
```

Stage per factor (ADR-0075): starter, bullpen, lineup-platoon, park = aggregated + interpreted + applied (tested path to a price, one NB run model prices ML/total/RL); not edge-bearing vs the market. Granularity index missing parts: rank vs history, market map.

Files: src/prediction_market_bot/mlb_engine/{lineup_aware,model_lineup,market_line}.py + 3 tests; 12_EXPLORATORY/mlb_engine/{run_w106_4,run_w106_4_market}.py, RESULTS_W106_4.json, RESULTS_W106_4_MARKET.json, RESULT_W106_4.md.

Not done / caveats: as-played lineups (late-scratch leak), no weather/umpire/injury/posted lineup, run line vs Kalshi unscored (KXMLBSPREAD semantics unverified), 58 market game-dates only. No future data waited on. Spring logging: Opening Day 2027; pre-registration committed before the first row (target first week of March 2027), shadow only.

Operator decisions: none.
