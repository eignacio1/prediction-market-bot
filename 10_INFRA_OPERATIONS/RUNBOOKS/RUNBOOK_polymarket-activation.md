# Runbook: Polymarket US API Activation (T-077 / ACC-0003)

**Purpose:** Step-by-step procedure to provision Polymarket US API access and activate VenueRouter best_price mode for Strategy E (line shopping) and Strategy C (complement lock scanning).  
**Owner:** Infrastructure Owner (IO) / Director/Sponsor (DS)  
**Last reviewed:** 2026-05-29 (initial draft — T-077)  
**Prerequisites:** ADR-0003 ACCEPTED (Polymarket US as Phase 6+ secondary venue); T-078 VenueRouter skeleton complete  
**Governance:** ACC-0003 entry in ACCESS_REQUESTS.md must be updated to GRANTED after key is provisioned  

---

## Overview

Polymarket US relaunched under CFTC regulation in December 2025. It operates a CLOB (Central Limit Order Book) for binary YES/NO prediction markets. Once your API key is provisioned and set in `.env`, `VenueRouter.from_env()` will automatically register the `PolymarketVenueAdapter` and enable multi-venue routing.

**What activates immediately on key provisioning:**
- `VenueRouter.fetch_all_markets()` in `best_price` mode merges Kalshi + Polymarket snapshots
- `ComplementLockScanner.scan_snapshot()` can detect cross-venue lock conditions
- `VenueRouter.get_best_market()` routes bets to the cheapest venue per direction

**What remains gated:**
- Live order execution (still requires BOT_C4_ACTIVE + ADR-0005 at G6)
- Complement lock execution (still requires APR-0010)

---

## Step 1 — Create Polymarket US Account

1. Go to **polymarket.com** and sign up for a US account
2. Complete KYC/identity verification (CFTC-regulated; ID required)
3. Navigate to **Settings → API** (or equivalent) to generate an API key
4. The key will be a long alphanumeric string — treat it as a secret (NFR-05)

---

## Step 2 — Provision API Key (NFR-05 protocol)

Add to your `.env` file (gitignored; never committed):

```bash
POLYMARKET_API_KEY=<your-key-here>
```

Verify it's set:
```bash
grep POLYMARKET_API_KEY .env   # should show the key
```

**Do NOT:**
- Hardcode the key in any source file
- Log or print the key
- Commit `.env` to git

---

## Step 3 — Verify Connectivity

Run the connectivity check from the project root:

```bash
PYTHONPATH=src /usr/local/bin/python3.11 -c "
from prediction_market_bot.c5_execution.venue_adapter import PolymarketVenueAdapter
adapter = PolymarketVenueAdapter.from_env()
ok, status = adapter.check_connectivity()
print('Connectivity:', ok, status)
"
```

Expected output: `Connectivity: True {'status_code': 200, 'venue': 'polymarket', 'reachable': True}`

If `status_code` is 401 or 403: key is invalid or account not approved.  
If connection fails: check network (home ISP may be blocked — try hotspot).

---

## Step 4 — Test Market Fetch

```bash
PYTHONPATH=src /usr/local/bin/python3.11 -c "
from prediction_market_bot.c5_execution.venue_adapter import PolymarketVenueAdapter
adapter = PolymarketVenueAdapter.from_env()
ok, snapshot = adapter.fetch_player_points_markets()
print(f'Markets fetched: {len(snapshot.markets)} | ok={ok}')
if snapshot.markets:
    m = snapshot.markets[0]
    print(f'  Sample: {m.player_name} | threshold={m.threshold} | mid={m.mid_price:.3f} | vig={m.vig:.3f}')
"
```

**If 0 markets returned:** Polymarket US may not yet have NBA player prop markets, or the tag/filter in `_parse_market()` needs updating. Check Polymarket's market catalog and update the `tag` parameter in `fetch_player_points_markets()`.

**If parsing fails:** The market question format may differ from the regex in `_parse_market()`. Inspect `snapshot.markets` raw and update the regex pattern in `PolymarketVenueAdapter._parse_market()`.

---

## Step 5 — Activate VenueRouter best_price mode

Add to `.env`:

```bash
VENUE_ROUTER_MODE=best_price
```

Test the full VenueRouter:

```bash
PYTHONPATH=src /usr/local/bin/python3.11 -c "
from prediction_market_bot.c5_execution.venue_router import VenueRouter
router = VenueRouter.from_env()
print('Active venues:', router.active_venues)
print('Mode:', router.mode)
ok, snapshot = router.fetch_all_markets()
print(f'Merged markets: {len(snapshot.markets)} | ok={ok}')
kalshi = [m for m in snapshot.markets if m.venue == 'kalshi']
poly   = [m for m in snapshot.markets if m.venue == 'polymarket']
print(f'  Kalshi: {len(kalshi)} | Polymarket: {len(poly)}')
"
```

Expected: both venues listed, merged snapshot has markets from both.

---

## Step 6 — Test Complement Lock Scanner

```bash
PYTHONPATH=src /usr/local/bin/python3.11 -c "
from prediction_market_bot.c5_execution.venue_router import VenueRouter
from prediction_market_bot.c5_execution.complement_lock_scanner import ComplementLockScanner
router = VenueRouter.from_env()
ok, snapshot = router.fetch_all_markets()
scanner = ComplementLockScanner()
opps = scanner.scan_snapshot(snapshot.markets)
print(f'Lock opportunities detected: {len(opps)}')
for o in opps[:3]:
    print(f'  {o.player_name} t={o.threshold}: YES@{o.yes_venue}={o.ask_yes:.3f} NO@{o.no_venue}={o.ask_no:.3f} net={o.net_profit:.4f}')
print('NOTE: Detection only — APR-0010 required before any execution')
"
```

---

## Step 7 — Update Governance Records

After successful connectivity and market fetch:

1. Update `ACCESS_REQUESTS.md`:
   - Move ACC-0003 from Pending to Active Grants
   - Record approval date and approver

2. Update `VENUE_REGISTRY.md` V-002:
   - Change `Activation` from `🔲 Phase 7 (T-077 / ACC-0003)` to `✅ ACTIVE`
   - Fill in confirmed API base URL
   - Record confirmed vig from live market data

3. Update `ENVIRONMENTS.md`:
   - Add `POLYMARKET_API_KEY` to ENV-02 variable table

4. Register in CHANGELOG.md: `ACC-0003 GRANTED — Polymarket US API active`

---

## Step 8 — VPS Deployment

Once validated locally, push changes to VPS:

```bash
ssh -i ~/.ssh/id_ed25519_droplet root@157.230.91.33
echo "POLYMARKET_API_KEY=<key>" >> /opt/prediction-market-bot/.env
echo "VENUE_ROUTER_MODE=best_price" >> /opt/prediction-market-bot/.env
```

Restart PIPE-02 to pick up the new env (cron will use it from next scheduled run):

```bash
source /opt/prediction-market-bot/.env
cd /opt/prediction-market-bot
/opt/prediction-market-bot/venv/bin/python src/prediction_market_bot/run_pregame.py
```

Verify in logs: `grep polymarket logs/audit.jsonl | tail -20`

---

## Rollback

If Polymarket connectivity causes PIPE-02 failures:

```bash
# On VPS — revert to Kalshi-only
sed -i 's/VENUE_ROUTER_MODE=best_price/VENUE_ROUTER_MODE=kalshi_only/' /opt/prediction-market-bot/.env
```

VenueRouter degrades gracefully: if Polymarket adapter fails, it falls back to Kalshi-only and logs a WARNING (not a kill-switch event).

---

## Known Limitations (verify on activation)

| Item | Status | Action |
|------|--------|--------|
| Exact API base URL | TBD — `clob.polymarket.com` assumed | Verify in Polymarket API docs |
| Market tag for NBA props | TBD — `"nba"` assumed | Check Polymarket tag taxonomy |
| Question regex pattern | TBD | Inspect live market questions; update `_parse_market()` if needed |
| WAF / IP blocking | Unknown | Test from hotspot + VPS; add to connectivity notes |
| Rate limits | Unknown | Add throttling in adapter if needed |
| NBA player prop availability | TBD | Confirm NBA player threshold markets exist on US platform |
