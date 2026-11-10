"""W106.4: the market's last pre-game line for MLB games, from the read-only Kalshi price archive.

Applies: KXMLBGAME (moneyline, two contracts per game) and KXMLBTOTAL (ladder; suffix k means total >= k, i.e. 'over k-0.5').
Does not apply: KXMLBSPREAD (contract semantics unverified here - skipped), fills (a mid is not a tradable price: the
half-spread is carried so the caller can say how wide the market was), postseason (not in the model's store).
Ticker: KX..-26SEP101905COLNYY-NYY  = YY MON DD HHMM(US Eastern, local first pitch) AWAY(3) HOME - side.
"""
from __future__ import annotations

import glob
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Optional, Tuple

import pandas as pd

MONTHS = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}
_EVENT = re.compile(r"^KX(?:MLBGAME|MLBTOTAL)-(\d\d)([A-Z]{3})(\d\d)(\d{4})([A-Z]+)$")
_TEAMS = ("ATH ATL AZ BAL BOS CHC CIN CLE COL CWS DET HOU KC LAA LAD MIA MIL MIN NYM NYY PHI PIT SD SEA SF STL TB TEX TOR TWS WSH").split()


def _split_teams(s: str) -> Optional[Tuple[str, str]]:
    for a in _TEAMS:
        if s.startswith(a) and s[len(a):] in _TEAMS:
            return a, s[len(a):]
    return None


def _et_offset_hours(d: datetime) -> int:
    """US Eastern offset from UTC (hours, positive): DST 2026-03-08 .. 2026-11-01 (the archive years only)."""
    return 4 if datetime(2026, 3, 8) <= d.replace(tzinfo=None) < datetime(2026, 11, 1) else 5


def parse_event(event_ticker: str) -> Optional[dict]:
    m = _EVENT.match(event_ticker)
    if not m:
        return None
    yy, mon, dd, hhmm, tm = m.groups()
    tt = _split_teams(tm)
    if mon not in MONTHS or not tt:
        return None
    local = datetime(2000 + int(yy), MONTHS[mon], int(dd), int(hhmm[:2]), int(hhmm[2:]))
    start = (local + timedelta(hours=_et_offset_hours(local))).replace(tzinfo=timezone.utc)
    return {"game_date": pd.Timestamp(local.date()), "start_utc": start, "away": tt[0], "home": tt[1]}


def last_pregame(archive_glob: str, cutoff_min: int = 10, series=("KXMLBGAME", "KXMLBTOTAL")) -> pd.DataFrame:
    """Per contract, the latest snapshot at least `cutoff_min` minutes before first pitch (never after)."""
    best: Dict[str, dict] = {}
    for f in sorted(glob.glob(archive_glob)):
        with open(f) as fh:
            for line in fh:
                if not any(s in line for s in series):
                    continue
                r = json.loads(line)
                if r.get("series_ticker") not in series:
                    continue
                ev = parse_event(r["event_ticker"])
                if ev is None:
                    continue
                ts = datetime.strptime(r["run_ts"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                if ts > ev["start_utc"] - timedelta(minutes=cutoff_min):
                    continue
                cur = best.get(r["ticker"])
                if cur is None or ts > cur["ts"]:
                    best[r["ticker"]] = {"ts": ts, "series": r["series_ticker"], "event": r["event_ticker"],
                                         "ticker": r["ticker"], "side": r["ticker"].rsplit("-", 1)[1],
                                         "bid": float(r["yes_bid"]), "ask": float(r["yes_ask"]),
                                         "volume": float(r.get("volume") or 0.0), **ev}
    return pd.DataFrame(best.values())


def moneyline(c: pd.DataFrame, max_half_spread: float = 1.0) -> pd.DataFrame:
    """One row per game: p_home_mkt = mid(home)/(mid(home)+mid(away)) (overround removed), half-spread, age."""
    g = c[c.series == "KXMLBGAME"].copy()
    g["mid"] = (g.bid + g.ask) / 2
    g["hs"] = (g.ask - g.bid) / 2
    rows = []
    for ev, x in g.groupby("event"):
        h, a = x[x.side == x.home.iloc[0]], x[x.side == x.away.iloc[0]]
        if len(h) != 1 or len(a) != 1 or (h.mid.iloc[0] + a.mid.iloc[0]) <= 0:
            continue
        hs = max(h.hs.iloc[0], a.hs.iloc[0])
        if hs > max_half_spread:
            continue
        rows.append({"event": ev, "game_date": x.game_date.iloc[0], "home": x.home.iloc[0], "away": x.away.iloc[0],
                     "p_home_mkt": h.mid.iloc[0] / (h.mid.iloc[0] + a.mid.iloc[0]), "half_spread": hs,
                     "volume": x.volume.sum(), "ts": min(h.ts.iloc[0], a.ts.iloc[0])})
    return pd.DataFrame(rows)


def total_rung(c: pd.DataFrame, max_half_spread: float = 1.0) -> pd.DataFrame:
    """One row per game: the ladder rung k whose mid is closest to 0.5; p_mkt = P(total >= k)."""
    t = c[c.series == "KXMLBTOTAL"].copy()
    t["k"] = t.side.astype(int)
    t["mid"] = (t.bid + t.ask) / 2
    t["hs"] = (t.ask - t.bid) / 2
    rows = []
    for ev, x in t.groupby("event"):
        x = x[x.hs <= max_half_spread]
        if len(x) < 3:
            continue
        r = x.iloc[(x.mid - 0.5).abs().argsort().iloc[0]]
        rows.append({"event": ev, "game_date": r.game_date, "home": r.home, "away": r.away, "k": int(r.k),
                     "p_mkt": float(r.mid), "half_spread": float(r.hs), "volume": float(r.volume), "ts": r.ts})
    return pd.DataFrame(rows)
