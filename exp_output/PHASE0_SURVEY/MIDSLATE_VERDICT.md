# Phase 0-G — Mid-slate depth re-verdict (T-411)

**Pre-slate sample:** `depth_sample.json`, `2026-07-31T20:13:03Z` (before any game that day had started).
**Mid-slate sample:** `depth/depth_midslate_20260803T233850Z.json`, `2026-08-03T23:40:53Z` (T4M-PROJ live, games in progress, t4-mlb confirmed active before/after, 0 anchored 429s).
**Targeted resample:** `depth/depth_kxmlbhit_targeted_<UTC>.json`, 2026-08-03, `KXMLBHIT` series only, 20/20 currently-open markets from tonight's slate — see "Critical correction" below.

## Table — Family-level pre-slate vs mid-slate, FAIL-NOBOOK vs FAIL-WIDE split

`UNCLASSIFIED` dropped per instruction (heterogeneous, confirmed NCAA-basketball/esports leakage).

| Family | 20:13Z pre-slate | mid-slate (23:38Z) | delta |
|---|---|---|---|
| GAME_TOTAL | 20/20 usable — 0 NOBOOK / 20 WIDE, median depth $0.00 → **FAIL** | 20/20 usable — 0 NOBOOK / 20 WIDE, median depth $0.00 → **FAIL** | No change. Persistent spread-only failure (book exists, never tightens) both times. |
| GAME_WINNER | 20/20 usable — 0 NOBOOK / 8 WIDE / 12 tight, median depth $1,646.50 → PASS | 20/20 usable — 0 NOBOOK / 11 WIDE / 9 tight, median depth $2.67 → **FAIL** | PASS→FAIL. Depth collapsed ~614x; wide-spread count grew 8→11. |
| PARTIAL_GAME_WINNER | 17/20 usable (3 NOBOOK) — 0 WIDE / 17 tight, median depth $410.99 → PASS | 20/20 usable (0 NOBOOK) — 18 WIDE / 2 tight, median depth $0.00 → **FAIL** | PASS→FAIL. Book coverage improved (17→20 usable) but spreads blew out (0→18 wide). |
| PLAYER_PROP (family bucket — see correction below, this is **not** KXMLBHIT) | 3/20 usable (17 NOBOOK) — 1 WIDE / 2 tight, median depth $0.90 → **FAIL** | 3/20 usable (17 NOBOOK) — 0 WIDE / 3 tight, median depth $255.90 → PASS | Usable count unchanged (3/20 both runs — same underlying thin series). Median depth swung ~284x on n=2-3 usable samples — noise, not a resolvable timing signal at this n. |
| RUN_LINE | 20/20 usable — 0 NOBOOK / 20 WIDE, median depth $0.00 → **FAIL** | 20/20 usable — 0 NOBOOK / 20 WIDE, median depth $0.00 → **FAIL** | No change. Same spread-only failure shape as GAME_TOTAL. |
| SEASON_WIN_TOTAL | 10/20 usable (10 NOBOOK) — 4 WIDE / 6 tight, median depth $5.96 → **FAIL** | 9/20 usable (11 NOBOOK) — 4 WIDE / 5 tight, median depth $15.75 → PASS | Modest improvement, still <50% of sampled tickers have any book at all. |
| TEAM_TOTAL | 20/20 usable — 0 NOBOOK / 0 WIDE / 20 tight, median depth $2,043.53 → PASS | 20/20 usable — 0 NOBOOK / 12 WIDE / 8 tight, median depth $0.00 → **FAIL** | PASS→FAIL. Spreads blew out (0→12 wide). |

**This is not a clean "pre-slate was too early, mid-slate is better" story.** Three families that PASSED pre-slate (GAME_WINNER, PARTIAL_GAME_WINNER, TEAM_TOTAL) flip to FAIL mid-slate; two that FAILED pre-slate (PLAYER_PROP-bucket, SEASON_WIN_TOTAL) flip to PASS. GAME_TOTAL and RUN_LINE are stable FAILs both times (a spread problem, not an absence problem, per 0C.10). At n=20 samples per family, single-point-in-time family medians are volatile enough that neither run alone should be read as the settled state — this reinforces the task's own note that "two points show whether depth builds as games progress, which one point cannot," and a single mid-slate point is still only the second point, not a trend.

