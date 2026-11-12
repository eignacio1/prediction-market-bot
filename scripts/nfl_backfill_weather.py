"""W113.2 Part A: day-1-ahead forecast backfill (Open-Meteo Previous-Runs, free) for played outdoor/open-roof games.
Reach: wind/precip complete from 2024-02, so the 2024 season onward. Writes filter_data/nfl_weather_backfill.csv.
usage: python3 -E nfl_backfill_weather.py   (network; ~1-2 min)"""
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from prediction_market_bot.nfl_engine import weather_forecast as wf  # noqa: E402

D = ROOT / "src/prediction_market_bot/decision_trees/filter_data"
sch = pd.read_csv(D / "nfl_schedule.csv")
sch = sch[(sch.gameday >= wf.BACKFILL_FIRST_COMPLETE) & (~sch.roof.fillna("").isin(["dome", "closed"]))]
sch = sch[pd.to_datetime(sch.kickoff_utc) < pd.Timestamp.now(tz="UTC") - pd.Timedelta(hours=6)]
rows, miss = [], 0
for r in sch.itertuples():
    rec = wf.fetch_backfill(r.stadium_id, r.kickoff_utc)
    if rec is None:
        miss += 1
    else:
        rows.append({"stadium_id": r.stadium_id, "kickoff_utc": r.kickoff_utc, "issued_utc": rec["issued_utc"],
                     "lead_h": rec["lead_h"], "temp_f": rec["temp_f"], "wind_mph": rec["wind_mph"], "precip_mm": rec["precip_mm"]})
    time.sleep(0.25)
pd.DataFrame(rows).to_csv(D / "nfl_weather_backfill.csv", index=False)
print("games", len(sch), "ok", len(rows), "missing", miss)
