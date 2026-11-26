"""NBA PAM state backfill from the event store (W129.4 Part B). Pure functions over DataFrames; the runner is
``scripts/pam_state_backfill_nba.py``.

Decision time (as_of_ts) = tip_earliest - 4h, the same ">= 4h before tip" rule as the injury-report reader.
Every input is a *prior* game (strictly earlier ET day, so complete before as_of_ts) or a report slot stamped
at or before as_of_ts. Games whose tip had to be imputed (no ESPN match) are skipped, not guessed.

Named choices (all recorded in the row version/extra):
* usage = (FGA + 0.44 FTA + TOV) share of team, standard USG% form, minute-weighted over prior games;
  shrunk to the player's previous-season value (else the theoretical league mean 0.20) with PAM-3's points k
  (60.1 pseudo-minutes). Usage is not itself a PAM-3 stat; the points k is a named stand-in, not a fit.
* rotation = trailing mean minutes over the last 10 team games (played games only, >= 3 played; carried forward
  up to 30 team games while a player is out so a long-term injured starter still counts as vacated) >= 15,
  and listed on this game's roster.
* minutes_expected = shrunk minutes-when-played (k 0.82 games, prior 24.0 = 240 / 10 rotation slots) plus an
  UNFITTED proportional redistribution of out teammates' trailing minutes, cap 42. Not scored; do not read as a model.
* out = listed Out or Doubtful in the latest report slot <= as_of_ts. No report for the date -> teammates_out,
  vacated_usage_share = None (unknown, never 0).
* role_security and return_window are None (class 4 is the PREREG_PAM4 hypothesis, not built here).
"""
from __future__ import annotations

import datetime as _dt
import gzip
import json
from typing import Any, Iterable, Iterator

import numpy as np
import pandas as pd

from ..c1_signal_ingestion.nba_injury_reports import norm_name
from .state import AvailabilityProfile, PlayerState, TraitReliability

VERSION = "backfill-w129.4-v1"
SOURCE = "nba_event_store:player_box+schedule+espn_schedule;injury_cache:name-based"
K_USAGE_MIN = 60.1       # PAM-3 points k (pseudo-minutes), named stand-in
K_MPG_GAMES = 0.82       # PAM-3 mpg k (games)
USAGE_PRIOR = 0.20       # theoretical league mean USG
MPG_PRIOR = 24.0         # 240 minutes / 10 rotation slots
ROT_MIN, ROT_WIN, ROT_MINPLAYED, MIN_FULL_GAMES, CAP, CARRY = 15.0, 10, 3, 5, 42.0, 30
LEAD = pd.Timedelta(hours=4)
KEEP_TYPES = ("regular-season", "playoffs", "play-in")
OUT_STATUS = ("Out", "Doubtful")
INJ_FIRST_SEASON = 2023  # first season with cached reports (2022-23)


def parse_minutes(s: pd.Series) -> pd.Series:
    def one(x: Any) -> float:
        if x is None or (isinstance(x, float) and np.isnan(x)):
            return 0.0
        x = str(x)
        if ":" not in x:
            try:
                return float(x)
            except ValueError:
                return 0.0
        m, sec = x.split(":")[:2]
        try:
            return int(m) + int(sec) / 60.0
        except ValueError:
            return 0.0
    return s.map(one)


