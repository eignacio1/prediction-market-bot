"""EXPLORATORY (W110.1): fetch Open-Meteo Previous-Runs precipitation_previous_day1 at each 2021-25 REG kickoff hour.
Free API, same legality rule as the temp/wind fetch (lead >= 12h). Writes only via safe_out() -> precip_kickoff.json."""
from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
VW = HERE.parent / "20261011_nfl_totals_venue_weather"
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(VW))
from _fence import safe_out  # noqa: E402
from vw_features import LATLON, canon, forecast_lead_hours, kickoff_utc, T1_MIN_LEAD_H  # noqa: E402

URL = "https://previous-runs-api.open-meteo.com/v1/forecast"
VAR = "precipitation_previous_day1"


def get(lat, lon, d0, d1):
    q = dict(latitude=lat, longitude=lon, start_date=d0, end_date=d1, hourly=VAR, timezone="UTC")
    for i in range(6):
        try:
            with urllib.request.urlopen(URL + "?" + urllib.parse.urlencode(q), timeout=60) as r:
                return json.load(r)["hourly"]
        except Exception as e:  # noqa: BLE001
            print("retry", i, e, file=sys.stderr); time.sleep(10 * (i + 1))
    raise RuntimeError("fetch failed")


def main():
    g = pd.read_csv(sys.argv[1])
    g = g[(g.game_type == "REG") & (g.season >= 2021) & (g.season <= 2025)]
    out = {}
    for team, gg in g.groupby(g.home_team.map(canon)):
        h = get(*LATLON[team], gg.gameday.min(), gg.gameday.max())
        idx = {t: i for i, t in enumerate(h["time"])}
        for r in gg.itertuples():
            k = kickoff_utc(r.gameday, r.gametime)
            lead = forecast_lead_hours(k)
            if lead < T1_MIN_LEAD_H:
                raise ValueError(f"lead {lead}h < {T1_MIN_LEAD_H}h")
            i = idx.get(k.strftime("%Y-%m-%dT%H:00"))
            if i is not None:
                out[r.game_id] = {"precip_mm": h[VAR][i], "lead_h": lead}
        time.sleep(1)
    safe_out(HERE / "precip_kickoff.json").write_text(json.dumps(out))
    print("games", len(out), "null", sum(v["precip_mm"] is None for v in out.values()))


if __name__ == "__main__":
    main()
