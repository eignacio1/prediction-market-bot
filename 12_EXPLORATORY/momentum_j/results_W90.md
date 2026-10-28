# W90.3 — Momentum, measured: follow it or fade it? (Strategy J)

**Purpose:** DEPTH + PROOF. Measures: D5(a) `momentum_looping` 0 → a measured basis per sport; follow/fade transition contexts estimated, 0 → n.
**Run:** 2026-10-27. Code `core.py` / `run_w90_3.py`, tests `tests/test_w90_3_momentum_j.py`, raw cells `out/summary.json`. Seed 20261027.

## Verdict (one paragraph)

**Pre-game moves of 3c or more do not continue and do not revert on a 1h or 3h horizon: gross follow P&L is 0.000 to 0.004 per contract
(MLB 1h +0.0004, 3h +0.0035; NFL 1h −0.005, 3h −0.013; NBA/NHL ≈ 0.001, all n ≥ 88), so the price after a move is a random walk with
no signal in either direction.** Net of half-spreads and the k007 fee on both legs, following loses 4c (tight books) to 13–17c (wide
books) per contract. **No context in the 97 testable main-grid cells has a positive game-clustered follow interval, and the
pre-registered-style train/hold-out routing rule routes zero contexts to MOMENTUM-FOLLOW or MOMENTUM-FADE.** 89.2's "reverting lost in
all 40 cells" was therefore not evidence for following: the fade gross is the mirror image of the follow gross, which is also ≈ 0. Both
lose because of cost, not because the market was efficient in a way that favours the other side.

## Method (what was and was not done)

- **Signal:** mid change ≥ 3c over a 40–80 min look-back (price archive, ~20-min snapshots; MLB + NFL, 2026-08-01..10-27) or one hourly step (89.7
  candles; NBA/NHL game markets, plus 2 NFL). One signal per ticker per 3 h. Size buckets 3–5c / 5–10c / 10c+.
- **Entry** at the NEXT snapshot's quote, in the direction of the move (follow) or against it (fade). YES at the ask, NO at 1 − bid.
- **Exit** +1 h, +3 h (sold at the later snapshot's bid / 1 − ask; pre-start only) or **settlement** (fetched from public Kalshi
  settled-market GETs, `fetch_settle.py`). **Costs:** the real quoted half-spreads on both legs + k007 fee on entry and exit (entry only
  for settlement).
- **Inference:** game-clustered bootstrap (`quant.inference.cluster_bootstrap`) and a cluster-robust z; a cell is testable at ≥ 30 games;
  Benjamini–Hochberg q = 0.10 across all 378 testable cells (main grid × time-to-start × book × news × source × direction, follow and fade).
- **Signals:** 20,409 (MLB 15,692, NFL 2,784, NHL 117, NBA 91 at the 1 h exit). NBA and NHL are 89.7 hourly candles of game
  markets only; no spread/total/prop candles exist, so those families are untested.
- **Quant bar:** (1) tests recover a simulated trend as FOLLOW and a simulated mean-reversion as FADE, and show a driftless walk losing
  on both sides after costs (`tests/test_w90_3_momentum_j.py`, 6 passing). (2) *Applies to* pre-game two-sided quotes where a later quote exists
  before the start; *does not apply* to in-play, one-sided books, or horizons shorter than the snapshot cadence (20 min / 1 h). (3) Measured
  results below carry n, games and a 95% interval.

## Part A — follow, net (pooled by sport; per-family grid in `out/summary.json`)

| Sport (source) | Hold | n | Gross follow | Net follow | 95% interval |
|---|---|---|---|---|---|
| MLB (20 min) | 1 h | 15,692 | +0.0004 | −0.146 | — |
| MLB | 3 h | 12,965 | +0.0035 | −0.125 | −0.129, −0.121 |
| MLB | settle | 10,917 | −0.0044 | −0.087 | −0.096, −0.078 |
| NFL (20 min) | 3 h | 1,412 | −0.013 | −0.157 | −0.190, −0.126 |
| NFL | settle | 3,204 | −0.003 | −0.091 | −0.117, −0.065 |
| NBA (1 h) | 3 h | 88 | +0.001 | −0.043 | −0.049, −0.037 |
| NBA | settle | 97 | +0.026 | +0.003 | −0.087, 0.096 |
| NHL (1 h) | 3 h | 114 | +0.000 | −0.065 | −0.073, −0.055 |
| NHL | settle | 119 | +0.070 | +0.038 | −0.041, 0.117 |

- **Book state decides how much you lose, not whether.** MLB tight books (half-spread ≤ 1c): net −0.039 at 3 h; wide books: −0.134. NFL tight −0.040 / wide −0.177.
- **Time to start:** every MLB/NFL tier with n ≥ 1,000 is a loss of 8–16c net with gross ≈ 0. Tiers T2–6h and T0–2h are too thin (≤ 46 signals).
- **Direction:** up-moves and down-moves behave alike (MLB 3 h net −0.142 / −0.112).
- **Multiplicity:** BH (q = 0.10) flags 335 of 378 cells; 333 of them are significant *losses*. Exactly two flagged cells are positive (below).
  Zero of 97 main-grid follow cells and 1 of 189 testable follow cells (the NBA one) have a positive interval.