def prepare(box: pd.DataFrame, tips: pd.DataFrame) -> pd.DataFrame:
    """Join tips, drop non-target games and imputed tips, compute per-game usage and sort for cumulation."""
    b = box.copy()
    b["game_id"] = b["game_id"].astype(str)
    b["pid"] = b["person_id"].astype(str)
    b["tid"] = b["team_id"].astype(str)
    b["min"] = parse_minutes(b["minutes"])
    b["used"] = b["field_goals_attempted"].fillna(0) + 0.44 * b["free_throws_attempted"].fillna(0) + b["turnovers"].fillna(0)
    t = tips[["season", "season_type", "game_date", "tip_earliest", "tip_imputed"]].rename(columns={"season": "tseason"})
    b = b.merge(t, left_on="game_id", right_index=True, how="inner")
    b = b[b["season_type"].isin(KEEP_TYPES) & ~b["tip_imputed"].astype(bool)].copy()
    b["season"] = b["tseason"].astype(int)
    b["tip_earliest"] = pd.to_datetime(b["tip_earliest"], utc=True)
    b["as_of"] = b["tip_earliest"] - LEAD
    b["day"] = pd.to_datetime(b["game_date"].astype(str)).dt.date
    tm = b.groupby(["game_id", "tid"]).agg(tm_min=("min", "sum"), tm_used=("used", "sum"))
    b = b.merge(tm, left_on=["game_id", "tid"], right_index=True)
    ok = (b["min"] > 0) & (b["tm_used"] > 0) & (b["tm_min"] > 0)
    b["usage_g"] = np.where(ok, b["used"] * (b["tm_min"] / 5.0) / (b["min"].where(b["min"] > 0, 1) * b["tm_used"].where(b["tm_used"] > 0, 1)), 0.0)
    b["played"] = b["min"] > 0
    return b.sort_values(["pid", "tip_earliest", "game_id"]).reset_index(drop=True)


def player_priors(b: pd.DataFrame) -> pd.DataFrame:
    """Pre-game cumulative usage / minutes per player-game (strictly prior games only, shrunk to prior season)."""
    b = b.copy()
    b["u_min"] = b["usage_g"] * b["min"]
    g = b.groupby(["pid", "season"], sort=False)
    for c in ("u_min", "min", "played"):
        b["cum_" + c] = g[c].cumsum() - b[c]          # exclusive: this game's own row is never in its own prior
    b["roster_prior"] = g.cumcount()                   # listed (incl DNP) rows before this one this season
    # previous-season finals per player (most recent earlier season with a played game)
    fin = b.groupby(["pid", "season"]).agg(u_min=("u_min", "sum"), mn=("min", "sum"), gp=("played", "sum")).reset_index()
    fin = fin[fin["gp"] > 0].sort_values(["pid", "season"])
    fin["prev_season"] = fin.groupby("pid")["season"].shift(1)
    fin["p_usage"] = fin["u_min"] / fin["mn"]
    fin["p_mpg"] = fin["mn"] / fin["gp"]
    pri = fin[["pid", "season", "p_usage", "p_mpg"]].copy()
    pri["season"] = pri["season"].astype(int)
    b = b.sort_values(["pid", "season"], kind="stable")
    left = b[["pid", "season"]].drop_duplicates().sort_values("season")
    pri = pri.sort_values("season")
    pri["season_from"] = pri["season"] + 1
    m = pd.merge_asof(left, pri[["pid", "season_from", "p_usage", "p_mpg"]].sort_values("season_from"),
                      left_on="season", right_on="season_from", by="pid", direction="backward")
    b = b.merge(m[["pid", "season", "p_usage", "p_mpg"]], on=["pid", "season"], how="left")
    b["prior_found"] = b["p_usage"].notna()
    pu, pm = b["p_usage"].fillna(USAGE_PRIOR), b["p_mpg"].fillna(MPG_PRIOR)
    xbar_u = np.where(b["cum_min"] > 0, b["cum_u_min"] / b["cum_min"].where(b["cum_min"] > 0, 1), 0.0)
    b["usage_s"] = (b["cum_min"] * xbar_u + K_USAGE_MIN * pu) / (b["cum_min"] + K_USAGE_MIN)
    xbar_m = np.where(b["cum_played"] > 0, b["cum_min"] / b["cum_played"].where(b["cum_played"] > 0, 1), 0.0)
    b["mpg_s"] = (b["cum_played"] * xbar_m + K_MPG_GAMES * pm) / (b["cum_played"] + K_MPG_GAMES)
    b["n_min_prior"] = b["cum_min"]
    return b.sort_values(["pid", "tip_earliest", "game_id"]).reset_index(drop=True)


def _inj_out_names(inj: dict, day: _dt.date, as_of: pd.Timestamp) -> set[str] | None:
    """Names Out/Doubtful in the latest slot (ET HH:MM on the game's ET date) at or before as_of. None = no usable report."""
    rep = inj.get(day)
    if not rep:
        return None
    et = as_of.tz_convert("America/New_York")
    if et.date() != day:
        return None
    best = None
    for slot, snap in rep.items():
        hh, mm = slot.split(":")
        if int(hh) * 60 + int(mm) <= et.hour * 60 + et.minute and (best is None or slot > best):
            best = slot
    if best is None:
        return None
    return {norm_name(n) for n, s in rep[best].items() if s in OUT_STATUS}


