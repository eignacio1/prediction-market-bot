# W52.C — MLB resolver (GG-440): why nothing has settled since 2026-08-06

**Session:** Wave 52 CC executor (cloud), T-656, 2026-10-03. **Fix:** draft PR #159, branch `w52/resolver-406` @ `fd315549` (not for merge yet).
**Network caveat:** this is NOT the VPS's network. From this cloud session the egress proxy refuses
`statsapi.mlb.com`, `site.api.espn.com` and `external-api.kalshi.com` (`Tunnel connection failed: 403 Forbidden`,
agent-proxy `connect_rejected`). Nothing below was reproduced against the live services; the VPS reproduction is VPS-PENDING.

## Root cause — LIKELY (needs the VPS reproduction)
Every stuck position goes through three sources in order (`fetch_actual_hits`): statsapi gameLog Regular → statsapi gameLog
Postseason → ESPN boxscore. It is settled only if one of them returns hits. **Statsapi returns HTTP 406 to the VPS
datacenter IP. That is MLB's Fastly CDN blocking the IP, not anything in the request: GG-084 testing on 2026-07-05
got the identical request answered 200 from a residential IP and 406 from 157.230.91.33. The ESPN fallback then also
returns nothing, through a code path that wrote no log line, so the log could not tell "player did not play" apart from
"name mismatch" or "ESPN fails from the VPS."**
The first half matches the code and GG-084's recorded evidence. The second half is inference: 16 of the 17 T1 markets
were cancelled by Kalshi (GG-450), which is consistent with those players not appearing in a boxscore, but the
remaining one (Henderson, a real `yes`) and the 9 T4 positions are unexplained without the VPS log.

## Evidence from the code (run_resolve_mlb.py at origin/main)
- `_fetch_mlb_hits` sends `requests.get(url, params=…)` with **no custom headers** (requests' default UA, `Accept: */*`).
  On an exception it retries 5/10/30 s and then trips the circuit breaker. That accounts for the ~17,000 `406` lines (GG-440).
- A 406 makes both statsapi attempts return `None`, which falls through to `_espn_fetch_hits(player_name, game_date)`.
- `_espn_fetch_hits` logged only fetch errors. When a player appeared in **no** final boxscore it returned `None`
  **without a log line**, so a scratched or DNP player, a display-name mismatch, and a game ESPN marks non-final all
  looked identical to "406 and nothing else."
- After 48 h, `None` makes the position `aged_open` (`api_no_result_48h`), retried every run, forever.
- **Latent hazard:** nothing checked the venue. If any source had returned hits for a game that was played, a market
  Kalshi *cancelled* would have been booked as a WIN or LOSS, which GG-450 forbids until you decide how to book it.

## Fix (PR #159), smallest safe change
1. **Venue gate:** book only when Kalshi reports the market settled `yes`/`no` (historical endpoint first, then live).
   Cancelled, not-final and unreadable markets are skipped, logged as `venue_not_settled_skip`, and never settled or aged.
2. **`--dry-run`:** classifies each position and writes nothing.
3. **Log line:** ESPN's "not found in any final boxscore" is now logged.
It does **not** change the resolution source (GG-440 disposition: operator/ADR-gated) and does not touch t4-mlb's
imports (the resolver is outside `run_t4_mlb_live.py`'s import closure).

## Reproduction attempted here (D2)
| Request | Result from this cloud session |
|---|---|
| resolver's exact statsapi gameLog request (no headers) | proxy refused (403 CONNECT) — not the VPS network |
| same + `Accept: application/json` | proxy refused |
| same + browser UA | proxy refused |
| ESPN scoreboard (no headers / browser UA) | proxy refused |

## VPS-PENDING (for a terminal session)
1. On the VPS, run the resolver's exact request and vary one thing at a time (`Accept: application/json`; no custom
   headers; default UA). Record the status and these response headers: `server`, `via`, `x-served-by`, `x-cache`.
2. `grep -c "ESPN-FALLBACK" logs/resolve_mlb_cron.log` and look at the last run's lines for the 26 positions.
3. Copy `logs/paper_portfolio_mlb.json` and `logs/paper_portfolio_mlb_t4.json` to a scratch dir, then
   `LOG_DIR=<copy> BOT_ENV=paper python3 src/prediction_market_bot/run_resolve_mlb.py --dry-run` (from PR #159's branch).
   Record, for each of the 26 positions: settles / skipped-cancelled / skipped-not-final / unresolvable.
4. Root cause becomes CONFIRMED only after 1 and 2.

## Operator decisions this depends on (not taken here)
- GG-450: how Kalshi-cancelled markets are booked (void / mark to settlement / exclude from G6).
- GG-440: whether Kalshi's own settlement becomes a resolution source (ADR-gated).