### News-driven vs unexplained moves — a calendar proxy, not observed report times

No archive of public news timestamps exists (the NBA injury-report relay is a recent-only PDF branch; NFL/MLB lineup times were never captured),
so "news" is a **scheduled-window proxy**: MLB lineups [start − 4 h, start − 1.5 h]; NFL Wed–Fri 17:00–18:30 ET reports + inactives [start − 1.75 h, − 1.25 h];
NBA 17:00 ET prior day, 13:00 and 17:00 ET game day, final [start − 1.25 h, − 0.5 h]; NHL 11:00–13:00 ET + final. A move is "news" if its look-back window overlaps one.
Registered as **GG-1300**. On this proxy: 98% of MLB signals are "quiet" (the archive's pre-start range sits mostly outside lineup windows), so the news cells are thin.

| Context (proxy) | Hold | n / games | Gross follow | Net follow | Net fade | Note |
|---|---|---|---|---|---|---|
| MLB news-window | settle | 53 / 41 | −0.177 | −0.218 (−0.318, −0.101) | **+0.136 (0.025, 0.240)** | BH-flagged, p = 0.010 |
| NFL news-window | 3 h | 145 / 41 | −0.025 | −0.109 (−0.145, −0.081) | — | loses |
| NFL news-window | settle | 147 / 43 | −0.010 | −0.065 (−0.139, −0.003) | — | loses |

## Part B — the transition

Rule (interpretable, no fitted model): cell = sport × time-to-start tier × move size (< 5c / ≥ 5c) × news flag, 3 h hold. Fit on the first half by date (to
2026-09-03; n = 8,008); a cell is routed FOLLOW if the train follow-net interval is above zero, FADE if the train fade-net interval is above zero; scored on the later half (n = 6,572).

- **Result: 0 of 4 train-testable cells route either way.** All four are MLB quiet cells; train follow net −0.109 to −0.139, train fade net −0.126 to −0.146;
  hold-out follow net −0.134 to −0.153 (every interval entirely below zero), hold-out fade −0.126 to −0.145. The transition point between following and fading
  *is not located on any axis we can measure at this cadence* — both sides sit equally below zero, so there is no sign change to find.
- **Out-of-sample net for routed contexts: none exist.** 90.2's router should route **nothing** to MOMENTUM-FOLLOW or MOMENTUM-FADE from this evidence; a
  momentum feature, if any, can only be a veto (do not enter against a ≥ 3c move in wide books, where the round trip costs more than the whole move).

## Two hypotheses worth a pre-registration (not verdicts)

Both come out of 378 tests, are small, cannot be hold-out validated at this n, and one rests on the calendar proxy. They are candidates, not findings.

1. **MLB: fade a ≥ 3c move that lands in the lineup-posting window and hold to settlement.** n = 53 / 41 games, net fade +0.136 (95% 0.025–0.240), BH p = 0.010.
   Needs: real lineup-post timestamps (GG-1300), then a pre-registered test at ≥ 150 games.
2. **NBA: follow ≥ 3c up-moves to settlement.** n = 52 / 42 games, net +0.145 (0.003–0.277), BH p = 0.033; the down-move mirror is −0.160 — the opposite sign,
   which argues against a real momentum effect and for a favourite/longshot artifact (settlement outcomes after up-moves). Weakest of the two.

## Component stage (ADR-0075, D5)

| Sport | momentum_looping | Stage |
|---|---|---|
| MLB, NFL, NBA, NHL | tested scaffold (`12_EXPLORATORY/momentum_j/`) with a measured basis: **no momentum at 1–3 h; both sides lose to cost** | **interpreted** (a measured fact about the market; *applied* would need a context that beats cost — none found) |

Granularity index: split = sport × family × move size × hold × time-to-start × book × news-proxy; rank vs history = the hold-out half; matchup cross = none (not built);
market map = the 13 game-market families in the archive; application = **none** — cost exceeds the whole effect.

## Caveats

- 20-min / 1-h cadence cannot see sub-20-minute reversion or continuation; this is the horizon where the bot's T1 sits, not where T4 sits.
- MLB start time is the ticker HHMM read as ET (GG-1253, still unverified) — it only affects the time-to-start tier, not the move or cost.
- NBA/NHL: 89.7 candles of game markets, a single season-start window, n ≤ 119; NFL candles contribute 1–2 signals. A 90.2 router decision should not rest on them.
- Settlement uses the outcome of the contract the bot trades; spread/total families are included in the main grid by series ticker.
