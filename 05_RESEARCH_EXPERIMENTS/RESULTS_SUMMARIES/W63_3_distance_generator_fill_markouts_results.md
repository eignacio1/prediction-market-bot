# W63.3 — Distance table computed + why our fills lose

Status: Part A merged (PR #202) and run on VPS; Part B analysed (PR #203). Demo-venue GETs only; nothing built or enabled.

## Part A — computed distance table (VPS, 2026-10-09T16:18Z, generator at aff51b12 + D1 manifest fix)

```
aff51b12 W63.3 Part A: distance-to-optimum generator, governance-scan + /project panel, required gap keys (#202)
DISTANCE TO OPTIMUM — computed 2026-10-09T16:18:56Z (alarm-only; values only from sources, never typed)
  B1  37 / 104
      source: src/prediction_market_bot/c5_execution/market_type_registry.py · as of 2026-10-09T15:53:41Z
  B2  12 / 18
      source: src/prediction_market_bot/c5_execution/market_type_registry.py · as of 2026-10-09T15:53:41Z
  B3  4 of 5 (missing: T5)
      source: src/prediction_market_bot/c5_execution/market_type_registry.py · as of 2026-10-09T15:53:41Z
  B4  1 · 0
      source: src/prediction_market_bot/c5_execution/market_type_registry.py · as of 2026-10-09T15:53:41Z
  D1  mlb_player_hits_t1: personnel, team, venue; mlb_game_pregame_v1: personnel, team; nfl_pregame_v1: team; nhl_pregame_v1: personnel, team, venue; nba_pregame_v1: team. Classes no live model conditions on: matchup, weather, qualitative
      source: scripts/distance_to_optimum_d1_manifest.json + model metadata · as of 2026-10-07T02:00:41Z
  D2  18 (mlb_player_hits_t1, 0 qualitative)
      source: models/mlb_v1_model_meta.json · as of 2026-06-24T19:11:31Z
  D3  0 (no PROPOSED/ACCEPTED challenger pre-registration found)
      source: 12_EXPLORATORY/ + 03_DECISIONS/ (*challenger*.md with Status PROPOSED|ACCEPTED) · as of 2026-10-09T16:18:48Z
  E1  t4_mlb: 166 / 4237 = 3.9% · t1_mlb: 85 / 485 = 17.5%
      source: logs/paper_portfolio_mlb_t4.json + logs/t4_mlb_fill_status.jsonl; logs/paper_portfolio_mlb.json + logs/t1_mlb_fill_status.jsonl · as of 2026-10-09T06:50:48Z
  E2  t4_mlb: $-0.26 (n=166, 66 games, 95% CI [-0.45, -0.07]; ledger-priced, not fill-priced) · t1_mlb: $-1.50 (n=83, 57 games, 95% CI [-3.67, 0.63]; ledger-priced, not fill-priced)
      source: logs/paper_portfolio_mlb_t4.json + logs/t4_mlb_fill_status.jsonl; logs/paper_portfolio_mlb.json + logs/t1_mlb_fill_status.jsonl · as of 2026-10-09T06:50:48Z
  E3  t4_mlb: fills 24.1% (n=166) vs non-fills 48.7% (n=4054) · t1_mlb: fills 28.9% (n=83) vs non-fills 52.1% (n=386)
      source: logs/paper_portfolio_mlb_t4.json + logs/t4_mlb_fill_status.jsonl; logs/paper_portfolio_mlb.json + logs/t1_mlb_fill_status.jsonl · as of 2026-10-09T06:50:48Z
  P1  0 / 45
      source: exp_output/CALIBRATION/engine_20261009T134917Z.json · as of 2026-10-09T13:49:01Z
  P2  0
      source: exp_output/CALIBRATION/engine_20261009T134917Z.json · as of 2026-10-09T13:49:01Z
  P3  2026-11-02 (12 cell(s), e.g. NFL_NFL_GAME_TOTAL_T1); modal outcome UNAVAILABLE (12_EXPLORATORY/NFL_FIRST_LOOK_EXPECTATIONS.md missing or unparseable)
      source: exp_output/CALIBRATION/engine_20261009T134917Z.json · as of 2026-10-09T13:49:01Z
```

### Differences from the hand table in ACTIVE_QUEUE.md (findings)
| Measure | Hand table | Computed | Why |
|---|---|---|---|
| B1 | 25 / 104 | 37 / 104 | hand table predates the 12 MLB postseason cells (W63.1) |
| B2 | 8 / 18 | 12 / 18 | same |
| D2 | 14 | 18 | hand value was stale vs model metadata (`models/mlb_v1_model_meta.json`) |
| P1 | 0 / 25 | 0 / 45 | calibration engine now counts 45 cells |
| D1 | typed | ERROR on first VPS run (`ops_l10`, `team_id` unclassifiable) | fixed: both added to manifest team class; now clean |
| P3 modal outcome | typed | UNAVAILABLE | `12_EXPLORATORY/NFL_FIRST_LOOK_EXPECTATIONS.md` missing on VPS (Wave 63.2 file not synced); date 2026-11-02 computed |

Also in Part A: governance_scan prints the table (alarm-only); `/project` shows a Distance section (stacked, checked at 390px); `gap_measure`/`gap_delta` required for handoffs timestamped after 2026-10-09T07:24:13Z, older handoffs parse (7 tests).

## Part B — why our fills lose

Method: all 251 CONFIRMED_FILLED positions (T1 MLB 85, T4 MLB 166) plus never-filled orders (ledger-derived limit = held-side mid floored to the cent; order GETs 404 for 301 of 551 sampled, so most never-filled rows are ledger-derived; ledger vs order limit matched 1 of 2 checked). Markouts from demo 1-minute candles, two-sided mid only. 95% CIs game-clustered, 4,000 resamples. NO side uses 1 − yes.

### Result
| | T1 MLB filled | T1 not filled | T4 filled | T4 not filled |
|---|---|---|---|---|
| n | 85 | 346 | 166 | 4,042 |
| Settled win rate | 28.2% [18.7, 38.0] | 50.6% [44.6, 56.5] | 24.1% [14.1, 34.7] | 48.7% [46.3, 51.1] |
| Settle − price | −0.386 [−0.485, −0.284] | +0.068 [+0.004, +0.131] | −0.250 [−0.373, −0.115] | +0.101 [+0.074, +0.127] |
| Median secs to fill | 5,873 | — | 2,276 | — |
| Taker share | 3.5% | — | 24.1% | — |

Markout after fill (mid − fill price, held side): T1 −0.09 / −0.12 / −0.10 (1/5/30 min); T4 −0.17 / −0.17 / −0.17. All CIs exclude 0. Markout from submit for filled orders: ≈0 (T1 +0.02/−0.02/−0.07; T4 +0.01/−0.01/−0.05) — the loss accrues between submit and fill.

Immediate vs resting (T4): fills ≤60 s win 35.3% (n=51, CI [10.8, 52.8]), settle−price −0.07 [−0.40, +0.15]; fills >60 s win 19.1% (n=115), −0.33 [−0.41, −0.24]. T1 immediate (n=17) win 23.5%, no better.

Quote-relative: limit sits 0.27 (T1) / 0.34 (T4 filled) / 0.54 (T4 not filled) below the ask; ledger mid is 0.12–0.16 below venue mid on the few two-sided rows (T1 n=6, T4 n=13).

### Verdict (plain English)
Our resting orders fill mostly when the market moves against us. The orders that fill win about a quarter of the time; the identical-model orders that never fill win about half. Orders sit in the book for 40–100 minutes at the model's mid, and the venue's book is often far from that price, so a fill means someone with better information (or a price move) hit a stale quote: **adverse selection compounded by stale pricing**. It is not a latency effect and not clearly a take-vs-make effect. This is the winner's-curse pattern, and it is consistent with E3 (fills 24.1% vs non-fills 48.7%).

Rule supported by the evidence: **cancel after N seconds (N ≈ 60) with price anchored to the live venue book**, not to the model mid. Take-vs-make is not decidable from this data.

### Caveats
- Demo book is thin and often one-sided; mid-based measures cover few rows. Settlement-based comparisons are the load-bearing ones.
- Never-filled markouts from submit (+0.18 to +0.30) mostly measure limit-to-book distance and are not used for the verdict.
- Filled vs never-filled is selection-confounded by construction; the claim is that fills are an adversely selected subset, not that the model is uniformly 50%.
- Immediate-fill subset is small (T1 n=17, T4 n=51); its CI includes zero.
- Candidate rule needs a forward test; see ADR-0072 DRAFT (PROPOSED, switch OFF).

### Artifacts
`scripts/w63_3_fetch_orders.py`, `w63_3_fetch_candles.py`, `w63_3_fill_markouts.py`, `tests/test_w63_3_fill_markouts.py`; `03_DECISIONS/ADR-0072_DRAFT_demo-fills-order-placement.md`.
