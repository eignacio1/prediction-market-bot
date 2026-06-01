# /hygiene — Pre-Commit Safety Check

Run all of the following. Report results. Do not proceed to any code commit, model deployment, or gate sign-off until all items are green.

## 1. Full Test Suite

```bash
cd "$(git rev-parse --show-toplevel)"
python -m pytest tests/ -v --tb=short 2>&1 | tail -20
```

Expected: all tests pass. Current baseline: 329/329.
If count drops, identify which test(s) failed and why before proceeding.

## 2. Temporal Integrity Spot Check

```bash
python3.11 -c "
import sys; sys.path.insert(0, 'src')
import pandas as pd
from prediction_market_bot.c2_feature_store.features import FeatureStore
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger
import logging
logger = logging.getLogger('hygiene')
fs = FeatureStore(logger=logger, snapshot_id='HYGIENE-CHECK')
print('FeatureStore FEATURE_VERSION:', fs.FEATURE_VERSION)
print('Feature names count:', len(fs.get_feature_names()))
print('TI-01 check: shift(1) present in source — verify manually in features.py ~line 200')
"
```

## 3. Secret Scan

```bash
# Ensure no secrets committed
grep -r "VENUE_API_KEY\s*=" src/ --include="*.py" | grep -v "os.environ" | grep -v "#"
grep -r "api_key\s*=\s*['\"]" src/ --include="*.py" | grep -v "os.environ"
grep -r "password\s*=\s*['\"]" src/ --include="*.py"
```

Expected: no output (zero matches). Any match = STOP immediately.

## 4. BOT_C4_ACTIVE Guard Check

```bash
grep -r "BOT_C4_ACTIVE" src/ --include="*.py"
```

Expected: only appears inside `os.environ.get(...)` checks — never set programmatically.

## 5. AuditLogger Kill Switch Check

```bash
grep -r "\.log\|\.info\|\.warning\|\.error\|\.critical" src/ --include="*.py" | grep -v "if " | grep -v "# " | head -20
```

Confirm: all AuditLogger calls have their return value checked (or are inside a component that triggers kill switch on False).

## 6. Execution Band + VenueRouter Integrity

```bash
python3 -c "
import sys; sys.path.insert(0, 'src')
from prediction_market_bot.execution_bands import BAND_CONFIGS, ExecutionBand, get_active_bands
from prediction_market_bot.c5_execution.venue_adapter import VenueAdapter, KalshiVenueAdapter
from unittest.mock import MagicMock
print('ExecutionBands loaded — bands:', [b.value for b in ExecutionBand])
active = get_active_bands()
print('Active (non-realtime) bands:', [c.band.value for c in active])
adapter = KalshiVenueAdapter(MagicMock())
assert isinstance(adapter, VenueAdapter), 'KalshiVenueAdapter does not satisfy VenueAdapter protocol'
print('VenueAdapter protocol: OK')
"
```

Expected: 5 bands defined; T1/T2/T3 in active list; VenueAdapter protocol satisfied.

## 7. Model File Integrity

```bash
python3.11 -c "
import joblib, json
model = joblib.load('models/prod_model.joblib')
meta = json.load(open('models/prod_model_meta.json'))
print(f'Model loaded OK: {meta[\"model_version\"]}')
print(f'Features in meta: {meta[\"feature_count\"]}')
print(f'Estimators: {type(model).__name__}')
"
```

## 8. MEMORY_BANK Staleness

Read `11_MEMORY_HANDOFF/MEMORY_BANK.md` header. Check:
- `Last reviewed` date — if older than today, update it
- `Confidence` — if < 8/10, flag for update
- `Current State Snapshot` — confirm gate history is current

## 9. TODO_NEXT Currency

Read `04_EXECUTION/TODO_NEXT.md`. Confirm:
- No tasks marked 🔲 NEXT that are now complete
- No tasks marked in-progress that are actually blocked

## Sign-Off Format

After all checks complete, report:

```
HYGIENE CHECK — [DATE]
Tests:          [N/N passing]   (baseline: 329/329)
Secrets:        [CLEAN / FAIL]
C4 guard:       [OK / FAIL]
Exec bands:     [OK / FAIL]     (T1–T5 defined; VenueAdapter protocol satisfied)
Model:          [version + age in days]
MEMORY_BANK:    [current / stale]
TODO_NEXT:      [current / stale]
RESULT:         [GREEN — safe to commit/deploy / RED — issues listed above]
```