## Critical correction — the PLAYER_PROP family bucket never sampled KXMLBHIT, in either run

Both the pre-slate and mid-slate `PLAYER_PROP` samples pulled the **identical 20 tickers, in identical order**: all `KXLEADERMLBHITS-26-*` (a season-long MLB hits-leaderboard market), zero `KXMLBHIT` (the single-game player-prop market GG-155 and CLAUDE.md's "$500-$2,000" claim are actually about, and the one traded 2,759 times). Root cause: `phase0_market_survey.py`'s `cmd_depth()` takes `group[:per_family]` from a family bucket built by iterating all series in a fixed order with no per-series balancing; `KXLEADERMLBHITS` sorts/iterates ahead of `KXMLBHIT` within the `PLAYER_PROP` classification and alone exceeds the 20-per-family cap, so `KXMLBHIT` — despite having 325 currently-open markets — has never once been reached by this tool's depth sampler. GG-155's original write-up assumed the family-level PLAYER_PROP measurement represented KXMLBHIT ("the `PLAYER_PROP` family — which `KXMLBHIT`/`KXMLBHR`/`KXMLBRBI`/`KXMLBKS` classify into"); that assumption was never actually true of the sample that produced the $0.90 figure.

**Targeted resample, run tonight directly against `KXMLBHIT`** (20/20 currently-open markets from the fresh mid-slate market list, same orderbook-fetch logic, same safety protocol — t4-mlb confirmed active before/after, 0 anchored 429s):

| Series | Sampled | Usable | FAIL-NOBOOK | FAIL-WIDE | Median half-spread | Median depth within 5c | Gate ($10.00 floor) |
|---|---:|---:|---:|---:|---:|---:|---|
| KXMLBHIT | 20 | 20 | 0 | 0 | 0.5c | **$4,313.72** | **PASS — 431x the floor** |

Every one of the 20 sampled KXMLBHIT markets had a usable, tight (0.5-1.0c half-spread) two-sided book. This is unambiguous: the market CLAUDE.md's "$500-$2,000" claim and GG-155 are actually about is deeply liquid on this venue tonight, and the prior FAIL verdict against it was never measured — it was inherited from an unrelated, genuinely thin series that happens to share a family label.

## The mandated one-sentence verdict

**PLAYER_PROP's pre-slate 3/20-usable / $0.90-median result is a STRUCTURAL finding about `KXLEADERMLBHITS` specifically (unchanged at 3/20 usable mid-slate, both runs sampling the identical thin series), not about `KXMLBHIT` — which a direct targeted sample shows is 20/20 usable at a $4,313.72 median depth (431x the gate floor) and should not have been excluded from Phase 1 scope on the strength of the family-bucket figure.**

## Third sample point (00:04Z, ~26 min after mid-slate) — requested same session, taken immediately rather than after a 90-min wait

**Family-level sample #3:** fresh market refresh (`markets_open_20260804T000153Z.json`, 220 series / 7,076 open markets, up from 6,564 at 23:38Z), t4-mlb confirmed active before and after, 0 anchored 429s in `audit_mlb_t4.jsonl` for the run window.

| Family | 20:13Z pre-slate | mid-slate (23:38Z) | sample 3 (00:04Z) | 3-point read |
|---|---|---|---|---|
| GAME_TOTAL | FAIL, $0.00 (0 NOBOOK/20 WIDE) | FAIL, $0.00 (0/20) | FAIL, $0.00 (0/20) | **Stable FAIL, 3/3.** Persistent spread-only failure. |
| GAME_WINNER | PASS, $1,646.50 (0/8) | FAIL, $2.67 (0/11) | FAIL, $2.13 (0/11) | **FAIL confirmed 2/3, most recent two agree.** Pre-slate PASS looks like the outlier. |
| PARTIAL_GAME_WINNER | PASS, $410.99 (3 NOBOOK/0) | FAIL, $0.00 (0/18) | FAIL, $0.00 (0/18) | **FAIL confirmed 2/3, most recent two agree and are numerically identical.** |
| PLAYER_PROP (bucket — still `KXLEADERMLBHITS`, not `KXMLBHIT`) | FAIL, $0.90 (17 NOBOOK/1) | PASS, $255.90 (17/0) | PASS, $255.90 (17/0) | **PASS confirmed 2/3.** Mid-slate and sample-3 medians are identical to the cent — same 3 usable tickers, unchanged book, 26 min apart: this series is stale/thin, not actively trading, not a real liquidity signal either way. |
| RUN_LINE | FAIL, $0.00 (0/20) | FAIL, $0.00 (0/20) | FAIL, $0.00 (0/20) | **Stable FAIL, 3/3.** |
| SEASON_WIN_TOTAL | FAIL, $5.96 (10 NOBOOK/4) | PASS, $15.75 (11/4) | PASS, $23.49 (11/2) | **PASS confirmed 2/3, trending up.** Still <50% book coverage (9/20 usable) both recent runs. |
| TEAM_TOTAL | PASS, $2,043.53 (0/0) | FAIL, $0.00 (0/12) | PASS, $30.60 (0/0) | **No majority — 2 PASS, 1 FAIL, and the two PASS magnitudes disagree by ~67x ($2,043.53 vs $30.60).** Genuinely unsettled; do not treat as resolved. |

**KXMLBHIT targeted resample #2** (00:04:50Z, same 20 tickers drawn fresh from the 00:01Z open-market list, 422 open markets available for the series, up from 325 at mid-slate):

| Run | Usable | FAIL-NOBOOK | FAIL-WIDE | Median half-spread | Median depth within 5c | Gate |
|---|---:|---:|---:|---:|---:|---|
| Targeted #1 (23:50:50Z) | 20/20 | 0 | 0 | 0.5c | $4,313.72 | PASS — 431x |
| Targeted #2 (00:04:50Z) | 20/20 | 0 | 0 | 0.5c | $304.685 | PASS — 30x |

**KXMLBHIT status is now confirmed PASS on two independent runs, ~14 minutes apart, with zero FAIL-NOBOOK and zero FAIL-WIDE both times — but the depth magnitude swung ~14x ($4,313.72 → $304.685) between them.** This is the same volatility pattern seen family-wide (TEAM_TOTAL swung ~67x between its two PASS points). **Per the task's own stability rule, this is decisive-PASS-but-not-stable-magnitude: CLAUDE.md's "$500–$2,000" text is still not corrected** — a fixed dollar range implies a stability neither run supports, even though both runs clear the $10 gate by 1-2 orders of magnitude. GG-155 updated accordingly below.

## Implications for Phase 1 build order (reporting only — no Phase 1 work started per scope boundary)

- `KXMLBHIT` clears the depth gate decisively on two independent samples and should be back in scope for whatever family/build-order decision Phase 1 was waiting on this data for. Its *magnitude* is volatile intraday (~14x swing in 14 minutes) — build-order sizing decisions should treat this as "liquid, order-of-magnitude uncertain," not a fixed number.
- `KXLEADERMLBHITS` (season leaderboard props) independently fails on its own thin-book merits — that verdict stands, it just isn't a KXMLBHIT verdict. Its own 2/3 samples are numerically identical, consistent with a market that simply isn't trading, not one that's liquid-but-noisy.
- GAME_WINNER and PARTIAL_GAME_WINNER now have 2/3 points agreeing on FAIL (the two most recent, most temporally adjacent runs) — treat the pre-slate PASS as the likely outlier, not the settled state, but this is still only 3 points.
- TEAM_TOTAL remains genuinely unsettled — 2 PASS/1 FAIL with the two PASS magnitudes disagreeing by ~67x. A 4th point would be needed before calling this either direction.
- The `phase0_market_survey.py` `cmd_depth()` per-family sampling gap (no per-series balancing within a family bucket) should be registered/fixed before this tool is trusted again for any family with more than ~20 constituent-series markets — `PLAYER_PROP` is not the only family with multiple series (see Table 1 in `SURVEY_TABLES_MIDSLATE.md`: `GAME_WINNER` alone spans MLB+NBA+NFL+NHL+OTHER).
- Separately: the first targeted-KXMLBHIT script (this session) had a bug — `client._get()` returns `tuple[bool, Any]`, and the first version treated it as the raw response dict, crashing with `AttributeError: 'tuple' object has no attribute 'get'` on the first call. Fixed by unpacking `ok, data = client._get(...)` before the second run. Worth noting since this is a one-off script, not the production `phase0_market_survey.py` (which handles this correctly) — do not copy the buggy unpacking pattern if this script is ever promoted to a reusable tool.
