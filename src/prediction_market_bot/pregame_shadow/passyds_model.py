"""W81.3 KXNFLPASSYDS strike model: starting-QB availability + QB-vs-defense matchup -> a passing-yards distribution per
QB-game -> P(passing yards >= strike). One feature code path serves both the fit (12_EXPLORATORY/thin_markets/passyds) and
the live shadow rows, so what was validated is what runs. Frozen: the artifact (models/passyds_strike_v1.json) carries its
sha256 in models/passyds_strike_v1.sha256 and is verified on load (Hard Rule 4). No market price enters the model.

Inputs are nflverse player-week stats and the nflverse schedule (free, public). Every feature uses only games strictly
before the target game (point in time)."""
from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

MIN_ATT = 15          # a QB-game counts as a start/primary-passer game at >= 15 attempts
HALFLIFE = 6.0        # games, exponential weighting
SHRINK_K = 4.0        # pseudo-games toward the league prior
MIN_PRIOR_STARTS = 3  # fewer -> cold start, no forecast (availability/role not established)
FEATURES = ("qb_shrunk", "opp_dev", "home")


def norm_name(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\b(jr|sr|ii|iii|iv)\b\.?", "", s)
    return re.sub(r"[^a-z ]", "", s).strip()


def _ew(vals: np.ndarray) -> tuple[float, float]:
    """(weighted mean, effective weight) of vals ordered oldest->newest, newest weighted most."""
    n = len(vals)
    w = 0.5 ** (np.arange(n - 1, -1, -1) / HALFLIFE)
    return float((w * vals).sum() / w.sum()), float(w.sum())


def _shrunk(vals: np.ndarray, prior: float) -> float:
    if len(vals) == 0:
        return prior
    m, we = _ew(vals)
    return (we * m + SHRINK_K * prior) / (we + SHRINK_K)


def qb_games(week_stats: pd.DataFrame, sched: pd.DataFrame) -> pd.DataFrame:
    """One row per QB-game (attempts >= MIN_ATT): who, team, opponent, date, yards, home flag."""
    q = week_stats[(week_stats["position"] == "QB") & (week_stats["attempts"] >= MIN_ATT)].copy()
    g = sched[["game_id", "gameday", "home_team"]].copy()
    q = q.merge(g, on="game_id", how="left")
    q["gameday"] = pd.to_datetime(q["gameday"])
    q["home"] = (q["team"] == q["home_team"]).astype(float)
    q["name_key"] = q["player_display_name"].map(norm_name)
    return q[["player_id", "name_key", "team", "opponent_team", "season", "week", "game_id", "gameday", "home",
              "passing_yards", "attempts"]].sort_values("gameday").reset_index(drop=True)


def defense_games(week_stats: pd.DataFrame, sched: pd.DataFrame) -> pd.DataFrame:
    """Passing yards each defense allowed per game (sum over the opposing QBs' passing, all QBs)."""
    q = week_stats[week_stats["position"] == "QB"]
    d = q.groupby(["game_id", "opponent_team"], as_index=False)["passing_yards"].sum()
    d = d.merge(sched[["game_id", "gameday"]], on="game_id", how="left")
    d["gameday"] = pd.to_datetime(d["gameday"])
    return d.sort_values("gameday").reset_index(drop=True)


def league_priors(qg: pd.DataFrame, dg: pd.DataFrame, before: pd.Timestamp) -> tuple[float, float]:
    return (float(qg.loc[qg["gameday"] < before, "passing_yards"].mean()),
            float(dg.loc[dg["gameday"] < before, "passing_yards"].mean()))


def features_for(qg: pd.DataFrame, dg: pd.DataFrame, key: str, team_opp: str, home: float, when: pd.Timestamp,
                 prior_q: float, prior_d: float) -> Optional[dict]:
    """Point-in-time features for one QB facing `team_opp` at `when`, or None on cold start."""
    hist = qg[(qg["name_key"] == key) & (qg["gameday"] < when)]
    if len(hist) < MIN_PRIOR_STARTS:
        return None
    dh = dg[(dg["opponent_team"] == team_opp) & (dg["gameday"] < when)]
    qb_s = _shrunk(hist["passing_yards"].to_numpy(float), prior_q)
    opp_s = _shrunk(dh["passing_yards"].to_numpy(float), prior_d)
    return {"qb_shrunk": qb_s, "opp_dev": opp_s - prior_d, "home": float(home),
            "n_prior_starts": int(len(hist)), "n_def_games": int(len(dh)),
            "qb_last_game": str(hist["gameday"].iloc[-1].date()),
            "def_last_game": str(dh["gameday"].iloc[-1].date()) if len(dh) else None}


def _phi(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


class StrikeModel:
    def __init__(self, art: dict):
        self.art = art
        self.coef = art["coef"]
        self.sigma_c = art["sigma_c"]

    def mean(self, f: dict) -> float:
        c = self.coef
        return c["intercept"] + sum(c[k] * f[k] for k in FEATURES)

    def p_ge(self, f: dict, strike: float) -> float:
        """P(passing_yards >= strike): integer yards, continuity-corrected normal with sd proportional to the mean."""
        mu = max(self.mean(f), 50.0)
        sd = self.sigma_c * mu
        k = math.ceil(strike - 1e-9)
        return min(max(1.0 - _phi((k - 0.5 - mu) / sd), 0.0), 1.0)


def fit(qg: pd.DataFrame, dg: pd.DataFrame, train_end: pd.Timestamp, min_date: pd.Timestamp) -> dict:
    """OLS of yards on the three features over QB-games in [min_date, train_end), features built point-in-time."""
    rows = []
    for r in qg[(qg["gameday"] >= min_date) & (qg["gameday"] < train_end)].itertuples():
        pq, pd_ = league_priors(qg, dg, r.gameday)
        f = features_for(qg, dg, r.name_key, r.opponent_team, r.home, r.gameday, pq, pd_)
        if f is not None:
            rows.append(([1.0] + [f[k] for k in FEATURES], r.passing_yards))
    X = np.array([a for a, _ in rows]); y = np.array([b for _, b in rows], float)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    sigma_c = float(np.std(resid / np.maximum(X @ beta, 50.0)))
    return {"coef": {"intercept": float(beta[0]), **{k: float(b) for k, b in zip(FEATURES, beta[1:])}},
            "sigma_c": sigma_c, "n_train": int(len(y))}


def sha256_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_frozen(models_dir: Path) -> tuple[StrikeModel, str]:
    """Load models/passyds_strike_v1.json, refusing if its bytes do not match the committed sha256."""
    art_p = Path(models_dir) / "passyds_strike_v1.json"
    want = (Path(models_dir) / "passyds_strike_v1.sha256").read_text().split()[0]
    got = sha256_file(art_p)
    if got != want:
        raise RuntimeError(f"passyds_strike_v1 artifact hash mismatch: {got} != {want}")
    return StrikeModel(json.loads(art_p.read_text())), got


def baseline_p_ge(qg: pd.DataFrame, key: str, when: pd.Timestamp, season: int, strike: float, pooled_sd: float,
                  prior_q: float) -> Optional[float]:
    """Naive comparator: the QB's same-season average to date (prior-season average when the season is new),
    pooled sd, normal. Used only by the sanity gate."""
    h = qg[(qg["name_key"] == key) & (qg["gameday"] < when)]
    cur = h[h["season"] == season]
    base = cur if len(cur) >= 1 else h[h["season"] == season - 1]
    if len(base) == 0:
        return None
    mu = float(base["passing_yards"].mean())
    return min(max(1.0 - _phi((math.ceil(strike - 1e-9) - 0.5 - mu) / pooled_sd), 0.0), 1.0)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------- runtime (shadow rows) ----------------------------
_BASE = "https://github.com/nflverse/nflverse-data/releases/download"
_OUT_STATUSES = {"out", "doubtful", "injured reserve", "suspended", "pup"}
_EVENT_RE = re.compile(r"^KXNFLPASSYDS-(\d{2})([A-Z]{3})(\d{2})([A-Z]+)$")
_NULL = {"model_p": None, "model_id": None, "model_sha256": None, "factor_inputs": None, "factor_as_of": None}
_RT: Optional["Runtime"] = None


def _fetch(url: str, dest: Path, max_age_s: Optional[float]) -> Path:
    import time
    import urllib.request
    if dest.exists() and (max_age_s is None or time.time() - dest.stat().st_mtime < max_age_s):
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".part")
    with urllib.request.urlopen(url, timeout=60) as r:
        tmp.write_bytes(r.read())
    tmp.replace(dest)
    return dest


def _teams_from_event(event: str) -> Optional[tuple[str, str]]:
    """(away, home) in nflverse codes from KXNFLPASSYDS-26OCT22NECHI."""
    from prediction_market_bot.pregame_shadow.nfl_forecaster import KALSHI_CODES, kalshi_to_nflverse
    m = _EVENT_RE.match(event or "")
    if not m:
        return None
    t = m.group(4)
    for i in (2, 3):
        a, h = t[:i], t[i:]
        if a in KALSHI_CODES and h in KALSHI_CODES:
            return kalshi_to_nflverse(a), kalshi_to_nflverse(h)
    return None


class Runtime:
    def __init__(self, root: Path, models_dir: Path, now: datetime):
        self.model, self.sha = load_frozen(models_dir)
        cache = Path(root) / "exp_output" / "NFL" / "passyds_cache"
        season = now.year if now.month >= 3 else now.year - 1
        frames = []
        for y in range(2018, season + 1):
            p = _fetch(f"{_BASE}/stats_player/stats_player_week_{y}.parquet", cache / f"w{y}.parquet",
                       21600.0 if y == season else None)
            frames.append(pd.read_parquet(p))
        ws = pd.concat(frames, ignore_index=True)
        ws = ws[ws["season_type"] == "REG"]
        sp = _fetch(f"{_BASE}/schedules/games.parquet", cache / "games.parquet", 21600.0)
        self.sched = pd.read_parquet(sp)
        self.qg, self.dg = qb_games(ws, self.sched), defense_games(ws, self.sched)
        self.inj = self._injuries(Path(root))

    @staticmethod
    def _injuries(root: Path) -> list:
        p = root / "exp_output" / "NFL" / "INJURY_SNAPSHOTS" / "snapshots.jsonl"
        try:
            last = p.read_text().strip().splitlines()[-1]
            d = json.loads(last)
            return [{**r, "_captured_utc": d.get("captured_utc")} for r in d.get("rows", []) if r.get("is_qb")]
        except Exception:
            return []

    def fields(self, m: dict, now: datetime) -> dict:
        teams = _teams_from_event(m.get("event_ticker", ""))
        name = (m.get("no_sub_title") or m.get("yes_sub_title") or "").split(":")[0].strip()
        strike = m.get("floor_strike")
        if teams is None or not name or strike is None:
            return {**_NULL, "model_status": "unparsed_market"}
        away, home = teams
        key = norm_name(name)
        when = pd.Timestamp(now.date())
        hist = self.qg[(self.qg["name_key"] == key) & (self.qg["gameday"] < when)]
        if len(hist) < MIN_PRIOR_STARTS:
            return {**_NULL, "model_status": "cold_start", "factor_inputs": {"n_prior_starts": int(len(hist))}}
        team = hist["team"].iloc[-1]
        if team not in (away, home):
            return {**_NULL, "model_status": "team_mismatch"}
        opp = home if team == away else away
        inj = [r for r in self.inj if norm_name(r.get("name", "")) == key]
        status = (inj[0].get("status") or "").lower() if inj else None
        if status in _OUT_STATUSES:
            return {**_NULL, "model_status": "qb_unavailable",
                    "factor_inputs": {"injury_status": inj[0].get("status")},
                    "factor_as_of": {"injury_snapshot_utc": inj[0].get("_captured_utc")}}
        pq, pd_ = league_priors(self.qg, self.dg, when)
        f = features_for(self.qg, self.dg, key, opp, 1.0 if team == home else 0.0, when, pq, pd_)
        if f is None:
            return {**_NULL, "model_status": "cold_start"}
        last_passer = self.qg[(self.qg["team"] == team) & (self.qg["gameday"] < when)]["name_key"].iloc[-1]
        p = self.model.p_ge(f, float(strike))
        return {"model_p": round(p, 6), "model_id": "passyds_strike_v1", "model_sha256": self.sha,
                "model_status": "ok", "model_mu": round(self.model.mean(f), 2),
                "factor_inputs": {"qb_shrunk": round(f["qb_shrunk"], 2), "opp_dev": round(f["opp_dev"], 2),
                                  "home": f["home"], "n_prior_starts": f["n_prior_starts"],
                                  "n_def_games": f["n_def_games"], "qb_team": team, "opp": opp,
                                  "injury_status": inj[0].get("status") if inj else None,
                                  "is_last_team_passer": last_passer == key},
                "factor_as_of": {"qb_last_game": f["qb_last_game"], "def_last_game": f["def_last_game"],
                                 "features_before": str(when.date()),
                                 "injury_snapshot_utc": inj[0].get("_captured_utc") if inj else None}}


def model_fields(m: dict, now: datetime, root: Optional[Path] = None) -> dict:
    """Hook for scripts/passyds_prekickoff_snapshot.py. Never raises; no market price is read."""
    global _RT
    try:
        if _RT is None:
            r = Path(root) if root else Path(__file__).resolve().parents[3]
            _RT = Runtime(r, r / "models", now)
        return _RT.fields(m, now)
    except Exception as e:  # shadow row still lands with a null model and the reason
        return {**_NULL, "model_status": "error:" + type(e).__name__ + ":" + str(e)[:120]}
