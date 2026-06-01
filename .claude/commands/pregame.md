# /pregame — Pre-Game Run Diagnostics

Run the following checks sequentially. Report each as [OK] or [FAIL + reason]. Stop and report on first FAIL — do not continue past a FAIL without explicit operator instruction.

## Environment Checks

```bash
# 1. Python version
python3.11 --version

# 2. Model file present and not stale
python3.11 -c "
import json
from datetime import datetime, timezone
m = json.load(open('models/prod_model_meta.json'))
age = (datetime.now(timezone.utc) - datetime.fromisoformat(m['trained_at'].replace('Z','+00:00'))).days
print(f'Model: {m[\"model_version\"]} | Features: {m[\"feature_count\"]} | Age: {age}d')
if age > 30: print('WARNING: Model >30 days old')
"

# 3. Kill switch not tripped (BOT_C4_ACTIVE must be absent)
python3.11 -c "
import os
val = os.environ.get('BOT_C4_ACTIVE', '')
if val.lower() in ('true', '1', 'yes'):
    print('FAIL: BOT_C4_ACTIVE is set — must not be set in ENV-02')
else:
    print('OK: BOT_C4_ACTIVE not set')
"

# 4. Audit log writable
python3.11 -c "
import os
log_dir = os.environ.get('LOG_DIR', 'logs')
os.makedirs(log_dir, exist_ok=True)
test_path = os.path.join(log_dir, '.write_test')
open(test_path, 'w').close(); os.remove(test_path)
print(f'OK: Log dir writable: {log_dir}')
"

# 5. Kalshi API reachable (read-only)
python3.11 -c "
import os, urllib.request, json
key = os.environ.get('VENUE_API_KEY', '')
if not key: print('FAIL: VENUE_API_KEY not set'); exit(1)
try:
    req = urllib.request.Request('https://api.elections.kalshi.com/trade-api/v2/exchange/status',
        headers={'Authorization': f'Bearer {key}'})
    r = json.loads(urllib.request.urlopen(req, timeout=10).read())
    print(f'OK: Kalshi exchange_active={r.get(\"exchange_active\")}')
except Exception as e:
    print(f'FAIL: Kalshi API unreachable: {e}')
"
```

## Pre-Run Summary

After checks pass, report:
- How many NBA games are scheduled today (check Kalshi KXNBAPTS markets)
- Expected run time (21:30 UTC = 5:30pm ET)
- Whether this is a late-game day (games after 10pm ET → 01:30 UTC cron catches them)

## Manual Trigger Command

If all checks pass and operator wants to run immediately:
```bash
source .env
PYTHONPATH=src python3.11 src/prediction_market_bot/run_pregame.py
```

Then verify:
```bash
cat logs/pregame_$(date +%Y%m%d).json | python3 -m json.tool | head -40
tail -5 logs/audit.jsonl
```

## VenueRouter Mode Check

```bash
python3.11 -c "
import os
mode = os.environ.get('VENUE_ROUTER_MODE', 'kalshi_only')
poly = bool(os.environ.get('POLYMARKET_API_KEY', ''))
print(f'VENUE_ROUTER_MODE: {mode}')
print(f'Polymarket key present: {poly}')
if mode == 'best_price' and not poly:
    print('WARNING: best_price mode set but POLYMARKET_API_KEY not present — fallback to kalshi_only')
else:
    print('OK: VenueRouter config consistent')
"
```

## What To Look For in Output

- `status: "edge_found"` — model found a positive-edge market
- `status: "no_markets"` — no KXNBAPTS markets open today (normal on off-days)
- `status: "rejected"` — C4 phase gate rejected (expected; BOT_C4_ACTIVE not set)
- Any `"severity": "ERROR"` lines in audit.jsonl = investigate immediately
- Kill switch trigger signature in audit.jsonl = STOP and report

## T3 Manual Trigger (pre-tip scan)

After PIPE-02 has run and T1 report exists, can run T3 scan manually:
```bash
source .env
PYTHONPATH=src python3.11 src/prediction_market_bot/run_t3_pretip.py

# Check output:
cat logs/t3_$(date +%Y%m%d)_*.json | python3 -m json.tool | grep -E "momentum_signal|t3_edge|player_name"
```

Expected: CONFIRM / FADE / NEUTRAL signals per actionable player. No ERROR entries.
