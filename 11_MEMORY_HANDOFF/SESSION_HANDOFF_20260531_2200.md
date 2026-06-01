# Session Handoff — 2026-05-31T22:00Z

**Trigger:** Operator-initiated — context window wrap + Earl's "items 2-4 are priorities" directive  
**Last commit:** `92539b9` (main) — pushed to GitHub + VPS

---

## Status

- **Phase:** 6/7 ACTIVE
- **Tests:** 548/548 passing
- **Capital:** NO live capital — paper trading only (G6 gate)
- **VPS:** 157.230.91.33 — cron RUNNING (22:00 UTC / 01:30 UTC / 06:00 UTC)
- **Paper bets:** 0/30 resolved — G6 gate. Clean evidence begins Finals G1 Jun 3.
- **Demo balance:** $999.36 | portfolio_value: $0.62 (open Costoulas YES position — will resolve when match ends)

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| APR-0016 "4 bets/game-day" estimate is STALE and CORRECTED | Written 2026-05-29 before ADR-0006 deleted count gate. Post-ADR-0006 throughput: 17-40+ bets per Finals game night. G6 30 bets may be reached in 1-2 Finals game nights. | DECISION_LOG.md (corrective entry 2026-05-31) + MEMORY_BANK invariant #8 | DS |
| T-111: Kalshi auth root cause — wrong base URL | `api.elections.kalshi.com` is legacy/public-only. Authenticated endpoints require `external-api.demo.kalshi.co` (demo) or `external-api.kalshi.com` (live). RSA-PSS signing was correct throughout. | DECISION_LOG.md (2026-05-31) + kalshi_client.py `_kalshi_base_url()` | EL |
| submit_order body must send exactly ONE price field | Kalshi 400 INVALID_ORDER if both yes_price and no_price are sent. Only send the field matching the side. | DECISION_LOG.md (2026-05-31) + kalshi_client.py `submit_order()` | EL |
| First live Kalshi demo order logged | Order 363c5f5b — KXWTACHALLENGERMATCH-26JUN01SAKCOS-COS, YES 1 contract at $0.62, status `executed`. End-to-end execution path proven. | DECISION_LOG.md (2026-05-31) | DS |

---

## ⚠️ NEW OPEN QUESTION — MUST ANSWER BEFORE G6 EVIDENCE IS VALID

**Does Kalshi demo use artificial/dummy prices for its markets?**

Evidence suggesting YES (artificial):
- WTA tennis demo order book: YES ask $0.62, YES bid $0.00 — typical of seeded-not-discovered pricing
- Demo has its own market set (not a mirror of production) — consistent with a testing sandbox
- Kalshi documentation describes demo as "for testing API integration"

**Why it matters:**
- Current paper trading (BOT_ENV=paper) routes ALL API calls → `external-api.demo.kalshi.co`
- Market prices fetched from demo are used to calculate `edge = model_p - market_price` and set bet price
- If demo prices are artificial: edge is meaningless; P&L does not validate the commercial case; G6 evidence is hollow
- If demo prices are real (community-discovered): no issue

**Proposed fix if confirmed artificial:**
- Add `_price_discovery_url()` to `kalshi_client.py` that always returns the production URL
- BOT_ENV=paper continues to suppress actual order submission (no live capital risk)
- Price discovery (GET /markets, GET /orderbook) uses production for real prices
- One-line config change; no architectural disruption

**How to confirm:**
1. At Finals G1, check a KXNBAPTS market price on demo vs. production simultaneously — if they diverge, demo is artificial
2. Contact Kalshi support / check docs at kalshi.com/docs
3. The most conservative interpretation: treat as artificial until proven otherwise

**Register this as a gate question before counting Finals G1 bets toward G6 if unresolved.**

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| T-111: Kalshi auth — wrong base URL | ✅ Fixed: `_kalshi_base_url()` reads BOT_ENV; demo URL corrected; `get_balance()` parsing fixed (flat dict); RSA-PSS unchanged |
| T-112: VPS deploy | ✅ `cryptography==43.0.3` installed on VPS; `VENUE_PRIVATE_KEY_PATH=/root/.ssh/kalshi_bot.pem` set; git pull HEAD 92539b9; cron intact |
| submit_order bug | ✅ Fixed: one price field only (yes_price OR no_price, not both); was returning HTTP 400 |
| APR-0016 correction | ✅ "4 bets/game-day" stale estimate corrected in DECISION_LOG and MEMORY_BANK invariant #8 |
| First live demo order | ✅ Order 363c5f5b executed at $0.62 YES; balance deducted confirmed; execution path proven end-to-end |

---