def build_player_state(b: pd.DataFrame, inj: dict, written_at: str) -> Iterator[PlayerState]:
    b = b.copy()
    b["nname"] = (b["first_name"].fillna("") + " " + b["family_name"].fillna("")).map(norm_name)
    for (tid, season), tg in b.groupby(["tid", "season"], sort=False):
        games = tg.drop_duplicates("game_id").sort_values(["tip_earliest", "game_id"])[["game_id", "tip_earliest", "as_of", "day", "tm_min"]]
        gids = games["game_id"].tolist()
        pids = sorted(tg["pid"].unique())
        pidx = {p: i for i, p in enumerate(pids)}
        gidx = {g: i for i, g in enumerate(gids)}
        M = np.full((len(gids), len(pids)), np.nan)
        for r in tg.itertuples():
            M[gidx[r.game_id], pidx[r.pid]] = r.min if r.min > 0 else np.nan
        played = ~np.isnan(M)
        Mz = np.where(played, M, 0.0)
        TM = games["tm_min"].to_numpy()
        # trailing mpg over last ROT_WIN team games (played only), strictly before the game
        trail = pd.DataFrame(M).rolling(ROT_WIN, min_periods=ROT_MINPLAYED).mean().ffill(limit=CARRY).shift(1).to_numpy()
        by_game = {k: v for k, v in tg.groupby("game_id")}
        usage_at = {(r.game_id, r.pid): r.usage_s for r in tg.itertuples()}
        for gi, g in enumerate(games.itertuples()):
            rows = by_game[g.game_id]
            nm = dict(zip(rows["pid"], rows["nname"]))
            tr = trail[gi]
            rot = [j for j in range(len(pids)) if tr[j] >= ROT_MIN and pids[j] in nm]
            out_names = _inj_out_names(inj, g.day, g.as_of) if season >= INJ_FIRST_SEASON else None
            names_here = rows["nname"].value_counts()
            # full-roster prior games: every rotation player played
            prior = np.arange(gi)
            miss = (~played[:gi][:, rot]).sum(axis=1) if rot and gi else np.zeros(gi, int)
            for r in rows.itertuples():
                j = pidx[r.pid]
                out_j: list[int] = []
                if out_names is not None:
                    for k in rot:
                        if k == j:
                            continue
                        nk = nm.get(pids[k])
                        if nk is not None and nk in out_names and names_here.get(nk, 0) == 1:
                            out_j.append(k)
                rot_ex = [k for k in rot if k != j]
                ref = rot_ex if out_names is None else [k for k in rot_ex if k not in out_j]
                uvals = {k: usage_at.get((g.game_id, pids[k]), USAGE_PRIOR) for k in rot}
                u_j = r.usage_s
                rank = 1 + sum(1 for k in ref if uvals[k] > u_j)
                if out_names is None:
                    vac = tout = None
                    mexp = r.mpg_s
                else:
                    tout = len(out_j)
                    wt = {k: uvals[k] * tr[k] for k in rot}
                    denom = sum(wt.values()) + (0.0 if j in rot else u_j * r.mpg_s)
                    vac = float(min(1.0, max(0.0, sum(wt[k] for k in out_j) / denom))) if denom > 0 else None
                    avail_m = sum(tr[k] for k in ref) + (0.0 if j in rot else r.mpg_s)
                    extra_m = (sum(tr[k] for k in out_j) * (r.mpg_s / avail_m)) if avail_m > 0 else 0.0
                    mexp = r.mpg_s + extra_m
                mexp = float(min(CAP, mexp))
                # minutes share in prior games where every rotation player (and this player) played
                if gi:
                    m = (miss == 0) & (played[:gi, j] if j not in rot else True)
                    nfull = int(m.sum())
                    share = float(Mz[:gi][m, j].sum() / TM[:gi][m].sum()) if nfull >= MIN_FULL_GAMES else None
                else:
                    nfull, share = 0, None
                yield PlayerState(
                    sport="nba", player_id=r.pid, game_id=g.game_id, team=tid,
                    as_of_ts=_iso(g.as_of), known_at=_iso(g.as_of), source=SOURCE, version=VERSION,
                    usage_rate_shrunk=float(min(1.0, max(0.0, u_j))), usage_rank_available=int(rank),
                    teammates_out=tout, vacated_usage_share=vac, minutes_expected=mexp,
                    minutes_share_full_roster=share, role_security=None, return_window=None,
                    extra={"written_at": written_at, "inj": out_names is not None,
                           "rank_basis": "available_rotation" if out_names is not None else "all_rotation",
                           "n_full": nfull, "n_min_prior": round(float(r.n_min_prior), 1),
                           "prior_found": bool(r.prior_found), "k_usage_min": K_USAGE_MIN})


