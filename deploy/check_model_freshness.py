"""Weekly model freshness check — called by cron Monday 14:00 UTC."""
import json, sys
from datetime import datetime, timezone
from pathlib import Path

meta_path = Path("models/prod_model_meta.json")
if not meta_path.exists():
    print("WARNING: prod_model_meta.json not found — model may not be trained")
    sys.exit(0)

m = json.loads(meta_path.read_text())
trained = datetime.fromisoformat(m["trained_at"].replace("Z", "+00:00"))
age_days = (datetime.now(timezone.utc) - trained).days
print(f"Model age: {age_days} days (trained {m['trained_at']})")
if age_days > 30:
    print("WARNING: Model is >30 days old — consider retraining")
    sys.exit(1)
