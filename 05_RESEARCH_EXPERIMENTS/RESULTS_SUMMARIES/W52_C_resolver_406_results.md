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

---

## VPS confirmation (W53.1, 2026-10-05)

**Verdict: CONFIRMED in refined form, and it is not the whole explanation.**
The VPS IP (157.230.91.33) gets HTTP 406 on every statsapi request that must go to origin (CDN cache MISS), independent
of headers, gameType or cache-buster. The same requests return 200 from the Mac, and 200 from the VPS when the object
is already in the CDN cache. Separately, 10 of the 26 stuck positions sit on POSTPONED games and could not resolve even
on an unblocked network. Wording: "406 to the VPS on cache-MISS" is evidenced; "Fastly IP block" vs "origin" is not
distinguishable (the 406 body is a Spring Boot-style JSON error, len 119).

### D1: request matrix (VPS, requests 2.31.0; Mac for comparison)
| Probe | VPS | Mac |
|---|---|---|
| resolver's exact request, player 660271, gameType R (no extra headers) | 200, len 178781, x-cache HIT (via google, varnish, varnish) | 200 |
| + `Accept: application/json` / curl UA / browser UA / no UA | 200 (same cached object) | 200 |
| gameType P, player 660271 | **406**, len 119, x-cache MISS, MISS | 200, len 2901 |
| per-player R (592518, 668930, 677800, 660271) | 200 (first layer HIT) | 200 |
| per-player P (same four) | **406** MISS, MISS | 200 |
| cache-busted: R popular, R again, P, P+Accept, P+Accept+browser UA, obscure id 701000 | **406** MISS, MISS on all | 200 on all |

A single cold probe looked like 200 on the VPS because of CDN HITs; that premise ("every request 406s") was refuted and
the method corrected with cache-busting.

### D2: log evidence
- First 406 in `resolve_mlb_cron.log`: 2026-06-27 (R and P both). The 2026-10-04 06:30Z run reached consecutive_failures
  123-125 with the circuit breaker open.
- 494 `ESPN-FALLBACK` lines, all fetch errors. The old code logged nothing when ESPN fetched fine but found no player,
  so ESPN's silence for the 26 positions was a logging gap, not evidence of success.

### D4: 26-position dry run (copies of both ledgers; `--dry-run`; VPS ledgers untouched)
| Group | n | Positions | Classification | Reason |
|---|---|---|---|---|
| T1 | 16 | CJ Abrams x2 (26JUL011335WSHBOS), Julio Rodriguez (26JUL032210TORSEA), Mike Trout (26JUL102010LAAMIN), Nick Kurtz x2 (26JUL101940ATHCWS), Bobby Witt Jr. x4 (26JUL191410SDKC, 26JUL211940SFKC), Ketel Marte x2 (26JUL231715AZSTL), Steven Kwan (26JUL241910CLETB), Jose Ramirez (26JUL241910CLETB), Christian Walker x2 (26JUL261410HOUCWS) | SKIPPED-CANCELLED | Kalshi result `scalar` / expiration "Cancelled" |
| T1 | 1 | Gunnar Henderson KXMLBHIT-26JUL211910BALBOS-BALGHENDERSON2-1 (venue yes) | UNRESOLVABLE | game POSTPONED Jul 21, played as doubleheader Jul 22 |
| T4 | 9 | all 26SEP221835TORBAL: Okamoto x3 (no), Alonso -2 (no), Henderson x3 (no), Springer -1 (yes), Springer -2 (no) | UNRESOLVABLE | game POSTPONED Sep 22, played Sep 23 |

Tally: 16 cancelled, 10 postponed-game, 0 settle, 0 not-final. **Zero cancelled markets received a WIN or LOSS.**
The Kalshi yes/no results on the 10 are consistent with the make-up-game stats.

### What the Mac not being blocked changes
The Mac can reach statsapi, but running the resolver from the Mac would still settle 0 of the 26 (16 cancelled by
design, 10 keyed to a postponed date). Unblocking the network alone fixes nothing for this set.

### D5: change on `w52/resolver-406` (c9462a1, log-only, +2 tests)
ESPN's not-found line now names POSTPONED games on the date, so this case is visible in the log. No resolution,
ledger, sizing or stake behavior changed. PR #159 not merged.

### Open for the operator
1. GG-450: how Kalshi-cancelled markets are booked (16 T1 positions).
2. GG-440: Kalshi settlement as a resolution source (ADR-gated).
3. New: how positions on postponed/rescheduled games resolve (follow the reschedule date vs. Kalshi's result).
4. Unexplained: T4 held 9 positions on a game ESPN reports POSTPONED (a started-then-suspended game?). Needs a look.
