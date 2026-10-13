"""Point-in-time feature frame for the W69.3 projected-minutes challenger (12_EXPLORATORY; no order/registry imports)."""
from __future__ import annotations

import bisect
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, os.path.dirname(__file__))

from injury_parse import norm_name  # noqa: E402
from prediction_market_bot.c1_signal_ingestion import nba_ingest as N  # noqa: E402
from prediction_market_bot.c1_signal_ingestion import nba_player_ingest as P  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_player_features import FEATURE_NAMES, PlayerFeatureBuilder  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_pregame_features import _dt, et_date, et_midnight_utc  # noqa: E402

LEAD = timedelta(hours=4)       # snapshot must be published >= 4h before tip
ACTIVE_DAYS = 21                # teammate counts as "rotation" only if he played within this many days
BOX_EXTRA = ["min30", "min_rank"]
INJ_EXTRA = ["out_min", "out_fga", "own_quest", "own_prob", "inj_missing"]
ARMS = {"ctrl_refit": FEATURE_NAMES, "minutes_box": FEATURE_NAMES + BOX_EXTRA,
        "minutes_inj": FEATURE_NAMES + BOX_EXTRA + INJ_EXTRA}


def load_inj(inj_dir: str) -> dict[str, dict[str, dict[str, str]]]:
    out = {}
    for f in os.listdir(inj_dir):
        if f.startswith("inj_") and f.endswith(".json"):
            out[f[4:-5]] = json.load(open(os.path.join(inj_dir, f)))
    return out


def snapshot(inj: dict, game_start: datetime):
    """Latest report on the game's ET date whose slot (HH:30 ET) is <= tip - 4h. None if none exists."""
    d = et_date(game_start)
    day = inj.get(str(d))
    if not day:
        return None
    base = et_midnight_utc(d)
    best = None
    for slot in sorted(day):
        hh, mm = slot.split(":")
        t = base + timedelta(hours=int(hh), minutes=int(mm))
        if t <= game_start - LEAD:
            best = slot
    return day[best] if best else None


def status_of(snap: dict, name: str):
    """Exact normalized match, else token-subset (parser can leak a team name into the middle of an entry)."""
    n = norm_name(name)
    if n in snap:
        return snap[n]
    toks = n.split()
    if len(toks) < 2:
        return None
    first, last = toks[0], toks[-1]
    hits = [v for k, v in snap.items() if first in k.split() and last in k.split()]
    return hits[0] if len(hits) == 1 else None


def _recent(fb, pid, team, cutoff):
    seq, starts = fb._by_player.get(pid, []), fb._pstarts.get(pid, [])
    j = bisect.bisect_left(starts, cutoff)
    hist = seq[:j]
    if len(hist) < 10 or hist[-1][2]["team"] != team or (cutoff - hist[-1][0]).days > ACTIVE_DAYS:
        return None
    s10 = [r for _, _, r in hist[-10:]]
    return {"min10": sum(r["minutes"] for r in s10) / len(s10), "fga10": sum(r["fga"] for r in s10) / len(s10),
            "min30": sum(r["minutes"] for _, _, r in hist[-30:]) / len(hist[-30:])}


def build_frame(raw: Path, inj_dir: str, seasons=(2023, 2024, 2025, 2026)) -> list[dict]:
    games, stores = [], []
    for s in seasons:
        games += list(N.load_season(s, raw)["games"].values())
        stores.append(P.load_players(s, raw))
    fb = PlayerFeatureBuilder(games, stores)
    gmap = {g["game_id"]: g for g in games}
    inj = load_inj(inj_dir)
    rows, cov = [], {}
    for store in stores:
        for gid, rec in store["games"].items():
            g = gmap.get(gid)
            if g is None or g["season_type"] != 2:
                continue
            start = _dt(rec["start_time_utc"])
            cutoff = min(start, et_midnight_utc(et_date(start)))
            snap = snapshot(inj, start)
            cov.setdefault(g["season"], [0, 0])[0 if snap is not None else 1] += 1
            team_pool: dict[str, dict] = {}
            for r in rec["rows"]:
                team_pool.setdefault(r["team"], {}).setdefault(r["player_id"], r["name"])
            for r in rec["rows"]:
                if r["dnp"]:
                    continue
                opp = g["away"] if r["team"] == g["home"] else g["home"]
                out = fb.row(r["player_id"], r["team"], opp, r["home"], g["season"], start, start)
                if out is None:
                    continue
                f = dict(out["features"])
                mates = {}
                for tm, nm in _team_candidates(fb, r["team"], cutoff).items():
                    st = _recent(fb, tm, r["team"], cutoff)
                    if st:
                        mates[tm] = (nm, st)
                me = _recent(fb, r["player_id"], r["team"], cutoff)
                mins = sorted((v[1]["min10"] for v in mates.values()), reverse=True)
                m10 = f["min10"]
                f["min30"] = me["min30"] if me else m10
                f["min_rank"] = float(1 + sum(1 for x in mins if x > m10))
                f["inj_missing"] = 1.0 if snap is None else 0.0
                f["out_min"] = f["out_fga"] = f["own_quest"] = f["own_prob"] = 0.0
                if snap is not None:
                    for pid, (nm, st) in mates.items():
                        if pid == r["player_id"]:
                            continue
                        if status_of(snap, nm) in ("Out", "Doubtful"):
                            f["out_min"] += st["min10"]
                            f["out_fga"] += st["fga10"]
                    s_me = status_of(snap, r["name"])
                    f["own_quest"] = 1.0 if s_me in ("Questionable", "Doubtful") else 0.0
                    f["own_prob"] = 1.0 if s_me == "Probable" else 0.0
                rows.append({"season": g["season"], "game_id": gid, "player_id": r["player_id"],
                             "points": r["points"], **f})
    build_frame.coverage = cov
    return rows


_cand_cache: dict = {}


def _team_candidates(fb, team, cutoff):
    """Players whose latest prior appearance (before cutoff) was for ``team`` -- includes players now listed Out."""
    key = (team, cutoff)
    if key in _cand_cache:
        return _cand_cache[key]
    res = {}
    for pid, starts in fb._pstarts.items():
        j = bisect.bisect_left(starts, cutoff)
        if j:
            t, _, r = fb._by_player[pid][j - 1]
            if r["team"] == team and (cutoff - t).days <= ACTIVE_DAYS:
                res[pid] = r["name"]
    _cand_cache[key] = res
    return res