def build_availability(b: pd.DataFrame, written_at: str) -> Iterator[AvailabilityProfile]:
    """One row per player per game date: games played / listed games per season, up to the last 5 seasons, pre-game."""
    b = b.sort_values(["pid", "tip_earliest", "game_id"])
    for pid, grp in b.groupby("pid", sort=False):
        fin: dict[int, list[int]] = {}
        cur_season, gp, listed = None, 0, 0
        for r in grp.itertuples():
            if r.season != cur_season:
                if cur_season is not None:
                    fin[cur_season] = [gp, listed]
                cur_season, gp, listed = r.season, 0, 0
            seasons = {s: v for s, v in fin.items() if s > r.season - 6}
            if listed:
                seasons[r.season] = [gp, listed]
            yield AvailabilityProfile(
                sport="nba", player_id=pid, as_of_ts=_iso(r.as_of), known_at=_iso(r.as_of), source=SOURCE,
                version=VERSION, gp_by_season={str(s): v for s, v in sorted(seasons.items())},
                missed_by_body_part=None, recurrence_flags=None, expected_games_dist=None,
                extra={"written_at": written_at, "denominator": "listed_games (roster rows incl DNP), not 82",
                       "game_id": r.game_id})
            listed += 1
            gp += int(r.played)


def build_trait_reliability(draft: dict, written_at: str) -> list[TraitReliability]:
    """From the PAM-3 draft. known_at = end of the fit window (2022-07-01): valid for decisions judged 2023+ only."""
    out = []
    for row in draft["rows"] if isinstance(draft, dict) and "rows" in draft else draft:
        out.append(TraitReliability(
            sport="nba", stat=row["stat"], as_of_ts="2022-07-01T00:00:00Z", known_at="2022-07-01T00:00:00Z",
            source="12_EXPLORATORY/pam_stability/trait_reliability_draft.json", version="pam3-draft-v1",
            rate_def=str(row.get("unit")), r_year_to_year=row.get("r_year_to_year_descriptive"),
            r_split_half=row.get("r_split_half"), r_split_half_interval=None, k_stabilize=row.get("k"),
            k_unit=str(row.get("unit")), prior_rule="shrunk = (n*x + k*prior)/(n + k)", fit_seasons=list(range(2016, 2023)),
            extra={"k_90ci": row.get("k_90ci"), "r_full": row.get("r_full"), "n_player_seasons": row.get("n_player_seasons"),
                   "written_at": written_at, "status": "DRAFT; r interval not in the draft, left null"}))
    return out


def _iso(ts: pd.Timestamp) -> str:
    return ts.tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")


def write_gz(path, rows: Iterable[Any]) -> tuple[int, str]:
    """Stream rows to gzip JSONL; returns (count, sha256 of the compressed bytes)."""
    import hashlib
    from pathlib import Path
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with gzip.GzipFile(p, "wb", mtime=0) as fh:
        for r in rows:
            fh.write((json.dumps(r.to_dict(), sort_keys=True, ensure_ascii=False) + "\n").encode())
            n += 1
    return n, hashlib.sha256(p.read_bytes()).hexdigest()


def read_gz(path, table: str) -> Iterator[Any]:
    from .state import _CLASSES
    cls = _CLASSES[table]
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield cls.from_dict(json.loads(line))
