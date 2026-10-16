"""EXPLORATORY -- W76.2: F8 unit-level starter availability (OL / skill / DL / CB / back-seven) as a rate-layer Factor.

What it is: for each team-game, the snap-weighted number of *usual starters* the final weekly injury report says are
absent, split by unit. Point-in-time contract (nfl_point_in_time.PointInTime):
  * injury rows are 'weekly' kind -> usable only for Sunday/Monday games of the same week (Thu/Fri/Sat games -> None);
  * a starter's usual snap share comes from 'post_game' snap rows, kickoff + 4h <= target kickoff;
  * P(absent | status) and the unit coefficients are fitted by the caller on seasons strictly before the test season.
QB is excluded on purpose: the projected-starter QB EPA is already in arm B. Not a live model.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from prediction_market_bot.c1_signal_ingestion.nfl_point_in_time import COMPLETION_BUFFER, WEEK_OF_OK_WEEKDAYS, PointInTime

POS_UNIT = {**{p: "OL" for p in ("T", "G", "C", "OL")}, **{p: "SK" for p in ("WR", "TE", "RB", "FB")},
            **{p: "DL" for p in ("DE", "DT", "NT", "DL")}, "CB": "CB",
            **{p: "BK" for p in ("LB", "SS", "FS", "S", "DB")}}
UNITS = ("OL", "SK", "DL", "CB", "BK")
OFF_UNITS, DEF_UNITS = ("OL", "SK"), ("DL", "CB", "BK")
STATUSES = ("Out", "Doubtful", "Questionable")
STARTER_MIN, HIST_N, HIST_MIN, HIST_DAYS = 0.40, 6, 3, 400
_SUFFIX = re.compile(r"\b(jr|sr|ii|iii|iv|v)\b")


def name_key(s) -> str:
    return re.sub(r"[^a-z0-9]", "", _SUFFIX.sub("", re.sub(r"\.", "", str(s).lower())))


def _read(root: Path, kind: str, seasons) -> pd.DataFrame:
    parts = []
    for s in seasons:
        p = root / "exp_output" / "NFL_EVENTS" / "raw" / kind / f"{kind}_{s}.parquet"
        if p.exists():
            parts.append(pd.read_parquet(p))
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def build_flags(root, sched: pd.DataFrame, seasons: list[int], norm=lambda t: t) -> tuple[pd.DataFrame, pd.DataFrame, PointInTime]:
    """Returns (flags, team_games, pit). flags: one row per flagged non-QB player-game with status/unit/share/absent.
    team_games: one row per (game_id, team): usable (weekly rule), has_report (any report row that team-week)."""
    root = Path(root)
    pit = PointInTime(sched)
    g = sched[(sched.game_type == "REG") & sched.season.isin(seasons)].drop_duplicates("game_id").copy()
    g["kickoff"] = g.game_id.map(pit.k.kickoff_utc)
    tg = pd.concat([
        pd.DataFrame(dict(game_id=g.game_id, season=g.season, week=g.week, team=g.home_team.map(norm), opp=g.away_team.map(norm),
                          weekday=g.weekday, kickoff=g.kickoff, home=True)),
        pd.DataFrame(dict(game_id=g.game_id, season=g.season, week=g.week, team=g.away_team.map(norm), opp=g.home_team.map(norm),
                          weekday=g.weekday, kickoff=g.kickoff, home=False))], ignore_index=True)
    tg["usable"] = tg.weekday.isin(WEEK_OF_OK_WEEKDAYS)

    snaps = _read(root, "snaps", range(min(seasons) - 1, max(seasons) + 1))
    snaps["team"] = snaps.team.map(norm)
    snaps["unit"] = snaps.position.map(POS_UNIT)
    snaps = snaps[snaps.unit.notna()].copy()
    snaps["pct"] = np.where(snaps.unit.isin(OFF_UNITS), snaps.offense_pct, snaps.defense_pct)
    snaps["played"] = (snaps.offense_snaps.fillna(0) + snaps.defense_snaps.fillna(0)) > 0
    snaps["key"] = snaps.player.map(name_key)
    snaps["kickoff"] = snaps.game_id.map(pit.k.kickoff_utc).dt.tz_convert("UTC").dt.tz_localize(None).astype("datetime64[ns]")
    snaps = snaps.dropna(subset=["kickoff", "pct"]).sort_values("kickoff")
    hist = {k: (d.kickoff.to_numpy(), d.pct.to_numpy(float), d.unit.iloc[-1]) for k, d in snaps.groupby(["key", "team"])}
    played = set(map(tuple, snaps.loc[snaps.played, ["game_id", "team", "key"]].to_numpy()))
    snap_games = set(snaps.game_id)

    inj = _read(root, "injuries", seasons)
    inj = inj[(inj.game_type == "REG")].copy()
    inj["team"] = inj.team.map(norm)
    inj["key"] = inj.full_name.map(name_key)
    has_rep = set(zip(inj.season.astype(int), inj.week.astype(int), inj.team))
    tg["has_report"] = [(int(s), int(w), t) in has_rep for s, w, t in zip(tg.season, tg.week, tg.team)]
    f = inj[inj.report_status.isin(STATUSES)].sort_values("date_modified")
    f = f.drop_duplicates(["season", "week", "team", "key"], keep="last")
    f = f.merge(tg[["season", "week", "team", "game_id", "opp", "kickoff", "usable"]], on=["season", "week", "team"], how="inner")
    rows = []
    for r in f.itertuples():
        h = hist.get((r.key, r.team))
        if h is None:
            continue
        ko, pc, unit = h
        cut = (r.kickoff - COMPLETION_BUFFER).tz_convert("UTC").tz_localize(None).to_datetime64().astype("datetime64[ns]")
        hi = np.searchsorted(ko, cut, side="right")
        lo = max(0, hi - HIST_N)
        sel_ko, sel = ko[lo:hi], pc[lo:hi]
        keep = sel_ko >= cut - np.timedelta64(HIST_DAYS, "D")
        sel = sel[keep]
        share = float(sel.mean()) if len(sel) >= HIST_MIN else 0.0
        if share < STARTER_MIN:
            continue
        rows.append(dict(game_id=r.game_id, team=r.team, opp=r.opp, season=int(r.season), status=r.report_status, unit=unit,
                         share=share, usable=bool(r.usable),
                         absent=(float((r.game_id, r.team, r.key) not in played) if r.game_id in snap_games else np.nan)))
    return pd.DataFrame(rows), tg, pit


def absence_rates(flags: pd.DataFrame, max_season: int) -> dict:
    """P(absent | status) on seasons <= max_season. Fitted by the caller on training seasons only."""
    d = flags[(flags.season <= max_season) & flags.absent.notna()]
    out = {s: float(d.absent[d.status == s].mean()) if (d.status == s).sum() >= 20 else {"Out": .95, "Doubtful": .8, "Questionable": .25}[s]
           for s in STATUSES}
    return out


def lost_table(flags: pd.DataFrame, tg: pd.DataFrame, rates: dict) -> pd.DataFrame:
    """Expected snap-weighted starters lost per (game_id, team, unit). NaN where the report is unusable or absent."""
    base = tg.set_index(["game_id", "team"])
    cols = {u: pd.Series(0.0, index=base.index) for u in UNITS}
    if len(flags):
        d = flags[flags.usable].copy()
        d["v"] = d.share * d.status.map(rates)
        s = d.groupby(["game_id", "team", "unit"]).v.sum().unstack(fill_value=0.0)
        for u in UNITS:
            if u in s:
                cols[u] = s[u].reindex(base.index).fillna(0.0)
    out = pd.DataFrame(cols)
    ok = (base.usable & base.has_report).to_numpy()
    out.loc[~ok, :] = np.nan
    return out


class AvailabilityFactor:
    """rate_layer.Factor: points(as_of, offense, defense) = sum_u coef_u * (lost_u - center_u) over offense units (offense's own
    lost starters) and defense units (the opposing defense's lost starters). None (= league average) when no usable report."""
    name = "F8_unit_availability"

    def __init__(self, lost: pd.DataFrame, games: pd.DataFrame, coef: dict, center: dict):
        self.lost, self.coef, self.center = lost, coef, center
        self.gid = {(str(r.gameday), r.home, r.away): r.game_id for r in games.itertuples()}

    def _game(self, as_of, offense, defense):
        d = pd.Timestamp(as_of).strftime("%Y-%m-%d")
        return self.gid.get((d, offense, defense)) or self.gid.get((d, defense, offense))

    def points(self, as_of, offense, defense):
        gid = self._game(as_of, offense, defense)
        if gid is None:
            return None
        try:
            lo, ld = self.lost.loc[(gid, offense)], self.lost.loc[(gid, defense)]
        except KeyError:
            return None
        if lo.isna().any() or ld.isna().any():
            return None
        return float(sum(self.coef.get(u, 0.0) * (lo[u] - self.center.get(u, 0.0)) for u in OFF_UNITS)
                     + sum(self.coef.get(u, 0.0) * (ld[u] - self.center.get(u, 0.0)) for u in DEF_UNITS))


def side_matrix(lost: pd.DataFrame, tg: pd.DataFrame) -> pd.DataFrame:
    """One row per (game_id, team) attacking side: own offense-unit loss + opposing defense-unit loss (units as columns)."""
    d = tg[["game_id", "team", "opp", "season", "week", "home"]].copy()
    own = lost[list(OFF_UNITS)].reindex(pd.MultiIndex.from_frame(d[["game_id", "team"]])).reset_index(drop=True)
    opp = lost[list(DEF_UNITS)].reindex(pd.MultiIndex.from_frame(d[["game_id", "opp"]])).reset_index(drop=True)
    return pd.concat([d.reset_index(drop=True), own, opp], axis=1)


def fit_coefs(X: pd.DataFrame, y: np.ndarray, lam: float = 50.0) -> tuple[dict, dict]:
    """Centered ridge of team-point residual on the five unit-loss columns (centers = training means). Returns (coef, center)."""
    ok = X.notna().all(axis=1).to_numpy()
    Xm = X[ok].to_numpy(float)
    c = Xm.mean(axis=0)
    Z = Xm - c
    b = np.linalg.solve(Z.T @ Z + lam * np.eye(Z.shape[1]), Z.T @ (y[ok] - y[ok].mean()))
    return dict(zip(X.columns, map(float, b))), dict(zip(X.columns, map(float, c)))