## ⚠️ PRIORITY QUEUE — ITEMS 2-4 (item 1 = Costoulas position, operator handling)

### PRIORITY 2 — G6 Evidence Accumulation (T-110)

Clean evidence begins **Finals G1 Jun 3, 2026**. Cron fires 22:00 UTC (early games) + 01:30 UTC (late games).

**After each cron fire:**
```bash
ssh root@157.230.91.33
cat /opt/prediction-market-bot/src/prediction_market_bot/logs/paper_portfolio.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'Bankroll: ${d[\"bankroll\"]:.2f} | Open: {len(d[\"open_positions\"])} | Resolved: {len(d[\"closed_positions\"])}')"
```

**Expected throughput:** 17-40+ bets per Finals game night (cohort v3: 55 players × Kalshi KXNBAPTS markets × C4 approval rate).

**⚠️ GATE THIS:** Confirm demo price validity (question above) before counting Finals bets toward G6.

---

### PRIORITY 3 — EXP-017 Part B: Commercial Validation (T-105) — OPERATOR ACTION

Part A complete: sensitivity sweep shows EV positive at ALL market price levels 0.40–0.60.  
**Part B requires operator to pull real Kalshi historical prices.**

Collection method:
```bash
# On VPS or local — requires VENUE_API_KEY
GET /trade-api/v2/markets?series_ticker=KXNBAPTS&closed=true
```

Save as: `exp_output/EXP-017/kalshi_prices.csv`  
Columns: `player_id, game_date, kalshi_threshold, kalshi_mid_price, kalshi_vig`

Then run:
```bash
PYTHONPATH=src python3 src/prediction_market_bot/run_exp017.py --kalshi-prices exp_output/EXP-017/kalshi_prices.csv
```

**Closes GG-004 (G6 blocker). Until this runs, the commercial case is unproven.**

---

### PRIORITY 4 — Resolution Procedure (T-109): After Each Game Day

VPS 403 blocks nba_api (stats.nba.com hard-blocks DigitalOcean IPs). Resolution must run locally.

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
BOT_ENV=paper PYTHONPATH=src python3 src/prediction_market_bot/run_resolve_local.py
```

Run this the morning after each Finals game (after ~10:00 AM ET when nba_api updates).

---

## ONE THING PENDING

**The demo price validity question must be answered before Finals G1 bets count toward G6.** If demo prices are artificial, the evidence is hollow. The fix (production price discovery in paper mode) is a one-hour implementation task. Do not let this slide past Finals G1.

---

## Current Paper Portfolio

- Bankroll: $999.36 (demo) | $0.62 open (Costoulas YES — will resolve naturally)
- Open: 1 (demo test position — does not count toward G6)
- Closed/Resolved: 0 | G6 gate: 0/30
- Clean slate: paper_portfolio.json reset on VPS; clean evidence starts Finals G1 Jun 3

---

## Active Cron on VPS (157.230.91.33)

```
21:00 UTC  — Health check
21:30 UTC  — PIPE-02 inference (run_pregame.py)
22:00 UTC  — PIPE-03 early (paper bets, 7pm ET games)
01:30 UTC  — PIPE-03 late (paper bets, 9pm+ ET games)
06:00 UTC  — PIPE-03R resolve-only (run_resolve.py)
14:00 UTC Mon — Model freshness check
```

---

## Key Constraints to Remember

1. Work wifi blocks Kalshi API — use any other network (home, hotspot)
2. No live capital until G6 (**30 resolved paper bets** + positive P&L — APR-0016)
3. VPS cannot resolve positions (stats.nba.com 403) — run `run_resolve_local.py` locally after each game day
4. kalshi_bot.pem MUST NOT be committed to VCS (NFR-05). It lives at `/root/.ssh/` on VPS and `~/.ssh/` locally.
5. Demo market set ≠ production market set. Test orders (like Order 363c5f5b) use demo-only markets. Production has the real KXNBAPTS NBA Finals markets.

---

## ⚙️ DECISION AUDIT

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| kalshi_client.py (modified) | N/A — code file | T-111 root cause + fix logged | ✅ |
| MEMORY_BANK.md (modified) | N/A | Invariant #8 updated | ✅ |
| DECISION_LOG.md | N/A | 3 new entries (APR-0016 correction, submit_order fix, Order 363c5f5b) | ✅ |
| All other docs: 7 documents with `decisions_logged: false` | false | Pre-existing — T-093 through T-099 registered | ✅ (tracked) |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude:
# "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260531_2200.md.
# Top priority: answer the demo price validity question before counting Finals G1 bets toward G6.
# Then monitor VPS cron output after Finals G1 Jun 3 (22:00 UTC)."
```
