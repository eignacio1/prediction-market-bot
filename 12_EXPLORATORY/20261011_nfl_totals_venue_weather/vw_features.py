"""EXPLORATORY point-in-time venue + weather features for the NFL totals challenger (W68.3). Pre-2026 only.

Every value is computed from information available at kickoff minus the T1 horizon (>=12h):
  * stadium indoor/turf share: ONLY the home team's prior home games (gameday strictly earlier).
  * forecast wind/temp: Open-Meteo Previous-Runs `*_previous_day1` (model run issued the day before; lead >= 24h).
  * observed nflverse temp/wind: NOT point-in-time -- used only by the flagged upper-bound arm.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pandas as pd

WINDOW = 24            # prior home games used for stadium category
T1_MIN_LEAD_H = 12.0   # forecast must be issued at least this long before kickoff
FCST_VARS = ("temperature_2m_previous_day1", "wind_speed_10m_previous_day1")
FCST_LEAD_H = 24.0     # minimum lead of a *_previous_day1 value (run of the prior UTC day)

LATLON = {
    "ARI": (33.5276, -112.2626), "ATL": (33.7554, -84.4008), "BAL": (39.2780, -76.6227), "BUF": (42.7738, -78.7870),
    "CAR": (35.2258, -80.8528), "CHI": (41.8623, -87.6167), "CIN": (39.0954, -84.5160), "CLE": (41.5061, -81.6995),
    "DAL": (32.7473, -97.0945), "DEN": (39.7439, -105.0201), "DET": (42.3400, -83.0456), "GB": (44.5013, -88.0622),
    "HOU": (29.6847, -95.4107), "IND": (39.7601, -86.1639), "JAX": (30.3239, -81.6373), "KC": (39.0489, -94.4839),
    "LA": (33.9535, -118.3392), "LAC": (33.9535, -118.3392), "LV": (36.0909, -115.1833), "MIA": (25.9580, -80.2389),
    "MIN": (44.9738, -93.2577), "NE": (42.0909, -71.2643), "NO": (29.9511, -90.0812), "NYG": (40.8135, -74.0745),
    "NYJ": (40.8135, -74.0745), "PHI": (39.9008, -75.1675), "PIT": (40.4468, -80.0158), "SEA": (47.5952, -122.3316),
    "SF": (37.4030, -121.9700), "TB": (27.9759, -82.5033), "TEN": (36.1665, -86.7713), "WAS": (38.9076, -76.8645),
}
ALIAS = {"OAK": "LV", "SD": "LAC", "STL": "LA", "WSH": "WAS", "LAR": "LA"}


def canon(t: str) -> str:
    return ALIAS.get(t, t)


def kickoff_utc(gameday: str, gametime: str) -> datetime:
    y, m, d = map(int, str(gameday).split("-"))
    hh, mm = map(int, str(gametime).split(":")[:2])
    return datetime(y, m, d, hh, mm, tzinfo=ZoneInfo("America/New_York")).astimezone(timezone.utc)


def _is_indoor(roof) -> float | None:
    if roof is None or (isinstance(roof, float) and math.isnan(roof)):
        return None
    return 1.0 if roof in ("dome", "closed") else 0.0


def _is_turf(surface) -> float | None:
    if surface is None or (isinstance(surface, float) and math.isnan(surface)):
        return None
    s = str(surface).strip().lower()
    return 0.0 if "grass" in s else 1.0


def stadium_category(ext: pd.DataFrame, home: str, gameday: str, window: int = WINDOW) -> dict:
    """Indoor share and turf share over the home team's prior home games, strictly before `gameday`."""
    h = canon(home)
    past = ext[(ext.home_team.map(canon) == h) & (ext.gameday.astype(str) < str(gameday))].sort_values("gameday").tail(window)
    ind = [v for v in (_is_indoor(r) for r in past.roof) if v is not None]
    trf = [v for v in (_is_turf(s) for s in past.surface) if v is not None]
    return {"p_indoor": sum(ind) / len(ind) if ind else 0.0, "p_turf": sum(trf) / len(trf) if trf else 0.0, "n_prior": len(past)}


def weather_effects(p_indoor: float, wind_mph, temp_f) -> dict:
    """Exposure-scaled weather. Missing weather -> zero effect (documented imputation)."""
    out = 1.0 - p_indoor
    w = 0.0 if wind_mph is None or pd.isna(wind_mph) else float(wind_mph)
    t = None if temp_f is None or pd.isna(temp_f) else float(temp_f)
    return {"wind_eff": w * out, "cold_eff": (max(0.0, 55.0 - t) if t is not None else 0.0) * out,
            "has_wx": float(t is not None)}


def assert_forecast_legal(var: str, lead_h: float) -> None:
    """Look-ahead guard: only previous-day forecast columns, and only at a lead >= T1 minimum horizon."""
    if var not in FCST_VARS:
        raise ValueError(f"not a point-in-time forecast column: {var}")
    if lead_h < T1_MIN_LEAD_H:
        raise ValueError(f"forecast lead {lead_h}h < T1 horizon {T1_MIN_LEAD_H}h")


def forecast_lead_hours(kick: datetime) -> float:
    """Minimum lead of a *_previous_day1 value for the kickoff hour: run is 00Z of the prior UTC day."""
    run = datetime(kick.year, kick.month, kick.day, tzinfo=timezone.utc) - pd.Timedelta(days=1)
    return (kick - run).total_seconds() // 3600.0
