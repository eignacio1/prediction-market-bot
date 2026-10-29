# SESSION_HANDOFF W94.3 (flex lane: red first + fill cost)

```
vision_pillar: PLUMBING (Parts A/B), EXECUTION (Part C)
gap_measure: surface budget RED->GREEN; silent arms 1->0 (read 00:17Z); E3 markout 0->measured; taker-avoided share 0->measured
gap_delta: silent arms 1->0 (no code change; false positive, first-row lag); E3: resting-fill adverse markout measured NHL -11c (5-30m), MLB -9..-17c (W63.3), NBA/NFL ~0; taker drift within +-0.3c, spread cost ~2c (NHL 6c); post-fill markout explains 22% (T1) / 48% (T4) of the filled-vs-never-filled settlement gap
pattern_sweep: Part A found no defect in code; t4_mlb is the only live-only arm in silent_arms SPECS, others not exposed to the first-row lag. Part C: sweep of fill-cost analyses found W63.3 (MLB) and W81.1-B collector (NBA/NFL/NHL); no duplicate code.
surface_delta: none (read-only analysis, no live component)
stage per factor: fill cost = aggregated + interpreted, not applied
```

## Part A/B
Not a dead process: t4-mlb up since 2026-10-27 04:58Z, NRestarts=0. The silent-arm gauge fired at 00:04Z, before T4's first row (00:08:14Z; first-row lag is typically 8-16 min after a cached `:00` start). No code changed. RECOMMENDED to the window, NOT applied (barred: fix the cause, never the gauge): `start_grace_h=0.5` on t4_mlb only, with a regression test replaying 2026-10-29 00:04Z and a test that a GG-163-style outage still alarms. GG-1440 (nightly false RED) and GG-1441 (unexplained large lags: 2026-10-06 22:00Z 218 min, 10-12 21:00Z 106, 10-18 21:08Z 1620, 09-27 17:05Z 61; doubleheader/postponement vs outage unchecked) registered. Results: `12_EXPLORATORY/t4_mlb_silent/results_W94_3.md`.

## Part C
`12_EXPLORATORY/fill_markout/results_W94_3C.md` (PR #370). Verdict: "taker at the quote" does not carry the maker adverse markout; limits are seconds-scale latency (unmeasurable from 2-30 min archive), NHL YES depth (77% hold $1), untested stake scaling and trigger conditioning. No change to EXP-042/043 needed.

## Observed, not fixed
Live C5-PAPER `kalshi_order_failed` HTTP 400 `insufficient_balance` on the demo account; `market_type_defaulted` warnings. Relevant to execution evidence; unregistered here.
