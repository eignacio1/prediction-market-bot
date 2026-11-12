"""NFL weather FORECAST store, point-in-time (W113.2, B-089). Factor N14 in SEATS/nfl.toml.

The 110.1 weather filter was fitted on realised conditions. This module supplies what was knowable BEFORE kickoff:
a free Open-Meteo forecast for the stadium at the kickoff hour, stamped with the time it was captured (`issued_utc`).

Two kinds of record, never mixed silently (`kind` field):
  * "live"     -- captured by the shadow cron's provider at row time; issued_utc = capture time; lead_h real.
  * "backfill" -- Open-Meteo Previous-Runs API, the forecast issued ~1 day before kickoff (`*_previous_day1`).
                  Complete for wind/precip only from ~2024-02 (temperature earlier). TRAINING / SCORING use only:
                  the issue time is nominal (kickoff - 24h), not a captured timestamp.
Open-Meteo is free and keyless ($0). Indoor stadiums (dome/closed) need no fetch: exposure is zero.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Tuple

from .weather_factor import WeatherContext

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
PREVIOUS_RUNS_URL = "https://previous-runs-api.open-meteo.com/v1/forecast"
HOURLY = "temperature_2m,wind_speed_10m,precipitation"
HORIZON_H = 16 * 24          # Open-Meteo forecasts reach 16 days; beyond that there is nothing to capture
BACKFILL_FIRST_COMPLETE = "2024-02-01"   # day-1 wind/precip are null before this

# nflverse stadium_id -> (lat, lon). Hand-written; ~city-level is enough for an hourly forecast.
STADIUMS = {
    "ATL97": (33.755, -84.401), "BAL00": (39.278, -76.623), "BOS00": (42.091, -71.264), "BUF00": (42.774, -78.787),
    "CAR00": (35.226, -80.853), "CHI98": (41.862, -87.617), "CIN00": (39.095, -84.516), "CLE00": (41.506, -81.700),
    "DAL00": (32.748, -97.093), "DEN00": (39.744, -105.020), "DET00": (42.340, -83.046), "FRA00": (50.069, 8.645),
    "GER00": (48.218, 11.624), "GNB00": (44.501, -88.062), "HOU00": (29.685, -95.411), "IND00": (39.760, -86.164),
    "JAX00": (30.324, -81.637), "KAN00": (39.049, -94.484), "LAX01": (33.953, -118.339), "LON00": (51.556, -0.280),
    "LON02": (51.604, -0.066), "MAD01": (40.453, -3.688), "MEL00": (-37.820, 144.983), "MEX00": (19.303, -99.151),
    "MIA00": (25.958, -80.239), "MIN01": (44.974, -93.258), "MUN01": (48.218, 11.624), "NAS00": (36.166, -86.771),
    "NOR00": (29.951, -90.081), "NYC01": (40.814, -74.074), "PAR00": (48.924, 2.360), "PHI00": (39.901, -75.167),
    "PHO00": (33.528, -112.263), "PIT00": (40.447, -80.016), "RIO00": (-22.912, -43.230), "SAO00": (-23.545, -46.474),
    "SEA00": (47.595, -122.332), "SFO01": (37.403, -121.970), "TAM00": (27.976, -82.503), "VEG00": (36.091, -115.184),
    "WAS00": (38.908, -76.865),
}

DEFAULT_STORE = Path("exp_output/NFL_WEATHER/forecast_captures.jsonl")
BACKFILL_CSV = Path(__file__).resolve().parents[1] / "decision_trees" / "filter_data" / "nfl_weather_backfill.csv"


def _utc(ts) -> datetime:
    if isinstance(ts, datetime):
        return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(str(ts).replace("Z", "+00:00")).astimezone(timezone.utc)


def _pick_hour(payload: dict, kickoff: datetime, suffix: str = "") -> Optional[dict]:
    h = payload.get("hourly") or {}
    times = h.get("time") or []
    key = kickoff.strftime("%Y-%m-%dT%H:00")
    if key not in times:
        return None
    i = times.index(key)
    g = lambda n: (h.get(n + suffix) or [None] * len(times))[i]   # noqa: E731
    t, w, p = g("temperature_2m"), g("wind_speed_10m"), g("precipitation")
    return {"temp_f": t, "wind_mph": w, "precip_mm": p}


def fetch_forecast(stadium_id: str, kickoff, *, timeout: float = 6.0, now: Optional[datetime] = None) -> Optional[dict]:
    """Live forecast for the kickoff hour; None when out of horizon / unreachable. Stamps issued_utc at capture."""
    import requests

    ko = _utc(kickoff)
    now = now or datetime.now(timezone.utc)
    if stadium_id not in STADIUMS or ko <= now or (ko - now).total_seconds() > HORIZON_H * 3600:
        return None
    lat, lon = STADIUMS[stadium_id]
    try:
        r = requests.get(FORECAST_URL, timeout=timeout, params={
            "latitude": lat, "longitude": lon, "hourly": HOURLY, "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph", "precipitation_unit": "mm", "timezone": "UTC", "forecast_days": 16})
        r.raise_for_status()
        got = _pick_hour(r.json(), ko)
    except Exception:  # noqa: BLE001 - weather is optional; the row records it as unavailable
        return None
    if not got:
        return None
    issued = datetime.now(timezone.utc)
    return {"kind": "live", "stadium_id": stadium_id, "kickoff_utc": ko.isoformat(), "issued_utc": issued.isoformat(),
            "lead_h": round((ko - issued).total_seconds() / 3600, 3), **got}


def fetch_backfill(stadium_id: str, kickoff, *, timeout: float = 20.0) -> Optional[dict]:
    """Day-1-ahead forecast for a PAST kickoff (Previous-Runs API). Nominal issue = kickoff - 24h. Training only."""
    import requests

    ko = _utc(kickoff)
    if stadium_id not in STADIUMS:
        return None
    lat, lon = STADIUMS[stadium_id]
    d = ko.strftime("%Y-%m-%d")
    hv = ",".join(f"{v}_previous_day1" for v in HOURLY.split(","))
    try:
        r = requests.get(PREVIOUS_RUNS_URL, timeout=timeout, params={
            "latitude": lat, "longitude": lon, "hourly": hv, "start_date": d, "end_date": d,
            "temperature_unit": "fahrenheit", "wind_speed_unit": "mph", "precipitation_unit": "mm", "timezone": "UTC"})
        r.raise_for_status()
        got = _pick_hour(r.json(), ko, "_previous_day1")
    except Exception:  # noqa: BLE001
        return None
    if not got or all(v is None for v in got.values()):
        return None
    issued = ko - timedelta(hours=24)
    return {"kind": "backfill", "stadium_id": stadium_id, "kickoff_utc": ko.isoformat(), "issued_utc": issued.isoformat(),
            "lead_h": 24.0, **got}


def append_capture(rec: dict, store: Path = DEFAULT_STORE) -> None:
    store.parent.mkdir(parents=True, exist_ok=True)
    with open(store, "a") as f:
        f.write(json.dumps(rec) + "\n")


def read_captures(store: Path = DEFAULT_STORE) -> list:
    if not store.exists():
        return []
    return [json.loads(x) for x in store.read_text().splitlines() if x.strip()]


def latest_before(captures: list, stadium_id: str, kickoff, as_of) -> Optional[dict]:
    """Latest capture for this game issued at or before `as_of` (point-in-time read)."""
    ko, t = _utc(kickoff).isoformat(), _utc(as_of)
    c = [r for r in captures if r["stadium_id"] == stadium_id and r["kickoff_utc"] == ko and _utc(r["issued_utc"]) <= t]
    return max(c, key=lambda r: r["issued_utc"]) if c else None


def to_context(rec: Optional[dict], roof: Optional[str]) -> Tuple[WeatherContext, Optional[str]]:
    """Capture -> (WeatherContext, issued_utc). No capture -> source 'none' (leaf 'unknown')."""
    if rec is None:
        return WeatherContext("none", roof), None
    return WeatherContext("forecast", roof, rec.get("temp_f"), rec.get("wind_mph"), rec.get("precip_mm"),
                          rec.get("lead_h")), rec["issued_utc"]


class CachedForecaster:
    """Live provider helper: one fetch per (stadium, kickoff) per `ttl_s`, every fetch appended to the store."""

    def __init__(self, store: Path = DEFAULT_STORE, ttl_s: float = 3 * 3600, fetch=fetch_forecast):
        self.store, self.ttl_s, self._fetch = store, ttl_s, fetch
        self._last: dict = {}

    def get(self, stadium_id: str, kickoff) -> Optional[dict]:
        key = (stadium_id, _utc(kickoff).isoformat())
        hit = self._last.get(key)
        if hit and time.time() - hit[0] < self.ttl_s:
            return hit[1]
        rec = self._fetch(stadium_id, kickoff)
        if rec:
            append_capture(rec, self.store)
        self._last[key] = (time.time(), rec)
        return rec
