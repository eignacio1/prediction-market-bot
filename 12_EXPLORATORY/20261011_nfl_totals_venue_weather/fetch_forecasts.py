"""EXPLORATORY: fetch Open-Meteo Previous-Runs *_previous_day1 forecasts at each 2021-25 REG kickoff hour. Free API.

Writes only via safe_out() -> forecast_kickoff.json (game_id -> temp_f, wind_mph, lead_h).
"""
from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
from _fence import safe_out  # noqa: E402
from vw_features import FCST_VARS, LATLON, assert_forecast_legal, canon, forecast_lead_hours, kickoff_utc  # noqa: E402

URL = "https://previous-runs-api.open-meteo.com/v1/forecast"


def get(lat, lon, d0, d1):
    q = dict(latitude=lat, longitude=lon, start_date=d0, end_date=d1, hourly=",".join(FCST_VARS),
             temperature_unit="fahrenheit", wind_speed_unit="mph", timezone="UTC")
    for i in range(6):
        try:
            with urllib.request.urlopen(URL + "?" + urllib.parse.urlencode(q), timeout=60) as r:
                return json.load(r)["hourly"]
        except Exception as e:  # noqa: BLE001
            print("retry", i, e, file=sys.stderr); time.sleep(10 * (i + 1))
    raise RuntimeError("fetch failed")


def main():
    ext = pd.read_parquet(sys.argv[1])
    ext = ext[(ext.game_type == "REG") & (ext.season >= 2021) & (ext.season <= 2025)]
    out = {}
    for team, g in ext.groupby(ext.home_team.map(canon)):
        h = get(*LATLON[team], g.gameday.min(), g.gameday.max())
        idx = {t: i for i, t in enumerate(h["time"])}
        for r in g.itertuples():
            k = kickoff_utc(r.gameday, r.gametime)
            lead = forecast_lead_hours(k)
            for v in FCST_VARS:
                assert_forecast_legal(v, lead)
            i = idx.get(k.strftime("%Y-%m-%dT%H:00"))
            if i is None:
                continue
            out[r.game_id] = {"temp_f": h[FCST_VARS[0]][i], "wind_mph": h[FCST_VARS[1]][i], "lead_h": lead}
        print(team, len(out), file=sys.stderr); time.sleep(1)
    safe_out(HERE / "forecast_kickoff.json").write_text(json.dumps(out))
    print("games", len(out), "null temp", sum(v["temp_f"] is None for v in out.values()))


if __name__ == "__main__":
    main()
